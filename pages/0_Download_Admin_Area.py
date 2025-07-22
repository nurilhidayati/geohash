import streamlit as st
import requests
import json
import tempfile
import osm2geojson

def get_area_id(area_name):
    """
    Get area ID from name using Overpass API (area[name=...] lookup).
    """
    query = f"""
    [out:json][timeout:25];
    area["name"="{area_name}"][admin_level];
    out ids;
    """
    response = requests.get("https://overpass-api.de/api/interpreter", params={"data": query})
    data = response.json()
    areas = data.get("elements", [])
    if not areas:
        raise ValueError(f"❌ Area ID not found for '{area_name}'")
    return areas[0]["id"]


def download_boundary_geojson(area_name, admin_level=None, save_as='boundary.geojson'):
    """
    Downloads administrative boundaries using area ID and filters by admin_level.
    """
    area_id = get_area_id(area_name)
    admin_filter = f'["admin_level"="{admin_level}"]' if admin_level else ""
    query = f"""
    [out:json][timeout:25];
    relation["boundary"="administrative"]{admin_filter}(area:{area_id});
    out body;
    >;
    out skel qt;
    """

    response = requests.get("https://overpass-api.de/api/interpreter", params={"data": query})
    if response.status_code != 200:
        raise Exception("Failed to query Overpass API")

    data = response.json()
    if 'elements' not in data or not data['elements']:
        raise ValueError(f"No boundary data found for '{area_name}' with admin_level={admin_level}.")

    geojson = osm2geojson.json2geojson(data, filter_used_refs=True)

    features = [feat for feat in geojson['features']
                if feat['geometry']['type'] in ['Polygon', 'MultiPolygon']]

    if not features:
        raise ValueError(f"No polygon geometry found for '{area_name}' with admin_level={admin_level}.")

    geojson_filtered = {
        "type": "FeatureCollection",
        "features": features
    }

    with open(save_as, 'w', encoding='utf-8') as f:
        json.dump(geojson_filtered, f, ensure_ascii=False, indent=2)

    return geojson_filtered, save_as


# --- Streamlit UI ---
st.header("🌍 Download Area Boundary as GeoJSON")

area_name = st.text_input("Enter area name (e.g., Jawa Barat, Sleman, Yogyakarta)")

admin_options = {
    "All levels": None,
    "Provinsi (admin_level = 4)": "4",
    "Kabupaten/Kota (admin_level = 6)": "6",
    "Kecamatan (admin_level = 8)": "8"
}
selected_label = st.selectbox("Select administrative level", options=list(admin_options.keys()))
admin_level = admin_options[selected_label]

custom_filename = st.text_input("Optional: Enter output filename (e.g., jawa_barat_boundary.geojson)")

if st.button("Download Boundary"):
    if not area_name.strip():
        st.warning("⚠️ Please enter an area name.")
    else:
        with st.spinner("⏳ Processing... Please wait."):
            try:
                final_filename = custom_filename.strip() or f"{area_name.replace(' ', '_')}_boundary.geojson"

                with tempfile.NamedTemporaryFile(delete=False, suffix=".geojson") as tmpfile:
                    geojson_data, filepath = download_boundary_geojson(
                        area_name=area_name.strip(),
                        admin_level=admin_level,
                        save_as=tmpfile.name
                    )

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
