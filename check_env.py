#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.env 파일 존재 및 환경 변수 로드 확인 스크립트
"""
from pathlib import Path
from dotenv import load_dotenv
import os

print("="*60)
print(".env 파일 및 환경 변수 확인")
print("="*60)

env_path = Path('.env')
print(f"\n1. .env 파일 존재 여부:")
print(f"   존재: {env_path.exists()}")
if env_path.exists():
    print(f"   경로: {env_path.resolve()}")
    print(f"   크기: {env_path.stat().st_size} bytes")
else:
    print(f"   ❌ .env 파일이 없습니다!")

print(f"\n2. env.example 파일 존재 여부:")
example_path = Path('env.example')
print(f"   존재: {example_path.exists()}")

print(f"\n3. 환경 변수 로드 테스트:")
if env_path.exists():
    load_dotenv(env_path)
    print("   ✅ .env 파일 로드 시도 완료")
else:
    print("   ⚠️  .env 파일이 없어 로드할 수 없습니다")

print(f"\n4. Oracle 환경 변수 확인:")
oracle_vars = {
    'ORACLE_USER': os.getenv('ORACLE_USER'),
    'ORACLE_PASSWORD': os.getenv('ORACLE_PASSWORD'),
    'ORACLE_HOST': os.getenv('ORACLE_HOST'),
    'ORACLE_PORT': os.getenv('ORACLE_PORT'),
    'ORACLE_SERVICE_NAME': os.getenv('ORACLE_SERVICE_NAME'),
}

all_set = True
for key, value in oracle_vars.items():
    if value:
        print(f"   ✅ {key}: {value}")
    else:
        print(f"   ❌ {key}: None (설정되지 않음)")
        all_set = False

print("\n" + "="*60)
if not env_path.exists():
    print("❌ .env 파일이 없습니다!")
    print("\n해결 방법:")
    print("  1. env.example 파일을 복사하여 .env 파일을 만드세요:")
    print("     Copy-Item env.example .env")
    print("  2. .env 파일을 열어 ORACLE_* 값들을 실제 값으로 변경하세요")
elif not all_set:
    print("⚠️  일부 환경 변수가 설정되지 않았습니다!")
    print("\n.env 파일에 다음이 모두 설정되어 있어야 합니다:")
    for key in oracle_vars.keys():
        print(f"  - {key}")
else:
    print("✅ 모든 환경 변수가 올바르게 설정되어 있습니다!")
    print("\n다음 단계: python test_oracle.py 실행")
print("="*60)



