import streamlit as st
import requests
import json
import tempfile
import osm2geojson


def download_building_geojson(area_name, save_as='buildings.geojson'):
    """
    Downloads building polygons from OpenStreetMap for a given area using Overpass API.
    """
    overpass_url = "https://overpass-api.de/api/interpreter"
    query = f"""
    [out:json][timeout:60];
    area["name"="{area_name}"]->.searchArea;
    (
      way["building"](area.searchArea);
      relation["building"](area.searchArea);
    );
    out body;
    >;
    out skel qt;
    """

    response = requests.get(overpass_url, params={'data': query})
    if response.status_code != 200:
        raise Exception("Failed to query Overpass API.")

    data = response.json()
    if 'elements' not in data or len(data['elements']) == 0:
        raise ValueError(f"No building data found for '{area_name}'.")

    geojson = osm2geojson.json2geojson(data)

    # Filter only Polygon/MultiPolygon features
    features = [
        feat for feat in geojson['features']
        if feat['geometry']['type'] in ['Polygon', 'MultiPolygon']
    ]

    if not features:
        raise ValueError(f"No polygon building features found for '{area_name}'.")

    geojson_filtered = {
        "type": "FeatureCollection",
        "features": features
    }

    with open(save_as, 'w', encoding='utf-8') as f:
        json.dump(geojson_filtered, f, ensure_ascii=False, indent=2)

    return geojson_filtered, save_as
# --- Streamlit UI ---
st.header("🏢 Download Building Footprints from OpenStreetMap")

area_name = st.text_input("Enter area name (e.g., Jakarta, Yogyakarta, etc.)")
custom_filename = st.text_input("Optional: Enter output filename (e.g., jakarta_buildings.geojson)")

if st.button("Download Buildings"):
    if not area_name.strip():
        st.warning("⚠️ Please enter an area name.")
    else:
        with st.spinner("⏳ Processing... Please wait."):
            try:
                final_filename = custom_filename.strip() or f"{area_name.replace(' ', '_')}_buildings.geojson"

                with tempfile.NamedTemporaryFile(delete=False, suffix=".geojson") as tmpfile:
                    geojson_data, filepath = download_building_geojson(area_name, save_as=tmpfile.name)

                    with open(filepath, 'rb') as f:
                        st.success("✅ Building data ready. Click below to download:")
                        st.download_button(
                            label="⬇️ Download GeoJSON",
                            data=f,
                            file_name=final_filename,
                            mime="application/geo+json"
                        )
            except Exception as e:
                st.error(str(e))
