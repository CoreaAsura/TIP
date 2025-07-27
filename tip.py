import streamlit as st
import requests
import pandas as pd

# 기본 설정
st.set_page_config(page_title="우주 낙하물체 경보 시스템", layout="wide")
st.title("🛰️ 전세계 우주물체 낙하 현황")

# Secrets에서 Space-Track 인증 정보 가져오기
id = st.secrets["space_track_id"]
pw = st.secrets["space_track_pw"]

# API 호출용 헤더 설정
def get_session():
    session = requests.Session()
    session.auth = (id, pw)
    return session

# TIP (Tracking and Impact Prediction) 데이터 요청 함수
@st.cache_data
def get_tip_data():
    url = "https://www.space-track.org/basicspacedata/query/class/tip/EPOCH/>now-168h/format/json"
    session = get_session()
    res = session.get(url)
    return res.json()

# Satellite Decay 데이터 요청 함수 (180일 내)
@st.cache_data
def get_decay_data():
    url = "https://www.space-track.org/basicspacedata/query/class/decay/EPOCH/>now-180d/orderby/DECAY_DATE%20desc/format/json"
    session = get_session()
    res = session.get(url)
    return res.json()

# 🚨 TIP 현황 섹션
with st.expander("📌 전세계 168시간 이내 낙하 예정 우주물체"):
    tip_data = get_tip_data()
    tip_count = len(tip_data)
    
    st.metric("총 TIP 분석 건수", f"{tip_count}건")
    
    if tip_count == 0:
        st.info("✅ 현재 168시간 이내 낙하 예정 우주물체는 없습니다.")
    else:
        df = pd.DataFrame([{
            "이름": item["OBJECT_NAME"],
            "국가": item["COUNTRY"],
            "낙하예정일": item["IMPACT_DATE"],
            "낙하지점": f'{item["LATITUDE"]}, {item["LONGITUDE"]}'
        } for item in tip_data])
        st.dataframe(df)

# 📆 180일 낙하예정 목록 섹션
with st.expander("📆 전세계 180일 내 낙하 예정 목록"):
    decay_data = get_decay_data()
    decay_items = [{
        "이름": item["OBJECT_NAME"],
        "국가": item["COUNTRY"],
        "낙하예정일": item["DECAY_DATE"]
    } for item in decay_data if item.get("DECAY_DATE")]

    st.metric("총 낙하 건수", f"{len(decay_items)}건")
    st.dataframe(pd.DataFrame(decay_items))

# 📍 미래 기능 힌트
st.caption("💡 다음 목표: 지도 위 낙하 위치 시각화, Slack 알림 연동, 위험도 분석 등!")

