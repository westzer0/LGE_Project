# ⚡ 7일 임시 배포 - 5분 완성!

로컬 서버를 인터넷에 공개하는 가장 빠른 방법입니다.

## 🚀 ngrok 사용 (추천)

### 1단계: ngrok 다운로드 (2분)
1. https://ngrok.com 접속
2. "Sign up" 클릭 (무료 가입)
3. https://ngrok.com/download → Windows 다운로드
4. 압축 해제 (예: `C:\ngrok\ngrok.exe`)

### 2단계: 인증 토큰 설정 (1분)
1. ngrok 대시보드 로그인
2. "Your Authtoken" 복사
3. PowerShell에서:
```powershell
cd C:\ngrok
.\ngrok.exe config add-authtoken YOUR_TOKEN_HERE
```

### 3단계: 실행 (1분)

**방법 A: 자동 스크립트 사용**
```powershell
# 프로젝트 폴더에서
.\start_ngrok.bat
```

**방법 B: 수동 실행**
```powershell
# 터미널 1: Django 서버
python manage.py runserver 8000

# 터미널 2: ngrok (새 터미널)
cd C:\ngrok
.\ngrok.exe http 8000
```

### 4단계: URL 확인
ngrok 창에서 다음과 같은 URL이 보입니다:
```
Forwarding: https://abc123-def456.ngrok-free.app -> http://localhost:8000
```

이 URL을 복사하세요!

### 5단계: 카카오 개발자 콘솔 설정
1. https://developers.kakao.com 접속
2. 내 애플리케이션 선택
3. "앱 설정" → "플랫폼" → "Web 플랫폼 등록"
4. 사이트 도메인: `https://abc123-def456.ngrok-free.app`

## ✅ 완료!

이제 인터넷 어디서나 `https://abc123-def456.ngrok-free.app`로 접속 가능합니다!

## ⚠️ 주의사항

1. **컴퓨터가 켜져 있어야 함**
   - 서버가 실행 중이어야 접속 가능

2. **ngrok도 실행 중이어야 함**
   - ngrok 창을 닫으면 접속 불가

3. **URL이 바뀔 수 있음**
   - ngrok 무료 플랜은 재시작 시 URL 변경
   - 해결: ngrok 계정에서 고정 URL 설정 (유료) 또는 Cloudflare Tunnel 사용

## 🔄 URL이 바뀌었을 때

1. ngrok에서 새 URL 확인
2. 카카오 개발자 콘솔에서 도메인 업데이트
3. 끝!

## 🎯 대안: Cloudflare Tunnel (URL 고정)

URL이 바뀌는 게 싫다면:

```powershell
# Cloudflare Tunnel 설치
choco install cloudflared

# 로그인 및 실행
cloudflared tunnel login
cloudflared tunnel --url http://localhost:8000
```

이 방법은 URL이 고정됩니다!

---

**총 소요 시간: 5분**
**비용: 완전 무료**

