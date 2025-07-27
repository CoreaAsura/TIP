import streamlit as st
import requests
from datetime import datetime
from geopy.distance import geodesic

# 🛰️ TIP 분석 시간 설정
def fetch_tip_data(hours):
    try:
        response = requests.get(f"https://space-track.org/api/tip?hours={hours}")
        if response.ok:
            return response.json()
    except:
        return None

# 🛰️ Satellite Decay 데이터 설정
def fetch_decay_data():
    try:
        response = requests.get("https://space-track.org/api/decay")
        if response.ok:
            return response.json()
    except:
        return None

# ✅ 낙하예상 기간 필터링
def analyze_decay_risk(decay_date_str):
    try:
        decay_date = datetime.strptime(decay_date_str, "%Y-%m-%d")
        delta_days = (decay_date - datetime.now()).days
        return 0 <= delta_days <= 180
    except:
        return False

# 📍 서울 기준 위치 필터링
def filter_by_location(data_list, center_coords, radius_km):
    filtered = []
    for obj in data_list:
        try:
            lat = float(obj.get('latitude', 0))
            lon = float(obj.get('longitude', 0))
            obj_coords = (lat, lon)
            if geodesic(center_coords, obj_coords).km <= radius_km:
                filtered.append(obj)
        except:
            continue
    return filtered

# 🛠️ 페이지 설정
st.set_page_config(page_title="우주낙하물체 현황 for MSSB", layout="wide")
st.title("🌌 우주낙하물체 현황 for MSSB")
st.caption("🌍 서울 기준 낙하물체, TIP 분석, 전세계 우주물체 정보를 통합 제공합니다.")

# 🕒 최근 업데이트 시각 표시
st.markdown(f"🕒 최근 업데이트: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

# 🎚️ TIP 분석 시간 & 서울 기준 반경 슬라이더 (업데이트 시각 아래로 위치)
hours = st.slider("TIP 메시지 분석 시간 범위 (시간 단위)", 24, 168, 72)
radius_km = st.slider("서울 기준 반경 (km)", 100, 3000, 800)

# 🔗 데이터 수신
tip_data = fetch_tip_data(hours)
decay_data = fetch_decay_data()

if not tip_data or not isinstance(tip_data, list):
    st.error("❌ TIP 메시지를 불러오지 못했습니다.")
else:
    st.success(f"✅ TIP 메시지 {len(tip_data)}건 수신됨")

if not decay_data or not isinstance(decay_data, list):
    st.error("❌ Satellite Decay 데이터를 불러오지 못했습니다.")
else:
    st.success(f"✅ Satellite Decay 데이터 {len(decay_data)}건 수신됨")

# 📌 서울 기준 낙하예상 물체 출력
st.subheader(f"📍 서울 기준 {radius_km}km 이내 우주 낙하물체")
seoul_coords = (37.5665, 126.9780)
nearby_objects = filter_by_location(decay_data, seoul_coords, radius_km)
if nearby_objects:
    for obj in nearby_objects:
        st.markdown(f"- **NORAD ID:** {obj.get('norad_cat_id', 'N/A')} | **이름:** {obj.get('satname', 'N/A')}  
            ➤ 좌표: ({obj.get('latitude', '?')}, {obj.get('longitude', '?')}) | 방향: {obj.get('direction', 'N/A')}")
else:
    st.info("❗ 해당 범위 내 낙하예상 물체가 없습니다.")

# 🌐 전세계 낙하 우주물체 현황
st.subheader("🌐 전세계 우주 낙하물체 현황")
for obj in decay_data[:20]:
    st.markdown(f"- **{obj.get('satname')}** | 국가: {obj.get('country', 'N/A')} | 예상 낙하: {obj.get('decay_date')}")

# 📅 180일 이내 예상 우주낙하물체
st.subheader("📅 180일 이내 예상 우주낙하물체")
for obj in decay_data:
    if analyze_decay_risk(obj.get('decay_date', '')):
        st.markdown(f"✅ **{obj['satname']}** | 예상 낙하일: {obj['decay_date']}")

st.markdown("---")
st.caption("📡 데이터 출처: space-track.org | 분석 기반: TIP 메시지 및 Satellite Decay API")
