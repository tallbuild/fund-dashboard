# app.py
import os
import pandas as pd
import streamlit as st
from datetime import datetime
import requests
from bs4 import BeautifulSoup

# ----------------------------
# Config
# ----------------------------
DATA_DIR = "data"
FUND_LIST = ["K-EUROPE-A(D)", "ONE-UGG-RA", "K-GHEALTH", "TISCOG"]

if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

# ----------------------------
# Function: fetch NAV online
# ----------------------------
def fetch_nav_online(fund_name):
    """
    ดึง NAV จาก Morningstar Thailand (ตัวอย่าง)
    """
    st.info(f"🌐 กำลังดึงข้อมูลออนไลน์ของ {fund_name} ...")
    try:
        # URL ตัวอย่าง (ปรับตาม fund_name จริง)
        url = "https://www.morningstarthailand.com/th/funds/snapshot/snapshot.aspx?id=F000000RG5&lang=en-TH"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")

        # ดึง NAV ล่าสุด (ตัวอย่าง)
        nav_value = soup.find("span", {"id": "ctl00_ContentPlaceHolder1_lblNAV"})
        nav_date = soup.find("span", {"id": "ctl00_ContentPlaceHolder1_lblDate"})

        if nav_value and nav_date:
            nav = float(nav_value.text.strip())
            date = pd.to_datetime(nav_date.text.strip(), dayfirst=True)
            df = pd.DataFrame({"date": [date], "nav": [nav]})
            return df
        else:
            st.warning(f"⚠️ ไม่พบข้อมูล NAV ของ {fund_name}")
            return pd.DataFrame(columns=["date","nav"])

    except Exception as e:
        st.error(f"❌ Fetch NAV ของ {fund_name} ล้มเหลว: {e}")
        return pd.DataFrame(columns=["date","nav"])

# ----------------------------
# Function: get fund data
# ----------------------------
def get_fund_data(fund_name):
    file_path = os.path.join(DATA_DIR, f"{fund_name}.csv")

    # ----------------------------
    # Fetch online if file missing or outdated
    # ----------------------------
    fetch_online_flag = True
    if os.path.exists(file_path):
        mtime = os.path.getmtime(file_path)
        file_date = datetime.fromtimestamp(mtime).date()
        if file_date == datetime.today().date():
            fetch_online_flag = False

    if fetch_online_flag:
        df_online = fetch_nav_online(fund_name)
        if not df_online.empty:
            with st.spinner(f"💾 กำลังบันทึก CSV ของ {fund_name} ..."):
                df_online.to_csv(file_path, index=False)
        else:
            # สร้าง CSV เปล่าถ้าไม่มี
            if not os.path.exists(file_path):
                pd.DataFrame({"date":[], "nav":[]}).to_csv(file_path, index=False)

    # ----------------------------
    # Load CSV
    # ----------------------------
    if not os.path.exists(file_path) or os.path.getsize(file_path) == 0:
        st.warning(f"⚠️ ไฟล์ CSV ของ {fund_name} ว่างหรือไม่พบไฟล์ สร้างไฟล์เปล่าใหม่")
        pd.DataFrame({"date":[], "nav":[]}).to_csv(file_path, index=False)

    try:
        df = pd.read_csv(file_path)
        if "date" not in df.columns or "nav" not in df.columns:
            st.warning(f"⚠️ CSV ของ {fund_name} ไม่มีคอลัมน์ date/nav สร้าง DataFrame เปล่าแทน")
            df = pd.DataFrame(columns=["date","nav"])
        else:
            df["date"] = pd.to_datetime(df["date"])
    except Exception as e:
        st.error(f"❌ อ่านไฟล์ CSV ของ {fund_name} ไม่สำเร็จ: {e}")
        df = pd.DataFrame(columns=["date","nav"])

    # ----------------------------
    # คำนวณ MA และ Signal
    # ----------------------------
    if df.empty:
        return df

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

# ----------------------------
# Streamlit App
# ----------------------------
st.title("📈 Fund Dashboard (Thai)")

selected_fund = st.selectbox("เลือกกองทุน", FUND_LIST)

df = get_fund_data(selected_fund)

# Latest Signal
if df.empty or "Signal" not in df.columns:
    latest_signal = "HOLD"
else:
    latest_signal = df["Signal"].replace("", "HOLD").iloc[-1]

st.subheader(f"Latest Signal: {latest_signal}")

# Show DataFrame
st.subheader("NAV Data")
st.dataframe(df)

# Plot Graph
if not df.empty:
    st.subheader("กราฟ NAV + MA")
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(10,5))
    ax.plot(df["date"], df["nav"], label="NAV", marker='o')
    ax.plot(df["date"], df["MA5"], label="MA5")
    ax.plot(df["date"], df["MA20"], label="MA20")

    # Plot BUY/SELL points
    buy_points = df[df["Signal"]=="BUY"]
    sell_points = df[df["Signal"]=="SELL"]
    ax.scatter(buy_points["date"], buy_points["nav"], marker="^", color="green", s=100, label="BUY")
    ax.scatter(sell_points["date"], sell_points["nav"], marker="v", color="red", s=100, label="SELL")

    ax.set_xlabel("Date")
    ax.set_ylabel("NAV")
    ax.legend()
    ax.grid(True)
    st.pyplot(fig)