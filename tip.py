import streamlit as st
import requests
import math
import pandas as pd
from datetime import datetime, timedelta
from sgp4.api import Satrec, jday
from pytz import timezone
import os

# 📍 서울 위치
SEOUL_LAT, SEOUL_LON = 37.5665, 126.9780
kst_now = datetime.utcnow().astimezone(timezone("Asia/Seoul"))
st.set_page_config(page_title="우주 낙하물체 예측 for MSSB", layout="wide")
st.title("☄️ 우주 낙하물체 예측 for MSSB")
st.markdown(f"🕒 현재 시각 (KST): `{kst_now.strftime('%Y-%m-%d %H:%M:%S')}`")

# 📁 파일 경로 설정
TLE_DIR = r"C:\tip"
TLE_FILE = os.path.join(TLE_DIR, "active.txt")
TLE_URL = "https://celestrak.org/NORAD/elements/active.txt"

# 📥 TLE 다운로드 버튼
if st.button("📥 전체 TLE 다운로드하기"):
    try:
        os.makedirs(TLE_DIR, exist_ok=True)
        res = requests.get(TLE_URL, timeout=10)
        with open(TLE_FILE, "w", encoding="utf-8") as f:
            f.write(res.text)
        st.success(f"✅ 다운로드 완료!\n📂 저장 위치: `{TLE_FILE}`")
    except Exception as e:
        st.error(f"❌ 다운로드 오류: {e}")

# 📂 TLE 불러오기 버튼
if st.button("📂 저장된 TLE 불러오기"):
    if os.path.exists(TLE_FILE):
        with open(TLE_FILE, "r", encoding="utf-8") as f:
            lines = f.readlines()
        tle_sets = []
        for i in range(0, len(lines), 3):
            if i + 2 < len(lines):
                name = lines[i].strip()
                line1 = lines[i+1].strip()
                line2 = lines[i+2].strip()
                tle_sets.append((name, line1, line2))
        st.session_state['tle_sets'] = tle_sets
        st.success(f"🛰️ 총 `{len(tle_sets)}`개의 위성 데이터 불러옴")
    else:
        st.warning(f"⚠️ TLE 파일이 `{TLE_FILE}`에 존재하지 않습니다. 먼저 다운로드하세요.")

# 🎛️ 분석 파라미터 설정
st.markdown("### 🎚️ 낙하 분석 설정")
radius_km = st.slider("서울 기준 분석 반경 (km)", 500, 5000, 3000)
analysis_hours = st.slider("낙하 예측 시간 범위 (시간)", 24, 168, 72)

# ☄️ 분석 시작
if st.button("☄️ 낙하예상 분석 시작"):
    tle_sets = st.session_state.get('tle_sets', [])
    if not tle_sets:
        st.error("📂 먼저 TLE 파일을 불러와주세요.")
    else:
        def haversine(lat1, lon1, lat2, lon2):
            R = 6371
            dLat = math.radians(lat2 - lat1)
            dLon = math.radians(lon2 - lon1)
            a = math.sin(dLat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dLon/2)**2
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

        result_objects = []
        for name, line1, line2 in tle_sets:
            tokens = line1.split()
            norad_id = tokens[1] if len(tokens) > 1 else "00000"
            try:
                pos_list = predict_positions(line1, line2, analysis_hours)
                for idx in range(1, len(pos_list)):
                    dt, alt, lat, lon = pos_list[idx]
                    _, _, prev_lat, prev_lon = pos_list[idx - 1]
                    dist = haversine(SEOUL_LAT, SEOUL_LON, lat, lon)
                    if alt < 200 and dist <= radius_km:
                        kst_dt = dt.astimezone(timezone("Asia/Seoul"))
                        direction = bearing(prev_lat, prev_lon, lat, lon)
                        result_objects.append({
                            "NORAD ID": norad_id,
                            "위성명칭": name,
                            "예상 낙하 위도": round(lat, 2),
                            "예상 낙하 경도": round(lon, 2),
                            "예상 낙하 시간(KST)": kst_dt.strftime("%Y-%m-%d %H:%M:%S"),
                            "비행방향(°)": direction
                        })
                        break
            except Exception:
                continue

        if result_objects:
            df = pd.DataFrame(result_objects)
            st.session_state['result_df'] = df
            st.subheader("📍 분석 결과: 서울 기준 낙하예상 물체")
            st.dataframe(df, use_container_width=True)
            csv = df.to_csv(index=False).encode("utf-8")
            st.download_button("📂 분석 결과 CSV 다운로드", data=csv, file_name="decay_list.csv", mime="text/csv")
        else:
            st.info("✅ 현재 반경 내 낙하예상 물체가 없습니다.")

# 📌 이전 결과 유지
if 'result_df' in st.session_state:
    st.markdown("✅ 최근 분석 결과 보기:")
    st.dataframe(st.session_state['result_df'], use_container_width=True)
