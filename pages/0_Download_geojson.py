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

st.set_page_config(layout="wide")
st.title("🗺️ Boundary Explorer")

# Siapkan peta dasar
m = folium.Map(location=[-2.5, 117.5], zoom_start=5)

# Buat dua kolom
col1, col2 = st.columns([1, 1])

# --- Kabupaten ---
kab_file = "pages/batas_admin_kabupaten.geojson"
selected_kabupaten = "-- Pilih Kabupaten --"
if os.path.exists(kab_file):
    with open(kab_file, "r", encoding="utf-8") as f:
        kab_geojson = json.load(f)
    kabupaten_list = sorted({f["properties"].get("WADMKK") for f in kab_geojson["features"] if f["properties"].get("WADMKK")})
    with col1:
        selected_kabupaten = st.selectbox("🏙️ Pilih Kabupaten (WADMKK):", ["-- Pilih Kabupaten --"] + kabupaten_list)
else:
    st.error("❌ File 'batas_admin_kabupaten.geojson' tidak ditemukan")

# --- Provinsi ---
prov_file = "pages/batas_admin_provinsi.geojson"
selected_provinsi = "-- Pilih Provinsi --"
if os.path.exists(prov_file):
    with open(prov_file, "r", encoding="utf-8") as f:
        prov_geojson = json.load(f)
    provinsi_list = sorted({f["properties"].get("PROVINSI") for f in prov_geojson["features"] if f["properties"].get("PROVINSI")})
    with col2:
        selected_provinsi = st.selectbox("🏞️ Pilih Provinsi (PROVINSI):", ["-- Pilih Provinsi --"] + provinsi_list)
else:
    st.error("❌ File 'batas_admin_provinsi.geojson' tidak ditemukan")

# Tampilkan kabupaten jika dipilih
if selected_kabupaten != "-- Pilih Kabupaten --":
    filtered_kab = [f for f in kab_geojson["features"] if f["properties"].get("WADMKK") == selected_kabupaten]
    kab_geo = {"type": "FeatureCollection", "features": filtered_kab}
    folium.GeoJson(kab_geo, name="Kabupaten").add_to(m)
    if filtered_kab:
        m.fit_bounds(get_bounds_from_geojson(kab_geo))

# Tampilkan provinsi jika dipilih
if selected_provinsi != "-- Pilih Provinsi --":
    filtered_prov = [f for f in prov_geojson["features"] if f["properties"].get("PROVINSI") == selected_provinsi]
    prov_geo = {"type": "FeatureCollection", "features": filtered_prov}
    folium.GeoJson(prov_geo, name="Provinsi", style_function=lambda x: {"color": "green", "weight": 2}).add_to(m)
    if filtered_prov:
        m.fit_bounds(get_bounds_from_geojson(prov_geo))

# Peta hasil akhir
st_folium(m, width=1200, height=600)
