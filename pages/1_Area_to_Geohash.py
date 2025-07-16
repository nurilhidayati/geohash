import streamlit as st
import json
import geohash2
import numpy as np
from shapely.geometry import shape, box, GeometryCollection, Polygon
from shapely.validation import make_valid
import geopandas as gpd

st.set_page_config(page_title="GeoJSON to Geohash6", layout="wide")
st.title("Area to Geohash6 Converter")

# Required input: filename
custom_filename = st.text_input("📄 Please wite a filename for download (required)")
filename_ready = bool(custom_filename.strip())

# Upload file
uploaded_file = st.file_uploader("📂 Upload a GeoJSON file", type=["geojson", "json"])

def geojson_to_geohash6(geojson_data, precision=6, step=0.0015):
    if 'features' in geojson_data:
        geometries = [shape(feature['geometry']) for feature in geojson_data['features']]
    elif 'geometry' in geojson_data:
        geometries = [shape(geojson_data['geometry'])]
    elif 'type' in geojson_data and 'coordinates' in geojson_data:
        geometries = [shape(geojson_data)]
    else:
        raise ValueError("Unsupported GeoJSON structure")

    full_geom = GeometryCollection(geometries) if len(geometries) > 1 else geometries[0]
    full_geom = make_valid(full_geom)

    minx, miny, maxx, maxy = full_geom.bounds

    geohashes = set()
    for lat in np.arange(miny, maxy, step):
        for lon in np.arange(minx, maxx, step):
            cell = box(lon, lat, lon + step, lat + step)
            if full_geom.intersects(cell):
                gh = geohash2.encode(lat, lon, precision)
                geohashes.add(gh)
    return geohashes

def geohash6_to_geojson(geohashes):
    features = []
    for gh in geohashes:
        lat, lon, lat_err, lon_err = geohash2.decode_exactly(gh)
        cell = {
            "n": lat + lat_err,
            "s": lat - lat_err,
            "e": lon + lon_err,
            "w": lon - lon_err,
        }
        poly = Polygon([
            (cell['w'], cell['s']),
            (cell['e'], cell['s']),
            (cell['e'], cell['n']),
            (cell['w'], cell['n']),
            (cell['w'], cell['s']),
        ])
        features.append({
            "type": "Feature",
            "geometry": json.loads(json.dumps(poly.__geo_interface__)),
            "properties": {"Name": gh}
        })

    geojson_output = {
        "type": "FeatureCollection",
        "features": features
    }
    return geojson_output

# Main logic only runs if both file and filename are provided
if uploaded_file and filename_ready:
    try:
        geojson_data = json.load(uploaded_file)

        # Only show spinner during processing
        with st.spinner("⏳ Converting GeoJSON to Geohash6..."):
            geohashes = geojson_to_geohash6(geojson_data)
            geojson_result = geohash6_to_geojson(geohashes)
            geojson_str = json.dumps(geojson_result)

        # Spinner already done — only show download now
        st.download_button(
            label="📥 Download data GeoJSON",
            data=geojson_str,
            file_name=f"{custom_filename.strip()}.geojson",
            mime="application/geo+json"
        )

    except Exception as e:
        st.error(f"❌ Error processing file: {e}")

elif uploaded_file and not filename_ready:
    st.warning("⚠️ Please enter a filename before downloading.")
