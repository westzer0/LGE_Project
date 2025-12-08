# API 문서

LG 가전 패키지 추천 시스템 API 문서입니다.

## 기본 정보

- **Base URL**: `http://localhost:8000` (개발 환경)
- **Content-Type**: `application/json`
- **인코딩**: UTF-8

## 인증

대부분의 API는 인증이 필요하지 않지만, 일부 기능(카카오 로그인 등)은 인증이 필요합니다.

## 공통 응답 형식

### 성공 응답
```json
{
  "success": true,
  "data": { ... }
}
```

### 에러 응답
```json
{
  "success": false,
  "error": "에러 메시지"
}
```

## API 엔드포인트

### 1. 추천 API

#### 제품 추천
```http
POST /api/recommend/
```

**요청 본문:**
```json
{
  "vibe": "modern",
  "household_size": 4,
  "housing_type": "apartment",
  "pyung": 30,
  "priority": "tech",
  "budget_level": "medium",
  "categories": ["TV"],
  "member_id": "optional_member_id"
}
```

**응답:**
```json
{
  "success": true,
  "count": 3,
  "recommendations": [
    {
      "product_id": 1,
      "name": "제품명",
      "category": "TV",
      "price": 2000000,
      "match_score": 95,
      "reason": "추천 이유"
    }
  ]
}
```

---

### 2. 제품 API

#### 제품 목록 조회
```http
GET /api/products/?category=TV&page=1&page_size=20
```

**쿼리 파라미터:**
- `category` (선택): 제품 카테고리 (TV, KITCHEN, LIVING, AIR, AI, OBJET, SIGNATURE)
- `search` (선택): 검색어
- `id` (선택): 특정 제품 ID
- `page` (선택): 페이지 번호 (기본값: 1)
- `page_size` (선택): 페이지당 항목 수 (기본값: 20)

**응답:**
```json
{
  "success": true,
  "count": 100,
  "page": 1,
  "page_size": 20,
  "products": [
    {
      "id": 1,
      "name": "제품명",
      "model_number": "모델번호",
      "category": "TV",
      "price": 2000000,
      "discount_price": 1800000,
      "image_url": "https://...",
      "is_active": true
    }
  ]
}
```

#### 제품 스펙 조회
```http
GET /api/products/{product_id}/spec/
```

**응답:**
```json
{
  "success": true,
  "product_id": 1,
  "spec": {
    "화면크기": "65인치",
    "해상도": "4K UHD",
    ...
  }
}
```

#### 제품 리뷰 조회
```http
GET /api/products/{product_id}/reviews/
```

**응답:**
```json
{
  "success": true,
  "product_id": 1,
  "reviews": [
    {
      "star": "5",
      "review_text": "리뷰 내용",
      "source": "리뷰 출처",
      "created_at": "2024-01-01T00:00:00Z"
    }
  ]
}
```

#### 제품 추천 이유 조회
```http
GET /api/products/{product_id}/recommend-reason/
```

**응답:**
```json
{
  "success": true,
  "product_id": 1,
  "reason_text": "이 제품을 추천하는 이유..."
}
```

#### 제품 인구통계 조회
```http
GET /api/products/{product_id}/demographics/
```

**응답:**
```json
{
  "success": true,
  "product_id": 1,
  "family_types": ["신혼", "부모님"],
  "house_sizes": ["20평", "30평대"],
  "house_types": ["아파트", "단독주택"]
}
```

#### 제품 이미지 조회 (이름으로)
```http
GET /api/products/image-by-name/?name=제품명&category=TV
```

**쿼리 파라미터:**
- `name` (필수): 제품명
- `category` (선택): 카테고리 힌트

**응답:**
```json
{
  "success": true,
  "image_url": "https://..."
}
```

---

### 3. 온보딩 API

#### 온보딩 단계 저장
```http
POST /api/onboarding/step/
```

**요청 본문:**
```json
{
  "session_id": "abc12345",
  "step": 1,
  "data": {
    "vibe": "modern"
  }
}
```

#### 온보딩 완료 및 추천 생성
```http
POST /api/onboarding/complete/
```

**요청 본문:**
```json
{
  "session_id": "abc12345",
  "user_id": "kakao_12345",
  "vibe": "modern",
  "household_size": 4,
  "housing_type": "apartment",
  "pyung": 30,
  "priority": "tech",
  "budget_level": "medium",
  "categories": ["TV"]
}
```

**응답:**
```json
{
  "success": true,
  "session_id": "abc12345",
  "portfolio_id": "PF-XXXXXX",
  "recommendations": [...],
  "style_analysis": {...},
  "total_price": 5000000,
  "total_discount_price": 4500000
}
```

