import streamlit as st
import json
import folium
from streamlit_folium import st_folium
import os

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

st.header("🗺️ Peta Kabupaten (Filter Berdasarkan WADMKK)")

# File path
file_path = "pages/batas_admin_indoensia.geojson"

# Cek keberadaan file
if not os.path.exists(file_path):
    st.error("❌ File 'batas_admin_indoensia.geojson' tidak ditemukan di folder 'pages/'")
    st.stop()

# Baca GeoJSON
with open(file_path, "r", encoding="utf-8") as f:
    geojson_data = json.load(f)

# Ambil list unik WADMKK (tanpa None)
wadmkk_list = sorted({f["properties"].get("WADMKK") for f in geojson_data["features"] if f["properties"].get("WADMKK")})

# Dropdown hanya nama kabupaten
selected_wadmkk = st.selectbox("🏙️ Pilih Kabupaten (WADMKK):", wadmkk_list)

# Filter fitur berdasarkan pilihan
filtered_features = [f for f in geojson_data["features"] if f["properties"].get("WADMKK") == selected_wadmkk]
filtered_geojson = {
    "type": "FeatureCollection",
    "features": filtered_features
}

# Peta
m = folium.Map(location=[-2.5, 117.5], zoom_start=5)
folium.GeoJson(filtered_geojson, name=selected_wadmkk).add_to(m)

if filtered_features:
    bounds = get_bounds_from_geojson(filtered_geojson)
    m.fit_bounds(bounds)

st_folium(m, width=700, height=500)
