-- ============================================================
-- 컬럼별 COMMENT 추가 스크립트
-- Oracle 11g 호환
-- ============================================================
-- 이 스크립트는 모든 주요 테이블의 컬럼에 의미를 설명하는 COMMENT를 추가합니다.
-- ============================================================

-- ============================================================
-- 1. TASTE_CONFIG 테이블
-- ============================================================

COMMENT ON TABLE TASTE_CONFIG IS 'Taste별 추천 설정 관리 테이블 (1-120개의 Taste ID별 설정)';

COMMENT ON COLUMN TASTE_CONFIG.TASTE_ID IS 'Taste ID (1-120 범위, PRIMARY KEY)';
COMMENT ON COLUMN TASTE_CONFIG.DESCRIPTION IS 'Taste에 대한 설명 (예: "모던 스타일, 1인 가구")';
COMMENT ON COLUMN TASTE_CONFIG.REPRESENTATIVE_VIBE IS '대표 인테리어 무드 (modern/cozy/pop/luxury)';
COMMENT ON COLUMN TASTE_CONFIG.REPRESENTATIVE_HOUSEHOLD_SIZE IS '대표 가구 인원수 (1-5인)';
COMMENT ON COLUMN TASTE_CONFIG.REPRESENTATIVE_MAIN_SPACE IS '대표 주요 공간 (living/kitchen/bedroom/dressing 등)';
COMMENT ON COLUMN TASTE_CONFIG.REPRESENTATIVE_HAS_PET IS '대표 반려동물 여부 (Y/N)';
COMMENT ON COLUMN TASTE_CONFIG.REPRESENTATIVE_PRIORITY IS '대표 구매 우선순위 (design/tech/eco/value)';
COMMENT ON COLUMN TASTE_CONFIG.REPRESENTATIVE_BUDGET_LEVEL IS '대표 예산 수준 (low/medium/high/premium/luxury)';
COMMENT ON COLUMN TASTE_CONFIG.RECOMMENDED_CATEGORIES IS '추천 MAIN_CATEGORY 리스트 (JSON 배열: ["TV", "냉장고", "에어컨"])';
COMMENT ON COLUMN TASTE_CONFIG.CATEGORY_SCORES IS '카테고리별 점수 매핑 (JSON 객체: {"TV": 85.0, "냉장고": 70.0})';
COMMENT ON COLUMN TASTE_CONFIG.RECOMMENDED_PRODUCTS IS '카테고리별 추천 제품 ID 매핑 (JSON 객체: {"TV": [1,2,3], "냉장고": [...]})';
COMMENT ON COLUMN TASTE_CONFIG.RECOMMENDED_PRODUCT_SCORES IS '카테고리별 추천 제품 점수 매핑 (JSON 객체, RECOMMENDED_PRODUCTS와 1:1 매핑)';
COMMENT ON COLUMN TASTE_CONFIG.ILL_SUITED_CATEGORIES IS '부적합 카테고리 리스트 (JSON 배열: ["의류관리기"])';
COMMENT ON COLUMN TASTE_CONFIG.IS_ACTIVE IS '활성화 여부 (Y/N, 기본값: Y)';
COMMENT ON COLUMN TASTE_CONFIG.AUTO_GENERATED IS '자동 생성 여부 (Y/N, 기본값: N)';
COMMENT ON COLUMN TASTE_CONFIG.LAST_SIMULATION_DATE IS '마지막 시뮬레이션 실행 일시';
COMMENT ON COLUMN TASTE_CONFIG.CREATED_AT IS '생성 일시 (기본값: SYSDATE)';
COMMENT ON COLUMN TASTE_CONFIG.UPDATED_AT IS '수정 일시 (기본값: SYSDATE)';

-- ============================================================
-- 2. TASTE_CATEGORY_SCORES 테이블 (정규화된 테이블)
-- ============================================================

COMMENT ON TABLE TASTE_CATEGORY_SCORES IS 'Taste별 카테고리 점수 관리 테이블 (정규화)';

COMMENT ON COLUMN TASTE_CATEGORY_SCORES.TASTE_ID IS 'Taste ID (FK, TASTE_CONFIG 참조)';
COMMENT ON COLUMN TASTE_CATEGORY_SCORES.CATEGORY_NAME IS '카테고리명 (예: "TV", "냉장고", "에어컨")';
COMMENT ON COLUMN TASTE_CATEGORY_SCORES.SCORE IS '카테고리 점수 (0~100점, NUMBER(5,2))';
COMMENT ON COLUMN TASTE_CATEGORY_SCORES.IS_RECOMMENDED IS '추천 카테고리 여부 (Y/N, 기본값: N)';
COMMENT ON COLUMN TASTE_CATEGORY_SCORES.IS_ILL_SUITED IS '부적합 카테고리 여부 (Y/N, 기본값: N)';
COMMENT ON COLUMN TASTE_CATEGORY_SCORES.CREATED_AT IS '생성 일시 (기본값: SYSDATE)';
COMMENT ON COLUMN TASTE_CATEGORY_SCORES.UPDATED_AT IS '수정 일시 (기본값: SYSDATE)';

