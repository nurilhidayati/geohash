import streamlit as st
import requests
import json

def search_buildings(area_name, keyword):
    """
    Search named buildings in a given area using Overpass API and filter by keyword.
    """
    query = f"""
    [out:json][timeout:60];
    area["name"="{area_name}"]->.searchArea;
    (
      way["building"]["name"](area.searchArea);
      relation["building"]["name"](area.searchArea);
    );
    out tags center;
    """

    response = requests.get("https://overpass-api.de/api/interpreter", params={'data': query})
    if response.status_code != 200:
        raise Exception("Failed to query Overpass API.")

    data = response.json()
    if 'elements' not in data or len(data['elements']) == 0:
        return []

    keyword_lower = keyword.lower()
    results = []
    for el in data['elements']:
        tags = el.get("tags", {})
        name = tags.get("name")
        btype = tags.get("building")
        if name and keyword_lower in name.lower():
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

col1, col2 = st.columns(2)
with col1:
    area_name = st.text_input("Enter area name (e.g., Jakarta, Yogyakarta)")
with col2:
    keyword = st.text_input("Search building name (e.g., PIK)")

if st.button("🔍 Search Buildings"):
    if not area_name.strip() or not keyword.strip():
        st.warning("⚠️ Please fill in both area and building name keyword.")
    else:
        with st.spinner("⏳ Searching building names... Please wait."):
            try:
                results = search_buildings(area_name, keyword)
                if results:
                    st.success(f"✅ Found {len(results)} buildings with keyword '{keyword}' in {area_name}")
                    st.dataframe(results, use_container_width=True)
                else:
                    st.warning(f"No buildings with name like '{keyword}' found in '{area_name}'.")
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
