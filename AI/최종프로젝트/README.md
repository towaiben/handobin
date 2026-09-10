# 파이낸싱 요율 조회·산출·제안서 자동화

단일 HTML로 기준금리·환가료·보험요율을 조회하고, 목표 거래이익에 맞는 Admin Fee / Interest Spread를 역산한 뒤 Financing Proposal을 Word·PDF로 만드는 도구입니다.

---

## 프로젝트 이름

**Financing Rate Calculator — 파이낸싱 요율 조회·산출·제안서 자동화**

---

## 프로젝트 개요

**목적과 임팩트**  
파이낸싱 견적 때 Term SOFR, EURIBOR, SHIBOR, HIBOR, 환가료, K-SURE·AR 보험요율을 사이트와 엑셀에서 따로 찾고, 목표 거래이익에 맞춰 Admin Fee와 Interest Spread를 반복 계산한 뒤 영문 제안서에 다시 옮겨 적던 일을 한 화면에서 끝냅니다. 견적 회신 시간을 줄이고, 숫자 오기와 제안서 재작성 부담을 낮춰 영업 품질을 맞추는 것이 목표입니다.

**도입 전 / 도입 후**  
도입 전에는 기준금리 사이트, 환가료 엑셀, 보험요율표, 원가 계산, 영문 제안서 작성이 각각 끊겨 있었습니다. 도입 후에는 요율 조회 → 요율 산출(목표 이익 역산·조합 추천) → 요율제안서 미리보기·문서 생성까지 같은 흐름으로 이어집니다.

**프로세스와 기술 흐름**  
조회 탭은 공개 금리 페이지를 CORS 프록시로 읽어 최근 5영업일을 보여주고, 환가료·보험은 HTML에 내장한 표(이 패키지는 시연용 더미)를 사용합니다. 산출 탭은 구매가·기간·결제조건·보험을 받아 판매가·금융비용·거래이익을 계산하고, Admin 최소 1.50%·0.10% 단위로 목표 이익을 맞추는 조합을 제시합니다. 확정 요율은 제안서 탭으로 넘어가 브라우저에서 DOCX(ZIP/OOXML)와 PDF(html2canvas + 자체 PDF)를 만듭니다.

**특별히 신경 쓴 점**  
Interest Rate는 시장 금리 커브가 아니라 목표 거래이익을 맞추려고 역산한 연율입니다. 기간이 길수록 같은 연율의 이자 금액이 커지므로 화면에 보이는 연율은 오히려 낮아질 수 있습니다. Admin 하한, 수동 입력, 추천값 복원, 산출 보고서 PDF까지 협상 숫자를 바로 시험할 수 있게 만들었습니다.

**후속 프로젝트**  
사내 최신 환가료·보험요율표를 업로드하면 자동 반영되게 하고, CME 공식 Term SOFR·내부 ERP 원가와 연동하면 운영 도구로 키울 수 있습니다. 거래 건별 견적 이력 저장과 승인 흐름을 붙이는 것도 다음 단계입니다.

---

## 프로젝트 기술스택

**큰 틀: 단일 HTML**

설치 없이 브라우저만 있으면 동작하는 한 장의 `Financing Rate Calculator.html`이 본편입니다. 초기에 만든 Streamlit 초안(`Financing Rate Calculator.py`)은 제안서 작성만 있는 프로토타입입니다.

| 구분 | 이름 | 한 줄 설명 |
| --- | --- | --- |
| 앱 구조 | HTML / CSS / JavaScript | 조회·산출·제안서 3개 탭을 한 파일에 구성 |
| 글꼴 | Open Sans, NanumBarunGothic | 화면·제안서용 영문/한글 웹폰트 |
| 금리 조회 | `fetch` + CORS 프록시 | Term SOFR, EURIBOR, SHIBOR, HIBOR 최근 고시 수집 |
| 캐시 | `localStorage` | 조회한 기준금리를 브라우저에 잠시 저장 |
| PDF | html2canvas | 화면을 이미지로 캡처해 산출 보고서·제안서 PDF에 사용 |
| PDF | 자체 PDF writer | 캡처 이미지를 PDF 바이트로 조립 |
| Word | 자체 DOCX (ZIP + OOXML) | 서버 없이 Financing Proposal `.docx` 생성 |
| 프로토타입 | Streamlit | 초기에 제안서 화면만 검증할 때 사용 |

