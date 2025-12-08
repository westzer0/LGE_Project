-- ============================================================
-- 모든 컬럼 COMMENT 추가 스크립트
-- Oracle 11g 호환
-- models.py와 기존 코드를 참고하여 작성
-- ============================================================

-- ============================================================
-- 1. TASTE_CONFIG 테이블 - 카테고리별 SCORE 컬럼들
-- ============================================================

COMMENT ON COLUMN TASTE_CONFIG.TV_SCORE IS 'TV 카테고리 점수 (0~100점)';
COMMENT ON COLUMN TASTE_CONFIG.냉장고_SCORE IS '냉장고 카테고리 점수 (0~100점)';
COMMENT ON COLUMN TASTE_CONFIG.김치냉장고_SCORE IS '김치냉장고 카테고리 점수 (0~100점)';
COMMENT ON COLUMN TASTE_CONFIG.세탁기_SCORE IS '세탁기 카테고리 점수 (0~100점)';
COMMENT ON COLUMN TASTE_CONFIG.건조기_SCORE IS '건조기 카테고리 점수 (0~100점)';
COMMENT ON COLUMN TASTE_CONFIG.에어컨_SCORE IS '에어컨 카테고리 점수 (0~100점)';
COMMENT ON COLUMN TASTE_CONFIG.청소기_SCORE IS '청소기 카테고리 점수 (0~100점)';
COMMENT ON COLUMN TASTE_CONFIG.정수기_SCORE IS '정수기 카테고리 점수 (0~100점)';
COMMENT ON COLUMN TASTE_CONFIG.제습기_SCORE IS '제습기 카테고리 점수 (0~100점)';
COMMENT ON COLUMN TASTE_CONFIG.가습기_SCORE IS '가습기 카테고리 점수 (0~100점)';
COMMENT ON COLUMN TASTE_CONFIG.오븐_SCORE IS '오븐 카테고리 점수 (0~100점)';
COMMENT ON COLUMN TASTE_CONFIG.전자레인지_SCORE IS '전자레인지 카테고리 점수 (0~100점)';
COMMENT ON COLUMN TASTE_CONFIG.식기세척기_SCORE IS '식기세척기 카테고리 점수 (0~100점)';
COMMENT ON COLUMN TASTE_CONFIG.와인셀러_SCORE IS '와인셀러 카테고리 점수 (0~100점)';
COMMENT ON COLUMN TASTE_CONFIG.사운드바_SCORE IS '사운드바 카테고리 점수 (0~100점)';
COMMENT ON COLUMN TASTE_CONFIG.오디오_SCORE IS '오디오 카테고리 점수 (0~100점)';
COMMENT ON COLUMN TASTE_CONFIG.스탠바이미_SCORE IS '스탠바이미 카테고리 점수 (0~100점)';
COMMENT ON COLUMN TASTE_CONFIG.프로젝터_SCORE IS '프로젝터 카테고리 점수 (0~100점)';
COMMENT ON COLUMN TASTE_CONFIG.워시타워_SCORE IS '워시타워 카테고리 점수 (0~100점)';
COMMENT ON COLUMN TASTE_CONFIG.AIHOME_SCORE IS 'AI Home 카테고리 점수 (0~100점)';
COMMENT ON COLUMN TASTE_CONFIG.OBJET_SCORE IS 'LG Objet 카테고리 점수 (0~100점)';
COMMENT ON COLUMN TASTE_CONFIG.SIGNATURE_SCORE IS 'LG SIGNATURE 카테고리 점수 (0~100점)';

-- ============================================================
-- 2. ONBOARDING_SESSION 테이블
-- ============================================================

COMMENT ON COLUMN ONBOARDING_SESSION.CREATED_DATE IS '세션 생성 일시 (기본값: SYSDATE)';
COMMENT ON COLUMN ONBOARDING_SESSION.MEMBER_ID IS '회원 ID (카카오 로그인 연동 시, FK: MEMBER.MEMBER_ID)';
COMMENT ON COLUMN ONBOARDING_SESSION.UPDATED_DATE IS '세션 수정 일시 (기본값: SYSDATE)';

