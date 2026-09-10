import os
from datetime import date
from pathlib import Path

import pandas as pd
import plotly.express as px
import requests
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

API_URL = "https://api.stlouisfed.org/fred/series/observations"
API_KEY = os.getenv("FRED_KEY", "")

INDICATORS = [
    ("DEXKOUS", "원/달러 환율"),
    ("DCOILWTICO", "WTI 유가"),
    ("WPU1017", "미 철강 생산자물가"),
    ("FEDFUNDS", "미 연방기금금리"),
    ("DTWEXBGS", "달러 인덱스"),
    ("CPIAUCSL", "미 소비자물가"),
]
PLUS_COLOR = "#d32f2f"
MINUS_COLOR = "#1565c0"
PERF_PATH = Path(__file__).parent / "data" / "hc_01_사업부_월별실적.csv"
PERF_METRICS = [
    ("매출액", "우리 매출액"),
    ("영업이익", "우리 영업이익"),
]
PERF_AMOUNT_COLS = [
    "매출액",
    "원화매출액",
    "매출원가",
    "매출총이익",
    "판관비",
    "영업이익",
    "EBITDA",
    "영업현금흐름",
]
CORR_METRICS = ["매출액", "영업이익", "매출총이익", "EBITDA", "영업현금흐름"]
MIN_CORR_MONTHS = 6


def months_ago(today: date, months: int) -> date:
    return (pd.Timestamp(today) - pd.DateOffset(months=months)).date()


@st.cache_data(ttl=3600)
def fetch_observations(series_id: str, start: str, end: str) -> tuple[int, dict]:
    response = requests.get(
        API_URL,
        params={
            "series_id": series_id,
            "api_key": API_KEY,
            "file_type": "json",
            "observation_start": start,
            "observation_end": end,
        },
        timeout=20,
    )
    try:
        payload = response.json()
    except ValueError:
        payload = {"error_message": response.text}
    return response.status_code, payload


def observations_to_frame(rows: list) -> tuple[pd.DataFrame, int]:
    missing = 0
    records = []
    for row in rows:
        raw = str(row.get("value", "")).strip()
        if raw == ".":
            missing += 1
            continue
        try:
            records.append({"date": row.get("date"), "value": float(raw)})
        except ValueError:
            missing += 1
    df = pd.DataFrame(records)
    if df.empty:
        return df, missing
    df["date"] = pd.to_datetime(df["date"])
    return df.sort_values("date").reset_index(drop=True), missing


def format_value(value: float) -> str:
    return f"{value:,.2f}"


@st.cache_data
def load_performance() -> pd.DataFrame:
    df = pd.read_csv(PERF_PATH)
    df["월"] = pd.to_datetime(df["월"] + "-01")
    return df.sort_values(["월", "사업부"]).reset_index(drop=True)


def performance_indicators(df: pd.DataFrame, start: date, end: date) -> list[dict]:
    if df.empty:
        return []
    start_ts = pd.Timestamp(start).replace(day=1)
    end_ts = pd.Timestamp(end)
    totals = df.groupby("월", as_index=False)[[col for col, _ in PERF_METRICS]].sum()
    totals = totals[(totals["월"] >= start_ts) & (totals["월"] <= end_ts)]
    items = []
    for column, name in PERF_METRICS:
        frame = totals[["월", column]].rename(columns={"월": "date", column: "value"})
        if frame.empty:
            continue
        items.append({"series_id": "HC", "name": name, "df": frame, "missing_count": 0})
    return items


def filter_performance(df: pd.DataFrame, units: list[str], start: date, end: date) -> pd.DataFrame:
    view = df[df["사업부"].isin(units)].copy() if units else df.iloc[0:0].copy()
    start_ts = pd.Timestamp(start).replace(day=1)
    end_ts = pd.Timestamp(end)
    return view[(view["월"] >= start_ts) & (view["월"] <= end_ts)]


