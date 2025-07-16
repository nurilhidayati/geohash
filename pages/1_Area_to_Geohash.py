import streamlit as st
import json
import geohash2
import numpy as np
from shapely.geometry import shape, box, GeometryCollection, Polygon
from shapely.validation import make_valid
import geopandas as gpd
import pydeck as pdk

st.set_page_config(page_title="GeoJSON to Geohash6", layout="wide")
st.title("🧭 GeoJSON to Geohash6 Converter")

uploaded_file = st.file_uploader("Upload a GeoJSON file", type=["geojson", "json"])

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

if uploaded_file:
    try:
        geojson_data = json.load(uploaded_file)
        st.success("✅ File successfully uploaded and parsed.")

        geohashes = geojson_to_geohash6(geojson_data)
        st.write(f"✅ Found **{len(geohashes)}** geohash6 cells")

        geojson_result = geohash6_to_geojson(geohashes)
        geojson_str = json.dumps(geojson_result)

        st.download_button(
            label="📥 Download GeoJSON with Geohash6 Cells",
            data=geojson_str,
            file_name="geohash6_cells.geojson",
            mime="application/geo+json"
        )

        # Optional: show result using pydeck
        gdf = gpd.GeoDataFrame.from_features(geojson_result["features"])
        gdf["coordinates"] = gdf["geometry"].apply(lambda geom: list(geom.exterior.coords))

        polygon_layer = pdk.Layer(
            "PolygonLayer",
            gdf,
            get_polygon="coordinates",
            get_fill_color="[200, 30, 0, 80]",
            pickable=True,
            auto_highlight=True,
        )

        view_state = pdk.ViewState(
            longitude=gdf.geometry.centroid.x.mean(),
            latitude=gdf.geometry.centroid.y.mean(),
            zoom=10,
            pitch=0,
        )

        st.pydeck_chart(pdk.Deck(
            map_style="mapbox://styles/mapbox/light-v9",
            layers=[polygon_layer],
            initial_view_state=view_state,
        ))

    except Exception as e:
        st.error(f"❌ Error processing file: {e}")
