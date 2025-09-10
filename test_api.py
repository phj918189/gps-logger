import requests
import json
import os

# 환경변수에서 서버 URL 가져오기 (Railway 배포 시)
SERVER_URL = os.getenv('GPS_SERVER_URL', 'http://localhost:5000')

# 서버가 실행 중인지 확인
try:
    # 최근 데이터 확인
    response = requests.get(f"{SERVER_URL}/last?n=5")
    if response.status_code == 200:
        data = response.json()
        print("최근 5개 데이터:")
        for row in data['rows']:
            print(f"{row['ts_kst']} | {row['lat']}, {row['lon']} | {row['device_id']}")
        print(f"총 {data['count']}개")
    else:
        print(f"API 호출 실패: {response.status_code}")
        
    # 지도 데이터 확인 (최근 7일)
    print("\n지도 데이터 (최근 7일):")
    response = requests.get(f"{SERVER_URL}/map2?days=7")
    if response.status_code == 200:
        print("지도 데이터 로드 성공")
    else:
        print(f"지도 데이터 로드 실패: {response.status_code}")
        
    # 전체 데이터 확인
    print("\n전체 데이터:")
    response = requests.get(f"{SERVER_URL}/map2?all=1")
    if response.status_code == 200:
        print("전체 데이터 로드 성공")
    else:
        print(f"전체 데이터 로드 실패: {response.status_code}")
        
except requests.exceptions.ConnectionError:
    print("서버에 연결할 수 없습니다. 서버가 실행 중인지 확인하세요.")
    print(f"서버 URL: {SERVER_URL}")
except Exception as e:
    print(f"오류 발생: {e}")
