# ngrok 오프라인 오류 해결 방법 (ERR_NGROK_3200)

## 🔴 문제
`ERR_NGROK_3200: The endpoint is offline` 오류는 다음 중 하나일 때 발생합니다:
- ngrok이 실행되지 않음
- Django 서버가 실행되지 않음
- ngrok URL이 변경되었지만 설정이 업데이트되지 않음

---

## ✅ 해결 방법

### 방법 1: 자동 실행 (가장 쉬움)

PowerShell에서:
```powershell
cd "c:\Users\134\Desktop\DX Project"
.\start_server_fixed.bat
```

이 명령어는 Django 서버와 ngrok을 모두 자동으로 실행합니다.

---

### 방법 2: 수동 실행 (2개의 PowerShell 창 필요)

#### 창 1: Django 서버 실행
```powershell
cd "c:\Users\134\Desktop\DX Project"
.\venv\Scripts\activate
python manage.py runserver 8000
```

**확인:** `Starting development server at http://127.0.0.1:8000/` 메시지가 보이면 정상

#### 창 2: ngrok 실행
```powershell
cd "c:\Users\134\Desktop\DX Project"
.\ngrok\ngrok.exe http 8000
```

**확인:** `Forwarding https://xxxx-xxx-xxx.ngrok-free.app -> http://localhost:8000` 메시지가 보이면 정상

---

## 🔍 실행 상태 확인

### Django 서버 확인
브라우저에서 `http://localhost:8000` 접속
- 접속되면 ✅ 정상
- 접속 안 되면 ❌ 서버가 실행되지 않음

### ngrok 확인
1. **ngrok 창에서 확인:**
   - `Session Status: online` 이어야 함
   - `Forwarding` 줄에 URL이 있어야 함

2. **웹 인터페이스에서 확인:**
   - 브라우저에서 `http://localhost:4040` 열기
   - Forwarding URL 확인

---

## ⚠️ 주의사항

### 1. 실행 순서
**반드시 Django 서버를 먼저 실행한 후 ngrok을 실행하세요!**

### 2. URL 변경
ngrok 무료 계정은 **매번 실행할 때마다 URL이 변경**됩니다.
- 새로운 URL을 확인하세요
- 카카오 개발자 콘솔에 새 URL을 등록하세요

### 3. 포트 확인
- Django 서버가 8000 포트에서 실행 중인지 확인
- 다른 포트를 사용하면 ngrok도 같은 포트로 실행

---

## 🛠️ 문제 해결

### "포트 8000이 이미 사용 중입니다"
다른 프로그램이 8000 포트를 사용 중입니다:
```powershell
# 포트 사용 확인
netstat -ano | findstr ":8000"

# 다른 포트 사용 (예: 8001)
python manage.py runserver 8001
.\ngrok\ngrok.exe http 8001
```

### "ngrok이 실행되지 않습니다"
1. ngrok 창이 열려있는지 확인
2. ngrok 토큰이 설정되어 있는지 확인:
   ```powershell
   .\ngrok\ngrok.exe config check
   ```

### "Django 서버가 시작되지 않습니다"
1. 가상환경이 활성화되어 있는지 확인
2. 오류 메시지 확인
3. DB 연결 문제일 수 있음 (DISABLE_DB=true 설정 고려)

---

## 📝 체크리스트

실행 전 확인:
- [ ] 가상환경 활성화됨
- [ ] Django 서버 실행됨 (http://localhost:8000 접속 가능)
- [ ] ngrok 실행됨 (http://localhost:4040 접속 가능)
- [ ] Forwarding URL 확인됨
- [ ] 카카오 개발자 콘솔에 새 URL 등록됨

---

## 💡 팁

**가장 빠른 방법:**
```powershell
.\start_server_fixed.bat
```
이 한 줄이면 Django 서버와 ngrok이 모두 자동으로 실행됩니다!
