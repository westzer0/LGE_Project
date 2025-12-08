# 다음 단계 실행 가이드

## ✅ 완료된 작업

1. ✅ ERD 기반 34개 테이블 모델 생성
2. ✅ DRF Serializers 및 ViewSets 생성
3. ✅ URL 라우팅 설정
4. ✅ Admin 인터페이스 등록
5. ✅ API 문서 작성
6. ✅ 서버 실행 (백그라운드)

## 🚀 다음 단계 실행 방법

### 1. 마이그레이션 실행

터미널에서 다음 명령어를 실행하세요:

```bash
# 마이그레이션 생성 (변경사항이 있다면)
python manage.py makemigrations

# 마이그레이션 적용
python manage.py migrate

# 마이그레이션 상태 확인
python manage.py showmigrations
```

### 2. 서버 실행 확인

서버가 이미 백그라운드에서 실행 중일 수 있습니다. 확인하려면:

```bash
# 서버 실행 (이미 실행 중이면 포트 충돌 오류 발생)
python manage.py runserver 8000
```

또는 브라우저에서 접속:
- http://localhost:8000/api/v1/members/
- http://localhost:8000/admin/

### 3. API 테스트

#### 방법 1: Python 스크립트 사용
```bash
python test_erd_api.py
```

#### 방법 2: curl 사용
```bash
# 회원 목록 조회
curl http://localhost:8000/api/v1/members/

# 온보딩 질문 조회
curl http://localhost:8000/api/v1/onboarding-questions/

# Taste 설정 조회
curl http://localhost:8000/api/v1/taste-configs/
```

#### 방법 3: 브라우저에서 직접 접속
- http://localhost:8000/api/v1/members/
- http://localhost:8000/api/v1/onboarding-questions/
- http://localhost:8000/api/v1/taste-configs/

### 4. Admin 인터페이스 확인

1. 관리자 계정이 없다면 생성:
```bash
python manage.py createsuperuser
```

2. 브라우저에서 접속:
- http://localhost:8000/admin/
- 로그인 후 새로 추가된 모델들 확인:
  - Member (회원)
  - CartNew (장바구니)
  - Orders (주문)
  - OnboardingQuestion (온보딩 질문)
  - TasteConfig (Taste 설정)
  - 등등...

## 📋 주요 API 엔드포인트

### 회원/인증
- `GET /api/v1/members/` - 회원 목록
- `POST /api/v1/members/` - 회원 가입
- `POST /api/v1/members/kakao_login/` - 카카오 로그인

### 장바구니
- `GET /api/v1/carts/` - 장바구니 목록
- `POST /api/v1/carts/{id}/add_item/` - 제품 추가
- `DELETE /api/v1/carts/{id}/remove_item/` - 제품 제거

### 주문/결제
- `GET /api/v1/orders/` - 주문 목록
- `POST /api/v1/orders/{id}/create_from_cart/` - 장바구니에서 주문 생성
- `POST /api/v1/payments/` - 결제 생성

### 온보딩
- `GET /api/v1/onboarding-questions/` - 질문 목록
- `GET /api/v1/onboarding-questions/by_type/?question_type=vibe` - 질문 유형별 조회
- `POST /api/v1/onboarding-user-responses/` - 응답 저장

### Taste 추천
- `GET /api/v1/taste-configs/` - Taste 설정 목록
- `GET /api/v1/taste-configs/{id}/recommendations/` - 추천 제품 조회
- `POST /api/v1/taste-configs/match_taste/` - Taste 매칭

### 포트폴리오/견적
- `GET /api/v1/portfolio-products/` - 포트폴리오 제품 목록
- `GET /api/v1/estimates/` - 견적 목록
- `POST /api/v1/estimates/create_from_portfolio/` - 견적 생성
- `GET /api/v1/consultations/` - 상담 목록

## 🔍 문제 해결

### 마이그레이션 오류가 발생하는 경우

1. 기존 마이그레이션과 충돌하는 경우:
```bash
# 마이그레이션 파일 확인
ls api/migrations/

# 특정 마이그레이션만 실행
python manage.py migrate api 0015_erd_models
```

2. 모델 변경사항이 반영되지 않는 경우:
```bash
# 마이그레이션 강제 생성
python manage.py makemigrations --empty api
# 그 다음 수동으로 마이그레이션 파일 편집
```

### 서버가 시작되지 않는 경우

1. 포트가 이미 사용 중인 경우:
```bash
# 다른 포트 사용
python manage.py runserver 8001
```

2. 모델 임포트 오류:
```bash
# Django 체크 실행
python manage.py check
```

### API가 404를 반환하는 경우

1. URL 라우팅 확인:
   - `config/urls.py`에서 `router.urls`가 포함되어 있는지 확인
   - `/api/v1/` 경로가 올바른지 확인

2. ViewSet이 제대로 등록되었는지 확인:
   - `api/viewsets_erd.py` 파일 확인
   - `config/urls.py`에서 import 확인

## 📚 참고 문서

- **API 문서**: `ERD_BACKEND_API_DOCS.md`
- **구현 요약**: `ERD_BACKEND_IMPLEMENTATION_SUMMARY.md`
- **테스트 스크립트**: `test_erd_api.py`

## ✨ 다음 개선 사항

1. **JWT 인증 완전 구현**
   - `djangorestframework-simplejwt` 설정
   - 토큰 발급/갱신 엔드포인트 추가

2. **Kakao OAuth2 완전 연동**
   - 카카오 로그인 콜백 처리
   - 사용자 정보 저장

3. **테스트 작성**
   - 단위 테스트
   - 통합 테스트

4. **성능 최적화**
   - 쿼리 최적화
   - 캐싱 추가

---

**생성일**: 2024-12-08  
**상태**: ✅ 핵심 기능 완료, 테스트 및 배포 준비 중