#### 온보딩 세션 조회
```http
GET /api/onboarding/session/{session_id}/
```

**응답:**
```json
{
  "success": true,
  "session": {
    "session_id": "abc12345",
    "current_step": 5,
    "status": "completed",
    "vibe": "modern",
    "household_size": 4,
    ...
  }
}
```

---

### 4. 포트폴리오 API

#### 포트폴리오 저장
```http
POST /api/portfolio/save/
```

**요청 본문:**
```json
{
  "session_id": "abc12345",
  "user_id": "kakao_12345",
  "style_type": "modern",
  "style_title": "모던 & 미니멀 라이프",
  "products": [...]
}
```

#### 포트폴리오 조회
```http
GET /api/portfolio/{portfolio_id}/
```

**응답:**
```json
{
  "success": true,
  "portfolio": {
    "portfolio_id": "PF-XXXXXX",
    "user_id": "kakao_12345",
    "style_type": "modern",
    "products": [...],
    "total_price": 5000000,
    "match_score": 93
  }
}
```

#### 포트폴리오 목록 조회
```http
GET /api/portfolio/list/?user_id=kakao_12345
```

**쿼리 파라미터:**
- `user_id` (선택): 사용자 ID

#### 포트폴리오 공유
```http
POST /api/portfolio/{portfolio_id}/share/
```

#### 포트폴리오 새로고침 (재추천)
```http
POST /api/portfolio/{portfolio_id}/refresh/
```

#### 포트폴리오 대안 제품 조회
```http
GET /api/portfolio/{portfolio_id}/alternatives/
```

#### 포트폴리오 장바구니 추가
```http
POST /api/portfolio/{portfolio_id}/add-to-cart/
```

**요청 본문:**
```json
{
  "user_id": "kakao_12345"
}
```

#### 포트폴리오 편집
```http
POST /api/portfolio/{portfolio_id}/edit/
PUT /api/portfolio/{portfolio_id}/edit/
```

**요청 본문:**
```json
{
  "products": [1, 2, 3],
  "style_title": "새로운 스타일 제목"
}
```

#### 포트폴리오 견적 계산
```http
POST /api/portfolio/{portfolio_id}/estimate/
```

---

### 5. 장바구니 API

#### 장바구니에 제품 추가
```http
POST /api/cart/add/
```

**요청 본문:**
```json
{
  "user_id": "kakao_12345",
  "product_id": 1,
  "quantity": 1
}
```

#### 장바구니에서 제품 제거
```http
POST /api/cart/remove/
```

**요청 본문:**
```json
{
  "user_id": "kakao_12345",
  "product_id": 1
}
```

#### 장바구니 목록 조회
```http
GET /api/cart/list/?user_id=kakao_12345
```

---

### 6. 위시리스트 API

#### 위시리스트에 제품 추가
```http
POST /api/wishlist/add/
```

**요청 본문:**
```json
{
  "user_id": "kakao_12345",
  "product_id": 1
}
```

#### 위시리스트에서 제품 제거
```http
POST /api/wishlist/remove/
```

**요청 본문:**
```json
{
  "user_id": "kakao_12345",
  "product_id": 1
}
```

#### 위시리스트 목록 조회
```http
GET /api/wishlist/list/?user_id=kakao_12345
```

---

### 7. 검색 API

#### 제품 검색
```http
GET /api/search/?q=검색어&category=TV
```

**쿼리 파라미터:**
- `q` (필수): 검색어
- `category` (선택): 카테고리 필터

**응답:**
```json
{
  "success": true,
  "count": 10,
  "results": [...]
}
```

---

### 8. 제품 비교 API

#### 제품 비교
```http
GET /api/products/compare/?ids=1,2,3
POST /api/products/compare/
```

**GET 요청:**
- 쿼리 파라미터: `ids` (쉼표로 구분된 제품 ID)

**POST 요청 본문:**
```json
{
  "product_ids": [1, 2, 3]
}
```

**응답:**
```json
{
  "success": true,
  "products": [
    {
      "id": 1,
      "name": "제품1",
      "specs": {...},
      "price": 2000000
    },
    ...
  ],
  "comparison": {
    "price_range": [1800000, 2500000],
    "common_features": [...],
    "differences": [...]
  }
}
```

---

### 9. AI API

#### AI 추천 이유 생성
```http
POST /api/ai/recommendation-reason/
```

**요청 본문:**
```json
{
  "product_id": 1,
  "user_profile": {...}
}
```

#### AI 스타일 메시지 생성
```http
POST /api/ai/style-message/
```

#### AI 리뷰 요약
```http
POST /api/ai/review-summary/
```

