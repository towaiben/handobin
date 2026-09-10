import os
from datetime import date, timedelta

import pandas as pd
import plotly.express as px
import requests
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

API_URL = "https://oapi.koreaexim.go.kr/site/program/financial/exchangeJSON"
API_KEY = os.getenv("KOREAEXIM_KEY", "")

RESULT_MESSAGES = {
    1: "성공",
    2: "데이터 코드 오류",
    3: "인증 실패",
    4: "해당 일자 데이터 없음",
}

COLUMN_LABELS = {
    "cur_unit": "통화코드",
    "cur_nm": "통화명",
    "deal_bas_r": "매매기준율",
    "ttb": "전신환(매입)",
    "tts": "전신환(매도)",
    "bkpr": "장부가격",
    "kftc_bkpr": "서울외국환중개 장부가격",
    "kftc_deal_bas_r": "서울외국환중개 매매기준율",
    "yy_efee_r": "년환가료율",
    "ten_dd_efee_r": "10일환가료율",
    "unit_qty": "단위",
}

FEATURED = ["USD", "EUR", "JPY", "CNH", "GBP", "AUD"]

st.set_page_config(
    page_title="한국수출입은행 환율 대시보드",
    page_icon="💱",
    layout="wide",
    initial_sidebar_state="expanded",
)


def parse_number(value) -> float:
    if value is None or value == "":
        return 0.0
    return float(str(value).replace(",", ""))


def parse_unit(cur_unit: str) -> tuple[str, int]:
    if "(" in cur_unit and cur_unit.endswith(")"):
        code, qty = cur_unit.split("(", 1)
        return code, int(qty.rstrip(")"))
    return cur_unit, 1


@st.cache_data(ttl=300)
def fetch_rates(search_date: str) -> tuple[list, int | None]:
    params = {"authkey": API_KEY, "data": "AP01", "searchdate": search_date}
    response = requests.get(API_URL, params=params, timeout=20)
    response.raise_for_status()
    payload = response.json()
    if isinstance(payload, dict):
        return [], payload.get("result")
    if not payload:
        return [], None
    return payload, payload[0].get("result")


def to_dataframe(rows: list) -> pd.DataFrame:
    records = []
    for row in rows:
        code, qty = parse_unit(row.get("cur_unit", ""))
        records.append(
            {
                "통화코드": code,
                "통화명": row.get("cur_nm", ""),
                "단위": qty,
                "매매기준율": parse_number(row.get("deal_bas_r")),
                "전신환(매입)": parse_number(row.get("ttb")),
                "전신환(매도)": parse_number(row.get("tts")),
                "장부가격": parse_number(row.get("bkpr")),
                "서울외국환중개 장부가격": parse_number(row.get("kftc_bkpr")),
                "서울외국환중개 매매기준율": parse_number(row.get("kftc_deal_bas_r")),
                "년환가료율": parse_number(row.get("yy_efee_r")),
                "10일환가료율": parse_number(row.get("ten_dd_efee_r")),
                "원본코드": row.get("cur_unit", ""),
            }
        )
    df = pd.DataFrame(records)
    if df.empty:
        return df
    df["원 환산(1단위)"] = df["매매기준율"] / df["단위"]
    return df.sort_values("매매기준율", ascending=False).reset_index(drop=True)


def find_recent_business_day(start: date, max_lookback: int = 10) -> tuple[pd.DataFrame, date, int | None]:
    last_result = None
    for offset in range(max_lookback):
        day = start - timedelta(days=offset)
        rows, result = fetch_rates(day.strftime("%Y%m%d"))
        last_result = result
        df = to_dataframe(rows)
        if not df.empty and result == 1:
            return df, day, result
    return pd.DataFrame(), start, last_result


def format_krw(value: float) -> str:
    return f"{value:,.2f} 원"


st.title("💱 한국수출입은행 환율 대시보드")
st.caption("한국수출입은행 현재환율 API (`data=AP01`) 기준으로 고시 환율을 보여줍니다.")

if not API_KEY:
    st.error(".env 파일에 `KOREAEXIM_KEY`가 없습니다.")
    st.stop()

with st.sidebar:
    st.header("조회 조건")
    selected_date = st.date_input("조회일", value=date.today(), max_value=date.today())
    auto_fallback = st.toggle("휴일/주말이면 최근 영업일 사용", value=True)
    if st.button("새로고침", width="stretch"):
        st.cache_data.clear()
        st.rerun()
    st.divider()
    st.caption("출처: 한국수출입은행 현재환율 API")

with st.spinner("환율 데이터를 불러오는 중..."):
    try:
        rows, result = fetch_rates(selected_date.strftime("%Y%m%d"))
        df = to_dataframe(rows)
        used_date = selected_date
        if df.empty and auto_fallback:
            df, used_date, result = find_recent_business_day(selected_date)
    except requests.RequestException as exc:
        st.error(f"API 요청에 실패했습니다: {exc}")
        st.stop()

if df.empty:
    message = RESULT_MESSAGES.get(result, "응답 데이터가 비어 있습니다.")
    st.warning(f"{selected_date.strftime('%Y-%m-%d')} 환율을 가져오지 못했습니다. ({message})")
    st.info("주말·공휴일에는 고시가 없을 수 있습니다. 사이드바에서 최근 영업일 옵션을 켜거나 다른 날짜를 선택해 보세요.")
    st.stop()

