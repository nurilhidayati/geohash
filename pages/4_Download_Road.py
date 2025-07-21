import streamlit as st
import osmnx as ox
import geopandas as gpd
import pandas as pd
from shapely.geometry import Polygon, MultiPolygon
from streamlit_folium import st_folium
import folium

# Set default highway filters
HIGHWAY_FILTERS = [
    "motorway", "motorway_link", "secondary", "secondary_link",
    "primary", "primary_link", "residential", "trunk", "trunk_link",
    "tertiary", "tertiary_link", "living_street", "service", "unclassified"
]

st.title("📍 OSM Road Downloader from GeoJSON Upload")

# Upload GeoJSON
uploaded_file = st.file_uploader("Upload a GeoJSON file with polygon geometries:", type=["geojson", "json"])

# Trigger download processing
if uploaded_file and st.button("Download Roads"):
    try:
        gdf = gpd.read_file(uploaded_file)

        if gdf.empty:
            st.warning("⚠️ The uploaded GeoJSON is empty.")
        elif not gdf.geometry.is_valid.all():
            st.error("❌ Some geometries are invalid.")
        else:
            st.info("🔄 Downloading road data from OSM...")
            all_roads_list = []

            for i, geom in enumerate(gdf.geometry):
                if geom.is_empty or not isinstance(geom, (Polygon, MultiPolygon)):
                    st.warning(f"⚠️ Skipping geometry {i}: empty or unsupported type.")
                    continue

                try:
                    G = ox.graph_from_polygon(geom, network_type='all', simplify=True)
                    if len(G.nodes) == 0:
                        st.warning(f"⚠️ No roads found in geometry {i}. Skipping.")
                        continue

                    edges = ox.graph_to_gdfs(G, nodes=False)

                    # Filter roads
                    def match_highway(hw):
                        if isinstance(hw, list):
                            return any(h in HIGHWAY_FILTERS for h in hw)
                        return hw in HIGHWAY_FILTERS

                    filtered = edges[edges['highway'].apply(match_highway)]
                    if not filtered.empty:
                        all_roads_list.append(filtered)
                except Exception as e:
                    st.warning(f"⚠️ Could not download roads for geometry {i}: {e}")
                    continue

            if all_roads_list:
                all_roads = pd.concat(all_roads_list).reset_index(drop=True)

                # Calculate total road length in kilometers
                all_roads_metric = all_roads.to_crs(epsg=3857)  # Project to metric CRS
                all_roads_metric["length_m"] = all_roads_metric.geometry.length
                total_length_km = all_roads_metric["length_m"].sum() / 1000

                st.success(f"✅ Found {len(all_roads)} road segments.")
                st.info(f"🧮 Total Road Length: **{total_length_km:.2f} km**")
                st.dataframe(all_roads[['name', 'highway', 'geometry']].head(10))

                # Map view
                try:
                    centroid = gdf.geometry.centroid.iloc[0]
                    m = folium.Map(location=[centroid.y, centroid.x], zoom_start=14)
                    folium.GeoJson(all_roads, name="Roads").add_to(m)

                    st.subheader("🗺️ Map View of Extracted Roads")
                    st_folium(m, width=700, height=500)
                except Exception as map_error:
                    st.warning(f"⚠️ Could not render map: {map_error}")

                # Export
                output_file = "roads_from_geojson.gpkg"
                try:
                    all_roads.to_file(output_file, layer='roads', driver="GPKG")
                    with open(output_file, "rb") as f:
                        st.download_button("📥 Download Result (.gpkg)", f, file_name=output_file)
                except Exception as file_error:
                    st.error(f"❌ Failed to save output: {file_error}")
            else:
                st.warning("⚠️ No road data found in the uploaded area.")

    except Exception as load_error:
        st.error(f"❌ Failed to read uploaded file: {load_error}")
