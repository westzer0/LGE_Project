# Django REST Framework (DRF) 도입 완료

## ✅ 완료된 작업

### 1. 패키지 설치
- `djangorestframework>=3.14.0` 추가 (requirements.txt)

### 2. Django 설정
- `config/settings.py`에 `rest_framework` 추가
- DRF 기본 설정 추가 (페이징, 렌더러 등)

### 3. Serializers 생성
- `api/serializers.py` 파일 생성
  - `RecommendRequestSerializer`: 추천 요청 검증
  - `RecommendResponseSerializer`: 추천 응답
  - `PortfolioSerializer`: 포트폴리오 모델
  - `PortfolioCreateSerializer`: 포트폴리오 생성
  - `OnboardingSessionSerializer`: 온보딩 세션

### 4. DRF Views 생성
- `api/views_drf.py` 파일 생성
  - `RecommendAPIView`: 추천 API (DRF 버전)
  - `PortfolioViewSet`: 포트폴리오 CRUD (ViewSet)
  - `OnboardingSessionViewSet`: 온보딩 세션 조회

### 5. URL 설정
- `config/urls.py`에 DRF 라우터 추가
- 기존 API와 공존하도록 설정

## 🔗 새로운 API 엔드포인트

### 추천 API
```
POST /api/drf/recommend/
```

### 포트폴리오 API (ViewSet)
```
GET    /api/drf/portfolios/              - 리스트
POST   /api/drf/portfolios/              - 생성
GET    /api/drf/portfolios/{id}/         - 상세
PUT    /api/drf/portfolios/{id}/         - 전체 수정
PATCH  /api/drf/portfolios/{id}/         - 부분 수정
DELETE /api/drf/portfolios/{id}/         - 삭제
POST   /api/drf/portfolios/{id}/share/   - 공유 (커스텀)
```

### 온보딩 세션 API
```
GET /api/drf/onboarding-sessions/        - 리스트
GET /api/drf/onboarding-sessions/{id}/   - 상세
```

## 📝 사용 방법

### 1. 추천 API 호출 (DRF 버전)

**기존 방식:**
```python
POST /api/recommend/
{
    "household_size": 4,
    "categories": ["TV"]
}
```

**DRF 방식:**
```python
POST /api/drf/recommend/
{
    "household_size": 4,
    "categories": ["TV"],
    "has_pet": true
}
```

**차이점:**
- ✅ 자동 데이터 검증
- ✅ 자동 에러 메시지
- ✅ 표준화된 응답 형식

### 2. 포트폴리오 API (ViewSet)

**생성:**
```python
POST /api/drf/portfolios/
{
    "style_type": "modern",
    "products": [...],
    "match_score": 85
}
```

**조회:**
```python
GET /api/drf/portfolios/{portfolio_id}/
```

**리스트 (user_id 필터링):**
```python
GET /api/drf/portfolios/?user_id=user123
```

**공유:**
```python
POST /api/drf/portfolios/{portfolio_id}/share/
```

## 🎯 기존 API vs DRF API

### 공존 가능
- 기존 API (`/api/recommend/`)는 그대로 작동
- 새로운 DRF API (`/api/drf/recommend/`)도 별도로 사용 가능
- 점진적으로 마이그레이션 가능

### 장점
1. **자동 검증**: Serializer가 데이터 자동 검증
2. **자동 문서화**: 브라우저에서 API 테스트 가능
3. **표준화**: RESTful API 표준 준수
4. **유지보수**: 코드가 더 깔끔하고 관리 쉬움

## 🔧 다음 단계

### 선택사항
1. **API 문서화**: Swagger/OpenAPI 설정
2. **인증 추가**: Token 인증 등
3. **기존 API 완전 전환**: 모든 API를 DRF로 전환

### 테스트 방법

```bash
# 1. 서버 시작
python manage.py runserver

# 2. 브라우저에서 API 테스트
http://127.0.0.1:8000/api/drf/portfolios/

# 3. 추천 API 테스트
curl -X POST http://127.0.0.1:8000/api/drf/recommend/ \
  -H "Content-Type: application/json" \
  -d '{"household_size": 4, "categories": ["TV"]}'
```

## 📚 참고

- DRF 공식 문서: https://www.django-rest-framework.org/
- Serializers 가이드: https://www.django-rest-framework.org/api-guide/serializers/
- ViewSets 가이드: https://www.django-rest-framework.org/api-guide/viewsets/

