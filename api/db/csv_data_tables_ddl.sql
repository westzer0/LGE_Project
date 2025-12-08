-- ============================================
-- CSV 데이터를 위한 Oracle 테이블 생성 DDL
-- ============================================

-- 1. 평균벡터 테이블 (model_name, recommend_reason 구조)
--    예: 냉장고_모델별_평균벡터.csv, 공기청정기_모델별_평균벡터.csv 등

-- 시퀀스 생성
CREATE SEQUENCE seq_product_recommend_reasons
    START WITH 1
    INCREMENT BY 1
    NOCACHE;

CREATE TABLE product_recommend_reasons (
    id NUMBER PRIMARY KEY,
    product_category VARCHAR2(100) NOT NULL,  -- 제품 카테고리 (냉장고, 공기청정기 등)
    model_name VARCHAR2(200) NOT NULL,
    recommend_reason CLOB,  -- 긴 텍스트를 위해 CLOB 사용
    created_at DATE DEFAULT SYSDATE,
    CONSTRAINT uk_product_recommend UNIQUE (product_category, model_name)
);

-- 자동 증가 트리거 생성
CREATE OR REPLACE TRIGGER trg_product_recommend_reasons
    BEFORE INSERT ON product_recommend_reasons
    FOR EACH ROW
BEGIN
    IF :NEW.id IS NULL THEN
        SELECT seq_product_recommend_reasons.NEXTVAL INTO :NEW.id FROM DUAL;
    END IF;
END;
/

-- 인덱스 생성
CREATE INDEX idx_product_recommend_category ON product_recommend_reasons(product_category);
CREATE INDEX idx_product_recommend_model ON product_recommend_reasons(model_name);

-- 2. 리뷰 인구통계 정보 테이블 (Product_code, family_list, size_list, house_list 구조)
--    예: TV_모델별_리뷰_인구통계정보.csv, 세탁기_모델별_리뷰_인구통계정보.csv 등

-- 시퀀스 생성
CREATE SEQUENCE seq_product_review_demographics
    START WITH 1
    INCREMENT BY 1
    NOCACHE;

CREATE TABLE product_review_demographics (
    id NUMBER PRIMARY KEY,
    product_category VARCHAR2(100) NOT NULL,  -- 제품 카테고리
    product_code VARCHAR2(200) NOT NULL,
    family_list CLOB,  -- JSON 배열 형태로 저장 (예: ['부모님', '신혼'])
    size_list CLOB,    -- JSON 배열 형태로 저장 (예: ['20평', '30평'])
    house_list CLOB,   -- JSON 배열 형태로 저장 (예: ['아파트', '주택'])
    created_at DATE DEFAULT SYSDATE,
    CONSTRAINT uk_product_demographics UNIQUE (product_category, product_code)
);

-- 자동 증가 트리거 생성
CREATE OR REPLACE TRIGGER trg_product_review_demographics
    BEFORE INSERT ON product_review_demographics
    FOR EACH ROW
BEGIN
    IF :NEW.id IS NULL THEN
        SELECT seq_product_review_demographics.NEXTVAL INTO :NEW.id FROM DUAL;
    END IF;
END;
/

-- 인덱스 생성
CREATE INDEX idx_product_demographics_category ON product_review_demographics(product_category);
CREATE INDEX idx_product_demographics_code ON product_review_demographics(product_code);

-- 테이블 코멘트 추가
COMMENT ON TABLE product_recommend_reasons IS '제품별 추천 이유 (평균벡터 데이터)';
COMMENT ON COLUMN product_recommend_reasons.product_category IS '제품 카테고리 (냉장고, 공기청정기 등)';
COMMENT ON COLUMN product_recommend_reasons.model_name IS '모델명';
COMMENT ON COLUMN product_recommend_reasons.recommend_reason IS '추천 이유 (사용자 리뷰 기반)';

COMMENT ON TABLE product_review_demographics IS '제품별 리뷰 인구통계 정보';
COMMENT ON COLUMN product_review_demographics.product_category IS '제품 카테고리';
COMMENT ON COLUMN product_review_demographics.product_code IS '제품 코드';
COMMENT ON COLUMN product_review_demographics.family_list IS '가족 구성 리스트 (JSON 배열)';
COMMENT ON COLUMN product_review_demographics.size_list IS '주거 크기 리스트 (JSON 배열)';
COMMENT ON COLUMN product_review_demographics.house_list IS '주거 형태 리스트 (JSON 배열)';

