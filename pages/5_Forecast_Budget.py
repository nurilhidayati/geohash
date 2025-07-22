import streamlit as st
import pandas as pd
import requests


@st.cache_data(ttl=3600)
def get_exchange_rates():
    try:
        response = requests.get("https://api.exchangerate-api.com/v4/latest/USD")
        response.raise_for_status()
        data = response.json()

        if "rates" in data and "IDR" in data["rates"]:
            usd_to_idr = data["rates"]["IDR"]
            idr_to_usd = 1 / usd_to_idr

            return {
                "usd_to_idr": round(usd_to_idr, 2),
                "idr_to_usd": round(idr_to_usd, 8),
                "last_updated": data.get("date", "Unknown"),
                "success": True
            }
        else:
            raise Exception("IDR rate not found")
    except Exception as e:
        st.warning(f"Gagal ambil kurs real-time. Gunakan fallback. Error: {str(e)}")
        return {
            "usd_to_idr": 15800,
            "idr_to_usd": 0.00006329,
            "last_updated": "Fallback",
            "success": False
        }

def get_usd_to_idr_rate():
    return get_exchange_rates()["usd_to_idr"]

def format_currency(amount, currency="IDR"):
    if currency == "IDR":
        return f"Rp {amount:,.0f}"
    else:
        return f"${amount:,.2f}"

# --- FORECAST FUNCTION ---
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

# --- STREAMLIT PAGE CONFIG ---
st.set_page_config(page_title="Forecast Budget Estimator", layout="centered")

# --- STYLING ---
st.markdown("""
    <style>
    body { background-color: #0f1116; color: white; }
    .title {
        text-align: center;
        font-size: 38px;
        font-weight: bold;
        color: #f1c40f;
    }
    .subtitle {
        text-align: center;
        font-size: 18px;
        color: #95a5a6;
    }
    .result-box {
        background: #1e1e2f;
        border: 1px solid #2e2e3e;
        border-radius: 12px;
        padding: 16px;
        color: #ecf0f1;
    }
    .stButton button {
        background-color: #f1c40f;
        color: black;
        font-weight: bold;
        border-radius: 8px;
    }
    .stButton button:hover {
        background-color: #f39c12;
        color: white;
    }
    </style>
""", unsafe_allow_html=True)

# --- TITLE & RATE ---
st.markdown('<div class="title">📊 Forecast Budget Estimator</div>', unsafe_allow_html=True)

exchange_rate = get_usd_to_idr_rate()
st.info(f"💱 Current Exchange Rate: 1 USD = Rp {exchange_rate:,.0f}")

# --- BULK FORECAST ---
st.subheader("📂 Bulk Forecast from CSV")
uploaded_file = st.file_uploader("Upload CSV file (target_km, dax_number, month_estimation)", type=["csv"])

if uploaded_file:
    df = pd.read_csv(uploaded_file)
    required_cols = {'target_km', 'dax_number', 'month_estimation'}
    if required_cols.issubset(df.columns):
        st.success("✅ File successfully uploaded and read.")
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
        st.error("⚠️ CSV file is missing required columns!")

# --- MANUAL INPUT ---
st.subheader("🧮 Manual Calculation")

# Dua kolom: kiri untuk input, kanan untuk hasil
col1, col2 = st.columns([1, 1.2])

with col1:
    with st.form("forecast_form"):
        st.markdown("#### 🔧 Input Parameters")
        target_km = st.number_input("📏 Total Target KM", min_value=0.0, value=0.0, step=100.0)
        dax_number = st.number_input("👷 Number of DAX", min_value=1, value=1, step=1)
        month_estimation = st.number_input("🗓️ Duration (months)", min_value=0.1, value=1.0, step=0.1, format="%.1f")
        submitted = st.form_submit_button("🧮 Calculate Budget")

with col2:
    if submitted:
        result = forecast_budget(target_km, dax_number, month_estimation, exchange_rate=exchange_rate)
        st.markdown("#### 📈 Forecast Result")

        # Bullet list komponen biaya
        bullets = ""
        for key, value in result.items():
            if "Total Forecast Budget" in key:
                continue
            elif "Month" in key:
                bullets += f"- **{key}**: {value} bulan\n"
            elif "USD" in key:
                continue
            else:
                bullets += f"- **{key}**: {format_currency(value)}\n"
        st.markdown(bullets)

        # Total dalam 1 baris: IDR dan USD
        st.markdown(
            f"""
            <div class="result-box">
                <strong>Total Forecast Budget:</strong> {format_currency(result["Total Forecast Budget"])} &nbsp;&nbsp; | &nbsp;&nbsp;
                <strong>USD:</strong> ${result["Total Forecast Budget (USD)"]:,.2f}
            </div>
            """,
            unsafe_allow_html=True
        )
