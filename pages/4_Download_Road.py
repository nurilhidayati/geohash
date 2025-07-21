import streamlit as st
import osmnx as ox
import geopandas as gpd
import pandas as pd
import io
import geohash2
from shapely.geometry import box

st.title("🗺️ Restricted Roads Downloader (GeoHash6 Based)")

uploaded_file = st.file_uploader("📄 Upload CSV with `geoHash` column (length 6)", type=["csv"])

# Fungsi bantu: decode geohash ke bounding box polygon
def geohash_to_polygon(gh):
    if len(gh) != 6:
        raise ValueError("Geohash must be 6 characters long.")
    lat, lon, lat_err, lon_err = geohash2.decode_exactly(gh)
    return box(lon - lon_err, lat - lat_err, lon + lon_err, lat + lat_err)

# Fungsi utama: ambil restricted roads berdasarkan daftar geohash
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
            if gdf.empty:
                st.warning(f"⚠️ No matching roads found in geohash {gh}")
                continue
            gdf = gdf[gdf.geometry.type.isin(["LineString", "MultiLineString"])]
            all_roads = pd.concat([all_roads, gdf])
        except Exception as e:
            st.warning(f"⚠️ Failed to fetch for geohash {gh}: {e}")
    all_roads = all_roads.reset_index(drop=True)
    return all_roads

# Tombol proses
if uploaded_file and st.button("🚧 Download Restricted Roads (GeoJSON)"):
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
                st.info(f"🔍 Fetching restricted roads from {len(geohash_list)} geohash6 areas...")
                gdf_roads = download_restricted_roads_from_geohashes(geohash_list)

                if gdf_roads.empty:
                    st.warning("⚠️ No restricted roads found in all geohashes.")
                else:
                    gdf_roads = gdf_roads.to_crs(epsg=4326)
                    buffer = io.BytesIO()
                    gdf_roads.to_file(buffer, driver="GeoJSON")
                    buffer.seek(0)
                    st.success(f"✅ {len(gdf_roads)} restricted roads found.")
                    st.download_button("⬇️ Download Roads", buffer, "restricted_roads.geojson", "application/geo+json")
                    # Preview peta
                    gdf_roads["lon"] = gdf_roads.geometry.centroid.x
                    gdf_roads["lat"] = gdf_roads.geometry.centroid.y
                    st.map(gdf_roads[["lat", "lon"]])
    except Exception as e:
        st.error(f"❌ Unexpected error: {e}")
