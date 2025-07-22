import streamlit as st
import requests
import pandas as pd
import openpyxl
from openpyxl.utils.dataframe import dataframe_to_rows
from io import BytesIO


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
st.subheader("🔄 Currency Converter")

conversion_direction = st.radio("Choose conversion direction:", ("IDR to USD", "USD to IDR"))

if conversion_direction == "IDR to USD":
    idr = st.number_input("Enter amount in Rupiah (IDR):", min_value=0.0, step=1000.0)
    if idr > 0:
        usd = idr * rates["idr_to_usd"]
        st.success(f"{format_currency(idr, 'IDR')} = {format_currency(usd, 'USD')}")
else:
    usd = st.number_input("Enter amount in USD:", min_value=0.0, step=10.0)
    if usd > 0:
        idr = usd * rates["usd_to_idr"]
        st.success(f"{format_currency(usd, 'USD')} = {format_currency(idr, 'IDR')}")

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
import openpyxl
from openpyxl.utils.dataframe import dataframe_to_rows
from io import BytesIO

# === BULK FORECAST ===
st.subheader("📂 Bulk Forecast from CSV")
uploaded_file = st.file_uploader("Upload CSV (city, target_km, dax_number, month_estimation)", type=["csv"])
if uploaded_file:
    df = pd.read_csv(uploaded_file)
    required_cols = {'city', 'target_km', 'dax_number', 'month_estimation'}
    if required_cols.issubset(df.columns):
        st.success("✅ File loaded.")

        # List untuk menyimpan hasil forecast
        forecast_results = []
        for idx, row in df.iterrows():
            result = forecast_budget(
                target_km=row['target_km'],
                dax_number=int(row['dax_number']),
                month_estimation=row['month_estimation'],
                exchange_rate=rates["usd_to_idr"]
            )
            forecast_results.append({
                "City": row['city'],
                "UKM Target": row['target_km'],
                "Basic Incentive": result["Basic Incentive"],
                ">95% Bonus Coverage": result[">95% Bonus Coverage"],
                "Insurance": result["Insurance"],
                "Data Plan": result["Dataplan"],
                "Miscellaneous (5%)": result["Miscellaneous (5%)"],
                "Estimation Incentive (IDR)": result["Total Forecast Budget"],
                "Estimation Incentive (USD)": result["Total Forecast Budget (USD)"]
            })

        df_forecast = pd.DataFrame(forecast_results)

        # === Load template Excel and append ===
        path_template = "/pages/forecast_budget.xlsx"
        wb = openpyxl.load_workbook(path_template)
        ws = wb.active

        for r in dataframe_to_rows(df_forecast, index=False, header=False):
            ws.append(r)

        output_excel = BytesIO()
        wb.save(output_excel)

        st.success("✅ Forecast berhasil dimasukkan ke Excel!")

        st.download_button(
            label="📥 Download Forecast Excel",
            data=output_excel.getvalue(),
            file_name="forecast_budget_filled.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    else:
        st.error("⚠️ Kolom CSV harus memiliki: city, target_km, dax_number, month_estimation")


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
