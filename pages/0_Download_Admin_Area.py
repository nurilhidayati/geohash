import streamlit as st
import requests
import json
import tempfile
import osm2geojson
import folium
from streamlit_folium import st_folium
import os


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


# --- Streamlit UI ---
st.header("🌍 Download Area Boundary as GeoJSON")

# Initialize session_state
if "geojson_data" not in st.session_state:
    st.session_state.geojson_data = None
if "download_path" not in st.session_state:
    st.session_state.download_path = ""
if "filename" not in st.session_state:
    st.session_state.filename = ""

area_name = st.text_input("Enter area name (e.g., Jakarta, Yogyakarta, etc.)")
custom_filename = st.text_input("Optional: Enter output filename (e.g., jakarta_boundary.geojson)")

if st.button("Download Boundary"):
    if not area_name.strip():
        st.warning("⚠️ Please enter an area name.")
    else:
        with st.spinner("⏳ Processing... Please wait."):
            try:
                final_filename = custom_filename.strip() or f"{area_name.replace(' ', '_')}_boundary.geojson"

                with tempfile.NamedTemporaryFile(delete=False, suffix=".geojson", mode='w') as tmpfile:
                    geojson_data, filepath = download_boundary_geojson(area_name, save_as=tmpfile.name)

                    # Save to session state
                    st.session_state.geojson_data = geojson_data
                    st.session_state.download_path = filepath
                    st.session_state.filename = final_filename

                    st.success("✅ Boundary successfully retrieved!")
            except Exception as e:
                st.error(str(e))

# Map preview
st.subheader("🗺️ Map Preview")

map_location = [-2.5, 117.5]  # default center of Indonesia
m = folium.Map(location=map_location, zoom_start=5)

if st.session_state.geojson_data:
    geojson = st.session_state.geojson_data
    coords = geojson['features'][0]['geometry']['coordinates']
    if geojson['features'][0]['geometry']['type'] == 'Polygon':
        lon, lat = coords[0][0]
    else:
        lon, lat = coords[0][0][0]

    # Update map location
    m.location = [lat, lon]
    m.zoom_start = 10
    folium.GeoJson(geojson, name="Boundary").add_to(m)

st_folium(m, width=700, height=450)

# Always show download button if available
if st.session_state.download_path and os.path.exists(st.session_state.download_path):
    with open(st.session_state.download_path, 'rb') as f:
        st.download_button(
            label="⬇️ Download GeoJSON",
            data=f,
            file_name=st.session_state.filename,
            mime="application/geo+json"
        )
