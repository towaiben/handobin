from datetime import date, datetime, time
from io import BytesIO
import math
import time as time_module

import numpy as np
import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="Streamlit 컴포넌트 갤러리",
    page_icon="🎈",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        "Get Help": "https://docs.streamlit.io",
        "Report a bug": "https://github.com/streamlit/streamlit/issues",
        "About": "Streamlit 요소를 한곳에서 살펴보는 데모입니다.",
    },
)


def has_api(name: str) -> bool:
    return hasattr(st, name)


def call_api(name: str, *args, **kwargs):
    fn = getattr(st, name, None)
    if fn is None:
        st.caption(f"`st.{name}` 은 현재 Streamlit 버전에 없습니다.")
        return None
    return fn(*args, **kwargs)


@st.cache_data
def sample_sales() -> pd.DataFrame:
    months = pd.date_range("2026-01-01", periods=12, freq="MS")
    rng = np.random.default_rng(42)
    return pd.DataFrame(
        {
            "월": months,
            "매출": rng.integers(80, 180, size=12) * 100,
            "비용": rng.integers(40, 120, size=12) * 100,
            "이익": rng.integers(10, 80, size=12) * 100,
        }
    )


@st.cache_data
def sample_people() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "이름": ["김민수", "이지은", "박서준", "최유진", "정하늘"],
            "부서": ["영업", "재무", "개발", "영업", "기획"],
            "점수": [88, 93, 76, 85, 91],
            "활성": [True, True, False, True, True],
        }
    )


@st.cache_data
def sample_map() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "lat": [37.5665, 35.1796, 35.1595, 37.4563, 33.4996],
            "lon": [126.9780, 129.0756, 126.8526, 126.7052, 126.5312],
            "도시": ["서울", "부산", "광주", "인천", "제주"],
        }
    )


if "counter" not in st.session_state:
    st.session_state.counter = 0
if "chat_history" not in st.session_state:
    st.session_state.chat_history = [
        {"role": "assistant", "content": "안녕하세요! 아래 입력창에 메시지를 남겨 보세요."}
    ]


SECTIONS = [
    "텍스트",
    "데이터",
    "차트",
    "입력 위젯",
    "미디어",
    "레이아웃",
    "상태와 알림",
    "채팅 / 폼",
    "고급 기능",
]

with st.sidebar:
    if has_api("logo"):
        st.logo("https://streamlit.io/images/brand/streamlit-mark-color.png")
    st.title("🎈 갤러리")
    st.caption("사이드바, 라디오, 슬라이더, 토글 등")
    section = st.radio("섹션 선택", SECTIONS, index=0)
    st.divider()
    st.slider("사이드바 슬라이더", 0, 100, 35, key="sidebar_slider")
    st.selectbox("사이드바 선택", ["한국어", "English", "日本語"], key="sidebar_lang")
    dark_mode = st.toggle("다크 모드처럼 보이기", value=False)
    st.metric("세션 카운터", st.session_state.counter, delta=1)
    st.link_button("Streamlit 문서", "https://docs.streamlit.io")

if dark_mode:
    st.markdown(
        """
        <style>
        .stApp { background-color: #0e1117; color: #fafafa; }
        </style>
        """,
        unsafe_allow_html=True,
    )

st.title("Streamlit 컴포넌트 갤러리")
st.caption("가능한 많은 Streamlit 요소를 한 페이지에서 살펴볼 수 있습니다.")
if has_api("badge"):
    c1, c2, c3 = st.columns(3)
    with c1:
        st.badge("텍스트", color="blue")
    with c2:
        st.badge("위젯", color="green")
    with c3:
        st.badge("차트", color="orange")


def section_text() -> None:
    st.header("텍스트 요소")
    st.subheader("제목 / 본문 / 수식 / 코드")
    st.markdown("마크다운으로 **굵게**, *기울임*, `코드`, [링크](https://docs.streamlit.io)를 쓸 수 있습니다.")
    st.text("st.text: 고정 폭 텍스트입니다.")
    st.caption("st.caption: 작은 설명 텍스트입니다.")
    st.latex(r"e^{i\pi} + 1 = 0")
    st.code("for i in range(3):\n    print('hello', i)", language="python")
    if has_api("html"):
        st.html("<p style='color:#ff4b4b'>st.html 로 직접 HTML을 넣을 수 있습니다.</p>")
    st.write("st.write 는 문자열, 숫자, 리스트, 데이터프레임을 모두 출력합니다.", [1, 2, 3])
    with st.echo():
        st.write("st.echo: 코드와 실행 결과를 같이 보여줍니다.")
    st.help(pd.DataFrame)


