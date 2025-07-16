import streamlit as st
import requests
import json
import tempfile
import osm2geojson


def search_buildings(area_name):
    """
    Search buildings by name in a given area using Overpass API.
    """
    query = f"""
    [out:json][timeout:60];
    area["name"="{area_name}"]->.searchArea;
    (
      way["building"](area.searchArea);
      relation["building"](area.searchArea);
    );
    out tags center;
    """

    response = requests.get("https://overpass-api.de/api/interpreter", params={'data': query})
    if response.status_code != 200:
        raise Exception("Failed to query Overpass API.")

    data = response.json()
    if 'elements' not in data or len(data['elements']) == 0:
        return []

    results = []
    for el in data['elements']:
        tags = el.get("tags", {})
        name = tags.get("name")
        btype = tags.get("building")
        if name:
            results.append({
                "name": name,
                "type": btype or "unknown",
                "lat": el.get("lat") or el.get("center", {}).get("lat"),
                "lon": el.get("lon") or el.get("center", {}).get("lon")
            })
    return results


# ============ STREAMLIT UI ==============

st.set_page_config(page_title="OSM Building Search", layout="wide")
st.title("🏢 Search Named Buildings in OSM")

area_name = st.text_input("Enter area name (e.g., Jakarta, Yogyakarta, etc.)")

if st.button("🔍 Search Buildings"):
    if not area_name.strip():
        st.warning("⚠️ Please enter a valid area name.")
    else:
        with st.spinner("⏳ Searching building names... Please wait."):
            try:
                results = search_buildings(area_name)
                if results:
                    st.success(f"✅ Found {len(results)} named buildings in {area_name}")
                    st.dataframe(results, use_container_width=True)
                else:
                    st.warning(f"No named buildings found in '{area_name}'.")
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
