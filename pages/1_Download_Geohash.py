import streamlit as st
import folium
from streamlit_folium import st_folium
import geopandas as gpd
import json

# Konfigurasi halaman
st.set_page_config(layout="wide")
st.title("🗺️ Swipe Map: Boundary vs GeoHash")

# Upload dua file
boundary_file = st.file_uploader("📁 Upload Boundary GeoJSON", type=["geojson"])
geohash_file = st.file_uploader("📁 Upload GeoHash GeoJSON", type=["geojson"])

if boundary_file and geohash_file:
    boundary_gdf = gpd.read_file(boundary_file).to_crs("EPSG:4326")
    geohash_gdf = gpd.read_file(geohash_file).to_crs("EPSG:4326")

    center = boundary_gdf.unary_union.centroid.coords[0][::-1]  # lat, lon

    # Convert to GeoJSON string
    boundary_geojson = json.dumps(json.loads(boundary_gdf.to_json()))
    geohash_geojson = json.dumps(json.loads(geohash_gdf.to_json()))

    # Inisialisasi folium map
    m = folium.Map(location=center, zoom_start=11)

    # Tambahkan placeholder div untuk side-by-side
    folium.Element("""
        <link rel="stylesheet" href="https://unpkg.com/leaflet-side-by-side/leaflet-side-by-side.css"/>
        <script src="https://unpkg.com/leaflet-side-by-side/leaflet-side-by-side.js"></script>
    """).add_to(m)

    # Tambahkan GeoJSON layer tanpa menampilkannya dulu
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

    # Tambahkan JavaScript untuk Side-by-Side
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

    # Render peta
    st_data = st_folium(m, width=1100, height=600)

else:
    st.info("⬆️ Upload dua file GeoJSON untuk melihat peta geser (swipe map).")
