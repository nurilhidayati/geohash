import streamlit as st
import requests
import json
import tempfile
import osm2geojson

def download_boundary_geojson(area_name, admin_level=None, save_as='boundary.geojson'):
    """
    Download administrative boundary polygons from OSM for a given area name.
    Optionally filter by admin_level (string).
    """
    overpass_url = "https://overpass-api.de/api/interpreter"

    # Construct Overpass QL query
    # Try to get area by name and boundary=administrative, then relations inside it.
    # Also get relation by name and boundary=administrative directly.
    admin_level_filter = f'["admin_level"="{admin_level}"]' if admin_level else ''

    query = f"""
    [out:json][timeout:25];
    // Get area id by name and boundary=administrative
    area["name"="{area_name}"]["boundary"="administrative"]->.searchArea;

    (
      // relations inside the area with boundary=administrative and optional admin_level
      relation(area.searchArea)["boundary"="administrative"]{admin_level_filter};
      // relation with the exact name and boundary=administrative (in case area is itself a relation)
      relation["name"="{area_name}"]["boundary"="administrative"]{admin_level_filter};
    );
    out body;
    >;
    out skel qt;
    """

    response = requests.get(overpass_url, params={'data': query})
    if response.status_code != 200:
        raise Exception(f"Failed to query Overpass API (status code {response.status_code})")

    data = response.json()
    if 'elements' not in data or len(data['elements']) == 0:
        raise ValueError(f"No boundary data found for '{area_name}'.")

    geojson = osm2geojson.json2geojson(data)

    # Filter polygon/multipolygon features only
    features = [f for f in geojson['features'] if f['geometry']['type'] in ('Polygon', 'MultiPolygon')]
    if not features:
        raise ValueError(f"No polygon boundaries found for '{area_name}'.")

    geojson_filtered = {
        "type": "FeatureCollection",
        "features": features
    }

    with open(save_as, 'w', encoding='utf-8') as f:
        json.dump(geojson_filtered, f, ensure_ascii=False, indent=2)

    return geojson_filtered, save_as


# --- Streamlit UI ---
st.header("🌍 Download Area Boundary as GeoJSON")

area_name = st.text_input("Enter area name (e.g., Jakarta, Yogyakarta, etc.)")
admin_level = st.text_input("Optional: Admin level filter (e.g., 4, 6)")
custom_filename = st.text_input("Optional: Output filename (e.g., jakarta_boundary.geojson)")

if st.button("Download Boundary"):
    if not area_name.strip():
        st.warning("⚠️ Please enter an area name.")
    else:
        with st.spinner("⏳ Processing... Please wait."):
            try:
                final_filename = custom_filename.strip() or f"{area_name.replace(' ', '_')}_boundary.geojson"
                with tempfile.NamedTemporaryFile(delete=False, suffix=".geojson") as tmpfile:
                    geojson_data, filepath = download_boundary_geojson(area_name, admin_level=admin_level.strip() or None, save_as=tmpfile.name)

                with open(filepath, "rb") as f:
                    st.success("✅ Boundary ready. Click below to download:")
                    st.download_button(
                        label="⬇️ Download GeoJSON",
                        data=f,
                        file_name=final_filename,
                        mime="application/geo+json"
                    )
            except Exception as e:
                st.error(str(e))
