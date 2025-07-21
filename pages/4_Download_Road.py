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
    all_roads = gpd.GeoDataFrame()
    for gh in geohash_list:
        try:
            polygon = geohash_to_polygon(gh)
            # Ambil semua geometri OSM dalam polygon
            gdf_all = ox.geometries_from_polygon(polygon, tags=None)

            if gdf_all.empty:
                st.warning(f"⚠️ No OSM features in geohash {gh}")
                continue

            # Filter fitur jalan terbatas
            gdf = gdf_all[
                gdf_all.geometry.type.isin(["LineString", "MultiLineString"]) &
                (
                    (gdf_all.get("access").isin(["private", "no", "military", "customers", "permit"])) |
                    (gdf_all.get("barrier").isin(["gate", "fence", "bollard"])) |
                    (gdf_all.get("highway") == "service") |
                    (gdf_all.get("military").notna()) |
                    (gdf_all.get("landuse").isin(["military", "industrial", "government"]))
                )
            ]

            if gdf.empty:
                st.warning(f"⚠️ No restricted roads found in geohash {gh}")
                continue

            all_roads = pd.concat([all_roads, gdf])

        except Exception as e:
            st.warning(f"⚠️ Failed to fetch for geohash {gh}: {e}")
    return all_roads.reset_index(drop=True)



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
