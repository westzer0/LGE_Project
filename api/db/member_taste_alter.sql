-- ============================================================
-- MEMBER 테이블 TASTE 칼럼 수정
-- Oracle 11g 호환
-- TASTE를 1~1920 범위의 정수(NUMBER)로 보장
-- ============================================================

-- 1. 기존 TASTE 칼럼이 있으면 삭제 (데이터 백업 필요 시 별도 처리)
-- 주의: 이 스크립트는 TASTE 칼럼을 NUMBER(4)로 변경합니다.
-- 기존 데이터가 있으면 먼저 백업하세요.

BEGIN
    -- TASTE 칼럼이 VARCHAR2나 다른 타입이면 삭제 후 재생성
    BEGIN
        EXECUTE IMMEDIATE 'ALTER TABLE MEMBER DROP COLUMN TASTE';
        DBMS_OUTPUT.PUT_LINE('기존 TASTE 칼럼 삭제 완료');
    EXCEPTION
        WHEN OTHERS THEN
            IF SQLCODE = -904 THEN
                DBMS_OUTPUT.PUT_LINE('TASTE 칼럼이 존재하지 않습니다');
            ELSE
                RAISE;
            END IF;
    END;
    
    -- TASTE 칼럼 추가 (NUMBER(4), 1~1920 범위)
    BEGIN
        EXECUTE IMMEDIATE 'ALTER TABLE MEMBER ADD (TASTE NUMBER(4))';
        DBMS_OUTPUT.PUT_LINE('TASTE 칼럼 추가 완료 (NUMBER(4))');
    EXCEPTION
        WHEN OTHERS THEN
            IF SQLCODE = -1430 THEN
                DBMS_OUTPUT.PUT_LINE('TASTE 칼럼은 이미 존재합니다');
            ELSE
                RAISE;
            END IF;
    END;
    
    -- CHECK 제약조건 추가 (1~1920 범위)
    BEGIN
        EXECUTE IMMEDIATE 'ALTER TABLE MEMBER ADD CONSTRAINT CHK_TASTE_RANGE CHECK (TASTE IS NULL OR (TASTE >= 1 AND TASTE <= 1920))';
        DBMS_OUTPUT.PUT_LINE('TASTE 범위 제약조건 추가 완료 (1~1920)');
    EXCEPTION
        WHEN OTHERS THEN
            IF SQLCODE = -2260 THEN
                DBMS_OUTPUT.PUT_LINE('TASTE 범위 제약조건은 이미 존재합니다');
            ELSE
                RAISE;
            END IF;
    END;
    
    COMMIT;
    DBMS_OUTPUT.PUT_LINE('MEMBER.TASTE 칼럼 수정 완료');
END;
/

-- ============================================================
-- 기존 데이터 정리 (선택사항)
-- ============================================================
-- 기존 TASTE 값이 1~1920 범위를 벗어나면 NULL로 설정하거나
-- 범위 내 값으로 변환하는 스크립트입니다.

-- 예시: 범위를 벗어난 값은 NULL로 설정
-- UPDATE MEMBER 
-- SET TASTE = NULL 
-- WHERE TASTE IS NOT NULL AND (TASTE < 1 OR TASTE > 1920);

-- 예시: 범위를 벗어난 값을 1~1920 범위로 변환 (나머지 연산)
-- UPDATE MEMBER 
-- SET TASTE = MOD(ABS(TASTE), 1920) + 1 
-- WHERE TASTE IS NOT NULL AND (TASTE < 1 OR TASTE > 1920);

-- COMMIT;

