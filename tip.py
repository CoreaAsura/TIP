import streamlit as st
import pandas as pd
from sgp4.api import Satrec, jday
import math
from datetime import datetime, timedelta

# 서울 중심 기준 (위도/경도)
SEOUL_LAT = 37.5665
SEOUL_LON = 126.9780

# 분석 기준
RANGE_MIN = 500
RANGE_MAX = 3000
HOURS_AHEAD = 48

st.set_page_config(page_title="우주 낙하물체 예측 for MSSB", layout="wide")
st.title("🛰️ 우주 낙하물체 예측 for MSSB")
st.markdown("서울 중심 반경 **500km~3000km**, 향후 **48시간 내** 낙하 가능성이 있는 물체를 예측합니다.")

uploaded_file = st.file_uploader("📂 TLE 파일 (.txt)을 업로드하세요", type="txt")

def read_tle(file):
    lines = file.getvalue().decode("utf-8").splitlines()
    sats = []
    for i in range(0, len(lines), 3):
        try:
            name = lines[i].strip()
            l1 = lines[i+1].strip()
            l2 = lines[i+2].strip()
            sat = Satrec.twoline2rv(l1, l2)
            sats.append({
                "name": name,
                "line1": l1,
                "line2": l2,
                "sat": sat
            })
        except:
            continue
    return sats

def geodetic_pos(r):
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
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))

def predict(sats):
    now = datetime.utcnow()
    events = []

    for s in sats:
        sat = s["sat"]
        name = s["name"]
        l1 = s["line1"]
        sat_id = l1[2:7]

        for h in range(1, HOURS_AHEAD+1):
            ft = now + timedelta(hours=h)
            jd, fr = jday(ft.year, ft.month, ft.day, ft.hour, ft.minute, ft.second)
            e, r, _ = sat.sgp4(jd, fr)
            if e != 0: continue

            lat, lon, head = geodetic_pos(r)
            d = haversine(SEOUL_LAT, SEOUL_LON, lat, lon)

            if RANGE_MIN <= d <= RANGE_MAX:
                kst = ft + timedelta(hours=9)
                events.append({
                    "NORAD ID": sat_id,
                    "Name": name,
                    "Predicted Time (KST)": kst.strftime("%Y-%m-%d %H:%M:%S"),
                    "Latitude": round(lat, 4),
                    "Longitude": round(lon, 4),
                    "Direction (°)": round(head, 1)
                })
                break

    return pd.DataFrame(events)

if uploaded_file and st.button("🚨 48시간 낙하 예측 시작"):
    sats = read_tle(uploaded_file)
    df = predict(sats)

    if df.empty:
        st.warning("✨ 48시간 내 서울 반경에서 예상되는 낙하 이벤트가 없습니다.")
    else:
        st.success(f"🔎 총 {len(df)}건의 낙하 이벤트 예측됨")
        st.dataframe(df, use_container_width=True)

        csv = df.to_csv(index=False)
        st.download_button("📥 결과 CSV 다운로드", data=csv.encode("utf-8"), file_name="mssb_48h_prediction.csv", mime="text/csv")
