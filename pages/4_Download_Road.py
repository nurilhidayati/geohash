import streamlit as st
import osmnx as ox
import geopandas as gpd
import pandas as pd
import io
import geohash2  # ✅ PENTING: yang benar, bukan geoHash2
from shapely.geometry import box

st.title("🗺️ Restricted Area & Road Downloader")

# 👉 Upload file berisi geoHash
uploaded_file = st.file_uploader("Upload CSV with geoHash column", type=["csv"])

# Fungsi bantu: Decode geoHash ke polygon
def geohash_to_polygon(gh):  # ✅ gunakan nama modul geohash2, bukan geoHash2
    lat, lon, lat_err, lon_err = geohash2.decode_exactly(gh)
    return box(lon - lon_err, lat - lat_err, lon + lon_err, lat + lat_err)

# Fungsi utama: Download jalan terbatas (LineString)
def download_restricted_roads_from_geohashes(geohash_list):
    tags = {
        "access": ["private", "no", "military", "customers", "permit"],
        "highway": ["service"],
        "service": True,
        "barrier": ["gate", "fence", "bollard"],
        "military": True,
        "landuse": ["military", "industrial", "government"]
    }

    all_roads = gpd.GeoDataFrame()
    for gh in geohash_list:
        try:
            polygon = geohash_to_polygon(gh)
            gdf = ox.features.features_from_polygon(polygon, tags=tags)
            gdf = gdf[gdf.geometry.type.isin(["LineString", "MultiLineString"])]
            all_roads = pd.concat([all_roads, gdf])
        except Exception as e:
            st.warning(f"⚠️ Failed to fetch for geohash {gh}: {e}")
    all_roads = all_roads.reset_index(drop=True)
    return all_roads

# Tombol download roads
if uploaded_file and st.button("🚧 Download Restricted Roads (GeoJSON)"):
    try:
        df = pd.read_csv(uploaded_file)
        if 'geoHash' not in df.columns:
            st.error("❌ CSV must contain a 'geoHash' column.")
        else:
            geohash_list = df['geoHash'].dropna().unique().tolist()
            st.info("Fetching restricted roads from geohashes...")
            gdf_roads = download_restricted_roads_from_geohashes(geohash_list)
            if gdf_roads.empty:
                st.warning("⚠️ No roads found in the selected geohashes.")
            else:
                gdf_roads = gdf_roads.to_crs(epsg=4326)
                buffer = io.BytesIO()
                gdf_roads.to_file(buffer, driver="GeoJSON")
                buffer.seek(0)
                st.success(f"✅ {len(gdf_roads)} restricted roads found")
                st.download_button("⬇️ Download Roads", buffer, "restricted_roads.geojson", "application/geo+json")
                # Map preview
                gdf_roads["lon"] = gdf_roads.geometry.centroid.x
                gdf_roads["lat"] = gdf_roads.geometry.centroid.y
                st.map(gdf_roads[["lat", "lon"]])
    except Exception as e:
        st.error(f"❌ Error: {e}")
