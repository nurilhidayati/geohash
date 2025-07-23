# app.py
import streamlit as st
import pandas as pd
import geopandas as gpd
import tempfile
import zipfile
import os

st.title("GeoJSON to CSV Converter")
st.markdown("Upload one or more GeoJSON files. Each file will be converted to a CSV with geometry coordinates.")

uploaded_files = st.file_uploader("📄 Upload GeoJSON files", type="geojson", accept_multiple_files=True)

if uploaded_files:
    output_dir = tempfile.mkdtemp()
    csv_paths = []

    for file in uploaded_files:
        st.write(f"Processing: **{file.name}**")
        try:
            gdf = gpd.read_file(file)

            # Flatten geometry to WKT or GeoJSON string
            gdf['geometry'] = gdf['geometry'].apply(lambda geom: geom.wkt)

            csv_name = file.name.replace(".geojson", ".csv")
            csv_path = os.path.join(output_dir, csv_name)
            gdf.to_csv(csv_path, index=False)

            csv_paths.append(csv_path)
            st.success(f"✅ Converted: {csv_name}")
        except Exception as e:
            st.error(f"Error processing `{file.name}`: {e}")

    if len(csv_paths) == 1:
        # Single file: Download directly
        csv_path = csv_paths[0]
        with open(csv_path, "rb") as f:
            st.download_button(
                label="⬇️ Download CSV",
                data=f,
                file_name=os.path.basename(csv_path),
                mime="text/csv"
            )

    elif len(csv_paths) > 1:
        # Multiple files: Zip and download
        zip_path = os.path.join(output_dir, "converted_csvs.zip")
        with zipfile.ZipFile(zip_path, 'w') as zipf:
            for csv_file in csv_paths:
                zipf.write(csv_file, os.path.basename(csv_file))

        with open(zip_path, "rb") as f:
            st.download_button(
                label="📦 Download All CSVs as ZIP",
                data=f,
                file_name="csv_output.zip",
                mime="application/zip"
            )

# Footer
st.markdown(
    """
    <hr style="margin-top: 2rem; margin-bottom: 1rem;">
    <div style='text-align: center; color: grey; font-size: 0.9rem;'>
        © 2025 ID Karta IoT Team
    </div>
    """,
    unsafe_allow_html=True
)
