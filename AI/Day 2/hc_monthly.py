import os
from datetime import date, timedelta
from pathlib import Path

import pandas as pd
import requests
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

API_URL = "https://oapi.koreaexim.go.kr/site/program/financial/exchangeJSON"
API_KEY = os.getenv("KOREAEXIM_KEY", "")

st.set_page_config(page_title="사업부 월별실적", layout="wide")
st.title("사업부 월별실적")
st.caption("원화매출액 = 내수매출 + 수출매출 × (당월 말 영업일 USD 매매기준율 ÷ 1,000)")


def parse_number(value):
    if value is None or value == "":
        return None
    return float(str(value).replace(",", ""))


def month_end(year: int, month: int) -> date:
    if month == 12:
        return date(year, 12, 31)
    return date(year, month + 1, 1) - timedelta(days=1)


@st.cache_data(ttl=3600)
def fetch_usd_rate(search_date: str):
    if not API_KEY:
        return None
    response = requests.get(
        API_URL,
        params={"authkey": API_KEY, "data": "AP01", "searchdate": search_date},
        timeout=20,
    )
    response.raise_for_status()
    payload = response.json()
    if not isinstance(payload, list) or not payload:
        return None
    if payload[0].get("result") != 1:
        return None
    for row in payload:
        if str(row.get("cur_unit", "")).startswith("USD"):
            return parse_number(row.get("deal_bas_r"))
    return None


@st.cache_data(ttl=3600)
def usd_rate_for_month(month_key: str):
    year, month = map(int, str(month_key).split("-"))
    day = month_end(year, month)
    for _ in range(14):
        rate = fetch_usd_rate(day.strftime("%Y%m%d"))
        if rate is not None:
            return {"환율": rate, "환율일자": day.strftime("%Y-%m-%d")}
        day -= timedelta(days=1)
    return {"환율": None, "환율일자": None}


csv_path = Path(__file__).parent / "data" / "hc_01_사업부_월별실적.csv"
df = pd.read_csv(csv_path)

if not API_KEY:
    st.error(".env의 KOREAEXIM_KEY가 없습니다.")
    st.stop()

with st.spinner("한국수출입은행 환율을 조회하는 중..."):
    month_fx = {month: usd_rate_for_month(month) for month in df["월"].unique()}

df["적용환율"] = df["월"].map(lambda month: month_fx[month]["환율"])
df["환율일자"] = df["월"].map(lambda month: month_fx[month]["환율일자"])
df["원화매출액"] = (
    df["매출액"] * (1 - df["수출비중"] / 100)
    + df["매출액"] * (df["수출비중"] / 100) * (df["적용환율"] / 1000)
).round()

front = ["사업부", "월", "매출액", "수출비중", "적용환율", "환율일자", "원화매출액"]
rest = [col for col in df.columns if col not in front]
df = df[front + rest]

st.dataframe(df, use_container_width=True, hide_index=True)
