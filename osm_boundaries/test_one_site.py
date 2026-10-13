#!/usr/bin/env python3
"""
Test script to query Overpass API for one AOI site and convert to GeoJSON.
"""

import json
import urllib.request

# Configuration for Cnergyico Hub, Pakistan
CENTER_LAT = 24.90995
CENTER_LON = 66.7084
FACILITY_NAME = "Cnergyico Hub, Pakistan"
SEARCH_WINDOW = 0.5  # degrees (approximately 55 km at equator - very broad search)

# Calculate bounding box (raw values, no URL encoding)
lat_min = CENTER_LAT - SEARCH_WINDOW
lat_max = CENTER_LAT + SEARCH_WINDOW
lon_min = CENTER_LON - SEARCH_WINDOW
lon_max = CENTER_LON + SEARCH_WINDOW

print(f"Facility: {FACILITY_NAME}")
print(f"Center: ({CENTER_LAT}, {CENTER_LON})")
print(f"Bounding box: ({lon_min}, {lat_min}) to ({lon_max}, {lat_max})")

# Build Overpass query - request nodes with their coordinates
query = f'''
[out:json][timeout:25][bbox:{lon_min},{lat_min},{lon_max},{lat_max}];
way["industrial"="refinery"];
way["landuse"="industrial"];
out body;
>;
out skel qt;
'''

print("\nQuery:")
print(query)

# Fetch from Overpass API
headers = {
    "User-Agent": "Mozilla/5.0",
    "Referer": "https://overpass-turbo.eu/",
    "Accept": "application/json"
}

req = urllib.request.Request(
    "https://overpass-api.de/api/interpreter",
    data=query.encode('utf-8'),
    headers=headers,
    method='POST'
)

try:
    with urllib.request.urlopen(req, timeout=60) as response:
        data = response.read().decode('utf-8')
        print("\nResponse received:")
        print(data[:3000])  # Print first 3000 chars
        
        # Parse the Overpass response
        osm = json.loads(data)
        
        # Convert to GeoJSON
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
                "generated_at": "2026-09-30T22:57:02Z",
                "source": "Overpass API",
                "query_type": "industrial_refinery_boundaries",
                "facility": FACILITY_NAME
            }
        }
        
        print("\nConverted to GeoJSON:")
        print(json.dumps(geojson, indent=2)[:2000])
        
except urllib.error.HTTPError as e:
    print(f"HTTP Error {e.code}: {e.reason}")
    print(f"Response: {e.read().decode('utf-8')}")
except urllib.error.URLError as e:
    print(f"URL Error: {e.reason}")
except Exception as e:
    print(f"Error: {str(e)}")