# ngrok 문제 해결 가이드

## 발견된 문제점

### 1. ✅ 수정 완료: 경로 문제
- **문제**: `start_ngrok.bat`에서 `ngrok.exe`를 PATH에서 찾으려고 함
- **해결**: 프로젝트 내 `ngrok\ngrok.exe` 경로를 사용하도록 수정 완료

### 2. ⚠️ 가능한 문제: 인증 토큰 미설정
- **증상**: ngrok 실행 시 인증 오류
- **해결 방법**:
  ```powershell
  # 1. 토큰 발급: https://dashboard.ngrok.com/get-started/your-authtoken
  # 2. 토큰 설정:
  .\ngrok\ngrok.exe config add-authtoken YOUR_TOKEN
  ```

### 3. ⚠️ 가능한 문제: 포트 8000 사용 중
- **증상**: "address already in use" 오류
- **해결 방법**:
  ```powershell
  # 포트 사용 확인
  netstat -ano | findstr :8000
  
  # 다른 포트 사용
  python manage.py runserver 8001
  .\ngrok\ngrok.exe http 8001
  ```

### 4. ⚠️ 가능한 문제: 실행 중인 ngrok 프로세스
- **증상**: ngrok이 이미 실행 중
- **해결 방법**:
  ```powershell
  # 실행 중인 프로세스 확인
  tasklist | findstr ngrok
  
  # 프로세스 종료
  taskkill /F /IM ngrok.exe
  ```

### 5. ⚠️ 가능한 문제: 방화벽 차단
- **증상**: ngrok이 연결되지 않음
- **해결 방법**: Windows 방화벽에서 ngrok.exe 허용

## 자동 진단 및 수정 도구

### 진단 스크립트 실행
```powershell
powershell -ExecutionPolicy Bypass -File diagnose_ngrok.ps1
```

### 자동 수정 스크립트 실행
```powershell
.\auto_fix_ngrok.bat
```

## 단계별 해결 방법

### Step 1: ngrok.exe 확인
```powershell
cd "c:\Users\134\Desktop\DX Project"
dir ngrok\ngrok.exe
```

없으면:
```powershell
powershell -ExecutionPolicy Bypass -File setup_ngrok_simple.ps1
```

### Step 2: 인증 토큰 확인
```powershell
.\ngrok\ngrok.exe config check
```

토큰이 없으면:
```powershell
# 1. https://dashboard.ngrok.com/get-started/your-authtoken 접속
# 2. 토큰 복사 후:
.\ngrok\ngrok.exe config add-authtoken YOUR_TOKEN
```

### Step 3: 포트 및 프로세스 확인
```powershell
# 포트 확인
netstat -ano | findstr :8000

# ngrok 프로세스 확인
tasklist | findstr ngrok
```

### Step 4: 서버 시작
```powershell
.\start_ngrok.bat
# 또는
.\start_server_fixed.bat
```

## 다른 로컬과의 차이점 확인

다른 로컬에서는 작동하는데 현재 로컬에서만 안 되는 경우:

1. **ngrok 인증 토큰**: 사용자별로 설정 필요
2. **방화벽 설정**: 로컬 보안 정책 차이
3. **포트 충돌**: 다른 프로그램이 포트 사용 중
4. **ngrok 버전**: 다른 버전 사용 가능성
5. **PATH 설정**: 시스템 PATH에 ngrok이 있는 경우

## 빠른 테스트

```powershell
# 1. ngrok 실행 테스트
.\ngrok\ngrok.exe version

# 2. 인증 토큰 테스트
.\ngrok\ngrok.exe config check

# 3. 간단한 터널 테스트 (로컬 서버가 실행 중일 때)
.\ngrok\ngrok.exe http 8000
```

## 추가 도움말

- ngrok 공식 문서: https://ngrok.com/docs
- ngrok 대시보드: https://dashboard.ngrok.com
