# LG 가전 추천 AI 백엔드 API 문서

## 📋 개요

ERD 기반 34개 테이블을 완전히 구현한 Django REST Framework 백엔드 API 문서입니다.

**기술 스택:**
- Django 4.2.16
- Django REST Framework 3.14.0
- Oracle DB / SQLite
- JWT 인증 (djangorestframework-simplejwt)
- Kakao OAuth2

---

## 🚀 빠른 시작

### 1. 환경 설정

```bash
# 가상환경 생성 및 활성화
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 의존성 설치
pip install -r requirements.txt

# 마이그레이션
python manage.py makemigrations
python manage.py migrate

# 관리자 계정 생성
python manage.py createsuperuser

# 서버 실행
python manage.py runserver
```

### 2. API 기본 URL

- **기본 URL**: `http://localhost:8000`
- **API v1**: `http://localhost:8000/api/v1/`
- **Admin**: `http://localhost:8000/admin/`

---

## 📚 API 엔드포인트 목록

### 🔐 인증/회원 (Members)

#### 회원 목록 조회
```
GET /api/v1/members/
```

#### 회원 상세 조회
```
GET /api/v1/members/{member_id}/
```

#### 회원 가입
```
POST /api/v1/members/
Body: {
    "member_id": "user123",
    "password": "encrypted_password",
    "name": "홍길동",
    "age": 30,
    "gender": "M",
    "contact": "010-1234-5678"
}
```

#### 카카오 로그인
```
POST /api/v1/members/kakao_login/
Body: {
    "kakao_id": "kakao_user_id",
    "name": "홍길동"
}
```

---

### 🛒 장바구니 (Cart)

#### 장바구니 목록 조회
```
GET /api/v1/carts/
```

#### 장바구니 생성
```
POST /api/v1/carts/
Body: {
    "member": "member_id"
}
```

#### 장바구니에 제품 추가
```
POST /api/v1/carts/{cart_id}/add_item/
Body: {
    "product_id": 1,
    "quantity": 2
}
```

#### 장바구니에서 제품 제거
```
DELETE /api/v1/carts/{cart_id}/remove_item/
Body: {
    "product_id": 1
}
```

#### 장바구니 항목 수정
```
PUT /api/v1/cart-items/{cart_item_id}/
Body: {
    "quantity": 3
}
```

---

### 📦 주문/결제 (Orders & Payments)

#### 주문 목록 조회
```
GET /api/v1/orders/
```

#### 주문 생성 (장바구니에서)
```
POST /api/v1/orders/{order_id}/create_from_cart/
Body: {
    "cart_id": 1
}
```

#### 주문 상세 조회
```
GET /api/v1/orders/{order_id}/
```

#### 결제 생성
```
POST /api/v1/payments/
Body: {
    "order": 1,
    "payment_status": "결제완료",
    "method": "카드"
}
```

---

### 📝 온보딩 (Onboarding)

#### 온보딩 질문 목록 조회
```
GET /api/v1/onboarding-questions/
```

#### 질문 유형별 조회
```
GET /api/v1/onboarding-questions/by_type/?question_type=vibe
```

#### 온보딩 답변 선택지 조회
```
GET /api/v1/onboarding-answers/
GET /api/v1/onboarding-answers/?question=vibe_question
```

#### 사용자 응답 저장
```
POST /api/v1/onboarding-user-responses/
Body: {
    "session": 1,
    "question": "vibe_question",
    "answer": 1,
    "input_value": null
}
```

---

### 🎯 Taste 추천 (Taste-based Recommendation)

#### Taste 설정 목록 조회
```
GET /api/v1/taste-configs/
```

#### Taste별 추천 제품 조회
```
GET /api/v1/taste-configs/{taste_id}/recommendations/
GET /api/v1/taste-configs/{taste_id}/recommendations/?category=TV
```

#### 온보딩 결과로 Taste 매칭
```
POST /api/v1/taste-configs/match_taste/
Body: {
    "session_id": 1
}
```

