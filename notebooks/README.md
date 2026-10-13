# Tank lab notebooks

Run in order. Each notebook explains its own concepts.

Click a notebook name to read it on GitHub. Click the **Open in Colab** badge to run it in Google Colab. Colab needs one setup cell for Labs 1 to 5. See [Running in Google Colab](#running-in-google-colab) below.

| Notebook | Purpose | Needs | Colab |
|---|---|---|---|
| [`01_search_and_retrieve_planet_imagery`](01_search_and_retrieve_planet_imagery.ipynb) | Search and download PlanetScope or SkySat clips for each AOI | Planet API key | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/mapninja/power-radar-lab/blob/main/notebooks/01_search_and_retrieve_planet_imagery.ipynb) |
| [`02_tank_inventory_osm`](02_tank_inventory_osm.ipynb) | Tank outlines, diameters, rough capacity from OpenStreetMap | Internet | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/mapninja/power-radar-lab/blob/main/notebooks/02_tank_inventory_osm.ipynb) |
| [`03_tank_metrics_from_imagery`](03_tank_metrics_from_imagery.ipynb) | Shadow geometry, fill and volume, accuracy tests (runs offline on simulated tanks) | Labs 1 and 2 for the real-imagery section | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/mapninja/power-radar-lab/blob/main/notebooks/03_tank_metrics_from_imagery.ipynb) |
| [`04_sentinel2_earth_engine_tank_metrics`](04_sentinel2_earth_engine_tank_metrics.ipynb) | Free Sentinel-2 imagery from Google Earth Engine, plus a sub-pixel method for coarse pixels | Earth Engine account and project | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/mapninja/power-radar-lab/blob/main/notebooks/04_sentinel2_earth_engine_tank_metrics.ipynb) |
| [`05_sentinel1_backscatter_and_ais_draught`](05_sentinel1_backscatter_and_ais_draught.ipynb) | Part A: Sentinel-1 radar time series per tank in Earth Engine, plus a test against optical fill. Part B: tanker draught from AIS to a rough cargo estimate (runs on made-up data without downloads) | Earth Engine account; Lab 2 tank file; optional AIS files in `data/ais/` | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/mapninja/power-radar-lab/blob/main/notebooks/05_sentinel1_backscatter_and_ais_draught.ipynb) |
| [`06_catalog_planetscope_skysat_iran_war_window`](06_catalog_planetscope_skysat_iran_war_window.ipynb) | Search-only catalog of PlanetScope and SkySat scenes over all six AOIs, from 6 months before the Iran war (28 Feb 2026) to today, with cloud and coverage filters. Uses the Planet Python SDK. No ordering or downloads | Planet API key (Colab secret or `PL_API_KEY` environment variable) | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/mapninja/power-radar-lab/blob/main/notebooks/06_catalog_planetscope_skysat_iran_war_window.ipynb) |

`tank_utils.py` holds functions copied from Lab 3 for reuse in Lab 4. Edit both if you change one.

## Running locally

Install packages with `pip install -r requirements.txt`. Start Jupyter or VS Code from a Terminal window if you use an environment variable for your Planet key (Lab 6 explains why).

## Running in Google Colab

Opening a notebook from the badge gives Colab **only that one file**. The notebooks read the `AOI/` folder and (Lab 4) `tank_utils.py` using paths that start with `..`, so they need the rest of the repo next to them.

**Add this as the first cell** of the notebook, and run it before anything else. It copies the repo into Colab, moves into the `notebooks/` folder so the `..` paths work, and installs the packages Colab does not include:

```python
!git clone -q https://github.com/mapninja/power-radar-lab.git /content/power-radar-lab
%cd /content/power-radar-lab/notebooks
%pip install -q planet rasterio earthengine-api
```

Notes:

- Lab 6 also works without this cell if you upload the `AOI` folder to Colab and point `AOI_DIR` at it (Lab 6, Step 4 explains how). The cell above is the simpler route.
- Files saved in Colab disappear when the session ends. Download anything you want to keep, or mount Google Drive.
- Keys: in Colab, store your Planet key as a **secret** named `PL_API_KEY` (key icon in the left sidebar, notebook access on). Lab 6, Step 3, Method A walks through it. Never paste a key into a cell.
- Labs 1 to 5 were written for a local setup. They have not been tested in Colab. If one fails there, tell your instructor which cell and what the message said.
