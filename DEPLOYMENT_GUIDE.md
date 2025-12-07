# 🚀 실제 서버 배포 가이드

로컬 개발 환경(`http://127.0.0.1:8000`)이 아닌 실제 인터넷에서 접속 가능한 서버로 배포하는 방법입니다.

## 📋 배포 전 체크리스트

- [ ] 프로덕션 환경 변수 설정 (`.env` 파일 또는 배포 플랫폼 환경 변수)
- [ ] `DEBUG = False` 설정
- [ ] `ALLOWED_HOSTS`에 배포 도메인 추가
- [ ] `SECRET_KEY` 환경 변수로 관리
- [ ] 데이터베이스 마이그레이션 완료
- [ ] 정적 파일 수집 (`collectstatic`)
- [ ] 카카오 개발자 콘솔에 배포 도메인 등록

---

## 🎯 배포 옵션 비교

### 1. **Railway** (추천 ⭐ - 가장 쉬움)
- ✅ 무료 플랜 제공
- ✅ 자동 HTTPS
- ✅ GitHub 연동 쉬움
- ✅ Oracle DB 연결 가능
- 💰 무료 플랜 있음, 유료는 $5/월부터
- 🔗 https://railway.app

### 2. **Render**
- ✅ 무료 플랜 제공
- ✅ 자동 배포
- ⚠️ 무료 플랜은 일정 시간 후 sleep
- 🔗 https://render.com

### 3. **AWS / GCP / Azure**
- ✅ 확장성 높음
- ✅ 많은 기능
- ⚠️ 설정 복잡, 비용 관리 필요
- 💰 사용량 기반 과금
- 🔗 AWS: https://aws.amazon.com

### 4. **자체 서버 (VPS)**
- ✅ 완전한 제어권
- ✅ Oracle DB 직접 연결 가능
- ⚠️ 서버 관리 필요
- 💰 월 $5~20 정도

---

## 🔧 Railway로 배포하기 (단계별 가이드)

### 1단계: 프로젝트 준비

#### 1-1. settings.py 프로덕션 설정 확인

현재 `settings.py`는 환경 변수를 통해 프로덕션/개발 환경을 자동으로 구분합니다:
- `DEBUG`: 환경 변수 `DJANGO_DEBUG` (기본값: `True`)
- `ALLOWED_HOSTS`: 환경 변수 `ALLOWED_HOSTS` (쉼표로 구분)

#### 1-2. requirements.txt 확인

필요한 패키지가 모두 포함되어 있는지 확인:
```bash
pip freeze > requirements.txt
```

필수 패키지:
- `gunicorn` - 프로덕션 서버
- `whitenoise` - 정적 파일 서빙 (선택사항)

#### 1-3. Procfile 생성

프로젝트 루트에 `Procfile` 파일 생성 (확장자 없음):
```
web: gunicorn config.wsgi:application --bind 0.0.0.0:$PORT
```

### 2단계: Railway 가입 및 프로젝트 생성

1. https://railway.app 접속
2. GitHub 계정으로 로그인
3. "New Project" 클릭
4. "Deploy from GitHub repo" 선택
5. GitHub 저장소 연결 및 선택

### 3단계: 환경 변수 설정

Railway 대시보드에서 "Variables" 탭으로 이동하여 다음 환경 변수 추가:

```bash
# Django 필수 설정
DJANGO_SECRET_KEY=your-secret-key-here
DJANGO_DEBUG=False
ALLOWED_HOSTS=your-app.railway.app,yourdomain.com

# 카카오 API
KAKAO_REST_API_KEY=your-kakao-rest-api-key
KAKAO_JS_KEY=your-kakao-js-key

# OpenAI API
OPENAI_API_KEY=your-openai-api-key

# Oracle 데이터베이스 (원격 DB 사용 시)
USE_ORACLE=true
ORACLE_HOST=project-db-campus.smhrd.com
ORACLE_PORT=1524
ORACLE_USER=campus_24K_LG3_DX7_p3_4
ORACLE_PASSWORD=your-db-password
ORACLE_SID=xe
```

**SECRET_KEY 생성 방법:**
```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

### 4단계: 빌드 및 시작 명령어 설정

Railway 대시보드에서 "Settings" → "Deploy" 섹션:

**Build Command:**
```bash
pip install -r requirements.txt && python manage.py collectstatic --noinput
```

**Start Command:**
```bash
gunicorn config.wsgi:application --bind 0.0.0.0:$PORT
```

또는 Procfile을 사용하면 자동으로 감지됩니다.

### 5단계: 도메인 설정

1. Railway 대시보드에서 "Settings" → "Networking"
2. "Generate Domain" 클릭 (예: `your-app.up.railway.app`)
3. 또는 구매한 도메인 연결 가능

### 6단계: 배포 확인

1. Railway 대시보드에서 "Deployments" 탭 확인
2. 배포 완료 후 생성된 도메인으로 접속 테스트
3. 로그 확인: "Deployments" → "View Logs"

---

## 🌐 카카오 개발자 콘솔 설정

배포된 도메인을 카카오 API에 등록해야 합니다.

### 1. 플랫폼 등록
1. https://developers.kakao.com 접속
2. 내 애플리케이션 선택
3. "앱 설정" → "플랫폼" → "Web 플랫폼 등록"
4. 배포된 도메인 추가:
   - 사이트 도메인: `https://your-app.railway.app`
   - Redirect URI: `https://your-app.railway.app/oauth/callback` (필요시)

