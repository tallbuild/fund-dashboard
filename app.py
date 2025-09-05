import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import requests
import datetime

# -----------------------
# ฟังก์ชันดึงข้อมูล NAV (Mockup ใช้ CSV แทน)
# -----------------------
def get_fund_data(fund_code):
    # ในเวอร์ชันจริงจะดึงจาก Morningstar
    url = f"https://raw.githubusercontent.com/yourusername/fund-dashboard/main/data/{fund_code}.csv"
    df = pd.read_csv(url, parse_dates=["date"])
    return df

# -----------------------
# Indicator (MA, RSI)
# -----------------------
def add_indicators(df):
    df["MA20"] = df["nav"].rolling(20).mean()
    df["MA50"] = df["nav"].rolling(50).mean()

    delta = df["nav"].diff()
    gain = (delta.where(delta > 0, 0)).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    rs = gain / loss
    df["RSI"] = 100 - (100 / (1 + rs))
    return df

def generate_signal(df):
    last = df.iloc[-1]
    if last["RSI"] < 30:
        return "สัญญาณซื้อ (Oversold)"
    elif last["RSI"] > 70:
        return "สัญญาณขาย (Overbought)"
    else:
        return "ถือรอ"

# -----------------------
# UI
# -----------------------
st.title("📊 Fund Dashboard")
funds = ["ONE-UGG-RA", "K-GHEALTH", "K-EUROPE-A(D)", "ONE-BTCETFOF"]

selected = st.selectbox("เลือกกองทุน", funds)

df = get_fund_data(selected)
df = add_indicators(df)

signal = generate_signal(df)
st.write(f"📌 {selected} : {signal}")

fig, ax = plt.subplots()
ax.plot(df["date"], df["nav"], label="NAV")
ax.plot(df["date"], df["MA20"], label="MA20")
ax.plot(df["date"], df["MA50"], label="MA50")
ax.legend()
st.pyplot(fig)
