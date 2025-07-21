import streamlit as st
import geohash2
import osmnx as ox
import geopandas as gpd
from shapely.geometry import box

# Set default highway filters
HIGHWAY_FILTERS = [
    "motorway", "motorway_link", "secondary", "secondary_link",
    "primary", "primary_link", "residential", "trunk", "trunk_link",
    "tertiary", "tertiary_link", "living_street", "service", "unclassified"
]

st.title("OSM Road Downloader from Geohash List")

# Input geohashes
geohash_input = st.text_area("Enter list of Geohashes (one per line):")

# Download button
if st.button("Download Roads"):
    geohash_list = geohash_input.strip().splitlines()

    if not geohash_list:
        st.warning("Please enter at least one geohash.")
    else:
        st.info("Downloading data...")

        all_roads = gpd.GeoDataFrame()

        for gh in geohash_list:
            try:
                lat, lon = geohash2.decode(gh)
                precision = len(gh)
                bbox = geohash2.bbox(gh)
                bounds = box(bbox['w'], bbox['s'], bbox['e'], bbox['n'])

                # Use osmnx to get road network by bounding box
                graph = ox.graph_from_polygon(bounds, network_type='all')
                edges = ox.graph_to_gdfs(graph, nodes=False)

                # Filter by highway tag
                filtered = edges[edges['highway'].isin(HIGHWAY_FILTERS)]
                all_roads = pd.concat([all_roads, filtered])

            except Exception as e:
                st.error(f"Error processing geohash {gh}: {e}")

        if not all_roads.empty:
            # Save to GeoPackage (or any format you want)
            output_file = "roads_from_geohash.gpkg"
            all_roads.to_file(output_file, layer='roads', driver="GPKG")
            st.success(f"Downloaded and saved {len(all_roads)} roads.")
            with open(output_file, "rb") as f:
                st.download_button("Download Result", f, file_name=output_file)
        else:
            st.warning("No road data found for the input geohashes.")
