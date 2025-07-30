import streamlit as st
import requests
import pandas as pd
import datetime

# ▶️ 인증
def get_authenticated_session():
    login_url = "https://www.space-track.org/ajaxauth/login"
    payload = {
        "identity": st.secrets["space_track_id"],
        "password": st.secrets["space_track_pw"]
    }
    session = requests.Session()
    res = session.post(login_url, data=payload)

    if res.status_code == 200:
        st.success("🔐 인증 성공")
        return session
    else:
        st.error(f"🚨 인증 실패: {res.status_code}")
        st.write(res.text)
        return None

# ▶️ TIP 메시지
def fetch_tip_data(session, hours):
    try:
        url = f"https://www.space-track.org/basicspacedata/query/class/tip/EPOCH>now-{hours}h/format/json"
        res = session.get(url)
        if res.status_code == 200:
            data = res.json()
            return pd.DataFrame(data)
        else:
            st.error(f"❌ TIP 오류: {res.status_code}")
            st.write(res.text)
            return pd.DataFrame()
    except Exception as e:
        st.error(f"❌ TIP 오류 발생: {str(e)}")
        return pd.DataFrame()

# ▶️ Decay 메시지
def fetch_decay_data(session):
    try:
        past = (datetime.datetime.utcnow() - datetime.timedelta(days=180)).strftime('%Y-%m-%d')
        url = f"https://www.space-track.org/basicspacedata/query/class/decay/EPOCH>{past}/format/json"
        res = session.get(url)
        if res.status_code == 200:
            data = res.json()
            return pd.DataFrame(data)
        else:
            st.error(f"❌ Decay 오류: {res.status_code}")
            st.write(res.text)
            return pd.DataFrame()
    except Exception as e:
        st.error(f"❌ Decay 오류 발생: {str(e)}")
        return pd.DataFrame()

# ▶️ 서울 기준 필터링
def filter_tip_seoul(df):
    try:
        df["IMPACT_LATITUDE"] = df["IMPACT_LATITUDE"].astype(float)
        df["IMPACT_LONGITUDE"] = df["IMPACT_LONGITUDE"].astype(float)
        return df[
            df["IMPACT_LATITUDE"].between(30.0, 40.0) &
            df["IMPACT_LONGITUDE"].between(120.0, 135.0)
        ]
    except:
        return pd.DataFrame()

# ▶️ Streamlit 구성
st.set_page_config(page_title="☄️ 우주 낙하물체 모니터링", layout="wide")
st.title("☄️ 우주 낙하물체 모니터링 시스템")
st.markdown(f"🕒 업데이트 시각: `{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}`")

# 🎛️ 슬라이더, 리프레시, 디버그 토글
tip_hours = st.slider("TIP 분석 시간 범위", 24, 240, 72)
seoul_radius = st.slider("서울 기준 반경 (km)", 100, 3000, 800)
debug = st.checkbox("📊 원시 데이터 확인")
if st.button("🔁 데이터 새로고침"):
    st.experimental_rerun()

# 🔐 인증
session = get_authenticated_session()
if not session:
    st.stop()

# 📡 데이터 로딩
tip_df = fetch_tip_data(session, tip_hours)
decay_df = fetch_decay_data(session)

# 📍 서울 기준 TIP 메시지
st.subheader("📍 서울 기준 낙하물체 (TIP 기반)")
if not tip_df.empty:
    seoul_df = filter_tip_seoul(tip_df)
    if not seoul_df.empty:
        st.success(f"✅ 서울 기준 낙하물체 {len(seoul_df)}개 탐지됨")
        st.dataframe(seoul_df)
    else:
        st.info("📭 서울 인근 낙하 예측이 없습니다. 최근에는 낙하 이벤트가 보고되지 않았을 수 있어요.")
else:
    st.warning("📭 최근 TIP 메시지 수신 실패 또는 데이터 없음")

# 🌐 전세계 TIP 메시지
st.subheader("🌐 전세계 낙하물체 (TIP 메시지)")
if not tip_df.empty:
    st.dataframe(tip_df)
else:
    st.warning("🌐 전세계 TIP 메시지가 비어 있습니다.")

# 📅 Decay 기반 예측
st.subheader("📅 위성 낙하 예측 (180일, Decay 기반)")
if not decay_df.empty:
    st.success(f"✅ 예상 낙하물체 수: {len(decay_df)}")
    st.dataframe(decay_df)
else:
    st.info("📭 최근 180일간 위성 낙하 예측이 없습니다.")

# 🐞 디버깅 영역
if debug:
    st.subheader("🐞 원시 TIP 데이터 보기")
    st.write(tip_df.head())

    st.subheader("🐞 원시 Decay 데이터 보기")
    st.write(decay_df.head())
