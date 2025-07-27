import streamlit as st
import requests
import pandas as pd
import datetime

# 1. 세션 인증: POST 기반 로그인 처리
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
        st.error(f"🚨 Space-Track 로그인 실패: {res.status_code}")
        return None

# 2. TIP 메시지 가져오기 (168시간 이내)
def fetch_tip_data(session):
    url = "https://www.space-track.org/basicspacedata/query/class/tip/EPOCH>now-168h/format/json"
    res = session.get(url)
    if res.status_code == 200:
        return pd.DataFrame(res.json())
    else:
        st.error(f"❌ TIP 메시지 API 오류: {res.status_code}")
        return pd.DataFrame()

# 3. Satellite Decay 데이터 가져오기 (180일 이내)
def fetch_decay_data(session):
    today = datetime.datetime.utcnow()
    past_date = today - datetime.timedelta(days=180)
    url = f"https://www.space-track.org/basicspacedata/query/class/decay/EPOCH>{past_date.strftime('%Y-%m-%d')}/format/json"
    res = session.get(url)
    if res.status_code == 200:
        return pd.DataFrame(res.json())
    else:
        st.error(f"❌ Decay API 오류: {res.status_code}")
        return pd.DataFrame()

# 4. 서울 기준 낙하물체 필터링
def filter_seoul_objects(df):
    lat_min, lat_max = 36.5, 37.7
    lon_min, lon_max = 126.5, 127.5
    if "IMPACT_LATITUDE" in df.columns and "IMPACT_LONGITUDE" in df.columns:
        filtered = df[
            df["IMPACT_LATITUDE"].astype(float).between(lat_min, lat_max) &
            df["IMPACT_LONGITUDE"].astype(float).between(lon_min, lon_max)
        ]
        return filtered
    return pd.DataFrame()

# 5. Streamlit 앱 실행
st.set_page_config(page_title="우주 낙하물체 분석", page_icon="🛰️")
st.title("🛰️ 우주 낙하물체 분석 시스템")
st.caption("TIP 메시지 기반 서울 및 전세계 분석 / Satellite Decay 기반 180일 예측")

# 인증 세션 연결
session = get_authenticated_session()

if session:
    tip_df = fetch_tip_data(session)
    decay_df = fetch_decay_data(session)

    # TIP 메시지 데이터 출력
    if not tip_df.empty:
        st.subheader("📍 서울 기준 낙하물체 (TIP 메시지)")
        seoul_df = filter_seoul_objects(tip_df)
        st.dataframe(seoul_df)

        st.subheader("🌐 전세계 낙하물체 (TIP 메시지 전체)")
        st.dataframe(tip_df)

    # Satellite Decay 데이터 출력
    if not decay_df.empty:
        st.subheader("📅 180일 이내 예상 낙하물체 (Satellite Decay)")
        st.dataframe(decay_df)
