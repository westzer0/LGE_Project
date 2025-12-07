# 백엔드 로직 구현 가이드

## 개요

PRD(Product Requirements Document)를 기반으로 프론트엔드는 유지하고 백엔드 로직을 구현했습니다.

## 구현된 주요 기능

### 1. 스타일 분석 서비스 (`api/services/style_analysis_service.py`)

**목적**: 온보딩 결과를 기반으로 사용자 스타일 분석 및 메시지 생성

**주요 로직**:
- **Vibe 기반 스타일 정보 결정** (PRD Step 1 로직 반영)
  - 모던 & 미니멀: Essence White, Matte Black | Basic, Built-in
  - 코지 & 네이처: Nature Beige, Clay Brown | Objet Collection
  - 유니크 & 팝: Calming Green, Active Red | MoodUP
  - 럭셔리 & 아티스틱: LG SIGNATURE | Stainless Steel, Glass

- **스타일 메시지 생성**
  - ChatGPT API 활용 (가능한 경우)
  - PRD 패턴 기반 Fallback 로직
  - 타이틀: "모던 & 미니멀 라이프를 위한 오브제 스타일" 등
  - 서브타이틀: 사용자 특성 반영 (가족 구성, 라이프스타일, 예산 등)

**사용 예시**:
```python
from api.services.style_analysis_service import style_analysis_service

style_analysis = style_analysis_service.generate_style_analysis(
    onboarding_data={
        'vibe': 'modern',
        'household_size': 2,
        'housing_type': 'apartment',
        'pyung': 30,
        'priority': 'design',
        'budget_level': 'medium',
        'has_pet': False,
        'cooking': 'often',
        'laundry': 'weekly',
        'media': 'balanced',
        'main_space': 'kitchen'
    },
    user_profile={...}
)
```

### 2. 포트폴리오 서비스 (`api/services/portfolio_service.py`)

**목적**: 포트폴리오 생성, 관리, 추천 로직

**주요 기능**:

#### 2-1. 포트폴리오 생성 (`create_portfolio_from_onboarding`)
- 온보딩 세션 기반 자동 포트폴리오 생성
- 스타일 분석 결과 포함
- 카테고리별 최대 3개씩 제품 추천
- 가격 합계 자동 계산

**로직 흐름**:
1. 온보딩 세션 조회
2. 사용자 프로필 생성
3. 스타일 분석 생성
4. 추천 엔진 호출
5. 카테고리별 제품 그룹화 (최대 3개씩)
6. 포트폴리오 저장

#### 2-2. 다시 추천받기 (`refresh_portfolio`)
- 기존 추천 제품 제외
- 중복 제거 로직
- 새로운 추천 결과 반환

**중복 제거 로직**:
- 기존 포트폴리오의 제품 ID 수집
- 제외할 제품 ID 리스트 병합
- 추천 엔진 호출 시 제외 필터 적용

#### 2-3. 다른 추천 후보 확인 (`get_alternative_recommendations`)
- 카테고리별 최대 3개씩 대안 제품 제공
- 기존 추천 제품 제외
- 특정 카테고리 필터링 지원

#### 2-4. 포트폴리오 전체 장바구니 담기 (`add_products_to_cart`)
- 포트폴리오의 모든 제품을 장바구니에 추가
- 기존 장바구니 항목이 있으면 수량 증가
- 제품별 가격 정보 포함

### 3. API 엔드포인트

#### 3-1. 포트폴리오 생성/저장
```
POST /api/portfolio/save/
{
    "session_id": "abc12345",  # 필수
    "user_id": "kakao_12345"
}
```

**응답**:
```json
{
    "success": true,
    "portfolio_id": "PF-XXXXXX",
    "internal_key": "P001",
    "style_analysis": {
        "title": "모던 & 미니멀 라이프를 위한 오브제 스타일",
        "subtitle": "...",
        "style_type": "modern",
        "color_group": ["Essence White", "Matte Black"],
        "line": ["Basic", "Built-in"]
    },
    "recommendations": [...],
    "total_price": 5000000,
    "total_discount_price": 4500000,
    "match_score": 85
}
```

#### 3-2. 다시 추천받기
```
POST /api/portfolio/<portfolio_id>/refresh/
{
    "exclude_product_ids": [1, 2, 3]  # 선택
}
```

