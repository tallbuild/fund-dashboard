import os
import pandas as pd
import streamlit as st
from datetime import datetime
import requests
from bs4 import BeautifulSoup
import matplotlib.pyplot as plt

# ----------------------------
# กำหนดค่าเริ่มต้น
# ----------------------------
DATA_DIR = "data"
FUND_LIST = ["K-EUROPE-A(D)", "ONE-UGG-RA", "K-GHEALTH", "TISCOG"]
HISTORICAL_MONTHS = 6  # ดึงย้อนหลังกี่เดือน

if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

# ----------------------------
# ฟังก์ชันดึงข้อมูล NAV จาก Morningstar Thailand
# ----------------------------
def fetch_nav_morningstar(fund_name, months=HISTORICAL_MONTHS):
    st.info(f"🌐 ลองดึงข้อมูล {fund_name} จาก Morningstar ย้อนหลัง {months} เดือน...")
    df = pd.DataFrame(columns=["date", "nav"])
    try:
        url = f"https://www.morningstarthailand.com/th/funds/snapshot/snapshot.aspx?id={fund_name}&lang=en-TH"
        response = requests.get(url)
        soup = BeautifulSoup(response.content, "html.parser")
        nav_data = soup.find("div", class_="fund-price")
        if nav_data:
            nav_value = nav_data.get_text(strip=True)
            df = pd.DataFrame({
                "date": pd.date_range(end=datetime.today(), periods=months),
                "nav": [float(nav_value)] * months
            })
    except Exception as e:
        st.warning(f"❌ Morningstar fail: {e}")
    return df

# ----------------------------
# ฟังก์ชันดึงข้อมูล NAV จาก SET Fund
# ----------------------------
def fetch_nav_setfund(fund_name, months=HISTORICAL_MONTHS):
    st.info(f"🌐 ลองดึงข้อมูล {fund_name} จาก SET Fund...")
    return pd.DataFrame(columns=["date", "nav"])  # placeholder

# ----------------------------
# ฟังก์ชันดึงข้อมูล NAV จาก Yahoo Finance สำหรับ ETF
# ----------------------------
def fetch_nav_yahoo(fund_name, months=HISTORICAL_MONTHS):
    st.info(f"🌐 ลองดึงข้อมูล {fund_name} จาก Yahoo Finance...")
    return pd.DataFrame(columns=["date", "nav"])  # placeholder

# ----------------------------
# ฟังก์ชันดึงข้อมูล NAV จากหลายแหล่ง
# ----------------------------
def fetch_nav_multi_source(fund_name, months=HISTORICAL_MONTHS):
    sources = [fetch_nav_morningstar, fetch_nav_setfund, fetch_nav_yahoo]
    for func in sources:
        df = func(fund_name, months)
        if not df.empty:
            st.success(f"✅ ดึงข้อมูล {fund_name} สำเร็จจาก {func.__name__}")
            return df
    st.error(f"❌ ไม่สามารถดึงข้อมูล {fund_name} จากทุกแหล่งได้")
    return pd.DataFrame(columns=["date", "nav"])

# ----------------------------
# ฟังก์ชันโหลดและอัปเดตข้อมูล CSV
# ----------------------------
def get_fund_data(fund_name, months=HISTORICAL_MONTHS):
    file_path = os.path.join(DATA_DIR, f"{fund_name}.csv")
    df_old = pd.DataFrame(columns=["date", "nav"])
    if os.path.exists(file_path):
        try:
            df_old = pd.read_csv(file_path)
            if "date" in df_old.columns:
                df_old["date"] = pd.to_datetime(df_old["date"])
        except:
            st.warning(f"❌ อ่าน CSV เก่าของ {fund_name} ล้มเหลว")
    
    # ดึงข้อมูลย้อนหลัง
    df_new = fetch_nav_multi_source(fund_name, months)
    
    # รวมข้อมูลใหม่กับข้อมูลเก่า
    df = pd.concat([df_old, df_new], ignore_index=True)
    df.drop_duplicates(subset="date", inplace=True)
    df = df.sort_values("date")
    
    # คำนวณ MA5 / MA20 และ Signal
    if not df.empty:
        df["MA5"] = df["nav"].rolling(5).mean()
        df["MA20"] = df["nav"].rolling(20).mean()
        df["Signal"] = ""
        for i in range(1, len(df)):
            if df["MA5"].iloc[i] > df["MA20"].iloc[i] and df["MA5"].iloc[i-1] <= df["MA20"].iloc[i-1]:
                df.loc[df.index[i], "Signal"] = "BUY"
            elif df["MA5"].iloc[i] < df["MA20"].iloc[i] and df["MA5"].iloc[i-1] >= df["MA20"].iloc[i-1]:
                df.loc[df.index[i], "Signal"] = "SELL"
    
    # บันทึกข้อมูลลง CSV
    df.to_csv(file_path, index=False)
    return df

# ----------------------------
# Streamlit App
# ----------------------------
st.title("📈 Fund Dashboard (Multi-Source + Historical)")

selected_fund = st.selectbox("เลือกกองทุน", FUND_LIST)
df = get_fund_data(selected_fund, HISTORICAL_MONTHS)

# สัญญาณล่าสุด
if df.empty or "Signal" not in df.columns:
    latest_signal = "HOLD"
else:
    latest_signal = df["Signal"].replace("", "HOLD").iloc[-1]

st.subheader(f"Latest Signal: {latest_signal}")

# แสดง DataFrame
st.subheader("NAV Data")
if df.empty:
    st.warning("ไม่มีข้อมูลให้แสดง")
else:
    st.dataframe(df.fillna(""))

# แสดงกราฟ
if not df.empty and "nav" in df.columns:
    st.subheader("กราฟ NAV + MA")
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.plot(df["date"], df["nav"], label="NAV", marker='o')
    if "MA5" in df.columns:
        ax.plot(df["date"], df["MA5"], label="MA5")
    if "MA20" in df.columns:
        ax.plot(df["date"], df["MA20"], label="MA20")
    
    # แสดงจุด BUY/SELL
    if "Signal" in df.columns:
        buy_points = df[df["Signal"] == "BUY"]
        sell_points = df[df["Signal"] == "SELL"]
        if not buy_points.empty:
            ax.scatter(buy_points["date"], buy_points["nav"], marker="^", color="green", s=100, label="BUY")
        if not sell_points.empty:
            ax.scatter(sell_points["date"], sell_points["nav"], marker="v", color="red", s=100, label="SELL")
    
    ax.set_xlabel("Date")
    ax.set_ylabel("NAV")
    ax.legend()
    ax.grid(True)
    st.pyplot(fig)