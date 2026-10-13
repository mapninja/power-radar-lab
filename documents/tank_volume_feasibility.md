# Feasibility: Floating-roof tank volume from PlanetScope or SkySat

Date: 2026-10-04
Scope: the six sites in `data/Book1.csv` and `AOI/` (Shandong Jingbo, SK Ulsan, Shell Pernis, Reliance Jamnagar, Cnergyico Karachi, Valero Benicia).

## Bottom line

- **Classify tanks (floating vs. fixed roof, diameter): feasible** with PlanetScope for large tanks, and reliable with SkySat.
- **Measure fill level (volume) with PlanetScope: marginal.** Works only in low-sun months and only as a coarse, relative index. Not suited to absolute volumes.
- **Measure fill level with SkySat: feasible**, with roughly 2 to 5% of tank height per pixel. Limited by tasking cost and quota, not by physics.
- **Best practical path:** use PlanetScope for daily screening and tank inventory, and SkySat or Pelican for scheduled calibration passes. Add SAR (Sentinel-1, or commercial SAR) as the all-weather check. Optical shadow fails under cloud and at high sun.

## Update: Sentinel-2 and Google Earth Engine (2026-10-05)

- **Sentinel-2 (free, 10 m, 2 to 5 day revisit):** feasible for **large** tanks only. At 8 pixels across, the smallest usable tank is 80 m wide. Same 10:30 local overpass as PlanetScope, so the sun-angle limits in the tables below apply. One pixel of shadow width stands for about 2 to 6 m of roof depth in December (10 m × tan of 12° to 39°) and 7 to 22 m from spring through summer, against a typical tank height of 15 to 20 m (assumption). Only winter is workable.
- **Edge-finding fails at 10 m.** In simulation (100 m wide, 15 m tall tank), the Lab 3 edge method has fill RMSE of about 0.14 to 0.37 and reads tanks too full.
- **Profile fitting works much better if wall height is known.** The same simulation gives RMSE of about 0.04 to 0.09. It needs two calibration constants (shaded-to-lit brightness ratios) and a wall height. Without a known height the fit is erratic.
- **The same fit also helps PlanetScope** (simulated RMSE about 0.01 to 0.03 vs. 0.06 to 0.20 for edges). Lab 3 still teaches the edge method first.
- **Earth Engine:** hosts `COPERNICUS/S2_SR_HARMONIZED` and the per-pixel clarity dataset `GOOGLE/CLOUD_SCORE_PLUS/V1/S2_HARMONIZED`. Scene metadata includes solar azimuth and zenith angles. Small chips download with `getDownloadURL` (about 32 MB limit). Lab 4 (`notebooks/04_sentinel2_earth_engine_tank_metrics.ipynb`) covers search, cloud screening, download and measurement.
- **Caveats:** These are simulation results with ideal calibration. Real tanks have roof fittings, neighbors, haze and unknown calibration. Nothing here has been checked against real Sentinel-2 chips or ground truth. The Earth Engine code was written from documentation and tested only against stubs.
- **Role in the plan:** Sentinel-2 is the free, repeatable option for the largest tanks, and the one students can run without a license. Use PlanetScope or SkySat when tanks are under 80 m wide or when you need a finer reading. Radar remains the all-weather check.
- **Constellation status** (from ESA pages found by search): Sentinel-2C replaced 2A in operations in January 2025, and 2A has been flying an extension campaign. Confirm current status before relying on revisit rates.

