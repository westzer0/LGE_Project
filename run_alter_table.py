#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
ALTER TABLE만 실행하는 스크립트
"""
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

from api.db.oracle_client import get_connection


def run_alter_table():
    """ALTER TABLE 실행"""
    print("=" * 60)
    print("ALTER TABLE 실행 - 누락된 칼럼 추가")
    print("=" * 60)
    
    try:
        conn = get_connection()
        print("\n[1] Oracle DB 연결 성공!")
        
        # ALTER TABLE SQL
        alter_statements = [
            ("HAS_PET", "ALTER TABLE ONBOARDING_SESSION ADD (HAS_PET CHAR(1))"),
            ("MAIN_SPACE", "ALTER TABLE ONBOARDING_SESSION ADD (MAIN_SPACE CLOB)"),
            ("COOKING", "ALTER TABLE ONBOARDING_SESSION ADD (COOKING VARCHAR2(20))"),
            ("LAUNDRY", "ALTER TABLE ONBOARDING_SESSION ADD (LAUNDRY VARCHAR2(20))"),
            ("MEDIA", "ALTER TABLE ONBOARDING_SESSION ADD (MEDIA VARCHAR2(20))"),
            ("PRIORITY_LIST", "ALTER TABLE ONBOARDING_SESSION ADD (PRIORITY_LIST CLOB)"),
        ]
        
        print("\n[2] ALTER TABLE 실행 중...")
        with conn.cursor() as cur:
            for col_name, sql in alter_statements:
                try:
                    cur.execute(sql)
                    print(f"  ✓ {col_name} 칼럼 추가 완료")
                except Exception as e:
                    error_msg = str(e)
                    # ORA-01430: column already exists
                    if '01430' in error_msg or 'already exists' in error_msg.lower() or 'name is already used' in error_msg.lower():
                        print(f"  ⚠ {col_name} 칼럼은 이미 존재합니다 (무시)")
                    else:
                        print(f"  ✗ {col_name} 칼럼 추가 실패: {error_msg}")
                        raise
        
        conn.commit()
        print("\n[3] 모든 ALTER TABLE 작업 완료!")
        
        # 칼럼 확인
        print("\n[4] 추가된 칼럼 확인 중...")
        with conn.cursor() as cur:
            cur.execute("""
                SELECT COLUMN_NAME, DATA_TYPE, DATA_LENGTH, NULLABLE
                FROM USER_TAB_COLUMNS
                WHERE TABLE_NAME = 'ONBOARDING_SESSION'
                AND COLUMN_NAME IN ('HAS_PET', 'MAIN_SPACE', 'COOKING', 'LAUNDRY', 'MEDIA', 'PRIORITY_LIST')
                ORDER BY COLUMN_NAME
            """)
            results = cur.fetchall()
            if results:
                print("\n  추가된 칼럼 목록:")
                for row in results:
                    col_name, data_type, data_length, nullable = row
                    length_info = f"({data_length})" if data_length else ""
                    null_info = "NULL 허용" if nullable == 'Y' else "NOT NULL"
                    print(f"    - {col_name}: {data_type}{length_info} ({null_info})")
            else:
                print("  ⚠ 추가된 칼럼을 찾을 수 없습니다.")
        
        conn.close()
        print("\n" + "=" * 60)
        print("✅ 완료!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n✗ 오류 발생: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    run_alter_table()