-- ============================================================
-- 3. TASTE_RECOMMENDED_PRODUCTS 테이블 (정규화된 테이블)
-- ============================================================

COMMENT ON TABLE TASTE_RECOMMENDED_PRODUCTS IS 'Taste별 추천 제품 관리 테이블 (정규화)';

COMMENT ON COLUMN TASTE_RECOMMENDED_PRODUCTS.TASTE_ID IS 'Taste ID (FK, TASTE_CONFIG 참조)';
COMMENT ON COLUMN TASTE_RECOMMENDED_PRODUCTS.CATEGORY_NAME IS '카테고리명 (예: "TV", "냉장고")';
COMMENT ON COLUMN TASTE_RECOMMENDED_PRODUCTS.PRODUCT_ID IS '제품 ID (FK, PRODUCT 테이블 참조)';
COMMENT ON COLUMN TASTE_RECOMMENDED_PRODUCTS.SCORE IS '해당 제품의 점수 (0~100점, NUMBER(5,2))';
COMMENT ON COLUMN TASTE_RECOMMENDED_PRODUCTS.RANK_ORDER IS '카테고리 내 순위 (1, 2, 3...)';
COMMENT ON COLUMN TASTE_RECOMMENDED_PRODUCTS.CREATED_AT IS '생성 일시 (기본값: SYSDATE)';
COMMENT ON COLUMN TASTE_RECOMMENDED_PRODUCTS.UPDATED_AT IS '수정 일시 (기본값: SYSDATE)';

-- ============================================================
-- 4. PRODUCT 테이블
-- ============================================================

COMMENT ON TABLE PRODUCT IS 'LG 가전 제품 정보 테이블';

COMMENT ON COLUMN PRODUCT.PRODUCT_ID IS '제품 ID (PRIMARY KEY)';
COMMENT ON COLUMN PRODUCT.MODEL_CODE IS '모델 코드 (예: "OLED65C3PSA")';
COMMENT ON COLUMN PRODUCT.PRODUCT_NAME IS '제품명 (예: "LG 올레드 TV 65인치")';
COMMENT ON COLUMN PRODUCT.MAIN_CATEGORY IS '메인 카테고리 (예: "TV", "냉장고", "세탁기")';
COMMENT ON COLUMN PRODUCT.CATEGORY IS '세부 카테고리 (예: "TV", "KITCHEN", "LIVING")';
COMMENT ON COLUMN PRODUCT.PRICE IS '제품 가격 (원 단위)';
COMMENT ON COLUMN PRODUCT.DISCOUNT_PRICE IS '할인 가격 (원 단위, NULL 가능)';
COMMENT ON COLUMN PRODUCT.IMAGE_URL IS '제품 이미지 URL';
COMMENT ON COLUMN PRODUCT.STATUS IS '판매 상태 (예: "판매중", "품절")';
COMMENT ON COLUMN PRODUCT.CREATED_AT IS '생성 일시';
COMMENT ON COLUMN PRODUCT.UPDATED_AT IS '수정 일시';

-- ============================================================
-- 5. PRODUCT_SPEC 테이블
-- ============================================================

COMMENT ON TABLE PRODUCT_SPEC IS '제품 스펙 정보 테이블 (EAV 패턴)';

COMMENT ON COLUMN PRODUCT_SPEC.PRODUCT_ID IS '제품 ID (FK, PRODUCT 참조)';
COMMENT ON COLUMN PRODUCT_SPEC.SPEC_KEY IS '스펙 키 (예: "용량", "화면크기", "해상도", "에너지효율")';
COMMENT ON COLUMN PRODUCT_SPEC.SPEC_VALUE IS '스펙 값 (예: "850L", "65인치", "4K", "1등급")';
COMMENT ON COLUMN PRODUCT_SPEC.SPEC_TYPE IS '스펙 타입 (COMMON: 모든 variant에 공통, SPECIFIC: 특정 variant만)';
COMMENT ON COLUMN PRODUCT_SPEC.CREATED_AT IS '생성 일시';
COMMENT ON COLUMN PRODUCT_SPEC.UPDATED_AT IS '수정 일시';

-- ============================================================
-- 6. ONBOARDING_SESSION 테이블
-- ============================================================

COMMENT ON TABLE ONBOARDING_SESSION IS '온보딩 세션 정보 테이블 (사용자 설문 응답 저장)';

