-- ============================================================
-- ONBOARDING_SESSION.MEMBER_ID NULL 허용 확인 및 수정
-- ============================================================
-- 이 스크립트는 MEMBER_ID 컬럼이 NULL을 허용하는지 확인하고,
-- 허용하지 않으면 NULL 허용으로 변경합니다.
-- ============================================================

SET SERVEROUTPUT ON;

DECLARE
    v_nullable VARCHAR2(3);
    v_table_exists NUMBER;
BEGIN
    -- 1. ONBOARDING_SESSION 테이블 존재 여부 확인
    SELECT COUNT(*) INTO v_table_exists
    FROM USER_TABLES
    WHERE TABLE_NAME = 'ONBOARDING_SESSION';
    
    IF v_table_exists = 0 THEN
        DBMS_OUTPUT.PUT_LINE('[오류] ONBOARDING_SESSION 테이블이 존재하지 않습니다.');
        RETURN;
    END IF;
    
    -- 2. MEMBER_ID 컬럼 존재 여부 및 NULL 허용 여부 확인
    SELECT NULLABLE INTO v_nullable
    FROM USER_TAB_COLUMNS
    WHERE TABLE_NAME = 'ONBOARDING_SESSION'
      AND COLUMN_NAME = 'MEMBER_ID';
    
    IF v_nullable IS NULL THEN
        DBMS_OUTPUT.PUT_LINE('[오류] MEMBER_ID 컬럼이 존재하지 않습니다.');
        RETURN;
    END IF;
    
    DBMS_OUTPUT.PUT_LINE('========================================');
    DBMS_OUTPUT.PUT_LINE('MEMBER_ID NULL 허용 여부 확인');
    DBMS_OUTPUT.PUT_LINE('========================================');
    DBMS_OUTPUT.PUT_LINE('현재 상태: ' || CASE WHEN v_nullable = 'Y' THEN 'NULL 허용' ELSE 'NULL 불허용' END);
    
    -- 3. NULL 허용이 아니면 변경
    IF v_nullable = 'N' THEN
        DBMS_OUTPUT.PUT_LINE('MEMBER_ID를 NULL 허용으로 변경 중...');
        
        BEGIN
            EXECUTE IMMEDIATE 'ALTER TABLE ONBOARDING_SESSION MODIFY MEMBER_ID NULL';
            DBMS_OUTPUT.PUT_LINE('[성공] MEMBER_ID가 NULL 허용으로 변경되었습니다.');
        EXCEPTION
            WHEN OTHERS THEN
                DBMS_OUTPUT.PUT_LINE('[오류] MEMBER_ID NULL 허용 변경 실패: ' || SQLERRM);
                RAISE;
        END;
    ELSE
        DBMS_OUTPUT.PUT_LINE('[정보] MEMBER_ID는 이미 NULL 허용입니다.');
    END IF;
    
    DBMS_OUTPUT.PUT_LINE('========================================');
    
EXCEPTION
    WHEN NO_DATA_FOUND THEN
        DBMS_OUTPUT.PUT_LINE('[오류] MEMBER_ID 컬럼을 찾을 수 없습니다.');
    WHEN OTHERS THEN
        DBMS_OUTPUT.PUT_LINE('[오류] 예상치 못한 오류 발생: ' || SQLERRM);
        RAISE;
END;
/

COMMIT;

-- 확인 쿼리
SELECT 
    COLUMN_NAME,
    NULLABLE,
    DATA_TYPE,
    DATA_LENGTH
FROM USER_TAB_COLUMNS
WHERE TABLE_NAME = 'ONBOARDING_SESSION'
  AND COLUMN_NAME = 'MEMBER_ID';

