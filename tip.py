import streamlit as st
import requests
import datetime
import pytz
from math import radians, cos, sin, sqrt, atan2

# 📍 설정값
KST = pytz.timezone('Asia/Seoul')
SEOUL_LAT, SEOUL_LON = 37.5665, 126.9780
TIP_URL = "https://www.space-track.org/basicspacedata/query/TIP"
SATDECAY_URL = "https://www.space-track.org/basicspacedata/query/SATDECAY"

def get_current_kst():
    return datetime.datetime.now(KST).strftime('%Y-%m-%d %H:%M:%S')

def fetch_tip_data(hours):
    assert 24 <= hours <= 168, "시간 범위는 24~168시간 사이여야 합니다."
    params = {"hours": hours, "format": "json"}
    response = requests.get(TIP_URL, params=params)
    return response.json() if response.ok else []

def fetch_decay_data(days=180):
    params = {"days": days, "format": "json"}
    response = requests.get(SATDECAY_URL, params=params)
    return response.json() if response.ok else []

def haversine(lat1, lon1, lat2, lon2):
    R = 6371
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat/2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon/2)**2
    return R * 2 * atan2(sqrt(a), sqrt(1 - a))

def filter_near_seoul(data, radius_km=3000):
    filtered = []
    for item in data:
        lat = item.get("LATITUDE")
        lon = item.get("LONGITUDE")
        if lat and lon:
            distance = haversine(SEOUL_LAT, SEOUL_LON, float(lat), float(lon))
            if distance <= radius_km:
                filtered.append(item)
    return filtered

# 🖥️ Streamlit 렌더링 시작
st.set_page_config(page_title="우주낙하물체 현황 for MSSB", layout="wide")
st.title("🛰️ 우주낙하물체 현황 for MSSB")
st.caption(f"업데이트 시각: {get_current_kst()}")

# 🎛️ 사용자 입력 받기
hours = st.sidebar.slider("TIP 분석 시간 범위 (단위: 시간)", min_value=24, max_value=168, value=72)
radius = st.sidebar.slider("서울 기준 반경 (km)", min_value=500, max_value=5000, value=3000)

# 📡 데이터 불러오기
tip_data = fetch_tip_data(hours)
decay_data = fetch_decay_data()
near_seoul = filter_near_seoul(tip_data, radius_km=radius)

# 📍 서울 기준 3000km 이내 물체 표시
st.subheader(f"🎯 서울 기준 {radius}km 이내 낙하예정 물체")
for item in near_seoul:
    st.markdown(f"""
**🔖 명칭**: {item.get('OBJECT_NAME', '이름없음')}  
**🛰️ NORAD ID**: {item.get('NORAD_CAT_ID', '알 수 없음')}  
**📍 예상좌표**: {item.get('LATITUDE', '?')}, {item.get('LONGITUDE', '?')}  
**⏰ 예상시간**: {item.get('IMPACT_DATE', '미정')}  
**🧭 비행방향**: {item.get('IMPACT_DIRECTION', '미정')}
---
""")

# 🌍 전 세계 TIP 일부 표시
st.subheader("🌍 전 세계 낙하예상 우주물체 (샘플)")
world_sample = [
    {
        "명칭": item.get("OBJECT_NAME", "이름없음"),
        "좌표": f"{item.get('LATITUDE', '?')}, {item.get('LONGITUDE', '?')}"
    }
    for item in tip_data[:5]
]
st.table(world_sample)

# ☄️ 180일 내 낙하 Satellite
st.subheader("☄️ 180일 내 낙하예정 Satellite 목록")
decay_sample = [
    {
        "명칭": item.get("OBJECT_NAME", "이름없음"),
        "예정일": item.get("DECAY_DATE", "미정")
    }
    for item in decay_data[:5]
]
st.table(decay_sample)
