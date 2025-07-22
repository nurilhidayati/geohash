import streamlit as st
import requests
import json
import tempfile
import osm2geojson
import folium
from streamlit_folium import st_folium
import os


@st.cache_data(ttl=86400)
def get_all_kabupaten_names():
    overpass_url = "https://overpass-api.de/api/interpreter"
    query = """
    [out:json][timeout:60];
    area["name"="Indonesia"]->.indonesia;
    (
      relation["boundary"="administrative"]["admin_level"="6"](area.indonesia);
    );
    out tags;
    """
    response = requests.get(overpass_url, params={'data': query})
    if response.status_code != 200:
        raise Exception("Failed to fetch kabupaten list from Overpass API.")

    data = response.json()
    names = sorted({el["tags"]["name"] for el in data["elements"] if "tags" in el and "name" in el["tags"]})
    return names


def download_boundary_geojson(area_name, save_as='boundary.geojson'):
    overpass_url = "https://overpass-api.de/api/interpreter"
    query = f"""
    [out:json][timeout:25];
    area["name"="{area_name}"]->.searchArea;
    (
      relation["boundary"="administrative"](area.searchArea);
    );
    out body;
    >;
    out skel qt;
    """

    response = requests.get(overpass_url, params={'data': query})
    if response.status_code != 200:
        raise Exception("Failed to query Overpass API")

    data = response.json()
    if 'elements' not in data or len(data['elements']) == 0:
        raise ValueError(f"No boundary data found for '{area_name}'.")

    geojson = osm2geojson.json2geojson(data)

    features = [feat for feat in geojson['features']
                if feat['geometry']['type'] in ['Polygon', 'MultiPolygon']]

    if not features:
        raise ValueError(f"No polygon boundaries found for '{area_name}'.")

    geojson_filtered = {
        "type": "FeatureCollection",
        "features": features
    }

    with open(save_as, 'w', encoding='utf-8') as f:
        json.dump(geojson_filtered, f, ensure_ascii=False, indent=2)

    return geojson_filtered, save_as


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


# --- Streamlit UI ---
st.header("🌍 Download Kabupaten Boundary (Admin Level 6)")

# Initialize session_state
if "geojson_data" not in st.session_state:
    st.session_state.geojson_data = None
if "download_path" not in st.session_state:
    st.session_state.download_path = ""
if "filename" not in st.session_state:
    st.session_state.filename = ""

# Get all kabupaten names from OSM
with st.spinner("🔍 Fetching kabupaten list..."):
    try:
        kabupaten_names = get_all_kabupaten_names()
    except Exception as e:
        st.error(f"❌ Failed to load kabupaten list: {e}")
        st.stop()

# Select kabupaten from dropdown
selected_kabupaten = st.selectbox("Select a Kabupaten/Kota in Indonesia:", kabupaten_names)

if st.button("⬇️ Download Boundary"):
    with st.spinner("⏳ Downloading boundary data..."):
        try:
            filename = selected_kabupaten.strip().replace(" ", "_").lower() + "_boundary.geojson"

            with tempfile.NamedTemporaryFile(delete=False, suffix=".geojson", mode='w') as tmpfile:
                geojson_data, filepath = download_boundary_geojson(selected_kabupaten, save_as=tmpfile.name)

                # Save to session state
                st.session_state.geojson_data = geojson_data
                st.session_state.download_path = filepath
                st.session_state.filename = filename

                st.success("✅ Boundary successfully retrieved!")
        except Exception as e:
            st.error(str(e))

# Map preview
st.subheader("🗺️ Map Preview")

m = folium.Map(location=[-2.5, 117.5], zoom_start=5)

if st.session_state.geojson_data:
    geojson = st.session_state.geojson_data
    gj = folium.GeoJson(geojson, name="Boundary")
    gj.add_to(m)

    bounds = get_bounds_from_geojson(geojson)
    m.fit_bounds(bounds)

st_folium(m, width=700, height=450)

# Download button
if st.session_state.download_path and os.path.exists(st.session_state.download_path):
    with open(st.session_state.download_path, 'rb') as f:
        st.download_button(
            label="⬇️ Download GeoJSON",
            data=f,
            file_name=st.session_state.filename,
            mime="application/geo+json"
        )
