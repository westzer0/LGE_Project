# 오라클 DB 스키마 문서

이 문서는 오라클 데이터베이스의 테이블 구조와 각 테이블의 역할, 주요 컬럼 의미를 설명합니다.

## 전체 사용자 여정

이 데이터베이스 구조는 **"회원 → 온보딩 세션/응답 → 포트폴리오 생성 → 상품/장바구니/주문/결제 및 상담·견적"**으로 이어지는 전체 사용자 여정을 표현합니다.

---

## 회원 및 온보딩

### MEMBER
서비스 사용자를 나타내는 회원 기본 정보 테이블.

**주요 컬럼:**
- `MEMBER_ID`: 회원 PK
- `PASSWORD`: 비밀번호
- `NAME`: 이름
- `AGE`: 나이
- `GENDER`: 성별
- `CONTACT`: 연락처
- `PROFILE_IMAGE`: 프로필 이미지
- `POINT`: 적립 포인트
- `CREATED_DATE`: 생성일시
- `TASTE`: 선호/취향 태그

---

### ONBOARDING_SESSION
한 번의 온보딩(설문/초기 상담) 진행 단위를 나타내는 세션 테이블.

**주요 컬럼:**
- `SESSION_ID`: PK
- `MEMBER_ID`: 어떤 회원의 세션인지
- `CREATED_DATE`: 생성일시
- `UPDATED_DATE`: 수정일시

---

### ONBOARDING_QUESTION
온보딩에서 노출되는 질문 마스터.

**주요 컬럼:**
- `QUESTION_CODE`: PK
- `QUESTION_TEXT`: 질문 내용
- `QUESTION_TYPE`: 단일/복수 선택, 입력형 등
- `IS_REQUIRED`: 필수 여부
- `CREATED_DATE`: 생성일시

---

### ONBOARDING_ANSWER
각 질문에 대한 선택지(Answer) 마스터.

**주요 컬럼:**
- `ANSWER_ID`: PK
- `QUESTION_CODE`: 어떤 질문의 선택지인지
- `ANSWER_VALUE`: 코드값 또는 점수
- `ANSWER_TEXT`: 화면에 보이는 텍스트
- `CREATED_DATE`: 생성일시

---

### ONBOARDING_USER_RESPONSE
회원이 실제로 온보딩에서 답변한 결과(설문 응답 로그).

**주요 컬럼:**
- `RESPONSE_ID`: PK
- `SESSION_ID`: 어떤 온보딩 세션의 응답인지
- `QUESTION_CODE`: 질문 코드
- `ANSWER_ID`: 선택형일 때 선택한 답변
- `INPUT_VALUE`: 직접 입력형 값
- `CREATED_DATE`: 생성일시

---

## 장바구니 · 주문 · 결제

### CART
회원의 장바구니 헤더 테이블.

**주요 컬럼:**
- `CART_ID`: PK
- `MEMBER_ID`: 어떤 회원의 장바구니인지
- `CREATED_DATE`: 생성일시

---

### CART_ITEM
장바구니에 담긴 개별 상품 정보.

**주요 컬럼:**
- `CART_ITEM_ID`: PK
- `CART_ID`: 어떤 장바구니인지
- `PRODUCT_ID`: 담긴 상품
- `QUANTITY`: 수량

---

### ORDERS
확정된 주문(장바구니 → 주문 전환 결과).

**주요 컬럼 예시:**
- `ORDER_ID`: PK
- `MEMBER_ID`: 회원 ID
- `ORDER_STATUS`: 주문 상태
- `CREATED_DATE`: 생성일시
- (실제 컬럼 명은 DB 기준으로 사용)

---

### ORDER_DETAIL
주문에 포함된 개별 상품 라인.

**주요 컬럼:**
- `DETAIL_ID`: PK
- `ORDER_ID`: 어떤 주문의 항목인지
- `PRODUCT_ID`: 상품 ID
- `QUANTITY`: 수량

---

### PAYMENT
주문에 대한 결제 정보.

