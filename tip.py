# tip.py
import streamlit as st
import requests
from datetime import datetime, timezone, timedelta
import pytz
from geopy.distance import geodesic

SEOUL = (37.5665, 126.9780)

class SpaceDebris:
    def __init__(self, norad_id, name, lat, lon, utc_time, azimuth_deg):
        self.norad_id = norad_id
        self.name = name
        self.lat = lat
        self.lon = lon
        self.utc_time = utc_time
        self.azimuth_deg = azimuth_deg

    @property
    def time_kst(self):
        return self.utc_time.astimezone(pytz.timezone("Asia/Seoul")).strftime("%Y-%m-%d %H:%M:%S")

    @property
    def is_near_seoul(self):
        return geodesic(SEOUL, (self.lat, self.lon)).km <= 3000

def fetch_tip_data_from_space_track():
    try:
        session = requests.Session()
        # 🔐 로그인 요청
        auth = {
            "identity": st.secrets["space_track_id"],
            "password": st.secrets["space_track_pw"]
        }
        session.post("https://www.space-track.org/ajaxauth/login", data=auth)

        # ⏱️ TIP 메시지 쿼리 (마지막 168시간 기준 TIP)
        tip_query_url = "https://www.space-track.org/basicspacedata/query/class/tip/decay_date/%3Enow/orderby/decay_date%20asc/format/json"

        response = session.get(tip_query_url)
        data = response.json()

        debris_list = []
        for item in data:
            try:
                norad_id = int(item.get("NORAD_CAT_ID", -1))
                name = item.get("OBJECT_NAME", "Unknown")
                lat = float(item.get("DECAY_LAT", 0.0))
                lon = float(item.get("DECAY_LON", 0.0))
                az = float(item.get("DECAY_DIR", 0.0))

                utc_time = datetime.strptime(item.get("DECAY_DATE"), "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
                debris_list.append(SpaceDebris(norad_id, name, lat, lon, utc_time, az))
            except:
                continue
        return debris_list
    except Exception as e:
        st.error(f"TIP 데이터 가져오기 오류: {e}")
        return []

def main():
    st.set_page_config(page_title="우주낙하물체 경보 for MSSB", layout="wide")
    st.title("🛰️ 우주낙하물체 경보 for MSSB")

    now_kst = datetime.now(pytz.timezone("Asia/Seoul")).strftime("%Y-%m-%d %H:%M:%S")
    st.markdown(f"**업데이트 기준 시간 (KST):** {now_kst}")

    st.markdown("**🕒 조회 시간 범위 선택 (단위: 시간):**")
    time_window = st.slider("조회 범위", min_value=24, max_value=168, step=24, value=48)
    st.divider()

    debris_list = fetch_tip_data_from_space_track()
    window_limit = datetime.now(timezone.utc) + timedelta(hours=time_window)
    filtered_all = [d for d in debris_list if d.utc_time <= window_limit]
    filtered_seoul = [d for d in filtered_all if d.is_near_seoul]

    # 서울 반경
    st.subheader("📍 서울 반경 3000km 이내 재진입 예정 우주물체")
    if filtered_seoul:
        st.table([{
            "NORAD ID": d.norad_id,
            "우주물체 명칭": d.name,
            "예상 낙하 좌표": f"{d.lat}, {d.lon}",
            "예상 낙하 시간 (KST)": d.time_kst,
            "비행 방향 (°)": f"{d.azimuth_deg}°"
        } for d in filtered_seoul])
    else:
        st.info("🚫 해당 시간 범위 내 서울 반경 3000km 내 낙하물체 없음")

    st.divider()

    # 전세계 현황
    st.subheader("🌍 전 세계 재진입 예정 우주물체 현황")
    if filtered_all:
        st.table([{
            "NORAD ID": d.norad_id,
            "우주물체 명칭": d.name,
            "예상 좌표": f"{d.lat}, {d.lon}",
            "예상 낙하 시간 (KST)": d.time_kst,
            "비행 방향 (°)": f"{d.azimuth_deg}°"
        } for d in filtered_all])
    else:
        st.info("🌐 해당 시간 범위 내 재진입 예정 물체 없음")

if __name__ == "__main__":
    main()
