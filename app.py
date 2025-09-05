# app.py
import os
import pandas as pd
import streamlit as st
from datetime import datetime
import requests
from bs4 import BeautifulSoup
import matplotlib.pyplot as plt

# ----------------------------
# Config
# ----------------------------
DATA_DIR = "data"
FUND_LIST = ["K-EUROPE-A(D)", "ONE-UGG-RA", "K-GHEALTH", "TISCOG"]

if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

# ----------------------------
# Fetch NAV: Morningstar
# ----------------------------
def fetch_nav_morningstar(fund_name):
    st.info(f"🌐 ลองดึง NAV ของ {fund_name} จาก Morningstar ...")
    try:
        url = "https://www.morningstarthailand.com/th/funds/snapshot/snapshot.aspx?id=F000000RG5&lang=en-TH"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        nav_value = soup.find("span", {"id": "ctl00_ContentPlaceHolder1_lblNAV"})
        nav_date = soup.find("span", {"id": "ctl00_ContentPlaceHolder1_lblDate"})
        if nav_value and nav_date:
            nav = float(nav_value.text.strip())
            date = pd.to_datetime(nav_date.text.strip(), dayfirst=True)
            return pd.DataFrame({"date":[date],"nav":[nav]})
    except:
        return pd.DataFrame(columns=["date","nav"])
    return pd.DataFrame(columns=["date","nav"])

# ----------------------------
# Fetch NAV: SET Fund (ตัวอย่าง)
# ----------------------------
def fetch_nav_setfund(fund_name):
    st.info(f"🌐 ลองดึง NAV ของ {fund_name} จาก SET Fund ...")
    # ตัวอย่าง dummy (ต้องใส่ scraping/API จริง)
    try:
        # URL ของ SET Fund
        # response = requests.get(...)
        # parse HTML ...
        return pd.DataFrame(columns=["date","nav"])  # placeholder
    except:
        return pd.DataFrame(columns=["date","nav"])

# ----------------------------
# Fetch NAV: Yahoo Finance (สำหรับ ETF ต่างประเทศ)
# ----------------------------
def fetch_nav_yahoo(fund_name):
    st.info(f"🌐 ลองดึง NAV ของ {fund_name} จาก Yahoo Finance ...")
    try:
        # ตัวอย่าง placeholder
        return pd.DataFrame(columns=["date","nav"])
    except:
        return pd.DataFrame(columns=["date","nav"])

# ----------------------------
# Fetch NAV หลายแหล่ง (fallback)
# ----------------------------
def fetch_nav_multi_source(fund_name):
    sources = [fetch_nav_morningstar, fetch_nav_setfund, fetch_nav_yahoo]
    for func in sources:
        df = func(fund_name)
        if not df.empty:
            st.success(f"✅ ดึงข้อมูล {fund_name} สำเร็จจาก {func.__name__}")
            return df
    st.error(f"❌ ไม่สามารถดึงข้อมูล {fund_name} จากทุกแหล่งได้")
    return pd.DataFrame(columns=["date","nav"])

# ----------------------------
# Load / update CSV
# ----------------------------
def get_fund_data(fund_name):
    file_path = os.path.join(DATA_DIR, f"{fund_name}.csv")
    fetch_online_flag = True
    if os.path.exists(file_path):
        mtime = os.path.getmtime(file_path)
        file_date = datetime.fromtimestamp(mtime).date()
        if file_date == datetime.today().date():
            fetch_online_flag = False

    if fetch_online_flag:
        df_online = fetch_nav_multi_source(fund_name)
        if not df_online.empty:
            with st.spinner(f"💾 บันทึก CSV ของ {fund_name} ..."):
                df_online.to_csv(file_path, index=False)
        else:
            if not os.path.exists(file_path):
                pd.DataFrame({"date":[],"nav":[]}).to_csv(file_path,index=False)

    # Load CSV
    if not os.path.exists(file_path) or os.path.getsize(file_path) == 0:
        pd.DataFrame({"date":[],"nav":[]}).to_csv(file_path,index=False)
    try:
        df = pd.read_csv(file_path)
        if "date" not in df.columns or "nav" not in df.columns:
            df = pd.DataFrame(columns=["date","nav"])
        else:
            df["date"] = pd.to_datetime(df["date"])
    except:
        df = pd.DataFrame(columns=["date","nav"])

    # คำนวณ MA / Signal
    if not df.empty:
        df = df.sort_values("date")
        df["MA5"] = df["nav"].rolling(5).mean()
        df["MA20"] = df["nav"].rolling(20).mean()
        df["Signal"] = ""
        for i in range(1,len(df)):
            if df["MA5"].iloc[i] > df["MA20"].iloc[i] and df["MA5"].iloc[i-1] <= df["MA20"].iloc[i-1]:
                df.loc[df.index[i],"Signal"]="BUY"
            elif df["MA5"].iloc[i] < df["MA20"].iloc[i] and df["MA5"].iloc[i-1] >= df["MA20"].iloc[i-1]:
                df.loc[df.index[i],"Signal"]="SELL"

    return df

# ----------------------------
# Streamlit App
# ----------------------------
st.title("📈 Fund Dashboard (Multi-Source)")

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
if df.empty:
    st.warning("ไม่มีข้อมูลให้แสดง")
else:
    st.dataframe(df.fillna(""))

# Plot Graph
if not df.empty and "nav" in df.columns:
    st.subheader("กราฟ NAV + MA")
    fig, ax = plt.subplots(figsize=(10,5))
    ax.plot(df["date"], df["nav"], label="NAV", marker='o')
    if "MA5" in df.columns:
        ax.plot(df["date"], df["MA5"], label="MA5")
    if "MA20" in df.columns:
        ax.plot(df["date"], df["MA20"], label="MA20")

    # Plot BUY/SELL
    if "Signal" in df.columns:
        buy_points = df[df["Signal"]=="BUY"]
        sell_points = df[df["Signal"]=="SELL"]
        if not buy_points.empty:
            ax.scatter(buy_points["date"], buy_points["nav"], marker="^", color="green", s=100, label="BUY")
        if not sell_points.empty:
            ax.scatter(sell_points["date"], sell_points["nav"], marker="v", color="red", s=100, label="SELL")

    ax.set_xlabel("Date")
    ax.set_ylabel("NAV")
    ax.legend()
    ax.grid(True)
    st.pyplot(fig)