-- ============================================================
-- 3. ONBOARD_SESS_MAIN_SPACES 테이블 (정규화)
-- ============================================================

COMMENT ON TABLE ONBOARD_SESS_MAIN_SPACES IS '온보딩 세션별 주요 공간 정보 테이블 (정규화)';
COMMENT ON COLUMN ONBOARD_SESS_MAIN_SPACES.SESSION_ID IS '세션 ID (FK, ONBOARDING_SESSION.SESSION_ID 참조)';
COMMENT ON COLUMN ONBOARD_SESS_MAIN_SPACES.MAIN_SPACE IS '주요 공간 (living/kitchen/bedroom/dressing/study/all)';
COMMENT ON COLUMN ONBOARD_SESS_MAIN_SPACES.CREATED_AT IS '생성 일시 (기본값: SYSDATE)';

-- ============================================================
-- 4. ONBOARD_SESS_PRIORITIES 테이블 (정규화)
-- ============================================================

COMMENT ON TABLE ONBOARD_SESS_PRIORITIES IS '온보딩 세션별 우선순위 정보 테이블 (정규화)';
COMMENT ON COLUMN ONBOARD_SESS_PRIORITIES.SESSION_ID IS '세션 ID (FK, ONBOARDING_SESSION.SESSION_ID 참조)';
COMMENT ON COLUMN ONBOARD_SESS_PRIORITIES.PRIORITY IS '우선순위 값 (design/tech/eco/value)';
COMMENT ON COLUMN ONBOARD_SESS_PRIORITIES.PRIORITY_ORDER IS '우선순위 순서 (1, 2, 3...)';
COMMENT ON COLUMN ONBOARD_SESS_PRIORITIES.CREATED_AT IS '생성 일시 (기본값: SYSDATE)';

-- ============================================================
-- 5. ONBOARD_SESS_CATEGORIES 테이블 (정규화)
-- ============================================================

COMMENT ON TABLE ONBOARD_SESS_CATEGORIES IS '온보딩 세션별 선택 카테고리 정보 테이블 (정규화)';
COMMENT ON COLUMN ONBOARD_SESS_CATEGORIES.SESSION_ID IS '세션 ID (FK, ONBOARDING_SESSION.SESSION_ID 참조)';
COMMENT ON COLUMN ONBOARD_SESS_CATEGORIES.CATEGORY_NAME IS '선택한 카테고리명 (예: "TV", "냉장고", "에어컨")';
COMMENT ON COLUMN ONBOARD_SESS_CATEGORIES.CREATED_AT IS '생성 일시 (기본값: SYSDATE)';

-- ============================================================
-- 6. ONBOARD_SESS_REC_PRODUCTS 테이블 (정규화)
-- ============================================================

COMMENT ON TABLE ONBOARD_SESS_REC_PRODUCTS IS '온보딩 세션별 추천 제품 정보 테이블 (정규화)';
COMMENT ON COLUMN ONBOARD_SESS_REC_PRODUCTS.SESSION_ID IS '세션 ID (FK, ONBOARDING_SESSION.SESSION_ID 참조)';
COMMENT ON COLUMN ONBOARD_SESS_REC_PRODUCTS.PRODUCT_ID IS '제품 ID (FK, PRODUCT.PRODUCT_ID 참조)';
COMMENT ON COLUMN ONBOARD_SESS_REC_PRODUCTS.CATEGORY_NAME IS '카테고리명 (예: "TV", "냉장고")';
COMMENT ON COLUMN ONBOARD_SESS_REC_PRODUCTS.RANK_ORDER IS '카테고리 내 순위 (1, 2, 3...)';
COMMENT ON COLUMN ONBOARD_SESS_REC_PRODUCTS.SCORE IS '해당 제품의 점수 (0~100점, NUMBER(5,2))';
COMMENT ON COLUMN ONBOARD_SESS_REC_PRODUCTS.CREATED_AT IS '생성 일시 (기본값: SYSDATE)';

