#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import sys
import django

sys.path.insert(0, '.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from api.db.oracle_client import get_connection

# Oracle DB의 PRODUCT 테이블 구조 확인
with get_connection() as conn:
    with conn.cursor() as cur:
        # 테이블 구조 확인
        cur.execute("""
            SELECT column_name, data_type, nullable
            FROM user_tab_columns 
            WHERE table_name = 'PRODUCT'
            ORDER BY column_id
        """)
        columns = cur.fetchall()
        print("PRODUCT 테이블 구조:")
        for col in columns:
            print(f"  - {col[0]}: {col[1]} (nullable: {col[2]})")
        
        print("\n" + "="*80)
        
        # 샘플 데이터 확인
        cur.execute("SELECT * FROM PRODUCT WHERE ROWNUM <= 3")
        sample_rows = cur.fetchall()
        if sample_rows:
            col_names = [desc[0] for desc in cur.description]
            print("\n샘플 데이터 (첫 3개 행):")
            for row in sample_rows:
                print(f"\n  {dict(zip(col_names, row))}")

