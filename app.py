import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import os
import requests
from bs4 import BeautifulSoup
from datetime import datetime

st.set_page_config(layout="wide")
st.title("📊 Fund Dashboard - สัญญาณล่าสุดทุกกองทุน")

DATA_DIR = "data"
os.makedirs(DATA_DIR, exist_ok=True)

# รายชื่อกองทุน (ใช้ไฟล์ CSV หรือกำหนดชื่อกองทุนออนไลน์)
funds = ["ONE-UGG-RA", "K-GHEALTH", "K-EUROPE-A(D)", "ONE-BTCETFOF"]

def fetch_nav_online(fund_name):
    """
    ตัวอย่าง fetch online จากเว็บไซต์กองทุน
    ให้ปรับ URL / parsing ตามเว็บจริงของกองทุน
    """
    with st.spinner(f"🔄 กำลังดึงข้อมูล NAV ของ {fund_name}..."):
        # --- ตัวอย่าง mockup URL ---
        url = f"https://www.example.com/{fund_name}"
        try:
            r = requests.get(url)
            r.raise_for_status()
            soup = BeautifulSoup(r.text, "html.parser")
            table = soup.find("table")
            if table:
                df = pd.read_html(str(table))[0]
                df.columns = ["date", "nav"]
                df["date"] = pd.to_datetime(df["date"])
                return df
        except Exception as e:
            st.error(f"❌ ไม่สามารถดึง NAV ของ {fund_name} ได้: {e}")
    return None

def get_fund_data(fund_name):
    file_path = os.path.join(DATA_DIR, f"{fund_name}.csv")
    fetch_online_flag = True

    if os.path.exists(file_path):
        mtime = os.path.getmtime(file_path)
        file_date = datetime.fromtimestamp(mtime).date()
        if file_date == datetime.today().date():
            fetch_online_flag = False

    if fetch_online_flag:
        df_online = fetch_nav_online(fund_name)
        if df_online is not None:
            with st.spinner(f"💾 กำลังบันทึก CSV ของ {fund_name}..."):
                df_online.to_csv(file_path, index=False)

    with st.spinner(f"📂 กำลังโหลด CSV ของ {fund_name}..."):
        df = pd.read_csv(file_path, parse_dates=["date"])

    df = df.sort_values("date")
    df["MA5"] = df["nav"].rolling(5).mean()
    df["MA20"] = df["nav"].rolling(20).mean()
    df["Signal"] = ""
    for i in range(1, len(df)):
        if df["MA5"].iloc[i] > df["MA20"].iloc[i] and df["MA5"].iloc[i-1] <= df["MA20"].iloc[i-1]:
            df.loc[df.index[i], "Signal"] = "BUY"
        elif df["MA5"].iloc[i] < df["MA20"].iloc[i] and df["MA5"].iloc[i-1] >= df["MA20"].iloc[i-1]:
            df.loc[df.index[i], "Signal"] = "SELL"
    return df

# 🔔 สรุปสัญญาณล่าสุดทุกกองทุน
st.subheader("🔔 สัญญาณล่าสุดของทุกกองทุน")
for f in funds:
    df = get_fund_data(f)
    latest_signal = df["Signal"].replace("", "HOLD").iloc[-1]
    if latest_signal == "BUY":
        st.markdown(f"<div style='background-color: #a8e6a1; padding:5px; font-weight:bold;'>{f}: {latest_signal}</div>", unsafe_allow_html=True)
    elif latest_signal == "SELL":
        st.markdown(f"<div style='background-color: #f28b82; padding:5px; font-weight:bold;'>{f}: {latest_signal}</div>", unsafe_allow_html=True)
    else:
        st.markdown(f"<div style='background-color: #fff59d; padding:5px; font-weight:bold;'>{f}: {latest_signal}</div>", unsafe_allow_html=True)

# แสดงกราฟ NAV + MA + จุด Buy/Sell ของแต่ละกองทุน
for f in funds:
    st.markdown(f"### 📈 {f}")
    df = get_fund_data(f)

    fig, ax = plt.subplots(figsize=(8,3))
    ax.plot(df["date"], df["nav"], label="NAV", color="blue")
    ax.plot(df["date"], df["MA5"], label="MA5", color="green")
    ax.plot(df["date"], df["MA20"], label="MA20", color="red")

    buy_signals = df[df["Signal"] == "BUY"]
    sell_signals = df[df["Signal"] == "SELL"]
    ax.scatter(buy_signals["date"], buy_signals["nav"], marker="^", color="green", s=80, label="BUY")
    ax.scatter(sell_signals["date"], sell_signals["nav"], marker="v", color="red", s=80, label="SELL")

    ax.set_xlabel("Date")
    ax.set_ylabel("NAV")
    ax.legend()
    plt.xticks(rotation=45)
    st.pyplot(fig)