-- ============================================================
-- 7. ONBOARDING_QUESTION 테이블
-- ============================================================

COMMENT ON COLUMN ONBOARDING_QUESTION.CREATED_DATE IS '질문 생성 일시 (기본값: SYSDATE)';
COMMENT ON COLUMN ONBOARDING_QUESTION.QUESTION_CODE IS '질문 코드 (시스템 내부 식별자)';

-- ============================================================
-- 8. ONBOARDING_ANSWER 테이블
-- ============================================================

COMMENT ON COLUMN ONBOARDING_ANSWER.CREATED_DATE IS '선택지 생성 일시 (기본값: SYSDATE)';
COMMENT ON COLUMN ONBOARDING_ANSWER.QUESTION_CODE IS '질문 코드 (시스템 내부 식별자)';

-- ============================================================
-- 9. ONBOARDING_USER_RESPONSE 테이블
-- ============================================================

COMMENT ON COLUMN ONBOARDING_USER_RESPONSE.CREATED_DATE IS '응답 생성 일시 (기본값: SYSDATE)';
COMMENT ON COLUMN ONBOARDING_USER_RESPONSE.QUESTION_CODE IS '질문 코드 (시스템 내부 식별자)';
COMMENT ON COLUMN ONBOARDING_USER_RESPONSE.INPUT_VALUE IS '사용자 입력 값 (텍스트 입력인 경우)';

-- ============================================================
-- 10. PRODUCT 테이블
-- ============================================================

COMMENT ON COLUMN PRODUCT.CREATED_DATE IS '제품 생성 일시';
COMMENT ON COLUMN PRODUCT.RATING IS '제품 평점 (예: 4.5)';
COMMENT ON COLUMN PRODUCT.SUB_CATEGORY IS '세부 카테고리 (예: "OLED", "QLED", "냉장고", "김치냉장고")';
COMMENT ON COLUMN PRODUCT.URL IS '제품 상세 페이지 URL';

-- ============================================================
-- 11. PRODUCT_SPEC 테이블
-- ============================================================

COMMENT ON COLUMN PRODUCT_SPEC.SPEC_ID IS '스펙 ID (PRIMARY KEY)';

-- ============================================================
-- 12. PRODUCT_IMAGE 테이블
-- ============================================================

COMMENT ON TABLE PRODUCT_IMAGE IS '제품 이미지 정보 테이블';
COMMENT ON COLUMN PRODUCT_IMAGE.PRODUCT_IMAGE_ID IS '제품 이미지 ID (PRIMARY KEY)';
COMMENT ON COLUMN PRODUCT_IMAGE.PRODUCT_ID IS '제품 ID (FK, PRODUCT.PRODUCT_ID 참조)';
COMMENT ON COLUMN PRODUCT_IMAGE.IMAGE_URL IS '제품 이미지 URL';

-- ============================================================
-- 13. PROD_DEMO_FAMILY_TYPES 테이블 (정규화)
-- ============================================================

COMMENT ON TABLE PROD_DEMO_FAMILY_TYPES IS '제품별 가족 구성 타입 테이블 (정규화)';
COMMENT ON COLUMN PROD_DEMO_FAMILY_TYPES.PRODUCT_ID IS '제품 ID (FK, PRODUCT.PRODUCT_ID 참조)';
COMMENT ON COLUMN PROD_DEMO_FAMILY_TYPES.FAMILY_TYPE IS '가족 구성 타입 (예: "신혼", "부모님", "1인가구")';
COMMENT ON COLUMN PROD_DEMO_FAMILY_TYPES.CREATED_AT IS '생성 일시 (기본값: SYSDATE)';

