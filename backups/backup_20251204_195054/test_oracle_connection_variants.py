#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Oracle 연결 형식 변형 테스트
Service Name과 SID를 모두 시도
"""
import oracledb
import os
from dotenv import load_dotenv
from pathlib import Path

# .env 파일 로드
env_path = Path(__file__).resolve().parent / '.env'
load_dotenv(dotenv_path=env_path)

user = os.getenv("ORACLE_USER")
password = os.getenv("ORACLE_PASSWORD")
host = os.getenv("ORACLE_HOST")
port = os.getenv("ORACLE_PORT", "1524")
service_name = os.getenv("ORACLE_SERVICE_NAME", "MAPPP")

print("="*60)
print("Oracle 연결 형식 변형 테스트")
print("="*60)
print(f"\n기본 정보:")
print(f"  USER: {user}")
print(f"  HOST: {host}")
print(f"  PORT: {port}")
print(f"  SERVICE_NAME: {service_name}")

if not user or not password or not host:
    print("\n❌ 필수 환경 변수가 설정되지 않았습니다!")
    exit(1)

# 테스트할 연결 형식들
connection_variants = [
    {
        "name": "Service Name 형식 (현재 설정)",
        "dsn": f"{host}:{port}/{service_name}",
        "description": f"DSN: {host}:{port}/{service_name}"
    },
    {
        "name": "Service Name 형식 (별도 파라미터)",
        "params": {
            "user": user,
            "password": password,
            "host": host,
            "port": int(port),
            "service_name": service_name
        },
        "description": f"host={host}, port={port}, service_name={service_name}"
    },
    {
        "name": "SID 형식 시도",
        "params": {
            "user": user,
            "password": password,
            "host": host,
            "port": int(port),
            "sid": service_name
        },
        "description": f"host={host}, port={port}, sid={service_name}"
    },
    {
        "name": "SID 형식 (Easy Connect)",
        "dsn": f"{host}:{port}:{service_name}",
        "description": f"DSN: {host}:{port}:{service_name} (콜론 구분)"
    },
]

print(f"\n총 {len(connection_variants)}가지 연결 형식을 테스트합니다...\n")

success_count = 0
for i, variant in enumerate(connection_variants, 1):
    print(f"\n{'='*60}")
    print(f"테스트 {i}/{len(connection_variants)}: {variant['name']}")
    print(f"{'='*60}")
    print(f"설정: {variant['description']}")
    
    try:
        conn = None
        if "dsn" in variant:
            # DSN 문자열 사용
            conn = oracledb.connect(
                user=user,
                password=password,
                dsn=variant["dsn"]
            )
        elif "params" in variant:
            # 파라미터 직접 전달
            conn = oracledb.connect(**variant["params"])
        
        # 간단한 쿼리로 연결 확인
        with conn.cursor() as cur:
            cur.execute("SELECT USER, SYSDATE FROM DUAL")
            result = cur.fetchone()
            print(f"\n✅ 연결 성공!")
            print(f"   사용자: {result[0]}")
            print(f"   서버 시간: {result[1]}")
            print(f"\n✅ 이 형식이 작동합니다: {variant['name']}")
            
            # 추가 정보 확인
            try:
                cur.execute("SELECT sys_context('USERENV', 'SERVICE_NAME'), sys_context('USERENV', 'DB_NAME') FROM DUAL")
                service_info = cur.fetchone()
                print(f"   실제 Service Name: {service_info[0]}")
                print(f"   DB Name: {service_info[1]}")
            except:
                pass
            
            success_count += 1
            conn.close()
            print(f"\n✅ 성공한 연결 형식: {variant['name']}")
            print(f"   사용 설정: {variant['description']}")
            break
            
    except Exception as e:
        print(f"\n❌ 실패: {type(e).__name__}: {str(e)}")
        if conn:
            try:
                conn.close()
            except:
                pass

print(f"\n{'='*60}")
print(f"테스트 완료")
print(f"{'='*60}")
if success_count > 0:
    print(f"✅ {success_count}개의 연결 형식이 성공했습니다.")
    print(f"\n성공한 형식을 Django 설정에 사용하세요.")
else:
    print(f"❌ 모든 연결 형식이 실패했습니다.")
    print(f"\n확인 사항:")
    print(f"  1. 학원에서 제공한 정확한 Service Name이나 SID 확인")
    print(f"  2. 네트워크 연결 상태 확인")
    print(f"  3. Oracle 서버가 실행 중인지 확인")
    print(f"  4. 방화벽 설정 확인")
print(f"{'='*60}")

