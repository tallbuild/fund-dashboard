import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import os

st.title("📊 Fund Dashboard - สัญญาณล่าสุดทุกกองทุน")

DATA_DIR = "data"
fund_files = [f for f in os.listdir(DATA_DIR) if f.endswith(".csv")]
funds = [os.path.splitext(f)[0] for f in fund_files]

if not funds:
    st.error("❌ ไม่พบไฟล์กองทุนในโฟลเดอร์ data/")
    st.stop()

def get_fund_data(fund_name: str):
    file_path = os.path.join(DATA_DIR, f"{fund_name}.csv")
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

# 🔔 สรุปสัญญาณล่าสุดทุกกองทุน พร้อม Highlight
st.subheader("🔔 สัญญาณล่าสุดของทุกกองทุน")
for f in funds:
    df = get_fund_data(f)
    latest_signal = df["Signal"].replace("", "HOLD").iloc[-1]
    
    if latest_signal == "BUY":
        st.markdown(f"**{f}: {latest_signal}**", unsafe_allow_html=True)
        st.markdown(f"<div style='background-color: #a8e6a1; padding:5px;'>{latest_signal}</div>", unsafe_allow_html=True)
    elif latest_signal == "SELL":
        st.markdown(f"**{f}: {latest_signal}**", unsafe_allow_html=True)
        st.markdown(f"<div style='background-color: #f28b82; padding:5px;'>{latest_signal}</div>", unsafe_allow_html=True)
    else:
        st.markdown(f"**{f}: {latest_signal}**", unsafe_allow_html=True)
        st.markdown(f"<div style='background-color: #fff59d; padding:5px;'>{latest_signal}</div>", unsafe_allow_html=True)

# แสดงกราฟของแต่ละกองทุน
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