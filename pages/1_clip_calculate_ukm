import streamlit as st
import geopandas as gpd
from shapely.geometry import LineString, MultiLineString
from io import BytesIO
import os

def clip_roads_by_geohash_from_local(uploaded_geohash_file, roads_path="pages/road_data.geojson"):
    st.info("📥 Membaca file geohash yang diupload...")
    geohash_gdf = gpd.read_file(uploaded_geohash_file).to_crs("EPSG:4326")

    st.info("🛣️ Membaca file jalan lokal...")
    if not os.path.exists(roads_path):
        st.error(f"❌ File jalan tidak ditemukan di path: {roads_path}")
        return

    roads_gdf = gpd.read_file(roads_path).to_crs("EPSG:4326")
    roads_gdf = roads_gdf[roads_gdf.geometry.type.isin(['LineString', 'MultiLineString'])]

    st.info("✂️ Melakukan clip jalan berdasarkan geohash...")
    clipped = gpd.overlay(roads_gdf, geohash_gdf, how='intersection')

    if clipped.empty:
        st.warning("🚫 Tidak ada jalan yang terklip dengan geohash.")
        return

    st.info("📏 Menghitung panjang jalan...")
    clipped = clipped.to_crs("EPSG:3857")
    clipped['length_m'] = clipped.geometry.length
    clipped['length_km'] = clipped['length_m'] / 1000

    # Pastikan kolom geohash ada setelah overlay (misalnya di kolom 'geohash')
    if 'geohash' not in clipped.columns:
        st.error("⚠️ Kolom 'geohash' tidak ditemukan di hasil overlay.")
        return

    result = clipped[['geohash', 'geometry', 'length_km']].to_crs("EPSG:4326")

    # Tampilkan tabel panjang jalan per geohash
    summary = result.groupby('geohash')['length_km'].sum().reset_index()
    st.dataframe(summary, use_container_width=True)

    # Tombol download GeoJSON hasil klip
    buffer = BytesIO()
    result.to_file(buffer, driver="GeoJSON")
    buffer.seek(0)
    st.download_button(
        label="💾 Download Jalan Terklip per Geohash",
        data=buffer,
        file_name="clipped_roads_by_geohash.geojson",
        mime="application/geo+json"
    )

st.title("✂️ Clip Jalan dari File Lokal berdasarkan Geohash")

geohash_file = st.file_uploader("📁 Upload GeoJSON Geohash (Polygon)", type=["geojson", "json"])

if geohash_file and st.button("🚀 Run Clipping"):
    clip_roads_by_geohash_from_local(geohash_file, roads_path="pages/road_data.geojson")
