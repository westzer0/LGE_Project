-- ============================================================
-- 온보딩 테이블 칼럼 추가 (ALTER TABLE만)
-- Oracle 11g 호환
-- ============================================================

-- ONBOARDING_SESSION 테이블에 추가 칼럼 추가
-- 이미 존재하는 칼럼은 무시됩니다 (ORA-01430: column already exists)

BEGIN
    -- HAS_PET 추가
    BEGIN
        EXECUTE IMMEDIATE 'ALTER TABLE ONBOARDING_SESSION ADD (HAS_PET CHAR(1))';
        DBMS_OUTPUT.PUT_LINE('HAS_PET 칼럼 추가 완료');
    EXCEPTION
        WHEN OTHERS THEN
            IF SQLCODE = -1430 THEN
                DBMS_OUTPUT.PUT_LINE('HAS_PET 칼럼은 이미 존재합니다');
            ELSE
                RAISE;
            END IF;
    END;
    
    -- MAIN_SPACE 추가
    BEGIN
        EXECUTE IMMEDIATE 'ALTER TABLE ONBOARDING_SESSION ADD (MAIN_SPACE CLOB)';
        DBMS_OUTPUT.PUT_LINE('MAIN_SPACE 칼럼 추가 완료');
    EXCEPTION
        WHEN OTHERS THEN
            IF SQLCODE = -1430 THEN
                DBMS_OUTPUT.PUT_LINE('MAIN_SPACE 칼럼은 이미 존재합니다');
            ELSE
                RAISE;
            END IF;
    END;
    
    -- COOKING 추가
    BEGIN
        EXECUTE IMMEDIATE 'ALTER TABLE ONBOARDING_SESSION ADD (COOKING VARCHAR2(20))';
        DBMS_OUTPUT.PUT_LINE('COOKING 칼럼 추가 완료');
    EXCEPTION
        WHEN OTHERS THEN
            IF SQLCODE = -1430 THEN
                DBMS_OUTPUT.PUT_LINE('COOKING 칼럼은 이미 존재합니다');
            ELSE
                RAISE;
            END IF;
    END;
    
    -- LAUNDRY 추가
    BEGIN
        EXECUTE IMMEDIATE 'ALTER TABLE ONBOARDING_SESSION ADD (LAUNDRY VARCHAR2(20))';
        DBMS_OUTPUT.PUT_LINE('LAUNDRY 칼럼 추가 완료');
    EXCEPTION
        WHEN OTHERS THEN
            IF SQLCODE = -1430 THEN
                DBMS_OUTPUT.PUT_LINE('LAUNDRY 칼럼은 이미 존재합니다');
            ELSE
                RAISE;
            END IF;
    END;
    
    -- MEDIA 추가
    BEGIN
        EXECUTE IMMEDIATE 'ALTER TABLE ONBOARDING_SESSION ADD (MEDIA VARCHAR2(20))';
        DBMS_OUTPUT.PUT_LINE('MEDIA 칼럼 추가 완료');
    EXCEPTION
        WHEN OTHERS THEN
            IF SQLCODE = -1430 THEN
                DBMS_OUTPUT.PUT_LINE('MEDIA 칼럼은 이미 존재합니다');
            ELSE
                RAISE;
            END IF;
    END;
    
    -- PRIORITY_LIST 추가
    BEGIN
        EXECUTE IMMEDIATE 'ALTER TABLE ONBOARDING_SESSION ADD (PRIORITY_LIST CLOB)';
        DBMS_OUTPUT.PUT_LINE('PRIORITY_LIST 칼럼 추가 완료');
    EXCEPTION
        WHEN OTHERS THEN
            IF SQLCODE = -1430 THEN
                DBMS_OUTPUT.PUT_LINE('PRIORITY_LIST 칼럼은 이미 존재합니다');
            ELSE
                RAISE;
            END IF;
    END;
    
    COMMIT;
    DBMS_OUTPUT.PUT_LINE('모든 칼럼 추가 작업 완료');
END;
/

