
import streamlit as st
import pandas as pd
import yfinance as yf
import matplotlib.pyplot as plt
from datetime import datetime

st.set_page_config(layout="wide", page_title="IBIT Strategy Dashboard", page_icon="📊")

# --- Header ---
st.title("📊 IBIT Strategy Dashboard v5")
st.markdown("### Bitcoin Power Law Strategy Engine (Goal: 1 BTC = 1756 IBIT Shares)")

# --- Sidebar Inputs ---
st.sidebar.header("Upload Portfolio")
uploaded_file = st.sidebar.file_uploader("Upload your Excel portfolio file", type=["xlsx"])

# --- Live BTC/IBIT Price ---
btc_price = yf.Ticker("BTC-USD").history(period="1d")["Close"][-1]
ibit_price = yf.Ticker("IBIT").history(period="1d")["Close"][-1]
st.sidebar.metric("📈 BTC Price", f"${btc_price:,.2f}")
st.sidebar.metric("🟠 IBIT Price", f"${ibit_price:,.2f}")

# --- Power Law Chart ---
st.markdown("#### 📈 BTC Price vs Power Law Model")

years = list(range(2013, 2030))
fair_value = [10, 50, 250, 1000, 4000, 16000, 64000, 256000]
btc_actual = [10, 100, 400, 1000, 18000, 30000, btc_price]

fig, ax = plt.subplots()
ax.plot(years[:len(fair_value)], fair_value, label="Power Law Model", linestyle="--")
ax.plot(years[:len(btc_actual)], btc_actual, label="BTC Price", linewidth=2)
ax.set_yscale("log")
ax.set_title("BTC vs Power Law Model (Log Scale)")
ax.set_ylabel("Price (Log USD)")
ax.set_xlabel("Year")
ax.legend()
st.pyplot(fig)

# --- Upload Portfolio & Commentary ---
if uploaded_file:
    df = pd.read_excel(uploaded_file)

    st.markdown("#### 📂 Uploaded Portfolio Summary")
    st.dataframe(df)

    ibit_shares = df[df["Type"] == "IBIT Share"]["Quantity"].sum()
    fbtc_shares = df[df["Type"] == "FBTC Share"]["Quantity"].sum()
    ibit_equiv = ibit_shares + fbtc_shares  # FBTC converted to IBIT directly

    st.markdown(f"**📌 Current IBIT-Equivalent Shares:** {ibit_equiv}")
    goal = 1756
    percent_to_goal = min(100, round((ibit_equiv / goal) * 100, 2))
    st.progress(percent_to_goal / 100, text=f"{percent_to_goal}% toward 1 BTC (1756 IBIT)")

    st.markdown("#### 🧠 Strategy Commentary")

    for i, row in df.iterrows():
        if row["Type"] == "Call Option":
            strike = row["Strike"]
            expiry = row["Expiry"]
            delta = row.get("Delta", 0.5)
            days_left = (pd.to_datetime(expiry) - datetime.now()).days

            price_target = 120
            in_the_money = ibit_price > strike
            recommendation = "🟩 Hold"
            rationale = "Good delta and time left."

            if days_left < 90 and delta < 0.4:
                recommendation = "🟧 Monitor"
                rationale = "Low delta + near expiry."
            if delta < 0.2:
                recommendation = "🟥 Consider Selling"
                rationale = "Low chance of profitability unless IBIT spikes."
            if in_the_money and delta > 0.7:
                recommendation = "🟩 Hold or Exercise"
                rationale = "Strong delta and ITM."

            st.markdown(f"- **{expiry} $ {strike}C** → {recommendation} ({rationale})")

else:
    st.info("Upload your portfolio Excel file to see commentary and goal tracking.")
