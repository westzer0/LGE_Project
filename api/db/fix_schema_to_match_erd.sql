-- ============================================================
-- ERD에 맞게 데이터베이스 스키마 수정
-- 이 스크립트는 ERD.mmd에 정의된 스키마와 실제 DB를 일치시킵니다
-- ============================================================

SET SERVEROUTPUT ON;

BEGIN
    DBMS_OUTPUT.PUT_LINE('========================================');
    DBMS_OUTPUT.PUT_LINE('ERD 스키마 마이그레이션 시작');
    DBMS_OUTPUT.PUT_LINE('========================================');
    
    -- ============================================================
    -- Step 1: MEMBER 테이블에 'GUEST' 레코드 생성
    -- ============================================================
    DBMS_OUTPUT.PUT_LINE('');
    DBMS_OUTPUT.PUT_LINE('Step 1: MEMBER 테이블에 GUEST 레코드 생성');
    
    BEGIN
        -- MEMBER 테이블에 CREATED_DATE 컬럼이 있는지 확인
        DECLARE
            v_col_exists NUMBER;
        BEGIN
            SELECT COUNT(*) INTO v_col_exists
            FROM USER_TAB_COLUMNS
            WHERE TABLE_NAME = 'MEMBER' AND COLUMN_NAME = 'CREATED_DATE';
            
            -- GUEST 레코드가 없으면 생성
            DECLARE
                v_guest_exists NUMBER;
            BEGIN
                SELECT COUNT(*) INTO v_guest_exists
                FROM MEMBER
                WHERE MEMBER_ID = 'GUEST';
                
                IF v_guest_exists = 0 THEN
                    -- CREATED_DATE 컬럼이 있으면 사용, 없으면 SYSDATE만 사용
                    IF v_col_exists > 0 THEN
                        INSERT INTO MEMBER (MEMBER_ID, CREATED_DATE)
                        VALUES ('GUEST', SYSDATE);
                    ELSE
                        -- CREATED_DATE 컬럼이 없으면 MEMBER_ID만 삽입
                        INSERT INTO MEMBER (MEMBER_ID)
                        VALUES ('GUEST');
                    END IF;
                    COMMIT;
                    DBMS_OUTPUT.PUT_LINE('✅ GUEST 레코드 생성 완료');
                ELSE
                    DBMS_OUTPUT.PUT_LINE('✅ GUEST 레코드가 이미 존재합니다');
                END IF;
            EXCEPTION
                WHEN OTHERS THEN
                    DBMS_OUTPUT.PUT_LINE('⚠️ GUEST 레코드 생성 중 오류: ' || SQLERRM);
                    -- 오류가 발생해도 계속 진행
            END;
        END;
    EXCEPTION
        WHEN OTHERS THEN
            DBMS_OUTPUT.PUT_LINE('⚠️ MEMBER 테이블 확인 중 오류: ' || SQLERRM);
    END;
    
    -- ============================================================
    -- Step 2: ONBOARDING_SESSION 테이블의 SESSION_ID를 VARCHAR2(100)로 변경
    -- ============================================================
    DBMS_OUTPUT.PUT_LINE('');
    DBMS_OUTPUT.PUT_LINE('Step 2: SESSION_ID 타입을 VARCHAR2(100)로 변경');
    
    DECLARE
        v_data_type VARCHAR2(20);
        v_table_exists NUMBER;
    BEGIN
        -- 테이블 존재 확인
        SELECT COUNT(*) INTO v_table_exists
        FROM USER_TABLES
        WHERE TABLE_NAME = 'ONBOARDING_SESSION';
        
        IF v_table_exists = 0 THEN
            DBMS_OUTPUT.PUT_LINE('⚠️ ONBOARDING_SESSION 테이블이 존재하지 않습니다');
        ELSE
            -- SESSION_ID 컬럼 타입 확인
            BEGIN
                SELECT DATA_TYPE INTO v_data_type
                FROM USER_TAB_COLUMNS
                WHERE TABLE_NAME = 'ONBOARDING_SESSION' AND COLUMN_NAME = 'SESSION_ID';
                
                IF v_data_type = 'VARCHAR2' THEN
                    DBMS_OUTPUT.PUT_LINE('✅ SESSION_ID는 이미 VARCHAR2 타입입니다');
                ELSIF v_data_type = 'NUMBER' THEN
                    DBMS_OUTPUT.PUT_LINE('⚠️ SESSION_ID가 NUMBER 타입입니다. VARCHAR2(100)로 변경 중...');
                    
                    -- FK 제약조건 때문에 직접 DROP이 불가능하므로 복잡한 마이그레이션 필요
                    -- 방법: 임시 테이블 생성 -> 데이터 마이그레이션 -> 테이블 교체
                    
                    BEGIN
                        -- 1. 임시 테이블 생성 (VARCHAR2 SESSION_ID)
                        EXECUTE IMMEDIATE '
                            CREATE TABLE ONBOARDING_SESSION_NEW (
                                SESSION_ID VARCHAR2(100) PRIMARY KEY,
                                MEMBER_ID VARCHAR2(30),
                                USER_ID VARCHAR2(100),
                                CURRENT_STEP NUMBER DEFAULT 1,
                                STATUS VARCHAR2(20) DEFAULT ''IN_PROGRESS'',
                                VIBE VARCHAR2(20),
                                HOUSEHOLD_SIZE NUMBER,
                                HAS_PET CHAR(1),
                                HOUSING_TYPE VARCHAR2(20),
                                PYUNG NUMBER,
                                COOKING VARCHAR2(20),
                                LAUNDRY VARCHAR2(20),
                                MEDIA VARCHAR2(20),
                                PRIORITY VARCHAR2(20),
                                BUDGET_LEVEL VARCHAR2(20),
                                CREATED_AT DATE DEFAULT SYSDATE,
                                UPDATED_AT DATE DEFAULT SYSDATE,
                                COMPLETED_AT DATE,
                                CONSTRAINT FK_SESSION_MEMBER_NEW FOREIGN KEY (MEMBER_ID) REFERENCES MEMBER(MEMBER_ID)
                            )
                        ';
                        DBMS_OUTPUT.PUT_LINE('  ✅ 임시 테이블 생성 완료');
                        
                        -- 2. 기존 데이터 마이그레이션 (NUMBER를 VARCHAR2로 변환)
                        EXECUTE IMMEDIATE '
                            INSERT INTO ONBOARDING_SESSION_NEW (
                                SESSION_ID, MEMBER_ID, USER_ID, CURRENT_STEP, STATUS,
                                VIBE, HOUSEHOLD_SIZE, HAS_PET, HOUSING_TYPE, PYUNG,
                                COOKING, LAUNDRY, MEDIA, PRIORITY, BUDGET_LEVEL,
                                CREATED_AT, UPDATED_AT, COMPLETED_AT
                            )
                            SELECT 
                                TO_CHAR(SESSION_ID) AS SESSION_ID,
                                MEMBER_ID, USER_ID, CURRENT_STEP, STATUS,
                                VIBE, HOUSEHOLD_SIZE, HAS_PET, HOUSING_TYPE, PYUNG,
                                COOKING, LAUNDRY, MEDIA, PRIORITY, BUDGET_LEVEL,
                                CREATED_AT, UPDATED_AT, COMPLETED_AT
                            FROM ONBOARDING_SESSION
                        ';
                        DBMS_OUTPUT.PUT_LINE('  ✅ 데이터 마이그레이션 완료');
                        
                        -- 3. 정규화 테이블들의 FK도 업데이트 필요
                        -- ONBOARD_SESS_* 테이블들의 SESSION_ID도 VARCHAR2로 변경
                        DECLARE
                            v_ref_table VARCHAR2(100);
                            v_ref_exists NUMBER;
                        BEGIN
                            -- ONBOARD_SESS_CATEGORIES
                            SELECT COUNT(*) INTO v_ref_exists
                            FROM USER_TABLES
                            WHERE TABLE_NAME = 'ONBOARD_SESS_CATEGORIES';
                            
                            IF v_ref_exists > 0 THEN
                                BEGIN
                                    EXECUTE IMMEDIATE 'DROP TABLE ONBOARD_SESS_CATEGORIES CASCADE CONSTRAINTS';
                                    DBMS_OUTPUT.PUT_LINE('  ✅ ONBOARD_SESS_CATEGORIES 테이블 삭제 (재생성 예정)');
                                EXCEPTION
                                    WHEN OTHERS THEN
                                        DBMS_OUTPUT.PUT_LINE('  ⚠️ ONBOARD_SESS_CATEGORIES 삭제 중 오류: ' || SQLERRM);
                                END;
                            END IF;
                            
                            -- ONBOARD_SESS_MAIN_SPACES
                            SELECT COUNT(*) INTO v_ref_exists
                            FROM USER_TABLES
                            WHERE TABLE_NAME = 'ONBOARD_SESS_MAIN_SPACES';
                            
                            IF v_ref_exists > 0 THEN
                                BEGIN
                                    EXECUTE IMMEDIATE 'DROP TABLE ONBOARD_SESS_MAIN_SPACES CASCADE CONSTRAINTS';
                                    DBMS_OUTPUT.PUT_LINE('  ✅ ONBOARD_SESS_MAIN_SPACES 테이블 삭제 (재생성 예정)');
                                EXCEPTION
                                    WHEN OTHERS THEN
                                        DBMS_OUTPUT.PUT_LINE('  ⚠️ ONBOARD_SESS_MAIN_SPACES 삭제 중 오류: ' || SQLERRM);
                                END;
                            END IF;
                            
                            -- ONBOARD_SESS_PRIORITIES
                            SELECT COUNT(*) INTO v_ref_exists
                            FROM USER_TABLES
                            WHERE TABLE_NAME = 'ONBOARD_SESS_PRIORITIES';
                            
                            IF v_ref_exists > 0 THEN
                                BEGIN
                                    EXECUTE IMMEDIATE 'DROP TABLE ONBOARD_SESS_PRIORITIES CASCADE CONSTRAINTS';
                                    DBMS_OUTPUT.PUT_LINE('  ✅ ONBOARD_SESS_PRIORITIES 테이블 삭제 (재생성 예정)');
                                EXCEPTION
                                    WHEN OTHERS THEN
                                        DBMS_OUTPUT.PUT_LINE('  ⚠️ ONBOARD_SESS_PRIORITIES 삭제 중 오류: ' || SQLERRM);
                                END;
                            END IF;
                            
                            -- ONBOARD_SESS_REC_PRODUCTS
                            SELECT COUNT(*) INTO v_ref_exists
                            FROM USER_TABLES
                            WHERE TABLE_NAME = 'ONBOARD_SESS_REC_PRODUCTS';
                            
                            IF v_ref_exists > 0 THEN
                                BEGIN
                                    EXECUTE IMMEDIATE 'DROP TABLE ONBOARD_SESS_REC_PRODUCTS CASCADE CONSTRAINTS';
                                    DBMS_OUTPUT.PUT_LINE('  ✅ ONBOARD_SESS_REC_PRODUCTS 테이블 삭제 (재생성 예정)');
                                EXCEPTION
                                    WHEN OTHERS THEN
                                        DBMS_OUTPUT.PUT_LINE('  ⚠️ ONBOARD_SESS_REC_PRODUCTS 삭제 중 오류: ' || SQLERRM);
                                END;
                            END IF;
                        END;
                        
                        -- 4. 기존 테이블 삭제
                        EXECUTE IMMEDIATE 'DROP TABLE ONBOARDING_SESSION CASCADE CONSTRAINTS';
                        DBMS_OUTPUT.PUT_LINE('  ✅ 기존 테이블 삭제 완료');
                        
                        -- 5. 새 테이블 이름 변경
                        EXECUTE IMMEDIATE 'ALTER TABLE ONBOARDING_SESSION_NEW RENAME TO ONBOARDING_SESSION';
                        DBMS_OUTPUT.PUT_LINE('  ✅ 테이블 이름 변경 완료');
                        
                        -- 6. 인덱스 재생성
                        BEGIN
                            EXECUTE IMMEDIATE 'CREATE INDEX IDX_SESSION_USER_ID ON ONBOARDING_SESSION(USER_ID)';
                        EXCEPTION
                            WHEN OTHERS THEN
                                IF SQLCODE = -955 THEN
                                    DBMS_OUTPUT.PUT_LINE('  ✅ 인덱스 IDX_SESSION_USER_ID는 이미 존재합니다');
                                ELSE
                                    RAISE;
                                END IF;
                        END;
                        
                        BEGIN
                            EXECUTE IMMEDIATE 'CREATE INDEX IDX_SESSION_STATUS ON ONBOARDING_SESSION(STATUS)';
                        EXCEPTION
                            WHEN OTHERS THEN
                                IF SQLCODE = -955 THEN
                                    DBMS_OUTPUT.PUT_LINE('  ✅ 인덱스 IDX_SESSION_STATUS는 이미 존재합니다');
                                ELSE
                                    RAISE;
                                END IF;
                        END;
                        
                        BEGIN
                            EXECUTE IMMEDIATE 'CREATE INDEX IDX_SESSION_CREATED_AT ON ONBOARDING_SESSION(CREATED_AT)';
                        EXCEPTION
                            WHEN OTHERS THEN
                                IF SQLCODE = -955 THEN
                                    DBMS_OUTPUT.PUT_LINE('  ✅ 인덱스 IDX_SESSION_CREATED_AT는 이미 존재합니다');
                                ELSE
                                    RAISE;
                                END IF;
                        END;
                        
                        COMMIT;
                        DBMS_OUTPUT.PUT_LINE('✅ SESSION_ID가 VARCHAR2(100)로 변경되었습니다');
                        
                    EXCEPTION
                        WHEN OTHERS THEN
                            DBMS_OUTPUT.PUT_LINE('  ❌ SESSION_ID 타입 변경 중 오류: ' || SQLERRM);
                            ROLLBACK;
                            -- 임시 테이블 정리
                            BEGIN
                                EXECUTE IMMEDIATE 'DROP TABLE ONBOARDING_SESSION_NEW';
                            EXCEPTION
                                WHEN OTHERS THEN NULL;
                            END;
                            RAISE;
                    END;
                ELSE
                    DBMS_OUTPUT.PUT_LINE('⚠️ SESSION_ID 타입: ' || v_data_type || ' (예상: VARCHAR2 또는 NUMBER)');
                END IF;
            EXCEPTION
                WHEN NO_DATA_FOUND THEN
                    DBMS_OUTPUT.PUT_LINE('⚠️ SESSION_ID 컬럼을 찾을 수 없습니다');
                WHEN OTHERS THEN
                    DBMS_OUTPUT.PUT_LINE('⚠️ SESSION_ID 타입 확인 중 오류: ' || SQLERRM);
            END;
        END IF;
    EXCEPTION
        WHEN OTHERS THEN
            DBMS_OUTPUT.PUT_LINE('⚠️ ONBOARDING_SESSION 테이블 확인 중 오류: ' || SQLERRM);
    END;
    
    -- ============================================================
    -- Step 3: ONBOARDING_SESSION.MEMBER_ID를 NULL 허용으로 변경 (ERD에 따르면 nullable)
    -- ============================================================
    DBMS_OUTPUT.PUT_LINE('');
    DBMS_OUTPUT.PUT_LINE('Step 3: MEMBER_ID를 NULL 허용으로 변경');
    
    BEGIN
        DECLARE
            v_nullable VARCHAR2(1);
        BEGIN
            SELECT NULLABLE INTO v_nullable
            FROM USER_TAB_COLUMNS
            WHERE TABLE_NAME = 'ONBOARDING_SESSION' AND COLUMN_NAME = 'MEMBER_ID';
            
            IF v_nullable = 'N' THEN
                -- FK 제약조건이 있으면 먼저 삭제
                BEGIN
                    EXECUTE IMMEDIATE 'ALTER TABLE ONBOARDING_SESSION DROP CONSTRAINT FK_SESSION_MEMBER';
                EXCEPTION
                    WHEN OTHERS THEN
                        IF SQLCODE = -2443 THEN
                            DBMS_OUTPUT.PUT_LINE('  ✅ FK 제약조건이 없습니다');
                        ELSE
                            -- 다른 이름의 제약조건일 수 있음
                            DBMS_OUTPUT.PUT_LINE('  ⚠️ FK 제약조건 삭제 중 오류 (다른 이름일 수 있음): ' || SQLERRM);
                        END IF;
                END;
                
                -- NULL 허용으로 변경
                BEGIN
                    EXECUTE IMMEDIATE 'ALTER TABLE ONBOARDING_SESSION MODIFY MEMBER_ID VARCHAR2(30) NULL';
                    DBMS_OUTPUT.PUT_LINE('  ✅ MEMBER_ID를 NULL 허용으로 변경 완료');
                    
                    -- FK 제약조건 재생성 (NULL 허용)
                    BEGIN
                        EXECUTE IMMEDIATE 'ALTER TABLE ONBOARDING_SESSION ADD CONSTRAINT FK_SESSION_MEMBER FOREIGN KEY (MEMBER_ID) REFERENCES MEMBER(MEMBER_ID)';
                        DBMS_OUTPUT.PUT_LINE('  ✅ FK 제약조건 재생성 완료');
                    EXCEPTION
                        WHEN OTHERS THEN
                            IF SQLCODE = -2260 THEN
                                DBMS_OUTPUT.PUT_LINE('  ✅ FK 제약조건이 이미 존재합니다');
                            ELSE
                                DBMS_OUTPUT.PUT_LINE('  ⚠️ FK 제약조건 재생성 중 오류: ' || SQLERRM);
                            END IF;
                    END;
                    
                    COMMIT;
                EXCEPTION
                    WHEN OTHERS THEN
                        DBMS_OUTPUT.PUT_LINE('  ❌ MEMBER_ID NULL 허용 변경 중 오류: ' || SQLERRM);
                        ROLLBACK;
                END;
            ELSE
                DBMS_OUTPUT.PUT_LINE('  ✅ MEMBER_ID는 이미 NULL 허용입니다');
            END IF;
        EXCEPTION
            WHEN NO_DATA_FOUND THEN
                DBMS_OUTPUT.PUT_LINE('  ⚠️ MEMBER_ID 컬럼을 찾을 수 없습니다');
            WHEN OTHERS THEN
                DBMS_OUTPUT.PUT_LINE('  ⚠️ MEMBER_ID 확인 중 오류: ' || SQLERRM);
        END;
    EXCEPTION
        WHEN OTHERS THEN
            DBMS_OUTPUT.PUT_LINE('⚠️ MEMBER_ID 수정 중 오류: ' || SQLERRM);
    END;
    
    DBMS_OUTPUT.PUT_LINE('');
    DBMS_OUTPUT.PUT_LINE('========================================');
    DBMS_OUTPUT.PUT_LINE('ERD 스키마 마이그레이션 완료');
    DBMS_OUTPUT.PUT_LINE('========================================');
    
EXCEPTION
    WHEN OTHERS THEN
        DBMS_OUTPUT.PUT_LINE('');
        DBMS_OUTPUT.PUT_LINE('❌ 마이그레이션 중 치명적 오류 발생:');
        DBMS_OUTPUT.PUT_LINE('   ' || SQLERRM);
        ROLLBACK;
        RAISE;
END;
/