def section_data() -> None:
    st.header("데이터 표시")
    df = sample_people()
    sales = sample_sales()

    m1, m2, m3 = st.columns(3)
    m1.metric("매출", "1.2억", "+8%")
    m2.metric("비용", "0.7억", "-3%")
    m3.metric("이익", "0.5억", "+12%")

    st.subheader("st.dataframe")
    st.dataframe(sales, width="stretch", hide_index=True)

    st.subheader("st.table")
    st.table(df)

    st.subheader("st.data_editor")
    edited = st.data_editor(
        df,
        num_rows="dynamic",
        width="stretch",
        column_config={
            "점수": st.column_config.ProgressColumn("점수", min_value=0, max_value=100),
            "활성": st.column_config.CheckboxColumn("활성"),
        },
    )
    st.json({"선택한 행 수": len(edited), "부서": edited["부서"].tolist()})

    csv = sales.to_csv(index=False).encode("utf-8-sig")
    st.download_button("CSV 다운로드", csv, file_name="sales.csv", mime="text/csv")


def section_charts() -> None:
    st.header("차트")
    sales = sample_sales().set_index("월")[["매출", "비용", "이익"]]
    chart_tabs = st.tabs(["라인", "바", "영역", "산점", "지도", "기타"])

    with chart_tabs[0]:
        st.line_chart(sales)
    with chart_tabs[1]:
        st.bar_chart(sales)
        try:
            st.bar_chart(sales["이익"], horizontal=True)
        except TypeError:
            pass
    with chart_tabs[2]:
        st.area_chart(sales)
    with chart_tabs[3]:
        st.scatter_chart(sales, x="비용", y="매출", size="이익")
    with chart_tabs[4]:
        st.map(sample_map(), size=80)
    with chart_tabs[5]:
        try:
            import matplotlib.pyplot as plt

            fig, ax = plt.subplots()
            ax.plot(sales.index, sales["매출"], marker="o")
            ax.set_title("matplotlib example")
            st.pyplot(fig)
        except Exception as exc:
            st.info(f"matplotlib 차트를 건너뜁니다: {exc}")

        try:
            import plotly.express as px

            fig = px.line(sales.reset_index(), x="월", y=["매출", "비용"], title="Plotly example")
            st.plotly_chart(fig, width="stretch")
        except Exception as exc:
            st.info(f"plotly 차트를 건너뜁니다: {exc}")

        try:
            st.graphviz_chart(
                """
                digraph {
                    시작 -> 입력
                    입력 -> 처리
                    처리 -> 출력
                }
                """
            )
        except Exception as exc:
            st.info(f"graphviz 차트를 건너뜁니다: {exc}")


