import streamlit as st
import pandas as pd
import os
import requests

# 설정
TITLE = "☄️ 우주 낙하물체 예측 for MSSB"
LOCAL_DIR = r"C:\tip"
CSV_PATH = os.path.join(LOCAL_DIR, "gp_active.csv")
CSV_URL = "https://celestrak.org/NORAD/elements/gp.php?GROUP=active&FORMAT=CSV"

st.set_page_config(page_title=TITLE)
st.title(TITLE)

# 📥 1. CSV 다운로드 버튼
if st.button("1️⃣ GP CSV 다운로드"):
    try:
        os.makedirs(LOCAL_DIR, exist_ok=True)
        response = requests.get(CSV_URL, timeout=10)
        with open(CSV_PATH, "wb") as f:
            f.write(response.content)
        st.success(f"✅ 다운로드 완료 → `{CSV_PATH}`")
    except Exception as e:
        st.error(f"❌ 다운로드 실패: {e}")

# 📂 2. CSV 불러오기 버튼
if st.button("2️⃣ 로컬 CSV 파일 불러오기"):
    if os.path.exists(CSV_PATH):
        df = pd.read_csv(CSV_PATH)
        st.session_state["sat_df"] = df
        st.success(f"📊 위성 데이터 불러오기 성공 → `{len(df)}개` 개체")
    else:
        st.warning("⚠️ CSV 파일이 존재하지 않습니다. 먼저 다운로드하세요.")

# ▶️ 3. 분석 시작 버튼
if st.button("3️⃣ 낙하 이벤트 분석 시작"):
    if "sat_df" not in st.session_state:
        st.warning("❗ 먼저 로컬 CSV를 불러와주세요.")
    else:
        df = st.session_state["sat_df"]
        # 분석 로직 삽입 위치 → 낙하 이벤트 판별, 거리/고도 계산 등
        st.info("🔍 분석 기능은 곧 추가됩니다.")
