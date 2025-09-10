# Railway 배포 가이드

## 🚀 Railway에 GPS Logger 배포하기

### 1. Railway 계정 생성
1. [Railway.app](https://railway.app) 방문
2. GitHub 계정으로 로그인
3. "New Project" 클릭

### 2. 프로젝트 배포
1. "Deploy from GitHub repo" 선택
2. GPS Logger 저장소 선택
3. "Deploy" 클릭

### 3. PostgreSQL 데이터베이스 추가
1. 프로젝트 대시보드에서 "New" 클릭
2. "Database" → "PostgreSQL" 선택
3. 데이터베이스가 자동으로 생성됨

### 4. 환경변수 설정
Railway에서 자동으로 설정되는 환경변수:
- `DATABASE_URL`: PostgreSQL 연결 URL
- `PORT`: 서버 포트 (자동 설정)

### 5. OwnTracks 앱 설정
1. OwnTracks 앱 열기
2. 설정 → Connection
3. Host: `your-app-name.railway.app`
4. Port: `443` (HTTPS)
5. Path: `/owntracks`
6. Protocol: `https`

### 6. 테스트
```bash
# 로컬에서 테스트
python test_api.py

# 환경변수 설정 후 테스트
export GPS_SERVER_URL=https://your-app-name.railway.app
python test_api.py
```

## 📱 외부 접근 방법

### 웹 브라우저
- 지도 보기: `https://your-app-name.railway.app/map2`
- 데이터 확인: `https://your-app-name.railway.app/last?n=10`
- CSV 내보내기: `https://your-app-name.railway.app/export.csv`

### API 엔드포인트
- GPS 데이터 전송: `POST https://your-app-name.railway.app/api/loc`
- OwnTracks: `POST https://your-app-name.railway.app/owntracks`

## 🔧 문제 해결

### 데이터베이스 연결 오류
- Railway에서 PostgreSQL 서비스가 실행 중인지 확인
- `DATABASE_URL` 환경변수가 올바른지 확인

### OwnTracks 연결 실패
- HTTPS 사용 확인 (http가 아닌 https)
- 포트 443 사용 확인
- 방화벽 설정 확인

### 서버 오류
- Railway 로그 확인
- 환경변수 설정 확인
- 데이터베이스 연결 상태 확인

## 💰 비용
- Railway 무료 티어: 월 $5 크레딧
- PostgreSQL: 무료 (제한된 용량)
- 도메인: 무료 (railway.app 서브도메인)

## 🔄 로컬 + 클라우드 동기화
로컬 서버와 클라우드 서버를 동시에 사용하려면:
1. 로컬에서는 SQLite 사용
2. 클라우드에서는 PostgreSQL 사용
3. 데이터 동기화 스크립트 작성 (선택사항)
