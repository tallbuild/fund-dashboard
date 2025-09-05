import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import os

st.title("📊 Fund Dashboard")

# 📂 หาไฟล์ทั้งหมดในโฟลเดอร์ data/
DATA_DIR = "data"
fund_files = [f for f in os.listdir(DATA_DIR) if f.endswith(".csv")]

# แปลงชื่อไฟล์ -> ชื่อกองทุน (ตัด .csv ออก)
funds = [os.path.splitext(f)[0] for f in fund_files]

if not funds:
    st.error("❌ ไม่พบไฟล์กองทุนในโฟลเดอร์ data/")
    st.stop()

# dropdown ให้เลือกกองทุน
selected = st.selectbox("เลือกกองทุน", funds)

def get_fund_data(fund_name: str):
    file_path = os.path.join(DATA_DIR, f"{fund_name}.csv")
    df = pd.read_csv(file_path, parse_dates=["date"])
    return df

# โหลดข้อมูลกองทุนที่เลือก
df = get_fund_data(selected)

# แสดงข้อมูลล่าสุด
st.subheader(f"📈 ข้อมูลล่าสุดของ {selected}")
st.dataframe(df.tail(10))

# วาดกราฟ NAV
fig, ax = plt.subplots()
ax.plot(df["date"], df["nav"], marker="o")
ax.set_title(f"NAV: {selected}")
ax.set_xlabel("Date")
ax.set_ylabel("NAV")
plt.xticks(rotation=45)
st.pyplot(fig)