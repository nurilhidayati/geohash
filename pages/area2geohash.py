# app.py
import streamlit as st

st.set_page_config(page_title="GeoHash Toolbox", page_icon="🌍")

st.title("🌍 GeoHash Toolbox")
st.markdown("""
Selamat datang di **GeoHash Toolbox**!

Gunakan sidebar di kiri untuk mengakses fitur:
- 🔄 Konversi Geohash ke GeoJSON
- ➡️ Konversi GeoJSON ke Geohash
- 🗺️ Viewer Peta GeoJSON

Website ini membantu kamu dalam mengolah data spasial dengan format geohash secara praktis.
""")
