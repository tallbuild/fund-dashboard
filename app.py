import pandas as pd
import os
import requests
from bs4 import BeautifulSoup
from datetime import datetime

DATA_DIR = "data"

def fetch_nav_online(fund_name):
    """
    ตัวอย่าง mockup: ดึงข้อมูล NAV จากเว็บกองทุน
    ให้ปรับ URL และ logic ตามเว็บไซต์จริงของกองทุนแต่ละกองทุน
    """
    if fund_name == "ONE-UGG-RA":
        url = "https://www.oneasset.com/fund-nav/one-ugg-ra"  # ตัวอย่าง
    elif fund_name == "K-GHEALTH":
        url = "https://www.kasikornasset.com/fund-nav/k-health"  # ตัวอย่าง
    else:
        return None
    
    # ส่งคำขอ
    r = requests.get(url)
    soup = BeautifulSoup(r.text, "html.parser")
    
    # สมมุติ: parse ตาราง NAV ออกมาเป็น DataFrame
    table = soup.find("table")  # ปรับตามโครงสร้างเว็บจริง
    if table:
        df = pd.read_html(str(table))[0]
        df.columns = ["date", "nav"]
        df["date"] = pd.to_datetime(df["date"])
        return df
    return None

def get_fund_data(fund_name):
    file_path = os.path.join(DATA_DIR, f"{fund_name}.csv")
    
    # ถ้าไฟล์ CSV ไม่มีหรือเก่ากว่า 1 วัน → ดึงออนไลน์
    fetch_online = True
    if os.path.exists(file_path):
        mtime = os.path.getmtime(file_path)
        file_date = datetime.fromtimestamp(mtime).date()
        if file_date == datetime.today().date():
            fetch_online = False
    
    if fetch_online:
        df_online = fetch_nav_online(fund_name)
        if df_online is not None:
            df_online.to_csv(file_path, index=False)
    
    # โหลด CSV
    df = pd.read_csv(file_path, parse_dates=["date"])
    df = df.sort_values("date")
    
    # คำนวณ MA และสัญญาณ
    df["MA5"] = df["nav"].rolling(5).mean()
    df["MA20"] = df["nav"].rolling(20).mean()
    df["Signal"] = ""
    for i in range(1, len(df)):
        if df["MA5"].iloc[i] > df["MA20"].iloc[i] and df["MA5"].iloc[i-1] <= df["MA20"].iloc[i-1]:
            df.loc[df.index[i], "Signal"] = "BUY"
        elif df["MA5"].iloc[i] < df["MA20"].iloc[i] and df["MA5"].iloc[i-1] >= df["MA20"].iloc[i-1]:
            df.loc[df.index[i], "Signal"] = "SELL"
    
    return df