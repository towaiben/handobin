from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

DATA_DIR = Path(__file__).resolve().parent / "data"
MONTHLY_PATH = DATA_DIR / "hc_01_사업부_월별실적.csv"
BUDGET_PATH = DATA_DIR / "hc_03_예산_실적.csv"

FONT = "Malgun Gothic, Apple SD Gothic Neo, sans-serif"
COLOR_ACTUAL = "#1B6CA8"
COLOR_BUDGET = "#94A3B8"
COLOR_POS = "#0F766E"
COLOR_NEG = "#B91C1C"
COLOR_ACCENT = "#D97706"
DIV_COLORS = [
    "#1B6CA8",
    "#0F766E",
    "#D97706",
    "#7C3AED",
    "#BE123C",
    "#0369A1",
    "#4D7C0F",
    "#0E7490",
]


@st.cache_data
def load_csv(path: Path) -> pd.DataFrame:
    return pd.read_csv(path, encoding="utf-8-sig")


def style_fig(fig: go.Figure, height: int = 400) -> go.Figure:
    fig.update_layout(
        height=height,
        margin=dict(l=8, r=8, t=48, b=8),
        font=dict(family=FONT, size=13),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0),
        hovermode="x unified",
    )
    fig.update_xaxes(showgrid=False)
    fig.update_yaxes(gridcolor="#EEF2F6", zerolinecolor="#E2E8F0")
    return fig


def fmt_int(value: float) -> str:
    return f"{value:,.0f}"


def fmt_pct(value: float) -> str:
    return f"{value:.1f}%"


