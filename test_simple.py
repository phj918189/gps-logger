import requests

# 서버 URL
SERVER_URL = "https://web-production-e1bf.up.railway.app"

# 간단한 테스트 데이터
data = {
    "device_id": "test_phone",
    "lat": 36.3504,
    "lon": 127.3845,
    "accuracy": 10.0,
    "provider": "manual"
}

try:
    response = requests.post(f"{SERVER_URL}/api/loc", json=data)
    print(f"상태 코드: {response.status_code}")
    print(f"응답: {response.text}")
except Exception as e:
    print(f"오류: {e}")

# 데이터 확인
try:
    response = requests.get(f"{SERVER_URL}/last?n=5")
    print(f"\n데이터 확인 - 상태 코드: {response.status_code}")
    print(f"응답: {response.text}")
except Exception as e:
    print(f"데이터 확인 오류: {e}")
