-- ============================================================
-- ONBOARDING_SESSION 테이블에 TASTE_ID 컬럼 추가
-- Oracle 11g 호환
-- ============================================================

BEGIN
    -- TASTE_ID 컬럼 추가
    BEGIN
        EXECUTE IMMEDIATE 'ALTER TABLE ONBOARDING_SESSION ADD (TASTE_ID NUMBER(4))';
        DBMS_OUTPUT.PUT_LINE('TASTE_ID 컬럼 추가 완료');
    EXCEPTION
        WHEN OTHERS THEN
            IF SQLCODE = -1430 THEN
                DBMS_OUTPUT.PUT_LINE('TASTE_ID 컬럼은 이미 존재합니다');
            ELSE
                RAISE;
            END IF;
    END;
    
    -- 인덱스 생성
    BEGIN
        EXECUTE IMMEDIATE 'CREATE INDEX IDX_SESSION_TASTE_ID ON ONBOARDING_SESSION(TASTE_ID)';
        DBMS_OUTPUT.PUT_LINE('TASTE_ID 인덱스 생성 완료');
    EXCEPTION
        WHEN OTHERS THEN
            IF SQLCODE = -955 THEN
                DBMS_OUTPUT.PUT_LINE('TASTE_ID 인덱스는 이미 존재합니다');
            ELSE
                RAISE;
            END IF;
    END;
    
    -- 외래키 제약조건 추가 (선택사항)
    BEGIN
        EXECUTE IMMEDIATE 'ALTER TABLE ONBOARDING_SESSION ADD CONSTRAINT FK_SESSION_TASTE FOREIGN KEY (TASTE_ID) REFERENCES TASTE_CONFIG(TASTE_ID)';
        DBMS_OUTPUT.PUT_LINE('TASTE_ID 외래키 제약조건 추가 완료');
    EXCEPTION
        WHEN OTHERS THEN
            IF SQLCODE = -2260 THEN
                DBMS_OUTPUT.PUT_LINE('TASTE_ID 외래키 제약조건은 이미 존재합니다');
            ELSE
                -- 외래키 제약조건 추가 실패는 무시 (TASTE_CONFIG 테이블이 없을 수 있음)
                DBMS_OUTPUT.PUT_LINE('TASTE_ID 외래키 제약조건 추가 실패 (무시됨)');
            END IF;
    END;
    
    COMMIT;
    DBMS_OUTPUT.PUT_LINE('ONBOARDING_SESSION.TASTE_ID 컬럼 추가 완료');
END;
/

-- 주석 추가
COMMENT ON COLUMN ONBOARDING_SESSION.TASTE_ID IS '매칭된 Taste ID (1-1920, TASTE_CONFIG와 비교하여 설정)';




