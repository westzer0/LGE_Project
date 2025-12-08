# Comet에게 전달할 All-in-One 프롬프트

## 현재 상황 요약

### 1. AI Assistant (Auto)의 현재 상태
- **역할**: Cursor IDE에서 작동하는 AI 코딩 어시스턴트 (Auto)
- **위치**: Windows 10 환경 (PowerShell)
- **작업 공간**: `C:\Users\Tissue\Desktop\LGE_Project-main`
- **상태**: 프로젝트 구조 파악 완료, 사용자의 추가 지시 대기 중

### 2. 프로젝트 개요
**프로젝트명**: LGE_Project-main (LG 가전 패키지 추천 시스템)

**주요 기능**:
- 사용자 온보딩 설문을 통한 가전 제품 추천
- TV/오디오 포트폴리오 추천 엔진
- 카카오 API 연동 (인증, 메시지)
- OpenAI ChatGPT 연동
- Figma MCP 서버 연동
- 제품 비교 및 추천 이유 제공

**기술 스택**:
- **백엔드**: Django 5.2.8 (Python)
- **프론트엔드**: React 18.2.0 + Vite 5.0.8
- **스타일링**: Tailwind CSS 3.3.6
- **데이터베이스**: SQLite (기본) / Oracle (선택적)
- **기타**: ngrok (터널링), Node.js v24.11.1

**프로젝트 구조**:
```
LGE_Project-main/
├── api/                    # Django 앱 (메인 비즈니스 로직)
│   ├── models.py          # 데이터 모델
│   │   ├── Product (제품 정보)
│   │   ├── ProductSpec (제품 스펙 JSON)
│   │   ├── ProductDemographics (제품 인구통계)
│   │   ├── ProductReview (제품 리뷰)
│   │   ├── ProductRecommendReason (추천 이유)
│   │   ├── OnboardingSession (온보딩 세션)
│   │   ├── Portfolio (포트폴리오 추천 결과)
│   │   └── UserSample (사용자 샘플 데이터)
│   ├── views.py           # 뷰 로직
│   ├── views_drf.py       # DRF API 뷰
│   ├── services/          # 비즈니스 서비스 레이어 (22개 서비스)
│   │   ├── recommendation_engine.py
│   │   ├── ai_recommendation_service.py
│   │   ├── taste_based_recommendation_engine.py
│   │   ├── playbook_recommendation_engine.py
│   │   ├── column_based_recommendation_engine.py
│   │   ├── taste_based_product_scorer.py
│   │   ├── taste_scoring_logic_service.py
│   │   ├── taste_calculation_service.py
│   │   ├── playbook_scoring.py
│   │   ├── portfolio_service.py
│   │   ├── product_comparison_service.py
│   │   ├── recommendation_reason_generator.py
│   │   ├── chatgpt_service.py
│   │   ├── kakao_auth_service.py
│   │   ├── kakao_message_service.py
│   │   ├── onboarding_db_service.py
│   │   ├── style_analysis_service.py
│   │   ├── playbook_explanation_generator.py
│   │   ├── playbook_filters.py
│   │   └── figma_to_code_service.py
│   ├── db/                # 데이터베이스 관련 스크립트
│   │   ├── oracle_client.py
│   │   └── [다양한 SQL 스크립트들]
│   ├── utils/             # 유틸리티 함수들
│   ├── scoring_logic/     # 점수 계산 로직 (JSON)
│   ├── migrations/        # Django 마이그레이션
│   ├── management/commands/  # 커스텀 관리 명령어
│   └── templates/         # HTML 템플릿
├── config/                # Django 설정
│   ├── settings.py        # 프로젝트 설정 (Oracle/SQLite 지원)
│   ├── urls.py           # URL 라우팅
│   ├── wsgi.py
│   └── asgi.py
├── src/                   # React 프론트엔드
│   ├── App.jsx
│   ├── main.jsx
│   ├── index.css
│   ├── components/
│   │   ├── ProductCard.jsx
│   │   └── StepIndicator.jsx
│   ├── pages/
│   │   ├── Onboarding.jsx
│   │   ├── PortfolioResult.jsx
│   │   └── Section1.jsx
│   └── utils/
├── data/                  # 데이터 파일
│   ├── 제품스펙/          # 제품 스펙 CSV
│   ├── 온보딩/            # 온보딩 데이터
│   ├── 리뷰/              # 리뷰 데이터
│   └── simulation/        # 시뮬레이션 데이터
├── ngrok/                 # ngrok 실행 파일
├── scripts/               # 유틸리티 스크립트
├── backups/               # 백업 파일
├── logs/                  # 로그 파일
├── requirements.txt       # Python 의존성
├── package.json           # Node.js 의존성
├── vite.config.js         # Vite 설정
├── tailwind.config.js     # Tailwind CSS 설정
├── Dockerfile             # Docker 설정
├── Procfile               # 배포 설정
├── render.yaml            # Render 배포 설정
├── fly.toml               # Fly.io 배포 설정
├── railway_deploy.sh      # Railway 배포 스크립트
├── LOCAL_ENV_PROMPT.md    # 로컬 환경 설정 가이드
└── COMET_PROMPT.md        # Comet 프롬프트 (이 파일)
```

