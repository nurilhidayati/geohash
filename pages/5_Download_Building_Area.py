import streamlit as st
import requests
import json
import osm2geojson

@st.cache_data(ttl=3600)
def fetch_all_buildings(area_name):
    """
    Fetch all building data (not filtered yet) from Overpass.
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

# ============ Streamlit UI ==============
st.set_page_config(page_title="OSM Building Finder", layout="wide")
st.title("🏢 Search Buildings by Partial Name in OpenStreetMap")

col1, col2 = st.columns(2)
with col1:
    area_name = st.text_input("Enter area (e.g., Jakarta, Tangerang):", value="Jakarta")
with col2:
    name_query = st.text_input("Search building name (e.g., PIK):")

if st.button("🔍 Search"):
    if not area_name.strip():
        st.warning("⚠️ Area name required.")
    else:
        with st.spinner("⏳ Fetching and filtering buildings..."):
            try:
                buildings = fetch_all_buildings(area_name)

                # Filter locally using partial match (case-insensitive)
                if name_query.strip():
                    buildings = [
                        b for b in buildings if name_query.lower() in b["name"].lower()
                    ]

                if buildings:
                    st.success(f"✅ Found {len(buildings)} building(s) matching your search.")
                    st.dataframe(buildings, use_container_width=True)
                else:
                    st.warning("No buildings matched your search.")
            except Exception as e:
                st.error(str(e))
