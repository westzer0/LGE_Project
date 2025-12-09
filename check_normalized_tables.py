#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""정규화 테이블 존재 여부 확인"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

import django
django.setup()

from api.db.oracle_client import get_connection

with get_connection() as conn:
    with conn.cursor() as cur:
        cur.execute("""
            SELECT TABLE_NAME 
            FROM USER_TABLES 
            WHERE TABLE_NAME LIKE '%ONBOARD%' 
               OR TABLE_NAME LIKE '%MAIN%'
               OR TABLE_NAME LIKE '%PRIORIT%'
            ORDER BY TABLE_NAME
        """)
        tables = [row[0] for row in cur.fetchall()]
        print("관련 테이블 목록:")
        for table in tables:
            print(f"  - {table}")

