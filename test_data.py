import re
import requests
import json
from datetime import datetime, timedelta, timezone

#서버 URL
SERVER_URL = "https://web-production-e1bf.up.railway.app"

#테스트 데이터
test_data = [
    # 9월 8일 출근
    {
        "device_id": "test_phone",
        "lat": 36.3504,  # 대전 서구 도마로7번길 41 (예상 좌표)
        "lon": 127.3845,
        "accuracy": 10.0,
        "ts": "2025-09-08T13:30:00+09:00", 
        "provider": "manual"
    },
    {
        "device_id": "test_phone", 
        "lat": 36.3489,  # 대전 서구 가수원동 799-2 (예상 좌표)
        "lon": 127.3821,
        "accuracy": 10.0,
        "ts": "2025-09-08T13:45:00+09:00",  # 오후 1시 45분 (UTC)
        "provider": "manual"
    },
    # 9월 8일 퇴근
    {
        "device_id": "test_phone",
        "lat": 36.3489,  # 가수원동 799-2
        "lon": 127.3821,
        "accuracy": 10.0,
        "ts": "2025-09-08T18:15:00+09:00",  # 저녁 6시 15분 (UTC)
        "provider": "manual"
    },
    {
        "device_id": "test_phone",
        "lat": 36.3504,  # 도마로7번길 41
        "lon": 127.3845,
        "accuracy": 10.0,
        "ts": "2025-09-08T18:30:00+09:00",  # 저녁 6시 30분 (UTC)
        "provider": "manual"
    }
]

#데이터 전송
for data in test_data:
    try:
        response = requests.post(f"{SERVER_URL}/api/loc", json=data)
        if response.status_code == 200:
            print(f"데이터 전송 성공: {data['ts']}")
        else:
            print(f"데이터 전송 실패: {response.status_code}")
    except Exception as e:
        print(f"오류 발생: {e}")

print("\n테스트 완료")
print(f"지도확인: {SERVER_URL}/map?days=7")
print(f"데이터확인: {SERVER_URL}/last?n=5")
