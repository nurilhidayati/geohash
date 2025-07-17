import streamlit as st

st.set_page_config(
    page_title="Karta IoT Tools",
    page_icon="🌍",
    initial_sidebar_state="expanded"  # ✅ biar sidebar langsung terbuka
)

st.title("🌍 Karta IoT Tools")
st.markdown("""
Selamat datang di **Karta IoT Tools**!

Gunakan menu di sidebar kiri:
- 🔄 Area to GeoHash6
- ➡️ CSV to GeoJSON
- 🗺️ GeoJSON to CSV
""")
