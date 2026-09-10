import os
import time

import requests
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(page_title="API 요청/응답 뷰어", layout="wide")

KOREAEXIM_KEY = os.getenv("KOREAEXIM_KEY", "")
FRED_KEY = os.getenv("FRED_KEY", "")
DART_KEY = os.getenv("DART_KEY", "")

APIS = [
    {
        "name": "한국수출입은행 환율",
        "method": "GET",
        "base_url": "https://oapi.koreaexim.go.kr/site/program/financial/exchangeJSON",
        "params": {
            "authkey": KOREAEXIM_KEY,
            "data": "AP01",
        },
        "secret_param": "authkey",
        "key_ok": bool(KOREAEXIM_KEY),
        "key_label": "KOREAEXIM_KEY",
    },
    {
        "name": "FRED DEXKOUS",
        "method": "GET",
        "base_url": "https://api.stlouisfed.org/fred/series/observations",
        "params": {
            "series_id": "DEXKOUS",
            "api_key": FRED_KEY,
            "file_type": "json",
            "observation_start": "2026-01-01",
        },
        "secret_param": "api_key",
        "key_ok": bool(FRED_KEY),
        "key_label": "FRED_KEY",
    },
    {
        "name": "OpenDART 재무제표",
        "method": "GET",
        "base_url": "https://opendart.fss.or.kr/api/fnlttSinglAcnt.json",
        "params": {
            "crtfc_key": DART_KEY,
            "corp_code": "00126380",
            "bsns_year": "2024",
            "reprt_code": "11011",
        },
        "secret_param": "crtfc_key",
        "key_ok": bool(DART_KEY),
        "key_label": "DART_KEY",
    },
]


def mask_params(params: dict, secret_param: str) -> dict:
    masked = dict(params)
    value = masked.get(secret_param, "")
    if value:
        masked[secret_param] = value[:4] + "****" + value[-4:]
    else:
        masked[secret_param] = "(미설정)"
    return masked


def build_url(base_url: str, params: dict) -> str:
    query = "&".join(f"{k}={v}" for k, v in params.items())
    return f"{base_url}?{query}"


def call_api(api: dict):
    started = time.perf_counter()
    try:
        response = requests.get(api["base_url"], params=api["params"], timeout=20)
        elapsed_ms = (time.perf_counter() - started) * 1000
        try:
            body = response.json()
        except ValueError:
            body = response.text
        return {
            "ok": True,
            "status_code": response.status_code,
            "elapsed_ms": elapsed_ms,
            "headers": dict(response.headers),
            "body": body,
        }
    except requests.RequestException as exc:
        elapsed_ms = (time.perf_counter() - started) * 1000
        return {
            "ok": False,
            "status_code": None,
            "elapsed_ms": elapsed_ms,
            "headers": {},
            "body": str(exc),
        }


def render_api(api: dict) -> None:
    if not api["key_ok"]:
        st.error(f".env 에 {api['key_label']} 가 없습니다.")
        return

    result = call_api(api)
    visible_params = mask_params(api["params"], api["secret_param"])
    visible_url = build_url(api["base_url"], visible_params)

    col_req, col_res = st.columns(2)

    with col_req:
        st.markdown("**요청 (Request)**")
        st.code(f"{api['method']} {visible_url}", language="http")
        st.json(
            {
                "method": api["method"],
                "url": api["base_url"],
                "params": visible_params,
            }
        )

    with col_res:
        st.markdown("**응답 (Response)**")
        if result["ok"]:
            st.metric("HTTP 상태", result["status_code"])
            st.caption(f"소요 시간: {result['elapsed_ms']:.0f} ms")
            with st.expander("응답 헤더"):
                st.json(result["headers"])
            st.json(result["body"])
        else:
            st.error("요청 실패")
            st.caption(f"소요 시간: {result['elapsed_ms']:.0f} ms")
            st.code(result["body"])


st.title("세 가지 API 요청 / 응답")
st.caption(".env 의 KOREAEXIM_KEY, FRED_KEY, DART_KEY 를 사용해 각 API를 호출합니다.")

if st.button("다시 요청하기", type="primary"):
    st.rerun()

tabs = st.tabs([api["name"] for api in APIS])
for tab, api in zip(tabs, APIS):
    with tab:
        render_api(api)
