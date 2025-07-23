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
@st.cache_data(show_spinner="⏳ Processing GeoHash...")
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

    # Gunakan linspace untuk kurangi jumlah iterasi (lebih cepat)
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

# Setup
st.set_page_config(layout="wide")
st.title("🗺️ Download GeoHash")

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

# === Dropdown dan Tombol Cari dalam satu baris ===
# === 3 kolom utama: Regency, Province, dan tombol Cari ===
col1, col2, col3 = st.columns([2, 2, 1])

# === Regency Dropdown + Clear Button ===
with col1:
    subcol1, subcol2 = st.columns([5, 1])
    with subcol1:
        selected_kabupaten = None
        if kab_geojson:
            kabupaten_list = sorted({f["properties"].get("WADMKK") for f in kab_geojson["features"] if f["properties"].get("WADMKK")})
            selected_kabupaten = st.selectbox(
                "🏙️ Select Regency:",
                ["-- Select Regency --"] + kabupaten_list,
                key="regency_select"
            )
    with subcol2:
        st.markdown("###### ")  # Spacer
        if st.button("❌", key="clear_regency"):
            st.session_state["regency_select"] = "-- Select Regency --"

# === Province Dropdown + Clear Button ===
with col2:
    subcol3, subcol4 = st.columns([5, 1])
    with subcol3:
        selected_provinsi = None
        if prov_geojson:
            provinsi_list = sorted({f["properties"].get("PROVINSI") for f in prov_geojson["features"] if f["properties"].get("PROVINSI")})
            selected_provinsi = st.selectbox(
                "🏞️ Select Province:",
                ["-- Select Province --"] + provinsi_list,
                key="province_select"
            )
    with subcol4:
        st.markdown("###### ")  # Spacer
        if st.button("❌", key="clear_province"):
            st.session_state["province_select"] = "-- Select Province --"

# === Tombol Cari Sejajar ===
with col3:
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("🔍 Cari"):
        if st.session_state.get("regency_select") and st.session_state["regency_select"] != "-- Select Regency --":
            st.session_state.selected_kabupaten = st.session_state["regency_select"]
            st.session_state.selected_provinsi = None
            st.session_state.has_searched = True
        elif st.session_state.get("province_select") and st.session_state["province_select"] != "-- Select Province --":
            st.session_state.selected_provinsi = st.session_state["province_select"]
            st.session_state.selected_kabupaten = None
            st.session_state.has_searched = True
        else:
            st.warning("Please select either a district or a province")
            st.session_state.has_searched = False



# Proses hasil pencarian
if st.session_state.has_searched:
    selected_geojson = None
    layer_name = ""

    if st.session_state.selected_kabupaten:
        filtered_kab = [
            f for f in kab_geojson["features"]
            if f["properties"].get("WADMKK") == st.session_state.selected_kabupaten
        ]
        selected_geojson = {"type": "FeatureCollection", "features": filtered_kab}
        layer_name = st.session_state.selected_kabupaten
        if filtered_kab:
            m.fit_bounds(get_bounds_from_geojson(selected_geojson))

    elif st.session_state.selected_provinsi:
        filtered_prov = [
            f for f in prov_geojson["features"]
            if f["properties"].get("PROVINSI") == st.session_state.selected_provinsi
        ]
        selected_geojson = {"type": "FeatureCollection", "features": filtered_prov}
        layer_name = st.session_state.selected_provinsi
        if filtered_prov:
            m.fit_bounds(get_bounds_from_geojson(selected_geojson))

    st.session_state.geojson_result = selected_geojson

    if selected_geojson:
        name = layer_name.replace(" ", "_").lower()

        # Generate GeoHash
        geohashes = geojson_to_geohash6(selected_geojson)
        geohash_geojson = geohash6_to_geojson(geohashes)

        # ✅ Tampilkan hanya GeoHash di peta
        folium.GeoJson(
            geohash_geojson,
            name="GeoHash6",
            style_function=lambda x: {"color": "#ff6600", "weight": 1, "fillOpacity": 0.3}
        ).add_to(m)

        # === Tombol download
        with col1:
            # Download geohash
            geohash_str = json.dumps(geohash_geojson, ensure_ascii=False, indent=2)
            st.download_button(
                label="📥 Download GeoHash6",
                data=geohash_str,
                file_name=f"{name}_geohash6.geojson",
                mime="application/geo+json"
            )
        with col2:
            geohash_csv = geohash_to_csv(geohashes)
            st.download_button(
                label="📄 Download GeoHash6 CSV",
                data=geohash_csv,
                file_name=f"{name}_geohash6.csv",
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
