import streamlit as st
import pandas as pd
import requests

# Fungsi ambil kurs USD-IDR
@st.cache_data(ttl=3600)
def get_usd_to_idr_rate():
    try:
        response = requests.get("https://api.exchangerate.host/latest?base=USD&symbols=IDR")
        response.raise_for_status()
        data = response.json()
        return round(data["rates"]["IDR"], 2)
    except Exception as e:
        st.warning("⚠️ Gagal mengambil kurs online. Menggunakan nilai default Rp 16.000")
        return 16000  # fallback default
   

# Page config
st.set_page_config(page_title="Forecast Budget Estimator", layout="centered")

# CSS Styling
st.markdown("""
    <style>
    body {
        background-color: #0f1116;
        color: white;
        font-family: 'Segoe UI', sans-serif;
    }
    .title {
        text-align: center;
        font-size: 38px;
        font-weight: bold;
        color: #f1c40f;
        margin-top: 20px;
        margin-bottom: 10px;
    }
    .subtitle {
        text-align: center;
        font-size: 18px;
        color: #95a5a6;
        margin-bottom: 30px;
    }
    .result-box {
        background: #1e1e2f;
        border: 1px solid #2e2e3e;
        border-radius: 12px;
        padding: 16px;
        margin-bottom: 12px;
        color: #ecf0f1;
        transition: 0.3s ease-in-out;
    }
    .result-box:hover {
        background: #2c2c40;
        border-color: #f1c40f;
    }
    label, .stNumberInput label, .stTextInput label {
        color: #ecf0f1 !important;
    }
    .stButton button {
        background-color: #f1c40f;
        color: black;
        font-weight: bold;
        border-radius: 8px;
        transition: all 0.3s ease;
    }
    .stButton button:hover {
        background-color: #f39c12;
        color: white;
    }
    </style>
""", unsafe_allow_html=True)

# Title
st.markdown('<div class="title">📊 Forecast Budget Estimator</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Prediksi anggaran berdasarkan target KM, jumlah DAX, dan durasi</div>', unsafe_allow_html=True)

# Ambil nilai tukar
exchange_rate = get_usd_to_idr_rate()
st.info(f"💱 Kurs saat ini: 1 USD = Rp {exchange_rate:,.0f}")

# Forecast function
def forecast_budget(target_km, dax_number, month_estimation,
                    harga_ukm=8000,
                    insurance_per_dax_per_month=132200,
                    dataplan_per_dax_per_month=450000,
                    exchange_rate=16000):

    basic_incentive = target_km * harga_ukm
    bonus_coverage = target_km * harga_ukm
    insurance = insurance_per_dax_per_month * dax_number * month_estimation
    dataplan = dataplan_per_dax_per_month * dax_number * month_estimation
    total_before_misc = basic_incentive + bonus_coverage + insurance + dataplan
    miscellaneous = total_before_misc * 0.05
    total_forecast = total_before_misc + miscellaneous
    total_forecast_usd = total_forecast / exchange_rate

    return {
        "Month Estimation": round(month_estimation, 2),
        "Basic Incentive": round(basic_incentive),
        ">95% Bonus Coverage": round(bonus_coverage),
        "Insurance": round(insurance),
        "Dataplan": round(dataplan),
        "Miscellaneous (5%)": round(miscellaneous),
        "Total Forecast Budget": round(total_forecast),
        "Total Forecast Budget (USD)": round(total_forecast_usd, 2)
    }

# --- BULK FORECAST ---
st.subheader("📂 Bulk Forecast dari CSV")
uploaded_file = st.file_uploader("Unggah file CSV (dengan kolom: target_km, dax_number, month_estimation)", type=["csv"])

if uploaded_file:
    df = pd.read_csv(uploaded_file)
    required_cols = {'target_km', 'dax_number', 'month_estimation'}
    if required_cols.issubset(df.columns):
        st.success("✅ File berhasil diunggah dan dibaca.")
        st.markdown("### 📋 Hasil Perhitungan Forecast (CSV):")

        for idx, row in df.iterrows():
            result = forecast_budget(
                target_km=float(row['target_km']),
                dax_number=int(row['dax_number']),
                month_estimation=float(row['month_estimation']),
                exchange_rate=exchange_rate
            )
            st.markdown(f"#### 🔹 Baris ke-{idx + 1}")
            for key, value in result.items():
                if "Month" in key:
                    st.markdown(f'<div class="result-box"><strong>{key}:</strong> {value} bulan</div>', unsafe_allow_html=True)
                elif "USD" in key:
                    st.markdown(f'<div class="result-box"><strong>{key}:</strong> ${value:,.2f}</div>', unsafe_allow_html=True)
                else:
                    st.markdown(f'<div class="result-box"><strong>{key}:</strong> Rp {value:,.0f}</div>', unsafe_allow_html=True)
    else:
        st.error("⚠️ CSV tidak memiliki semua kolom yang dibutuhkan!")

# --- MANUAL INPUT ---
st.subheader("🧮 Hitung Manual")
with st.form("forecast_form"):
    st.header("🔧 Input Parameters")
    col1, col2 = st.columns(2)
    with col1:
        target_km = st.number_input("📏 Total Target KM", min_value=0.0, value=0.0, step=100.0)
        dax_number = st.number_input("👷 Jumlah DAX", min_value=1, value=1, step=1)
    with col2:
        month_estimation = st.number_input("🗓️ Estimasi Bulan", min_value=0.1, value=1.0, step=0.1, format="%.1f")

    submitted = st.form_submit_button("🧮 Hitung Budget")

if submitted:
    result = forecast_budget(target_km, dax_number, month_estimation, exchange_rate=exchange_rate)
    st.markdown("### 📑 Hasil Perhitungan:")
    for key, value in result.items():
        if "Month" in key:
            st.markdown(f'<div class="result-box"><strong>{key}:</strong> {value} bulan</div>', unsafe_allow_html=True)
        elif "USD" in key:
            st.markdown(f'<div class="result-box"><strong>{key}:</strong> ${value:,.2f}</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="result-box"><strong>{key}:</strong> Rp {value:,.0f}</div>', unsafe_allow_html=True)
