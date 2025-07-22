import streamlit as st
import pandas as pd

# Set page config
st.set_page_config(page_title="Forecast Budget Estimator", layout="centered")

# Dark mode CSS
st.markdown(
    """
    <style>
    body {
        background-color: #111111;
        color: white;
    }
    .title {
        text-align: center;
        font-size: 32px;
        font-weight: bold;
        color: #F1C40F;
        margin-bottom: 10px;
    }
    .subtitle {
        text-align: center;
        font-size: 18px;
        color: #BDC3C7;
        margin-bottom: 30px;
    }
    .result-box {
        background-color: #1e1e1e;
        border: 1px solid #444;
        border-radius: 12px;
        padding: 16px;
        margin-bottom: 10px;
        color: white;
    }
    label, .stNumberInput label, .stTextInput label {
        color: white !important;
    }
    .stButton button {
        background-color: #F1C40F;
        color: black;
        font-weight: bold;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# Forecast function
def forecast_budget(
    target_km: float,
    dax_number: int,
    month_estimation: float,
    harga_ukm: float = 8000,
    insurance_per_dax_per_month: int = 132200,
    dataplan_per_dax_per_month: int = 450000
):
    basic_incentive = target_km * harga_ukm
    bonus_coverage = target_km * harga_ukm
    insurance = insurance_per_dax_per_month * dax_number * month_estimation
    dataplan = dataplan_per_dax_per_month * dax_number * month_estimation
    total_before_misc = basic_incentive + bonus_coverage + insurance + dataplan
    miscellaneous = total_before_misc * 0.05
    total_forecast = total_before_misc + miscellaneous

    return {
        "Month Estimation": round(month_estimation, 2),
        "Basic Incentive": round(basic_incentive),
        ">95% Bonus Coverage": round(bonus_coverage),
        "Insurance": round(insurance),
        "Dataplan": round(dataplan),
        "Miscellaneous (5%)": round(miscellaneous),
        "Total Forecast Budget": round(total_forecast)
    }

# Title
st.markdown('<div class="title">📊 Forecast Budget Estimator</div>', unsafe_allow_html=True)

# Upload CSV for Bulk Forecast
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
                month_estimation=float(row['month_estimation'])
            )
            st.markdown(f"#### 🔹 Baris ke-{idx + 1}")
            for key, value in result.items():
                if "Month" in key:
                    st.markdown(f'<div class="result-box"><strong>{key}:</strong> {value} bulan</div>', unsafe_allow_html=True)
                else:
                    st.markdown(f'<div class="result-box"><strong>{key}:</strong> Rp {value:,.0f}</div>', unsafe_allow_html=True)
    else:
        st.error("⚠️ CSV tidak memiliki semua kolom yang dibutuhkan!")

# Manual Input Form
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
    result = forecast_budget(target_km, dax_number, month_estimation)
    st.markdown("### 📑 Hasil Perhitungan:")
    for key, value in result.items():
        if "Month" in key:
            st.markdown(f'<div class="result-box"><strong>{key}:</strong> {value} bulan</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="result-box"><strong>{key}:</strong> Rp {value:,.0f}</div>', unsafe_allow_html=True)
