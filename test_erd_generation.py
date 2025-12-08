#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

import django
django.setup()

from api.db.oracle_client import get_connection, fetch_all_dict, DatabaseDisabledError

try:
    print("테스트 시작...", flush=True)
    conn = get_connection()
    print("연결 성공!", flush=True)
    
    # 간단한 테이블 목록 조회
    tables = fetch_all_dict("SELECT TABLE_NAME FROM USER_TABLES ORDER BY TABLE_NAME")
    print(f"테이블 수: {len(tables)}", flush=True)
    
    for table in tables[:5]:
        print(f"  - {table['TABLE_NAME']}", flush=True)
    
    conn.close()
    print("테스트 완료!", flush=True)
    
except DatabaseDisabledError as e:
    print(f"DB가 비활성화되어 있습니다: {e}", flush=True)
except Exception as e:
    print(f"오류: {e}", flush=True)
    import traceback
    traceback.print_exc()
