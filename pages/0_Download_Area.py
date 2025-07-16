import streamlit as st
import requests
import json
from osmtogeojson import osmtogeojson  # ✅ correct function

def download_boundary_geojson(area_name, save_as='boundary.geojson'):
    """
    Downloads the administrative boundary of a given area as a GeoJSON file
    using Overpass API (OpenStreetMap).

    Parameters:
    - area_name (str): Name of the city, region, or area.
    - save_as (str): Output filename for the GeoJSON file.

    Returns:
    - dict: GeoJSON content as a dictionary.
    - str: Saved file path.
    """
    query = f"""
    [out:json];
    area["name"="{area_name}"]->.searchArea;
    (
      relation["boundary"="administrative"](area.searchArea);
    );
    out ids;
    """

    response = requests.get("https://overpass-api.de/api/interpreter", params={'data': query})
    data = response.json()

    if not data['elements']:
        raise ValueError(f"Area '{area_name}' not found in OSM.")

    relation_id = data['elements'][0]['id']
    geojson_query = f"""
    [out:json][timeout:25];
    relation({relation_id});
    out body;
    >;
    out skel qt;
    """

    response = requests.get("https://overpass-api.de/api/interpreter", params={'data': geojson_query})
    if response.status_code != 200:
        raise ConnectionError("Failed to fetch boundary data.")

    geojson_data = osmtogeojson(response.json())  # ✅ Use the correct function

    with open(save_as, 'w', encoding='utf-8') as f:
        json.dump(geojson_data, f, ensure_ascii=False, indent=2)

    return geojson_data, save_as

# --- Streamlit App ---
st.header("🌍 Download Area Boundary as GeoJSON")

area_name = st.text_input("Enter area name (e.g., Jakarta, Yogyakarta, etc.)")

if st.button("Download Boundary"):
    try:
        geojson_data, filepath = download_boundary_geojson(area_name)
        with open(filepath, 'rb') as f:
            st.download_button("⬇️ Download GeoJSON", f, file_name=filepath, mime="application/geo+json")
    except Exception as e:
        st.error(str(e))
