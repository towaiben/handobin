import os

import streamlit as st
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

st.set_page_config(page_title="AI Chat", page_icon="💬", layout="centered")

api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    st.error(".env 파일에 OPENAI_API_KEY가 없습니다.")
    st.stop()

client = OpenAI(api_key=api_key)

MODELS = ["gpt-4.1-mini", "gpt-4.1", "gpt-4o-mini", "gpt-4o"]

if "messages" not in st.session_state:
    st.session_state.messages = []

with st.sidebar:
    st.title("설정")
    model = st.selectbox("모델", MODELS, index=0)
    st.caption("대화 내용은 이 브라우저 세션에만 유지됩니다.")
    if st.button("대화 초기화", width="stretch"):
        st.session_state.messages = []
        st.rerun()

st.title("💬 AI Chat")
st.caption("OpenAI API로 대화합니다.")

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

prompt = st.chat_input("메시지를 입력하세요")
if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        try:
            stream = client.chat.completions.create(
                model=model,
                messages=st.session_state.messages,
                stream=True,
            )
            reply = st.write_stream(stream)
        except Exception as exc:
            reply = f"응답을 가져오지 못했습니다: {exc}"
            st.error(reply)

    st.session_state.messages.append({"role": "assistant", "content": reply})
