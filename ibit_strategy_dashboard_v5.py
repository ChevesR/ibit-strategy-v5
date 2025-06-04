
import streamlit as st
import pandas as pd
import yfinance as yf
import matplotlib.pyplot as plt
from datetime import datetime
import numpy as np
from streamlit_autorefresh import st_autorefresh

st.set_page_config(layout="wide", page_title="IBIT Strategy Dashboard", page_icon="📊")

# Refresh every minute to keep price data current
st_autorefresh(interval=60_000, key="data_refresh")

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

# Pull full BTC history and fit a simple power law on log-log scale
btc_hist = yf.Ticker("BTC-USD").history(period="max")
btc_hist = btc_hist[btc_hist["Close"] > 0]
btc_hist["Days"] = (btc_hist.index - btc_hist.index[0]).days + 1

log_x = np.log(btc_hist["Days"])  # time since inception
log_y = np.log(btc_hist["Close"])
slope, intercept = np.polyfit(log_x, log_y, 1)
btc_hist["Model"] = np.exp(intercept) * btc_hist["Days"] ** slope

fig, ax = plt.subplots()
ax.plot(btc_hist.index, btc_hist["Close"], label="BTC Price", linewidth=2)
ax.plot(btc_hist.index, btc_hist["Model"], label="Power Law Fit", linestyle="--")
ax.set_yscale("log")
ax.set_title("BTC vs Power Law Model (Log Scale)")
ax.set_ylabel("Price (USD)")
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

    # --- Portfolio Value & Projection ---
    current_value = ibit_equiv * ibit_price
    st.markdown(f"**💰 Current Portfolio Value:** ${current_value:,.2f}")

    # Project future BTC price using the power law model
    days_ahead = np.arange(0, 365 * 3 + 1, 30)
    future_dates = btc_hist.index[-1] + pd.to_timedelta(days_ahead, unit="D")
    future_btc = np.exp(intercept) * (btc_hist["Days"].max() + days_ahead) ** slope
    future_value = future_btc * (ibit_equiv / 1756)

    pred_1yr_value = future_value[12]  # 365 days / 30 step ~= index 12
    st.metric("Projected Value in 1 Year", f"${pred_1yr_value:,.2f}")

    fig_future, ax_future = plt.subplots()
    ax_future.plot(future_dates, future_value, label="Projected Value")
    ax_future.set_ylabel("Value (USD)")
    ax_future.set_title("Projected Portfolio Value (Power Law)")
    ax_future.legend()
    st.pyplot(fig_future)

    # Visual tracker as a pie chart showing progress toward 1756 shares
    fig_progress, ax_progress = plt.subplots()
    ax_progress.pie(
        [ibit_equiv, max(goal - ibit_equiv, 0)],
        labels=["Owned", "Remaining"],
        colors=["#FF9900", "#CCCCCC"],
        startangle=90,
        counterclock=False,
        autopct=lambda pct: f"{pct:.1f}%",
    )
    ax_progress.axis("equal")
    st.pyplot(fig_progress)

    st.markdown("#### 🧠 Strategy Commentary")

    for _, row in df.iterrows():
        if row["Type"] == "Call Option":
            strike = row["Strike"]
            expiry = row["Expiry"]
            delta = row.get("Delta", 0.5)
            days_left = (pd.to_datetime(expiry) - datetime.now()).days

            in_the_money = ibit_price > strike
            status = "🟩 Hold"
            rationale = [f"Δ={delta:.2f}", f"{days_left}d left"]

            if days_left < 30 or delta < 0.2:
                status = "🟥 Consider Selling"
            elif days_left < 90 or delta < 0.4:
                status = "🟧 Monitor"
            if in_the_money and delta > 0.7:
                status = "🟩 Hold or Exercise"
                rationale.append("ITM")
            elif not in_the_money:
                rationale.append("OTM")

            st.markdown(
                f"- **{expiry} $ {strike}C** → {status} ({', '.join(rationale)})"
            )

else:
    st.info("Upload your portfolio Excel file to see commentary and goal tracking.")
