import streamlit as st
import requests
import pandas as pd
import datetime

# 1. Space-Track 계정 인증 정보 (secrets에서 불러오기)
SPACE_ID = st.secrets["space_track_id"]
SPACE_PW = st.secrets["space_track_pw"]

# 2. 세션 생성 후 로그인
def get_authenticated_session():
    session = requests.Session()
    session.auth = (SPACE_ID, SPACE_PW)
    return session

# 3. TIP 메시지 데이터 가져오기 (168시간 이내 = 7일)
def fetch_tip_data(session):
    url = "https://www.space-track.org/basicspacedata/query/class/tip/EPOCH>now-168h/format/json"
    response = session.get(url)
    if response.status_code == 200:
        return pd.DataFrame(response.json())
    else:
        st.error(f"TIP 메시지 API 오류: {response.status_code}")
        return pd.DataFrame()

# 4. Satellite Decay 데이터 가져오기 (180일 이내)
def fetch_decay_data(session):
    today = datetime.datetime.utcnow()
    past_date = today - datetime.timedelta(days=180)
    url = f"https://www.space-track.org/basicspacedata/query/class/decay/EPOCH>{past_date.strftime('%Y-%m-%d')}/format/json"
    response = session.get(url)
    if response.status_code == 200:
        return pd.DataFrame(response.json())
    else:
        st.error(f"Satellite Decay API 오류: {response.status_code}")
        return pd.DataFrame()

# 5. 서울 기준 낙하물체 필터링 함수 (TIP)
def filter_seoul_objects(df):
    # 서울 위치 기준 (대략적 범위)
    lat_min, lat_max = 36.5, 37.7
    lon_min, lon_max = 126.5, 127.5
    if "IMPACT_LATITUDE" in df.columns and "IMPACT_LONGITUDE" in df.columns:
        filtered = df[(df["IMPACT_LATITUDE"].astype(float).between(lat_min, lat_max)) &
                      (df["IMPACT_LONGITUDE"].astype(float).between(lon_min, lon_max))]
        return filtered
    return pd.DataFrame()

# 6. Streamlit 앱 시작
st.title("🛰️ 우주 낙하물체 분석 시스템")
st.caption("서울 기준 낙하물체 / 전세계 TIP 메시지 / 180일 예상 낙하 분석")

# 인증 세션 생성
session = get_authenticated_session()

# TIP 메시지 불러오기
tip_df = fetch_tip_data(session)
if not tip_df.empty:
    st.subheader("📍 서울 기준 낙하물체 (TIP 메시지)")
    seoul_df = filter_seoul_objects(tip_df)
    st.dataframe(seoul_df)

    st.subheader("🌐 전세계 TIP 메시지 전체")
    st.dataframe(tip_df)

# Satellite Decay 불러오기
decay_df = fetch_decay_data(session)
if not decay_df.empty:
    st.subheader("📅 180일 이내 예상 낙하물체 (Satellite Decay)")
    st.dataframe(decay_df)