---

## 프로젝트 사용방법

이 폴더를 받은 뒤 **본편은 HTML을 더블클릭**하면 됩니다. 인터넷이 되어야 최신 기준금리와 글꼴·PDF 도구를 불러옵니다.

### 1) 본편 실행 (권장)

1. `최종프로젝트` 폴더를 연다.
2. `Assignment` 폴더를 연다.
3. `Financing Rate Calculator.html`을 더블클릭한다.
4. 브라우저가 열리면 위쪽 탭 순서대로 사용한다.
   - **요율 조회**: 기준금리 새로고침, 환가료·보험 표 확인
   - **요율 산출**: 목표 거래이익·거래 조건을 넣고 조합을 고른 뒤 `적용`
   - **요율제안서 작성**: 회사명 등을 채우고 Word 또는 PDF로 저장

Windows에서 기본 브라우저로 열리면 추가 설치는 필요 없습니다.

### 2) (선택) 초안 Streamlit 화면

제안서만 있는 예전 버전입니다. 본편 HTML과 기능이 다릅니다.

1. 컴퓨터에 Python이 없으면 [https://www.python.org/downloads/](https://www.python.org/downloads/) 에서 설치한다.  
   설치 화면에서 **Add python.exe to PATH** 에 체크한다.
2. 키보드 `Win + R` 을 누르고 `cmd` 를 입력한 뒤 확인을 누른다.
3. 아래를 **한 줄씩** 복사해서 검은 창에 붙여넣고 Enter를 누른다.

```bat
cd /d %USERPROFILE%\Desktop\AI\최종프로젝트\Assignment
```

폴더를 다른 곳에 두었다면 `cd /d` 뒤에 그 폴더 경로를 넣는다.

4. 필요한 프로그램을 설치한다.

```bat
pip install streamlit
```

5. 실행한다.

```bat
streamlit run "Financing Rate Calculator.py"
```

6. 브라우저가 자동으로 열리면 사용한다. 안 열리면 검은 창에 나온 `http://localhost:8501` 주소를 브라우저 주소창에 붙여넣는다.

---

## 폴더 안내

원본 `Assignment` 폴더 구조를 그대로 복사했습니다. 원본 파일은 원래 자리에 그대로 있습니다.

```
최종프로젝트/
  README.md
  Assignment/
    Financing Rate Calculator.html          ← 본편 (더블클릭)
    Financing Rate Calculator.py            ← Streamlit 초안
    Financing Rate Calculator 발표 스크립트.txt
    Agent 등록 답안.txt
    Interest Rate가 기간이 길수록 낮아지는 것은 버그가.txt
    AI Agent Data Scrolling URL.docx        ← 공개 금리 사이트 주소
    26년 적용 보험요율표.xlsx               ← 시연용 더미
    AR보험 비교.xlsx                        ← 시연용 더미
    ★환가료율표(안내용) 26.03.23 1.xlsx     ← 시연용 더미
```

---

## 민감정보 처리

이 패키지는 **공유·제출용**입니다. 사내 숫자는 넣지 않았습니다.

| 항목 | 처리 | 설명 |
| --- | --- | --- |
| 환가료율표 | 더미 파일 + HTML 더미 숫자 | 기간·L/C·D/A 구조만 남기고 스프레드는 가상 값 |
| K-SURE 2026 적용요율 | 더미 파일 + HTML 더미 숫자 | 등급·기간 칸 구조만 유지 |
| AR 보험 비교 | 더미 파일 + HTML 더미 숫자 | 관련 법인을 SAMPLE-A~E로, 보험료는 가상 값 |
| 작업용 AUTOCOM 원가 Table | **생략** | Buyer/Maker 실명, 거래 원가·마진·금액이 들어 있는 사내 작업 파일 |
| 제안서 서명자 | 더미 | `SAMPLE SIGNER` 로 대체. 실제 운영 시 HTML의 `LENDER_SIGNER`를 바꾸면 됩니다 |

실제 견적에 쓰려면 원본 `Assignment` 폴더의 사내 엑셀을 보고 HTML 안 `FX_FEE_*`, `KSURE_RATES`, `AR_INSURERS` 값을 다시 넣으면 됩니다. 이 패키지의 숫자로 대외 견적을 내지 마십시오.

기준금리(Term SOFR 등)는 공개 웹 고시라 그대로 조회합니다.
