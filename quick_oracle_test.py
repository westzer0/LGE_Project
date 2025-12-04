#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
import os
from pathlib import Path

# 즉시 출력
sys.stdout.flush()
sys.stderr.flush()

print("스크립트 시작...", flush=True)

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

print(f"BASE_DIR: {BASE_DIR}", flush=True)

try:
    print("모듈 import 시도...", flush=True)
    from api.db.oracle_client import get_connection, fetch_one
    print("✅ 모듈 import 성공", flush=True)
    
    print("연결 테스트...", flush=True)
    result = fetch_one("SELECT USER, SYSDATE FROM DUAL")
    print(f"✅ 연결 성공! 사용자: {result[0]}, 시간: {result[1]}", flush=True)
    
    # 테이블 목록
    from api.db.oracle_client import fetch_all_dict
    tables = fetch_all_dict("SELECT table_name FROM user_tables ORDER BY table_name")
    print(f"✅ 테이블 {len(tables)}개 발견:", flush=True)
    for t in tables:
        print(f"  - {t['TABLE_NAME']}", flush=True)
        
except Exception as e:
    print(f"❌ 오류: {type(e).__name__}: {e}", flush=True)
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("완료!", flush=True)


