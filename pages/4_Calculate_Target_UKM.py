import streamlit as st
import osmnx as ox
import geopandas as gpd
import pandas as pd
import io
import geohash2
from shapely.geometry import box

st.set_page_config(page_title="🛣️ Calculate Target UKM", layout="wide")
st.title("🛣️ Calculate Target UKM")

uploaded_file = st.file_uploader("📄 Upload GeoJSON or CSV with `geoHash` column", type=["csv", "geojson", "json"])

# Reset hasil roads saat tombol calculate ditekan
if 'gdf_roads' not in st.session_state:
    st.session_state['gdf_roads'] = None

def geohash_to_bounds(gh):
    lat, lon, lat_err, lon_err = geohash2.decode_exactly(gh)
    return (lat - lat_err, lat + lat_err, lon - lon_err, lon + lon_err)

@st.cache_data(show_spinner="📡 Downloading roads...", ttl=3600)
def download_clipped_roads_from_geohashes(geohash_list):
    roads = []
    tags = {
        "highway": [
            "motorway", "motorway_link", "secondary", "secondary_link",
            "primary", "primary_link", "residential", "trunk", "trunk_link",
            "tertiary", "tertiary_link", "living_street", "service", "unclassified"
        ]
    }

    progress = st.progress(0)
    for i, gh in enumerate(geohash_list):
        try:
            south, north, west, east = geohash_to_bounds(gh)
            polygon = box(west, south, east, north)

            gdf_all = ox.features_from_bbox(north, south, east, west, tags=tags)
            gdf_lines = gdf_all[gdf_all.geometry.type.isin(["LineString", "MultiLineString"])]
            gdf_clipped = gpd.clip(gdf_lines, polygon)

            if not gdf_clipped.empty:
                roads.append(gdf_clipped)
        except Exception:
            pass

        progress.progress((i + 1) / len(geohash_list))

    if roads:
        return pd.concat(roads).reset_index(drop=True)
    else:
        return gpd.GeoDataFrame()

if uploaded_file and st.button("🗂️ Calculate UKM (GeoJSON)"):
    st.session_state['gdf_roads'] = None  # reset saat tombol calculate ditekan
    try:
        filename = uploaded_file.name.lower()
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
                    st.session_state['gdf_roads'] = gdf_roads  # simpan ke session

    except Exception as e:
        st.error(f"❌ Unexpected error: {e}")

# Tombol download muncul hanya jika sudah ada hasil
if st.session_state['gdf_roads'] is not None:
    buffer = io.BytesIO()
    st.session_state['gdf_roads'].to_file(buffer, driver="GeoJSON")
    buffer.seek(0)
    st.download_button("⬇️ Download Roads", buffer, "roads_inside_geohash.geojson", "application/geo+json")

# Footer
st.markdown(
    """
    <hr style="margin-top: 2rem; margin-bottom: 1rem;">
    <div style='text-align: center; color: grey; font-size: 0.9rem;'>
        © 2025 ID Karta IoT Team
    </div>
    """,
    unsafe_allow_html=True
)
