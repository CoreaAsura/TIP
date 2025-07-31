# app.py
import streamlit as st
import os
import pandas as pd
import requests
from datetime import datetime, timedelta
from sgp4.api import Satrec, WGS72

# 경로 설정
CSV_URL = "https://celestrak.org/NORAD/elements/gp.php?GROUP=active&FORMAT=CSV"
TLE_DIR = r"C:\tip"
CSV_FILE = os.path.join(TLE_DIR, "gp_active.csv")
FALL_THRESHOLD_KM = 120  # 대기권 경계 기준 고도 (임계 낙하 고도)

# ----------------------------------------
# 📥 데이터 다운로드
# ----------------------------------------
def download_gp_data():
    os.makedirs(TLE_DIR, exist_ok=True)
    try:
        res = requests.get(CSV_URL, timeout=10)
        res.raise_for_status()
        with open(CSV_FILE, "wb") as f:
            f.write(res.content)
        st.success("CSV 데이터 다운로드 완료!")
    except Exception as e:
        st.error(f"데이터 다운로드 실패: {e}")

# ----------------------------------------
# 🔍 위성 궤도 예측
# ----------------------------------------
def predict_position(row, target_dt):
    try:
        sat = Satrec()
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
        jd = target_dt.year + (target_dt - datetime(target_dt.year, 1, 1)).days / 365.25
        e, r, v = sat.sgp4(target_dt.year, target_dt.timetuple().tm_yday + target_dt.hour / 24.0)
        return r[2]  # z: 고도
    except Exception as e:
        return None

# ----------------------------------------
# 🖼️ Streamlit UI
# ----------------------------------------
st.title("🌍 GP CSV 기반 낙하지점 분석기")
st.markdown("CelesTrak의 GP CSV 데이터를 기반으로 위성 궤도를 예측하고 낙하지점을 분석합니다.")

if st.button("📥 CSV 데이터 다운로드"):
    download_gp_data()

if os.path.exists(CSV_FILE):
    df = pd.read_csv(CSV_FILE)
    sat_list = df["OBJECT_NAME"].dropna().unique()
    selected_sat = st.selectbox("위성 선택", sat_list)

    sat_row = df[df["OBJECT_NAME"] == selected_sat].iloc[0]

    predict_time = st.slider("예측 시점 (UTC)", 0, 48, 1, help="몇 시간 후의 위성 고도를 예측합니다")
    future_dt = datetime.utcnow() + timedelta(hours=predict_time)

    if st.button("🚀 낙하 여부 분석"):
        alt_km = predict_position(sat_row, future_dt)
        if alt_km is None:
            st.error("궤도 예측 실패 😢")
        else:
            st.metric("예측 고도 (km)", f"{alt_km:.2f}")
            if alt_km < FALL_THRESHOLD_KM:
                st.warning("❗ 대기권 재진입 가능성 있음!")
            else:
                st.success("✅ 궤도 안정 상태")

else:
    st.info("먼저 데이터를 다운로드해주세요.")
