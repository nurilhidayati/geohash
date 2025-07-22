import streamlit as st
import requests
import json
import tempfile
import osm2geojson

def download_boundary_geojson(area_name, admin_level=None, save_as='boundary.geojson'):
    """
    Downloads administrative boundary polygons as GeoJSON using Overpass API.
    Can be filtered by admin_level (e.g., 4=provinsi, 6=kabupaten, 8=kecamatan).
    """
    overpass_url = "https://overpass-api.de/api/interpreter"

    # Build admin level filter
    admin_filter = f'["admin_level"="{admin_level}"]' if admin_level else ""

    query = f"""
    [out:json][timeout:25];
    area["name"="{area_name}"]->.searchArea;
    (
      relation["boundary"="administrative"]{admin_filter}(area.searchArea);
    );
    out body;
    >;
    out skel qt;
    """

    response = requests.get(overpass_url, params={'data': query})
    if response.status_code != 200:
        raise Exception("Failed to query Overpass API")

    data = response.json()
    if 'elements' not in data or len(data['elements']) == 0:
        raise ValueError(f"No boundary data found for '{area_name}' with admin_level={admin_level}.")

    # Convert to GeoJSON
    geojson = osm2geojson.json2geojson(data)

    # Filter to only Polygon or MultiPolygon features
    features = [feat for feat in geojson['features']
                if feat['geometry']['type'] in ['Polygon', 'MultiPolygon']]

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

# Input area name
area_name = st.text_input("Enter area name (e.g., Jawa Barat, Jakarta, Sleman)")

# Admin level dropdown
admin_options = {
    "All levels": None,
    "Provinsi (admin_level = 4)": "4",
    "Kabupaten/Kota (admin_level = 6)": "6",
    "Kecamatan (admin_level = 8)": "8"
}
selected_label = st.selectbox("Select administrative level", options=list(admin_options.keys()))
admin_level = admin_options[selected_label]

# Optional filename
custom_filename = st.text_input("Optional: Enter output filename (e.g., jakarta_boundary.geojson)")

# Button to trigger download
if st.button("Download Boundary"):
    if not area_name.strip():
        st.warning("⚠️ Please enter an area name.")
    else:
        with st.spinner("⏳ Processing... Please wait."):
            try:
                final_filename = custom_filename.strip() or f"{area_name.replace(' ', '_')}_boundary.geojson"

                with tempfile.NamedTemporaryFile(delete=False, suffix=".geojson") as tmpfile:
                    geojson_data, filepath = download_boundary_geojson(area_name, admin_level=admin_level, save_as=tmpfile.name)

                    with open(filepath, 'rb') as f:
                        st.success("✅ Boundary ready. Click below to download:")
                        st.download_button(
                            label="⬇️ Download GeoJSON",
                            data=f,
                            file_name=final_filename,
                            mime="application/geo+json"
                        )
            except Exception as e:
                st.error(str(e))
