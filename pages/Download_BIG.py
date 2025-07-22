import streamlit as st
import requests
import geopandas as gpd
from shapely.geometry import shape
from io import BytesIO

# URL for the MapServer layer query endpoint
BASE_URL = "https://geoservices.big.go.id/rbi/rest/services/BATASWILAYAH/Administrasi_AR_KabKota_50K/MapServer/0/query"

def fetch_geojson(where_clause="1=1"):
    """
    Fetch GeoJSON data from BIG MapServer with optional SQL-like WHERE clause filter.
    """
    params = {
        "where": where_clause,
        "outFields": "*",
        "f": "geojson",
        "returnGeometry": "true",
    }
    response = requests.get(BASE_URL, params=params)
    response.raise_for_status()
    return response.json()

def filter_geojson_by_name(name):
    # Simple case-insensitive filter on 'WADMKC' attribute (Kab/Kota name)
    # You can adjust attribute name if needed (inspect API response)
    name = name.lower()
    geojson = fetch_geojson()
    gdf = gpd.GeoDataFrame.from_features(geojson["features"])
    filtered_gdf = gdf[gdf["WADMKC"].str.lower().str.contains(name)]
    return filtered_gdf.__geo_interface__

st.title("🌏 Download Batas Area Kabupaten/Kota from BIG GeoServices")

name_filter = st.text_input("Filter by Kabupaten/Kota name (optional):")

if st.button("Fetch and Download GeoJSON"):
    try:
        if name_filter.strip():
            filtered_geojson = filter_geojson_by_name(name_filter.strip())
            if len(filtered_geojson['features']) == 0:
                st.warning("No boundaries found matching that name.")
            else:
                geojson_bytes = BytesIO(json.dumps(filtered_geojson).encode("utf-8"))
                st.success(f"Found {len(filtered_geojson['features'])} features matching '{name_filter}'.")
                st.download_button(
                    label="⬇️ Download Filtered GeoJSON",
                    data=geojson_bytes,
                    file_name=f"{name_filter.strip().replace(' ', '_')}_batas_kabkota.geojson",
                    mime="application/geo+json",
                )
        else:
            # Fetch full dataset
            geojson = fetch_geojson()
            geojson_bytes = BytesIO(json.dumps(geojson).encode("utf-8"))
            st.success("Full Kabupaten/Kota boundaries downloaded.")
            st.download_button(
                label="⬇️ Download Full GeoJSON",
                data=geojson_bytes,
                file_name="batas_kabkota_full.geojson",
                mime="application/geo+json",
            )
    except Exception as e:
        st.error(f"Error: {e}")
