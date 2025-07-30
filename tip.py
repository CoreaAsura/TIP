import streamlit as st
import requests
from sgp4.api import Satrec, jday
from datetime import datetime, timedelta
import math
import pandas as pd
from pytz import timezone

# 서울 기준 좌표
SEOUL_LAT, SEOUL_LON = 37.5665, 126.9780

# 📌 UI 설정
st.set_page_config(page_title="우주낙하물체 현황 for MSSB", layout="wide")
st.title("☄️ 우주낙하물체 현황 for MSSB")

kst_now = datetime.utcnow().astimezone(timezone("Asia/Seoul"))
st.markdown(f"🕒 최근 업데이트 (KST): `{kst_now.strftime('%Y-%m-%d %H:%M:%S')}`")

# 🎛️ 사용자 설정
hours = st.slider("TIP 분석 시간 범위 (시간)", 24, 168, 72)
radius_km = st.slider("서울 기준 분석 반경 (km)", 500, 5000, 3000)

# 📡 TLE 데이터 불러오기 (CelesTrak)
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

tle_sets = fetch_all_tle()
st.markdown(f"🛰️ 분석 대상 우주물체 수: `{len(tle_sets)}` 개")

# 거리 계산 함수 (Haversine)
def haversine(lat1, lon1, lat2, lon2):
    R = 6371
    dLat = math.radians(lat2 - lat1)
    dLon = math.radians(lon2 - lon1)
    a = math.sin(dLat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dLon/2)**2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

# 궤도 예측 및 분석 함수
def predict_positions(name, line1, line2, duration_hr):
    sat = Satrec.twoline2rv(line1, line2)
    positions = []
    now = datetime.utcnow()
    for i in range(0, duration_hr * 60, 30):  # 30분 간격
        dt = now + timedelta(minutes=i)
        jd, fr = jday(dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second)
        e, r, v = sat.sgp4(jd, fr)
        if e == 0:
            x, y, z = r
            altitude = math.sqrt(x**2 + y**2 + z**2) - 6371
            lon = math.degrees(math.atan2(y, x))
            hyp = math.sqrt(x**2 + y**2)
            lat = math.degrees(math.atan2(z, hyp))
            positions.append((dt, altitude, lat, lon))
    return positions

# 분석 수행
seoul_objects = []
decaying_objects = []
for name, line1, line2 in tle_sets:
    try:
        sat = Satrec.twoline2rv(line1, line2)
        positions = predict_positions(name, line1, line2, hours)

        # 서울 기준 반경 이내 + 고도 조건
        for dt, alt, lat, lon in positions:
            dist = haversine(SEOUL_LAT, SEOUL_LON, lat, lon)
            if dist <= radius_km and alt < 200:
                seoul_objects.append({
                    "NORAD ID": line1.split()[1],
                    "위성명칭": name,
                    "예상 낙하 위도": round(lat, 2),
                    "예상 낙하 경도": round(lon, 2),
                    "예상 낙하 시간": dt.strftime('%Y-%m-%d %H:%M:%S UTC')
                })
                break

        # decay term 기반 낙하 예측 (line1 → column 53~61)
        decay_term_str = line1[53:61].strip()
        if decay_term_str and float(decay_term_str) >= 0.0001:
            decaying_objects.append(name)

    except:
        continue

# 📍 서울 기준 낙하물체 섹션
st.subheader("📍 서울 기준 지정범위 내 예상 우주낙하물체")
if seoul_objects:
    seoul_df = pd.DataFrame(seoul_objects)[["NORAD ID", "위성명칭", "예상 낙하 위도", "예상 낙하 경도", "예상 낙하 시간"]]
    st.dataframe(seoul_df, use_container_width=True)
    csv = seoul_df.to_csv(index=False).encode('utf-8')
    st.download_button("📂 낙하예상 우주물체 CSV 다운로드", data=csv, file_name="seoul_decay_objects.csv", mime='text/csv')
else:
    st.info("✅ 해당 반경 내 낙하예상 물체가 없습니다.")

# 📅 180일 이내 궤도 붕괴 섹션
st.subheader("📅 180일 이내 예상 우주 낙하물체")
if decaying_objects:
    for name in decaying_objects:
        st.markdown(f"- 🛰️ **{name}** | TLE decay term ≥ 0.0001")
else:
    st.info("📭 현재 180일 이내 궤도 붕괴 예상 우주물체가 없습니다.")
