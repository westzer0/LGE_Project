# LG 가전 패키지 추천 시스템

LG 가전 제품을 사용자 취향에 맞게 추천하는 AI 기반 추천 시스템입니다.

## 📋 프로젝트 개요

이 프로젝트는 사용자의 온보딩 설문을 기반으로 최적의 가전 제품 포트폴리오를 추천하는 시스템입니다.

### 주요 기능

- 🎯 **온보딩 설문**: 5단계 설문을 통한 사용자 취향 파악
- 🤖 **AI 기반 추천**: 다중 추천 엔진을 통한 맞춤형 제품 추천
- 📊 **포트폴리오 관리**: 추천 결과 저장 및 공유
- 🔍 **제품 비교**: 제품 간 상세 비교 기능
- 💬 **카카오 연동**: 카카오 로그인 및 메시지 전송
- 🎨 **Figma 연동**: Figma 디자인을 코드로 변환

### 기술 스택

**백엔드**
- Django 5.2.8
- Django REST Framework
- SQLite (개발) / Oracle (프로덕션)
- Python 3.x

**프론트엔드**
- React 18.2.0
- Vite 5.0.8
- Tailwind CSS 3.3.6
- React Router 6.20.0

**외부 서비스**
- OpenAI ChatGPT API
- 카카오 API (인증, 메시지)
- Figma MCP 서버

## 🚀 빠른 시작

### 사전 요구사항

- Python 3.8 이상
- Node.js 18 이상 (권장: v24.11.1)
- PostgreSQL 또는 Oracle (프로덕션)
- Git

### 설치 방법

1. **저장소 클론**
```bash
git clone <repository-url>
cd LGE_Project-main
```

2. **Python 가상환경 설정**
```bash
# 가상환경 생성
python -m venv venv

# 가상환경 활성화
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate

# 의존성 설치
pip install -r requirements.txt
```

3. **Node.js 의존성 설치**
```bash
npm install
```

4. **환경 변수 설정**
```bash
# env.example을 참고하여 .env 파일 생성
cp env.example .env

# .env 파일 편집하여 실제 API 키 입력
# - DJANGO_SECRET_KEY
# - KAKAO_REST_API_KEY, KAKAO_JS_KEY
# - OPENAI_API_KEY
# - Oracle DB 설정 (선택)
```

5. **데이터베이스 마이그레이션**
```bash
python manage.py migrate
```

6. **서버 실행**

**Django 서버 (터미널 1)**
```bash
python manage.py runserver 8000
```

**React 개발 서버 (터미널 2)**
```bash
npm run dev
```

**ngrok 터널 (카카오 API 연동 시 필요, 터미널 3)**
```bash
ngrok\ngrok.exe http 8000
```

### 접속 URL

- React 앱: http://localhost:3000
- Django API: http://localhost:8000
- Django Admin: http://localhost:8000/admin

## 📁 프로젝트 구조

```
LGE_Project-main/
├── api/                    # Django 앱
│   ├── models.py          # 데이터 모델
│   ├── views.py           # 뷰 로직
│   ├── views_drf.py       # DRF API 뷰
│   ├── services/          # 비즈니스 서비스 레이어
│   ├── db/                # 데이터베이스 스크립트
│   ├── utils/             # 유틸리티 함수
│   └── templates/         # HTML 템플릿
├── config/                # Django 설정
│   ├── settings.py
│   └── urls.py
├── src/                   # React 프론트엔드
│   ├── pages/             # 페이지 컴포넌트
│   ├── components/        # 재사용 컴포넌트
│   └── utils/             # 유틸리티
├── data/                  # 데이터 파일 (CSV, 이미지)
├── scripts/               # 유틸리티 스크립트
└── docs/                  # 문서
```

## 🔧 주요 명령어

### Django

```bash
# 서버 실행
python manage.py runserver 8000

# 마이그레이션 생성
python manage.py makemigrations

# 마이그레이션 적용
python manage.py migrate

# 관리자 계정 생성
python manage.py createsuperuser

# 데이터 로드 (커스텀 명령어)
python manage.py load_products
python manage.py load_reviews
```

### React

```bash
# 개발 서버 실행
npm run dev

# 프로덕션 빌드
npm run build

# 빌드 미리보기
npm run preview
```

### 배포

```bash
# Railway 배포
bash railway_deploy.sh

# Docker 빌드
docker build -t lge-project .

# Docker 실행
docker run -p 8000:8000 lge-project
```

## 📚 API 문서

자세한 API 문서는 [API_DOCUMENTATION.md](./docs/API_DOCUMENTATION.md)를 참고하세요.

### 주요 API 엔드포인트

- `POST /api/recommend/` - 제품 추천
- `GET /api/products/` - 제품 목록 조회
- `POST /api/onboarding/complete/` - 온보딩 완료
- `GET /api/portfolio/{id}/` - 포트폴리오 조회
- `POST /api/portfolio/save/` - 포트폴리오 저장
- `GET /api/products/compare/` - 제품 비교

## 🗄️ 데이터베이스

### 개발 환경 (SQLite)
기본적으로 SQLite를 사용합니다. `db.sqlite3` 파일이 자동으로 생성됩니다.

### 프로덕션 환경 (Oracle)
`.env` 파일에 다음 설정을 추가하세요:
```env
USE_ORACLE=true
ORACLE_USER=your_user
ORACLE_PASSWORD=your_password
ORACLE_HOST=your_host
ORACLE_PORT=1524
ORACLE_SID=xe
```

## 🔐 환경 변수

필수 환경 변수:
- `DJANGO_SECRET_KEY`: Django 시크릿 키
- `KAKAO_REST_API_KEY`: 카카오 REST API 키
- `KAKAO_JS_KEY`: 카카오 JavaScript 키
- `OPENAI_API_KEY`: OpenAI API 키

선택 환경 변수:
- `USE_ORACLE`: Oracle DB 사용 여부 (true/false)
- `DJANGO_DEBUG`: 디버그 모드 (true/false)
- `ALLOWED_HOSTS`: 허용된 호스트 (쉼표로 구분)

자세한 내용은 `env.example` 파일을 참고하세요.

## 🧪 테스트

```bash
# Django 테스트
python manage.py test

# 특정 앱 테스트
python manage.py test api
```

## 📖 추가 문서

- [로컬 환경 설정 가이드](./LOCAL_ENV_PROMPT.md)
- [React 프론트엔드 설정](./README_REACT_SETUP.md)
- [API 문서](./docs/API_DOCUMENTATION.md) (작성 예정)

## 🚢 배포

### Railway
```bash
bash railway_deploy.sh
```

### Render
`render.yaml` 파일을 사용하여 자동 배포 가능합니다.

### Fly.io
```bash
flyctl deploy
```

### Docker
```bash
docker build -t lge-project .
docker run -p 8000:8000 --env-file .env lge-project
```

## 🤝 기여하기

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📝 라이선스

이 프로젝트는 비공개 프로젝트입니다.

## 📞 문의

프로젝트 관련 문의사항이 있으시면 이슈를 등록해주세요.

## 🙏 감사의 말

- LG전자
- OpenAI
- 카카오

---

**마지막 업데이트**: 2024년 12월

