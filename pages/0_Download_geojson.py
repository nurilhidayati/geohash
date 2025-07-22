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

# Siapkan default map
m = folium.Map(location=[-2.5, 117.5], zoom_start=5)

# File kabupaten dan provinsi
kab_file = "pages/batas_admin_kabupaten.geojson"
prov_file = "pages/batas_admin_provinsi.geojson"

# Load GeoJSON
kab_geojson = None
prov_geojson = None

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

# Setup kolom dan dropdown
col1, col2 = st.columns([1, 1])

selected_kabupaten = None
selected_provinsi = None

with col1:
    if kab_geojson:
        kabupaten_list = sorted({f["properties"].get("WADMKK") for f in kab_geojson["features"] if f["properties"].get("WADMKK")})
        selected_kabupaten = st.selectbox("🏙️ Pilih Kabupaten (WADMKK):", ["-- Pilih Kabupaten --"] + kabupaten_list)

with col2:
    if prov_geojson:
        provinsi_list = sorted({f["properties"].get("PROVINSI") for f in prov_geojson["features"] if f["properties"].get("PROVINSI")})
        selected_provinsi = st.selectbox("🏞️ Pilih Provinsi (PROVINSI):", ["-- Pilih Provinsi --"] + provinsi_list)

# Tombol cari
search = st.button("🔍 Cari")

# Logika jika tombol diklik
if search:
    # Jika kabupaten dipilih, reset provinsi
    if selected_kabupaten and selected_kabupaten != "-- Pilih Kabupaten --":
        selected_provinsi = None

        filtered_kab = [f for f in kab_geojson["features"] if f["properties"].get("WADMKK") == selected_kabupaten]
        kab_geo = {"type": "FeatureCollection", "features": filtered_kab}
        folium.GeoJson(kab_geo, name="Kabupaten").add_to(m)
        if filtered_kab:
            m.fit_bounds(get_bounds_from_geojson(kab_geo))

    # Jika provinsi dipilih, reset kabupaten
    elif selected_provinsi and selected_provinsi != "-- Pilih Provinsi --":
        selected_kabupaten = None

        filtered_prov = [f for f in prov_geojson["features"] if f["properties"].get("PROVINSI") == selected_provinsi]
        prov_geo = {"type": "FeatureCollection", "features": filtered_prov}
        folium.GeoJson(prov_geo, name="Provinsi", style_function=lambda x: {"color": "green", "weight": 2}).add_to(m)
        if filtered_prov:
            m.fit_bounds(get_bounds_from_geojson(prov_geo))
    else:
        st.warning("Silakan pilih salah satu: kabupaten **atau** provinsi")

# Tampilkan map
st_folium(m, width=1200, height=600)
