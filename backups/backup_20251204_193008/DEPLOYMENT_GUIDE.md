# 배포 가이드 - 실제 도메인으로 서버 운영하기

## 🚀 배포 옵션

로컬호스트(`http://127.0.0.1:8000`) 대신 실제 도메인으로 서비스하려면 다음과 같은 방법이 있습니다:

### 1. **Railway** (추천 - 가장 쉬움) ⭐
- **장점**: 무료 플랜, 자동 HTTPS, GitHub 연동 쉬움
- **단점**: 무료 플랜은 제한적
- **가격**: 무료 플랜 있음, 유료는 $5/월부터
- **URL**: https://railway.app

### 2. **Render**
- **장점**: 무료 플랜, 자동 배포
- **단점**: 무료 플랜은 일정 시간 후 sleep
- **가격**: 무료 플랜 있음
- **URL**: https://render.com

### 3. **Heroku**
- **장점**: 사용하기 쉬움
- **단점**: 무료 플랜 종료됨
- **가격**: $7/월부터
- **URL**: https://www.heroku.com

### 4. **AWS / GCP / Azure**
- **장점**: 확장성, 많은 기능
- **단점**: 설정 복잡, 비용 관리 필요
- **가격**: 사용량 기반
- **추천**: 프로덕션 환경에서 사용

## 📋 배포 전 준비사항

### 1. 도메인 구매 (선택사항)
- **국내**: 가비아 (https://www.gabia.com), 후이즈 (https://whois.co.kr)
- **해외**: Namecheap (https://www.namecheap.com), GoDaddy (https://www.godaddy.com)
- **가격**: 연간 1만원~2만원 정도

### 2. 프로젝트 설정 변경

#### settings.py 수정 필요
```python
# DEBUG 모드 끄기
DEBUG = False

# ALLOWED_HOSTS에 도메인 추가
ALLOWED_HOSTS = ['your-domain.com', 'www.your-domain.com', 'your-app.railway.app']

# 환경 변수에서 SECRET_KEY 가져오기
SECRET_KEY = os.environ.get('SECRET_KEY', 'fallback-key')

# 정적 파일 설정 (CSS, JS)
STATIC_ROOT = BASE_DIR / 'staticfiles'

# 데이터베이스 설정 (배포 환경용)
# PostgreSQL 사용 권장
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('DB_NAME'),
        'USER': os.environ.get('DB_USER'),
        'PASSWORD': os.environ.get('DB_PASSWORD'),
        'HOST': os.environ.get('DB_HOST'),
        'PORT': os.environ.get('DB_PORT', '5432'),
    }
}
```

#### .env 파일 생성 (로컬에서만 사용)
```
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
```

## 🔧 Railway로 배포하기 (가장 쉬운 방법)

### 1단계: Railway 가입
1. https://railway.app 접속
2. GitHub 계정으로 로그인

### 2단계: 새 프로젝트 생성
1. "New Project" 클릭
2. "Deploy from GitHub repo" 선택
3. GitHub 저장소 연결

### 3단계: 환경 변수 설정
Railway 대시보드에서 환경 변수 추가:
```
SECRET_KEY=your-secret-key
DEBUG=False
KAKAO_REST_API_KEY=your-key
KAKAO_JS_KEY=your-key
OPENAI_API_KEY=your-key
ALLOWED_HOSTS=your-app.railway.app
```

### 4단계: requirements.txt 확인
```
Django==4.2.17
python-dotenv>=1.0.0
openai>=1.0.0
gunicorn>=21.0.0  # 서버 실행용
whitenoise>=6.0.0  # 정적 파일 서빙
```

### 5단계: Procfile 생성 (프로젝트 루트)
```
web: gunicorn config.wsgi:application
```

### 6단계: Railway 설정
- Build Command: `pip install -r requirements.txt && python manage.py collectstatic --noinput`
- Start Command: (Procfile 사용 시 자동 감지)

### 7단계: 도메인 연결 (선택사항)
1. Railway 대시보드에서 "Settings" → "Networking"
2. "Generate Domain" 클릭 (예: `your-app.up.railway.app`)
3. 또는 구매한 도메인 연결 가능

## 🌐 카카오 개발자 콘솔 설정

### 도메인 등록 필요
1. https://developers.kakao.com 접속
2. 내 애플리케이션 선택
3. "플랫폼" → "Web 플랫폼 등록"
4. 배포된 도메인 추가 (예: `https://your-app.railway.app`)

### 사이트 도메인 설정
- 개발 환경: `http://127.0.0.1:8000`
- 배포 환경: `https://your-app.railway.app`

## 📝 배포 체크리스트

- [ ] `DEBUG = False` 설정
- [ ] `ALLOWED_HOSTS` 설정
- [ ] `SECRET_KEY` 환경 변수로 관리
- [ ] `.env` 파일을 Git에 올리지 않음 (`.gitignore` 확인)
- [ ] 데이터베이스 마이그레이션 (`python manage.py migrate`)
- [ ] 정적 파일 수집 (`python manage.py collectstatic`)
- [ ] 카카오 개발자 콘솔에 배포 도메인 등록
- [ ] HTTPS 사용 (대부분 플랫폼 자동 제공)

## 🔗 공유 URL 변경

배포 후 포트폴리오 URL은 다음과 같이 변경됩니다:
- **로컬**: `http://127.0.0.1:8000/portfolio/PF-JW650Y/`
- **배포**: `https://your-app.railway.app/portfolio/PF-JW650Y/`

코드 변경은 필요 없습니다. `window.location.origin`이 자동으로 올바른 도메인을 사용합니다.

## ⚠️ 주의사항

1. **환경 변수 보안**: API 키는 절대 코드에 직접 입력하지 마세요
2. **데이터베이스 백업**: 배포 전 데이터 백업
3. **로컬 테스트**: 배포 전 로컬에서 충분히 테스트
4. **비용 관리**: 무료 플랜 제한 확인

## 🎯 빠른 시작 (Railway)

```bash
# 1. Railway CLI 설치
npm i -g @railway/cli

# 2. 로그인
railway login

# 3. 프로젝트 초기화
railway init

# 4. 배포
railway up
```

## 📚 추가 자료

- Railway 문서: https://docs.railway.app
- Django 배포 가이드: https://docs.djangoproject.com/en/stable/howto/deployment/
- 카카오 개발자 가이드: https://developers.kakao.com/docs

