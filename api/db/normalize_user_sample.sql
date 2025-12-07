-- ============================================================
-- USER_SAMPLE 정규화 마이그레이션 스크립트
-- ============================================================
-- 이 스크립트는 USER_SAMPLE 테이블의 추천 제품 정보를
-- 정규화된 테이블로 분리합니다.
-- ============================================================

-- ============================================================
-- Step 1: 새 테이블 생성
-- ============================================================

-- 1.1 USER_SAMPLE_RECOMMENDATIONS 테이블 생성
CREATE TABLE USER_SAMPLE_RECOMMENDATIONS (
    USER_ID VARCHAR2(50) NOT NULL,
    CATEGORY_NAME VARCHAR2(50) NOT NULL,
    RECOMMENDED_VALUE VARCHAR2(100),
    RECOMMENDED_UNIT VARCHAR2(20),
    CREATED_AT DATE DEFAULT SYSDATE,
    PRIMARY KEY (USER_ID, CATEGORY_NAME),
    FOREIGN KEY (USER_ID) REFERENCES USER_SAMPLE(USER_ID) ON DELETE CASCADE
);

CREATE INDEX IDX_USER_SAMPLE_REC_USER ON USER_SAMPLE_RECOMMENDATIONS(USER_ID);
CREATE INDEX IDX_USER_SAMPLE_REC_CATEGORY ON USER_SAMPLE_RECOMMENDATIONS(CATEGORY_NAME);

COMMENT ON TABLE USER_SAMPLE_RECOMMENDATIONS IS '사용자 샘플별 추천 제품 정보 (정규화)';
COMMENT ON COLUMN USER_SAMPLE_RECOMMENDATIONS.USER_ID IS '사용자 ID (FK)';
COMMENT ON COLUMN USER_SAMPLE_RECOMMENDATIONS.CATEGORY_NAME IS '카테고리명 (예: "냉장고", "세탁기", "TV")';
COMMENT ON COLUMN USER_SAMPLE_RECOMMENDATIONS.RECOMMENDED_VALUE IS '추천 값 (예: "850", "15", "65")';
COMMENT ON COLUMN USER_SAMPLE_RECOMMENDATIONS.RECOMMENDED_UNIT IS '추천 단위 (예: "L", "KG", "INCH")';
COMMENT ON COLUMN USER_SAMPLE_RECOMMENDATIONS.CREATED_AT IS '생성 일시';

-- 1.2 USER_SAMPLE_PURCHASED_ITEMS 테이블 생성
CREATE TABLE USER_SAMPLE_PURCHASED_ITEMS (
    USER_ID VARCHAR2(50) NOT NULL,
    PRODUCT_ID NUMBER NOT NULL,
    PURCHASED_AT DATE,
    CREATED_AT DATE DEFAULT SYSDATE,
    PRIMARY KEY (USER_ID, PRODUCT_ID),
    FOREIGN KEY (USER_ID) REFERENCES USER_SAMPLE(USER_ID) ON DELETE CASCADE
);

CREATE INDEX IDX_USER_SAMPLE_PURCH_USER ON USER_SAMPLE_PURCHASED_ITEMS(USER_ID);
CREATE INDEX IDX_USER_SAMPLE_PURCH_PRODUCT ON USER_SAMPLE_PURCHASED_ITEMS(PRODUCT_ID);

COMMENT ON TABLE USER_SAMPLE_PURCHASED_ITEMS IS '사용자 샘플별 구매한 제품 (정규화)';
COMMENT ON COLUMN USER_SAMPLE_PURCHASED_ITEMS.USER_ID IS '사용자 ID (FK)';
COMMENT ON COLUMN USER_SAMPLE_PURCHASED_ITEMS.PRODUCT_ID IS '제품 ID';
COMMENT ON COLUMN USER_SAMPLE_PURCHASED_ITEMS.PURCHASED_AT IS '구매 일시';
COMMENT ON COLUMN USER_SAMPLE_PURCHASED_ITEMS.CREATED_AT IS '생성 일시';

-- ============================================================
-- Step 2: 데이터 마이그레이션
-- ============================================================
-- 주의: Django ORM을 사용하는 경우 Python 스크립트로 마이그레이션
-- ============================================================

-- 데이터 마이그레이션은 Python 스크립트로 수행
-- api/management/commands/migrate_user_sample_to_normalized.py 참고

-- ============================================================
-- Step 3: 기존 컬럼 제거 (선택사항, 마이그레이션 완료 후)
-- ============================================================
-- 주의: 모든 코드가 새 구조를 사용하는지 확인 후 실행
-- ============================================================

-- ALTER TABLE USER_SAMPLE DROP COLUMN RECOMMENDED_FRIDGE_L;
-- ALTER TABLE USER_SAMPLE DROP COLUMN RECOMMENDED_WASHER_KG;
-- ALTER TABLE USER_SAMPLE DROP COLUMN RECOMMENDED_TV_INCH;
-- ALTER TABLE USER_SAMPLE DROP COLUMN RECOMMENDED_VACUUM;
-- ALTER TABLE USER_SAMPLE DROP COLUMN RECOMMENDED_OVEN;
-- ALTER TABLE USER_SAMPLE DROP COLUMN PURCHASED_ITEMS;

-- ============================================================
-- 롤백 스크립트 (필요시)
-- ============================================================

-- DROP TABLE USER_SAMPLE_PURCHASED_ITEMS;
-- DROP TABLE USER_SAMPLE_RECOMMENDATIONS;