def prepare(monthly: pd.DataFrame, budget: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    monthly = monthly.copy()
    budget = budget.copy()
    monthly["월"] = pd.to_datetime(monthly["월"])
    budget["월"] = pd.to_datetime(budget["월"])

    monthly["매출총이익률"] = monthly["매출총이익"] / monthly["매출액"] * 100
    monthly["영업이익률"] = monthly["영업이익"] / monthly["매출액"] * 100
    monthly["EBITDA마진"] = monthly["EBITDA"] / monthly["매출액"] * 100
    monthly["원가율"] = monthly["매출원가"] / monthly["매출액"] * 100
    monthly["판관비율"] = monthly["판관비"] / monthly["매출액"] * 100

    budget["영업이익달성률"] = budget["실적영업이익"] / budget["예산영업이익"] * 100
    budget["영업이익차이"] = budget["실적영업이익"] - budget["예산영업이익"]
    return monthly, budget


def filter_frame(df: pd.DataFrame, divisions: list[str], start, end) -> pd.DataFrame:
    return df[df["사업부"].isin(divisions) & df["월"].between(start, end)].copy()


def month_label(series: pd.Series) -> pd.Series:
    return series.dt.strftime("%Y-%m")


st.set_page_config(page_title="실적 비교 대시보드", page_icon="📊", layout="wide")
st.markdown(
    """
    <style>
      .block-container { padding-top: 1.4rem; padding-bottom: 2rem; }
      div[data-testid="stMetricValue"] { font-size: 1.45rem; }
    </style>
    """,
    unsafe_allow_html=True,
)

monthly_raw = load_csv(MONTHLY_PATH)
budget_raw = load_csv(BUDGET_PATH)
monthly_all, budget_all = prepare(monthly_raw, budget_raw)

months = sorted(monthly_all["월"].unique())
divisions = sorted(monthly_all["사업부"].unique())

st.sidebar.header("조회 조건")
selected_divs = st.sidebar.multiselect("사업부", divisions, default=divisions)
start_m, end_m = st.sidebar.select_slider(
    "기간",
    options=months,
    value=(months[0], months[-1]),
    format_func=lambda d: pd.Timestamp(d).strftime("%Y-%m"),
)

if not selected_divs:
    st.warning("사업부를 한 개 이상 선택하세요.")
    st.stop()

monthly = filter_frame(monthly_all, selected_divs, start_m, end_m)
budget = filter_frame(budget_all, selected_divs, start_m, end_m)

if monthly.empty or budget.empty:
    st.warning("선택한 조건에 해당하는 데이터가 없습니다.")
    st.stop()

sales_act = budget["실적매출"].sum()
sales_bud = budget["예산매출"].sum()
sales_gap = sales_act - sales_bud
sales_rate = sales_act / sales_bud * 100
op_act = budget["실적영업이익"].sum()
op_bud = budget["예산영업이익"].sum()
op_gap = op_act - op_bud
op_rate = op_act / op_bud * 100
gpm = monthly["매출총이익"].sum() / monthly["매출액"].sum() * 100
opm = monthly["영업이익"].sum() / monthly["매출액"].sum() * 100
ebitda = monthly["EBITDA"].sum()
ocf = monthly["영업현금흐름"].sum()

st.title("실적 비교 대시보드")
st.caption(
    f"{pd.Timestamp(start_m).strftime('%Y-%m')} ~ {pd.Timestamp(end_m).strftime('%Y-%m')}  ·  "
    f"{len(selected_divs)}개 사업부  ·  단위: 백만원, %"
)

k1, k2, k3, k4, k5, k6 = st.columns(6)
k1.metric("실적 매출", fmt_int(sales_act), f"{sales_gap:+,.0f} vs 예산")
k2.metric("매출 달성률", fmt_pct(sales_rate), f"{sales_rate - 100:+.1f}%p")
k3.metric("실적 영업이익", fmt_int(op_act), f"{op_gap:+,.0f} vs 예산")
k4.metric("영업이익 달성률", fmt_pct(op_rate), f"{op_rate - 100:+.1f}%p")
k5.metric("영업이익률", fmt_pct(opm), f"매출총이익률 {gpm:.1f}%")
k6.metric("EBITDA / 영업CF", f"{fmt_int(ebitda)}", f"CF {fmt_int(ocf)}")

by_div = (
    budget.groupby("사업부", as_index=False)
    .agg(
        예산매출=("예산매출", "sum"),
        실적매출=("실적매출", "sum"),
        매출차이=("차이", "sum"),
        예산영업이익=("예산영업이익", "sum"),
        실적영업이익=("실적영업이익", "sum"),
        담당=("담당", "first"),
    )
)
by_div["매출달성률"] = by_div["실적매출"] / by_div["예산매출"] * 100
by_div["영업이익달성률"] = by_div["실적영업이익"] / by_div["예산영업이익"] * 100
by_div["영업이익차이"] = by_div["실적영업이익"] - by_div["예산영업이익"]
by_div = by_div.sort_values("매출달성률", ascending=False)

best = by_div.iloc[0]
worst = by_div.iloc[-1]
st.info(
    f"**최고 달성** {best['사업부']} {best['매출달성률']:.1f}% ({best['담당']})  ·  "
    f"**최저 달성** {worst['사업부']} {worst['매출달성률']:.1f}% ({worst['담당']})"
)

tab_budget, tab_trend, tab_quality, tab_raw = st.tabs(
    ["예산 vs 실적", "손익 추이", "수익성 · 효율", "원본 데이터"]
)

with tab_budget:
    c1, c2 = st.columns(2)
    with c1:
        sales_long = by_div.melt(
            id_vars="사업부",
            value_vars=["예산매출", "실적매출"],
            var_name="구분",
            value_name="금액",
        )
        fig = px.bar(
            sales_long,
            x="사업부",
            y="금액",
            color="구분",
            barmode="group",
            color_discrete_map={"예산매출": COLOR_BUDGET, "실적매출": COLOR_ACTUAL},
            title="사업부별 매출: 예산 vs 실적",
        )
        fig.update_traces(hovertemplate="%{x}<br>%{fullData.name}: %{y:,.0f}<extra></extra>")
        st.plotly_chart(style_fig(fig), width="stretch")

    with c2:
        op_long = by_div.melt(
            id_vars="사업부",
            value_vars=["예산영업이익", "실적영업이익"],
            var_name="구분",
            value_name="금액",
        )
        fig = px.bar(
            op_long,
            x="사업부",
            y="금액",
            color="구분",
            barmode="group",
            color_discrete_map={"예산영업이익": COLOR_BUDGET, "실적영업이익": COLOR_ACCENT},
            title="사업부별 영업이익: 예산 vs 실적",
        )
        fig.update_traces(hovertemplate="%{x}<br>%{fullData.name}: %{y:,.0f}<extra></extra>")
        st.plotly_chart(style_fig(fig), width="stretch")

    c3, c4 = st.columns(2)
    with c3:
        rate_df = by_div.sort_values("매출달성률")
        colors = [COLOR_POS if v >= 100 else COLOR_NEG for v in rate_df["매출달성률"]]
        fig = go.Figure(
            go.Bar(
                x=rate_df["매출달성률"],
                y=rate_df["사업부"],
                orientation="h",
                marker_color=colors,
                text=[f"{v:.1f}%" for v in rate_df["매출달성률"]],
                textposition="outside",
                hovertemplate="%{y}: %{x:.1f}%<extra></extra>",
            )
        )
        fig.add_vline(x=100, line_dash="dash", line_color="#64748B")
        fig.update_xaxes(title="매출 달성률 (%)")
        fig.update_layout(title="매출 달성률 순위 (100% 기준선)")
        st.plotly_chart(style_fig(fig), width="stretch")

    with c4:
        gap_df = by_div.sort_values("매출차이")
        gap_colors = [COLOR_POS if v >= 0 else COLOR_NEG for v in gap_df["매출차이"]]
        fig = go.Figure(
            go.Bar(
                x=gap_df["매출차이"],
                y=gap_df["사업부"],
                orientation="h",
                marker_color=gap_colors,
                text=[f"{v:+,.0f}" for v in gap_df["매출차이"]],
                textposition="outside",
                hovertemplate="%{y}: %{x:+,.0f}<extra></extra>",
            )
        )
        fig.add_vline(x=0, line_color="#64748B")
        fig.update_xaxes(title="매출 차이 (실적 - 예산)")
        fig.update_layout(title="사업부별 매출 차이")
        st.plotly_chart(style_fig(fig), width="stretch")

    heat = budget.copy()
    heat["월라벨"] = month_label(heat["월"])
    heat_pivot = heat.pivot_table(index="사업부", columns="월라벨", values="달성률", aggfunc="mean")
    fig = px.imshow(
        heat_pivot,
        color_continuous_scale=["#B91C1C", "#F8FAFC", "#0F766E"],
        color_continuous_midpoint=100,
        aspect="auto",
        title="월별 매출 달성률 히트맵",
        labels={"color": "달성률(%)"},
    )
    fig.update_traces(hovertemplate="%{y} · %{x}<br>달성률 %{z:.1f}%<extra></extra>")
    st.plotly_chart(style_fig(fig, height=460), width="stretch")

    rank = by_div[
        [
            "사업부",
            "담당",
            "예산매출",
            "실적매출",
            "매출차이",
            "매출달성률",
            "예산영업이익",
            "실적영업이익",
            "영업이익차이",
            "영업이익달성률",
        ]
    ].copy()
    st.subheader("사업부 요약")
    st.dataframe(
        rank,
        width="stretch",
        hide_index=True,
        column_config={
            "예산매출": st.column_config.NumberColumn(format="%.0f"),
            "실적매출": st.column_config.NumberColumn(format="%.0f"),
            "매출차이": st.column_config.NumberColumn(format="%+.0f"),
            "매출달성률": st.column_config.NumberColumn(format="%.1f%%"),
            "예산영업이익": st.column_config.NumberColumn(format="%.0f"),
            "실적영업이익": st.column_config.NumberColumn(format="%.0f"),
            "영업이익차이": st.column_config.NumberColumn(format="%+.0f"),
            "영업이익달성률": st.column_config.NumberColumn(format="%.1f%%"),
        },
    )

with tab_trend:
    monthly_plot = monthly.copy()
    monthly_plot["월라벨"] = month_label(monthly_plot["월"])
    monthly_plot = monthly_plot.sort_values("월")

    total_month = (
        monthly.groupby("월", as_index=False)[["매출액", "영업이익", "EBITDA", "영업현금흐름"]].sum()
    )
    total_month["월라벨"] = month_label(total_month["월"])

    c1, c2 = st.columns(2)
    with c1:
        fig = px.line(
            monthly_plot,
            x="월라벨",
            y="매출액",
            color="사업부",
            color_discrete_sequence=DIV_COLORS,
            markers=True,
            title="사업부별 월 매출 추이",
        )
        st.plotly_chart(style_fig(fig), width="stretch")
    with c2:
        fig = px.line(
            monthly_plot,
            x="월라벨",
            y="영업이익",
            color="사업부",
            color_discrete_sequence=DIV_COLORS,
            markers=True,
            title="사업부별 월 영업이익 추이",
        )
        st.plotly_chart(style_fig(fig), width="stretch")

    tot_long = total_month.melt(
        id_vars="월라벨",
        value_vars=["매출액", "영업이익", "EBITDA"],
        var_name="지표",
        value_name="금액",
    )
    fig = px.line(
        tot_long,
        x="월라벨",
        y="금액",
        color="지표",
        markers=True,
        color_discrete_map={"매출액": COLOR_ACTUAL, "영업이익": COLOR_ACCENT, "EBITDA": COLOR_POS},
        title="전사 합산 손익 추이",
    )
    st.plotly_chart(style_fig(fig), width="stretch")

    budget_plot = budget.copy()
    budget_plot["월라벨"] = month_label(budget_plot["월"])
    rate_month = budget_plot.groupby("월라벨", as_index=False).agg(
        예산매출=("예산매출", "sum"),
        실적매출=("실적매출", "sum"),
        예산영업이익=("예산영업이익", "sum"),
        실적영업이익=("실적영업이익", "sum"),
    )
    rate_month["매출달성률"] = rate_month["실적매출"] / rate_month["예산매출"] * 100
    rate_month["영업이익달성률"] = rate_month["실적영업이익"] / rate_month["예산영업이익"] * 100
    rate_long = rate_month.melt(
        id_vars="월라벨",
        value_vars=["매출달성률", "영업이익달성률"],
        var_name="구분",
        value_name="달성률",
    )
    fig = px.line(
        rate_long,
        x="월라벨",
        y="달성률",
        color="구분",
        markers=True,
        color_discrete_map={"매출달성률": COLOR_ACTUAL, "영업이익달성률": COLOR_ACCENT},
        title="월별 예산 달성률",
    )
    fig.add_hline(y=100, line_dash="dash", line_color="#64748B")
    st.plotly_chart(style_fig(fig), width="stretch")

    fig = px.bar(
        total_month,
        x="월라벨",
        y="영업현금흐름",
        title="월별 영업현금흐름",
        color="영업현금흐름",
        color_continuous_scale=["#B91C1C", "#F8FAFC", "#0F766E"],
        color_continuous_midpoint=0,
    )
    fig.update_coloraxes(showscale=False)
    st.plotly_chart(style_fig(fig), width="stretch")

with tab_quality:
    monthly_plot = monthly.copy()
    monthly_plot["월라벨"] = month_label(monthly_plot["월"])
    monthly_plot = monthly_plot.sort_values("월")

    margin_src = monthly.copy()
    margin_src["수출가중"] = margin_src["매출액"] * margin_src["수출비중"]
    margin_month = margin_src.groupby("월", as_index=False).agg(
        매출액=("매출액", "sum"),
        매출총이익=("매출총이익", "sum"),
        영업이익=("영업이익", "sum"),
        EBITDA=("EBITDA", "sum"),
        수출가중=("수출가중", "sum"),
    )
    margin_month["매출총이익률"] = margin_month["매출총이익"] / margin_month["매출액"] * 100
    margin_month["영업이익률"] = margin_month["영업이익"] / margin_month["매출액"] * 100
    margin_month["EBITDA마진"] = margin_month["EBITDA"] / margin_month["매출액"] * 100
    margin_month["월라벨"] = month_label(margin_month["월"])

    c1, c2 = st.columns(2)
    with c1:
        m_long = margin_month.melt(
            id_vars="월라벨",
            value_vars=["매출총이익률", "영업이익률", "EBITDA마진"],
            var_name="마진",
            value_name="비율",
        )
        fig = px.line(
            m_long,
            x="월라벨",
            y="비율",
            color="마진",
            markers=True,
            title="전사 수익성 마진 추이",
        )
        st.plotly_chart(style_fig(fig), width="stretch")
    with c2:
        fig = px.line(
            monthly_plot,
            x="월라벨",
            y="수출비중",
            color="사업부",
            color_discrete_sequence=DIV_COLORS,
            markers=True,
            title="사업부별 수출비중",
        )
        st.plotly_chart(style_fig(fig), width="stretch")

    struct = (
        monthly.groupby("사업부", as_index=False)[["매출액", "매출원가", "매출총이익", "판관비", "영업이익"]]
        .sum()
        .sort_values("매출액", ascending=False)
    )
    struct_long = struct.melt(
        id_vars="사업부",
        value_vars=["매출원가", "판관비", "영업이익"],
        var_name="구성",
        value_name="금액",
    )
    fig = px.bar(
        struct_long,
        x="사업부",
        y="금액",
        color="구성",
        barmode="stack",
        color_discrete_map={"매출원가": "#CBD5E1", "판관비": "#94A3B8", "영업이익": COLOR_ACTUAL},
        title="사업부 손익 구조 (원가 + 판관비 + 영업이익 ≈ 매출)",
    )
    st.plotly_chart(style_fig(fig), width="stretch")

    c3, c4 = st.columns(2)
    with c3:
        fig = px.line(
            monthly_plot,
            x="월라벨",
            y="AR회전일수",
            color="사업부",
            color_discrete_sequence=DIV_COLORS,
            markers=True,
            title="AR 회전일수 (낮을수록 회수 빠름)",
        )
        st.plotly_chart(style_fig(fig), width="stretch")
    with c4:
        fig = px.line(
            monthly_plot,
            x="월라벨",
            y="AP회전일수",
            color="사업부",
            color_discrete_sequence=DIV_COLORS,
            markers=True,
            title="AP 회전일수",
        )
        st.plotly_chart(style_fig(fig), width="stretch")

    wc = (
        monthly.groupby("사업부", as_index=False)
        .agg(AR회전일수=("AR회전일수", "mean"), AP회전일수=("AP회전일수", "mean"), 수출비중=("수출비중", "mean"))
        .round(1)
    )
    wc = wc.merge(
        by_div[["사업부", "매출달성률", "영업이익달성률", "실적매출", "실적영업이익"]],
        on="사업부",
    )
    st.subheader("사업부 효율 요약")
    st.dataframe(
        wc.sort_values("실적매출", ascending=False),
        width="stretch",
        hide_index=True,
        column_config={
            "AR회전일수": st.column_config.NumberColumn(format="%.1f일"),
            "AP회전일수": st.column_config.NumberColumn(format="%.1f일"),
            "수출비중": st.column_config.NumberColumn(format="%.1f%%"),
            "매출달성률": st.column_config.NumberColumn(format="%.1f%%"),
            "영업이익달성률": st.column_config.NumberColumn(format="%.1f%%"),
            "실적매출": st.column_config.NumberColumn(format="%.0f"),
            "실적영업이익": st.column_config.NumberColumn(format="%.0f"),
        },
    )

with tab_raw:
    left_col, right_col = st.columns(2, gap="large")
    show_monthly = monthly.sort_values(["사업부", "월"]).copy()
    show_monthly["월"] = month_label(show_monthly["월"])
    show_budget = budget.sort_values(["사업부", "월"]).copy()
    show_budget["월"] = month_label(show_budget["월"])

    with left_col:
        st.subheader("사업부 월별 실적")
        st.caption(MONTHLY_PATH.name)
        st.dataframe(show_monthly, width="stretch", hide_index=True, height=640)
    with right_col:
        st.subheader("예산 대비 실적")
        st.caption(BUDGET_PATH.name)
        st.dataframe(show_budget, width="stretch", hide_index=True, height=640)