COMMENT ON COLUMN ONBOARDING_SESSION.SESSION_ID IS '세션 ID (PRIMARY KEY, UUID 또는 고유 문자열)';
COMMENT ON COLUMN ONBOARDING_SESSION.USER_ID IS '사용자 ID (선택적, 카카오 로그인 연동 시)';
COMMENT ON COLUMN ONBOARDING_SESSION.CURRENT_STEP IS '현재 진행 단계 (1~6, 기본값: 1)';
COMMENT ON COLUMN ONBOARDING_SESSION.STATUS IS '상태 (IN_PROGRESS: 진행중, COMPLETED: 완료, ABANDONED: 포기)';
COMMENT ON COLUMN ONBOARDING_SESSION.VIBE IS 'Step 1: 인테리어 무드 (modern/cozy/pop/luxury)';
COMMENT ON COLUMN ONBOARDING_SESSION.HOUSEHOLD_SIZE IS 'Step 2: 가구 인원수 (1-5인)';
COMMENT ON COLUMN ONBOARDING_SESSION.HAS_PET IS 'Step 2: 반려동물 여부 (Y/N)';
COMMENT ON COLUMN ONBOARDING_SESSION.HOUSING_TYPE IS 'Step 3: 주거 형태 (apartment/detached/villa/officetel/studio)';
COMMENT ON COLUMN ONBOARDING_SESSION.PYUNG IS 'Step 3: 평수 (예: 25평)';
COMMENT ON COLUMN ONBOARDING_SESSION.MAIN_SPACE IS 'Step 3: 주요 공간 (JSON 배열 문자열: ["living", "kitchen"])';
COMMENT ON COLUMN ONBOARDING_SESSION.COOKING IS 'Step 4: 요리 빈도 (rarely/sometimes/often)';
COMMENT ON COLUMN ONBOARDING_SESSION.LAUNDRY IS 'Step 4: 세탁 빈도 (weekly/few_times/daily)';
COMMENT ON COLUMN ONBOARDING_SESSION.MEDIA IS 'Step 4: 미디어 사용 패턴 (ott/gaming/tv/none)';
COMMENT ON COLUMN ONBOARDING_SESSION.PRIORITY IS 'Step 5: 첫 번째 우선순위 (design/tech/eco/value)';
COMMENT ON COLUMN ONBOARDING_SESSION.PRIORITY_LIST IS 'Step 5: 우선순위 목록 (JSON 배열 문자열: ["design", "tech", "eco"])';
COMMENT ON COLUMN ONBOARDING_SESSION.BUDGET_LEVEL IS 'Step 6: 예산 범위 (budget/standard/premium)';
COMMENT ON COLUMN ONBOARDING_SESSION.SELECTED_CATEGORIES IS '선택한 카테고리 (JSON 배열 문자열: ["TV", "냉장고"])';
COMMENT ON COLUMN ONBOARDING_SESSION.RECOMMENDED_PRODUCTS IS '추천 제품 ID 목록 (JSON 배열 문자열: [1, 2, 3])';
COMMENT ON COLUMN ONBOARDING_SESSION.RECOMMENDATION_RESULT IS '최종 추천 결과 (JSON 객체 문자열)';
COMMENT ON COLUMN ONBOARDING_SESSION.CREATED_AT IS '생성 일시 (기본값: SYSDATE)';
COMMENT ON COLUMN ONBOARDING_SESSION.UPDATED_AT IS '수정 일시 (기본값: SYSDATE)';
COMMENT ON COLUMN ONBOARDING_SESSION.COMPLETED_AT IS '완료 일시 (STATUS가 COMPLETED일 때 설정)';

-- ============================================================
-- 7. MEMBER 테이블 (사용자 정보)
-- ============================================================

COMMENT ON TABLE MEMBER IS '회원 정보 테이블';

COMMENT ON COLUMN MEMBER.MEMBER_ID IS '회원 ID (PRIMARY KEY)';
COMMENT ON COLUMN MEMBER.USER_ID IS '사용자 ID (카카오 로그인 연동 시)';
COMMENT ON COLUMN MEMBER.TASTE IS '할당된 Taste ID (1-120 범위, NULL 가능)';
COMMENT ON COLUMN MEMBER.CREATED_AT IS '생성 일시';
COMMENT ON COLUMN MEMBER.UPDATED_AT IS '수정 일시';

-- ============================================================
-- 8. ONBOARDING_QUESTION 테이블
-- ============================================================

COMMENT ON TABLE ONBOARDING_QUESTION IS '온보딩 질문 항목 테이블';

