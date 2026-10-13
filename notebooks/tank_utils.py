"""Shared helpers for the tank labs.

These functions are copied unchanged from notebooks/03_tank_metrics_from_imagery.ipynb
so Lab 4 can reuse them. If you change a function here, change it in Lab 3 too.
"""
import numpy as np
import pandas as pd
from scipy.ndimage import gaussian_filter, map_coordinates
from skimage.filters import threshold_multiotsu
from skimage.feature import canny
from skimage.transform import hough_circle, hough_circle_peaks

BARRELS_PER_M3 = 6.2898     # one cubic meter holds about 6.29 barrels


def shadow_length(height_m, sun_elev_deg):
    """Length on flat ground of the shadow cast by something height_m tall."""
    return height_m / np.tan(np.radians(sun_elev_deg))


def depth_per_pixel(pixel_m, sun_elev_deg):
    """How much roof depth one pixel of shadow width stands for."""
    return pixel_m * np.tan(np.radians(sun_elev_deg))


def render_scene(tanks, sun_az, sun_elev, pixel_m, half_extent_m,
                 hires_m=0.5, noise=0.03, blur_sigma_px=0.6, seed=0):
    """Draw a grayscale overhead image (north is up) of floating-roof tanks.

    tanks: list of dicts with x, y (meters from image center), diameter_m, height_m, fill (0 to 1)
    Returns the image as a 2D array of brightness values between 0 and 1.
    """
    rng = np.random.default_rng(seed)                       # reproducible noise
    k = int(round(pixel_m / hires_m))                       # fine cells per output pixel
    n_out = int(round(2 * half_extent_m / pixel_m))         # output pixels per side
    n_hi = n_out * k                                        # fine cells per side

    # Coordinates of every fine cell, in meters. Rows run north to south.
    coords = (np.arange(n_hi) + 0.5) * hires_m - half_extent_m
    X, Y = np.meshgrid(coords, -coords)

    # Ground: mid-gray with gentle texture.
    img = 0.35 + 0.02 * gaussian_filter(rng.standard_normal((n_hi, n_hi)), 6) * 6

    # Unit vector pointing the way shadows fall (east, north components).
    az_s = np.radians((sun_az + 180) % 360)
    sx, sy = np.sin(az_s), np.cos(az_s)
    tan_e = np.tan(np.radians(sun_elev))

    inside_any = np.zeros(img.shape, dtype=bool)
    ground_shadow = np.zeros(img.shape, dtype=bool)

    for tk in tanks:
        R = tk["diameter_m"] / 2
        H = tk["height_m"]
        L_out = H / tan_e                                    # outer shadow length
        dx, dy = X - tk["x"], Y - tk["y"]                    # offset from tank center

        # Outer shadow = all points within R of the line from the tank center
        # to a point L_out away in the shadow direction.
        along = np.clip(dx * sx + dy * sy, 0, L_out)
        dist = np.hypot(dx - along * sx, dy - along * sy)
        ground_shadow |= dist <= R

        inside = np.hypot(dx, dy) <= R                       # cells on the roof

        # Inner shadow: a roof cell is shaded if the wall rim blocks the sun.
        # t is the horizontal distance from the cell to the wall, toward the sun.
        d = (1 - tk["fill"]) * H                             # roof depth below rim
        ps = dx * sx + dy * sy
        t = ps + np.sqrt(np.maximum(ps ** 2 + R ** 2 - (dx ** 2 + dy ** 2), 0))
        roof_shaded = t < d / tan_e

        roof = np.where(roof_shaded, 0.12, 0.60)             # dark in shadow, bright in sun
        img[inside] = roof[inside]
        inside_any |= inside

    img[ground_shadow & ~inside_any] = 0.09                  # dark outer shadow on ground

    # Mimic a real sensor: blur, then average fine cells into pixels, then add noise.
    img = gaussian_filter(img, blur_sigma_px * pixel_m / hires_m)
    img = img.reshape(n_out, k, n_out, k).mean(axis=(1, 3))
    img = img + rng.normal(0, noise, img.shape)
    return np.clip(img, 0, 1)


def to_pixel(x_m, y_m, pixel_m, half_extent_m):
    """Convert meters from image center to (column, row) pixel coordinates."""
    col = (x_m + half_extent_m) / pixel_m - 0.5
    row = (half_extent_m - y_m) / pixel_m - 0.5
    return col, row


