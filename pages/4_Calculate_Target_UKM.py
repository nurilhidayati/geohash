import streamlit as st
import osmnx as ox
import geopandas as gpd
import pandas as pd
import io
import geohash2
import json
from shapely.geometry import box

st.set_page_config(page_title="🛣️ Calculate Target UKM", layout="wide")
st.title("🛣️ Calculate Target UKM")

uploaded_file = st.file_uploader("📄 Upload GeoJSON or CSV with `geoHash` column", type=["csv", "geojson", "json"])

def geohash_to_polygon(gh):
    if len(gh) != 6:
        raise ValueError("Geohash must be 6 characters long.")
    lat, lon, lat_err, lon_err = geohash2.decode_exactly(gh)
    return box(lon - lon_err, lat - lat_err, lon + lon_err, lat + lat_err)

def download_clipped_roads_from_geohashes(geohash_list):
    all_roads = gpd.GeoDataFrame()
    tags = {
        "highway": [
            "motorway", "motorway_link", "secondary", "secondary_link",
            "primary", "primary_link", "residential", "trunk", "trunk_link",
            "tertiary", "tertiary_link", "living_street", "service", "unclassified"
        ]
    }

    for gh in geohash_list:
        try:
            polygon = geohash_to_polygon(gh)
            gdf_all = ox.features_from_polygon(polygon, tags=tags)

            if gdf_all.empty:
                st.warning(f"⚠️ No road features in geohash {gh}")
                continue

            gdf_lines = gdf_all[gdf_all.geometry.type.isin(["LineString", "MultiLineString"])]
            gdf_clipped = gpd.clip(gdf_lines, polygon)

            if gdf_clipped.empty:
                st.warning(f"⚠️ No clipped roads inside geohash {gh}")
                continue

            all_roads = pd.concat([all_roads, gdf_clipped])

        except Exception as e:
            st.warning(f"⚠️ Failed to fetch for geohash {gh}: {e}")
    return all_roads.reset_index(drop=True)

if uploaded_file and st.button("🗂️ Calculate UKM (GeoJSON)"):
    try:
        filename = uploaded_file.name.lower()
        # Baca data berdasarkan jenis file
        if filename.endswith(".csv"):
            df = pd.read_csv(uploaded_file)
        elif filename.endswith((".geojson", ".json")):
            gdf = gpd.read_file(uploaded_file)
            if 'geoHash' not in gdf.columns:
                st.error("❌ GeoJSON must contain a 'geoHash' property.")
                st.stop()
            df = pd.DataFrame(gdf.drop(columns='geometry', errors='ignore'))
        else:
            st.error("❌ Unsupported file type.")
            st.stop()

        if 'geoHash' not in df.columns:
            st.error("❌ File must contain a column named 'geoHash'")
        else:
            geohash_list = df['geoHash'].dropna().astype(str).str.strip()
            geohash_list = geohash_list[geohash_list.str.len() == 6].unique().tolist()

            if not geohash_list:
                st.warning("⚠️ No valid 6-character geohashes found.")
            else:
                st.info(f"🔍 Fetching clipped roads from {len(geohash_list)} geohash6 areas...")
                gdf_roads = download_clipped_roads_from_geohashes(geohash_list)

                if gdf_roads.empty:
                    st.warning("⚠️ No roads found inside all geohashes.")
                else:
                    gdf_roads_metric = gdf_roads.to_crs(epsg=3857)
                    total_length_km = gdf_roads_metric.length.sum() / 1000

                    st.success(f"✅ {len(gdf_roads)} clipped road segments found.")
                    st.info(f"🧮 Total road length: **{total_length_km:.2f} km**")

                    gdf_roads = gdf_roads.to_crs(epsg=4326)
                    buffer = io.BytesIO()
                    gdf_roads.to_file(buffer, driver="GeoJSON")
                    buffer.seek(0)
                    st.download_button("⬇️ Download Roads", buffer, "roads_inside_geohash.geojson", "application/geo+json")

    except Exception as e:
        st.error(f"❌ Unexpected error: {e}")