### 2. JavaScript 키 확인
- "앱 키" 탭에서 JavaScript 키 확인
- Railway 환경 변수 `KAKAO_JS_KEY`에 입력

---

## 🖥️ 자체 서버 (VPS) 배포하기

### 1. 서버 준비
- Ubuntu 20.04 이상 권장
- Python 3.9 이상 설치
- Nginx 설치 (웹 서버)

### 2. 프로젝트 배포

```bash
# 서버에 접속
ssh user@your-server-ip

# 프로젝트 클론
git clone https://github.com/your-username/your-repo.git
cd your-repo

# 가상환경 생성 및 활성화
python3 -m venv venv
source venv/bin/activate

# 의존성 설치
pip install -r requirements.txt

# 환경 변수 설정 (.env 파일 생성)
nano .env
# 필요한 환경 변수 입력

# 데이터베이스 마이그레이션
python manage.py migrate

# 정적 파일 수집
python manage.py collectstatic --noinput

# 관리자 계정 생성
python manage.py createsuperuser
```

### 3. Gunicorn으로 서버 실행

```bash
# Gunicorn 설치
pip install gunicorn

# Gunicorn 실행 (테스트)
gunicorn config.wsgi:application --bind 0.0.0.0:8000

# Systemd 서비스로 등록 (백그라운드 실행)
sudo nano /etc/systemd/system/gunicorn.service
```

**gunicorn.service 파일 내용:**
```ini
[Unit]
Description=gunicorn daemon
After=network.target

[Service]
User=your-username
Group=www-data
WorkingDirectory=/path/to/your/project
ExecStart=/path/to/venv/bin/gunicorn config.wsgi:application --bind 127.0.0.1:8000

[Install]
WantedBy=multi-user.target
```

```bash
# 서비스 시작
sudo systemctl start gunicorn
sudo systemctl enable gunicorn
```

### 4. Nginx 설정

```bash
sudo nano /etc/nginx/sites-available/your-project
```

**Nginx 설정 파일 내용:**
```nginx
server {
    listen 80;
    server_name your-domain.com;

    location /static/ {
        alias /path/to/your/project/staticfiles/;
    }

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

```bash
# 심볼릭 링크 생성
sudo ln -s /etc/nginx/sites-available/your-project /etc/nginx/sites-enabled/

# Nginx 재시작
sudo nginx -t
sudo systemctl restart nginx
```

### 5. SSL 인증서 설정 (HTTPS)

```bash
# Certbot 설치
sudo apt install certbot python3-certbot-nginx

# SSL 인증서 발급
sudo certbot --nginx -d your-domain.com
```

---

## ⚙️ 프로덕션 설정 자동화

현재 `settings.py`는 환경 변수를 통해 자동으로 프로덕션/개발 환경을 구분합니다:

```python
# 환경 변수로 제어
DEBUG = os.environ.get('DJANGO_DEBUG', 'True').lower() == 'true'
ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',')
```

**프로덕션 환경 변수 예시:**
```bash
DJANGO_DEBUG=False
ALLOWED_HOSTS=your-app.railway.app,yourdomain.com
```

---

## 🔒 보안 체크리스트

- [ ] `DEBUG = False` 설정
- [ ] `SECRET_KEY` 환경 변수로 관리 (코드에 하드코딩 금지)
- [ ] `ALLOWED_HOSTS`에 허용된 도메인만 추가
- [ ] `.env` 파일을 `.gitignore`에 추가
- [ ] HTTPS 사용 (대부분 플랫폼 자동 제공)
- [ ] API 키는 환경 변수로 관리
- [ ] 데이터베이스 비밀번호 보안 관리

---

## 🐛 문제 해결

### 정적 파일이 로드되지 않을 때
```bash
python manage.py collectstatic --noinput
```

### 데이터베이스 연결 오류
- Oracle DB의 경우 방화벽 설정 확인
- 환경 변수 `USE_ORACLE=true` 설정 확인
- Oracle Instant Client 경로 확인 (로컬에서만 필요, 서버에서는 Thin 모드 사용)

### 500 에러 발생 시
- Railway/Render 로그 확인
- `DEBUG=True`로 임시 설정하여 에러 메시지 확인
- 환경 변수 설정 확인

### 카카오 로그인 오류
- 카카오 개발자 콘솔에 배포 도메인 등록 확인
- `KAKAO_JS_KEY` 환경 변수 확인

---

## 📚 추가 자료

- Railway 문서: https://docs.railway.app
- Django 배포 가이드: https://docs.djangoproject.com/en/stable/howto/deployment/
- Gunicorn 문서: https://gunicorn.org/
- Nginx 문서: https://nginx.org/en/docs/

---

## 💡 빠른 시작 (Railway CLI)

```bash
# 1. Railway CLI 설치
npm i -g @railway/cli

# 2. 로그인
railway login

# 3. 프로젝트 초기화
railway init

# 4. 환경 변수 설정
railway variables set DJANGO_SECRET_KEY=your-key
railway variables set DJANGO_DEBUG=False
railway variables set ALLOWED_HOSTS=your-app.railway.app

# 5. 배포
railway up
```

---

## 🎯 다음 단계

배포 완료 후:
1. 도메인 연결 (선택사항)
2. 모니터링 설정
3. 백업 자동화
4. CI/CD 파이프라인 구축

