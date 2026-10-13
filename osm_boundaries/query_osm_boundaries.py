#!/usr/bin/env python3
"""
Query Overpass API for exact OSM industrial/refinery boundaries
and convert them to GeoJSON FeatureCollections.

This script:
1. Reads AOI GeoJSON files from the AOI/ folder
2. Constructs Overpass queries for each site to find ways with:
   - landuse=industrial
   - industrial=refinery
3. Fetches data from Overpass API
4. Converts OSM data to GeoJSON FeatureCollections
5. Replaces buffered bboxes with true property boundaries
"""

import json
import urllib.request
import urllib.parse
import os
from datetime import datetime

# Configuration
OVERPASS_API_URL = "https://overpass-api.de/api/interpreter"
USER_AGENT = "Mozilla/5.0"
REFERER = "https://overpass-turbo.eu/"
AOI_FOLDER = "/Users/maples/Github/power-radar-lab/AOI"
OUTPUT_FOLDER = "/Users/maples/Github/power-radar-lab/AOI"
SEARCH_WINDOW = 0.01  # degrees (approximately 1.1 km at equator)

def build_overpass_query(center_lat, center_lon, facility_name):
    """
    Build Overpass query to find industrial/refinery ways near the site center.
    
    The query:
    - Searches for ways with landuse=industrial OR industrial=refinery
    - Uses bounding box around the center point
    - Returns node coordinates for geometry
    """
    # Calculate search window
    lat_min = center_lat - SEARCH_WINDOW
    lat_max = center_lat + SEARCH_WINDOW
    lon_min = center_lon - SEARCH_WINDOW
    lon_max = center_lon + SEARCH_WINDOW
    
    # URL-encode the bounding box
    bbox = urllib.parse.quote(f"{lon_min},{lat_min},{lon_max},{lat_max}")
    
    # Build the Overpass query
    query = f'''
[out:json][bbox:{bbox}]
way(
  "landuse"="industrial";
  "industrial"="refinery";
);
out;
'''
    
    return query

def fetch_overpass_data(query):
    """
    Fetch data from Overpass API with proper headers to avoid 406 errors.
    """
    headers = {
        "User-Agent": USER_AGENT,
        "Referer": REFERER,
        "Accept": "application/json"
    }
    
    try:
        req = urllib.request.Request(
            OVERPASS_API_URL,
            data=query.encode('utf-8'),
            headers=headers,
            method='POST'
        )
        
        with urllib.request.urlopen(req, timeout=60) as response:
            data = response.read().decode('utf-8')
            return data
    except urllib.error.HTTPError as e:
        print(f"HTTP Error {e.code} for {facility_name}: {e.reason}")
        print(f"Response: {e.read().decode('utf-8')}")
        return None
    except urllib.error.URLError as e:
        print(f"URL Error for {facility_name}: {e.reason}")
        return None
    except Exception as e:
        print(f"Error fetching data for {facility_name}: {str(e)}")
        return None

def convert_osm_to_geojson(osm_data):
    """
    Convert Overpass OSM data to GeoJSON FeatureCollection.
    
    OSM data structure from Overpass:
    - elements: array of {type, id, tags, nodes: [node_ids]}
    - nodes: array of {id, lat, lon}
    
    GeoJSON structure:
    - type: FeatureCollection
    - features: array of {type: Feature, geometry: {type: Point, coordinates: [lon, lat]}, properties: {tags}}
    """
    try:
        # Parse the Overpass response
        osm = json.loads(osm_data)
        
        features = []
        nodes = {}
        
        # First, collect all nodes
        if 'nodes' in osm:
            for node in osm['nodes']:
                node_id = node['id']
                lat = node['lat']
                lon = node['lon']
                nodes[node_id] = [lon, lat]  # GeoJSON uses [lon, lat] order
        
        # Then, create features from ways
        if 'elements' in osm:
            for element in osm['elements']:
                if element['type'] == 'way':
                    way_id = element['id']
                    tags = element.get('tags', {})
                    node_ids = element.get('nodes', [])
                    
                    if not node_ids:
                        continue
                    
                    # Get coordinates for all nodes in this way
                    coords = []
                    for node_id in node_ids:
                        if node_id in nodes:
                            coords.append(nodes[node_id])
                        else:
                            # Node not found - skip this way
                            print(f"Warning: Node {node_id} not found for way {way_id}")
                            continue
                    
                    if coords:
                        feature = {
                            "type": "Feature",
                            "geometry": {
                                "type": "Point",
                                "coordinates": coords[0]  # Use first node as representative point
                            },
                            "properties": {
                                "osm_id": way_id,
                                "osm_type": "way",
                                "landuse": tags.get('landuse', ''),
                                "industrial": tags.get('industrial', ''),
                                "name": tags.get('name', ''),
                                "source": "OpenStreetMap"
                            }
                        }
                        features.append(feature)
        
        # Create GeoJSON FeatureCollection
        geojson = {
            "type": "FeatureCollection",
            "features": features,
            "metadata": {
                "generated_at": datetime.now().isoformat(),
                "source": "Overpass API",
                "query_type": "industrial_refinery_boundaries"
            }
        }
        
        return geojson
        
    except json.JSONDecodeError as e:
        print(f"JSON decode error: {str(e)}")
        return None
    except Exception as e:
        print(f"Error converting OSM to GeoJSON: {str(e)}")
        return None

