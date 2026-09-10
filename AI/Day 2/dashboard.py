from pathlib import Path

import pandas as pd
import streamlit as st

DATA_PATH = Path(__file__).parent / "data" / "hc_01_사업부_월별실적.csv"
AMOUNT_COLS = [
    "매출액",
    "매출원가",
    "매출총이익",
    "판관비",
    "영업이익",
    "EBITDA",
    "영업현금흐름",
]
RATIO_COLS = ["수출비중"]
DAY_COLS = ["AR회전일수", "AP회전일수"]

st.set_page_config(
    page_title="사업부 월별 실적 대시보드",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)


@st.cache_data
def load_data() -> pd.DataFrame:
    df = pd.read_csv(DATA_PATH)
    df["월"] = pd.to_datetime(df["월"] + "-01")
    df["매출총이익률"] = df["매출총이익"] / df["매출액"] * 100
    df["영업이익률"] = df["영업이익"] / df["매출액"] * 100
    df["EBITDA마진"] = df["EBITDA"] / df["매출액"] * 100
    df["판관비율"] = df["판관비"] / df["매출액"] * 100
    df["현금전환일수"] = df["AR회전일수"] - df["AP회전일수"]
    return df.sort_values(["월", "사업부"]).reset_index(drop=True)


def fmt_amount(value: float) -> str:
    return f"{value:,.0f}"


def fmt_pct(value: float) -> str:
    return f"{value:.1f}%"


def fmt_day(value: float) -> str:
    return f"{value:.0f}일"


def weighted_avg(frame: pd.DataFrame, col: str) -> float:
    weights = frame["매출액"]
    if weights.sum() == 0:
        return 0.0
    return float((frame[col] * weights).sum() / weights.sum())


def summarize(frame: pd.DataFrame) -> dict[str, float]:
    if frame.empty:
        return {col: 0.0 for col in [*AMOUNT_COLS, *RATIO_COLS, *DAY_COLS, "영업이익률", "매출총이익률", "현금전환일수"]}
    summary = {col: float(frame[col].sum()) for col in AMOUNT_COLS}
    summary["수출비중"] = weighted_avg(frame, "수출비중")
    summary["매출총이익률"] = summary["매출총이익"] / summary["매출액"] * 100 if summary["매출액"] else 0.0
    summary["영업이익률"] = summary["영업이익"] / summary["매출액"] * 100 if summary["매출액"] else 0.0
    summary["AR회전일수"] = weighted_avg(frame, "AR회전일수")
    summary["AP회전일수"] = weighted_avg(frame, "AP회전일수")
    summary["현금전환일수"] = summary["AR회전일수"] - summary["AP회전일수"]
    return summary


def delta_pct_label(current: float, previous: float) -> str | None:
    if previous == 0:
        return None
    return f"{(current - previous) / abs(previous) * 100:+.1f}%"


def delta_pp_label(current: float, previous: float) -> str | None:
    return f"{current - previous:+.1f}%p"


def month_label(ts: pd.Timestamp) -> str:
    return ts.strftime("%Y-%m")


df = load_data()
units = sorted(df["사업부"].unique())
months = sorted(df["월"].unique())

with st.sidebar:
    st.header("필터")
    selected_units = st.multiselect("사업부", units, default=units)
    start_month, end_month = st.select_slider(
        "기간",
        options=months,
        value=(months[0], months[-1]),
        format_func=month_label,
    )
    compare_mode = st.radio("KPI 비교 기준", ["전월", "전년 동월"], horizontal=True)
    st.caption("금액 단위: 백만원")

if not selected_units:
    st.warning("사업부를 하나 이상 선택하세요.")
    st.stop()

filtered = df[
    df["사업부"].isin(selected_units)
    & (df["월"] >= start_month)
    & (df["월"] <= end_month)
].copy()

latest_month = filtered["월"].max()
prev_month = latest_month - pd.DateOffset(months=1)
yoy_month = latest_month - pd.DateOffset(years=1)
compare_month = prev_month if compare_mode == "전월" else yoy_month

latest = filtered[filtered["월"] == latest_month]
compare = df[df["사업부"].isin(selected_units) & (df["월"] == compare_month)]
kpi = summarize(latest)
kpi_prev = summarize(compare)

st.title("사업부 월별 실적 대시보드")
st.caption(
    f"{month_label(start_month)} ~ {month_label(end_month)}  ·  "
    f"기준월 {month_label(latest_month)}  ·  "
    f"{', '.join(selected_units)}"
)