-- ============================================================
-- 14. PROD_DEMO_HOUSE_SIZES 테이블 (정규화)
-- ============================================================

COMMENT ON TABLE PROD_DEMO_HOUSE_SIZES IS '제품별 집 크기 테이블 (정규화)';
COMMENT ON COLUMN PROD_DEMO_HOUSE_SIZES.PRODUCT_ID IS '제품 ID (FK, PRODUCT.PRODUCT_ID 참조)';
COMMENT ON COLUMN PROD_DEMO_HOUSE_SIZES.HOUSE_SIZE IS '집 크기 (예: "20평", "30평대", "40평대")';
COMMENT ON COLUMN PROD_DEMO_HOUSE_SIZES.CREATED_AT IS '생성 일시 (기본값: SYSDATE)';

-- ============================================================
-- 15. PROD_DEMO_HOUSE_TYPES 테이블 (정규화)
-- ============================================================

COMMENT ON TABLE PROD_DEMO_HOUSE_TYPES IS '제품별 주거 형태 테이블 (정규화)';
COMMENT ON COLUMN PROD_DEMO_HOUSE_TYPES.PRODUCT_ID IS '제품 ID (FK, PRODUCT.PRODUCT_ID 참조)';
COMMENT ON COLUMN PROD_DEMO_HOUSE_TYPES.HOUSE_TYPE IS '주거 형태 (예: "아파트", "원룸", "단독주택")';
COMMENT ON COLUMN PROD_DEMO_HOUSE_TYPES.CREATED_AT IS '생성 일시 (기본값: SYSDATE)';

-- ============================================================
-- 16. USER_SAMPLE_RECOMMENDATIONS 테이블 (정규화)
-- ============================================================

COMMENT ON TABLE USER_SAMPLE_RECOMMENDATIONS IS '사용자 샘플별 추천 정보 테이블 (정규화)';
COMMENT ON COLUMN USER_SAMPLE_RECOMMENDATIONS.USER_ID IS '사용자 ID (FK, USER_SAMPLE.USER_ID 참조)';
COMMENT ON COLUMN USER_SAMPLE_RECOMMENDATIONS.CATEGORY_NAME IS '카테고리명 (예: "냉장고", "세탁기", "TV")';
COMMENT ON COLUMN USER_SAMPLE_RECOMMENDATIONS.RECOMMENDED_VALUE IS '추천 값 (예: "850", "15", "65")';
COMMENT ON COLUMN USER_SAMPLE_RECOMMENDATIONS.RECOMMENDED_UNIT IS '추천 단위 (예: "L", "kg", "inch")';
COMMENT ON COLUMN USER_SAMPLE_RECOMMENDATIONS.CREATED_AT IS '생성 일시 (기본값: SYSDATE)';

-- ============================================================
-- 17. USER_SAMPLE_PURCHASED_ITEMS 테이블 (정규화)
-- ============================================================

COMMENT ON TABLE USER_SAMPLE_PURCHASED_ITEMS IS '사용자 샘플별 구매 제품 정보 테이블 (정규화)';
COMMENT ON COLUMN USER_SAMPLE_PURCHASED_ITEMS.USER_ID IS '사용자 ID (FK, USER_SAMPLE.USER_ID 참조)';
COMMENT ON COLUMN USER_SAMPLE_PURCHASED_ITEMS.PRODUCT_ID IS '제품 ID (FK, PRODUCT.PRODUCT_ID 참조)';
COMMENT ON COLUMN USER_SAMPLE_PURCHASED_ITEMS.PURCHASED_AT IS '구매 일시';
COMMENT ON COLUMN USER_SAMPLE_PURCHASED_ITEMS.CREATED_AT IS '생성 일시 (기본값: SYSDATE)';

-- ============================================================
-- 18. MEMBER 테이블
-- ============================================================

