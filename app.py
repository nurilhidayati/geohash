
import streamlit as st

st.title("Geohash Converter")

st.markdown("You can obtain geohash using this tools by simply copy coordinates or drawing polygon using this tools and download it as csv files ")

st.header("1. Copy Coordinates")
st.write(" If you have list of coordinates separated by comma, you can just paste it in fill column and the choose which digit geohash you want then you can download it as csv")


st.video(video_bytes1)

st.header("2. Draw Polygon")
st.write("Geohash can be obtained by draw polygon over area you want to obtain geohash, then pick digit geohash you want, after that another map will popup show geohash coverage based your polygon drawing. ")