has_compare = not compare.empty
k1, k2, k3, k4, k5, k6 = st.columns(6)
k1.metric("매출액", fmt_amount(kpi["매출액"]), delta=delta_pct_label(kpi["매출액"], kpi_prev["매출액"]) if has_compare else None)
k2.metric("영업이익", fmt_amount(kpi["영업이익"]), delta=delta_pct_label(kpi["영업이익"], kpi_prev["영업이익"]) if has_compare else None)
k3.metric("EBITDA", fmt_amount(kpi["EBITDA"]), delta=delta_pct_label(kpi["EBITDA"], kpi_prev["EBITDA"]) if has_compare else None)
k4.metric(
    "영업현금흐름",
    fmt_amount(kpi["영업현금흐름"]),
    delta=delta_pct_label(kpi["영업현금흐름"], kpi_prev["영업현금흐름"]) if has_compare else None,
)
k5.metric(
    "영업이익률",
    fmt_pct(kpi["영업이익률"]),
    delta=delta_pp_label(kpi["영업이익률"], kpi_prev["영업이익률"]) if has_compare else None,
)
k6.metric(
    "수출비중",
    fmt_pct(kpi["수출비중"]),
    delta=delta_pp_label(kpi["수출비중"], kpi_prev["수출비중"]) if has_compare else None,
)

tab_trend, tab_unit, tab_profit, tab_wc, tab_table = st.tabs(
    ["실적 추이", "사업부 비교", "수익성", "운전자본", "상세 데이터"]
)

monthly = (
    filtered.groupby("월", as_index=False)[AMOUNT_COLS]
    .sum()
    .assign(
        매출총이익률=lambda x: x["매출총이익"] / x["매출액"] * 100,
        영업이익률=lambda x: x["영업이익"] / x["매출액"] * 100,
        EBITDA마진=lambda x: x["EBITDA"] / x["매출액"] * 100,
    )
)
monthly["월라벨"] = monthly["월"].dt.strftime("%Y-%m")

with tab_trend:
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("매출 · 원가 · 이익")
        st.line_chart(
            monthly.set_index("월라벨")[["매출액", "매출원가", "매출총이익", "영업이익"]],
            width="stretch",
        )
    with c2:
        st.subheader("현금창출력")
        st.line_chart(
            monthly.set_index("월라벨")[["EBITDA", "영업현금흐름"]],
            width="stretch",
        )

    st.subheader("사업부별 매출 추이")
    sales_pivot = (
        filtered.pivot_table(index="월", columns="사업부", values="매출액", aggfunc="sum")
        .sort_index()
    )
    sales_pivot.index = sales_pivot.index.strftime("%Y-%m")
    st.area_chart(sales_pivot, width="stretch")

with tab_unit:
    unit_latest = (
        latest.groupby("사업부", as_index=False)
        .agg(
            매출액=("매출액", "sum"),
            영업이익=("영업이익", "sum"),
            EBITDA=("EBITDA", "sum"),
            영업현금흐름=("영업현금흐름", "sum"),
            수출비중=("수출비중", "mean"),
        )
        .assign(영업이익률=lambda x: x["영업이익"] / x["매출액"] * 100)
        .sort_values("매출액", ascending=False)
    )

    left, right = st.columns(2)
    with left:
        st.subheader(f"{month_label(latest_month)} 사업부 매출")
        st.bar_chart(unit_latest.set_index("사업부")[["매출액"]], width="stretch")
    with right:
        st.subheader(f"{month_label(latest_month)} 영업이익")
        st.bar_chart(unit_latest.set_index("사업부")[["영업이익"]], width="stretch")

    st.subheader("기간 합계 비교")
    unit_period = (
        filtered.groupby("사업부", as_index=False)[AMOUNT_COLS]
        .sum()
        .assign(
            영업이익률=lambda x: x["영업이익"] / x["매출액"] * 100,
            매출총이익률=lambda x: x["매출총이익"] / x["매출액"] * 100,
        )
        .sort_values("매출액", ascending=False)
    )
    st.dataframe(
        unit_period,
        width="stretch",
        hide_index=True,
        column_config={
            col: st.column_config.NumberColumn(col, format="%,.0f")
            for col in AMOUNT_COLS
        }
        | {
            "영업이익률": st.column_config.NumberColumn("영업이익률", format="%.1f%%"),
            "매출총이익률": st.column_config.NumberColumn("매출총이익률", format="%.1f%%"),
        },
    )