COMMENT ON COLUMN MEMBER.AGE IS '회원 나이';
COMMENT ON COLUMN MEMBER.CONTACT IS '회원 연락처';
COMMENT ON COLUMN MEMBER.CREATED_DATE IS '회원 가입 일시';
COMMENT ON COLUMN MEMBER.GENDER IS '회원 성별 (M/F)';
COMMENT ON COLUMN MEMBER.NAME IS '회원 이름';
COMMENT ON COLUMN MEMBER.PASSWORD IS '회원 비밀번호 (암호화)';
COMMENT ON COLUMN MEMBER.POINT IS '회원 포인트';

-- ============================================================
-- 19. CART 테이블
-- ============================================================

COMMENT ON TABLE CART IS '장바구니 테이블';
COMMENT ON COLUMN CART.CART_ID IS '장바구니 ID (PRIMARY KEY)';
COMMENT ON COLUMN CART.MEMBER_ID IS '회원 ID (FK, MEMBER.MEMBER_ID 참조)';
COMMENT ON COLUMN CART.CREATED_DATE IS '장바구니 생성 일시';

-- ============================================================
-- 20. CART_ITEM 테이블
-- ============================================================

COMMENT ON TABLE CART_ITEM IS '장바구니 항목 테이블';
COMMENT ON COLUMN CART_ITEM.CART_ITEM_ID IS '장바구니 항목 ID (PRIMARY KEY)';
COMMENT ON COLUMN CART_ITEM.CART_ID IS '장바구니 ID (FK, CART.CART_ID 참조)';
COMMENT ON COLUMN CART_ITEM.PRODUCT_ID IS '제품 ID (FK, PRODUCT.PRODUCT_ID 참조)';
COMMENT ON COLUMN CART_ITEM.QUANTITY IS '제품 수량';

-- ============================================================
-- 21. ORDERS 테이블
-- ============================================================

COMMENT ON TABLE ORDERS IS '주문 정보 테이블';
COMMENT ON COLUMN ORDERS.ORDER_ID IS '주문 ID (PRIMARY KEY)';
COMMENT ON COLUMN ORDERS.MEMBER_ID IS '회원 ID (FK, MEMBER.MEMBER_ID 참조)';
COMMENT ON COLUMN ORDERS.ORDER_DATE IS '주문 일시';
COMMENT ON COLUMN ORDERS.ORDER_STATUS IS '주문 상태 (예: "주문완료", "배송중", "배송완료")';
COMMENT ON COLUMN ORDERS.PAYMENT_STATUS IS '결제 상태 (예: "결제완료", "결제대기", "결제취소")';
COMMENT ON COLUMN ORDERS.TOTAL_AMOUNT IS '주문 총액';

-- ============================================================
-- 22. ORDER_DETAIL 테이블
-- ============================================================

COMMENT ON TABLE ORDER_DETAIL IS '주문 상세 정보 테이블';
COMMENT ON COLUMN ORDER_DETAIL.DETAIL_ID IS '주문 상세 ID (PRIMARY KEY)';
COMMENT ON COLUMN ORDER_DETAIL.ORDER_ID IS '주문 ID (FK, ORDERS.ORDER_ID 참조)';
COMMENT ON COLUMN ORDER_DETAIL.PRODUCT_ID IS '제품 ID (FK, PRODUCT.PRODUCT_ID 참조)';
COMMENT ON COLUMN ORDER_DETAIL.QUANTITY IS '제품 수량';

-- ============================================================
-- 23. PAYMENT 테이블
-- ============================================================

COMMENT ON TABLE PAYMENT IS '결제 정보 테이블';
COMMENT ON COLUMN PAYMENT.PAYMENT_ID IS '결제 ID (PRIMARY KEY)';
COMMENT ON COLUMN PAYMENT.ORDER_ID IS '주문 ID (FK, ORDERS.ORDER_ID 참조)';
COMMENT ON COLUMN PAYMENT.METHOD IS '결제 방법 (예: "카드", "계좌이체", "무통장입금")';
COMMENT ON COLUMN PAYMENT.PAYMENT_DATE IS '결제 일시';
COMMENT ON COLUMN PAYMENT.PAYMENT_STATUS IS '결제 상태 (예: "결제완료", "결제대기", "결제취소")';

