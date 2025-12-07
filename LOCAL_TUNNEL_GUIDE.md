# 🚇 로컬 서버를 인터넷에 공개하기 (7일 임시)

로컬에서 실행 중인 서버를 인터넷에서 접속 가능하게 만드는 방법입니다.

## 🎯 방법 1: ngrok (가장 간단 ⭐)

### 장점
- ✅ 5분 안에 설정 완료
- ✅ 무료 플랜 제공
- ✅ HTTPS 자동 제공
- ✅ 7일 사용 충분

### 단점
- ⚠️ 무료 플랜은 URL이 매번 바뀜 (재시작 시)
- ⚠️ ngrok 앱이 실행 중이어야 함

### 설치 및 사용

#### 1단계: ngrok 가입 및 설치
1. https://ngrok.com 가입 (무료)
2. https://ngrok.com/download 다운로드
3. 압축 해제 후 `ngrok.exe` 경로 확인

#### 2단계: 인증 토큰 설정
```powershell
# ngrok.exe가 있는 폴더로 이동
cd C:\path\to\ngrok

# 인증 토큰 설정 (ngrok 대시보드에서 복사)
.\ngrok.exe config add-authtoken YOUR_AUTH_TOKEN
```

#### 3단계: Django 서버 실행
```powershell
# 프로젝트 폴더에서
python manage.py runserver 8000
```

#### 4단계: ngrok 터널 시작
```powershell
# 새 터미널에서
.\ngrok.exe http 8000
```

#### 5단계: 공개 URL 확인
ngrok이 다음과 같은 URL을 제공합니다:
```
Forwarding: https://abc123.ngrok-free.app -> http://localhost:8000
```

이 URL을 카카오 개발자 콘솔에 등록하면 됩니다!

---

## 🎯 방법 2: Cloudflare Tunnel (완전 무료, URL 고정)

### 장점
- ✅ 완전 무료
- ✅ URL 고정 (재시작해도 동일)
- ✅ 무제한 사용

### 단점
- ⚠️ 설정이 조금 더 복잡

### 설치 및 사용

#### 1단계: Cloudflare Tunnel 설치
```powershell
# Chocolatey 사용 (관리자 권한)
choco install cloudflared

# 또는 직접 다운로드
# https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/install-and-setup/installation/
```

#### 2단계: 터널 생성
```powershell
# 로그인
cloudflared tunnel login

# 터널 생성
cloudflared tunnel create lge-project

# 터널 실행
cloudflared tunnel run lge-project
```

#### 3단계: 도메인 연결 (선택사항)
더 나은 URL을 원하면:
```powershell
# 도메인 등록 (Cloudflare 무료 도메인 사용 가능)
cloudflared tunnel route dns lge-project your-subdomain.yourdomain.com
```

---

## 🎯 방법 3: localtunnel (설치 불필요)

### 장점
- ✅ npm만 있으면 됨 (설치 불필요)
- ✅ 완전 무료

### 사용법
```powershell
# npm이 설치되어 있다면
npx localtunnel --port 8000

# 또는 글로벌 설치
npm install -g localtunnel
lt --port 8000
```

---

## 📋 빠른 시작 (ngrok 추천)

### 1. ngrok 다운로드
https://ngrok.com/download → Windows 다운로드

### 2. 가입 및 인증
```powershell
# ngrok.exe 실행
.\ngrok.exe config add-authtoken YOUR_TOKEN
```

### 3. Django 서버 실행
```powershell
python manage.py runserver 8000
```

### 4. ngrok 시작
```powershell
.\ngrok.exe http 8000
```

### 5. URL 복사
```
Forwarding: https://xxxx-xxx-xxx.ngrok-free.app
```

### 6. 카카오 개발자 콘솔 설정
- https://developers.kakao.com
- 플랫폼 → Web 플랫폼 등록
- 사이트 도메인: `https://xxxx-xxx-xxx.ngrok-free.app`

---

## ⚠️ 주의사항

1. **ngrok 무료 플랜 제한**
   - URL이 재시작할 때마다 바뀜
   - 세션 시간 제한 있음 (8시간)
   - 해결: ngrok 계정 업그레이드 또는 Cloudflare Tunnel 사용

2. **로컬 서버가 실행 중이어야 함**
   - 컴퓨터가 꺼지면 접속 불가
   - ngrok도 실행 중이어야 함

3. **방화벽 설정**
   - Windows 방화벽에서 포트 8000 허용 필요할 수 있음

---

## 🔧 자동화 스크립트

### start_tunnel.bat (Windows)
```batch
@echo off
echo Django 서버 시작 중...
start cmd /k "python manage.py runserver 8000"
timeout /t 3
echo ngrok 터널 시작 중...
start cmd /k "ngrok.exe http 8000"
echo 완료! ngrok 창에서 URL 확인하세요.
pause
```

---

## 🎯 추천: ngrok (가장 빠름)

7일만 사용할 거라면 **ngrok**이 가장 간단합니다:
1. 다운로드 2분
2. 가입 1분
3. 실행 1분
4. 끝!

**총 5분 안에 완료!**

