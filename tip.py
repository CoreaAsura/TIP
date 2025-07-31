import streamlit as st
import pandas as pd
import os
import requests

# 📌 설정값
TITLE = "☄️ 우주 낙하물체 예측 for MSSB"
LOCAL_DIR = r"C:\tip"
CSV_PATH = os.path.join(LOCAL_DIR, "gp_active.csv")
CSV_URL = "https://celestrak.org/NORAD/elements/gp.php?GROUP=active&FORMAT=CSV"

st.set_page_config(page_title=TITLE)
st.title(TITLE)

# 📥 1️⃣ CSV 다운로드 버튼
if st.button("1️⃣ GP CSV 다운로드 시작"):
    os.makedirs(LOCAL_DIR, exist_ok=True)
    try:
        response = requests.get(CSV_URL, timeout=10)
        if response.status_code == 200:
            with open(CSV_PATH, "wb") as f:
                f.write(response.content)

            # 📏 파일 크기 유효성 확인
            if os.path.getsize(CSV_PATH) > 1000:  # 최소 1KB 이상
                st.success(f"✅ CSV 다운로드 완료: `{CSV_PATH}`")
            else:
                os.remove(CSV_PATH)
                st.error("❌ 파일은 다운로드 되었지만 내용이 비어있거나 잘못되었습니다.")
        else:
            st.error(f"❌ 다운로드 실패 - 응답 코드: {response.status_code}")
    except Exception as e:
        st.error(f"🚫 다운로드 에러 발생: {str(e)}")

# 📂 2️⃣ 로컬 CSV 불러오기 버튼
if st.button("2️⃣ 로컬 파일 불러오기"):
    if os.path.exists(CSV_PATH):
        try:
            df = pd.read_csv(CSV_PATH)
            st.session_state["sat_df"] = df
            st.success(f"📊 위성 데이터 불러오기 완료: `{len(df)}` 개체")
        except Exception as e:
            st.error(f"⚠️ CSV 파일 파싱 실패: {str(e)}")
    else:
        st.warning("⚠️ 아직 파일이 존재하지 않습니다. 먼저 다운로드 버튼을 누르세요.")

# ▶️ 3️⃣ 낙하 이벤트 분석 시작 버튼 (로직은 이후 삽입)
if st.button("3️⃣ 낙하 이벤트 분석 시작"):
    if "sat_df" not in st.session_state:
        st.warning("❗ 먼저 CSV 파일을 불러와주세요.")
    else:
        st.info("🔍 분석 로직은 다음 단계에서 연결됩니다.")
