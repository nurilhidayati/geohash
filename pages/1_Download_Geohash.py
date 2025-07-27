import streamlit as st
import folium
from streamlit_folium import st_folium
import geopandas as gpd
import json
import os

# Konfigurasi halaman
st.set_page_config(layout="wide")
st.title("🗺️ Swipe Map: Boundary vs GeoHash by Region")

# Load all GeoJSON data from predefined folders
province_gdf = gpd.read_file(os.path.join( "pages/batas_admin_provinsi.geojson"))
regency_gdf = gpd.read_file(os.path.join( "pages/batas_admin_kabupaten.geojson"))
geohash_gdf = gpd.read_file(os.path.join("geohash_output.geojson"))

# Dropdown pemilihan provinsi dan kabupaten
selected_province = st.selectbox("📍 Pilih Provinsi", province_gdf["province_name"].unique())
filtered_regency = regency_gdf[regency_gdf["province_name"] == selected_province]
selected_regency = st.selectbox("🏙️ Pilih Kabupaten/Kota", filtered_regency["regency_name"].unique())

# Filter berdasarkan pilihan
boundary_gdf = filtered_regency[filtered_regency["regency_name"] == selected_regency]

# Clip geohash berdasarkan boundary
boundary_union = boundary_gdf.geometry.unary_union
clipped_geohash = geohash_gdf[geohash_gdf.geometry.intersects(boundary_union)]

if not clipped_geohash.empty:
    center = boundary_union.centroid.coords[0][::-1]  # lat, lon

    # Convert to GeoJSON
    boundary_geojson = json.dumps(json.loads(boundary_gdf.to_crs("EPSG:4326").to_json()))
    geohash_geojson = json.dumps(json.loads(clipped_geohash.to_crs("EPSG:4326").to_json()))

    # Inisialisasi folium map
    m = folium.Map(location=center, zoom_start=11)

    # Tambahkan plugin leaflet side-by-side
    folium.Element("""
        <link rel=\"stylesheet\" href=\"https://unpkg.com/leaflet-side-by-side/leaflet-side-by-side.css\"/>
        <script src=\"https://unpkg.com/leaflet-side-by-side/leaflet-side-by-side.js\"></script>
    """).add_to(m)

    # Layer
    boundary_layer = folium.GeoJson(
        boundary_geojson,
        name="Boundary",
        style_function=lambda x: {"fillColor": "#3186cc", "color": "#3186cc", "weight": 2, "fillOpacity": 0.4},
    )
    geohash_layer = folium.GeoJson(
        geohash_geojson,
        name="GeoHash",
        style_function=lambda x: {"fillColor": "#ff6600", "color": "#ff6600", "weight": 1, "fillOpacity": 0.3},
    )

    boundary_layer.add_to(m)
    geohash_layer.add_to(m)

    # Tambahkan JavaScript kontrol swipe
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

    # Tampilkan peta
    st_data = st_folium(m, width=1100, height=600)

else:
    st.warning("⚠️ Tidak ada data GeoHash untuk wilayah yang dipilih.")
