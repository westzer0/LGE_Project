# ngrok 서버 실행 가이드

## 빠른 시작

### 방법 1: 배치 파일 사용 (권장)
```powershell
# 프로젝트 폴더에서 실행
.\start_server_fixed.bat
```

이 스크립트는 자동으로:
1. Django 서버를 8000 포트에서 시작
2. ngrok 터널을 시작하여 인터넷에 공개

### 방법 2: 수동 실행

**터미널 1 - Django 서버 실행:**
```powershell
cd "c:\Users\134\Desktop\DX Project"
# 가상환경 활성화 (있는 경우)
.\venv\Scripts\activate
# Django 서버 시작
python manage.py runserver 8000
```

**터미널 2 - ngrok 실행:**
```powershell
cd "c:\Users\134\Desktop\DX Project"
.\ngrok\ngrok.exe http 8000
```

## ngrok 인증 토큰 설정 (처음 한 번만)

ngrok을 처음 사용하는 경우 인증 토큰이 필요합니다:

1. **토큰 발급 받기:**
   - https://dashboard.ngrok.com/get-started/your-authtoken 접속
   - (회원가입 필요 - 무료)

2. **토큰 설정:**
```powershell
.\ngrok\ngrok.exe config add-authtoken YOUR_AUTH_TOKEN
```

또는 자동 설정 스크립트 사용:
```powershell
powershell -ExecutionPolicy Bypass -File setup_ngrok_simple.ps1 -Token YOUR_AUTH_TOKEN
```

## Forwarding URL 확인 방법 (중요!)

### 방법 1: NGROK 터미널 창에서 확인 (가장 쉬움)

`start_ngrok.bat`을 실행하면 **"ngrok Tunnel"** 이라는 제목의 검은색 CMD 창이 열립니다.

이 창에서 다음과 같은 텍스트를 찾으세요:

```
Session Status                online
Account                       Your Name (Plan: Free)
Version                       3.x.x
Region                        Asia Pacific (ap)
Latency                       -
Web Interface                 http://127.0.0.1:4040
Forwarding                    https://xxxx-xxx-xxx.ngrok-free.app -> http://localhost:8000

Connections                   ttl     opn     rt1     rt5     p50     p90
                              0       0       0.00    0.00    0.00    0.00
```

**여기서 중요한 부분:**
- `Forwarding` 줄을 보세요!
- `https://xxxx-xxx-xxx.ngrok-free.app` ← **이게 공개 URL입니다!**
- 이 URL을 복사해서 사용하세요.

**예시:**
```
Forwarding   https://abc123-def456.ngrok-free.app -> http://localhost:8000
```
→ `https://abc123-def456.ngrok-free.app` 이 부분을 복사하세요!

### 방법 2: 웹 인터페이스에서 확인 (더 편함)

NGROK을 실행하면 자동으로 웹 인터페이스가 열립니다:
- 주소: **http://localhost:4040** 또는 **http://127.0.0.1:4040**
- 브라우저에서 이 주소를 열면 NGROK 대시보드가 나타납니다
- 여기서 Forwarding URL을 쉽게 확인하고 복사할 수 있습니다

**웹 인터페이스가 자동으로 안 열리면:**
1. 브라우저를 엽니다
2. 주소창에 `http://localhost:4040` 입력
3. Enter 키 누르기
4. 화면에서 Forwarding URL 확인

### 방법 3: NGROK API로 확인 (고급)

터미널에서:
```powershell
curl http://localhost:4040/api/tunnels
```

또는 브라우저에서:
```
http://localhost:4040/api/tunnels
```

JSON 형식으로 URL 정보를 받을 수 있습니다.

---

**💡 팁:**
- NGROK 창이 너무 작으면 창을 크게 늘려서 보세요
- `Forwarding` 줄은 보통 화면 상단에 있습니다
- URL은 매번 실행할 때마다 달라질 수 있습니다 (무료 계정의 경우)

## 주의사항

1. **Django ALLOWED_HOSTS 설정**: 
   - `config/settings.py`에 ngrok 도메인이 이미 포함되어 있습니다
   - 새로운 ngrok URL이 생성되면 환경 변수나 settings.py에 추가해야 할 수 있습니다

2. **CSRF_TRUSTED_ORIGINS**:
   - ngrok URL을 CSRF 허용 목록에 추가해야 할 수 있습니다
   - 예: `CSRF_TRUSTED_ORIGINS = ['https://xxxx-xxx-xxx.ngrok-free.app']`

3. **무료 계정 제한**:
   - ngrok 무료 계정은 매번 다른 URL이 생성됩니다
   - 고정 URL을 원하면 유료 플랜 사용 필요

## 문제 해결

### "ngrok.exe를 찾을 수 없습니다" 오류
```powershell
# ngrok 재설치
powershell -ExecutionPolicy Bypass -File setup_ngrok_simple.ps1
```

### 포트 8000이 이미 사용 중인 경우
다른 포트 사용:
```powershell
# Django 서버를 8001 포트로 실행
python manage.py runserver 8001

# ngrok도 해당 포트로 터널링
.\ngrok\ngrok.exe http 8001
```
