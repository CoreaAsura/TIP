import streamlit as st
import requests
import pandas as pd
import datetime

# ▶️ Space-Track 인증: 세션 기반 로그인
def get_authenticated_session():
    login_url = "https://www.space-track.org/ajaxauth/login"
    payload = {
        "identity": st.secrets["space_track_id"],
        "password": st.secrets["space_track_pw"]
    }
    session = requests.Session()
    res = session.post(login_url, data=payload)

    if res.status_code == 200:
        return session
    else:
        st.error(f"🚨 로그인 실패: {res.status_code}")
        st.write(res.text)
        return None

# ▶️ TIP 메시지 가져오기 (최근 168시간 기준)
def fetch_tip_data(session, hours):
    url = f"https://www.space-track.org/basicspacedata/query/class/tip/EPOCH>now-{hours}h/format/json"
    res = session.get(url)
    if res.status_code == 200:
        return pd.DataFrame(res.json())
    else:
        st.error(f"❌ TIP 메시지 오류: {res.status_code}")
        st.write(res.text)
        return pd.DataFrame()

# ▶️ Satellite Decay 데이터 가져오기 (최근 180일 기준)
def fetch_decay_data(session):
    past = (datetime.datetime.utcnow() - datetime.timedelta(days=180)).strftime('%Y-%m-%d')
    url = f"https://www.space-track.org/basicspacedata/query/class/decay/EPOCH>{past}/format/json"
    res = session.get(url)
    if res.status_code == 200:
        return pd.DataFrame(res.json())
    else:
        st.error(f"❌ Decay API 오류: {res.status_code}")
        st.write(res.text)
        return pd.DataFrame()

# ▶️ 서울 기준 낙하물체 필터링 (TIP 기반)
def filter_tip_seoul(df):
    lat_min, lat_max = 30.0, 40.0
    lon_min, lon_max = 120.0, 135.0
    try:
        df["IMPACT_LATITUDE"] = df["IMPACT_LATITUDE"].astype(float)
        df["IMPACT_LONGITUDE"] = df["IMPACT_LONGITUDE"].astype(float)
        filtered = df[
            df["IMPACT_LATITUDE"].between(lat_min, lat_max) &
            df["IMPACT_LONGITUDE"].between(lon_min, lon_max)
        ]
        return filtered
    except:
        return pd.DataFrame()

# ▶️ Streamlit 앱 구성
st.set_page_config(page_title="우주낙하물체 현황 for MSSB", layout="wide")
st.title("🌌 우주낙하물체 현황 for MSSB")
st.markdown(f"🕒 최근 업데이트: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

# 🎛️ 분석 범위 슬라이더
tip_hours = st.slider("TIP 메시지 분석 시간 범위 (시간)", 24, 168, 72)
seoul_radius = st.slider("서울 기준 반경 (km)", 100, 3000, 800)

# 🔐 인증 후 세션 확보
session = get_authenticated_session()
if not session:
    st.stop()

# 📡 데이터 불러오기
tip_df = fetch_tip_data(session, tip_hours)
decay_df = fetch_decay_data(session)

# 📍 서울 기준 낙하물체 (TIP 기반)
st.subheader(f"📍 서울 기준 {seoul_radius}km 이내 우주 낙하물체 (TIP 메시지 기반)")
if not tip_df.empty:
    seoul_df = filter_tip_seoul(tip_df)
    st.dataframe(seoul_df)
else:
    st.info("TIP 메시지를 불러오지 못했거나 데이터가 없습니다.")

# 🌐 전세계 우주 낙하물체 (TIP 메시지 기반)
st.subheader("🌐 전세계 우주 낙하물체 (TIP 메시지 기반)")
if not tip_df.empty:
    st.dataframe(tip_df)
else:
    st.warning("전세계 TIP 데이터가 없습니다.")

# 📅 180일 이내 예상 우주낙하물체 (Satellite Decay 기반)
st.subheader("📅 180일 이내 예상 우주낙하물체 (Satellite Decay 기반)")
if not decay_df.empty:
    st.dataframe(decay_df)
else:
    st.warning("Satellite Decay 데이터를 불러오지 못했습니다.")
