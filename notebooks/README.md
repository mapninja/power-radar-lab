# Tank lab notebooks

Run in order. Each notebook explains its own concepts.

| Notebook | Purpose | Needs |
|---|---|---|
| `01_search_and_retrieve_planet_imagery` | Search and download PlanetScope or SkySat clips for each AOI | Planet API key |
| `02_tank_inventory_osm` | Tank outlines, diameters, rough capacity from OpenStreetMap | Internet |
| `03_tank_metrics_from_imagery` | Shadow geometry, fill and volume, accuracy tests (runs offline on simulated tanks) | Labs 1 and 2 for the real-imagery section |
| `04_sentinel2_earth_engine_tank_metrics` | Free Sentinel-2 imagery from Google Earth Engine, plus a sub-pixel method for coarse pixels | Earth Engine account and project |
| `05_sentinel1_backscatter_and_ais_draught` | Part A: Sentinel-1 radar time series per tank in Earth Engine, plus a test against optical fill. Part B: tanker draught from AIS to a rough cargo estimate (runs on made-up data without downloads) | Earth Engine account; Lab 2 tank file; optional AIS files in `data/ais/` |
| `06_catalog_planetscope_skysat_iran_war_window` | Search-only catalog of PlanetScope and SkySat scenes over all six AOIs, from 6 months before the Iran war (28 Feb 2026) to today, with cloud and coverage filters. Uses the Planet Python SDK. No ordering or downloads | Planet API key (Colab secret or `PL_API_KEY` environment variable) |

`tank_utils.py` holds functions copied from Lab 3 for reuse in Lab 4. Edit both if you change one.

Install packages with `pip install -r requirements.txt`.
