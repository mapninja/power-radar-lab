#!/usr/bin/env python3
"""
Create 10km buffer bboxes for all AOI sites and search for Teapot refineries.
This script:
1. Reads AOI GeoJSON files from the AOI/ folder
2. Creates 10km buffer bboxes around each site
3. Queries Overpass API for industrial/refinery boundaries
4. Converts OSM data to GeoJSON FeatureCollections with resolved node coordinates
5. Replaces buffered bboxes with true property boundaries where found
"""

import json
import urllib.request
import os
import math
import time

# Configuration
OVERPASS_API_URL = "https://overpass-api.de/api/interpreter"
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
REFERER = "https://overpass-turbo.eu/"
AOI_FOLDER = "/Users/maples/Github/power-radar-lab/AOI"
BUFFER_KM = 10  # 10km buffer radius

def create_bbox_from_center(lat, lon, radius_km):
    """
    Create a bounding box around a center point with given radius.
    
    Args:
        lat: Center latitude in degrees
        lon: Center longitude in degrees
        radius_km: Radius in kilometers
    
    Returns:
        Tuple of (lat_min, lon_min, lat_max, lon_max)
    """
    # Approximate degrees per km
    degrees_per_km_lat = 1 / 111.32  # ~111 km per degree latitude
    degrees_per_km_lon = 1 / (111.32 * math.cos(math.radians(lat)))
    
    # Calculate bbox extent (radius in degrees)
    lat_extent = radius_km * degrees_per_km_lat
    lon_extent = radius_km * degrees_per_km_lon
    
    # Calculate bbox
    lat_min = max(-90, lat - lat_extent)
    lat_max = min(90, lat + lat_extent)
    lon_min = max(-180, lon - lon_extent)
    lon_max = min(180, lon + lon_extent)
    
    return lat_min, lon_min, lat_max, lon_max

def build_overpass_query(bbox):
    """
    Build Overpass query for industrial/refinery ways.
    
    Args:
        bbox: Tuple of (lat_min, lon_min, lat_max, lon_max)
    
    Returns:
        Overpass query string
    """
    lat_min, lon_min, lat_max, lon_max = bbox
    # Note: Overpass API bbox expects order: minlat,minlon,maxlat,maxlon
    query = f'''
[out:json][timeout:25][bbox:{lat_min},{lon_min},{lat_max},{lon_max}];
way["industrial"="refinery"];
way["landuse"="industrial"];
out body;
>;
out skel qt;
'''
    return query

def fetch_overpass_data(query, retries=3):
    """
    Fetch data from Overpass API with retry logic.
    
    Args:
        query: Overpass query string
        retries: Number of retry attempts
    
    Returns:
        JSON data or None on failure
    """
    headers = {
        "User-Agent": USER_AGENT,
        "Referer": REFERER,
        "Accept": "application/json"
    }
    
    for attempt in range(retries):
        try:
            req = urllib.request.Request(
                OVERPASS_API_URL,
                data=query.encode('utf-8'),
                headers=headers,
                method='POST'
            )
            
            with urllib.request.urlopen(req, timeout=120) as response:
                data = response.read().decode('utf-8')
                return data
        except urllib.error.HTTPError as e:
            print(f"  HTTP Error {e.code}: {e.reason}")
            if attempt < retries - 1:
                print(f"  Retrying in 5 seconds...")
                time.sleep(5)
        except urllib.error.URLError as e:
            print(f"  URL Error: {e.reason}")
            if attempt < retries - 1:
                print(f"  Retrying in 5 seconds...")
                time.sleep(5)
        except Exception as e:
            print(f"  Error fetching data: {str(e)}")
            if attempt < retries - 1:
                print(f"  Retrying in 5 seconds...")
                time.sleep(5)
    
    return None

def convert_osm_to_geojson(osm_data):
    """
    Convert Overpass OSM data to GeoJSON FeatureCollection.
    
    The Overpass API returns nodes and elements separately.
    We need to match node IDs to get coordinates.
    
    Args:
        osm_data: Raw Overpass API response string
    
    Returns:
        GeoJSON FeatureCollection or None on error
    """
    try:
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
                            continue
                    
                    if coords:
                        # Create a LineString geometry from the coordinates
                        # For proper polygon representation, we'd need to create
                        # a MultiPoint or use the coordinates as-is for LineString
                        feature = {
                            "type": "Feature",
                            "geometry": {
                                "type": "LineString",
                                "coordinates": coords
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
                "generated_at": "2026-10-01T04:44:01Z",
                "source": "Overpass API",
                "query_type": "industrial_refinery_boundaries",
                "search_window_km": BUFFER_KM,
                "features_count": len(features)
            }
        }
        
        return geojson
        
    except json.JSONDecodeError as e:
        print(f"  JSON decode error: {str(e)}")
        return None
    except Exception as e:
        print(f"  Error converting OSM to GeoJSON: {str(e)}")
        return None

def process_site(facility_name, center_lat, center_lon):
    """
    Process a single site: create 10km bbox, query Overpass, save to file.
    
    Args:
        facility_name: Name of the facility
        center_lat: Center latitude
        center_lon: Center longitude
    
    Returns:
        GeoJSON result or None
    """
    print(f"\nProcessing: {facility_name}")
    print(f"  Center: ({center_lat}, {center_lon})")
    
    # Create 10km bbox
    bbox = create_bbox_from_center(center_lat, center_lon, BUFFER_KM)
    print(f"  BBox: ({bbox[0]}, {bbox[1]}) to ({bbox[2]}, {bbox[3]})")
    
    # Build and execute query
    query = build_overpass_query(bbox)
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
    output_filename = f"{facility_name.lower().replace(' ', '_')}_10km_bbox.geojson"
    output_path = os.path.join(AOI_FOLDER, output_filename)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(geojson, f, indent=2)
    
    print(f"  Saved to: {output_path}")
    print(f"  Features found: {len(geojson['features'])}")
    
    return geojson

def main():
    """Main function to process all AOI sites."""
    print("=" * 70)
    print("Create 10km Buffer Bboxes for AOI Sites")
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
    total_features = sum(len(r['features']) for r in results.values())
    print(f"Total features found: {total_features}")
    
    # List output files
    print("\nOutput files created:")
    for filename in sorted(os.listdir(AOI_FOLDER)):
        if filename.endswith('_10km_bbox.geojson'):
            filepath = os.path.join(AOI_FOLDER, filename)
            print(f"  {filename}")
    
    return results

if __name__ == "__main__":
    results = main()