**응답**: 새로운 추천 결과 반환

#### 3-3. 다른 추천 후보 확인
```
GET /api/portfolio/<portfolio_id>/alternatives/?category=TV
```

**응답**:
```json
{
    "success": true,
    "alternatives": [
        {
            "category": "TV",
            "products": [...]
        },
        {
            "category": "KITCHEN",
            "products": [...]
        }
    ]
}
```

#### 3-4. 포트폴리오 전체 장바구니 담기
```
POST /api/portfolio/<portfolio_id>/add-to-cart/
{
    "user_id": "kakao_12345"
}
```

**응답**:
```json
{
    "success": true,
    "added_count": 5,
    "cart_items": [...],
    "message": "5개 제품이 장바구니에 추가되었습니다."
}
```

#### 3-5. 베스트샵 상담 예약
```
POST /api/bestshop/consultation/
{
    "portfolio_id": "PF-XXXXXX",
    "user_id": "kakao_12345",
    "consultation_purpose": "이사",
    "preferred_date": "2025-12-15",
    "preferred_time": "14:00",
    "store_location": "서울 강남점"
}
```

**응답**: 상담 예약 정보 및 베스트샵 URL 반환

**Note**: 실제 베스트샵 API 연동은 외부 시스템이므로, 여기서는 포트폴리오 정보를 준비만 합니다.

### 4. 온보딩 완료 시 자동 포트폴리오 생성

`onboarding_complete_view`에서 온보딩 완료 시 자동으로 포트폴리오를 생성합니다.

**로직**:
1. 온보딩 세션 저장
2. 추천 엔진 호출
3. **포트폴리오 자동 생성** (새로 추가)
4. Taste 계산 (member_id가 있는 경우)
5. 응답에 포트폴리오 정보 포함

## 구현 방식 설명

### 1. 스타일 분석 로직

**규칙 기반 + AI 하이브리드 방식**:
- ChatGPT API가 사용 가능하면 AI로 생성
- 실패 시 PRD 패턴 기반 규칙으로 Fallback

**PRD 로직 반영**:
- Step 1 Vibe Check 로직 그대로 구현
- 컬러 그룹, 라인, 기능, 소재 정보 결정
- 사용자 타입(1인/2인/가족) 기반 타이틀 선택

### 2. 포트폴리오 추천 로직

**카테고리별 그룹화 방식**:
- 각 카테고리(TV, KITCHEN, LIVING 등)별로 최대 3개씩 추천
- 추천 엔진의 점수 기반 정렬
- 중복 제품 제거

**다시 추천받기 로직**:
- 기존 추천 제품 ID를 수집
- 추천 엔진 호출 시 제외 필터 적용
- 완전히 새로운 제품만 추천

### 3. 장바구니 통합

**일괄 추가 방식**:
- 포트폴리오의 모든 제품을 순회
- 각 제품을 장바구니에 추가 (기존 항목이 있으면 수량 증가)
- 포트폴리오 정보를 extra_data에 저장

### 4. 베스트샵 연동

**데이터 준비 방식**:
- 포트폴리오 정보를 상담 예약 형식으로 변환
- 제품 목록, 가격, 스타일 분석 정보 포함
- 실제 예약은 외부 시스템과 연동 필요 (현재는 URL만 반환)

## 데이터 흐름

```
온보딩 완료
  ↓
추천 엔진 호출
  ↓
스타일 분석 생성
  ↓
포트폴리오 생성
  ↓
응답 반환 (포트폴리오 ID 포함)
```

## 주의사항

1. **온보딩 세션 필수**: 포트폴리오 생성은 온보딩 세션이 있어야 합니다.
2. **제품 중복 제거**: 다시 추천받기 시 기존 제품은 자동으로 제외됩니다.
3. **카테고리별 제한**: 각 카테고리별로 최대 3개씩만 추천됩니다.
4. **베스트샵 연동**: 실제 예약 기능은 외부 시스템과 연동이 필요합니다.

## 향후 개선 사항

1. **공간 이미지 기반 배치 시각화**: 외부 API 연동 필요
2. **실시간 견적 계산**: 옵션별 가격 계산 로직 추가
3. **포트폴리오 편집 기능**: 수동 제품 추가/삭제/업그레이드
4. **베스트샵 실제 연동**: 외부 API 연동 구현