def section_widgets() -> None:
    st.header("입력 위젯")
    left, right = st.columns(2)

    with left:
        st.subheader("버튼 / 선택")
        if st.button("카운터 +1", type="primary"):
            st.session_state.counter += 1
        agree = st.checkbox("이용 약관에 동의합니다")
        on = st.toggle("알림 받기", value=True)
        animal = st.radio("좋아하는 동물", ["고양이", "강아지", "토끼"], horizontal=True)
        city = st.selectbox("도시", ["서울", "부산", "대전", "광주"])
        fruits = st.multiselect("과일", ["사과", "바나나", "포도", "수박"], default=["사과"])
        if has_api("pills"):
            tags = st.pills("태그", ["업무", "학습", "취미"], selection_mode="multi")
        else:
            tags = None
        if has_api("segmented_control"):
            view = st.segmented_control("보기", ["일", "주", "월"], default="주")
        else:
            view = None
        if has_api("feedback"):
            st.feedback("thumbs")
        if has_api("menu_button"):
            st.menu_button("내보내기", options=["CSV", "JSON", "PDF"])

    with right:
        st.subheader("값 입력")
        name = st.text_input("이름", placeholder="홍길동")
        age = st.number_input("나이", min_value=0, max_value=120, value=30)
        comment = st.text_area("메모", height=80)
        score = st.slider("점수", 0, 100, 70)
        score_range = st.slider("점수 범위", 0, 100, (40, 90))
        size = st.select_slider("사이즈", options=["XS", "S", "M", "L", "XL"], value="M")
        birthday = st.date_input("생일", value=date(2000, 1, 1))
        meeting = st.time_input("미팅 시간", value=time(9, 30))
        if has_api("datetime_input"):
            event_at = st.datetime_input("일정", value=datetime(2026, 9, 8, 10, 0))
        else:
            event_at = datetime.combine(birthday, meeting)
        color = st.color_picker("테마 색", "#FF4B4B")
        if has_api("pagination"):
            page = st.pagination(42, key="demo_pagination")
        else:
            page = None

    st.info(
        f"동의={agree}, 알림={on}, 동물={animal}, 도시={city}, 과일={fruits}, "
        f"태그={tags}, 보기={view}, 이름={name}, 나이={age}, 점수={score}, "
        f"범위={score_range}, 사이즈={size}, 생일={birthday}, 시간={meeting}, "
        f"일정={event_at}, 색={color}, 페이지={page}, 메모={comment}"
    )

    uploaded = st.file_uploader("파일 업로드", type=["csv", "xlsx", "txt", "png", "jpg"])
    if uploaded is not None:
        st.success(f"업로드됨: {uploaded.name} ({uploaded.size} bytes)")


def section_media() -> None:
    st.header("미디어")
    img = np.zeros((120, 240, 3), dtype=np.uint8)
    img[:, :80] = [255, 75, 75]
    img[:, 80:160] = [255, 255, 255]
    img[:, 160:] = [75, 140, 255]
    st.image(img, caption="st.image: numpy 배열 이미지", width=360)

    sample_rate = 8000
    t = np.linspace(0, 0.4, int(sample_rate * 0.4), endpoint=False)
    wave = (np.sin(2 * math.pi * 440 * t) * 32767).astype(np.int16)
    buf = BytesIO()
    import wave as wav_module

    with wav_module.open(buf, "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(wave.tobytes())
    st.audio(buf.getvalue(), format="audio/wav")

    st.video("https://www.youtube.com/watch?v=B2iAodr0fOo")
    if has_api("audio_input"):
        st.audio_input("목소리 녹음")
    st.camera_input("카메라로 사진 찍기")
    if has_api("pdf"):
        st.caption("st.pdf 는 PDF 파일이 있을 때 미리보기를 보여줍니다.")
    if has_api("iframe"):
        st.iframe("https://docs.streamlit.io", height=320)


def section_layout() -> None:
    st.header("레이아웃")
    col1, col2, col3 = st.columns([2, 1, 1])
    col1.success("넓은 열")
    col2.warning("중간 열")
    col3.error("좁은 열")

    t1, t2, t3 = st.tabs(["탭 A", "탭 B", "탭 C"])
    t1.write("첫 번째 탭입니다.")
    t2.write("두 번째 탭입니다.")
    t3.write("세 번째 탭입니다.")

    with st.expander("펼쳐서 보기", expanded=False):
        st.write("st.expander 안에 숨겨진 내용입니다.")

    if has_api("popover"):
        with st.popover("팝오버"):
            st.checkbox("필터 적용", key="pop_filter")
            st.slider("임계값", 0, 10, 5, key="pop_slider")

    placeholder = st.empty()
    placeholder.info("st.empty: 이 자리는 아래에서 바뀝니다.")
    if st.button("플레이스홀더 바꾸기"):
        placeholder.success("내용이 교체되었습니다.")

    with st.container(border=True):
        st.write("st.container: 테두리 있는 묶음")
        if has_api("space"):
            st.space("small")
        a, b = st.columns(2)
        a.button("컨테이너 버튼 A")
        b.button("컨테이너 버튼 B")

    if has_api("container"):
        try:
            with st.container(horizontal=True):
                st.button("가로 1")
                st.button("가로 2")
                st.button("가로 3")
        except TypeError:
            pass


def section_status() -> None:
    st.header("상태 / 진행 / 알림")
    st.success("성공 메시지")
    st.info("정보 메시지")
    st.warning("경고 메시지")
    st.error("오류 메시지")
    try:
        1 / 0
    except ZeroDivisionError as exc:
        st.exception(exc)

    if st.button("스피너 3초 보기"):
        with st.spinner("처리 중..."):
            time_module.sleep(1.2)
        st.toast("완료되었습니다.")

    if st.button("진행 바 보기"):
        bar = st.progress(0, text="진행 중")
        for i in range(1, 6):
            time_module.sleep(0.15)
            bar.progress(i * 20, text=f"{i * 20}%")
        bar.progress(100, text="완료")

    if st.button("st.status 보기"):
        with st.status("작업 로그", expanded=True) as status:
            st.write("1단계: 데이터 준비")
            time_module.sleep(0.4)
            st.write("2단계: 계산")
            time_module.sleep(0.4)
            status.update(label="완료", state="complete")

    b1, b2 = st.columns(2)
    if b1.button("풍선 🎉"):
        st.balloons()
    if b2.button("눈 내리기 ❄️"):
        st.snow()


def section_chat_form() -> None:
    st.header("채팅 / 폼")

    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])

    prompt = st.chat_input("메시지를 입력하세요")
    if prompt:
        st.session_state.chat_history.append({"role": "user", "content": prompt})
        st.session_state.chat_history.append(
            {"role": "assistant", "content": f"받은 메시지: {prompt}"}
        )
        st.rerun()

    st.subheader("st.form")
    with st.form("signup_form"):
        user = st.text_input("사용자 이름")
        pw = st.text_input("비밀번호", type="password")
        role = st.selectbox("역할", ["시청자", "편집자", "관리자"])
        submitted = st.form_submit_button("제출")
        if submitted:
            st.success(f"{user or '이름 없음'} / {role} 제출 완료 (비밀번호 길이 {len(pw)})")

    if has_api("dialog"):

        @st.dialog("환영합니다")
        def welcome():
            st.write("이것은 st.dialog 모달입니다.")
            if st.button("닫기"):
                st.rerun()

        if st.button("다이얼로그 열기"):
            welcome()

    if has_api("fragment"):

        @st.fragment
        def live_fragment():
            st.write(f"조각 영역 시각: {datetime.now().strftime('%H:%M:%S')}")
            st.button("이 조각만 새로고침")

        live_fragment()