-- ============================================================
-- 24. PORTFOLIO_SESSION 테이블
-- ============================================================

COMMENT ON TABLE PORTFOLIO_SESSION IS '포트폴리오-세션 연결 테이블';
COMMENT ON COLUMN PORTFOLIO_SESSION.PORTFOLIO_ID IS '포트폴리오 ID (FK, PORTFOLIO 참조)';
COMMENT ON COLUMN PORTFOLIO_SESSION.SESSION_ID IS '세션 ID (FK, ONBOARDING_SESSION.SESSION_ID 참조)';
COMMENT ON COLUMN PORTFOLIO_SESSION.MEMBER_ID IS '회원 ID (FK, MEMBER.MEMBER_ID 참조)';
COMMENT ON COLUMN PORTFOLIO_SESSION.CREATED_DATE IS '생성 일시';

-- ============================================================
-- 25. PORTFOLIO_PRODUCT 테이블
-- ============================================================

COMMENT ON TABLE PORTFOLIO_PRODUCT IS '포트폴리오-제품 연결 테이블';
COMMENT ON COLUMN PORTFOLIO_PRODUCT.ID IS '포트폴리오 제품 ID (PRIMARY KEY)';
COMMENT ON COLUMN PORTFOLIO_PRODUCT.PORTFOLIO_ID IS '포트폴리오 ID (FK, PORTFOLIO 참조)';
COMMENT ON COLUMN PORTFOLIO_PRODUCT.PRODUCT_ID IS '제품 ID (FK, PRODUCT.PRODUCT_ID 참조)';
COMMENT ON COLUMN PORTFOLIO_PRODUCT.PRIORITY IS '우선순위 (1, 2, 3...)';
COMMENT ON COLUMN PORTFOLIO_PRODUCT.RECOMMEND_REASON IS '추천 이유 텍스트';

-- ============================================================
-- 26. ESTIMATE 테이블
-- ============================================================

COMMENT ON TABLE ESTIMATE IS '견적 정보 테이블';
COMMENT ON COLUMN ESTIMATE.ESTIMATE_ID IS '견적 ID (PRIMARY KEY)';
COMMENT ON COLUMN ESTIMATE.PORTFOLIO_ID IS '포트폴리오 ID (FK, PORTFOLIO 참조)';
COMMENT ON COLUMN ESTIMATE.TOTAL_PRICE IS '총 가격 (정가 합계)';
COMMENT ON COLUMN ESTIMATE.DISCOUNT_PRICE IS '할인 가격 (할인가 합계)';
COMMENT ON COLUMN ESTIMATE.RENTAL_MONTHLY IS '월 렌탈 비용';
COMMENT ON COLUMN ESTIMATE.CREATED_DATE IS '견적 생성 일시';

-- ============================================================
-- 27. CONSULTATION 테이블
-- ============================================================

COMMENT ON TABLE CONSULTATION IS '상담 예약 정보 테이블';
COMMENT ON COLUMN CONSULTATION.CONSULT_ID IS '상담 ID (PRIMARY KEY)';
COMMENT ON COLUMN CONSULTATION.MEMBER_ID IS '회원 ID (FK, MEMBER.MEMBER_ID 참조)';
COMMENT ON COLUMN CONSULTATION.PORTFOLIO_ID IS '포트폴리오 ID (FK, PORTFOLIO 참조)';
COMMENT ON COLUMN CONSULTATION.RESERVATION_DATE IS '상담 예약 일시';
COMMENT ON COLUMN CONSULTATION.STORE_NAME IS '매장명';
COMMENT ON COLUMN CONSULTATION.CREATED_DATE IS '상담 신청 일시';