Extra sources: [Harmonized Sentinel-2 SR, Earth Engine catalog](https://developers.google.com/earth-engine/datasets/catalog/COPERNICUS_S2_SR_HARMONIZED), [Sentinel-2 mission, SentiWiki](https://sentiwiki.copernicus.eu/web/s2-mission), [Image.getDownloadURL, Earth Engine docs](https://developers.google.com/earth-engine/apidocs/ee-image-getdownloadurl), [Authentication and initialization, Earth Engine](https://developers.google.com/earth-engine/guides/auth), [Estimating the volume of oil tanks from high-resolution images, Remote Sensing 2019](https://www.mdpi.com/2072-4292/11/7/793), [Floating-Lid-Tank-Depth (uses Sentinel-2), GitHub](https://github.com/124890/Floating-Lid-Tank-Depth).

## Update: Sentinel-1 radar and tanker draught (2026-10-05)

- **Sentinel-1 for tank volume:** The published single-tank radar work used high-resolution radar (DLR, IEEE JSTARS: roof-height RMSE about 1.05 m). Sentinel-1 has 20 x 22 m resolution and 10 m pixels, so a 60 to 100 m tank spans a few pixels. Kayrros reports using Sentinel-1 for floating-roof tanks at 500+ locations, and Ursa Space reports a 0.98 correlation with EIA Cushing figures. Both are company claims without a published method.
- **Working view (inference, untested here):** Sentinel-1 is more likely to work as a regional index or a gap-filler calibrated against optical fill than as a single-tank volume measure. Compare dates from one relative orbit and direction only, and average in linear power, not dB.
- **Fixed-roof and internal-floating-roof tanks** give no usable fill signal in radar either.
- **Tanker draught:** No validated way to measure draught directly from Sentinel-1 or Planet imagery was found. Practical analysis uses the AIS draught field, which the crew enters by hand (0.1 m units; 0 means not available; 25.5 means 25.5 m or more). Commercial providers compare it with the ship's maximum draught to label ships laden or in ballast. Imagery helps confirm a ship is at berth and estimate its length.
- **Rough cargo formula:** cargo change is about DWT × change in draught ÷ (full draught minus ballast draught). It ignores hull shape, fuel and ballast water. The class table in Lab 5 uses illustrative round numbers, not registry data.
- **Lab 5** (`notebooks/05_sentinel1_backscatter_and_ais_draught.ipynb`) builds the radar time series, a validation test against optical fill, and an AIS draught pipeline. The Earth Engine code was written from documentation and tested only against stubs. The AIS pipeline was tested only on made-up data.
- **Free AIS sources:** MarineCadastre / NOAA (U.S. waters; columns include Draft, VesselType, IMO, Length) and the Danish Maritime Authority (aisdata.ais.dk; columns include Draught, Ship type).

Extra sources: [Sentinel-1 SAR GRD, Earth Engine catalog](https://developers.google.com/earth-engine/datasets/catalog/COPERNICUS_S1_GRD), [Sentinel-1 helps monitor oil industry activity](https://sentinels.copernicus.eu/web/success-stories/-/copernicus-sentinel-1-helps-monitor-oil-industry-activity), [Monitoring of Oil Tank Filling with Spaceborne SAR (DLR)](https://elib.dlr.de/142408/1/IEEE%20JSTARS%20-%20Oil%20storage.pdf), [AIS Class A static and voyage data, Message 5 (USCG Navigation Center)](https://www.navcen.uscg.gov/ais-class-a-static-voyage-message-5), [AccessAIS, MarineCadastre](https://marinecadastre.gov/accessais/), [AIS data, Danish Maritime Authority](https://www.dma.dk/safety-at-sea/navigational-information/ais-data), [Sentinel-1A concludes its mission](https://defence-industry-space.ec.europa.eu/sentinel-1a-concludes-its-mission-leaving-lasting-legacy-copernicus-2026-06-30_en).

## What the repo has today

- Six 5x5 km AOIs plus 5 km buffers and 10 km bboxes. Site metadata is in `data/Book1.csv`.
- No tank inventory. `AOI/*_osm_boundaries.geojson` holds site outlines only (the Cnergyico file has zero features). No tank footprints, diameters or heights.
- The first step for any approach is a tank inventory (see Workflow).

## Sensor facts

| | PlanetScope (SuperDove) | SkySat |
|---|---|---|
| Pixel size | 3 m, 8 bands | 0.5 m orthorectified (about 0.8 m on standard archive products at Stanford) |
| Revisit | Near daily, global | Up to 10x daily by tasking |
| Swath | about 32.5 x 19.6 km scene | 5.5 to 8 km at nadir, depending on satellite |
| Overpass | About 10:30 local solar time, 90% within a roughly 1.5 to 2 hour window | Tasked, so you pick the window |
| Geolocation | CE90 about 13.8 m globally | Better, not quantified here |
| Access | Stanford enterprise account | Stanford archive quota about 5,000 km2; tasking grant 4 requests of 25 km2 each |

Notes:

- Planet's Pelican constellation (50 cm, 6 bands) is in general availability. It is being merged with SkySat into one tasking system. Check whether new SkySat tasking is still offered before planning around it.
- The Basic Education and Research program (3,000 km2/month) covers PlanetScope only, not SkySat or tasking. Stanford's enterprise account is the route to SkySat.
- The Planet docs pages could not be fetched in this session. Specs come from search summaries. Confirm against the current Planet product specifications before committing.

## How the shadow method works

A floating roof sits on the product. As the tank empties, the roof drops and the tank wall casts a shadow onto it. Fill fraction is estimated from the ratio of inner shadow to outer (ground) shadow. TankerTrackers and several open projects use this approach on Planet imagery. Open examples reach about 0.84 average precision for tank detection with YOLOv3. That figure is for detection, not volume accuracy.

Pixel math: a rim `d` meters above the roof casts a shadow of length `d / tan(sun elevation)`. One pixel of shadow width therefore resolves `pixel size x tan(elevation)` of roof depth.

Sun elevation at 10:30 local solar time (computed for this report):

| Site | Dec 21 | Mar 20 / Sep 22 | Jun 21 |
|---|---|---|---|
| Shell Pernis (51.9 N) | 12 | 34 | 57 |
| Shandong Jingbo (37.2 N) | 26 | 47 | 66 |
| SK Ulsan (35.4 N) | 27 | 48 | 67 |
| Valero Benicia (38.1 N) | 25 | 46 | 66 |
| Cnergyico Karachi (24.9 N) | 37 | 56 | 69 |
| Reliance Jamnagar (22.3 N) | 39 | 58 | 69 |

Roof depth resolved per pixel of shadow width (meters):

| Site | PlanetScope Dec | PlanetScope Mar/Sep | PlanetScope Jun | SkySat Dec | SkySat Mar/Sep | SkySat Jun |
|---|---|---|---|---|---|---|
| Shell Pernis | 0.6 | 2.0 | 4.6 | 0.11 | 0.34 | 0.76 |
| Shandong Jingbo | 1.4 | 3.2 | 6.8 | 0.24 | 0.53 | 1.14 |
| SK Ulsan | 1.6 | 3.3 | 7.1 | 0.26 | 0.56 | 1.18 |
| Valero Benicia | 1.4 | 3.1 | 6.7 | 0.23 | 0.52 | 1.12 |
| Cnergyico Karachi | 2.3 | 4.5 | 8.0 | 0.38 | 0.75 | 1.33 |
| Reliance Jamnagar | 2.5 | 4.8 | 7.9 | 0.41 | 0.80 | 1.32 |

Reading the table, assuming a typical large refinery tank is 15 to 20 m tall (assumption, not from the repo):

- **PlanetScope:** In winter at mid-latitudes, 1 to 2.5 m per pixel is about 5 to 15% of tank height. Usable as a coarse index. Sub-pixel edge fitting may improve it, but this is untested. In summer at 3 to 8 m per pixel, a pixel is a third or more of the tank height. Not usable for volume.
- **SkySat:** 0.1 to 0.8 m per pixel is about 1 to 5% of tank height, outside of summer. This is good enough for useful volume estimates.
- **Site ranking by physics:** Pernis is best (high latitude, long shadows) but is also cloudy. Jamnagar and Karachi are worst (high sun) but clearer skies. Winter is the usable season for PlanetScope everywhere.
- **Tank size:** A 3 m pixel against a 40 to 80 m diameter tank gives 13 to 27 pixels across. Detectable. Small tanks (under about 30 m) are not reliable on PlanetScope.

## Volume conversion

Volume = (fill fraction) x (tank capacity). Capacity needs diameter and shell height.

- Diameter: from imagery (footprint), good to about one pixel.
- Height: from the outer shadow length and sun elevation, or from a tank database. Outer shadow is more reliable on SkySat.
- Public US dataset of about 130,000 above-ground tanks (Scientific Data, 2023) can support training and the US site (Benicia). It does not cover the other five sites.
- Error terms to carry: roof-leg and pontoon geometry, tank-to-tank shading, wall height assumptions, sun elevation from metadata, geolocation offsets, and tanks with internal floating roofs (not visible at all).
- Floating roofs hide nothing about density, product type or heated/unheated state. Imagery gives volume, not product.

## Known limits

- Fixed-roof tanks and internal floating roof tanks give no usable fill signal in optical imagery.
- Cloud and haze. Coastal sites (Ulsan, Pernis, Benicia) lose many days. Planet's daily revisit helps but does not remove this.
- Fixed 10:30 overpass means you cannot choose a favorable sun angle with PlanetScope. SkySat tasking can pick early or late slots for longer shadows.
- Shadow is easiest when a tank is mostly empty or mostly full. Mid-range fills spread across a thin crescent.
- Commercial licensing: derived products and redistribution are restricted under Planet's terms. Check the Stanford agreement before publishing tank-level results.

## SAR as the cross-check

Commercial inventory providers (Ursa Space, Kayrros) rely mainly on SAR for floating-roof tanks because it works through cloud and at night. A published DLR study (IEEE JSTARS) reports tank height precision of 0.23 m and a floating-roof height RMSE of about 1.05 m, with R-squared 0.98 for storage change. It uses high-resolution SAR, not Sentinel-1. Ursa reports 0.98 correlation with EIA Cushing figures. Both are vendor or single-study results at sites with known tank data. Treat as indicative, not guaranteed. Sentinel-1 is free but coarser, so test it before assuming it matches these numbers.

## Per-site feasibility

| Site | Optical shadow outlook | Notes |
|---|---|---|
| SK Ulsan | Good with SkySat; PlanetScope winter only | Large coastal complex, matches "High" observability in `Book1.csv`. Best calibration case. |
| Shell Pernis | Best sun geometry; cloud is the constraint | Many tank farms nearby, so mixed fixed and floating roofs. |
| Valero Benicia | Good | Public tank data and permit records can ground-truth. Facility winding down in 2026, so useful for a visible drawdown. |
| Reliance Jamnagar | Hard for PlanetScope (high sun); SkySat workable | Large site. Clear skies. Many tanks, so SkySat footprint (about 6 to 8 km swath) fits a 5 km AOI. |
| Cnergyico Karachi | Same sun issue as Jamnagar | Book1 rates observability Low-Medium. Verify tank count first. |
| Shandong Jingbo | Weak | Book1 rates observability Low and public evidence is thin. Ground truth is unavailable. |

## Suggested workflow

1. **Tank inventory.** Pull storage tank footprints for each AOI from OSM (`man_made=storage_tank`, `content=oil`, `roof:shape`) using the Overpass skill. Fill gaps by detection on PlanetScope. Record diameter, location, roof type.
2. **Classify.** Floating vs. fixed using shadow and brightness patterns. Validate on 100+ hand-labeled tanks per site.
3. **Pilot.** SK Ulsan or Benicia. Collect one PlanetScope winter series plus 2 to 3 SkySat tasked passes at different sun times.
4. **Measure.** Segment inner and outer shadows, compute fill fraction, convert to volume.
5. **Validate.** Benicia against public records; others against SAR time series, flare and throughput signals already in the project.
6. **Scale** to the other sites only if the pilot error is acceptable.

## Rough cost and access

- PlanetScope archive: covered by the Stanford account within quota. A 5x5 km AOI is 25 km2 per scene, so a daily series uses roughly 9,000 km2 per year per site if downloaded every day. Check quota use before bulk pulls.
- SkySat: Stanford tasking grant allows 4 requests of 25 km2 each (100 km2 total). That covers about four site passes. A time series needs another budget or the Pelican route.
- Pricing for commercial tasking was not found in this research. Ask Planet or the Stanford Geospatial Center.

## Open questions

- How many tanks are in each AOI, and how many are external floating roof?
- Are tank heights available from any public source for the non-US sites?
- Does Stanford's agreement permit derived tank-level volumes in publications or course materials?
- Is new SkySat tasking still offered, or must requests go through Pelican?

## Sources

- [PlanetScope | Planet Documentation](https://docs.planet.com/data/imagery/planetscope/)
- [PlanetScope Product Specifications, June 2026](https://assets.planet.com/docs/Planet_PSScene_Imagery_Product_Spec_letter_screen.pdf)
- [SkySat | Planet Documentation](https://docs.planet.com/data/imagery/skysat/)
- [SkySat Constellation, eoPortal](https://www.eoportal.org/satellite-missions/skysat)
- [Pelican | Planet Documentation](https://docs.planet.com/data/imagery/pelican/)
- [Geometric Assessment of PlanetScope Imagery, NASA NTRS](https://ntrs.nasa.gov/citations/20240001689)
- [Global analysis of PlanetScope temporal availability, Remote Sensing of Environment](https://www.sciencedirect.com/science/article/pii/S0034425721003060)
- [Planet imagery at Stanford, Geospatial Center guide](https://guides.library.stanford.edu/planetlabs)
- [Planet Education and Research program](https://www.planet.com/industries/education-and-research/)
- [Does the Education and Research program include SkySat?, Planet Support](https://support.planet.com/hc/en-us/articles/360016382257-Does-the-Education-and-Research-program-include-SkySat-imagery-and-access-to-Tasking-dashboard)
- [TankerTrackers: oil storage tank occupancy from satellite imagery, Planet Stories](https://medium.com/planet-stories/a-beginners-guide-to-calculating-oil-storage-tank-occupancy-with-help-of-satellite-imagery-e8f387200178)
- [Oil storage tank volume occupancy using YOLOv3, Towards Data Science](https://towardsdatascience.com/oil-storage-tanks-volume-occupancy-on-satellite-imagery-using-yolov3-3cf251362d9d/)
- [Estimating floating-head tank volumes using shadows, GitHub](https://github.com/kheyer/Oil-Tank-Volume-Estimation)
- [Above-ground storage tank dataset, Scientific Data](https://www.nature.com/articles/s41597-023-02780-1)
- [Monitoring of Oil Tank Filling with Spaceborne SAR, DLR / IEEE JSTARS](https://elib.dlr.de/142408/1/IEEE%20JSTARS%20-%20Oil%20storage.pdf)
- [An inside look at SAR-based measurements, Ursa Space](https://ursaspace.com/blog/an-inside-look-at-sar-based-measurements/)
- [Crude Oil Inventory, Kayrros](https://www.kayrros.com/products/coi-for-traders/)
