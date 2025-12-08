# 서버 현황 체크리스트

## 📊 현재 상태 (체크 필요)

### 🔴 실행 중인 서버
- **Django 백엔드 (포트 8000)**: ❌ 실행 안 됨
- **Vite 프론트엔드 (포트 3000)**: ❌ 실행 안 됨  
- **ngrok 터널 (포트 4040)**: ❌ 실행 안 됨

### 📁 환경 설정 파일
- `.env` 파일: 확인 필요
- `venv` (Python 가상환경): 확인 필요
- `node_modules` (Node.js 모듈): 확인 필요

---

## 🚀 서버 시작 방법

### 1. 백엔드 서버 (Django)
```bash
# 방법 1: 배치 파일 사용 (권장)
start_server_fixed.bat

# 방법 2: 수동 실행
venv\Scripts\activate
python manage.py runserver 8000
```

### 2. 프론트엔드 서버 (Vite/React)
```bash
npm run dev
```
→ 포트 3000에서 실행됩니다

### 3. ngrok 터널 (인터넷 공개)
```bash
# 먼저 설정 (최초 1회)
powershell -ExecutionPolicy Bypass -File setup_ngrok_simple.ps1 -Token YOUR_TOKEN

# 터널 시작
ngrok\ngrok.exe http 8000
```

---

## 🗄️ 데이터베이스 설정

### Oracle DB 사용 시
`.env` 파일에 다음 설정 추가:
```env
USE_ORACLE=true
ORACLE_USER=campus_24K_LG3_DX7_p3_4
ORACLE_PASSWORD=your_password
ORACLE_HOST=project-db-campus.smhrd.com
ORACLE_PORT=1524
ORACLE_SID=xe
ORACLE_INSTANT_CLIENT_PATH=C:\oracle\instantclient_19_23
```

### SQLite 사용 시 (기본값)
`.env` 파일에 `USE_ORACLE=false` 또는 설정하지 않으면 자동으로 SQLite 사용

---

## ✅ 빠른 체크 명령어

### PowerShell에서 실행:
```powershell
# 서버 상태 확인 스크립트 실행
powershell -ExecutionPolicy Bypass -File check_server_status.ps1

# 또는 수동 확인
netstat -ano | findstr ":8000"  # Django
netstat -ano | findstr ":3000"  # Vite
netstat -ano | findstr ":4040"  # ngrok
```

---

## 📝 다음 단계

1. **환경 확인**
   - `.env` 파일이 있는지 확인
   - `venv` 폴더가 있는지 확인
   - `node_modules` 폴더가 있는지 확인

2. **의존성 설치** (필요시)
   ```bash
   # Python 패키지
   pip install -r requirements.txt
   
   # Node 패키지
   npm install
   ```

3. **서버 시작**
   - 백엔드: `start_server_fixed.bat`
   - 프론트엔드: `npm run dev` (별도 터미널)

4. **접속 확인**
   - 백엔드: http://localhost:8000
   - 프론트엔드: http://localhost:3000

---

## 🔧 문제 해결

### 포트가 이미 사용 중일 때
```bash
# 프로세스 찾기
netstat -ano | findstr ":8000"
# PID 확인 후 종료
taskkill /PID [PID번호] /F
```

### 가상환경이 없을 때
```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

### node_modules가 없을 때
```bash
npm install
```
