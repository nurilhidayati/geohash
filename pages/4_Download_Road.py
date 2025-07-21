import streamlit as st
import geohash2
import osmnx as ox
import geopandas as gpd
import pandas as pd
from shapely.geometry import Polygon
from streamlit_folium import st_folium
import folium

# Set default highway filters
HIGHWAY_FILTERS = [
    "motorway", "motorway_link", "secondary", "secondary_link",
    "primary", "primary_link", "residential", "trunk", "trunk_link",
    "tertiary", "tertiary_link", "living_street", "service", "unclassified"
]

# Approximate geohash-6 cell size in degrees
LAT_HEIGHT = 0.0055
LON_WIDTH = 0.011

st.title("🚗 OSM Road Downloader from Geohash-6 List")

# Input geohashes
geohash_input = st.text_area("Enter list of Geohash-6 (one per line):", height=200)

# Download button
if st.button("Download Roads"):
    geohash_list = [gh.strip() for gh in geohash_input.strip().splitlines() if gh.strip()]

    if not geohash_list:
        st.warning("❗ Please enter at least one geohash.")
    else:
        st.info("🔄 Downloading data from OSM...")
        all_roads_list = []

        for gh in geohash_list:
            try:
                lat_str, lon_str = geohash2.decode(gh)
                lat = float(lat_str)
                lon = float(lon_str)

                lat_min = lat - LAT_HEIGHT / 2
                lat_max = lat + LAT_HEIGHT / 2
                lon_min = lon - LON_WIDTH / 2
                lon_max = lon + LON_WIDTH / 2

                bounds_polygon = Polygon([
                    (lon_min, lat_min),
                    (lon_max, lat_min),
                    (lon_max, lat_max),
                    (lon_min, lat_max),
                    (lon_min, lat_min)
                ])

                G = ox.graph_from_polygon(bounds_polygon, network_type='all')
                edges = ox.graph_to_gdfs(G, nodes=False)

                def match_highway(hw):
                    if isinstance(hw, list):
                        return any(h in HIGHWAY_FILTERS for h in hw)
                    return hw in HIGHWAY_FILTERS

                filtered = edges[edges['highway'].apply(match_highway)]
                if not filtered.empty:
                    all_roads_list.append(filtered)

            except Exception as e:
                st.error(f"❌ Error processing geohash '{gh}': {e}")

        if all_roads_list:
            all_roads = pd.concat(all_roads_list).reset_index(drop=True)

            # Show map
            try:
                center_lat, center_lon = geohash2.decode(geohash_list[0])
                m = folium.Map(location=[float(center_lat), float(center_lon)], zoom_start=14)
                folium.GeoJson(all_roads).add_to(m)

                st.subheader("🗺️ Map View of Extracted Roads")
                st_folium(m, width=700, height=500)
            except Exception as map_error:
                st.warning(f"⚠️ Could not render map: {map_error}")

            # Export to file
            output_file = "roads_from_geohash6.gpkg"
            try:
                all_roads.to_file(output_file, layer='roads', driver="GPKG")
                st.success(f"✅ Downloaded and saved {len(all_roads)} road segments.")
                with open(output_file, "rb") as f:
                    st.download_button("📥 Download Result", f, file_name=output_file)
            except Exception as file_error:
                st.error(f"❌ Failed to save output: {file_error}")
        else:
            st.warning("⚠️ No road data found for the provided geohashes.")