def measure_fill(img, col, row, radius_px, sun_az, sun_elev, pixel_m, height_m=None):
    """Estimate fill fraction and volume for one tank in one image.

    col, row: tank center in pixel coordinates; radius_px: tank radius in pixels.
    height_m: wall height if known. If None, it is estimated from the outer shadow.
    """
    # 1. Choose a brightness threshold from a square chip around the tank.
    r = int(5 * radius_px)
    r0, r1 = max(int(row) - r, 0), min(int(row) + r, img.shape[0])
    c0, c1 = max(int(col) - r, 0), min(int(col) + r, img.shape[1])
    chip = img[r0:r1, c0:c1]
    thr = threshold_multiotsu(chip, classes=3)[0]     # lowest break = shadow vs the rest

    # 2. Sample brightness along the shadow direction through the tank center.
    az_s = np.radians((sun_az + 180) % 360)
    dcol, drow = np.sin(az_s), -np.cos(az_s)          # image rows grow southward
    step = 0.1                                        # sample every 0.1 pixel
    t = np.arange(-1.5 * radius_px, 8 * radius_px, step)    # pixels from tank center
    smooth = gaussian_filter(img, 0.5)
    prof = map_coordinates(smooth, [row + t * drow, col + t * dcol], order=1, mode="nearest")
    dark = prof < thr

    def dark_run_end(start_t, tol=1.0):
        """Length of the dark run that begins within tol pixels of start_t."""
        near = np.where((np.abs(t - start_t) <= tol) & dark)[0]
        if len(near) == 0:
            return 0.0                                # no shadow found there
        i = near[0]
        while i < len(t) - 1 and dark[i + 1]:         # walk to the end of the run
            i += 1
        if i >= len(t) - 1:
            return t[-1] - start_t
        # Linear interpolation for a sub-pixel edge position.
        frac = (thr - prof[i]) / (prof[i + 1] - prof[i] + 1e-9)
        return (t[i] + frac * step) - start_t

    L_in_px = dark_run_end(-radius_px)                # starts at the sun-side wall
    L_out_px = dark_run_end(+radius_px)               # starts at the far wall

    flags = []
    if L_out_px < 2:
        flags.append("outer_shadow_too_short")
    if L_in_px >= 2 * radius_px - 1:
        flags.append("roof_fully_shaded_fill_is_upper_bound")
        L_in_px = 2 * radius_px
    if L_out_px > 7 * radius_px:
        flags.append("outer_shadow_runs_off_search_range")

    if L_out_px < 2:                                  # cannot compute a ratio
        return {"fill": np.nan, "flags": ";".join(flags), "threshold": thr,
                "t": t, "profile": prof}

    fill = float(np.clip(1 - L_in_px / L_out_px, 0, 1))
    L_in_m, L_out_m = L_in_px * pixel_m, L_out_px * pixel_m
    H_est = L_out_m * np.tan(np.radians(sun_elev))    # wall height from outer shadow
    H_used = height_m if height_m else H_est
    radius_m = radius_px * pixel_m
    volume_m3 = fill * np.pi * radius_m ** 2 * H_used

    # Rough error: one pixel of uncertainty on each shadow edge.
    fill_err = (1.0 / L_out_px) * np.sqrt(1 + (L_in_px / L_out_px) ** 2)

    return {"fill": fill, "fill_err_1px": fill_err, "L_in_m": L_in_m, "L_out_m": L_out_m,
            "height_est_m": H_est, "volume_m3": volume_m3,
            "barrels": volume_m3 * BARRELS_PER_M3,
            "flags": ";".join(flags), "threshold": thr, "t": t, "profile": prof}


def ring_contrast(img, col, row, radius):
    """Mean brightness inside a circle minus mean brightness in a thin ring just outside it."""
    yy, xx = np.ogrid[:img.shape[0], :img.shape[1]]          # row and column index grids
    dist = np.hypot(xx - col, yy - row)                      # distance of every pixel from the center
    inside = img[dist <= 0.9 * radius].mean()
    ring = img[(dist > radius + 1) & (dist <= radius + 4)].mean()
    return inside - ring


def detect_tanks(img, pixel_m, min_d_m=25, max_d_m=100, min_contrast=0.10):
    """Find circular tanks in an image. Returns centers and radii in pixels."""
    edges = canny(img, sigma=1.5)                         # outline the bright/dark boundaries
    r_min = max(int(min_d_m / 2 / pixel_m), 3)
    r_max = int(max_d_m / 2 / pixel_m)
    radii = np.arange(r_min, r_max + 1)                   # radii to test, in pixels
    spaces = hough_circle(edges, radii)
    scores, cols, rows, rads = hough_circle_peaks(
        spaces, radii, min_xdistance=2, min_ydistance=2,
        threshold=0.6 * spaces.max(), total_num_peaks=100)

    # Keep the best-scoring circle in each place. Drop weaker circles that overlap it.
    kept = []
    for s_, c_, r_, rad_ in sorted(zip(scores, cols, rows, rads), key=lambda z: -z[0]):
        if all(np.hypot(c_ - k[1], r_ - k[2]) > 0.7 * max(rad_, k[3]) for k in kept):
            kept.append((s_, c_, r_, rad_))
    found = pd.DataFrame(kept, columns=["score", "col", "row", "radius_px"])

    # Shadow edges also look like circles. A real roof is brighter than the ground
    # around it, so drop circles that fail that test.
    found["contrast"] = [ring_contrast(img, r.col, r.row, r.radius_px) for r in found.itertuples()]
    return found[found["contrast"] >= min_contrast].reset_index(drop=True)


def sun_elevation_at(lat_deg, month, solar_hour=10.5):
    """Sun elevation (degrees) at a local solar hour, mid-month."""
    day_of_year = 15 + 30.4 * (month - 1)
    # Solar declination: the latitude where the sun is overhead on that date.
    decl = np.radians(23.44 * np.sin(np.radians(360 / 365 * (day_of_year - 81))))
    lat = np.radians(lat_deg)
    hour_angle = np.radians(15 * (solar_hour - 12))
    sin_el = np.sin(lat) * np.sin(decl) + np.cos(lat) * np.cos(decl) * np.cos(hour_angle)
    return np.degrees(np.arcsin(sin_el))
