# 💰 무료 배포 옵션 가이드

Railway 대신 사용할 수 있는 **완전 무료** 배포 플랫폼들입니다.

---

## 🥇 1. Render (추천 ⭐ - 가장 쉬움)

### 장점
- ✅ **완전 무료** (무료 플랜 제공)
- ✅ GitHub 연동 자동 배포
- ✅ 자동 HTTPS
- ✅ PostgreSQL 무료 제공
- ✅ 설정 간단

### 단점
- ⚠️ 무료 플랜은 15분 비활성 시 sleep (첫 요청 시 깨어남)
- ⚠️ Oracle DB는 직접 연결 필요 (외부 DB 사용)

### 가격
- **무료**: 무제한
- 유료: $7/월부터 (sleep 없음)

### 배포 방법
1. https://render.com 가입 (GitHub 연동)
2. "New +" → "Web Service"
3. GitHub 저장소 선택: `westzer0/LGE_Project`
4. 설정:
   - **Build Command**: `pip install -r requirements.txt && python manage.py collectstatic --noinput`
   - **Start Command**: `gunicorn config.wsgi:application --bind 0.0.0.0:$PORT`
5. 환경 변수 추가 (Railway와 동일)
6. 배포 완료!

### 도메인
- 자동 생성: `your-app.onrender.com`
- 커스텀 도메인 무료 지원

---

## 🥈 2. Fly.io (추천 ⭐⭐)

### 장점
- ✅ **완전 무료** (무료 플랜)
- ✅ Sleep 없음 (항상 실행)
- ✅ 전 세계 CDN
- ✅ Docker 기반 (유연함)

### 단점
- ⚠️ 설정이 조금 복잡 (Dockerfile 필요)
- ⚠️ CLI 사용 필요

### 가격
- **무료**: 월 3개 VM, 160GB 네트워크
- 유료: 사용량 기반

### 배포 방법
```bash
# 1. Fly.io CLI 설치
powershell -Command "iwr https://fly.io/install.ps1 -useb | iex"

# 2. 로그인
fly auth login

# 3. 프로젝트 초기화
fly launch

# 4. 배포
fly deploy
```

---

## 🥉 3. PythonAnywhere

### 장점
- ✅ **완전 무료** (무료 계정)
- ✅ Python 전용 (Django 최적화)
- ✅ 간단한 웹 인터페이스
- ✅ MySQL 무료 제공

### 단점
- ⚠️ 무료 플랜은 하위 도메인만 가능 (`yourusername.pythonanywhere.com`)
- ⚠️ Oracle DB는 직접 연결 필요
- ⚠️ 일일 배포 제한 (무료 플랜)

### 가격
- **무료**: 제한적이지만 사용 가능
- 유료: $5/월부터

### 배포 방법
1. https://www.pythonanywhere.com 가입
2. "Web" 탭 → "Add a new web app"
3. Django 선택
4. GitHub에서 코드 클론
5. 가상환경 설정 및 의존성 설치
6. WSGI 설정
7. 배포 완료!

---

## 🚀 4. Oracle Cloud Free Tier (자체 서버)

### 장점
- ✅ **완전 무료** (평생 무료)
- ✅ 완전한 제어권
- ✅ Oracle DB 직접 설치 가능
- ✅ 2개 VM 무료 (영구)

### 단점
- ⚠️ 서버 관리 필요
- ⚠️ 설정 복잡
- ⚠️ 신용카드 필요 (과금 안 됨)

### 가격
- **무료**: 평생 무료 (제한적 리소스)

### 배포 방법
1. https://www.oracle.com/cloud/free/ 가입
2. VM 인스턴스 생성 (Ubuntu)
3. SSH 접속
4. Django 설치 및 배포
5. Nginx + Gunicorn 설정

---

## 📊 비교표

| 플랫폼 | 무료 여부 | Sleep | 설정 난이도 | 추천도 |
|--------|----------|-------|------------|--------|
| **Render** | ✅ | 있음 | ⭐ 쉬움 | ⭐⭐⭐⭐⭐ |
| **Fly.io** | ✅ | 없음 | ⭐⭐ 보통 | ⭐⭐⭐⭐ |
| **PythonAnywhere** | ✅ | 없음 | ⭐⭐ 보통 | ⭐⭐⭐ |
| **Oracle Cloud** | ✅ | 없음 | ⭐⭐⭐ 어려움 | ⭐⭐⭐ |

---

## 🎯 추천: Render로 바로 시작하기

가장 간단하고 빠르게 배포할 수 있습니다!

### Render 배포 준비 파일 생성

Render용 설정 파일을 만들어드릴까요?

