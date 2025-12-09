#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
ONBOARDING_SESSION 테이블에 UPDATED_AT 컬럼 추가
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


def add_updated_at_column():
    """ONBOARDING_SESSION 테이블에 UPDATED_AT 컬럼 추가"""
    print("=" * 80)
    print("ONBOARDING_SESSION 테이블에 UPDATED_AT 컬럼 추가")
    print("=" * 80)
    
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                # 1. 현재 테이블 구조 확인
                print("\n[1] 현재 테이블 구조 확인...")
                cur.execute("""
                    SELECT COLUMN_NAME, DATA_TYPE, NULLABLE, DATA_DEFAULT
                    FROM USER_TAB_COLUMNS
                    WHERE TABLE_NAME = 'ONBOARDING_SESSION'
                    AND COLUMN_NAME IN ('CREATED_AT', 'UPDATED_AT', 'COMPLETED_AT')
                    ORDER BY COLUMN_NAME
                """)
                columns = cur.fetchall()
                print(f"  발견된 컬럼: {len(columns)}개")
                for col in columns:
                    print(f"    - {col[0]} ({col[1]}, NULLABLE={col[2]}, DEFAULT={col[3]})")
                
                # 2. UPDATED_AT 컬럼 존재 여부 확인
                updated_at_exists = any(col[0] == 'UPDATED_AT' for col in columns)
                
                if updated_at_exists:
                    print("\n[2] UPDATED_AT 컬럼이 이미 존재합니다.")
                    print("  추가 작업이 필요하지 않습니다.")
                else:
                    print("\n[2] UPDATED_AT 컬럼 추가 중...")
                    try:
                        cur.execute("ALTER TABLE ONBOARDING_SESSION ADD UPDATED_AT DATE DEFAULT SYSDATE")
                        conn.commit()
                        print("  ✓ UPDATED_AT 컬럼 추가 완료!")
                        
                        # 3. 추가 후 확인
                        print("\n[3] 추가 후 테이블 구조 확인...")
                        cur.execute("""
                            SELECT COLUMN_NAME, DATA_TYPE, NULLABLE, DATA_DEFAULT
                            FROM USER_TAB_COLUMNS
                            WHERE TABLE_NAME = 'ONBOARDING_SESSION'
                            AND COLUMN_NAME = 'UPDATED_AT'
                        """)
                        result = cur.fetchone()
                        if result:
                            print(f"  ✓ 확인 완료: {result[0]} ({result[1]}, NULLABLE={result[2]}, DEFAULT={result[3]})")
                        else:
                            print("  ⚠️ 경고: 컬럼이 추가되었지만 확인할 수 없습니다.")
                            
                    except Exception as e:
                        error_msg = str(e)
                        if 'ORA-01430' in error_msg or '1430' in error_msg:
                            print("  - UPDATED_AT 컬럼이 이미 존재합니다 (다른 세션에서 추가됨)")
                        else:
                            print(f"  ✗ 오류 발생: {error_msg}")
                            raise
                
                print("\n" + "=" * 80)
                print("작업 완료!")
                print("=" * 80)
                
    except Exception as e:
        print(f"\n오류 발생: {str(e)}")
        import traceback
        print(traceback.format_exc())
        sys.exit(1)


if __name__ == '__main__':
    add_updated_at_column()

