# React 프론트엔드 설정 가이드

## 개요

이 프로젝트는 Django 백엔드와 React 프론트엔드를 함께 사용합니다.
- **Django**: API 서버 (포트 8000)
- **React**: 프론트엔드 앱 (포트 3000)

## 빠른 시작

### 1. 의존성 설치

```bash
# Node.js 패키지 설치
npm install
```

### 2. 개발 서버 실행

**터미널 1: Django 서버**
```bash
python manage.py runserver
```

**터미널 2: React 개발 서버**
```bash
npm run dev
```

### 3. 브라우저 접속

- React 앱: http://localhost:3000
- Django API: http://localhost:8000

## 주요 기능

### 온보딩 플로우
- `/onboarding` - 4단계 설문 (스타일, 가구 정보, 우선순위/예산, 카테고리)
- 설문 완료 후 자동으로 추천 결과 생성

### 결과 페이지
- `/result` - 추천 제품 포트폴리오 표시
- 포트폴리오 ID로 직접 접근 가능: `/result?portfolio_id=xxx`

## API 연결

React 앱은 Vite 프록시를 통해 Django API에 연결됩니다:
- `/api/*` 요청은 자동으로 `http://localhost:8000`으로 프록시됩니다.

### 주요 API 엔드포인트
- `POST /api/onboarding/complete/` - 온보딩 완료 및 추천 생성
- `GET /api/portfolio/{id}/` - 포트폴리오 조회
- `GET /api/products/` - 제품 목록 조회

## CSRF 토큰 처리

React 앱은 자동으로 Django의 CSRF 토큰을 처리합니다:
- `src/utils/api.js`의 `apiRequest` 함수가 자동으로 CSRF 토큰을 포함합니다.
- 컴포넌트 마운트 시 자동으로 토큰을 초기화합니다.

## 프로젝트 구조

```
src/
├── pages/
│   ├── Onboarding.jsx      # 온보딩 플로우
│   └── PortfolioResult.jsx  # 결과 페이지
├── components/
│   └── ProductCard.jsx      # 제품 카드 컴포넌트
├── utils/
│   └── api.js              # API 유틸리티 (CSRF 토큰 처리)
├── App.jsx                 # 메인 앱 (라우터 설정)
└── main.jsx                # 엔트리 포인트
```

## 문제 해결

### CORS 오류
Django 설정(`config/settings.py`)에 다음이 포함되어 있는지 확인:
```python
CSRF_TRUSTED_ORIGINS = ['http://localhost:3000']
```

### CSRF 토큰 오류
- 브라우저 개발자 도구에서 쿠키에 `csrftoken`이 있는지 확인
- Django 서버가 정상적으로 실행 중인지 확인

### API 연결 실패
- Vite 프록시 설정 확인 (`vite.config.js`)
- Django 서버가 포트 8000에서 실행 중인지 확인

## 빌드 및 배포

### 프로덕션 빌드
```bash
npm run build
```

빌드된 파일은 `dist/` 디렉토리에 생성됩니다.

### Django에서 React 앱 서빙 (선택사항)
프로덕션 환경에서는 Django가 React 빌드 파일을 서빙하도록 설정할 수 있습니다.
`config/settings.py`의 `STATICFILES_DIRS`에 `dist/` 디렉토리를 추가하세요.

