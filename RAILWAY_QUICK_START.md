# 🚂 Railway 빠른 배포 가이드

## 1단계: GitHub에 푸시 (완료됨 ✅)

프로젝트가 이미 GitHub에 푸시되어 있습니다: `westzer0/LGE_Project`

## 2단계: Railway에서 프로젝트 생성

1. **Railway 접속**: https://railway.app
2. **"New Project"** 클릭
3. **"Deploy from GitHub repo"** 선택
4. GitHub 저장소 선택: `westzer0/LGE_Project`

## 3단계: 환경 변수 설정 (중요!)

Railway 대시보드 → 프로젝트 → **"Variables"** 탭에서 다음 환경 변수 추가:

```bash
# Django 필수
DJANGO_SECRET_KEY=여기에-시크릿-키-입력
DJANGO_DEBUG=False
ALLOWED_HOSTS=your-app.railway.app

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

### SECRET_KEY 생성 방법:
```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

## 4단계: 배포 설정 확인

Railway 대시보드 → **"Settings"** → **"Deploy"**:

- **Build Command**: (자동 감지됨)
- **Start Command**: (Procfile 자동 감지됨)

## 5단계: 배포 완료!

1. Railway가 자동으로 배포 시작
2. **"Deployments"** 탭에서 진행 상황 확인
3. 배포 완료 후 생성된 도메인으로 접속 테스트

## 🔧 문제 해결

### 저장소가 안 보일 때:
- Railway Settings → Connected Accounts → GitHub 재연결
- "All repositories" 권한 허용

### 배포 실패 시:
- **"View Logs"**에서 에러 확인
- 환경 변수 설정 확인
- `requirements.txt` 확인

### 정적 파일이 안 보일 때:
- Railway에서 자동으로 `collectstatic` 실행됨
- 문제 시: Settings → Build Command에 `python manage.py collectstatic --noinput` 추가

## 📝 체크리스트

- [x] Procfile 생성됨
- [x] requirements.txt 업데이트됨
- [x] settings.py 프로덕션 설정 완료
- [ ] Railway 환경 변수 설정
- [ ] 배포 완료 확인
- [ ] 카카오 개발자 콘솔에 도메인 등록

## 🎯 배포 후 해야 할 일

1. **카카오 개발자 콘솔**
   - https://developers.kakao.com
   - 플랫폼 → Web 플랫폼 등록
   - 배포된 도메인 추가

2. **도메인 확인**
   - Railway → Settings → Networking
   - 생성된 도메인 확인 (예: `your-app.up.railway.app`)

3. **테스트**
   - 배포된 URL로 접속
   - 모든 기능 테스트