def section_advanced() -> None:
    st.header("고급 기능")
    st.subheader("세션 상태")
    c1, c2, c3 = st.columns(3)
    if c1.button("증가"):
        st.session_state.counter += 1
    if c2.button("감소"):
        st.session_state.counter -= 1
    if c3.button("초기화"):
        st.session_state.counter = 0
    st.write("현재 값:", st.session_state.counter)

    st.subheader("쿼리 파라미터")
    st.write(dict(st.query_params))

    st.subheader("컨텍스트")
    if has_api("context"):
        ctx = {}
        for attr in ("timezone", "locale", "theme", "url"):
            try:
                ctx[attr] = getattr(st.context, attr, None)
            except Exception:
                ctx[attr] = None
        st.json(ctx)

    st.subheader("스트리밍 출력")
    if st.button("st.write_stream 실행"):

        def streamer():
            for word in ["안녕하세요.", " Streamlit", " 갤러리", " 입니다."]:
                time_module.sleep(0.15)
                yield word

        st.write_stream(streamer())

    st.subheader("캐시")
    st.write("sample_sales / sample_people 는 `@st.cache_data` 로 캐시됩니다.")
    if st.button("캐시 비우기"):
        st.cache_data.clear()
        st.success("캐시를 비웠습니다.")

    st.subheader("코드로만 보여주는 기능")
    st.code(
        """
# 페이지 전환
# st.switch_page("pages/other.py")

# 즉시 중단
# st.stop()

# 로그인 (배포 환경)
# if not st.user.is_logged_in:
#     st.login()
""",
        language="python",
    )


PAGES = {
    "텍스트": section_text,
    "데이터": section_data,
    "차트": section_charts,
    "입력 위젯": section_widgets,
    "미디어": section_media,
    "레이아웃": section_layout,
    "상태와 알림": section_status,
    "채팅 / 폼": section_chat_form,
    "고급 기능": section_advanced,
}

PAGES[section]()