### 3. 주요 기능 모듈

#### 데이터 모델
- **Product**: 제품 기본 정보 (카테고리, 가격, 이미지 등)
- **ProductSpec**: 제품 스펙 (JSON 형식)
- **ProductDemographics**: 제품 인구통계 (가족 구성, 주거 형태 등)
- **ProductReview**: 제품 리뷰 데이터
- **ProductRecommendReason**: AI 생성 추천 이유
- **OnboardingSession**: 사용자 온보딩 세션 (5단계 설문 응답)
- **Portfolio**: 추천 포트폴리오 결과 저장
- **UserSample**: 샘플 사용자 데이터

#### 추천 엔진 (다중 엔진 지원)
- **recommendation_engine.py**: 기본 추천 엔진
- **taste_based_recommendation_engine.py**: 취향 기반 추천
- **playbook_recommendation_engine.py**: 플레이북 기반 추천
- **column_based_recommendation_engine.py**: 컬럼 기반 추천
- **ai_recommendation_service.py**: AI 기반 추천

#### 점수 계산 시스템
- **taste_based_product_scorer.py**: 취향 기반 점수 계산
- **taste_scoring_logic_service.py**: 점수 계산 로직
- **taste_calculation_service.py**: 취향 계산 서비스
- **playbook_scoring.py**: 플레이북 점수 계산
- **scoring_logic/**: JSON 기반 점수 계산 규칙

#### 외부 서비스 연동
- **chatgpt_service.py**: OpenAI ChatGPT 연동
- **kakao_auth_service.py**: 카카오 로그인
- **kakao_message_service.py**: 카카오 메시지 전송
- **figma_to_code_service.py**: Figma MCP 연동

#### 기타 서비스
- **portfolio_service.py**: 포트폴리오 관리
- **product_comparison_service.py**: 제품 비교
- **recommendation_reason_generator.py**: 추천 이유 생성
- **onboarding_db_service.py**: 온보딩 DB 관리
- **style_analysis_service.py**: 스타일 분석

### 4. 로컬 환경 의존성
- Node.js v24.11.1 (로컬 바이너리 필요)
- Cursor Talk to Figma MCP 서버
- ngrok (카카오 API 연동용 터널링)
- Python 가상환경 (venv)
- .env 파일 (API 키 등)

### 5. 현재까지의 작업 이력
- **프로젝트 구조 파악 완료**
- **LOCAL_ENV_PROMPT.md 파일 확인** (로컬 환경 설정 가이드)
- **package.json 확인** (React + Vite 프로젝트)
- **프로젝트 디렉토리 구조 분석 완료**
- **Django 모델 구조 파악** (8개 주요 모델)
- **서비스 레이어 분석** (22개 서비스 파일)
- **React 컴포넌트 구조 확인** (3개 페이지, 2개 컴포넌트)
- **데이터베이스 스키마 확인** (SQLite 기본, Oracle 지원)
- **배포 설정 파일 확인** (Railway, Render, Fly.io 지원)

### 6. 앞으로 해야 할 일
사용자가 추가로 요청할 작업들을 수행해야 합니다. 일반적으로 다음과 같은 작업들이 예상됩니다:

1. **코드 수정/개선**
   - Django 백엔드 로직 수정
   - React 프론트엔드 컴포넌트 개발/수정
   - API 엔드포인트 추가/수정
   - 데이터베이스 스키마 변경

2. **기능 추가**
   - 새로운 추천 알고리즘 구현
   - UI/UX 개선
   - 외부 API 연동 추가
   - 데이터 처리 스크립트 작성

3. **버그 수정**
   - 에러 디버깅
   - 성능 최적화
   - 호환성 문제 해결

4. **문서화**
   - 코드 주석 추가
   - API 문서 작성
   - 설정 가이드 업데이트

5. **테스트 및 배포**
   - 단위 테스트 작성
   - 통합 테스트
   - 배포 스크립트 수정

### 7. 사용자가 지금까지 날린 프롬프트
**현재 세션**: 이것이 첫 번째 대화입니다. 사용자가 comet에게 all-in-one 프롬프트를 보내기 위한 준비 단계입니다.

**사용자의 요청**:
- "너에게 all in one 프롬프트를 날리도록 comet에게 요청할건데, 너의 상황, 앞으로 너가 해야하는 일, 내가 지금까지 날렸던 프롬프트에 의거해서 현재 해야하는 일, 싸그리 다 정리해서 보내봐."

### 8. 작업 흐름
```
[사용자] → [Auto (나)] → [Comet] → [Auto (나)] → [사용자]
```

1. 사용자가 Auto에게 요청
2. Auto가 상황을 정리하여 Comet에게 프롬프트 전달
3. Comet이 종합 분석 후 Auto에게 작업 지시 프롬프트 생성
4. Auto가 Comet의 지시에 따라 작업 수행
5. 결과를 사용자에게 보고

### 9. 프로젝트의 특수 사항
- **다중 데이터베이스 지원**: SQLite (개발) / Oracle (프로덕션)
- **외부 서비스 연동**: 카카오, OpenAI, Figma
- **로컬 전용 요소**: Node.js 바이너리, MCP 서버, ngrok 등이 Git에 포함되지 않음
- **배포 준비**: Railway, Render, Fly.io 등 여러 플랫폼 지원 스크립트 포함

### 10. 현재 열려있는 파일
- `COMET_PROMPT.md` (197줄, 커서 위치: 197) - 현재 파일
- `LOCAL_ENV_PROMPT.md` (161줄)
- `package.json` (26줄)

### 11. 프로젝트 기술적 세부사항

#### Django 백엔드
- **버전**: Django 5.2.8
- **API**: Django REST Framework 사용
- **데이터베이스**: 
  - SQLite (개발 환경 기본)
  - Oracle (프로덕션, 정규화 테이블 지원)
- **인증**: 카카오 OAuth
- **환경 변수**: python-dotenv 사용

#### React 프론트엔드
- **버전**: React 18.2.0
- **빌드 도구**: Vite 5.0.8
- **라우팅**: react-router-dom 6.20.0
- **스타일링**: Tailwind CSS 3.3.6
- **주요 페이지**:
  - Onboarding.jsx: 5단계 온보딩 설문
  - PortfolioResult.jsx: 추천 결과 표시
  - Section1.jsx: 첫 화면

#### 데이터 처리
- **CSV 데이터**: 제품 스펙, 리뷰, 인구통계 등
- **JSON 데이터**: 제품 스펙, 점수 계산 로직
- **이미지**: 제품 이미지 (PNG, AVIF, JPG)
- **정규화**: Oracle DB에서 정규화된 테이블 사용

#### 배포 환경
- **Railway**: railway_deploy.sh
- **Render**: render.yaml
- **Fly.io**: fly.toml
- **Docker**: Dockerfile 포함

---

## Comet에게 요청할 내용

**Comet님, 위의 정보를 바탕으로 다음을 수행해주세요:**

1. **프로젝트 전체 상황 분석**
   - 현재 프로젝트의 상태 평가
   - 개선이 필요한 영역 식별
   - 우선순위 결정

2. **Auto에게 전달할 작업 지시 프롬프트 생성**
   - 구체적이고 실행 가능한 작업 목록 작성
   - 단계별 가이드라인 제공
   - 예상 결과물 명시

3. **프로젝트 개선 방향 제시**
   - 코드 품질 개선 사항
   - 아키텍처 개선 제안
   - 사용자 경험 개선 방안

4. **다음 단계 작업 계획 수립**
   - 즉시 수행할 작업
   - 단기 목표
   - 장기 목표

**출력 형식**: Auto가 바로 실행할 수 있는 명확하고 구체적인 프롬프트 형식으로 작성해주세요.

---

## 참고 정보

### 환경 변수 예시 (.env)
```
DJANGO_SECRET_KEY=your-secret-key
KAKAO_REST_API_KEY=your-kakao-key
KAKAO_JS_KEY=your-kakao-js-key
OPENAI_API_KEY=your-openai-key
USE_ORACLE=false
```

### 주요 명령어
```bash
# Django 서버 실행
python manage.py runserver 8000

# React 개발 서버 실행
npm run dev

# ngrok 터널 시작
ngrok\ngrok.exe http 8000

# 데이터베이스 마이그레이션
python manage.py migrate
```

### 프로젝트 의존성
- Python 패키지: `requirements.txt` 참조
- Node.js 패키지: `package.json` 참조

---

**이 프롬프트를 Comet에게 전달하여, Auto가 수행할 구체적인 작업 지시를 받아오세요.**

