#!/usr/bin/env python
"""SQLite DB의 테이블 목록 확인"""
import sqlite3
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
db_path = BASE_DIR / 'db.sqlite3'

if not db_path.exists():
    print(f"❌ DB 파일이 없습니다: {db_path}")
    exit(1)

print(f"📁 DB 파일: {db_path}")
print(f"📊 파일 크기: {db_path.stat().st_size} bytes\n")

conn = sqlite3.connect(str(db_path))
cursor = conn.cursor()

# 모든 테이블 목록
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
tables = cursor.fetchall()

print(f"📋 전체 테이블 수: {len(tables)}\n")
print("=" * 60)

# Onboarding 관련 테이블 찾기
onboarding_tables = []
for table in tables:
    table_name = table[0]
    if 'onboarding' in table_name.lower() or 'onboard' in table_name.lower():
        onboarding_tables.append(table_name)
        # 테이블 구조 확인
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = cursor.fetchall()
        print(f"\n✅ {table_name}")
        print(f"   컬럼 수: {len(columns)}")
        for col in columns[:5]:  # 처음 5개만
            print(f"   - {col[1]} ({col[2]})")
        if len(columns) > 5:
            print(f"   ... 외 {len(columns)-5}개 컬럼")

if not onboarding_tables:
    print("\n❌ Onboarding 관련 테이블이 없습니다!")
    print("\n전체 테이블 목록:")
    for table in tables[:20]:  # 처음 20개만
        print(f"  - {table[0]}")
    if len(tables) > 20:
        print(f"  ... 외 {len(tables)-20}개 테이블")
else:
    print(f"\n✅ Onboarding 관련 테이블 {len(onboarding_tables)}개 발견")

# api_onboardingsession 테이블이 있는지 확인
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='api_onboardingsession'")
if cursor.fetchone():
    print("\n✅ 'api_onboardingsession' 테이블이 존재합니다!")
    
    # 레코드 수 확인
    cursor.execute("SELECT COUNT(*) FROM api_onboardingsession")
    count = cursor.fetchone()[0]
    print(f"   레코드 수: {count}")
else:
    print("\n❌ 'api_onboardingsession' 테이블이 없습니다!")

conn.close()

