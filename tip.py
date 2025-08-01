import streamlit as st
import pandas as pd
from sgp4.api import Satrec, jday
import math
from datetime import datetime, timedelta
from io import StringIO

SEOUL_LAT = 37.5665
SEOUL_LON = 126.9780
RANGE_MIN = 500
RANGE_MAX = 3000
HOURS_AHEAD = 168

st.set_page_config(page_title="우주 낙하물체 예측 for MSSB", layout="wide")
st.title("🛰️ 우주 낙하물체 예측 for MSSB")
st.markdown("서울 중심 반경 **500~3000km** 내에서 향후 **168시간 이내** 낙하 가능성을 분석합니다.")

uploaded_file = st.file_uploader("📂 TLE 파일 (.txt)을 업로드하세요", type="txt")

def read_tle_file(file):
    lines = file.getvalue().decode("utf-8").splitlines()
    satellites = []
    for i in range(0, len(lines), 3):
        try:
            name = lines[i].strip()
            line1 = lines[i+1].strip()
            line2 = lines[i+2].strip()
            sat = Satrec.twoline2rv(line1, line2)
            satellites.append({"name": name, "line1": line1, "line2": line2, "sat": sat})
        except IndexError:
            continue
    return satellites

def geodetic_position(r):
    x, y, z = r
    R = math.sqrt(x**2 + y**2 + z**2)
    lat = math.degrees(math.asin(z / R))
    lon = math.degrees(math.atan2(y, x))
    heading = math.degrees(math.atan2(y, x)) % 360
    return lat, lon, heading

def haversine(lat1, lon1, lat2, lon2):
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    return R * c

def predict_reentries(satellites):
    now = datetime.utcnow()
    events = []

    for sat_data in satellites:
        sat = sat_data["sat"]
        name = sat_data["name"]
        line1 = sat_data["line1"]
        sat_id = line1[2:7]

        for h in range(1, HOURS_AHEAD + 1):
            future_time = now + timedelta(hours=h)
            jday_now, fr = jday(future_time.year, future_time.month, future_time.day,
                                future_time.hour, future_time.minute, future_time.second)
            e, r, _ = sat.sgp4(jday_now, fr)
            if e != 0:
                continue

            lat, lon, heading = geodetic_position(r)
            dist = haversine(SEOUL_LAT, SEOUL_LON, lat, lon)

            if RANGE_MIN <= dist <= RANGE_MAX:
                local_time = future_time + timedelta(hours=9)
                events.append({
                    "NORAD ID": sat_id,
                    "Name": name,
                    "Predicted Time (KST)": local_time.strftime("%Y-%m-%d %H:%M:%S"),
                    "Latitude": round(lat, 4),
                    "Longitude": round(lon, 4),
                    "Direction (°)": round(heading, 1)
                })
                break

    return pd.DataFrame(events)

if uploaded_file and st.button("🛰️ 낙하 예측 분석 시작"):
    sats = read_tle_file(uploaded_file)
    df = predict_reentries(sats)

    if df.empty:
        st.warning("✨ 서울 반경 내 낙하 이벤트가 예측되지 않았습니다.")
    else:
        st.success(f"🚨 예측된 낙하 이벤트 총 {len(df)}건")
        st.dataframe(df, use_container_width=True)

        csv = df.to_csv(index=False)
        st.download_button("📥 결과 CSV 다운로드", data=csv.encode("utf-8"), file_name="mssb_predictions.csv", mime="text/csv")
