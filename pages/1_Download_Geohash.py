import streamlit as st
import requests
import json
import tempfile
import osm2geojson
import folium
from streamlit_folium import st_folium
from shapely.geometry import shape, GeometryCollection, box, Polygon
from shapely.validation import make_valid
import geohash2
import pandas as pd
import numpy as np

# ======================== CONFIG ========================
st.set_page_config(page_title="📍 Download Boundary & GeoHash", layout="wide")
st.title("📍 Download Boundary & GeoHash")

# ======================== STYLE ========================
def get_bounds_from_geojson(geojson):
    bounds = [[90, 180], [-90, -180]]
    for feature in geojson["features"]:
        coords = feature["geometry"]["coordinates"]
        geom_type = feature["geometry"]["type"]
        if geom_type == "Polygon":
            coords = [coords]
        for polygon in coords:
            for point in polygon[0]:
                lat, lon = point[1], point[0]
                bounds[0][0] = min(bounds[0][0], lat)
                bounds[0][1] = min(bounds[0][1], lon)
                bounds[1][0] = max(bounds[1][0], lat)
                bounds[1][1] = max(bounds[1][1], lon)
    return bounds

def geohash_to_polygon(gh):
    lat, lon, lat_err, lon_err = geohash2.decode_exactly(gh)
    return box(lon - lon_err, lat - lat_err, lon + lon_err, lat + lat_err)

def geojson_to_geohash6(geojson, precision=6):
    polygons = []
    for feature in geojson["features"]:
        geom = shape(feature["geometry"])
        valid_geom = make_valid(geom)
        if isinstance(valid_geom, GeometryCollection):
            for g in valid_geom.geoms:
                if g.is_valid and not g.is_empty:
                    polygons.append(g)
        else:
            if valid_geom.is_valid and not valid_geom.is_empty:
                polygons.append(valid_geom)

    geohash_set = set()
    for poly in polygons:
        minx, miny, maxx, maxy = poly.bounds
        lats = np.arange(miny, maxy, 0.01)
        lons = np.arange(minx, maxx, 0.01)
        for lat in lats:
            for lon in lons:
                p = Polygon([(lon, lat), (lon + 0.01, lat), (lon + 0.01, lat + 0.01), (lon, lat + 0.01)])
                if poly.intersects(p.centroid):
                    geohash_set.add(geohash2.encode(lat, lon, precision=precision))
    return geohash_set

def geohash6_to_geojson(geohash_set):
    features = []
    for gh in geohash_set:
        poly = geohash_to_polygon(gh)
        feature = {
            "type": "Feature",
            "properties": {"geohash6": gh},
            "geometry": json.loads(json.dumps(poly.__geo_interface__)),
        }
        features.append(feature)
    return {"type": "FeatureCollection", "features": features}

# ======================== UI ========================
col1, col2 = st.columns(2)
with col1:
    wilayah = st.radio("Pilih Wilayah", ["Kabupaten", "Provinsi"])
with col2:
    area_name = st.text_input(f"Masukkan nama {wilayah.lower()}")

search = st.button("🔍 Cari")

# ======================== Map Setup ========================
m = folium.Map(location=[-2.5, 117.5], zoom_start=5, control_scale=True)

# Tampilkan hasil GeoHash di peta jika tersedia
if "geohash_geojson" in st.session_state and st.session_state["geohash_geojson"]:
    folium.GeoJson(
        st.session_state["geohash_geojson"],
        name="GeoHash6",
        style_function=lambda x: {"color": "#ff6600", "weight": 1, "fillOpacity": 0.3},
        tooltip=folium.GeoJsonTooltip(fields=["geohash6"])
    ).add_to(m)

# ======================== Search Logic ========================
if search and area_name:
    st.session_state["geojson_result"] = None
    query_area = f"{area_name}, Indonesia"
    level = "8" if wilayah == "Kabupaten" else "4"
    overpass_url = "http://overpass-api.de/api/interpreter"
    query = f"""
    [out:json];
    area["name"="{area_name}"]["admin_level"="{level}"][boundary="administrative"]->.searchArea;
    (
      relation(area.searchArea)["admin_level"="{level}"]["boundary"="administrative"];
    );
    out body;
    >;
    out skel qt;
    """
    response = requests.post(overpass_url, data={"data": query})

    if response.status_code == 200:
        osm_data = response.text
        try:
            geojson_data = osm2geojson.json2geojson(json.loads(osm_data))
            if len(geojson_data["features"]) > 0:
                area_geojson = geojson_data

                # Zoom map
                bounds = get_bounds_from_geojson(area_geojson)
                m.fit_bounds(bounds)

                # Convert to GeoHash
                geohashes = geojson_to_geohash6(area_geojson)
                geohash_geojson = geohash6_to_geojson(geohashes)

                # Simpan di session
                st.session_state["geojson_result"] = area_geojson
                st.session_state["geohash_geojson"] = geohash_geojson
                st.session_state["geohash_csv"] = pd.DataFrame({"geohash6": sorted(list(geohashes))})
                st.session_state["area_name"] = area_name
            else:
                st.error("❌ Area tidak ditemukan.")
        except Exception as e:
            st.error(f"❌ Gagal parsing GeoJSON: {e}")
    else:
        st.error("❌ Gagal mengambil data dari Overpass API.")

# ======================== Download Buttons ========================
if "geojson_result" in st.session_state and st.session_state["geojson_result"]:
    filename = f"{st.session_state['area_name'].replace(' ', '_').lower()}_boundary.geojson"
    st.download_button(
        label="💾 Download Area Boundary (GeoJSON)",
        data=json.dumps(st.session_state["geojson_result"]),
        file_name=filename,
        mime="application/geo+json"
    )

if "geohash_csv" in st.session_state and st.session_state["geohash_csv"] is not None:
    csv = st.session_state["geohash_csv"].to_csv(index=False).encode("utf-8")
    csv_filename = f"{st.session_state['area_name'].replace(' ', '_').lower()}_geohash6.csv"
    st.download_button(
        label="📥 Download GeoHash6 as CSV",
        data=csv,
        file_name=csv_filename,
        mime="text/csv"
    )

# ======================== Show Map ========================
st_data = st_folium(m, width=1200, height=600)
