import streamlit as st
import requests
import json
import tempfile
import osm2geojson

def download_boundary_geojson(area_name, save_as='boundary.geojson'):
    """
    Downloads the administrative boundary of a given area as a GeoJSON file using Overpass API.
    """
    overpass_url = "https://overpass-api.de/api/interpreter"
    query = f"""
    [out:json];
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

    geojson_data = osm2geojson.json2geojson(data)

    with open(save_as, 'w', encoding='utf-8') as f:
        json.dump(geojson_data, f, ensure_ascii=False, indent=2)

    return geojson_data, save_as


# --- Streamlit UI ---
st.header("🌍 Download Area Boundary as GeoJSON")

area_name = st.text_input("Enter area name (e.g., Jakarta, Yogyakarta, etc.)")
custom_filename = st.text_input("Optional: Enter output filename (e.g., jakarta_boundary.geojson)")

if st.button("Download Boundary"):
    if not area_name.strip():
        st.warning("⚠️ Please enter an area name.")
    else:
        with st.spinner("⏳ Processing... Please wait."):
            try:
                # Fallback if no filename is provided
                final_filename = custom_filename.strip() or f"{area_name.replace(' ', '_')}_boundary.geojson"

                with tempfile.NamedTemporaryFile(delete=False, suffix=".geojson") as tmpfile:
                    geojson_data, filepath = download_boundary_geojson(area_name, save_as=tmpfile.name)

                    with open(filepath, 'rb') as f:
                        st.download_button(
                            "⬇️ Download GeoJSON",
                            f,
                            file_name=final_filename,
                            mime="application/geo+json"
                        )
            except Exception as e:
                st.error(str(e))
