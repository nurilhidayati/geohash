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

st.header("🗺️ Peta Interaktif: Provinsi atau Kabupaten")

# Inisialisasi peta awal
m = folium.Map(location=[-2.5, 117.5], zoom_start=5)

# === Baca dan siapkan data kabupaten ===
kabupaten_file = "pages/batas_admin_kabupaten.geojson"
provinsi_file = "pages/batas_admin_provinsi.geojson"

if not os.path.exists(kabupaten_file) or not os.path.exists(provinsi_file):
    st.error("❌ File batas provinsi/kabupaten tidak ditemukan.")
    st.stop()

with open(kabupaten_file, "r", encoding="utf-8") as f:
    kabupaten_data = json.load(f)

with open(provinsi_file, "r", encoding="utf-8") as f:
    provinsi_data = json.load(f)

# Siapkan pilihan user
mode = st.radio("📌 Pilih Mode:", ["Provinsi", "Kabupaten"])

if mode == "Kabupaten":
    wadmkk_list = sorted({
        f["properties"].get("WADMKK")
        for f in kabupaten_data["features"]
        if f["properties"].get("WADMKK")
    })
    selected_kabupaten = st.selectbox("🏙️ Pilih Kabupaten:", ["-- Pilih --"] + wadmkk_list)

    if selected_kabupaten != "-- Pilih --":
        filtered_features = [
            f for f in kabupaten_data["features"]
            if f["properties"].get("WADMKK") == selected_kabupaten
        ]
        filtered_geojson = {
            "type": "FeatureCollection",
            "features": filtered_features
        }

        folium.GeoJson(filtered_geojson, name=selected_kabupaten).add_to(m)
        bounds = get_bounds_from_geojson(filtered_geojson)
        m.fit_bounds(bounds)

elif mode == "Provinsi":
    provinsi_list = sorted({
        f["properties"].get("PROVINSI")
        for f in provinsi_data["features"]
        if f["properties"].get("PROVINSI")
    })
    selected_provinsi = st.selectbox("🏛️ Pilih Provinsi:", ["-- Pilih --"] + provinsi_list)

    if selected_provinsi != "-- Pilih --":
        filtered_features = [
            f for f in provinsi_data["features"]
            if f["properties"].get("PROVINSI") == selected_provinsi
        ]
        filtered_geojson = {
            "type": "FeatureCollection",
            "features": filtered_features
        }

        folium.GeoJson(filtered_geojson, name=selected_provinsi).add_to(m)
        bounds = get_bounds_from_geojson(filtered_geojson)
        m.fit_bounds(bounds)

# Tampilkan peta
st_folium(m, width=700, height=500)
