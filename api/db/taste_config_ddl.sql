-- ============================================================
-- Taste 설정 관리 테이블 DDL
-- Oracle 11g 호환
-- ============================================================

-- TASTE_CONFIG: Taste별 추천 설정 관리
CREATE TABLE TASTE_CONFIG (
    TASTE_ID NUMBER PRIMARY KEY,  -- Taste ID (1-120)
    
    -- Taste 설명
    DESCRIPTION VARCHAR2(500),
    
    -- 대표 온보딩 특성 (참고용)
    REPRESENTATIVE_VIBE VARCHAR2(20),
    REPRESENTATIVE_HOUSEHOLD_SIZE NUMBER,
    REPRESENTATIVE_MAIN_SPACE VARCHAR2(50),
    REPRESENTATIVE_HAS_PET CHAR(1),  -- 'Y'/'N'
    REPRESENTATIVE_PRIORITY VARCHAR2(20),
    REPRESENTATIVE_BUDGET_LEVEL VARCHAR2(20),
    
    -- 추천 카테고리 (JSON 또는 CLOB)
    RECOMMENDED_CATEGORIES CLOB,  -- JSON 배열: ["TV", "냉장고", "에어컨"]
    
    -- 추천 카테고리와 점수 (JSON 객체)
    -- 구조: {"TV": 85.0, "냉장고": 70.0, "에어컨": 65.0}
    -- Oracle 11g는 컬럼명 30자 제한으로 CATEGORY_SCORES 사용
    CATEGORY_SCORES CLOB,  -- JSON 객체: 카테고리별 점수 (0~100점)
    
    -- 추천 제품 모델 (카테고리별 상위 3개씩, JSON)
    -- 구조: {"TV": [product_id1, product_id2, product_id3], "냉장고": [...]}
    RECOMMENDED_PRODUCTS CLOB,  -- JSON 객체
    
    -- 메타 정보
    IS_ACTIVE CHAR(1) DEFAULT 'Y',  -- 'Y'/'N'
    AUTO_GENERATED CHAR(1) DEFAULT 'N',  -- 'Y'/'N'
    LAST_SIMULATION_DATE DATE,
    
    CREATED_AT DATE DEFAULT SYSDATE,
    UPDATED_AT DATE DEFAULT SYSDATE
);

-- 인덱스 생성
CREATE INDEX IDX_TASTE_CONFIG_ACTIVE ON TASTE_CONFIG(IS_ACTIVE);
CREATE INDEX IDX_TASTE_CONFIG_UPDATED ON TASTE_CONFIG(UPDATED_AT);

-- 주석 추가
COMMENT ON TABLE TASTE_CONFIG IS 'Taste별 추천 설정 관리 테이블';
COMMENT ON COLUMN TASTE_CONFIG.TASTE_ID IS 'Taste ID (1-120)';
COMMENT ON COLUMN TASTE_CONFIG.RECOMMENDED_CATEGORIES IS '추천 MAIN_CATEGORY 리스트 (JSON 배열)';
COMMENT ON COLUMN TASTE_CONFIG.CATEGORY_SCORES IS '카테고리별 점수 매핑 (JSON 객체: {"TV": 85.0, "냉장고": 70.0})';
COMMENT ON COLUMN TASTE_CONFIG.RECOMMENDED_PRODUCTS IS '카테고리별 추천 제품 ID 매핑 (JSON 객체)';

-- 샘플 데이터 삽입 (예시)
-- INSERT INTO TASTE_CONFIG (
--     TASTE_ID, DESCRIPTION, REPRESENTATIVE_VIBE, REPRESENTATIVE_HOUSEHOLD_SIZE,
--     RECOMMENDED_CATEGORIES, RECOMMENDED_PRODUCTS, IS_ACTIVE, AUTO_GENERATED
-- ) VALUES (
--     1, '모던 스타일, 1인 가구', 'modern', 1,
--     '["TV", "냉장고", "에어컨", "청소기", "공기청정기"]',
--     '{"TV": [1, 2, 3], "냉장고": [10, 11, 12], "에어컨": [20, 21, 22]}',
--     'Y', 'N'
-- );

