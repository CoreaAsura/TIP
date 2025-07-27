import streamlit as st
import requests
import pandas as pd
import datetime

# ▶️ 세션 기반 로그인 인증
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

# ▶️ TIP 메시지 요청 (7일간)
def fetch_tip_data(session):
    url = "https://www.space-track.org/basicspacedata/query/class/tip/EPOCH>now-168h/format/json"
    res = session.get(url)
    if res.status_code == 200:
        return pd.DataFrame(res.json())
    else:
        st.error(f"❌ TIP 메시지 API 오류: {res.status_code}")
        st.write(res.text)
        return pd.DataFrame()

# ▶️ Satellite Decay 요청 (180일 이내)
def fetch_decay_data(session):
    past_date = (datetime.datetime.utcnow() - datetime.timedelta(days=180)).strftime('%Y-%m-%d')
    url = f"https://www.space-track.org/basicspacedata/query/class/decay/EPOCH>{past_date}/format/json"
    res = session.get(url)
    if res.status_code == 200:
        return pd.DataFrame(res.json())
    else:
        st.error(f"❌ Decay API 오류: {res.status_code}")
        st.write(res.text)
        return pd.DataFrame()

# ▶️ 서울 기준 낙하물체 필터링
def filter_seoul_objects(df):
    lat_min, lat_max = 36.5, 37.7
    lon_min, lon_max = 126.5, 127.5
    try:
        df["IMPACT_LATITUDE"] = df["IMPACT_LATITUDE"].astype(float)
        df["IMPACT_LONGITUDE"] = df["IMPACT_LONGITUDE"].astype(float)
        return df[
            df["IMPACT_LATITUDE"].between(lat_min, lat_max) &
            df["IMPACT_LONGITUDE"].between(lon_min, lon_max)
        ]
    except:
        st.warning("📍 서울 필터링에 필요한 좌표 정보가 없습니다.")
        return pd.DataFrame()

# ▶️ Streamlit 앱 구성
st.set_page_config(page_title="우주 낙하물체 분석", page_icon="🛰️")
st.title("🛰️ 우주 낙하물체 분석 시스템")
st.caption("서울 기준 TIP 낙하물체 + 전세계 TIP 메시지 + Satellite Decay 예측")

session = get_authenticated_session()
if session:
    # TIP 메시지
    tip_df = fetch_tip_data(session)
    if not tip_df.empty:
        st.subheader("📍 서울 기준 TIP 낙하물체")
        st.dataframe(filter_seoul_objects(tip_df))

        st.subheader("🌐 전세계 TIP 메시지")
        st.dataframe(tip_df)

    # Decay 분석
    decay_df = fetch_decay_data(session)
    if not decay_df.empty:
        st.subheader("📅 180일 이내 예상 낙하물체 (Satellite Decay)")
        st.dataframe(decay_df)
