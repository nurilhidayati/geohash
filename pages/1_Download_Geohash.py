import streamlit as st
import json
import folium
from streamlit_folium import st_folium
import os
import numpy as np
import pandas as pd
from shapely.geometry import shape, GeometryCollection, box, Polygon
from shapely.validation import make_valid
import geohash2

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

# GeoJSON ke GeoHash
def geojson_to_geohash6(geojson_data, precision=6, step=0.0015):
    if 'features' in geojson_data:
        geometries = [shape(feature['geometry']) for feature in geojson_data['features']]
    elif 'geometry' in geojson_data:
        geometries = [shape(geojson_data['geometry'])]
    elif 'type' in geojson_data and 'coordinates' in geojson_data:
        geometries = [shape(geojson_data)]
    else:
        raise ValueError("Unsupported GeoJSON structure")

    full_geom = GeometryCollection(geometries) if len(geometries) > 1 else geometries[0]
    full_geom = make_valid(full_geom)

    minx, miny, maxx, maxy = full_geom.bounds

    geohashes = set()
    for lat in np.arange(miny, maxy, step):
        for lon in np.arange(minx, maxx, step):
            cell = box(lon, lat, lon + step, lat + step)
            if full_geom.intersects(cell):
                gh = geohash2.encode(lat, lon, precision)
                geohashes.add(gh)
    return geohashes

# GeoHash ke GeoJSON
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
            "properties": {"geoHash": gh}
        })

    return {
        "type": "FeatureCollection",
        "features": features
    }

# Setup
st.set_page_config(layout="wide")
st.title("📍 Show GeoHash6 from Area")

# Siapkan default map
m = folium.Map(location=[-2.5, 117.5], zoom_start=5)

# Load data GeoJSON
kab_file = "pages/batas_admin_kabupaten.geojson"
prov_file = "pages/batas_admin_provinsi.geojson"
kab_geojson, prov_geojson = None, None

if os.path.exists(kab_file):
    with open(kab_file, "r", encoding="utf-8") as f:
        kab_geojson = json.load(f)
else:
    st.error("❌ File 'batas_admin_kabupaten.geojson' tidak ditemukan")

if os.path.exists(prov_file):
    with open(prov_file, "r", encoding="utf-8") as f:
        prov_geojson = json.load(f)
else:
    st.error("❌ File 'batas_admin_provinsi.geojson' tidak ditemukan")

# Dropdown
col1, col2 = st.columns([1, 1])
with col1:
    selected_kabupaten = "-- Select Regency --"
    if kab_geojson:
        kabupaten_list = sorted({f["properties"].get("WADMKK") for f in kab_geojson["features"] if f["properties"].get("WADMKK")})
        selected_kabupaten = st.selectbox("🏙️ Select Regency:", ["-- Select Regency --"] + kabupaten_list)

with col2:
    selected_provinsi = "-- Select Province --"
    if prov_geojson:
        provinsi_list = sorted({f["properties"].get("PROVINSI") for f in prov_geojson["features"] if f["properties"].get("PROVINSI")})
        selected_provinsi = st.selectbox("🏞️ Select Province:", ["-- Select Province --"] + provinsi_list)

# Tombol cari
if st.button("🔍 Show GeoHash"):
    area_geojson = None
    area_name = None

    if selected_kabupaten != "-- Select Regency --":
        filtered_kab = [
            f for f in kab_geojson["features"]
            if f["properties"].get("WADMKK") == selected_kabupaten
        ]
        area_geojson = {"type": "FeatureCollection", "features": filtered_kab}
        area_name = selected_kabupaten

    elif selected_provinsi != "-- Select Province --":
        filtered_prov = [
            f for f in prov_geojson["features"]
            if f["properties"].get("PROVINSI") == selected_provinsi
        ]
        area_geojson = {"type": "FeatureCollection", "features": filtered_prov}
        area_name = selected_provinsi

    if area_geojson:
        bounds = get_bounds_from_geojson(area_geojson)
        m.fit_bounds(bounds)

        geohashes = geojson_to_geohash6(area_geojson)
        geohash_geojson = geohash6_to_geojson(geohashes)

        # Tampilkan GeoHash layer
        folium.GeoJson(
            geohash_geojson,
            name="GeoHash6",
            style_function=lambda x: {"color": "#ff6600", "weight": 1, "fillOpacity": 0.3}
        ).add_to(m)

        # Tampilkan tombol download CSV
        gh_df = pd.DataFrame({"geohash6": sorted(list(geohashes))})
        csv = gh_df.to_csv(index=False).encode("utf-8")
        csv_filename = f"{area_name.replace(' ', '_').lower()}_geohash6.csv"
        st.download_button(
            label="📥 Download GeoHash as CSV",
            data=csv,
            file_name=csv_filename,
            mime="text/csv"
        )

# Tampilkan map
st_data = st_folium(m, width=1200, height=600)

# Footer
st.markdown(
    """
    <hr style="margin-top: 2rem; margin-bottom: 1rem;">
    <div style='text-align: center; color: grey; font-size: 0.9rem;'>
        © 2025 ID Karta IoT Team
    </div>
    """,
    unsafe_allow_html=True
)