with tab_profit:
    p1, p2, p3 = st.columns(3)
    p1.metric("매출총이익률", fmt_pct(kpi["매출총이익률"]))
    p2.metric("영업이익률", fmt_pct(kpi["영업이익률"]))
    p3.metric("판관비율", fmt_pct(weighted_avg(latest, "판관비율") if not latest.empty else 0))

    st.subheader("마진 추이")
    st.line_chart(
        monthly.set_index("월라벨")[["매출총이익률", "영업이익률", "EBITDA마진"]],
        width="stretch",
    )

    st.subheader("사업부 × 월 영업이익률")
    margin_pivot = filtered.pivot_table(
        index="사업부",
        columns=filtered["월"].dt.strftime("%Y-%m"),
        values="영업이익률",
        aggfunc="mean",
    )
    st.dataframe(
        margin_pivot.style.background_gradient(cmap="RdYlGn", axis=None).format("{:.1f}"),
        width="stretch",
    )

with tab_wc:
    wc_rows = []
    for month, group in filtered.groupby("월"):
        ar = weighted_avg(group, "AR회전일수")
        ap = weighted_avg(group, "AP회전일수")
        wc_rows.append(
            {
                "월": month,
                "AR회전일수": ar,
                "AP회전일수": ap,
                "현금전환일수": ar - ap,
                "수출비중": weighted_avg(group, "수출비중"),
            }
        )
    wc_monthly = pd.DataFrame(wc_rows)
    wc_monthly["월라벨"] = wc_monthly["월"].dt.strftime("%Y-%m")

    w1, w2, w3, w4 = st.columns(4)
    w1.metric("AR 회전일수", fmt_day(kpi["AR회전일수"]))
    w2.metric("AP 회전일수", fmt_day(kpi["AP회전일수"]))
    w3.metric("현금전환일수", fmt_day(kpi["현금전환일수"]))
    w4.metric("수출비중", fmt_pct(kpi["수출비중"]))

    st.caption("현금전환일수 = AR회전일수 − AP회전일수 (재고일수 없음)")
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("회수 · 지급 일수")
        st.line_chart(
            wc_monthly.set_index("월라벨")[["AR회전일수", "AP회전일수", "현금전환일수"]],
            width="stretch",
        )
    with c2:
        st.subheader("수출비중")
        st.line_chart(wc_monthly.set_index("월라벨")[["수출비중"]], width="stretch")

    st.subheader(f"{month_label(latest_month)} 사업부 운전자본")
    wc_unit = latest[["사업부", "AR회전일수", "AP회전일수", "현금전환일수", "수출비중"]].sort_values("AR회전일수", ascending=False)
    st.bar_chart(wc_unit.set_index("사업부")[["AR회전일수", "AP회전일수"]], width="stretch")

with tab_table:
    show = filtered.copy()
    show["월"] = show["월"].dt.strftime("%Y-%m")
    st.dataframe(
        show[
            [
                "사업부",
                "월",
                *AMOUNT_COLS,
                "수출비중",
                "매출총이익률",
                "영업이익률",
                "EBITDA마진",
                *DAY_COLS,
                "현금전환일수",
            ]
        ],
        width="stretch",
        hide_index=True,
        column_config={
            **{col: st.column_config.NumberColumn(col, format="%,.0f") for col in AMOUNT_COLS},
            "수출비중": st.column_config.NumberColumn("수출비중", format="%.1f%%"),
            "매출총이익률": st.column_config.NumberColumn("매출총이익률", format="%.1f%%"),
            "영업이익률": st.column_config.NumberColumn("영업이익률", format="%.1f%%"),
            "EBITDA마진": st.column_config.NumberColumn("EBITDA마진", format="%.1f%%"),
            "AR회전일수": st.column_config.NumberColumn("AR회전일수", format="%.0f일"),
            "AP회전일수": st.column_config.NumberColumn("AP회전일수", format="%.0f일"),
            "현금전환일수": st.column_config.NumberColumn("현금전환일수", format="%.0f일"),
        },
    )
    csv = show.to_csv(index=False).encode("utf-8-sig")
    st.download_button("필터 결과 CSV 다운로드", csv, file_name="사업부_월별실적_필터.csv", mime="text/csv")
