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

from api.db.oracle_client import get_connection, fetch_all_dict, fetch_one

print("=" * 60)
print("Oracle DB 연결 테스트")
print("=" * 60)

try:
    # 1. 연결 테스트
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT SYSDATE FROM DUAL")
            result = cur.fetchone()
            print(f"✅ 연결 성공! DB 시간: {result[0]}")
    
    # 2. 테이블 목록
    tables = fetch_all_dict("SELECT table_name FROM user_tables ORDER BY table_name")
    print(f"\n✅ 총 {len(tables)}개의 테이블 발견:")
    for i, table in enumerate(tables[:15], 1):
        print(f"   {i}. {table['TABLE_NAME']}")
    if len(tables) > 15:
        print(f"   ... 외 {len(tables) - 15}개")
    
    # 3. PRODUCT 테이블
    try:
        product_count = fetch_one("SELECT COUNT(*) FROM PRODUCT")
        print(f"\n✅ PRODUCT 테이블: {product_count[0]}개 행")
        
        samples = fetch_all_dict("SELECT PRODUCT_ID, PRODUCT_NAME FROM PRODUCT WHERE ROWNUM <= 3")
        if samples:
            print("\n   샘플 데이터:")
            for i, row in enumerate(samples, 1):
                print(f"   {i}. ID: {row.get('PRODUCT_ID')}, 이름: {row.get('PRODUCT_NAME', 'N/A')[:50]}")
    except Exception as e:
        print(f"\n⚠️ PRODUCT 테이블 조회 실패: {e}")
    
    # 4. MEMBER 테이블
    try:
        member_count = fetch_one("SELECT COUNT(*) FROM MEMBER")
        print(f"\n✅ MEMBER 테이블: {member_count[0]}개 행")
    except Exception as e:
        print(f"\n⚠️ MEMBER 테이블 조회 실패: {e}")
    
    # 5. ONBOARDING 테이블
    try:
        onboarding_count = fetch_one("SELECT COUNT(*) FROM ONBOARDING")
        print(f"\n✅ ONBOARDING 테이블: {onboarding_count[0]}개 행")
    except Exception as e:
        print(f"\n⚠️ ONBOARDING 테이블 조회 실패: {e}")
    
    print("\n" + "=" * 60)
    print("✅ 모든 테스트 완료!")
    print("=" * 60)
    
except Exception as e:
    print(f"\n❌ 오류 발생: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