-- ============================================================
-- 28. CATEGORY_COMMON_SPEC 테이블
-- ============================================================

COMMENT ON TABLE CATEGORY_COMMON_SPEC IS '카테고리별 공통 스펙 테이블';
COMMENT ON COLUMN CATEGORY_COMMON_SPEC.COMMON_ID IS '공통 스펙 ID (PRIMARY KEY)';
COMMENT ON COLUMN CATEGORY_COMMON_SPEC.MAIN_CATEGORY IS '메인 카테고리 (예: "TV", "냉장고")';
COMMENT ON COLUMN CATEGORY_COMMON_SPEC.SPEC_KEY IS '스펙 키 (예: "용량", "화면크기")';

-- ============================================================
-- 29. 추가 컬럼들
-- ============================================================

-- MEMBER 테이블
COMMENT ON COLUMN MEMBER.AGE IS '회원 나이';

-- ONBOARDING_ANSWER 테이블
COMMENT ON COLUMN ONBOARDING_ANSWER.CREATED_DATE IS '선택지 생성 일시 (기본값: SYSDATE)';

-- ONBOARDING_QUESTION 테이블
COMMENT ON COLUMN ONBOARDING_QUESTION.CREATED_DATE IS '질문 생성 일시 (기본값: SYSDATE)';

-- ONBOARDING_SESSION 테이블
COMMENT ON COLUMN ONBOARDING_SESSION.CREATED_DATE IS '세션 생성 일시 (기본값: SYSDATE)';

-- ONBOARDING_USER_RESPONSE 테이블
COMMENT ON COLUMN ONBOARDING_USER_RESPONSE.CREATED_DATE IS '응답 생성 일시 (기본값: SYSDATE)';

-- PRODUCT 테이블
COMMENT ON COLUMN PRODUCT.CREATED_DATE IS '제품 생성 일시';

-- PRODUCT_SPEC 테이블
COMMENT ON COLUMN PRODUCT_SPEC.SPEC_ID IS '스펙 ID (PRIMARY KEY)';

-- TASTE_CONFIG 테이블
COMMENT ON COLUMN TASTE_CONFIG.TV_SCORE IS 'TV 카테고리 점수 (0~100점)';

-- ============================================================
-- 30. 이전 정규화 테이블 (하위 호환성 유지)
-- ============================================================

-- ONBOARDING_SESSION_MAIN_SPACES (이전 테이블명, 사용 안 함)
COMMENT ON TABLE ONBOARDING_SESSION_MAIN_SPACES IS '온보딩 세션별 주요 공간 정보 테이블 (이전 버전, ONBOARD_SESS_MAIN_SPACES 사용 권장)';
COMMENT ON COLUMN ONBOARDING_SESSION_MAIN_SPACES.SESSION_ID IS '세션 ID (FK, ONBOARDING_SESSION.SESSION_ID 참조)';
COMMENT ON COLUMN ONBOARDING_SESSION_MAIN_SPACES.MAIN_SPACE IS '주요 공간 (living/kitchen/bedroom/dressing/study/all)';
COMMENT ON COLUMN ONBOARDING_SESSION_MAIN_SPACES.CREATED_AT IS '생성 일시 (기본값: SYSDATE)';

-- ONBOARDING_SESSION_PRIORITIES (이전 테이블명, 사용 안 함)
COMMENT ON TABLE ONBOARDING_SESSION_PRIORITIES IS '온보딩 세션별 우선순위 정보 테이블 (이전 버전, ONBOARD_SESS_PRIORITIES 사용 권장)';
COMMENT ON COLUMN ONBOARDING_SESSION_PRIORITIES.SESSION_ID IS '세션 ID (FK, ONBOARDING_SESSION.SESSION_ID 참조)';
COMMENT ON COLUMN ONBOARDING_SESSION_PRIORITIES.PRIORITY IS '우선순위 값 (design/tech/eco/value)';
COMMENT ON COLUMN ONBOARDING_SESSION_PRIORITIES.PRIORITY_ORDER IS '우선순위 순서 (1, 2, 3...)';
COMMENT ON COLUMN ONBOARDING_SESSION_PRIORITIES.CREATED_AT IS '생성 일시 (기본값: SYSDATE)';

