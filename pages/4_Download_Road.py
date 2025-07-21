import streamlit as st
import geohash2
import osmnx as ox
import geopandas as gpd
import pandas as pd
from shapely.geometry import Polygon

# Set default highway filters
HIGHWAY_FILTERS = [
    "motorway", "motorway_link", "secondary", "secondary_link",
    "primary", "primary_link", "residential", "trunk", "trunk_link",
    "tertiary", "tertiary_link", "living_street", "service", "unclassified"
]

# Approximate geohash-6 cell dimensions (in degrees)
LAT_HEIGHT = 0.61 / 111  # ~0.0055 deg
LON_WIDTH = 1.22 / 111  # ~0.011 deg

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
                lat, lon = geohash2.decode(gh)
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
