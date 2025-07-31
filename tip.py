import streamlit as st
import requests
import math
from datetime import datetime, timedelta
import pandas as pd
from sgp4.api import Satrec, jday
from pytz import timezone
import os

# 📍 서울 기준 좌표
SEOUL_LAT, SEOUL_LON = 37.5665, 126.9780

# 🕒 한국 시간
kst_now = datetime.utcnow().astimezone(timezone("Asia/Seoul"))
st.set_page_config(page_title="우주낙하물체 현황", layout="wide")
st.title("☄️ 우주낙하물체 현황 for MSSB")
st.markdown(f"🕒 최근 업데이트 (KST): `{kst_now.strftime('%Y-%m-%d %H:%M:%S')}`")

# 📦 TLE 경로
TLE_FILE = "active.txt"
TLE_URL = "https://celestrak.org/NORAD/elements/active.txt"

# 📥 TLE 다운로드 버튼
if st.button("📥 전체 TLE 파일 다운로드"):
    try:
        res = requests.get(TLE_URL, timeout=10)
        with open(TLE_FILE, "w", encoding="utf-8") as f:
            f.write(res.text)
        st.success("✅ TLE 파일 다운로드 및 저장 완료")
    except Exception as e:
        st.error(f"❌ 다운로드 오류: {e}")

# 📂 TLE 불러오기 버튼
if st.button("📂 저장된 TLE 파일 불러오기 및 분석 시작"):
    if not os.path.exists(TLE_FILE):
        st.error("⚠️ 저장된 TLE 파일이 없습니다. 먼저 다운로드해주세요.")
    else:
        with open(TLE_FILE, "r", encoding="utf-8") as f:
            lines = f.readlines()

        tle_sets = []
        for i in range(0, len(lines), 3):
            if i + 2 < len(lines):
                name = lines[i].strip()
                line1 = lines[i+1].strip()
                line2 = lines[i+2].strip()
                tle_sets.append((name, line1, line2))

        st.markdown(f"🛰️ 분석 대상 우주물체 수: `{len(tle_sets)}` 개")

        # 반경 슬라이더
        radius_km = st.slider("서울 기준 분석 반경 (km)", 500, 5000, 3000)
        analysis_hours = st.slider("분석 시간 범위 (시간)", 24, 168, 72)

        # 도구 함수
        def haversine(lat1, lon1, lat2, lon2):
            R = 6371
            dLat = math.radians(lat2 - lat1)
            dLon = math.radians(lon2 - lon1)
            a = math.sin(dLat/2)**2 + math.cos(math.radians(lat1))*math.cos(math.radians(lat2))*math.sin(dLon/2)**2
            return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

        def bearing(lat1, lon1, lat2, lon2):
            lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
            dLon = lon2 - lon1
            x = math.sin(dLon) * math.cos(lat2)
            y = math.cos(lat1)*math.sin(lat2) - math.sin(lat1)*math.cos(lat2)*math.cos(dLon)
            return round((math.degrees(math.atan2(x, y)) + 360) % 360, 1)

        def predict_positions(line1, line2, hours):
            sat = Satrec.twoline2rv(line1, line2)
            positions = []
            now = datetime.utcnow()
            for i in range(0, hours * 60, 30):
                dt = now + timedelta(minutes=i)
                jd, fr = jday(dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second)
                e, r, v = sat.sgp4(jd, fr)
                if e == 0:
                    x, y, z = r
                    alt = math.sqrt(x**2 + y**2 + z**2) - 6371
                    lon = math.degrees(math.atan2(y, x))
                    hyp = math.sqrt(x**2 + y**2)
                    lat = math.degrees(math.atan2(z, hyp))
                    positions.append((dt, alt, lat, lon))
            return positions

        # 분석
        seoul_objects = []
        for name, line1, line2 in tle_sets:
            norad_raw = line1.split()[1]
            norad_id = norad_raw.lstrip("U")

            try:
                pos_list = predict_positions(line1, line2, analysis_hours)
                for idx in range(1, len(pos_list)):
                    dt, alt, lat, lon = pos_list[idx]
                    prev_dt, _, prev_lat, prev_lon = pos_list[idx - 1]
                    dist = haversine(SEOUL_LAT, SEOUL_LON, lat, lon)
                    if alt < 200 and dist <= radius_km:
                        kst_dt = dt.astimezone(timezone("Asia/Seoul"))
                        angle = bearing(prev_lat, prev_lon, lat, lon)
                        seoul_objects.append({
                            "NORAD ID": norad_id,
                            "위성명칭": name,
                            "예상 낙하 위도": round(lat, 2),
                            "예상 낙하 경도": round(lon, 2),
                            "예상 낙하 시간(KST)": kst_dt.strftime("%Y-%m-%d %H:%M:%S"),
                            "비행방향 (°)": angle
                        })
                        break
            except:
                continue

        st.subheader("📍 서울 기준 지정범위 내 예상 우주낙하물체")
        if seoul_objects:
            seoul_df = pd.DataFrame(seoul_objects)
            st.dataframe(seoul_df, use_container_width=True)

            # 다운로드 제공
            csv = seoul_df.to_csv(index=False).encode('utf-8')
            st.download_button("📂 낙하예상 우주물체 CSV 다운로드", data=csv, file_name="decay_list.csv", mime="text/csv")
        else:
            st.info("✅ 해당 반경 내 낙하예상 우주물체가 없습니다.")