COMMENT ON COLUMN ONBOARDING_QUESTION.QUESTION_ID IS '질문 ID (PRIMARY KEY)';
COMMENT ON COLUMN ONBOARDING_QUESTION.STEP_NUMBER IS '단계 번호 (1~6)';
COMMENT ON COLUMN ONBOARDING_QUESTION.QUESTION_TYPE IS '질문 유형 (vibe/mate/housing_type/cooking/laundry/media/priority/budget)';
COMMENT ON COLUMN ONBOARDING_QUESTION.QUESTION_TEXT IS '질문 텍스트';
COMMENT ON COLUMN ONBOARDING_QUESTION.QUESTION_ORDER IS '질문 순서 (같은 단계 내에서)';
COMMENT ON COLUMN ONBOARDING_QUESTION.IS_REQUIRED IS '필수 여부 (Y/N, 기본값: Y)';
COMMENT ON COLUMN ONBOARDING_QUESTION.CONDITION_TYPE IS '조건부 질문 타입 (예: kitchen_selected, dressing_selected)';
COMMENT ON COLUMN ONBOARDING_QUESTION.CONDITION_VALUE IS '조건 값';
COMMENT ON COLUMN ONBOARDING_QUESTION.CREATED_AT IS '생성 일시 (기본값: SYSDATE)';
COMMENT ON COLUMN ONBOARDING_QUESTION.UPDATED_AT IS '수정 일시 (기본값: SYSDATE)';

-- ============================================================
-- 9. ONBOARDING_ANSWER 테이블
-- ============================================================

COMMENT ON TABLE ONBOARDING_ANSWER IS '온보딩 선택지 항목 테이블';

COMMENT ON COLUMN ONBOARDING_ANSWER.ANSWER_ID IS '선택지 ID (PRIMARY KEY)';
COMMENT ON COLUMN ONBOARDING_ANSWER.QUESTION_ID IS '질문 ID (FK, ONBOARDING_QUESTION 참조)';
COMMENT ON COLUMN ONBOARDING_ANSWER.ANSWER_VALUE IS '선택지 값 (예: modern, alone, apartment)';
COMMENT ON COLUMN ONBOARDING_ANSWER.ANSWER_TEXT IS '선택지 텍스트 (예: "모던 & 미니멀", "나 혼자 산다")';
COMMENT ON COLUMN ONBOARDING_ANSWER.ANSWER_ORDER IS '선택지 순서';
COMMENT ON COLUMN ONBOARDING_ANSWER.IMAGE_URL IS '이미지 URL (있는 경우)';
COMMENT ON COLUMN ONBOARDING_ANSWER.IS_ACTIVE IS '활성화 여부 (Y/N, 기본값: Y)';
COMMENT ON COLUMN ONBOARDING_ANSWER.CREATED_AT IS '생성 일시 (기본값: SYSDATE)';
COMMENT ON COLUMN ONBOARDING_ANSWER.UPDATED_AT IS '수정 일시 (기본값: SYSDATE)';

-- ============================================================
-- 10. ONBOARDING_USER_RESPONSE 테이블
-- ============================================================

COMMENT ON TABLE ONBOARDING_USER_RESPONSE IS '온보딩 사용자 선택지 결과 항목 테이블';

COMMENT ON COLUMN ONBOARDING_USER_RESPONSE.RESPONSE_ID IS '응답 ID (PRIMARY KEY)';
COMMENT ON COLUMN ONBOARDING_USER_RESPONSE.SESSION_ID IS '세션 ID (FK, ONBOARDING_SESSION 참조)';
COMMENT ON COLUMN ONBOARDING_USER_RESPONSE.QUESTION_ID IS '질문 ID (FK, ONBOARDING_QUESTION 참조)';
COMMENT ON COLUMN ONBOARDING_USER_RESPONSE.ANSWER_ID IS '선택지 ID (FK, ONBOARDING_ANSWER 참조, 단일 선택인 경우)';
COMMENT ON COLUMN ONBOARDING_USER_RESPONSE.ANSWER_VALUE IS '선택한 값 (다중 선택인 경우 직접 저장)';
COMMENT ON COLUMN ONBOARDING_USER_RESPONSE.RESPONSE_TEXT IS '텍스트 입력 값 (평수 등)';
COMMENT ON COLUMN ONBOARDING_USER_RESPONSE.STEP_NUMBER IS '단계 번호';
COMMENT ON COLUMN ONBOARDING_USER_RESPONSE.CREATED_AT IS '생성 일시 (기본값: SYSDATE)';

-- ============================================================
-- 실행 방법
-- ============================================================
-- 1. SQL*Plus 또는 SQL Developer에서 실행
-- 2. 또는 Python 스크립트로 실행:
--    python manage.py execute_sql_file api/db/add_column_comments.sql
-- ============================================================