#### Taste 카테고리 점수 조회
```
GET /api/v1/taste-category-scores/
GET /api/v1/taste-category-scores/?taste=1&category_name=TV
```

#### Taste 추천 제품 조회
```
GET /api/v1/taste-recommended-products/
GET /api/v1/taste-recommended-products/?taste=1&category_name=TV
```

---

### 🎨 포트폴리오 (Portfolio)

#### 포트폴리오 제품 목록 조회
```
GET /api/v1/portfolio-products/
```

#### 포트폴리오 제품 추가
```
POST /api/v1/portfolio-products/
Body: {
    "portfolio": "PF-XXXXXX",
    "product": 1,
    "recommend_reason": "추천 이유",
    "priority": 1
}
```

---

### 💰 견적 (Estimate)

#### 견적 목록 조회
```
GET /api/v1/estimates/
```

#### 포트폴리오로부터 견적 생성
```
POST /api/v1/estimates/create_from_portfolio/
Body: {
    "portfolio_id": "PF-XXXXXX"
}
```

#### 견적 상세 조회
```
GET /api/v1/estimates/{estimate_id}/
```

---

### 📞 상담 (Consultation)

#### 상담 목록 조회
```
GET /api/v1/consultations/
```

#### 상담 신청
```
POST /api/v1/consultations/
Body: {
    "member": "member_id",
    "portfolio": "PF-XXXXXX",
    "store_name": "서울 강남점",
    "reservation_date": "2024-01-15T10:00:00Z"
}
```

---

### 🖼️ 제품 이미지 (Product Images)

#### 제품 이미지 목록 조회
```
GET /api/v1/product-images/
GET /api/v1/product-images/?product=1
```

#### 제품 이미지 추가
```
POST /api/v1/product-images/
Body: {
    "product": 1,
    "image_url": "https://example.com/image.jpg"
}
```

---

### 📊 제품 스펙 (Product Specs)

#### 제품 스펙 목록 조회
```
GET /api/v1/product-specs/
GET /api/v1/product-specs/?product=1
```

#### 제품 스펙 추가
```
POST /api/v1/product-specs/
Body: {
    "product": 1,
    "spec_key": "용량",
    "spec_value": "850L",
    "spec_type": "COMMON"
}
```

---

### ⭐ 제품 리뷰 (Product Reviews)

#### 제품 리뷰 조회
```
GET /api/v1/product-reviews/
GET /api/v1/product-reviews/{product_id}/
```

---

## 🔄 온보딩 플로우 예시

### 1단계: 세션 생성
```python
# OnboardingSession 생성 (기존 API 사용)
POST /api/onboarding/step/
```

### 2단계: 질문 조회
```python
GET /api/v1/onboarding-questions/by_type/?question_type=vibe
```

### 3단계: 답변 선택 및 저장
```python
POST /api/v1/onboarding-user-responses/
{
    "session": 1,
    "question": "vibe_question",
    "answer": 1
}
```

### 4단계: Taste 매칭
```python
POST /api/v1/taste-configs/match_taste/
{
    "session_id": 1
}
```

### 5단계: 추천 제품 조회
```python
GET /api/v1/taste-configs/{taste_id}/recommendations/?category=TV
```

---

## 📊 ERD 테이블 구조

### 핵심 테이블 (34개)

