import streamlit as st
import json
import folium
from streamlit_folium import st_folium
import os

def get_bounds_from_geojson(geojson):
    bounds = [[90, 180], [-90, -180]]
    for feature in geojson['features']:
        coords = feature['geometry']['coordinates']
        if feature['geometry']['type'] == 'Polygon':
            rings = [coords]
        else:
            rings = coords
        for ring in rings:
            for point in ring[0]:
                lon, lat = point
                bounds[0][0] = min(bounds[0][0], lat)
                bounds[0][1] = min(bounds[0][1], lon)
                bounds[1][0] = max(bounds[1][0], lat)
                bounds[1][1] = max(bounds[1][1], lon)
    return bounds

st.header("🗺️ Peta Batas Admin Level 4 (Lokal)")

file_path = "pages/batas_admin_indoensia.geojson"

if not os.path.exists(file_path):
    st.error("❌ File 'batas_admin_indoensia.geojson' tidak ditemukan di folder 'pages/'")
    st.stop()

# Load GeoJSON
with open(file_path, "r", encoding="utf-8") as f:
    geojson_data = json.load(f)

# Ambil nilai unik WADMPR
wadmpr_values = sorted({f["properties"].get("WADMPR", "Unknown") for f in geojson_data["features"]})
selected_wadmpr = st.selectbox("🔍 Pilih Provinsi (WADMPR):", wadmpr_values)

# Filter fitur
filtered_features = [f for f in geojson_data["features"] if f["properties"].get("WADMPR") == selected_wadmpr]
filtered_geojson = {
    "type": "FeatureCollection",
    "features": filtered_features
}

# Tampilkan peta
m = folium.Map(location=[-2.5, 117.5], zoom_start=5)
folium.GeoJson(filtered_geojson, name=selected_wadmpr).add_to(m)

if filtered_features:
    bounds = get_bounds_from_geojson(filtered_geojson)
    m.fit_bounds(bounds)

st_folium(m, width=700, height=450)