if used_date != selected_date:
    st.info(f"{selected_date.strftime('%Y-%m-%d')}에는 고시가 없어 **{used_date.strftime('%Y-%m-%d')}** 데이터를 표시합니다.")

st.subheader(f"{used_date.strftime('%Y년 %m월 %d일')} 주요 통화")
featured = df[df["통화코드"].isin(FEATURED)].set_index("통화코드")
metric_cols = st.columns(len(FEATURED))
for col, code in zip(metric_cols, FEATURED):
    if code not in featured.index:
        col.metric(code, "-")
        continue
    row = featured.loc[code]
    unit_note = f" / {int(row['단위'])}{code}" if row["단위"] != 1 else f" / 1{code}"
    col.metric(f"{code} 매매기준율", format_krw(row["매매기준율"]), delta=unit_note)

st.divider()

left, right = st.columns([1.4, 1])
with left:
    st.subheader("통화별 매매기준율")
    chart_df = df[df["통화코드"] != "KRW"].copy()
    chart_df["표시"] = chart_df.apply(
        lambda r: f"{r['통화코드']}" + (f"({int(r['단위'])})" if r["단위"] != 1 else ""),
        axis=1,
    )
    fig = px.bar(
        chart_df,
        x="표시",
        y="매매기준율",
        hover_data={"통화명": True, "전신환(매입)": ":,.2f", "전신환(매도)": ":,.2f"},
        labels={"표시": "통화", "매매기준율": "원"},
    )
    fig.update_layout(margin=dict(l=10, r=10, t=10, b=10), height=420)
    st.plotly_chart(fig, width="stretch")

with right:
    st.subheader("간단 환전")
    currencies = df[df["통화코드"] != "KRW"]["통화코드"].tolist()
    default_idx = currencies.index("USD") if "USD" in currencies else 0
    picked = st.selectbox("통화", currencies, index=default_idx)
    picked_row = df.loc[df["통화코드"] == picked].iloc[0]
    per_unit = float(picked_row["원 환산(1단위)"])
    buy = float(picked_row["전신환(매입)"]) / float(picked_row["단위"])
    sell = float(picked_row["전신환(매도)"]) / float(picked_row["단위"])

    direction = st.radio("방향", ["외화 → 원", "원 → 외화"], horizontal=True)
    amount = st.number_input("금액", min_value=0.0, value=100.0, step=10.0)
    if direction == "외화 → 원":
        st.metric("매매기준율 환산", format_krw(amount * per_unit))
        st.caption(f"은행 살 때(매도) 기준이면 약 {format_krw(amount * sell)}")
    else:
        converted = amount / per_unit if per_unit else 0
        st.metric("매매기준율 환산", f"{converted:,.2f} {picked}")
        st.caption(f"은행 팔 때(매입) 기준이면 약 {amount / buy if buy else 0:,.2f} {picked}")

    st.caption(
        f"{picked} 1단위 = {format_krw(per_unit)}  "
        f"(API 고시 단위: {int(picked_row['단위'])}{picked} = {format_krw(picked_row['매매기준율'])})"
    )

st.subheader("전체 고시 환율")
keyword = st.text_input("통화 검색", placeholder="USD, 유로, 엔 등")
view = df.copy()
if keyword.strip():
    q = keyword.strip().lower()
    view = view[
        view["통화코드"].str.lower().str.contains(q)
        | view["통화명"].str.lower().str.contains(q)
    ]

display_cols = [
    "통화코드",
    "통화명",
    "단위",
    "매매기준율",
    "전신환(매입)",
    "전신환(매도)",
    "장부가격",
    "서울외국환중개 매매기준율",
]
st.dataframe(
    view[display_cols],
    width="stretch",
    hide_index=True,
    column_config={
        "매매기준율": st.column_config.NumberColumn(format="%.2f"),
        "전신환(매입)": st.column_config.NumberColumn(format="%.2f"),
        "전신환(매도)": st.column_config.NumberColumn(format="%.2f"),
        "장부가격": st.column_config.NumberColumn(format="%.0f"),
        "서울외국환중개 매매기준율": st.column_config.NumberColumn(format="%.2f"),
    },
)

csv = view[display_cols].to_csv(index=False).encode("utf-8-sig")
st.download_button(
    "CSV 다운로드",
    csv,
    file_name=f"koreaexim_fx_{used_date.strftime('%Y%m%d')}.csv",
    mime="text/csv",
)

with st.expander("원본 API 필드 설명"):
    st.markdown(
        """
        - `cur_unit` / `cur_nm`: 통화 코드와 한글명. `JPY(100)`처럼 괄호가 있으면 100단위 고시입니다.
        - `deal_bas_r`: 매매기준율
        - `ttb` / `tts`: 전신환 매입율 / 매도율
        - `bkpr`, `kftc_bkpr`, `kftc_deal_bas_r`: 장부가격 및 서울외국환중개 기준
        - `result`: 1 성공, 2 데이터 코드 오류, 3 인증 실패, 4 해당일 데이터 없음
        """
    )