def render_performance_table(df: pd.DataFrame) -> None:
    st.header("사업부 월별실적")
    st.caption("출처: `data/hc_01_사업부_월별실적.csv` · 금액 단위 백만원")
    if df.empty:
        st.caption("선택한 조건에 해당하는 실적이 없습니다.")
        return

    display = df.copy()
    display["월"] = display["월"].dt.strftime("%Y-%m")
    st.dataframe(
        display,
        width="stretch",
        hide_index=True,
        column_config={
            col: st.column_config.NumberColumn(col, format="%,.0f")
            for col in PERF_AMOUNT_COLS
        }
        | {
            "수출비중": st.column_config.NumberColumn("수출비중", format="%.1f%%"),
            "AR회전일수": st.column_config.NumberColumn("AR회전일수", format="%.0f"),
            "AP회전일수": st.column_config.NumberColumn("AP회전일수", format="%.0f"),
        },
    )
    latest = df["월"].max().strftime("%Y-%m")
    st.caption(f"표시 {len(display):,}행 · 실적 최신월 {latest}")


def monthly_average(df: pd.DataFrame, today: date) -> pd.Series:
    monthly = df.set_index("date")["value"].sort_index().resample("MS").mean().dropna()
    cutoff = pd.Timestamp(today).replace(day=1)
    return monthly[monthly.index < cutoff]


def value_for_month(monthly: pd.Series, month: pd.Timestamp) -> float | None:
    target = pd.Timestamp(month).to_period("M")
    matched = monthly[monthly.index.to_period("M") == target]
    if matched.empty or pd.isna(matched.iloc[0]):
        return None
    return float(matched.iloc[0])


def comparison_months(today: date) -> tuple[pd.Timestamp, pd.Timestamp]:
    current = pd.Timestamp(today).replace(day=1)
    last_complete = current - pd.DateOffset(months=1)
    previous = current - pd.DateOffset(months=2)
    return pd.Timestamp(last_complete), pd.Timestamp(previous)


def format_change(change: float | None) -> str:
    if change is None:
        return "발표 전"
    return f"{change:+.1f}%"


def style_change(value: str) -> str:
    if not isinstance(value, str) or value == "발표 전":
        return ""
    if value.startswith("+"):
        return f"color: {PLUS_COLOR}; font-weight: 600"
    if value.startswith("-"):
        return f"color: {MINUS_COLOR}; font-weight: 600"
    return ""


def load_series(series_id: str, name: str, start: str, end: str) -> dict | None:
    try:
        status, payload = fetch_observations(series_id, start, end)
    except requests.RequestException as exc:
        st.error(f"{series_id} API 요청에 실패했습니다: {exc}")
        return None
    if status != 200:
        st.error(payload.get("error_message", "알 수 없는 오류가 발생했습니다."))
        return None
    df, missing_count = observations_to_frame(payload.get("observations", []))
    if df.empty:
        st.warning(f"{series_id} {name}: 표시할 관측값이 없습니다.")
        return None
    return {"series_id": series_id, "name": name, "df": df, "missing_count": missing_count}


def render_series(item: dict) -> None:
    df = item["df"]
    latest = df.iloc[-1]
    previous = df.iloc[-2] if len(df) > 1 else None
    change = float(latest["value"] - previous["value"]) if previous is not None else None

    st.metric(
        "최신값",
        format_value(float(latest["value"])),
        delta=f"{change:+,.2f}" if change is not None else None,
        help=f"최신 관측일 {latest['date'].strftime('%Y-%m-%d')}",
    )
    fig = px.line(
        df,
        x="date",
        y="value",
        title=f"{item['series_id']} {item['name']}",
        labels={"date": "관측일", "value": item["name"]},
    )
    fig.update_layout(margin=dict(l=10, r=10, t=50, b=10), height=380)
    st.plotly_chart(fig, width="stretch")
    st.caption(f"출처: FRED, 결측(휴장일) {item['missing_count']}건 제외")
    st.divider()


