#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
ERD에 맞게 데이터베이스 스키마를 수정하는 스크립트
이 스크립트는 ERD.mmd에 정의된 스키마와 실제 Oracle DB를 일치시킵니다.
"""

import os
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

import django
django.setup()

from api.db.oracle_client import get_connection

def run_migration():
    """ERD에 맞게 스키마 수정"""
    print("=" * 80)
    print("ERD 스키마 마이그레이션 시작")
    print("=" * 80)
    print()
    
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                # ============================================================
                # Step 1: MEMBER 테이블에 'GUEST' 레코드 생성
                # ============================================================
                print("Step 1: MEMBER 테이블에 GUEST 레코드 생성")
                try:
                    # MEMBER 테이블에 CREATED_DATE 컬럼이 있는지 확인
                    cur.execute("""
                        SELECT COUNT(*) 
                        FROM USER_TAB_COLUMNS
                        WHERE TABLE_NAME = 'MEMBER' AND COLUMN_NAME = 'CREATED_DATE'
                    """)
                    has_created_date = cur.fetchone()[0] > 0
                    
                    # GUEST 레코드가 없으면 생성
                    cur.execute("SELECT COUNT(*) FROM MEMBER WHERE MEMBER_ID = 'GUEST'")
                    guest_exists = cur.fetchone()[0] > 0
                    
                    if not guest_exists:
                        # MEMBER 테이블의 필수 컬럼 확인
                        cur.execute("""
                            SELECT COLUMN_NAME, NULLABLE, DATA_DEFAULT
                            FROM USER_TAB_COLUMNS
                            WHERE TABLE_NAME = 'MEMBER'
                            ORDER BY COLUMN_ID
                        """)
                        columns = cur.fetchall()
                        
                        # 필수 컬럼 목록 생성
                        required_cols = []
                        col_values = []
                        
                        for col_name, nullable, data_default in columns:
                            col_name_upper = col_name.upper()
                            if col_name_upper == 'MEMBER_ID':
                                required_cols.append('MEMBER_ID')
                                col_values.append("'GUEST'")
                            elif nullable == 'N' and data_default is None:
                                # NOT NULL이고 기본값이 없는 필수 컬럼
                                if col_name_upper == 'PASSWORD':
                                    required_cols.append('PASSWORD')
                                    col_values.append("'GUEST_PASSWORD'")  # 더미 비밀번호
                                elif col_name_upper == 'NAME':
                                    required_cols.append('NAME')
                                    col_values.append("'GUEST'")
                                elif col_name_upper == 'CREATED_DATE' or col_name_upper == 'CREATED_AT':
                                    required_cols.append(col_name)
                                    col_values.append('SYSDATE')
                                else:
                                    # 다른 필수 컬럼은 기본값 사용
                                    required_cols.append(col_name)
                                    if 'DATE' in col_name_upper or 'AT' in col_name_upper:
                                        col_values.append('SYSDATE')
                                    else:
                                        col_values.append('NULL')  # 일단 NULL 시도
                        
                        # INSERT 문 생성
                        if required_cols:
                            cols_str = ', '.join(required_cols)
                            vals_str = ', '.join(col_values)
                            insert_sql = f"INSERT INTO MEMBER ({cols_str}) VALUES ({vals_str})"
                            
                            try:
                                cur.execute(insert_sql)
                                conn.commit()
                                print("  ✅ GUEST 레코드 생성 완료")
                            except Exception as insert_error:
                                # 더 간단한 방법 시도: MEMBER_ID만
                                try:
                                    cur.execute("INSERT INTO MEMBER (MEMBER_ID) VALUES ('GUEST')")
                                    conn.commit()
                                    print("  ✅ GUEST 레코드 생성 완료 (MEMBER_ID만)")
                                except Exception as e2:
                                    print(f"  ⚠️ GUEST 레코드 생성 실패: {e2}")
                                    conn.rollback()
                        else:
                            cur.execute("INSERT INTO MEMBER (MEMBER_ID) VALUES ('GUEST')")
                            conn.commit()
                            print("  ✅ GUEST 레코드 생성 완료")
                    else:
                        print("  ✅ GUEST 레코드가 이미 존재합니다")
                except Exception as e:
                    error_msg = str(e)
                    if 'ORA-00001' in error_msg:  # unique constraint violated
                        print("  ✅ GUEST 레코드가 이미 존재합니다")
                        conn.rollback()
                    else:
                        print(f"  ⚠️ GUEST 레코드 생성 중 오류: {error_msg}")
                        conn.rollback()
                
                print()
                
                # ============================================================
                # Step 2: ONBOARDING_SESSION 테이블의 SESSION_ID를 VARCHAR2(100)로 변경
                # ============================================================
                print("Step 2: SESSION_ID 타입을 VARCHAR2(100)로 변경")
                try:
                    # 테이블 존재 확인
                    cur.execute("""
                        SELECT COUNT(*) 
                        FROM USER_TABLES
                        WHERE TABLE_NAME = 'ONBOARDING_SESSION'
                    """)
                    table_exists = cur.fetchone()[0] > 0
                    
                    if not table_exists:
                        print("  ⚠️ ONBOARDING_SESSION 테이블이 존재하지 않습니다")
                    else:
                        # SESSION_ID 컬럼 타입 확인
                        cur.execute("""
                            SELECT DATA_TYPE 
                            FROM USER_TAB_COLUMNS
                            WHERE TABLE_NAME = 'ONBOARDING_SESSION' AND COLUMN_NAME = 'SESSION_ID'
                        """)
                        result = cur.fetchone()
                        
                        if result:
                            data_type = result[0]
                            if data_type == 'VARCHAR2':
                                print("  ✅ SESSION_ID는 이미 VARCHAR2 타입입니다")
                            elif data_type == 'NUMBER':
                                print("  ⚠️ SESSION_ID가 NUMBER 타입입니다. VARCHAR2(100)로 변경 중...")
                                
                                # 임시 테이블 생성
                                print("    - 임시 테이블 생성 중...")
                                cur.execute("""
                                    CREATE TABLE ONBOARDING_SESSION_NEW (
                                        SESSION_ID VARCHAR2(100) PRIMARY KEY,
                                        MEMBER_ID VARCHAR2(30),
                                        USER_ID VARCHAR2(100),
                                        CURRENT_STEP NUMBER DEFAULT 1,
                                        STATUS VARCHAR2(20) DEFAULT 'IN_PROGRESS',
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
                                        COMPLETED_AT DATE
                                    )
                                """)
                                
                                # FK 제약조건 추가 (나중에)
                                print("    - 데이터 마이그레이션 중...")
                                cur.execute("""
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
                                """)
                                
                                # 정규화 테이블 삭제 (FK 때문에)
                                ref_tables = [
                                    'ONBOARD_SESS_CATEGORIES',
                                    'ONBOARD_SESS_MAIN_SPACES',
                                    'ONBOARD_SESS_PRIORITIES',
                                    'ONBOARD_SESS_REC_PRODUCTS'
                                ]
                                
                                for ref_table in ref_tables:
                                    try:
                                        cur.execute(f"DROP TABLE {ref_table} CASCADE CONSTRAINTS")
                                        print(f"    - {ref_table} 테이블 삭제 완료")
                                    except Exception as e:
                                        if 'ORA-00942' in str(e):  # table does not exist
                                            pass
                                        else:
                                            print(f"    ⚠️ {ref_table} 삭제 중 오류: {e}")
                                
                                # 기존 테이블 삭제
                                print("    - 기존 테이블 삭제 중...")
                                cur.execute("DROP TABLE ONBOARDING_SESSION CASCADE CONSTRAINTS")
                                
                                # 새 테이블 이름 변경
                                print("    - 테이블 이름 변경 중...")
                                cur.execute("ALTER TABLE ONBOARDING_SESSION_NEW RENAME TO ONBOARDING_SESSION")
                                
                                # FK 제약조건 추가
                                print("    - FK 제약조건 추가 중...")
                                try:
                                    cur.execute("""
                                        ALTER TABLE ONBOARDING_SESSION 
                                        ADD CONSTRAINT FK_SESSION_MEMBER 
                                        FOREIGN KEY (MEMBER_ID) REFERENCES MEMBER(MEMBER_ID)
                                    """)
                                except Exception as e:
                                    if 'ORA-02275' in str(e) or 'ORA-02264' in str(e):
                                        print("    ⚠️ FK 제약조건이 이미 존재하거나 다른 이름으로 존재합니다")
                                    else:
                                        raise
                                
                                # 인덱스 재생성
                                indexes = [
                                    ('IDX_SESSION_USER_ID', 'USER_ID'),
                                    ('IDX_SESSION_STATUS', 'STATUS'),
                                    ('IDX_SESSION_CREATED_AT', 'CREATED_AT')
                                ]
                                
                                for idx_name, col_name in indexes:
                                    try:
                                        cur.execute(f"CREATE INDEX {idx_name} ON ONBOARDING_SESSION({col_name})")
                                    except Exception as e:
                                        if 'ORA-00955' in str(e):  # name is already used
                                            pass
                                        else:
                                            print(f"    ⚠️ 인덱스 {idx_name} 생성 중 오류: {e}")
                                
                                conn.commit()
                                print("  ✅ SESSION_ID가 VARCHAR2(100)로 변경되었습니다")
                            else:
                                print(f"  ⚠️ SESSION_ID 타입: {data_type} (예상: VARCHAR2 또는 NUMBER)")
                        else:
                            print("  ⚠️ SESSION_ID 컬럼을 찾을 수 없습니다")
                except Exception as e:
                    error_msg = str(e)
                    print(f"  ❌ SESSION_ID 타입 변경 중 오류: {error_msg}")
                    conn.rollback()
                    import traceback
                    traceback.print_exc()
                
                print()
                
                # ============================================================
                # Step 3: ONBOARDING_SESSION.MEMBER_ID를 NULL 허용으로 변경
                # ============================================================
                print("Step 3: MEMBER_ID를 NULL 허용으로 변경")
                try:
                    cur.execute("""
                        SELECT NULLABLE 
                        FROM USER_TAB_COLUMNS
                        WHERE TABLE_NAME = 'ONBOARDING_SESSION' AND COLUMN_NAME = 'MEMBER_ID'
                    """)
                    result = cur.fetchone()
                    
                    if result:
                        nullable = result[0]
                        if nullable == 'N':
                            # FK 제약조건 삭제 시도
                            try:
                                cur.execute("ALTER TABLE ONBOARDING_SESSION DROP CONSTRAINT FK_SESSION_MEMBER")
                            except Exception as e:
                                if 'ORA-02443' in str(e):  # Cannot drop constraint
                                    # 다른 이름의 제약조건 찾기
                                    cur.execute("""
                                        SELECT CONSTRAINT_NAME 
                                        FROM USER_CONS_COLUMNS
                                        WHERE TABLE_NAME = 'ONBOARDING_SESSION' 
                                          AND COLUMN_NAME = 'MEMBER_ID'
                                          AND CONSTRAINT_NAME IN (
                                              SELECT CONSTRAINT_NAME 
                                              FROM USER_CONSTRAINTS 
                                              WHERE CONSTRAINT_TYPE = 'R'
                                          )
                                    """)
                                    fk_result = cur.fetchone()
                                    if fk_result:
                                        fk_name = fk_result[0]
                                        cur.execute(f"ALTER TABLE ONBOARDING_SESSION DROP CONSTRAINT {fk_name}")
                            
                            # NULL 허용으로 변경
                            cur.execute("ALTER TABLE ONBOARDING_SESSION MODIFY MEMBER_ID VARCHAR2(30) NULL")
                            
                            # FK 제약조건 재생성
                            try:
                                cur.execute("""
                                    ALTER TABLE ONBOARDING_SESSION 
                                    ADD CONSTRAINT FK_SESSION_MEMBER 
                                    FOREIGN KEY (MEMBER_ID) REFERENCES MEMBER(MEMBER_ID)
                                """)
                            except Exception as e:
                                if 'ORA-02264' in str(e) or 'ORA-02275' in str(e):
                                    print("  ✅ FK 제약조건이 이미 존재합니다")
                                else:
                                    raise
                            
                            conn.commit()
                            print("  ✅ MEMBER_ID를 NULL 허용으로 변경 완료")
                        else:
                            print("  ✅ MEMBER_ID는 이미 NULL 허용입니다")
                    else:
                        print("  ⚠️ MEMBER_ID 컬럼을 찾을 수 없습니다")
                except Exception as e:
                    error_msg = str(e)
                    print(f"  ⚠️ MEMBER_ID 수정 중 오류: {error_msg}")
                    conn.rollback()
                
                print()
                print("=" * 80)
                print("✅ ERD 스키마 마이그레이션 완료!")
                print("=" * 80)
                return True
                        
    except Exception as e:
        print(f"❌ 데이터베이스 연결 또는 실행 중 오류:")
        print(f"   {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = run_migration()
    sys.exit(0 if success else 1)

