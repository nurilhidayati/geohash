import streamlit as st
import geopandas as gpd
import pandas as pd
import osmnx as ox
import geohash2
from shapely.geometry import Polygon
from io import BytesIO
from collections import Counter

def select_dense_geohash_from_uploaded_boundary(
    file, 
    tag_filters, 
    precision=6, 
    top_percent=0.5
):
    boundary_gdf = gpd.read_file(file).to_crs("EPSG:4326")
    polygon = boundary_gdf.unary_union

    st.info("📡 Fetching POI data...")
    tags_dict = {tag: True for tag in tag_filters}
    try:
        poi_gdf = ox.geometries_from_polygon(polygon, tags=tags_dict)
        poi_gdf = poi_gdf[poi_gdf.geometry.type.isin(['Point', 'Polygon', 'MultiPolygon'])]
        poi_gdf = poi_gdf.to_crs("EPSG:4326")
    except Exception as e:
        st.warning(f"⚠️ Gagal mengambil POI: {e}")
        poi_gdf = gpd.GeoDataFrame(columns=['geometry'], geometry='geometry', crs='EPSG:4326')

    st.info("🚗 Fetching major roads...")
    try:
        road_tags = {'highway': ['motorway', 'trunk', 'primary', 'secondary']}
        roads_gdf = ox.geometries_from_polygon(polygon, tags=road_tags)
        roads_gdf = roads_gdf[roads_gdf.geometry.type.isin(['LineString', 'MultiLineString'])]
        roads_gdf = roads_gdf.to_crs("EPSG:4326")
    except Exception as e:
        st.warning(f"⚠️ Gagal mengambil jalan besar: {e}")
        roads_gdf = gpd.GeoDataFrame(columns=['geometry'], geometry='geometry', crs='EPSG:4326')

    all_gdf = pd.concat([poi_gdf, roads_gdf], ignore_index=True)
    if all_gdf.empty:
        st.error("❌ Tidak ada data POI atau jalan.")
        return None

    def encode_geohash(geom):
        try:
            if geom.is_empty:
                return None
            if geom.geom_type == 'Point':
                point = geom
            else:
                point = geom.representative_point()
            return geohash2.encode(point.y, point.x, precision=precision)
        except:
            return None

    all_gdf['geohash'] = all_gdf.geometry.apply(encode_geohash)
    all_gdf = all_gdf.dropna(subset=['geohash'])
    all_gdf = all_gdf[all_gdf['geohash'].apply(lambda x: isinstance(x, str))]

    count_df = all_gdf.groupby('geohash').size().reset_index(name='count')
    threshold = count_df['count'].quantile(1 - top_percent)
    dense_df = count_df[count_df['count'] >= threshold]

    def add_missing_centers(df):
        all_neighbors = []
        for gh in df['geohash']:
            try:
                nbs = geohash2.neighbors(gh)
                all_neighbors.extend(nbs)
            except:
                continue
        freq = Counter(all_neighbors)
        missing = [g for g in freq if g not in df['geohash'].values and freq[g] >= 2]
        df_extra = count_df[count_df['geohash'].isin(missing)]
        return pd.concat([df, df_extra], ignore_index=True)

    dense_df = add_missing_centers(dense_df)

    def geohash_to_polygon(g):
        lat, lon, lat_err, lon_err = geohash2.decode_exactly(g)
        return Polygon([
            (lon - lon_err, lat - lat_err),
            (lon - lon_err, lat + lat_err),
            (lon + lon_err, lat + lat_err),
            (lon + lon_err, lat - lat_err),
            (lon - lon_err, lat - lat_err)
        ])

    dense_gdf = gpd.GeoDataFrame({
        'geohash': dense_df['geohash'],
        'count': dense_df['count'],
        'geometry': dense_df['geohash'].apply(geohash_to_polygon)
    }, crs='EPSG:4326')

    st.info("🧹 Menghapus outlier geohash yang jauh...")
    dense_union = dense_gdf.unary_union
    if dense_union.geom_type == 'MultiPolygon':
        largest = max(dense_union.geoms, key=lambda g: g.area)
    else:
        largest = dense_union
    dense_gdf = dense_gdf[dense_gdf.geometry.intersects(largest)]

    return dense_gdf

# STREAMLIT INTERFACE
st.title("🧭 Select Dense Geohash from Boundary")
uploaded_file = st.file_uploader("Upload GeoJSON Boundary", type=["geojson", "json"])
precision = st.slider("Geohash Precision", 4, 7, 6)
top_percent = st.slider("Top Percent for Dense Geohash", 0.1, 1.0, 0.5)

default_tags = [
    'shop', 'restaurant', 'fast_food', 'cafe', 'food_court',
    'bakery', 'convenience', 'supermarket', 'marketplace',
    'residential', 'building', 'commercial', 'retail',
    'bank', 'atm', 'clinic', 'pharmacy', 'hospital',
    'school', 'college', 'university',
    'parking', 'taxi', 'car_rental',
    'bus_station', 'bus_stop'
]

if uploaded_file and st.button("🚀 Run Extraction"):
    result_gdf = select_dense_geohash_from_uploaded_boundary(
        uploaded_file,
        tag_filters=default_tags,
        precision=precision,
        top_percent=top_percent
    )

    if result_gdf is not None:
        st.success("✅ Geohash padat berhasil diekstrak.")
        st.map(result_gdf)

        buffer = BytesIO()
        result_gdf.to_file(buffer, driver="GeoJSON")
        buffer.seek(0)
        st.download_button(
            label="💾 Download Dense Geohash GeoJSON",
            data=buffer,
            file_name="dense_osm_geohash.geojson",
            mime="application/geo+json"
        )
