import streamlit as st
import requests
import json
import tempfile

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

    # Use a tool-free way to convert to GeoJSON using OSM format with geometry
    from geojson import Feature, FeatureCollection, MultiPolygon
    import shapely.geometry as sg
    import osm2geojson

    geojson_data = osm2geojson.json2geojson(data)

    with open(save_as, 'w', encoding='utf-8') as f:
        json.dump(geojson_data, f, ensure_ascii=False, indent=2)

    return geojson_data, save_as

st.header("🌍 Download Area Boundary as GeoJSON")

area_name = st.text_input("Enter area name (e.g., Jakarta, Yogyakarta, etc.)")

if st.button("Download Boundary"):
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".geojson") as tmpfile:
            geojson_data, filepath = download_boundary_geojson(area_name, save_as=tmpfile.name)
            with open(filepath, 'rb') as f:
                st.download_button("⬇️ Download GeoJSON", f, file_name=f"{area_name}_boundary.geojson", mime="application/geo+json")
    except Exception as e:
        st.error(str(e))
