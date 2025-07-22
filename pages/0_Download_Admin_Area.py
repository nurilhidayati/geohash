import streamlit as st
import requests
import json
import tempfile
import osm2geojson
import folium
from streamlit_folium import st_folium


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

    # Convert to GeoJSON
    geojson = osm2geojson.json2geojson(data)

    # Filter polygon features
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

area_name = st.text_input("Enter area name (e.g., Jakarta, Yogyakarta, etc.)")
custom_filename = st.text_input("Optional: Enter output filename (e.g., jakarta_boundary.geojson)")

# Default map location
map_location = [-2.5, 117.5]  # Center of Indonesia
geojson_data = None  # placeholder

if st.button("Download Boundary"):
    if not area_name.strip():
        st.warning("⚠️ Please enter an area name.")
    else:
        with st.spinner("⏳ Processing... Please wait."):
            try:
                final_filename = custom_filename.strip() or f"{area_name.replace(' ', '_')}_boundary.geojson"

                with tempfile.NamedTemporaryFile(delete=False, suffix=".geojson") as tmpfile:
                    geojson_data, filepath = download_boundary_geojson(area_name, save_as=tmpfile.name)

                    # Get center of first feature for map
                    coords = geojson_data['features'][0]['geometry']['coordinates']
                    if geojson_data['features'][0]['geometry']['type'] == 'Polygon':
                        lon, lat = coords[0][0]
                    else:  # MultiPolygon
                        lon, lat = coords[0][0][0]
                    map_location = [lat, lon]

                    with open(filepath, 'rb') as f:
                        st.success("✅ Boundary ready. Click below to download:")
                        st.download_button(
                            label="⬇️ Download GeoJSON",
                            data=f,
                            file_name=final_filename,
                            mime="application/geo+json"
                        )
            except Exception as e:
                st.error(str(e))

# Always show map
st.subheader("🗺️ Map Preview")

m = folium.Map(location=map_location, zoom_start=5)

if geojson_data:
    folium.GeoJson(geojson_data, name="Boundary").add_to(m)

st_folium(m, width=700, height=450)