-- ONBOARDING_SESSION_CATEGORIES (이전 테이블명, 사용 안 함)
COMMENT ON TABLE ONBOARDING_SESSION_CATEGORIES IS '온보딩 세션별 선택 카테고리 정보 테이블 (이전 버전, ONBOARD_SESS_CATEGORIES 사용 권장)';
COMMENT ON COLUMN ONBOARDING_SESSION_CATEGORIES.SESSION_ID IS '세션 ID (FK, ONBOARDING_SESSION.SESSION_ID 참조)';
COMMENT ON COLUMN ONBOARDING_SESSION_CATEGORIES.CATEGORY_NAME IS '선택한 카테고리명 (예: "TV", "냉장고", "에어컨")';
COMMENT ON COLUMN ONBOARDING_SESSION_CATEGORIES.CREATED_AT IS '생성 일시 (기본값: SYSDATE)';

-- ============================================================
-- 30. 추가 컬럼들 (누락된 것들)
-- ============================================================

-- PRODUCT_IMAGE 테이블
COMMENT ON TABLE PRODUCT_IMAGE IS '제품 이미지 정보 테이블';
COMMENT ON COLUMN PRODUCT_IMAGE.PRODUCT_IMAGE_ID IS '제품 이미지 ID (PRIMARY KEY)';
COMMENT ON COLUMN PRODUCT_IMAGE.PRODUCT_ID IS '제품 ID (FK, PRODUCT.PRODUCT_ID 참조)';
COMMENT ON COLUMN PRODUCT_IMAGE.IMAGE_URL IS '제품 이미지 URL';

-- PRODUCT_REVIEW 테이블
COMMENT ON TABLE PRODUCT_REVIEW IS '제품 리뷰 테이블 (1:N)';
COMMENT ON COLUMN PRODUCT_REVIEW.PRODUCT_ID IS '제품 ID (FK, PRODUCT.PRODUCT_ID 참조)';
COMMENT ON COLUMN PRODUCT_REVIEW.STAR IS '별점/평가 (예: "5", "4.5")';
COMMENT ON COLUMN PRODUCT_REVIEW.REVIEW_TEXT IS '리뷰 내용 (CLOB)';
COMMENT ON COLUMN PRODUCT_REVIEW.SOURCE IS '리뷰 출처 (예: "고객센터", "온라인몰")';
COMMENT ON COLUMN PRODUCT_REVIEW.CREATED_AT IS '리뷰 작성 일시';

-- PRODUCT_SPEC 테이블 (추가 컬럼)
COMMENT ON COLUMN PRODUCT_SPEC.PRODUCT_ID IS '제품 ID (FK, PRODUCT.PRODUCT_ID 참조)';
COMMENT ON COLUMN PRODUCT_SPEC.SPEC_KEY IS '스펙 키 (예: "용량", "화면크기")';
COMMENT ON COLUMN PRODUCT_SPEC.SPEC_VALUE IS '스펙 값 (예: "850L", "65인치")';
COMMENT ON COLUMN PRODUCT_SPEC.SPEC_TYPE IS '스펙 타입 (COMMON: 공통, SPECIFIC: 특정 variant만)';
COMMENT ON COLUMN PRODUCT_SPEC.CREATED_AT IS '생성 일시';
COMMENT ON COLUMN PRODUCT_SPEC.UPDATED_AT IS '수정 일시';

-- ============================================================
-- 완료
-- ============================================================

