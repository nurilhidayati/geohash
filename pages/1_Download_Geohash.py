import streamlit as st
import folium
from streamlit_folium import st_folium
import geopandas as gpd
import json
import geohash2
from shapely.geometry import box

# Fungsi bantu: buat polygon dari geohash
def geohash_to_polygon(g):
    lat, lon, lat_err, lon_err = geohash2.decode_exactly(g)
    return box(lon - lon_err, lat - lat_err, lon + lon_err, lat + lat_err)

# Fungsi generate geohash dari boundary
def generate_geohash6_from_boundary(gdf, precision=6):
    bounds = gdf.total_bounds  # minx, miny, maxx, maxy
    minx, miny, maxx, maxy = bounds
    step = 0.01  # ~1km step
    geohash_set = set()

    lat = miny
    while lat < maxy:
        lon = minx
        while lon < maxx:
            g = geohash2.encode(lat, lon, precision)
            geohash_set.add(g)
            lon += step
        lat += step

    geohash_polygons = [geohash_to_polygon(g) for g in geohash_set]
    geohash_gdf = gpd.GeoDataFrame({'geohash': list(geohash_set)}, geometry=geohash_polygons, crs="EPSG:4326")
    geohash_gdf = geohash_gdf[geohash_gdf.geometry.intersects(gdf.unary_union)]
    return geohash_gdf

# Konfigurasi Streamlit
st.set_page_config(layout="wide")
st.title("🗺️ Swipe Map: Boundary vs GeoHash6 (Auto Convert)")

# Load batas wilayah
province_gdf = gpd.read_file("pages/batas_admin_provinsi.geojson")
regency_gdf = gpd.read_file("pages/batas_admin_kabupaten.geojson")

# Pilihan user
province_options = province_gdf["WADMPR"].unique()
selected_province = st.selectbox("📍 Pilih Provinsi", province_options)

# Filter kabupaten berdasarkan provinsi
filtered_regency = regency_gdf[regency_gdf["WADMPR"] == selected_province]
regency_options = filtered_regency["WADMKK"].unique()
selected_regency = st.selectbox("🏙️ Pilih Kabupaten/Kota", regency_options)

# Ambil boundary kabupaten
boundary_gdf = filtered_regency[filtered_regency["WADMKK"] == selected_regency]

# Konversi ke geohash6
geohash6_gdf = generate_geohash6_from_boundary(boundary_gdf, precision=6)

if not geohash6_gdf.empty:
    center = boundary_gdf.unary_union.centroid.coords[0][::-1]

    # Konversi GeoDataFrame ke GeoJSON
    boundary_geojson = json.loads(boundary_gdf.to_crs("EPSG:4326").to_json())
    geohash_geojson = json.loads(geohash6_gdf.to_crs("EPSG:4326").to_json())

    # Inisialisasi Folium Map
    m = folium.Map(location=center, zoom_start=11)

    # Tambahkan layer
    boundary_layer = folium.GeoJson(
        boundary_geojson,
        name="Boundary",
        style_function=lambda x: {"fillColor": "#3186cc", "color": "#3186cc", "weight": 2, "fillOpacity": 0.4},
    )
    geohash_layer = folium.GeoJson(
        geohash_geojson,
        name="GeoHash6",
        style_function=lambda x: {"fillColor": "#ff6600", "color": "#ff6600", "weight": 1, "fillOpacity": 0.3},
    )
    boundary_layer.add_to(m)
    geohash_layer.add_to(m)

    # Tambahkan plugin Leaflet untuk swipe
    m.get_root().html.add_child(folium.Element("""
        <link rel="stylesheet" href="https://unpkg.com/leaflet-side-by-side/leaflet-side-by-side.css"/>
        <script src="https://unpkg.com/leaflet-side-by-side/leaflet-side-by-side.js"></script>
    """))

    # Swipe Control Script
    m.get_root().html.add_child(folium.Element(f"""
        <script>
            setTimeout(function() {{
                var map = window.map;
                var leftLayer = map._layers[{list(boundary_layer._children.values())[0]._leaflet_id}];
                var rightLayer = map._layers[{list(geohash_layer._children.values())[0]._leaflet_id}];
                L.control.sideBySide(leftLayer, rightLayer).addTo(map);
            }}, 500);
        </script>
    """))

    # Tampilkan map di Streamlit
    st_folium(m, width=1100, height=600)

    # Tombol download hasil GeoHash6
    geojson_str = geohash6_gdf.to_json()
    st.download_button("📥 Download GeoHash6", data=geojson_str, file_name="geohash6_output.geojson", mime="application/geo+json")

else:
    st.warning("⚠️ Tidak ada GeoHash6 dalam boundary yang dipilih.")
