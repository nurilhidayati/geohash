import streamlit as st
import json
import folium
from streamlit_folium import st_folium
import os
import numpy as np
from shapely.geometry import shape, GeometryCollection, box, Polygon
from shapely.validation import make_valid
import geohash2
import pandas as pd
import geopandas as gpd

# Fungsi bantu untuk bounding map

def get_bounds_from_geojson(geojson):
    bounds = [[90, 180], [-90, -180]]
    for feature in geojson['features']:
        coords = feature['geometry']['coordinates']
        if feature['geometry']['type'] == 'Polygon':
            rings = [coords]
        else:  # MultiPolygon
            rings = coords
        for ring in rings:
            for point in ring[0]:
                lon, lat = point
                bounds[0][0] = min(bounds[0][0], lat)
                bounds[0][1] = min(bounds[0][1], lon)
                bounds[1][0] = max(bounds[1][0], lat)
                bounds[1][1] = max(bounds[1][1], lon)
    return bounds

# Fungsi GeoJSON ke GeoHash
@st.cache_data(show_spinner="\u231b Processing GeoHash...")
def geojson_to_geohash6(geojson_data, precision=6, step=0.005):
    if 'features' in geojson_data:
        geometries = [shape(feature['geometry']) for feature in geojson_data['features']]
    elif 'geometry' in geojson_data:
        geometries = [shape(geojson_data['geometry'])]
    elif 'type' in geojson_data and 'coordinates' in geojson_data:
        geometries = [shape(geojson_data)]
    else:
        raise ValueError("Unsupported GeoJSON structure")

    full_geom = GeometryCollection(geometries) if len(geometries) > 1 else geometries[0]
    if not full_geom.is_valid:
        full_geom = make_valid(full_geom)

    minx, miny, maxx, maxy = full_geom.bounds

    x_steps = np.linspace(minx, maxx, int((maxx - minx)/step))
    y_steps = np.linspace(miny, maxy, int((maxy - miny)/step))

    geohashes = set()
    for lat in y_steps:
        for lon in x_steps:
            cell = box(lon, lat, lon + step, lat + step)
            if full_geom.intersects(cell):
                gh = geohash2.encode(lat, lon, precision)
                geohashes.add(gh)
    return geohashes

# Fungsi GeoHash ke GeoJSON
def geohash6_to_geojson(geohashes):
    features = []
    for gh in geohashes:
        lat, lon, lat_err, lon_err = geohash2.decode_exactly(gh)
        cell = {
            "n": lat + lat_err,
            "s": lat - lat_err,
            "e": lon + lon_err,
            "w": lon - lon_err,
        }
        poly = Polygon([
            (cell['w'], cell['s']),
            (cell['e'], cell['s']),
            (cell['e'], cell['n']),
            (cell['w'], cell['n']),
            (cell['w'], cell['s']),
        ])
        features.append({
            "type": "Feature",
            "geometry": json.loads(json.dumps(poly.__geo_interface__)),
            "properties": {"Name": gh}
        })

    return {
        "type": "FeatureCollection",
        "features": features
    }

def geohash_to_csv(geohashes):
    rows = []
    for gh in geohashes:
        lat, lon, _, _ = geohash2.decode_exactly(gh)
        rows.append({"geohash": gh, "lat": lat, "lon": lon})
    df = pd.DataFrame(rows)
    return df.to_csv(index=False)

# Fungsi bantu render GeoJSON ke folium.Map
def render_map(geojson, center=[-6.2, 106.8], zoom=12, color="#3186cc"):
    m = folium.Map(location=center, zoom_start=zoom, tiles="cartodbpositron")
    folium.GeoJson(
        geojson,
        style_function=lambda x: {
            "fillColor": color,
            "color": color,
            "weight": 2,
            "fillOpacity": 0.4,
        }
    ).add_to(m)
    return m

# Streamlit UI
st.set_page_config(page_title="Split Map Viewer", layout="wide")
st.title("\ud83d\udea8 Split Map View: Boundary vs Geohash")

boundary_file = st.file_uploader("\ud83d\udcc1 Upload Boundary GeoJSON", type=["geojson"])
geohash_file = st.file_uploader("\ud83d\udcc1 Upload Geohash GeoJSON", type=["geojson"])

if boundary_file and geohash_file:
    boundary_gdf = gpd.read_file(boundary_file).to_crs("EPSG:4326")
    geohash_gdf = gpd.read_file(geohash_file).to_crs("EPSG:4326")

    center = boundary_gdf.unary_union.centroid.coords[0][::-1]  # lat, lon
    zoom = 13

    left_col, right_col = st.columns(2)

    with left_col:
        st.subheader("\ud83d\udccd Boundary Map")
        m1 = render_map(boundary_gdf.__geo_interface__, center=center, zoom=zoom, color="#3186cc")
        st_folium(m1, height=400)

    with right_col:
        st.subheader("\ud83d\udccd Geohash Map")
        m2 = render_map(geohash_gdf.__geo_interface__, center=center, zoom=zoom, color="#ff6600")
        st_folium(m2, height=400)
else:
    st.info("\u2b06\ufe0f Upload dua file GeoJSON untuk melihat perbandingan peta.")