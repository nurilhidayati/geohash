import streamlit as st
import osmnx as ox
import geopandas as gpd
import pandas as pd
import io
import geohash2
from shapely.geometry import box

st.title("🛣️ All Roads Downloader (GeoHash6 Based)")

uploaded_file = st.file_uploader("📄 Upload CSV with `geoHash` column (length 6)", type=["csv"])

def geohash_to_polygon(gh):
    if len(gh) != 6:
        raise ValueError("Geohash must be 6 characters long.")
    lat, lon, lat_err, lon_err = geohash2.decode_exactly(gh)
    return box(lon - lon_err, lat - lat_err, lon + lon_err, lat + lat_err)

def download_all_roads_from_geohashes(geohash_list):
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
            gdf_filtered = gdf_lines[gdf_lines.intersects(polygon)]

            if gdf_filtered.empty:
                st.warning(f"⚠️ No road geometries intersect with geohash {gh}")
                continue

            all_roads = pd.concat([all_roads, gdf_filtered])

        except Exception as e:
            st.warning(f"⚠️ Failed to fetch for geohash {gh}: {e}")
    return all_roads.reset_index(drop=True)


if uploaded_file and st.button("🗂️ Download All Roads (GeoJSON)"):
    try:
        df = pd.read_csv(uploaded_file)
        if 'geoHash' not in df.columns:
            st.error("❌ CSV must contain a column named 'geoHash'")
        else:
            geohash_list = df['geoHash'].dropna().astype(str).str.strip()
            geohash_list = geohash_list[geohash_list.str.len() == 6].unique().tolist()

            if not geohash_list:
                st.warning("⚠️ No valid 6-character geohashes found.")
            else:
                st.info(f"🔍 Fetching roads from {len(geohash_list)} geohash6 areas...")
                gdf_roads = download_all_roads_from_geohashes(geohash_list)

                if gdf_roads.empty:
                    st.warning("⚠️ No roads found in all geohashes.")
                else:
                    gdf_roads = gdf_roads.to_crs(epsg=4326)
                    buffer = io.BytesIO()
                    gdf_roads.to_file(buffer, driver="GeoJSON")
                    buffer.seek(0)
                    st.success(f"✅ {len(gdf_roads)} road segments found.")
                    st.download_button("⬇️ Download Roads", buffer, "all_roads.geojson", "application/geo+json")

                    gdf_roads["lon"] = gdf_roads.geometry.centroid.x
                    gdf_roads["lat"] = gdf_roads.geometry.centroid.y
                    st.map(gdf_roads[["lat", "lon"]])
    except Exception as e:
        st.error(f"❌ Unexpected error: {e}")