**요청 본문:**
```json
{
  "product_id": 1
}
```

#### AI 채팅
```http
POST /api/ai/chat/
```

**요청 본문:**
```json
{
  "message": "사용자 메시지",
  "context": {...}
}
```

#### AI 상태 확인
```http
GET /api/ai/status/
```

#### AI 자연어 추천
```http
POST /api/ai/natural-recommend/
```

**요청 본문:**
```json
{
  "query": "작은 집에 맞는 TV 추천해줘"
}
```

#### AI 채팅 기반 추천
```http
POST /api/ai/chat-recommend/
```

#### AI 제품 비교
```http
POST /api/ai/product-compare/
```

**요청 본문:**
```json
{
  "product_ids": [1, 2],
  "user_question": "어떤 제품이 더 나은가요?"
}
```

---

### 10. 카카오 인증 API

#### 카카오 로그인
```http
GET /api/auth/kakao/login/
```

**응답:** 카카오 로그인 페이지로 리다이렉트

#### 카카오 콜백
```http
GET /api/auth/kakao/callback/?code=인증코드
```

#### 카카오 로그아웃
```http
GET /api/auth/kakao/logout/
```

#### 카카오 사용자 정보 조회
```http
GET /api/auth/kakao/user/
```

#### 카카오 메시지 전송
```http
POST /api/kakao/send-message/
```

**요청 본문:**
```json
{
  "user_id": "kakao_12345",
  "message": "메시지 내용",
  "portfolio_id": "PF-XXXXXX"
}
```

---

### 11. 예약 API

#### 베스트샵 상담 예약
```http
POST /api/bestshop/consultation/
```

**요청 본문:**
```json
{
  "user_id": "kakao_12345",
  "portfolio_id": "PF-XXXXXX",
  "name": "홍길동",
  "phone": "010-1234-5678",
  "preferred_date": "2024-12-25",
  "preferred_time": "14:00"
}
```

#### 예약 목록 조회
```http
GET /api/reservation/list/?user_id=kakao_12345&status=pending
```

**쿼리 파라미터:**
- `user_id` (선택): 사용자 ID
- `status` (선택): 예약 상태 (pending, confirmed, cancelled)

#### 예약 상세 조회
```http
GET /api/reservation/{reservation_id}/
```

#### 예약 수정
```http
PUT /api/reservation/{reservation_id}/update/
POST /api/reservation/{reservation_id}/update/
```

**요청 본문:**
```json
{
  "preferred_date": "2024-12-26",
  "preferred_time": "15:00"
}
```

#### 예약 취소
```http
POST /api/reservation/{reservation_id}/cancel/
```

---

### 12. Figma API

#### Figma 이미지를 코드로 변환
```http
POST /api/figma-to-code/
```

**Content-Type**: `multipart/form-data`

**Form Data:**
- `image` (필수): 이미지 파일 (PNG, JPG, JPEG)
- `design_type` (선택): 디자인 타입 (기본값: 'web_page')
- `save_files` (선택): 파일 저장 여부 (true/false)

**응답:**
```json
{
  "success": true,
  "html": "...",
  "css": "...",
  "javascript": "...",
  "components": [...],
  "colors": {...},
  "fonts": [...]
}
```

---

## 에러 코드

| HTTP 상태 코드 | 설명 |
|--------------|------|
| 200 | 성공 |
| 400 | 잘못된 요청 |
| 404 | 리소스를 찾을 수 없음 |
| 500 | 서버 내부 오류 |

## 예제

### cURL 예제

```bash
# 제품 추천
curl -X POST http://localhost:8000/api/recommend/ \
  -H "Content-Type: application/json" \
  -d '{
    "vibe": "modern",
    "household_size": 4,
    "housing_type": "apartment",
    "pyung": 30,
    "priority": "tech",
    "budget_level": "medium",
    "categories": ["TV"]
  }'

# 제품 목록 조회
curl http://localhost:8000/api/products/?category=TV&page=1

# 온보딩 완료
curl -X POST http://localhost:8000/api/onboarding/complete/ \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "abc12345",
    "vibe": "modern",
    "household_size": 4,
    "housing_type": "apartment",
    "pyung": 30,
    "priority": "tech",
    "budget_level": "medium",
    "categories": ["TV"]
  }'
```

### JavaScript 예제

```javascript
// 제품 추천
const response = await fetch('http://localhost:8000/api/recommend/', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    vibe: 'modern',
    household_size: 4,
    housing_type: 'apartment',
    pyung: 30,
    priority: 'tech',
    budget_level: 'medium',
    categories: ['TV']
  })
});

const data = await response.json();
console.log(data);
```

---

**마지막 업데이트**: 2024년 12월

