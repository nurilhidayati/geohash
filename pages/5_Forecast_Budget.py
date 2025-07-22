import streamlit as st
import requests
import pandas as pd

# === PAGE CONFIG ===
st.set_page_config(page_title="💱 Forecast & Currency Converter", layout="centered")

# === CSS STYLING ===
st.markdown("""
    <style>
    .title {
        text-align: center;
        font-size: 36px;
        font-weight: bold;
        color: #f1c40f;
    }
    .result-box {
        background-color: #1e1e2f;
        border: 1px solid #444;
        border-radius: 10px;
        padding: 15px;
        margin-top: 10px;
        color: white;
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

# === EXCHANGE RATE FUNCTION ===
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

def format_currency(amount, currency="IDR"):
    if currency == "IDR":
        return f"Rp {amount:,.0f}"
    else:
        return f"${amount:,.2f}"

# === APP HEADER ===
st.markdown('<div class="title">💱 Currency Converter & Forecast Budget</div>', unsafe_allow_html=True)

# === EXCHANGE RATE DATA ===
rates = get_exchange_rates()
st.info(f"💸 **Exchange Rate:** 1 USD = Rp {rates['usd_to_idr']:,.0f} (Last updated: {rates['last_updated']})")

# === CURRENCY CONVERTER ===
st.markdown("---")
st.markdown('<h3 style="color:#f1c40f;">🔄 Currency Converter</h3>', unsafe_allow_html=True)

st.markdown("""
<style>
.radio-label {
    font-size: 18px;
    font-weight: 600;
    color: white;
    margin-bottom: 8px;
}
.input-label {
    font-size: 16px;
    color: #dddddd;
}
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="radio-label">🧭 Choose conversion direction:</div>', unsafe_allow_html=True)

conversion_direction = st.radio("", ("🇮🇩 IDR ➡️ USD", "💵 USD ➡️ IDR"))

if conversion_direction == "🇮🇩 IDR ➡️ USD":
    st.markdown('<div class="input-label">💰 Enter amount in Rupiah (IDR):</div>', unsafe_allow_html=True)
    idr = st.number_input("", min_value=0.0, step=1000.0, format="%.2f", key="idr_input")
    if idr > 0:
        usd = idr * rates["idr_to_usd"]
        st.success(f"✅ {format_currency(idr, 'IDR')} = {format_currency(usd, 'USD')}")
else:
    st.markdown('<div class="input-label">💵 Enter amount in USD:</div>', unsafe_allow_html=True)
    usd = st.number_input("", min_value=0.0, step=10.0, format="%.2f", key="usd_input")
    if usd > 0:
        idr = usd * rates["usd_to_idr"]
        st.success(f"✅ {format_currency(usd, 'USD')} = {format_currency(idr, 'IDR')}")


# === FORECAST FUNCTION ===
def forecast_budget(target_km, dax_number, month_estimation,
                    harga_ukm=8000,
                    insurance_per_dax_per_month=132200,
                    dataplan_per_dax_per_month=450000,
                    exchange_rate=16000):
    basic_incentive = target_km * harga_ukm
    bonus_coverage = basic_incentive
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

# === BULK FORECAST ===
st.subheader("📂 Bulk Forecast from CSV")
uploaded_file = st.file_uploader("Upload CSV (target_km, dax_number, month_estimation)", type=["csv"])
if uploaded_file:
    df = pd.read_csv(uploaded_file)
    required_cols = {'target_km', 'dax_number', 'month_estimation'}
    if required_cols.issubset(df.columns):
        st.success("✅ File loaded.")
        for idx, row in df.iterrows():
            result = forecast_budget(
                target_km=row['target_km'],
                dax_number=int(row['dax_number']),
                month_estimation=row['month_estimation'],
                exchange_rate=rates["usd_to_idr"]
            )
            st.markdown(f"#### 🔹 Baris ke-{idx + 1}")
            for key, value in result.items():
                if "USD" in key:
                    st.markdown(f'<div class="result-box"><strong>{key}:</strong> ${value:,.2f}</div>', unsafe_allow_html=True)
                elif "Month" in key:
                    st.markdown(f'<div class="result-box"><strong>{key}:</strong> {value} bulan</div>', unsafe_allow_html=True)
                else:
                    st.markdown(f'<div class="result-box"><strong>{key}:</strong> Rp {value:,.0f}</div>', unsafe_allow_html=True)
    else:
        st.error("⚠️ Missing columns in CSV.")

# === MANUAL INPUT FORECAST ===
st.subheader("🧮 Manual Forecast Calculator")
col1, col2 = st.columns([1, 1.2])

with col1:
    with st.form("manual_forecast"):
        st.markdown("#### 🔧 Input Parameters")
        target_km = st.number_input("📏 Target KM", min_value=0.0, step=100.0)
        dax_number = st.number_input("👷 DAX count", min_value=1, step=1)
        month_est = st.number_input("🗓️ Duration (months)", min_value=0.1, step=0.1, format="%.1f")
        submitted = st.form_submit_button("🧮 Calculate")

with col2:
    if submitted:
        result = forecast_budget(target_km, dax_number, month_est, exchange_rate=rates["usd_to_idr"])
        st.markdown("#### 📈 Forecast Result")
        # Bullet list
        bullets = ""
        for k, v in result.items():
            if "Total Forecast Budget" in k or "USD" in k:
                continue
            elif "Month" in k:
                bullets += f"- **{k}**: {v} bulan\n"
            else:
                bullets += f"- **{k}**: {format_currency(v)}\n"
        st.markdown(bullets)
        # Highlight Total
        st.markdown(f"""
            <div class="result-box">
            <strong>Total Forecast Budget:</strong> {format_currency(result['Total Forecast Budget'])} &nbsp;&nbsp;|&nbsp;&nbsp;
            <strong>USD:</strong> ${result['Total Forecast Budget (USD)']:,.2f}
            </div>
        """, unsafe_allow_html=True)
