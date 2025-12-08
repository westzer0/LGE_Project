-- ============================================================
-- TASTE_CONFIG 테이블에 RECOMMENDED_CATEGORIES_WITH_SCORES 컬럼 추가
-- ============================================================

-- 컬럼 추가 (Oracle 11g는 컬럼명 30자 제한)
ALTER TABLE TASTE_CONFIG
ADD CATEGORY_SCORES CLOB;

-- 주석 추가
COMMENT ON COLUMN TASTE_CONFIG.CATEGORY_SCORES IS '카테고리별 점수 매핑 (JSON 객체: {"TV": 85.0, "냉장고": 70.0})';

