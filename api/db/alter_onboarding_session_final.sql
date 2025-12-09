-- ============================================================
-- ONBOARDING_SESSION 테이블 최종 수정 스크립트
-- ============================================================
-- 이 스크립트는 실제 Oracle DB에 적용하여 다음을 수행합니다:
-- 1. CLOB 컬럼 제거 (정규화 테이블 사용)
-- 2. MEMBER_ID 외래키 제약조건 추가
-- 3. 컬럼명 통일 (CREATED_AT, UPDATED_AT)
-- ============================================================

-- ============================================================
-- Step 1: 기존 CLOB 데이터 백업 (선택사항)
-- ============================================================
-- 필요시 기존 CLOB 데이터를 정규화 테이블로 마이그레이션 후 실행

-- ============================================================
-- Step 2: MEMBER_ID 컬럼 추가 (없는 경우)
-- ============================================================
-- MEMBER_ID 컬럼이 없는 경우에만 실행
-- ALTER TABLE ONBOARDING_SESSION ADD MEMBER_ID VARCHAR2(30);

-- ============================================================
-- Step 3: MEMBER_ID를 NULL 허용으로 변경
-- ============================================================
ALTER TABLE ONBOARDING_SESSION MODIFY MEMBER_ID NULL;

-- ============================================================
-- Step 4: CLOB 컬럼 제거
-- ============================================================
-- 주의: 데이터가 있는 경우 먼저 정규화 테이블로 마이그레이션 필요

-- MAIN_SPACE CLOB 제거
ALTER TABLE ONBOARDING_SESSION DROP COLUMN MAIN_SPACE;

-- PRIORITY_LIST CLOB 제거
ALTER TABLE ONBOARDING_SESSION DROP COLUMN PRIORITY_LIST;

-- SELECTED_CATEGORIES CLOB 제거
ALTER TABLE ONBOARDING_SESSION DROP COLUMN SELECTED_CATEGORIES;

-- RECOMMENDED_PRODUCTS CLOB 제거
ALTER TABLE ONBOARDING_SESSION DROP COLUMN RECOMMENDED_PRODUCTS;

-- RECOMMENDATION_RESULT CLOB 제거
ALTER TABLE ONBOARDING_SESSION DROP COLUMN RECOMMENDATION_RESULT;

-- ============================================================
-- Step 5: MEMBER_ID 외래키 제약조건 추가
-- ============================================================
-- 기존 제약조건이 있는 경우 먼저 제거 필요
-- ALTER TABLE ONBOARDING_SESSION DROP CONSTRAINT FK_SESSION_MEMBER;

ALTER TABLE ONBOARDING_SESSION
ADD CONSTRAINT FK_SESSION_MEMBER 
FOREIGN KEY (MEMBER_ID) REFERENCES MEMBER(MEMBER_ID);

-- ============================================================
-- Step 6: 컬럼명 통일 (CREATED_DATE -> CREATED_AT, UPDATED_DATE -> UPDATED_AT)
-- ============================================================
-- CREATED_DATE가 CREATED_AT이 아닌 경우에만 실행
-- ALTER TABLE ONBOARDING_SESSION RENAME COLUMN CREATED_DATE TO CREATED_AT;
-- ALTER TABLE ONBOARDING_SESSION RENAME COLUMN UPDATED_DATE TO UPDATED_AT;

-- ============================================================
-- Step 7: 인덱스 생성 (MEMBER_ID)
-- ============================================================
CREATE INDEX IDX_SESSION_MEMBER_ID ON ONBOARDING_SESSION(MEMBER_ID);

-- ============================================================
-- Step 8: 정규화 테이블 생성 (없는 경우)
-- ============================================================

-- ONBOARD_SESS_MAIN_SPACES 테이블 생성
BEGIN
    EXECUTE IMMEDIATE '
        CREATE TABLE ONBOARD_SESS_MAIN_SPACES (
            SESSION_ID VARCHAR2(100) NOT NULL,
            MAIN_SPACE VARCHAR2(50) NOT NULL,
            CREATED_AT DATE DEFAULT SYSDATE,
            PRIMARY KEY (SESSION_ID, MAIN_SPACE),
            CONSTRAINT FK_SESS_MAIN_SPACES 
                FOREIGN KEY (SESSION_ID) REFERENCES ONBOARDING_SESSION(SESSION_ID) ON DELETE CASCADE
        )
    ';
    DBMS_OUTPUT.PUT_LINE('ONBOARD_SESS_MAIN_SPACES 테이블 생성 완료');
EXCEPTION
    WHEN OTHERS THEN
        IF SQLCODE = -955 THEN  -- 테이블이 이미 존재하는 경우
            DBMS_OUTPUT.PUT_LINE('ONBOARD_SESS_MAIN_SPACES 테이블이 이미 존재합니다.');
        ELSE
            RAISE;
        END IF;
