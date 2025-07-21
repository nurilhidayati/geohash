import streamlit as st
import geohash2
import osmnx as ox
import geopandas as gpd
import pandas as pd
from shapely.geometry import box, Polygon

# Set default highway filters
HIGHWAY_FILTERS = [
    "motorway", "motorway_link", "secondary", "secondary_link",
    "primary", "primary_link", "residential", "trunk", "trunk_link",
    "tertiary", "tertiary_link", "living_street", "service", "unclassified"
]

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
        all_roads = gpd.GeoDataFrame()

        for gh in geohash_list:
            try:
                bbox = geohash2.bbox(gh)
                bounds_polygon = Polygon([
                    (bbox['w'], bbox['s']),
                    (bbox['e'], bbox['s']),
                    (bbox['e'], bbox['n']),
                    (bbox['w'], bbox['n']),
                    (bbox['w'], bbox['s'])
                ])

                # Download road network inside bounding polygon
                G = ox.graph_from_polygon(bounds_polygon, network_type='all')
                edges = ox.graph_to_gdfs(G, nodes=False)

                # Normalize highway tags to lists for filtering
                def match_highway(hw):
                    if isinstance(hw, list):
                        return any(h in HIGHWAY_FILTERS for h in hw)
                    return hw in HIGHWAY_FILTERS

                filtered = edges[edges['highway'].apply(match_highway)]
                all_roads = pd.concat([all_roads, filtered])

            except Exception as e:
                st.error(f"❌ Error processing geohash {gh}: {e}")

        if not all_roads.empty:
            all_roads = all_roads.reset_index(drop=True)
            output_file = "roads_from_geohash6.gpkg"
            all_roads.to_file(output_file, layer='roads', driver="GPKG")
            st.success(f"✅ Downloaded and saved {len(all_roads)} road segments.")
            with open(output_file, "rb") as f:
                st.download_button("📥 Download Result", f, file_name=output_file)
        else:
            st.warning("⚠️ No road data found for the provided geohashes.")
