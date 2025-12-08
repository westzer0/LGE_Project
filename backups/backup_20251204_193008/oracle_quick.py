#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Oracle DB 빠른 확인 - 엔터만 치면 실행
"""

import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

print("="*60)
print("Oracle DB 연결 확인")
print("="*60)

try:
    from api.db.oracle_client import fetch_one, fetch_all_dict
    
    # 연결 테스트
    result = fetch_one("SELECT USER, SYSDATE FROM DUAL")
    print(f"\n✅ 연결 성공!")
    print(f"   사용자: {result[0]}")
    print(f"   서버 시간: {result[1]}")
    
    # 테이블 목록
    tables = fetch_all_dict("SELECT table_name FROM user_tables ORDER BY table_name")
    print(f"\n✅ 테이블 {len(tables)}개 발견:\n")
    
    for t in tables:
        table_name = t['TABLE_NAME']
        try:
            count = fetch_one(f"SELECT COUNT(*) FROM {table_name}")[0]
            print(f"  • {table_name:<40} {count:>10,}개 행")
        except:
            print(f"  • {table_name:<40} {'조회 실패':>10}")
    
    print("\n" + "="*60)
    
except Exception as e:
    print(f"\n❌ 오류: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