END;
/

CREATE INDEX IDX_SESS_MAIN_SP ON ONBOARD_SESS_MAIN_SPACES(SESSION_ID);

-- ONBOARD_SESS_PRIORITIES 테이블 생성
BEGIN
    EXECUTE IMMEDIATE '
        CREATE TABLE ONBOARD_SESS_PRIORITIES (
            SESSION_ID VARCHAR2(100) NOT NULL,
            PRIORITY VARCHAR2(20) NOT NULL,
            PRIORITY_ORDER NUMBER NOT NULL,
            CREATED_AT DATE DEFAULT SYSDATE,
            PRIMARY KEY (SESSION_ID, PRIORITY_ORDER),
            CONSTRAINT FK_SESS_PRIORITIES 
                FOREIGN KEY (SESSION_ID) REFERENCES ONBOARDING_SESSION(SESSION_ID) ON DELETE CASCADE
        )
    ';
    DBMS_OUTPUT.PUT_LINE('ONBOARD_SESS_PRIORITIES 테이블 생성 완료');
EXCEPTION
    WHEN OTHERS THEN
        IF SQLCODE = -955 THEN
            DBMS_OUTPUT.PUT_LINE('ONBOARD_SESS_PRIORITIES 테이블이 이미 존재합니다.');
        ELSE
            RAISE;
        END IF;
END;
/

CREATE INDEX IDX_SESS_PRIORITIES ON ONBOARD_SESS_PRIORITIES(SESSION_ID);

-- ONBOARD_SESS_CATEGORIES 테이블 생성
BEGIN
    EXECUTE IMMEDIATE '
        CREATE TABLE ONBOARD_SESS_CATEGORIES (
            SESSION_ID VARCHAR2(100) NOT NULL,
            CATEGORY_NAME VARCHAR2(50) NOT NULL,
            CREATED_AT DATE DEFAULT SYSDATE,
            PRIMARY KEY (SESSION_ID, CATEGORY_NAME),
            CONSTRAINT FK_SESS_CATEGORIES 
                FOREIGN KEY (SESSION_ID) REFERENCES ONBOARDING_SESSION(SESSION_ID) ON DELETE CASCADE
        )
    ';
    DBMS_OUTPUT.PUT_LINE('ONBOARD_SESS_CATEGORIES 테이블 생성 완료');
EXCEPTION
    WHEN OTHERS THEN
        IF SQLCODE = -955 THEN
            DBMS_OUTPUT.PUT_LINE('ONBOARD_SESS_CATEGORIES 테이블이 이미 존재합니다.');
        ELSE
            RAISE;
        END IF;
END;
/

CREATE INDEX IDX_SESS_CATEGORIES ON ONBOARD_SESS_CATEGORIES(SESSION_ID);

-- ONBOARD_SESS_REC_PRODUCTS 테이블 생성
BEGIN
    EXECUTE IMMEDIATE '
        CREATE TABLE ONBOARD_SESS_REC_PRODUCTS (
            SESSION_ID VARCHAR2(100) NOT NULL,
            PRODUCT_ID NUMBER NOT NULL,
            CATEGORY_NAME VARCHAR2(50),
            RANK_ORDER NUMBER,
            SCORE NUMBER(5,2),
            CREATED_AT DATE DEFAULT SYSDATE,
            PRIMARY KEY (SESSION_ID, PRODUCT_ID),
            CONSTRAINT FK_SESS_REC_PRODUCTS 
                FOREIGN KEY (SESSION_ID) REFERENCES ONBOARDING_SESSION(SESSION_ID) ON DELETE CASCADE,
            CONSTRAINT FK_SESS_REC_PRODUCT 
                FOREIGN KEY (PRODUCT_ID) REFERENCES PRODUCT(PRODUCT_ID) ON DELETE CASCADE
        )
    ';
    DBMS_OUTPUT.PUT_LINE('ONBOARD_SESS_REC_PRODUCTS 테이블 생성 완료');
EXCEPTION
    WHEN OTHERS THEN
        IF SQLCODE = -955 THEN
            DBMS_OUTPUT.PUT_LINE('ONBOARD_SESS_REC_PRODUCTS 테이블이 이미 존재합니다.');
        ELSE
            RAISE;
        END IF;
END;
/

CREATE INDEX IDX_SESS_REC_PRODUCTS ON ONBOARD_SESS_REC_PRODUCTS(SESSION_ID);
CREATE INDEX IDX_SESS_REC_PRODUCTS_CAT ON ONBOARD_SESS_REC_PRODUCTS(CATEGORY_NAME);

COMMIT;

-- ============================================================
-- 완료 메시지
-- ============================================================
SELECT 'ONBOARDING_SESSION 테이블 수정 완료' AS STATUS FROM DUAL;

