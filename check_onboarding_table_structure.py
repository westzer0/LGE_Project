#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
ONBOARDING_SESSION 테이블 구조 확인
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

import django
django.setup()

from api.db.oracle_client import get_connection

print("=" * 80)
print("ONBOARDING_SESSION 테이블 구조 확인")
print("=" * 80)
print()

with get_connection() as conn:
    with conn.cursor() as cur:
        # 테이블 컬럼 확인
        cur.execute("""
            SELECT COLUMN_NAME, DATA_TYPE, DATA_LENGTH, NULLABLE
            FROM USER_TAB_COLUMNS 
            WHERE TABLE_NAME = 'ONBOARDING_SESSION'
            ORDER BY COLUMN_ID
        """)
        columns = cur.fetchall()
        
        print("[테이블 컬럼 목록]")
        for col_name, data_type, data_length, nullable in columns:
            null_str = "NULL" if nullable == 'Y' else "NOT NULL"
            length_str = f"({data_length})" if data_length else ""
            print(f"  {col_name:30} {data_type}{length_str:15} {null_str}")
        
        print()
        
        # CLOB 컬럼 확인
        cur.execute("""
            SELECT COLUMN_NAME, DATA_TYPE
            FROM USER_TAB_COLUMNS 
            WHERE TABLE_NAME = 'ONBOARDING_SESSION' 
            AND DATA_TYPE LIKE '%LOB%'
            ORDER BY COLUMN_NAME
        """)
        clob_columns = cur.fetchall()
        
        print("[CLOB 컬럼]")
        if clob_columns:
            for col_name, data_type in clob_columns:
                print(f"  {col_name}: {data_type}")
        else:
            print("  CLOB 컬럼 없음 (정규화 테이블 사용)")
        
        print()
        
        # 샘플 데이터 확인
        print("[샘플 데이터 (최근 3개)]")
        cur.execute("""
            SELECT SESSION_ID, VIBE, HOUSING_TYPE, PYUNG, CREATED_AT
            FROM (
                SELECT SESSION_ID, VIBE, HOUSING_TYPE, PYUNG, CREATED_AT
                FROM ONBOARDING_SESSION
                ORDER BY CREATED_AT DESC
            )
            WHERE ROWNUM <= 3
        """)
        samples = cur.fetchall()
        for session_id, vibe, housing_type, pyung, created_at in samples:
            print(f"  {session_id}: vibe={vibe}, housing={housing_type}, pyung={pyung}, created={created_at}")