def render_comparison(loaded: list[dict], today: date) -> None:
    last_complete, previous = comparison_months(today)
    last_label = last_complete.strftime("%Y-%m")
    prev_label = previous.strftime("%Y-%m")

    indexed = {}
    rows = []
    moves = []

    for item in loaded:
        monthly = monthly_average(item["df"], today)
        if monthly.empty or monthly.iloc[0] == 0:
            continue
        indexed[item["name"]] = monthly / monthly.iloc[0] * 100

        last_value = value_for_month(monthly, last_complete)
        prev_value = value_for_month(monthly, previous)
        change = None
        if last_value is not None and prev_value not in (None, 0):
            change = (last_value - prev_value) / abs(prev_value) * 100
            moves.append((item["name"], change))

        rows.append(
            {
                "지표": item["name"],
                f"{last_label} 평균": format_value(last_value) if last_value is not None else "발표 전",
                f"{prev_label} 평균": format_value(prev_value) if prev_value is not None else "발표 전",
                "전월 대비": format_change(change),
            }
        )

    st.header("지표 비교")
    has_perf = any(item.get("series_id") == "HC" for item in loaded)
    extra = " · 우리 실적(매출액·영업이익)을 같은 지수로 겹쳐 표시" if has_perf else ""
    st.caption(
        f"월 평균 · 완결 월 {last_label} vs 전월 {prev_label} "
        f"(진행 중인 {today.strftime('%Y-%m')} 제외){extra}"
    )

    if indexed:
        wide = pd.concat(indexed, axis=1).sort_index()
        wide.index.name = "월"
        fig = px.line(
            wide.reset_index(),
            x="월",
            y=list(wide.columns),
            title="월 평균 (첫 달 = 100)",
            labels={"value": "지수", "variable": "지표"},
        )
        fig.add_hline(y=100, line_dash="dash", line_color="gray")
        for trace in fig.data:
            if str(trace.name).startswith("우리"):
                trace.line.width = 3
        fig.update_layout(margin=dict(l=10, r=10, t=50, b=10), height=420, legend_title_text="지표")
        st.plotly_chart(fig, width="stretch")
    else:
        st.warning("비교할 월 평균 데이터가 없습니다.")

    if rows:
        table = pd.DataFrame(rows)
        styled = table.style.map(style_change, subset=["전월 대비"])
        st.dataframe(styled, width="stretch", hide_index=True)

    if moves:
        name, change = max(moves, key=lambda item: abs(item[1]))
        color = PLUS_COLOR if change > 0 else MINUS_COLOR if change < 0 else "inherit"
        st.markdown(
            f'이번 달 가장 크게 움직인 지표: {name} '
            f'(<span style="color:{color}">{change:+.1f}%</span>)',
            unsafe_allow_html=True,
        )
    else:
        st.caption("이번 달 가장 크게 움직인 지표: 발표 전")


def load_all_fred(start: str, end: str, already: list[dict]) -> list[dict]:
    have = {item["series_id"] for item in already}
    items = list(already)
    for series_id, name in INDICATORS:
        if series_id in have:
            continue
        extra = load_series(series_id, name, start, end)
        if extra is not None:
            items.append(extra)
    return items


def to_month_index(series: pd.Series) -> pd.Series:
    out = series.astype(float).copy()
    out.index = pd.to_datetime(out.index).to_period("M").to_timestamp()
    return out.sort_index()


def transform_series(series: pd.Series, mode: str) -> pd.Series:
    out = to_month_index(series)
    if mode == "전월 대비 변화율":
        return out.pct_change()
    return out


def corr_strength(value: float) -> str:
    magnitude = abs(value)
    direction = "양(+)" if value > 0 else "음(-)" if value < 0 else "없음"
    if magnitude >= 0.7:
        grade = "강한"
    elif magnitude >= 0.4:
        grade = "보통"
    else:
        grade = "약한"
    return f"{grade} {direction}"


def style_corr(value) -> str:
    if not isinstance(value, (int, float)) or pd.isna(value):
        return ""
    if value > 0:
        return f"color: {PLUS_COLOR}; font-weight: 600"
    if value < 0:
        return f"color: {MINUS_COLOR}; font-weight: 600"
    return ""


def performance_metric_series(df: pd.DataFrame, unit: str, metric: str) -> pd.Series:
    if unit == "전사":
        return df.groupby("월")[metric].sum().sort_index()
    return df.loc[df["사업부"] == unit].set_index("월")[metric].sort_index()


