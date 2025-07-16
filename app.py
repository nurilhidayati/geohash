import streamlit as st

st.set_page_config(
    page_title="GeoHash Toolbox",
    page_icon="🌍",
    initial_sidebar_state="expanded"  # ✅ biar sidebar langsung terbuka
)

st.title("🌍 GeoHash Toolbox")
st.markdown("""
Selamat datang di **GeoHash Toolbox**!

Gunakan menu di sidebar kiri:
- 🔄 Geohash ke GeoJSON
- ➡️ GeoJSON ke Geohash
- 🗺️ Viewer Peta
""")
