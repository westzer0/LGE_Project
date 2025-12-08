# 로컬 환경 설정 완료 ✅

## 설정 완료 내역

### ✅ Python 가상환경
- 가상환경 생성 완료: `venv/`
- Python 버전: 3.8.3
- Django 버전: 4.2.16 (Python 3.8 호환)
- 모든 필수 패키지 설치 완료

### ✅ Node.js 의존성
- Node.js 버전: v24.11.1
- npm 패키지 설치 완료 (137개 패키지)

### ✅ 환경 변수 설정
- `.env` 파일 생성 완료
- Django 시크릿 키 자동 생성 및 설정 완료
- ⚠️ **필요한 API 키를 .env 파일에 입력해주세요:**
  - `KAKAO_REST_API_KEY`
  - `KAKAO_JS_KEY`
  - `KAKAO_NATIVE_APP_KEY`
  - `KAKAO_ADMIN_KEY`
  - `OPENAI_API_KEY`
  - `ORACLE_PASSWORD` (Oracle DB 사용 시)

### ✅ 데이터베이스
- SQLite 데이터베이스 마이그레이션 완료
- 모든 테이블 생성 완료

## 서버 실행 방법

### 1. Django 서버 실행 (터미널 1)

**PowerShell:**
```powershell
# 가상환경 활성화
.\venv\Scripts\Activate.ps1

# 서버 실행
python manage.py runserver 8000
```

**또는 배치 파일 사용:**
```powershell
.\start_server_fixed.bat
```

### 2. React 개발 서버 실행 (터미널 2)

```powershell
npm run dev
```

### 3. 접속 URL
- React 앱: http://localhost:3000
- Django API: http://localhost:8000
- Django Admin: http://localhost:8000/admin

## 추가 설정 (선택사항)

### Oracle 데이터베이스 사용 시
1. Oracle Instant Client 설치 필요
2. `.env` 파일에서 `ORACLE_PASSWORD` 설정
3. `USE_ORACLE=true` 추가 (필요 시)

### ngrok 설정 (카카오 API 연동 시)
```powershell
# ngrok 토큰 설정 (최초 1회)
powershell -ExecutionPolicy Bypass -File setup_ngrok_simple.ps1 -Token YOUR_NGROK_TOKEN
```

## 주의사항

1. **Python 버전**: 현재 Python 3.8.3을 사용 중입니다. Django 5.x를 사용하려면 Python 3.10 이상이 필요합니다.

2. **API 키**: `.env` 파일에 실제 API 키를 입력해야 일부 기능이 정상 작동합니다.

3. **가상환경 활성화**: Django 명령어를 실행하기 전에 항상 가상환경을 활성화해야 합니다.

4. **Oracle 경고**: Oracle Instant Client가 설치되지 않아 경고가 표시되지만, SQLite를 기본으로 사용하므로 문제없습니다.

## 문제 해결

### 가상환경 활성화 오류
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### 패키지 재설치
```powershell
.\venv\Scripts\python.exe -m pip install -r requirements.txt
```

### 데이터베이스 초기화
```powershell
.\venv\Scripts\python.exe manage.py migrate
```

---

**설정 완료 시간**: $(Get-Date -Format "yyyy-MM-dd HH:mm:ss")

