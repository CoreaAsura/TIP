import streamlit as st
import requests
from datetime import datetime
from geopy.distance import geodesic

# ✅ 분석 시간 설정
hours = st.slider("TIP 분석 시간 범위 (시간 단위)", 1, 72, 24)

# 🛰️ 위성 낙하 위험 분석 함수
def analyze_decay_risk(decay_date_str):
    try:
        decay_date = datetime.strptime(decay_date_str, "%Y-%m-%d")
        delta_days = (decay_date - datetime.now()).days
        return 0 <= delta_days <= 180
    except:
        return False

# 📍 반경 필터링 함수
def filter_by_location(data_list, center_coords, radius_km):
    filtered = []
    for obj in data_list:
        try:
            obj_coords = (float(obj['latitude']), float(obj['longitude']))
            if geodesic(center_coords, obj_coords).km <= radius_km:
                filtered.append(obj)
        except:
            continue
    return filtered

# 🔗 TIP 메시지 가져오기
def fetch_tip_data(hours):
    try:
        response = requests.get(f"https://space-track.org/api/tip?hours={hours}")
        if response.ok:
            return response.json()
    except:
        return None

# 🔗 Satellite Decay 데이터 가져오기
def fetch_decay_data():
    try:
        response = requests.get("https://space-track.org/api/decay")
        if response.ok:
            return response.json()
    except:
        return None

# 🛠️ 페이지 설정
st.set_page_config(page_title="우주 낙하물체 추적기", layout="wide")
st.title("🌍 서울 기준 우주 낙하물체 추적기")
st.caption("💫 전세계 우주 낙하물체 및 TIP 메시지를 실시간으로 확인합니다")

# ✅ API 수신 확인
st.subheader("데이터 수신 상태")

tip_data = fetch_tip_data(hours)
if not tip_data or not isinstance(tip_data, list):
    st.error("❌ TIP 메시지를 불러오지 못했습니다.")
else:
    st.success(f"✅ TIP 메시지 {len(tip_data)}건 수신됨")

decay_data = fetch_decay_data()
if not decay_data or not isinstance(decay_data, list):
    st.error("❌ Satellite Decay 데이터를 불러오지 못했습니다.")
else:
    st.success(f"✅ Satellite Decay 데이터 {len(decay_data)}건 수신됨")

# 🕒 업데이트 시각
st.markdown(f"🕒 최근 업데이트: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

# 📍 서울 기준 반경 슬라이더 (아래 위치)
radius_km = st.slider("서울 기준 반경 (km)", 100, 3000, 800)

# 🛰️ 서울 기준 낙하물체 목록
st.subheader(f"📌 서울 기준 {radius_km}km 이내 우주 낙하물체")
seoul_coords = (37.5665, 126.9780)
nearby_objects = filter_by_location(decay_data, seoul_coords, radius_km)
if nearby_objects:
    for obj in nearby_objects:
        st.markdown(f"- **{obj['satname']}** | 예상 낙하 시점: {obj['decay_date']}")
else:
    st.info("❗ 해당 범위 내 낙하예상 물체가 없습니다")

# 🌐 전세계 우주 낙하물체
st.subheader("🌐 전세계 우주 낙하물체")
for obj in decay_data[:20]:
    st.markdown(f"- **{obj['satname']}** | 국가: {obj.get('country', 'N/A')} | 낙하예상: {obj['decay_date']}")

# 📅 180일 이내 우주낙하물체
st.subheader("📅 180일 이내 예상 우주낙하물체")
for obj in decay_data:
    if analyze_decay_risk(obj['decay_date']):
        st.markdown(f"✅ **{obj['satname']}** | 예상 낙하: {obj['decay_date']}")

st.markdown("---")
st.caption("💡 데이터 출처: space-track.org | 분석 도구: TIP, Satellite Decay API")