**주요 컬럼 예시:**
- `PAYMENT_ID`: PK
- `ORDER_ID`: 주문 ID
- `AMOUNT`: 결제 금액
- `METHOD`: 결제 방법
- `CREATED_DATE`: 생성일시
- (실제 컬럼 명은 DB 기준으로 사용)

---

## 상품 · 스펙 · 포트폴리오

### PRODUCT
판매되는 단일 상품(모델) 마스터.

**주요 컬럼:**
- `PRODUCT_ID`: PK
- `PRODUCT_NAME`: 상품명
- `MAIN_CATEGORY`: 메인 카테고리
- `SUB_CATEGORY`: 서브 카테고리
- `MODEL_CODE`: 모델 코드
- `STATUS`: 판매 상태
- `PRICE`: 가격
- `RATING`: 평점
- `URL`: 상품 URL
- `CREATED_DATE`: 생성일시

---

### PRODUCT_IMAGE
상품 이미지 정보.

**주요 컬럼:**
- `PRODUCT_IMAGE_ID`: PK
- `PRODUCT_ID`: 어떤 상품 이미지인지
- `IMAGE_URL`: 이미지 URL

---

### PRODUCT_SPEC
상품별 상세 스펙(key–value 형태).

**주요 컬럼:**
- `SPEC_ID`: PK
- `PRODUCT_ID`: 상품 ID
- `SPEC_KEY`: 스펙 항목 이름
- `SPEC_VALUE`: 값
- `SPEC_TYPE`: 타입/표현 방식 등

---

### CATEGORY_COMMON_SPEC
카테고리별 공통 스펙 정의(어떤 카테고리에 어떤 스펙 키를 쓸 수 있는지).

**주요 컬럼:**
- `COMMON_ID`: PK
- `MAIN_CATEGORY`: 메인 카테고리
- `SPEC_KEY`: 스펙 키

---

### PORTFOLIO_SESSION
추천/컨설팅 결과로 만들어지는 하나의 "포트폴리오 세트"에 대한 세션 정보.

**주요 컬럼:**
- `PORTFOLIO_ID`: PK
- `MEMBER_ID`: 회원 ID
- `SESSION_ID`: 어떤 온보딩 세션 기반인지
- `CREATED_DATE`: 생성일시

---

### PORTFOLIO_PRODUCT
하나의 포트폴리오에 포함된 추천 상품 목록.

**주요 컬럼:**
- `ID`: PK
- `PORTFOLIO_ID`: 포트폴리오 ID
- `PRODUCT_ID`: 상품 ID
- `RECOMMEND_REASON`: 추천 사유 텍스트
- `PRIORITY`: 노출 순서/우선순위

---

## 상담 · 견적

### CONSULTATION
오프라인/온라인 상담 예약 및 이력 테이블.

**주요 컬럼:**
- `CONSULT_ID`: PK
- `MEMBER_ID`: 회원 ID
- `PORTFOLIO_ID`: 어떤 포트폴리오 기반 상담인지
- `STORE_NAME`: 매장명
- `RESERVATION_DATE`: 예약 일시
- `CREATED_DATE`: 생성일시

---

### ESTIMATE
상담/포트폴리오를 기반으로 생성되는 견적 정보.

**주요 컬럼:**
- `ESTIMATE_ID`: PK
- `PORTFOLIO_ID`: 포트폴리오 ID
- `TOTAL_PRICE`: 총 금액
- `DISCOUNT_PRICE`: 할인 후 금액
- `RENTAL_MONTHLY`: 렌탈 월 납부액
- `CREATED_DATE`: 생성일시

---

## 사용 가이드

이 스키마 문서를 참고하여:
- 데이터베이스 쿼리 작성 시 테이블 간 관계와 컬럼 의미를 정확히 이해하고 사용하세요.
- 코드 작성 시 각 테이블의 역할과 주요 컬럼을 고려하여 로직을 구현하세요.
- 새로운 기능 개발 시 전체 사용자 여정을 고려하여 적절한 테이블을 선택하세요.

