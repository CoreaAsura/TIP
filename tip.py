from sgp4.api import Satrec
from sgp4.api import jday
from datetime import datetime, timedelta
import requests

# ✅ TLE 데이터 불러오기 (CelesTrak 예시 URL)
def get_tle(norad_id):
    url = f"https://celestrak.org/NORAD/elements/gp.php?CATNR={norad_id}&FORMAT=TLE"
    response = requests.get(url)
    lines = response.text.strip().split('\n')
    return lines[1], lines[2]  # TLE line1, line2

# ✅ 위성 위치 예측 함수
def predict_orbit(satrec, dt):
    jd, fr = jday(dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second)
    e, r, v = satrec.sgp4(jd, fr)
    if e == 0:  # 정상 예측
        return r  # 위치 벡터 [x, y, z] (km)
    else:
        return None

# ✅ 분석 수행
def simulate_decay(norad_id, days=5, interval_min=10):
    tle_line1, tle_line2 = get_tle(norad_id)
    sat = Satrec.twoline2rv(tle_line1, tle_line2)
    
    now = datetime.utcnow()
    print(f"📡 위성 NORAD ID: {norad_id} 궤도 예측 시작")

    for i in range(0, days * 24 * 60, interval_min):
        dt = now + timedelta(minutes=i)
        pos = predict_orbit(sat, dt)
        if pos:
            altitude = (pos[0]**2 + pos[1]**2 + pos[2]**2)**0.5 - 6371  # 지구 반지름 km 제외
            print(f"{dt.isoformat()} → 고도: {altitude:.2f} km")
            if altitude < 150:  # 임계 고도 아래로 접근
                print("⚠️ 낙하 위험 예측: 궤도 고도 150km 이하 접근!")
        else:
            print(f"{dt.isoformat()} → 궤도 예측 실패")

# ✅ 예시 실행: 위성 NORAD ID 사용
simulate_decay(norad_id=25544)  # 국제우주정거장(ISS)
