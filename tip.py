import streamlit as st
import pandas as pd
import math
import os

# 📍 서울 기준 위치 및 반경 설정
SEOUL_LAT, SEOUL_LON = 37.5665, 126.9780
RADIUS_KM = 50

# 🧮 방위각 계산 함수
def calculate_bearing(lat1, lon1, lat2, lon2):
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    dLon = lon2 - lon1
    x = math.sin(dLon) * math.cos(lat2)
    y = math.cos(lat1)*math.sin(lat2) - math.sin(lat1)*math.cos(lat2)*math.cos(dLon)
    bearing = (math.degrees(math.atan2(x, y)) + 360) % 360
    return round(bearing, 1)

# 📍 거리 계산 (Haversine 공식)
def haversine(lat1, lon1, lat2, lon2):
    R = 6371  # 지구 반지름(km)
    dLat = math.radians(lat2 - lat1)
    dLon = math.radians(lon2 - lon1)
    a = math.sin(dLat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dLon/2)**2
    c = 2 * math.asin(math.sqrt(a))
    return R * c

# 📁 파일 존재 확인 및 로딩
csv_path = "sample_decay_data.csv"
if not os.path.exists(csv_path):
    st.error("❌ 데이터 파일 'sample_decay_data.csv'이 존재하지 않습니다.\n같은 디렉토리에 파일을 추가하거나 경로를 수정해주세요.")
else:
    df = pd.read_csv(csv_path)

    # 📌 서울 반경 내 위치 필터링
    filtered = df[df.apply(lambda row: haversine(SEOUL_LAT, SEOUL_LON, row['DecayLat'], row['DecayLon']) <= RADIUS_KM, axis=1)]

    # 🧭 비행방향 계산
    filtered["비행방향 (°)"] = filtered.apply(lambda row: calculate_bearing(row["PreLat"], row["PreLon"], row["DecayLat"], row["DecayLon"]), axis=1)

    # 🕒 시간 포맷 정리
    filtered["예상 낙하 시간(KST)"] = pd.to_datetime(filtered["DecayTime"]).dt.strftime("%Y-%m-%d %H:%M:%S")

    # 📊 최종 출력 데이터프레임 구성
    seoul_df = filtered[["NORAD", "Name", "DecayLat", "DecayLon", "예상 낙하 시간(KST)", "비행방향 (°)"]]

    # 📥 다운로드 버튼
    st.download_button(
        "📂 낙하예상 우주물체 CSV 다운로드",
        data=seoul_df.to_csv(index=False).encode('utf-8'),
        file_name="decay_list.csv",
        mime="text/csv"
    )
