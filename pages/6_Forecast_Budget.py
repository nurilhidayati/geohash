import streamlit as st

def forecast_budget(
    target_km: float,
    harga_ukm: float,
    dax_number: int,
    month_estimation: float,
    insurance_per_dax_per_month: float = 132000,
    dataplan_per_dax_per_month: float = 450000
):
    # Basic Incentive dan Bonus
    basic_incentive = target_km * harga_ukm
    bonus_coverage = target_km * harga_ukm  # >95% Bonus Coverage

    # Insurance dan Dataplan
    insurance = insurance_per_dax_per_month * dax_number * month_estimation
    dataplan = dataplan_per_dax_per_month * dax_number * month_estimation

    # Miscellaneous 5%
    total_before_misc = basic_incentive + bonus_coverage + insurance + dataplan
    miscellaneous = total_before_misc * 0.05

    # Total final
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

# Streamlit UI
st.title("📊 Forecast Budget Estimator")

st.header("🔧 Input Parameters")
target_km = st.number_input("📏 Total Target KM", min_value=0.0, value=10000.0, step=100.0)
harga_ukm = st.number_input("💰 Harga per KM (UKM)", min_value=0.0, value=5000.0, step=100.0)
dax_number = st.number_input("👷 Jumlah DAX", min_value=1, value=10, step=1)
month_estimation = st.number_input("🗓️ Estimasi Bulan", min_value=0.1, value=3.0, step=0.1, format="%.1f")

if st.button("🧮 Hitung Budget"):
    result = forecast_budget(target_km, harga_ukm, dax_number, month_estimation)

    st.subheader("📑 Hasil Perhitungan:")
    for key, value in result.items():
        if "Month" in key:
            st.write(f"**{key}:** {value} bulan")
        else:
            st.write(f"**{key}:** Rp {value:,.0f}")
