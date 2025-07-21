import streamlit as st
import streamlit.components.v1 as components

# Set page config
st.set_page_config(page_title="Forecast Budget Estimator", layout="centered")

# Styling
st.markdown(
    """
    <style>
    .title {
        text-align: center;
        font-size: 32px;
        font-weight: bold;
        color: #2C3E50;
        margin-bottom: 10px;
    }
    .subtitle {
        text-align: center;
        font-size: 18px;
        color: #7F8C8D;
        margin-bottom: 30px;
    }
    .result-box {
        background-color: #f9f9f9;
        border: 1px solid #e1e1e1;
        border-radius: 12px;
        padding: 16px;
        margin-bottom: 10px;
    }
    </style>
    """,
    unsafe_allow_html=True
)

def forecast_budget(
    target_km: float,
    harga_ukm: float,
    dax_number: int,
    month_estimation: float,
    insurance_per_dax_per_month: float = 132000,
    dataplan_per_dax_per_month: float = 450000
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
st.markdown('<div class="subtitle">Estimate the total budget based on your target coverage and operational costs</div>', unsafe_allow_html=True)

# Input Form
with st.form("forecast_form"):
    st.header("🔧 Input Parameters")
    col1, col2 = st.columns(2)
    with col1:
        target_km = st.number_input("📏 Total Target KM", min_value=0.0, value=10000.0, step=100.0)
        dax_number = st.number_input("👷 Jumlah DAX", min_value=1, value=10, step=1)
    with col2:
        harga_ukm = st.number_input("💰 Harga per KM (UKM)", min_value=0.0, value=5000.0, step=100.0)
        month_estimation = st.number_input("🗓️ Estimasi Bulan", min_value=0.1, value=3.0, step=0.1, format="%.1f")

    submitted = st.form_submit_button("🧮 Hitung Budget")

# Show Result
if submitted:
    result = forecast_budget(target_km, harga_ukm, dax_number, month_estimation)

    st.markdown("### 📑 Hasil Perhitungan:")
    for key, value in result.items():
        with st.container():
            if "Month" in key:
                st.markdown(f'<div class="result-box"><strong>{key}:</strong> {value} bulan</div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="result-box"><strong>{key}:</strong> Rp {value:,.0f}</div>', unsafe_allow_html=True)