def series_corr(left: pd.Series, right: pd.Series, lag: int) -> tuple[float | None, int]:
    left = to_month_index(left)
    right = to_month_index(right)
    if lag:
        right = right.shift(lag)
    joined = pd.concat({"left": left, "right": right}, axis=1, join="inner").dropna()
    if len(joined) < MIN_CORR_MONTHS:
        return None, len(joined)
    value = joined["left"].corr(joined["right"])
    if pd.isna(value):
        return None, len(joined)
    return float(value), len(joined)


def correlation_tables(
    perf_view: pd.DataFrame,
    fred_items: list[dict],
    metrics: list[str],
    today: date,
    mode: str,
    lag: int,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    fred_monthly = {}
    for item in fred_items:
        monthly = transform_series(monthly_average(item["df"], today), mode)
        if not monthly.empty:
            fred_monthly[item["name"]] = monthly
    if not fred_monthly:
        return pd.DataFrame(), pd.DataFrame()

    units = [*sorted(perf_view["사업부"].unique()), "전사"]
    matrix: dict[str, dict[str, float]] = {}
    rows = []
    for unit in units:
        for metric in metrics:
            raw = performance_metric_series(perf_view, unit, metric)
            series = transform_series(raw, mode)
            label = f"{unit} {metric}" if len(metrics) > 1 else unit
            matrix[label] = {}
            for fred_name, fred_series in fred_monthly.items():
                value, count = series_corr(series, fred_series, lag)
                coeff = value if value is not None else float("nan")
                matrix[label][fred_name] = coeff
                rows.append(
                    {
                        "사업부": unit,
                        "실적": metric,
                        "연준 지표": fred_name,
                        "상관계수": coeff,
                        "관계": corr_strength(coeff) if value is not None else "표본 부족",
                        "표본(월)": count,
                    }
                )
    heat = pd.DataFrame.from_dict(matrix, orient="index")
    rank = pd.DataFrame(rows)
    if not rank.empty:
        rank = rank.sort_values("상관계수", key=lambda col: col.abs(), ascending=False)
    return heat, rank


def render_correlation(perf_view: pd.DataFrame, fred_items: list[dict], today: date) -> None:
    st.header("상관관계 분석")
    if perf_view.empty or not fred_items:
        st.warning("상관관계를 계산할 실적 또는 FRED 지표가 없습니다.")
        return

    left, right = st.columns(2)
    with left:
        metrics = st.multiselect("실적 항목", CORR_METRICS, default=["매출액", "영업이익"])
    with right:
        mode = st.radio("계산 기준", ["전월 대비 변화율", "원계열"], horizontal=True)
    lag = st.slider("지표 시차(개월, 지표가 실적보다 앞선 기간)", 0, 3, 0)

    if not metrics:
        st.warning("실적 항목을 하나 이상 선택하세요.")
        return

    heat, rank = correlation_tables(perf_view, fred_items, metrics, today, mode, lag)
    if heat.empty or rank.empty:
        st.warning("겹치는 월이 부족해 상관계수를 계산하지 못했습니다.")
        return

    valid_n = int(rank["표본(월)"].max()) if not rank.empty else 0
    st.caption(
        f"Pearson 상관계수 · {mode} · 시차 {lag}개월 · "
        f"겹치는 월 최대 {valid_n}개 · 상관은 인과가 아닙니다"
    )

    fig = px.imshow(
        heat,
        color_continuous_scale="RdBu_r",
        zmin=-1,
        zmax=1,
        text_auto=".2f",
        aspect="auto",
        title="사업부 실적 × FRED 지표 상관계수",
        labels={"x": "FRED 지표", "y": "사업부 실적", "color": "r"},
    )
    fig.update_layout(margin=dict(l=10, r=10, t=50, b=10), height=max(360, 48 * len(heat) + 80))
    st.plotly_chart(fig, width="stretch")

    usable = rank.dropna(subset=["상관계수"])
    if usable.empty:
        st.caption("표본이 부족해 해석할 상관계수가 없습니다. 기간을 늘려 보세요.")
        return

    top = usable.iloc[0]
    color = PLUS_COLOR if top["상관계수"] > 0 else MINUS_COLOR
    st.markdown(
        f'가장 강한 상관: {top["사업부"]} {top["실적"]} ↔ {top["연준 지표"]} '
        f'(<span style="color:{color}">{top["상관계수"]:+.2f}</span>, {top["관계"]})',
        unsafe_allow_html=True,
    )

    show = usable.copy()
    show["상관계수"] = show["상관계수"].map(lambda value: round(float(value), 2))
    styled = show[["사업부", "실적", "연준 지표", "상관계수", "관계", "표본(월)"]].style.map(
        style_corr, subset=["상관계수"]
    )
    st.dataframe(styled, width="stretch", hide_index=True)

    st.subheader("산점도")
    options = usable.reset_index(drop=True)
    labels = [
        f"{row['사업부']} {row['실적']} ↔ {row['연준 지표']} ({row['상관계수']:+.2f})"
        for _, row in options.iterrows()
    ]
    picked = st.selectbox("확인할 조합", range(len(options)), format_func=lambda i: labels[i])
    row = options.iloc[picked]
    unit_series = transform_series(performance_metric_series(perf_view, row["사업부"], row["실적"]), mode)
    fred_item = next(item for item in fred_items if item["name"] == row["연준 지표"])
    fred_series = transform_series(monthly_average(fred_item["df"], today), mode)
    if lag:
        fred_series = to_month_index(fred_series).shift(lag)
    scatter = pd.concat(
        {row["실적"]: to_month_index(unit_series), row["연준 지표"]: to_month_index(fred_series)},
        axis=1,
        join="inner",
    ).dropna()
    plot_df = scatter.reset_index().rename(columns={"index": "월"})
    fig = px.scatter(
        plot_df,
        x=row["연준 지표"],
        y=row["실적"],
        hover_data={"월": True},
        title=f"{row['사업부']} {row['실적']} vs {row['연준 지표']}",
    )
    fig.update_layout(margin=dict(l=10, r=10, t=50, b=10), height=380)
    st.plotly_chart(fig, width="stretch")


st.set_page_config(
    page_title="FRED 글로벌 지표 모니터",
    page_icon="🌍",
    layout="wide",
)

st.title("🌍 FRED 글로벌 지표 모니터")

if not API_KEY:
    st.error(".env 파일에 `FRED_KEY`가 없습니다.")
    st.stop()

perf = load_performance()
perf_units = sorted(perf["사업부"].unique())

with st.sidebar:
    st.header("지표 선택")
    selected = []
    for index, (series_id, name) in enumerate(INDICATORS):
        if st.checkbox(f"{series_id} {name}", value=index < 3):
            selected.append((series_id, name))
    months = st.slider("기간(개월)", min_value=6, max_value=36, value=24)
    st.caption("같은 조건의 API 호출은 1시간 동안 캐시됩니다.")
    st.divider()
    st.header("우리 실적")
    selected_units = st.multiselect("사업부", perf_units, default=perf_units)
    st.caption("선택한 사업부 합계를 비교 차트에 같이 그립니다.")

if not selected:
    st.warning("사이드바에서 하나 이상 지표를 선택하세요.")
    st.stop()

today = date.today()
start = months_ago(today, months)
start_text = start.isoformat()
end_text = today.isoformat()

st.caption(f"FRED 관측값 · {start.strftime('%Y-%m-%d')} ~ {today.strftime('%Y-%m-%d')} ({months}개월)")

loaded = []
for series_id, name in selected:
    with st.spinner(f"{series_id} 불러오는 중..."):
        item = load_series(series_id, name, start_text, end_text)
    if item is not None:
        loaded.append(item)

if not loaded:
    st.stop()

for item in loaded:
    render_series(item)

perf_view = filter_performance(perf, selected_units, start, today)
compare_items = list(loaded) + performance_indicators(perf_view, start, today)
render_comparison(compare_items, today)
st.divider()
fred_for_corr = load_all_fred(start_text, end_text, loaded)
render_correlation(perf_view, fred_for_corr, today)
st.divider()
render_performance_table(perf_view)