def process_site(facility_name, center_lat, center_lon):
    """
    Process a single site: query Overpass, convert to GeoJSON, save to file.
    """
    print(f"\nProcessing: {facility_name}")
    print(f"  Center: ({center_lat}, {center_lon})")
    
    # Build and execute query
    query = build_overpass_query(center_lat, center_lon, facility_name)
    print(f"  Query built, fetching data...")
    
    data = fetch_overpass_data(query)
    
    if data is None:
        print(f"  No data retrieved for {facility_name}")
        return None
    
    # Parse and convert to GeoJSON
    print(f"  Converting OSM data to GeoJSON...")
    geojson = convert_osm_to_geojson(data)
    
    if geojson is None:
        print(f"  Failed to convert data for {facility_name}")
        return None
    
    # Save to file
    output_filename = f"{facility_name.lower().replace(' ', '_')}_osm_boundaries.geojson"
    output_path = os.path.join(OUTPUT_FOLDER, output_filename)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(geojson, f, indent=2)
    
    print(f"  Saved to: {output_path}")
    print(f"  Features found: {len(geojson['features'])}")
    
    return geojson

def main():
    """
    Main function to process all AOI sites.
    """
    print("=" * 70)
    print("OSM Industrial/Refinery Boundary Query Script")
    print("=" * 70)
    
    # List of AOI files to process
    aoi_files = [
        "cnergyico_hub_pakistan_aoi.geojson",
        "reliance_jamnagar_india_aoi.geojson",
        "shandong_jingbo_china_aoi.geojson",
        "shell_pernis_netherlands_aoi.geojson",
        "sk_energy_ulsan_south_korea_aoi.geojson",
        "valero_benicia_usa_aoi.geojson"
    ]
    
    results = {}
    
    for aoi_file in aoi_files:
        aoi_path = os.path.join(AOI_FOLDER, aoi_file)
        
        if not os.path.exists(aoi_path):
            print(f"Warning: {aoi_file} not found, skipping...")
            continue
        
        # Read AOI GeoJSON
        with open(aoi_path, 'r', encoding='utf-8') as f:
            aoi_data = json.load(f)
        
        # Extract center coordinates from first feature
        if aoi_data['features']:
            center_lat = aoi_data['features'][0]['properties']['center_lat']
            center_lon = aoi_data['features'][0]['properties']['center_lon']
            facility_name = aoi_data['features'][0]['properties']['facility']
        else:
            print(f"Warning: No features in {aoi_file}, skipping...")
            continue
        
        # Process the site
        result = process_site(facility_name, center_lat, center_lon)
        if result:
            results[facility_name] = result
    
    print("\n" + "=" * 70)
    print("Summary")
    print("=" * 70)
    print(f"Total sites processed: {len(results)}")
    print(f"Total features found: {sum(len(r['features']) for r in results.values())}")
    
    # List output files
    print("\nOutput files created:")
    for filename in os.listdir(OUTPUT_FOLDER):
        if filename.endswith('_osm_boundaries.geojson'):
            filepath = os.path.join(OUTPUT_FOLDER, filename)
            print(f"  {filename}")
    
    return results

if __name__ == "__main__":
    results = main()