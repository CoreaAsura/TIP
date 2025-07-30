import streamlit as st
import requests
from sgp4.api import Satrec, jday
from datetime import datetime, timedelta
import math

# 서울 위치
SEOUL_LAT, SEOUL_LON = 37.5665, 126.9780

# 페이지 설정
st.set_page_config(page_title="우주낙하물체 현황 for MSSB", layout="wide")
st.title("🌌 우주낙하물체 현황 for MSSB")
st.markdown(f"🕒 최근 업데이트: `{datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}`")

# 사용자 선택 슬라이더
hours = st.slider("TIP 분석 시간 범위 (시간)", 24, 168, 72)
radius_km = 3000  # 서울 기준 반경 고정

# TLE 목록 불러오기 (전체 위성)
@st.cache_data(ttl=3600)
def fetch_all_tle():
    url = "https://celestrak.org/NORAD/elements/gp.php?GROUP=active&FORMAT=TLE"
    res = requests.get(url)
    lines = res.text.strip().split('\n')
    tle_sets = []
    for i in range(0, len(lines), 3):
        name = lines[i].strip()
        line1 = lines[i+1].strip()
        line2 = lines[i+2].strip()
        tle_sets.append((name, line1, line2))
    return tle_sets

# 궤도 예측 함수
def predict_positions(name, line1, line2, duration_hr):
    sat = Satrec.twoline2rv(line1, line2)
    positions = []
    now = datetime.utcnow()
    for i in range(0, duration_hr * 60, 30):  # 30분 간격 예측
        dt = now + timedelta(minutes=i)
        jd, fr = jday(dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second)
        e, r, v = sat.sgp4(jd, fr)
        if e == 0:
            x, y, z = r
            altitude = math.sqrt(x**2 + y**2 + z**2) - 6371
            # 경도/위도 추정 간이 계산
            lon = math.degrees(math.atan2(y, x))
            hyp = math.sqrt(x**2 + y**2)
            lat = math.degrees(math.atan2(z, hyp))
            positions.append((dt, altitude, lat, lon))
    return positions

# 거리 계산
def haversine(lat1, lon1, lat2, lon2):
    R = 6371
    dLat = math.radians(lat2 - lat1)
    dLon = math.radians(lon2 - lon1)
    a = math.sin(dLat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dLon/2)**2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

# 데이터 분석
tle_sets = fetch_all_tle()
seoul_objects = []
decaying_objects = []

for name, line1, line2 in tle_sets:
    try:
        sat = Satrec.twoline2rv(line1, line2)
        positions = predict_positions(name, line1, line2, hours)
        for dt, alt, lat, lon in positions:
            dist = haversine(SEOUL_LAT, SEOUL_LON, lat, lon)
            if dist <= radius_km and alt < 200:
                seoul_objects.append((name, lat, lon, alt, dist))
                break  # 중복 피하기
        # 180일 내 궤도 붕괴 판단: TLE line1의 epoch date 활용
        epoch_year = int(line1[18:20])
        epoch_day = float(line1[20:32])
        year_full = 2000 + epoch_year if epoch_year < 57 else 1900 + epoch_year
        epoch_dt = datetime(year_full, 1, 1) + timedelta(days=epoch_day - 1)
        age_days = (datetime.utcnow() - epoch_dt).days
        if age_days >= 0 and age_days <= 180 and sat.no_kozai > 15:  # 높은 궤도 붕괴 가능성
            decaying_objects.append((name, round(age_days)))
    except:
        continue

# 출력
st.subheader(f"📍 서울 반경 {radius_km}km 이내 낙하위험 우주물체")
if seoul_objects:
    for obj in seoul_objects:
        st.markdown(f"- **{obj[0]}** ➤ 좌표: ({obj[1]:.2f}, {obj[2]:.2f}) | 고도: {obj[3]:.1f}km | 서울까지 거리: {obj[4]:.0f}km")
else:
    st.info("❗ 해당 범위 내 낙하위험 물체가 발견되지 않았습니다.")

st.subheader("📅 180일 이내 궤도 붕괴 예상 우주물체")
if decaying_objects:
    for name, age in decaying_objects:
        st.markdown(f"- **{name}** | TLE 기준으로 약 {age}일 경과 → 낙하 가능성 있음")
else:
    st.info("📭 현재 낙하예상 물체가 없습니다.")
