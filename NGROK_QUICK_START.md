# PowerShell에서 ngrok 서버 실행하기

## 🚀 가장 빠른 방법 (한 줄 명령어)

PowerShell을 열고 아래 명령어를 **그대로 복사해서 붙여넣기**:

```powershell
cd "c:\Users\134\Desktop\DX Project"; .\ngrok\ngrok.exe http 8000
```

---

## 📋 단계별 실행 방법

### 1단계: PowerShell 열기
- Windows 키 누르기
- "PowerShell" 입력
- "Windows PowerShell" 클릭

### 2단계: 프로젝트 폴더로 이동
```powershell
cd "c:\Users\134\Desktop\DX Project"
```

### 3단계: ngrok 실행
```powershell
.\ngrok\ngrok.exe http 8000
```

---

## ⚠️ 주의사항

### Django 서버가 먼저 실행되어 있어야 합니다!

ngrok은 로컬 서버(8000 포트)를 외부에 공개하는 터널이므로, **Django 서버가 먼저 실행 중이어야 합니다**.

#### Django 서버 실행 방법:

**방법 1: 별도 PowerShell 창에서**
```powershell
cd "c:\Users\134\Desktop\DX Project"
.\venv\Scripts\activate
python manage.py runserver 8000
```

**방법 2: 자동 실행 배치 파일 사용**
```powershell
cd "c:\Users\134\Desktop\DX Project"
.\start_server_fixed.bat
```
(이 파일은 Django 서버와 ngrok을 모두 자동으로 실행합니다)

---

## 🔍 Forwarding URL 확인하기

ngrok이 실행되면 다음과 같은 화면이 나타납니다:

```
Session Status                online
Account                       Your Name (Plan: Free)
Version                       3.x.x
Region                        Asia Pacific (ap)
Latency                       -
Web Interface                 http://127.0.0.1:4040
Forwarding                    https://xxxx-xxx-xxx.ngrok-free.app -> http://localhost:8000
```

**중요:** `Forwarding` 줄의 `https://xxxx-xxx-xxx.ngrok-free.app` 부분이 **공개 URL**입니다!

### URL 확인 방법:

1. **ngrok 창에서 직접 확인** (위의 Forwarding 줄)
2. **웹 인터페이스에서 확인** (브라우저에서 `http://localhost:4040` 열기)

---

## 🎯 전체 실행 순서 (권장)

### 터미널 1 - Django 서버:
```powershell
cd "c:\Users\134\Desktop\DX Project"
.\venv\Scripts\activate
python manage.py runserver 8000
```

### 터미널 2 - ngrok:
```powershell
cd "c:\Users\134\Desktop\DX Project"
.\ngrok\ngrok.exe http 8000
```

---

## 🛠️ 문제 해결

### ❌ "authtoken이 설정되지 않았습니다" 오류 (ERR_NGROK_4018)

**이 오류가 발생하면 아래 순서대로 진행하세요:**

#### 1단계: ngrok 토큰 발급받기
1. 브라우저에서 https://dashboard.ngrok.com/get-started/your-authtoken 접속
2. (회원가입 필요 - 무료)
3. 로그인 후 **"Your Authtoken"** 복사

#### 2단계: PowerShell에서 토큰 설정하기

**방법 1: 자동 스크립트 사용 (권장)**
```powershell
cd "c:\Users\134\Desktop\DX Project"
powershell -ExecutionPolicy Bypass -File set_ngrok_token.ps1
```
(토큰 입력 프롬프트가 나타나면 복사한 토큰을 붙여넣기)

**방법 2: 직접 명령어 입력**
```powershell
cd "c:\Users\134\Desktop\DX Project"
.\ngrok\ngrok.exe config add-authtoken YOUR_AUTH_TOKEN
```
(`YOUR_AUTH_TOKEN` 부분을 실제 토큰으로 교체)

#### 3단계: 설정 확인
```powershell
.\ngrok\ngrok.exe config check
```

#### 4단계: 다시 ngrok 실행
```powershell
.\ngrok\ngrok.exe http 8000
```

---

### "ngrok.exe를 찾을 수 없습니다" 오류
ngrok이 설치되지 않았습니다. 다음 명령어로 설치:
```powershell
cd "c:\Users\134\Desktop\DX Project"
powershell -ExecutionPolicy Bypass -File setup_ngrok_simple.ps1 -Token YOUR_AUTH_TOKEN
```

### "포트 8000이 이미 사용 중입니다" 오류
다른 포트 사용:
```powershell
.\ngrok\ngrok.exe http 8001
```
(Django 서버도 8001 포트로 실행해야 함)

---

## 💡 팁

- **가장 쉬운 방법**: `start_server_fixed.bat` 파일을 더블클릭하면 Django 서버와 ngrok이 모두 자동으로 실행됩니다!
- ngrok 무료 계정은 매번 다른 URL이 생성됩니다
- 고정 URL이 필요하면 ngrok 유료 플랜 사용 필요
