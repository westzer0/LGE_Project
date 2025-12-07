# 🎨 Render 배포 가이드 (완전 무료!)

Railway보다 훨씬 간단하고 무료로 배포할 수 있습니다.

## 🚀 5분 안에 배포하기

### 1단계: Render 가입
1. https://render.com 접속
2. "Get Started for Free" 클릭
3. **GitHub 계정으로 로그인** (가장 쉬움)

### 2단계: 새 Web Service 생성
1. 대시보드에서 **"New +"** 클릭
2. **"Web Service"** 선택
3. GitHub 저장소 연결:
   - "Connect account" (처음이면)
   - 저장소 선택: `westzer0/LGE_Project`
   - "Connect" 클릭

### 3단계: 서비스 설정

#### 기본 설정
- **Name**: `lge-project` (원하는 이름)
- **Region**: `Singapore` (한국과 가까움)
- **Branch**: `main`
- **Root Directory**: (비워두기)

#### 빌드 및 시작 명령어
- **Build Command**: 
  ```bash
  pip install -r requirements.txt && python manage.py collectstatic --noinput
  ```
- **Start Command**:
  ```bash
  gunicorn config.wsgi:application --bind 0.0.0.0:$PORT
  ```

#### 인스턴스 타입
- **Free** 선택 (무료)

### 4단계: 환경 변수 설정

"Environment" 섹션에서 다음 환경 변수 추가:

```bash
# Django 필수
DJANGO_SECRET_KEY=여기에-시크릿-키-입력
DJANGO_DEBUG=False
ALLOWED_HOSTS=your-app.onrender.com

# 카카오 API
KAKAO_REST_API_KEY=카카오-REST-API-키
KAKAO_JS_KEY=카카오-JavaScript-키

# OpenAI API
OPENAI_API_KEY=OpenAI-API-키

# Oracle 데이터베이스
USE_ORACLE=true
ORACLE_HOST=project-db-campus.smhrd.com
ORACLE_PORT=1524
ORACLE_USER=campus_24K_LG3_DX7_p3_4
ORACLE_PASSWORD=데이터베이스-비밀번호
ORACLE_SID=xe
```

**SECRET_KEY 생성:**
```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

### 5단계: 배포 시작!

1. **"Create Web Service"** 클릭
2. 자동으로 배포 시작됨
3. 로그에서 진행 상황 확인
4. 배포 완료 후 `https://your-app.onrender.com` 접속!

## ✅ 배포 완료 후

### 도메인 확인
- Render 대시보드에서 생성된 URL 확인
- 예: `https://lge-project.onrender.com`

### 카카오 개발자 콘솔 설정
1. https://developers.kakao.com 접속
2. 플랫폼 → Web 플랫폼 등록
3. 사이트 도메인: `https://your-app.onrender.com`

## ⚠️ 무료 플랜 제한사항

- **Sleep 모드**: 15분간 요청이 없으면 sleep
- 첫 요청 시 깨어나는 데 30초~1분 소요
- **해결책**: 
  - UptimeRobot 같은 무료 서비스로 주기적 핑
  - 또는 유료 플랜 ($7/월)으로 업그레이드

## 🔧 문제 해결

### 배포 실패 시
- "Logs" 탭에서 에러 확인
- 환경 변수 설정 확인
- `requirements.txt` 확인

### 정적 파일이 안 보일 때
- Build Command에 `collectstatic` 포함 확인
- `STATIC_ROOT` 설정 확인

### 데이터베이스 연결 오류
- Oracle DB 방화벽 설정 확인
- 환경 변수 `USE_ORACLE=true` 확인

## 🎯 Render vs Railway

| 항목 | Render | Railway |
|------|--------|---------|
| 무료 플랜 | ✅ | ✅ |
| 설정 난이도 | ⭐ 쉬움 | ⭐⭐ 보통 |
| Sleep 모드 | 있음 | 없음 |
| GitHub 연동 | ✅ | ✅ |
| 자동 HTTPS | ✅ | ✅ |

**결론: Render가 더 간단하고 무료로 사용하기 좋습니다!**

## 📚 추가 자료

- Render 문서: https://render.com/docs
- Django 배포: https://render.com/docs/deploy-django

