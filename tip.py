import requests
import datetime
import pytz
from math import radians, cos, sin, sqrt, atan2

# 📍 설정값
KST = pytz.timezone('Asia/Seoul')
SEOUL_LAT, SEOUL_LON = 37.5665, 126.9780
TIP_URL = "https://www.space-track.org/basicspacedata/query/TIP"
SATDECAY_URL = "https://www.space-track.org/basicspacedata/query/SATDECAY"

# 📡 현재 시간 (업데이트 시각 표시용)
def get_current_kst():
    return datetime.datetime.now(KST).strftime('%Y-%m-%d %H:%M:%S')

# 🔎 TIP 메시지 조회
def fetch_tip_data(hours):
    assert 24 <= hours <= 168, "시간 범위는 24~168시간 사이여야 합니다."
    params = {"hours": hours, "format": "json"}
    response = requests.get(TIP_URL, params=params)
    return response.json() if response.ok else []

# 🌐 SATDECAY API 조회
def fetch_decay_data(days=180):
    params = {"days": days, "format": "json"}
    response = requests.get(SATDECAY_URL, params=params)
    return response.json() if response.ok else []

# 📍 서울 기준 거리 계산
def haversine(lat1, lon1, lat2, lon2):
    R = 6371
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat/2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon/2)**2
    return R * 2 * atan2(sqrt(a), sqrt(1 - a))

# 🎯 서울 기준 3000km 이내 필터링
def filter_near_seoul(data, radius_km=3000):
    filtered = []
    for item in data:
        lat = item.get("LATITUDE")
        lon = item.get("LONGITUDE")
        if lat and lon:
            distance = haversine(SEOUL_LAT, SEOUL_LON, float(lat), float(lon))
            if distance <= radius_km:
                filtered.append(item)
    return filtered

# 🖥️ 데이터 출력
def render_report(hours):
    tip_data = fetch_tip_data(hours)
    decay_data = fetch_decay_data()
    near_seoul = filter_near_seoul(tip_data)

    print(f"\n📡 [우주낙하물체 현황 for MSSB] - 업데이트 시각: {get_current_kst()}")
    print(f"🕒 분석 대상 시간: 최근 {hours}시간 TIP 메시지 기반\n")

    print("🎯 [서울 기준 3000km 이내 낙하예정 물체]")
    for item in near_seoul:
        print(f"""
🛰️ NORAD ID: {item.get('NORAD_CAT_ID', '알 수 없음')}
🔖 명칭: {item.get('OBJECT_NAME', '이름없음')}
📍 예상좌표: {item.get('LATITUDE', '?')}, {item.get('LONGITUDE', '?')}
⏰ 예상시간: {item.get('IMPACT_DATE', '미정')}
🧭 비행방향: {item.get('IMPACT_DIRECTION', '미정')}
        """)

    print("\n🌍 [전 세계 낙하예정 우주물체 (일부)]")
    for item in tip_data[:5]:
        print(f" - {item.get('OBJECT_NAME', '이름없음')} @ {item.get('LATITUDE', '?')}, {item.get('LONGITUDE', '?')}")

    print("\n☄️ [180일 내 낙하예정 Satellite 목록]")
    for item in decay_data[:5]:
        print(f" - {item.get('OBJECT_NAME', '이름없음')} | 낙하예정일: {item.get('DECAY_DATE', '미정')}")

# ✅ 호출 예시
if __name__ == "__main__":
    render_report(72)  # 예시: 최근 72시간 데이터 조회
