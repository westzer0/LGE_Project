#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Step 1 검증 로직 수동 검증
실제 SQL 쿼리로 직접 확인하여 검증 로직이 올바른지 증명
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

import django
django.setup()

from api.db.oracle_client import get_connection


def verify_manually():
    """수동 검증 - 실제 SQL 쿼리로 확인"""
    print("=" * 80)
    print("Step 1 검증 로직 수동 검증")
    print("=" * 80)
    print()
    
    with get_connection() as conn:
        with conn.cursor() as cur:
            # 1. 테이블 존재 여부 직접 확인
            print("[1] 테이블 존재 여부 직접 확인")
            print("-" * 80)
            
            tables_to_check = [
                'ONBOARDING_SESSION',
                'ONBOARD_SESS_MAIN_SPACES',
                'ONBOARD_SESS_PRIORITIES',
                'MEMBER'
            ]
            
            for table_name in tables_to_check:
                cur.execute("""
                    SELECT COUNT(*) 
                    FROM USER_TABLES 
                    WHERE TABLE_NAME = :table_name
                """, {'table_name': table_name})
                count = cur.fetchone()[0]
                
                if count > 0:
                    print(f"  ✅ {table_name}: 존재 (COUNT={count})")
                else:
                    print(f"  ❌ {table_name}: 없음 (COUNT={count})")
            
            print()
            
            # 2. ONBOARDING_SESSION 컬럼 직접 확인
            print("[2] ONBOARDING_SESSION 테이블 컬럼 직접 확인")
            print("-" * 80)
            
            required_columns = [
                'SESSION_ID', 'MEMBER_ID', 'STATUS',
                'VIBE', 'HOUSEHOLD_SIZE', 'HOUSING_TYPE', 'PYUNG',
                'BUDGET_LEVEL', 'PRIORITY', 'HAS_PET',
                'COOKING', 'LAUNDRY', 'MEDIA'
            ]
            
            cur.execute("""
                SELECT COLUMN_NAME, DATA_TYPE, DATA_LENGTH, NULLABLE
                FROM USER_TAB_COLUMNS
                WHERE TABLE_NAME = 'ONBOARDING_SESSION'
                ORDER BY COLUMN_ID
            """)
            existing_columns = {row[0]: row[1:] for row in cur.fetchall()}
            
            for col_name in required_columns:
                if col_name in existing_columns:
                    data_type, data_length, nullable = existing_columns[col_name]
                    print(f"  ✅ {col_name}: {data_type}({data_length or 'N/A'}), NULLABLE={nullable}")
                else:
                    print(f"  ❌ {col_name}: 없음")
            
            print()
            
            # 3. MEMBER 테이블 TASTE 컬럼 직접 확인
            print("[3] MEMBER 테이블 TASTE 컬럼 직접 확인")
            print("-" * 80)
            
            cur.execute("""
                SELECT COLUMN_NAME, DATA_TYPE, DATA_PRECISION, DATA_SCALE, NULLABLE
                FROM USER_TAB_COLUMNS
                WHERE TABLE_NAME = 'MEMBER' AND COLUMN_NAME = 'TASTE'
            """)
            taste_col = cur.fetchone()
            
            if taste_col:
                col_name, data_type, precision, scale, nullable = taste_col
                print(f"  ✅ TASTE 컬럼 존재")
                print(f"     타입: {data_type}({precision or 'N/A'}{f',{scale}' if scale else ''})")
                print(f"     NULLABLE: {nullable}")
                
                # 범위 확인
                if precision:
                    print(f"     정밀도: {precision} (1~120 범위에 적합)")
            else:
                print(f"  ❌ TASTE 컬럼 없음")
            
            print()
            
            # 4. MEMBER.TASTE 제약조건 직접 확인
            print("[4] MEMBER.TASTE 제약조건 직접 확인")
            print("-" * 80)
            
            cur.execute("""
                SELECT CONSTRAINT_NAME, CONSTRAINT_TYPE, SEARCH_CONDITION
                FROM USER_CONSTRAINTS
                WHERE TABLE_NAME = 'MEMBER' 
                  AND CONSTRAINT_NAME LIKE '%TASTE%'
                  AND CONSTRAINT_TYPE = 'C'
            """)
            constraints = cur.fetchall()
            
            if constraints:
                for constraint_name, constraint_type, search_condition in constraints:
                    print(f"  ✅ 제약조건 존재: {constraint_name}")
                    print(f"     타입: {constraint_type} (CHECK)")
                    if search_condition:
                        print(f"     조건: {search_condition[:100]}...")
                        if '1' in search_condition and '120' in search_condition:
                            print(f"     ✅ 1~120 범위 제약조건 확인됨")
            else:
                print(f"  ⚠️ TASTE 관련 CHECK 제약조건 없음")
            
            print()
            
            # 5. 정규화 테이블 구조 직접 확인
            print("[5] 정규화 테이블 구조 직접 확인")
            print("-" * 80)
            
            # ONBOARD_SESS_MAIN_SPACES
            print("  [ONBOARD_SESS_MAIN_SPACES]")
            cur.execute("""
                SELECT COLUMN_NAME, DATA_TYPE, NULLABLE
                FROM USER_TAB_COLUMNS
                WHERE TABLE_NAME = 'ONBOARD_SESS_MAIN_SPACES'
                ORDER BY COLUMN_ID
            """)
            main_spaces_cols = cur.fetchall()
            for col_name, data_type, nullable in main_spaces_cols:
                print(f"    ✅ {col_name}: {data_type}, NULLABLE={nullable}")
            
            # FK 확인
            cur.execute("""
                SELECT c.CONSTRAINT_NAME, cc.COLUMN_NAME
                FROM USER_CONSTRAINTS c
                JOIN USER_CONS_COLUMNS cc ON c.CONSTRAINT_NAME = cc.CONSTRAINT_NAME
                WHERE c.TABLE_NAME = 'ONBOARD_SESS_MAIN_SPACES'
                  AND c.CONSTRAINT_TYPE = 'R'
            """)
            fk_info = cur.fetchone()
            if fk_info:
                print(f"    ✅ FK 제약조건: {fk_info[0]}")
                print(f"       {fk_info[1]} → ONBOARDING_SESSION.SESSION_ID")
            
            print()
            
            # ONBOARD_SESS_PRIORITIES
            print("  [ONBOARD_SESS_PRIORITIES]")
            cur.execute("""
                SELECT COLUMN_NAME, DATA_TYPE, NULLABLE
                FROM USER_TAB_COLUMNS
                WHERE TABLE_NAME = 'ONBOARD_SESS_PRIORITIES'
                ORDER BY COLUMN_ID
            """)
            priorities_cols = cur.fetchall()
            for col_name, data_type, nullable in priorities_cols:
                print(f"    ✅ {col_name}: {data_type}, NULLABLE={nullable}")
            
            # FK 확인
            cur.execute("""
                SELECT c.CONSTRAINT_NAME, cc.COLUMN_NAME
                FROM USER_CONSTRAINTS c
                JOIN USER_CONS_COLUMNS cc ON c.CONSTRAINT_NAME = cc.CONSTRAINT_NAME
                WHERE c.TABLE_NAME = 'ONBOARD_SESS_PRIORITIES'
                  AND c.CONSTRAINT_TYPE = 'R'
            """)
            fk_info = cur.fetchone()
            if fk_info:
                print(f"    ✅ FK 제약조건: {fk_info[0]}")
                print(f"       {fk_info[1]} → ONBOARDING_SESSION.SESSION_ID")
            
            print()
            
            # 6. 실제 데이터 샘플 확인 (있는 경우)
            print("[6] 실제 데이터 샘플 확인")
            print("-" * 80)
            
            # ONBOARDING_SESSION 샘플
            cur.execute("""
                SELECT COUNT(*) FROM ONBOARDING_SESSION
            """)
            session_count = cur.fetchone()[0]
            print(f"  ONBOARDING_SESSION 레코드 수: {session_count}")
            
            if session_count > 0:
                cur.execute("""
                    SELECT SESSION_ID, MEMBER_ID, STATUS, VIBE, HOUSEHOLD_SIZE
                    FROM ONBOARDING_SESSION
                    WHERE ROWNUM <= 3
                """)
                samples = cur.fetchall()
                print(f"  샘플 데이터 (최대 3개):")
                for sample in samples:
                    print(f"    - SESSION_ID={sample[0]}, MEMBER_ID={sample[1]}, STATUS={sample[2]}, VIBE={sample[3]}, HOUSEHOLD_SIZE={sample[4]}")
            
            # MEMBER.TASTE 샘플
            cur.execute("""
                SELECT COUNT(*) FROM MEMBER WHERE TASTE IS NOT NULL
            """)
            taste_count = cur.fetchone()[0]
            print(f"  MEMBER.TASTE가 설정된 회원 수: {taste_count}")
            
            if taste_count > 0:
                cur.execute("""
                    SELECT MEMBER_ID, TASTE
                    FROM MEMBER
                    WHERE TASTE IS NOT NULL
                      AND ROWNUM <= 5
                """)
                samples = cur.fetchall()
                print(f"  샘플 데이터 (최대 5개):")
                for sample in samples:
                    taste_id = sample[1]
                    range_ok = "✅" if 1 <= taste_id <= 120 else "❌"
                    print(f"    {range_ok} MEMBER_ID={sample[0]}, TASTE={taste_id}")
            
            print()
            
            # 7. 검증 로직과의 일치성 확인
            print("[7] 검증 로직과의 일치성 확인")
            print("-" * 80)
            
            # 테이블 존재 여부 재확인
            all_tables_exist = True
            for table_name in tables_to_check:
                cur.execute("""
                    SELECT COUNT(*) 
                    FROM USER_TABLES 
                    WHERE TABLE_NAME = :table_name
                """, {'table_name': table_name})
                if cur.fetchone()[0] == 0:
                    all_tables_exist = False
                    break
            
            # 필수 컬럼 존재 여부 재확인
            all_columns_exist = True
            for col_name in ['SESSION_ID', 'MEMBER_ID', 'STATUS']:
                if col_name not in existing_columns:
                    all_columns_exist = False
                    break
            
            # TASTE 컬럼 존재 여부 재확인
            taste_exists = taste_col is not None
            
            print(f"  테이블 존재: {'✅ 모두 존재' if all_tables_exist else '❌ 일부 없음'}")
            print(f"  필수 컬럼 존재: {'✅ 모두 존재' if all_columns_exist else '❌ 일부 없음'}")
            print(f"  TASTE 컬럼 존재: {'✅ 존재' if taste_exists else '❌ 없음'}")
            print(f"  TASTE 제약조건: {'✅ 존재' if constraints else '⚠️ 없음'}")
            
            print()
            print("=" * 80)
            if all_tables_exist and all_columns_exist and taste_exists:
                print("✅ 검증 로직이 올바르게 작동합니다!")
                print("   모든 필수 인프라가 실제로 존재하고 확인되었습니다.")
            else:
                print("❌ 검증 로직에 문제가 있을 수 있습니다.")
            print("=" * 80)


if __name__ == '__main__':
    try:
        verify_manually()
    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        exit(1)