1. **MEMBER** - 회원 정보
2. **CART** - 장바구니
3. **CART_ITEM** - 장바구니 항목
4. **ORDERS** - 주문
5. **ORDER_DETAIL** - 주문 상세
6. **PAYMENT** - 결제
7. **PRODUCT** - 제품
8. **PRODUCT_IMAGE** - 제품 이미지
9. **PRODUCT_SPEC** - 제품 스펙
10. **PRODUCT_REVIEW** - 제품 리뷰
11. **ONBOARDING_SESSION** - 온보딩 세션
12. **ONBOARDING_QUESTION** - 온보딩 질문
13. **ONBOARDING_ANSWER** - 온보딩 답변 선택지
14. **ONBOARDING_USER_RESPONSE** - 사용자 응답
15. **ONBOARDING_SESSION_CATEGORIES** - 세션 카테고리
16. **ONBOARDING_SESSION_MAIN_SPACES** - 세션 주요 공간
17. **ONBOARDING_SESSION_PRIORITIES** - 세션 우선순위
18. **ONBOARD_SESS_REC_PRODUCTS** - 세션 추천 제품
19. **TASTE_CONFIG** - Taste 설정
20. **TASTE_CATEGORY_SCORES** - Taste 카테고리 점수
21. **TASTE_RECOMMENDED_PRODUCTS** - Taste 추천 제품
22. **PORTFOLIO** - 포트폴리오
23. **PORTFOLIO_SESSION** - 포트폴리오 세션
24. **PORTFOLIO_PRODUCT** - 포트폴리오 제품
25. **ESTIMATE** - 견적
26. **CONSULTATION** - 상담
27. **PROD_DEMO_FAMILY_TYPES** - 제품 인구통계 - 가족 구성
28. **PROD_DEMO_HOUSE_SIZES** - 제품 인구통계 - 집 크기
29. **PROD_DEMO_HOUSE_TYPES** - 제품 인구통계 - 주거 형태
30. **USER_SAMPLE** - 사용자 샘플
31. **USER_SAMPLE_PURCHASED_ITEMS** - 사용자 샘플 구매 항목
32. **USER_SAMPLE_RECOMMENDATIONS** - 사용자 샘플 추천
33. **CATEGORY_COMMON_SPEC** - 카테고리 공통 스펙
34. **기타 보조 테이블들**

---

## 🔐 인증 설정 (향후 구현)

### JWT 토큰 발급
```python
POST /api/auth/jwt/token/
Body: {
    "member_id": "user123",
    "password": "password"
}
```

### JWT 토큰 갱신
```python
POST /api/auth/jwt/refresh/
Body: {
    "refresh": "refresh_token"
}
```

---

## 🧪 테스트 예시

### Python requests 예시

```python
import requests

BASE_URL = "http://localhost:8000/api/v1"

# 회원 가입
response = requests.post(f"{BASE_URL}/members/", json={
    "member_id": "test_user",
    "password": "test123",
    "name": "테스트 사용자",
    "age": 25,
    "gender": "M"
})
print(response.json())

# 장바구니 생성
response = requests.post(f"{BASE_URL}/carts/", json={
    "member": "test_user"
})
cart_id = response.json()["cart_id"]

# 장바구니에 제품 추가
response = requests.post(f"{BASE_URL}/carts/{cart_id}/add_item/", json={
    "product_id": 1,
    "quantity": 2
})
print(response.json())

# Taste 추천 제품 조회
response = requests.get(f"{BASE_URL}/taste-configs/1/recommendations/?category=TV")
print(response.json())
```

---

## 📝 주의사항

1. **하위 호환성**: 기존 모델(`Product`, `OnboardingSession` 등)은 하위 호환성을 위해 유지되었습니다.
2. **데이터베이스**: Oracle DB 또는 SQLite 사용 가능합니다.
3. **인증**: 현재는 `AllowAny`로 설정되어 있으나, 프로덕션에서는 JWT 인증을 활성화해야 합니다.
4. **CORS**: 개발 환경에서는 CORS가 활성화되어 있습니다.

---

## 🚧 향후 개선 사항

- [ ] JWT 인증 완전 구현
- [ ] Kakao OAuth2 완전 연동
- [ ] Celery 비동기 작업 설정
- [ ] Redis 캐싱
- [ ] API Rate Limiting
- [ ] Swagger/OpenAPI 문서 자동 생성
- [ ] 단위 테스트 작성
- [ ] 통합 테스트 작성

---

## 📞 문의

프로젝트 관련 문의사항은 이슈를 등록해주세요.

---

**생성일**: 2024-12-08  
**버전**: 1.0.0  
**기반 ERD**: 34개 테이블 완전 구현
