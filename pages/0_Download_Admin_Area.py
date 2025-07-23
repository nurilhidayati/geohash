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

# Setup
st.set_page_config(layout="wide")
st.title("🗺️ Download Boundary")

# Siapkan default map
m = folium.Map(location=[-2.5, 117.5], zoom_start=5)

# File kabupaten dan provinsi
kab_file = "pages/batas_admin_kabupaten.geojson"
prov_file = "pages/batas_admin_provinsi.geojson"

# Load GeoJSON
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

# Inisialisasi session_state
for key in ["selected_kabupaten", "selected_provinsi", "has_searched", "geojson_result"]:
    if key not in st.session_state:
        st.session_state[key] = None if key != "has_searched" else False

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

# Tombol cari & download
col_btn1, col_btn2 = st.columns([1, 1])
with col_btn1:
    if st.button("🔍 Cari"):
        if selected_kabupaten != "-- Select Regency --":
            st.session_state.selected_kabupaten = selected_kabupaten
            st.session_state.selected_provinsi = None
            st.session_state.has_searched = True
        elif selected_provinsi != "-- Select Province --":
            st.session_state.selected_provinsi = selected_provinsi
            st.session_state.selected_kabupaten = None
            st.session_state.has_searched = True
        else:
            st.warning("Please select either a district or a province")
            st.session_state.has_searched = False

# Proses hasil pencarian
if st.session_state.has_searched:
    if st.session_state.selected_kabupaten:
        filtered_kab = [
            f for f in kab_geojson["features"]
            if f["properties"].get("WADMKK") == st.session_state.selected_kabupaten
        ]
        kab_geo = {"type": "FeatureCollection", "features": filtered_kab}
        st.session_state.geojson_result = kab_geo
        folium.GeoJson(kab_geo, name="Kabupaten").add_to(m)
        if filtered_kab:
            m.fit_bounds(get_bounds_from_geojson(kab_geo))

    elif st.session_state.selected_provinsi:
        filtered_prov = [
            f for f in prov_geojson["features"]
            if f["properties"].get("PROVINSI") == st.session_state.selected_provinsi
        ]
        prov_geo = {"type": "FeatureCollection", "features": filtered_prov}
        st.session_state.geojson_result = prov_geo
        folium.GeoJson(
            prov_geo,
            name="Provinsi",
            style_function=lambda x: {"color": "green", "weight": 2}
        ).add_to(m)
        if filtered_prov:
            m.fit_bounds(get_bounds_from_geojson(prov_geo))

    # Tombol download muncul di sini
    with col_btn2:
        if st.session_state.geojson_result:
            name = (
                st.session_state.selected_kabupaten or
                st.session_state.selected_provinsi or
                "boundary"
            ).replace(" ", "_").lower()
            filename = f"{name}_boundary.geojson"
            geojson_str = json.dumps(st.session_state.geojson_result, ensure_ascii=False, indent=2)
            st.download_button(
                label="💾 Download Area",
                data=geojson_str,
                file_name=filename,
                mime="application/geo+json"
            )

# Tampilkan map
st_folium(m, width=1200, height=600)

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
