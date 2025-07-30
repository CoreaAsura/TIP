import streamlit as st
import requests
import pandas as pd
import datetime

# ▶️ 인증 및 세션 생성 (에러 메시지 출력 추가)
def get_authenticated_session():
    login_url = "https://www.space-track.org/ajaxauth/login"
    payload = {
        "identity": st.secrets["space_track_id"],
        "password": st.secrets["space_track_pw"]
    }
    session = requests.Session()
    res = session.post(login_url, data=payload)

    if res.status_code == 200:
        st.success("🔐 Space-Track 인증 성공")
        return session
    else:
        st.error(f"🚨 Space-Track 로그인 실패: {res.status_code}")
        st.write(res.text)
        return None

# ▶️ TIP 메시지 가져오기
def fetch_tip_data(session, hours):
    try:
        url = f"https://www.space-track.org/basicspacedata/query/class/tip/EPOCH>now-{hours}h/format/json"
        res = session.get(url)
        if res.status_code == 200:
            data = res.json()
            st.write(f"✅ TIP 응답 성공, 수신 데이터 행 수: {len(data)}")
            return pd.DataFrame(data)
        else:
            st.error(f"❌ TIP API 오류: {res.status_code}")
            st.write(res.text)
            return pd.DataFrame()
    except Exception as e:
        st.error(f"❌ TIP 데이터 오류: {str(e)}")
        return pd.DataFrame()

# ▶️ Satellite Decay 메시지 가져오기
def fetch_decay_data(session):
    try:
        past = (datetime.datetime.utcnow() - datetime.timedelta(days=180)).strftime('%Y-%m-%d')
        url = f"https://www.space-track.org/basicspacedata/query/class/decay/EPOCH>{past}/format/json"
        res = session.get(url)
        if res.status_code == 200:
            data = res.json()
            st.write(f"✅ Decay 응답 성공, 수신 데이터 행 수: {len(data)}")
            return pd.DataFrame(data)
        else:
            st.error(f"❌ Decay API 오류: {res.status_code}")
            st.write(res.text)
            return pd.DataFrame()
    except Exception as e:
        st.error(f"❌ Decay 데이터 오류: {str(e)}")
        return pd.DataFrame()

# ▶️ 서울 기준 낙하물체 필터링
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
        st.write(f"📍 서울 기준 필터링 결과: {len(filtered)}개")
        return filtered
    except Exception as e:
        st.warning(f"서울 기준 필터링 오류: {str(e)}")
        return pd.DataFrame()

# ▶️ Streamlit 앱 구성
st.set_page_config(page_title="우주 낙하물체 모니터링", layout="wide")
st.title("☄️ 우주 낙하물체 모니터링 시스템")
st.markdown(f"🕒 마지막 업데이트 시각: `{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}`")

# 🎛️ 사용자 입력 슬라이더 (범위 확장)
tip_hours = st.slider("TIP 메시지 분석 시간 (단위: 시간)", 24, 240, 72)
seoul_radius = st.slider("서울 기준 반경 (단위: km)", 100, 3000, 800)

# 🔐 인증 세션 확보
session = get_authenticated_session()
if not session:
    st.stop()

# 📡 데이터 요청
tip_df = fetch_tip_data(session, tip_hours)
decay_df = fetch_decay_data(session)

# 📍 서울 기준 TIP 메시지 필터링 결과
st.subheader("📍 서울 기준 낙하물체 (TIP 기반)")
if not tip_df.empty:
    seoul_df = filter_tip_seoul(tip_df)
    if not seoul_df.empty:
        st.dataframe(seoul_df)
    else:
        st.info("📭 서울 인근 낙하 예측 데이터가 없습니다.")
else:
    st.warning("📭 최근 TIP 메시지가 없거나 수신 실패했습니다.")

# 🌐 전세계 TIP 메시지
st.subheader("🌐 전체 TIP 메시지 기반 낙하물체 현황")
if not tip_df.empty:
    st.dataframe(tip_df)
else:
    st.warning("🌐 전세계 TIP 데이터가 없습니다.")

# 📅 Satellite Decay 예측 (180일)
st.subheader("📅 180일 이내 위성 낙하 예측 (Decay 기반)")
if not decay_df.empty:
    st.dataframe(decay_df)
else:
    st.info("📭 최근 180일간 낙하 예측 데이터가 없습니다.")
