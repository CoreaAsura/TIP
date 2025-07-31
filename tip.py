import streamlit as st
import pandas as pd
import requests
import os
import math
from datetime import datetime, timedelta
from sgp4.api import Satrec, WGS72
from pytz import timezone

# 설정
TITLE = "☄️ 우주 낙하물체 예측 for MSSB"
CSV_URL = "https://celestrak.org/NORAD/elements/gp.php?GROUP=active&FORMAT=CSV"
LOCAL_DIR = r"C:\tip"
CSV_PATH = os.path.join(LOCAL_DIR, "gp_active.csv")
SEOUL_LAT, SEOUL_LON = 37.5665, 126.9780
FALL_ALT_KM = 200  # 낙하 고도 기준

st.set_page_config(page_title=TITLE, layout="wide")
st.title(TITLE)

# 🔻 현재 시간 출력 (KST)
kst_now = datetime.utcnow().astimezone(timezone("Asia/Seoul"))
st.markdown(f"🕒 현재 시각 (KST): `{kst_now.strftime('%Y-%m-%d %H:%M:%S')}`")

# ✅ CSV 다운로드
if st.button("📥 전체 GP CSV 데이터 다운로드"):
    try:
        os.makedirs(LOCAL_DIR, exist_ok=True)
        res = requests.get(CSV_URL, timeout=10)
        with open(CSV_PATH, "wb") as f:
            f.write(res.content)
        st.success(f"✅ 다운로드 완료 → `{CSV_PATH}`")
    except Exception as e:
        st.error(f"❌ 다운로드 실패: {e}")

# 📂 CSV 불러오기
if os.path.exists(CSV_PATH):
    df = pd.read_csv(CSV_PATH)
    st.markdown(f"📊 CSV에서 불러온 위성 수: `{len(df)}`")

    # 🎛️ 파라미터 설정
    radius_km = st.slider("서울 중심 기준 분석 반경 (km)", 500, 3000, 1000, step=100)
    hours = st.slider("예측 시간 범위 (시간)", 1, 168, 24)

    # 🛠️ 함수 정의
    def haversine(lat1, lon1, lat2, lon2):
        R = 6371
        dLat = math.radians(lat2 - lat1)
        dLon = math.radians(lon2 - lon1)
        a = math.sin(dLat / 2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dLon / 2)**2
        return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    def bearing(lat1, lon1, lat2, lon2):
        lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
        dLon = lon2 - lon1
        x = math.sin(dLon) * math.cos(lat2)
        y = math.cos(lat1)*math.sin(lat2) - math.sin(lat1)*math.cos(lat2)*math.cos(dLon)
        return round((math.degrees(math.atan2(x, y)) + 360) % 360, 1)

    def propagate_satellite(row, dt):
        sat = Satrec()
        try:
            epoch = datetime.strptime(row["EPOCH"], "%Y-%m-%dT%H:%M:%S")
            sat.sgp4init(
                WGS72,
                bstar=row["BSTAR"],
                epoch=epoch,
                ndot=0.0, nddot=0.0,
                ecco=row["ECCENTRICITY"],
                argpo=row["ARG_OF_PERICENTER"],
                inclo=row["INCLINATION"],
                mo=row["MEAN_ANOMALY"],
                no_kozai=row["MEAN_MOTION"],
                nodeo=row["RA_OF_ASC_NODE"]
            )
            jd = dt.year + ((dt - datetime(dt.year, 1, 1)).days / 365.25)
            e, r, v = sat.sgp4(dt.year, dt.timetuple().tm_yday + dt.hour / 24.0)
            if e == 0:
                x, y, z = r
                alt = math.sqrt(x**2 + y**2 + z**2) - 6371
                lon = math.degrees(math.atan2(y, x))
                hyp = math.sqrt(x**2 + y**2)
                lat = math.degrees(math.atan2(z, hyp))
                return alt, lat, lon
        except:
            return None

    # ☄️ 전체 위성 분석
    results = []
    for _, row in df.iterrows():
        for h in range(1, hours + 1):
            dt = datetime.utcnow() + timedelta(hours=h)
            pos1 = propagate_satellite(row, dt - timedelta(hours=1))
            pos2 = propagate_satellite(row, dt)
            if pos2 and pos1:
                alt, lat, lon = pos2
                dist = haversine(SEOUL_LAT, SEOUL_LON, lat, lon)
                if alt < FALL_ALT_KM and dist <= radius_km:
                    bearing_deg = bearing(pos1[1], pos1[2], lat, lon)
                    dt_kst = dt.astimezone(timezone("Asia/Seoul")).strftime("%Y-%m-%d %H:%M:%S")
                    results.append({
                        "NORAD ID": row["NORAD_CAT_ID"],
                        "위성명칭": row["OBJECT_NAME"],
                        "예상 낙하시간(KST)": dt_kst,
                        "예상 낙하 위도": round(lat, 2),
                        "예상 낙하 경도": round(lon, 2),
                        "비행방향(DEGREE)": bearing_deg
                    })
                    break  # 낙하 예측되면 분석 종료

    # 📊 결과 출력
    st.subheader("📍 낙하 이벤트 분석 결과")
    if results:
        result_df = pd.DataFrame(results)
        st.dataframe(result_df, use_container_width=True)
        csv = result_df.to_csv(index=False).encode("utf-8")
        st.download_button("📂 분석 결과 CSV 다운로드", data=csv, file_name="decay_list.csv", mime="text/csv")
    else:
        st.info("✅ 설정한 시간/반경 내에서 낙하 이벤트가 탐지되지 않았습니다.")
else:
    st.info(f"⚠️ `{CSV_PATH}` 파일이 존재하지 않습니다. 먼저 데이터를 다운로드하세요.")
