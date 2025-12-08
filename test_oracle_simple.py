#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

# 환경 변수 설정
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

# Django 설정 로드
import django
django.setup()

# 이제 oracle_client 사용 가능
from api.db.oracle_client import get_connection, fetch_all_dict, fetch_one

print("=" * 60)
print("Oracle DB 연결 테스트")
print("=" * 60)

# 1. 연결 테스트
try:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT SYSDATE FROM DUAL")
            result = cur.fetchone()
            print(f"✅ 연결 성공! DB 시간: {result[0]}")
except Exception as e:
    print(f"❌ 연결 실패: {e}")
    sys.exit(1)

# 2. 테이블 목록
try:
    sql = "SELECT table_name FROM user_tables ORDER BY table_name"
    tables = fetch_all_dict(sql)
    print(f"\n✅ 총 {len(tables)}개의 테이블:")
    for i, table in enumerate(tables[:10], 1):
        print(f"   {i}. {table['TABLE_NAME']}")
except Exception as e:
    print(f"❌ 테이블 목록 조회 실패: {e}")

# 3. PRODUCT 테이블
try:
    sql = "SELECT COUNT(*) as cnt FROM PRODUCT"
    result = fetch_one(sql)
    print(f"\n✅ PRODUCT 테이블: {result[0]}개 행")
    
    sql_sample = "SELECT * FROM PRODUCT WHERE ROWNUM <= 3"
    samples = fetch_all_dict(sql_sample)
    if samples and len(samples) > 0:
        print("\n   샘플 데이터:")
        for i, row in enumerate(samples, 1):
            cols = list(row.keys())[:3]  # 처음 3개 컬럼만
            print(f"   {i}. {cols[0]}: {row.get(cols[0], 'N/A')}")
except Exception as e:
    print(f"⚠️ PRODUCT 테이블 조회 실패: {e}")

# 4. MEMBER 테이블
try:
    sql = "SELECT COUNT(*) as cnt FROM MEMBER"
    result = fetch_one(sql)
    print(f"\n✅ MEMBER 테이블: {result[0]}개 행")
except Exception as e:
    print(f"⚠️ MEMBER 테이블 조회 실패: {e}")

print("\n" + "=" * 60)
print("테스트 완료!")
print("=" * 60)
