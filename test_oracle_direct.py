#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Oracle 직접 연결 테스트 (Django 없이)
Service Name 사용 확인
"""
import os
import sys

try:
    import oracledb
except ImportError:
    print("❌ oracledb 모듈을 찾을 수 없습니다.")
    print("설치: pip install oracledb")
    sys.exit(1)

# 환경 변수에서 설정 로드
from pathlib import Path
from dotenv import load_dotenv

env_path = Path(__file__).resolve().parent / '.env'
load_dotenv(dotenv_path=env_path)

# Oracle 연결 정보
host = os.environ.get('ORACLE_HOST') or os.environ.get('DB_HOST', 'project-db-campus.smhrd.com')
port = os.environ.get('ORACLE_PORT') or os.environ.get('DB_PORT', '1524')
service_name = os.environ.get('ORACLE_SERVICE_NAME') or os.environ.get('DB_SERVICE_NAME') or os.environ.get('DB_NAME', 'MAPPP')
user = os.environ.get('ORACLE_USER') or os.environ.get('DB_USER', '')
password = os.environ.get('ORACLE_PASSWORD') or os.environ.get('DB_PASSWORD', '')

print("="*60)
print("Oracle 직접 연결 테스트 (Service Name 사용)")
print("="*60)
print(f"\n연결 정보:")
print(f"  Host: {host}")
print(f"  Port: {port}")
print(f"  Service Name: {service_name}")
print(f"  User: {user}")
print(f"  Password: {'설정됨' if password else '없음'}")

# 방법 1: DSN 문자열 사용
print("\n" + "="*60)
print("방법 1: DSN 문자열 사용")
print("="*60)
dsn = f"{host}:{port}/{service_name}"
print(f"DSN: {dsn}")

try:
    conn = oracledb.connect(
        user=user,
        password=password,
        dsn=dsn
    )
    cursor = conn.cursor()
    cursor.execute("SELECT USER, SYSDATE, '연결 성공!' FROM DUAL")
    result = cursor.fetchone()
    print(f"\n✅ 연결 성공!")
    print(f"사용자: {result[0]}")
    print(f"서버 시간: {result[1]}")
    print(f"상태: {result[2]}")
    cursor.close()
    conn.close()
    print("\n✅ 방법 1이 성공했습니다. 이 형식을 Django에서 사용해야 합니다.")
    sys.exit(0)
    
except Exception as e:
    print(f"\n❌ 방법 1 실패: {type(e).__name__}: {str(e)}")

# 방법 2: host, port, service_name 파라미터 사용
print("\n" + "="*60)
print("방법 2: host, port, service_name 파라미터 사용")
print("="*60)

try:
    conn = oracledb.connect(
        user=user,
        password=password,
        host=host,
        port=int(port),
        service_name=service_name
    )
    cursor = conn.cursor()
    cursor.execute("SELECT USER, SYSDATE, '연결 성공!' FROM DUAL")
    result = cursor.fetchone()
    print(f"\n✅ 연결 성공!")
    print(f"사용자: {result[0]}")
    print(f"서버 시간: {result[1]}")
    print(f"상태: {result[2]}")
    cursor.close()
    conn.close()
    print("\n✅ 방법 2가 성공했습니다.")
    sys.exit(0)
    
except Exception as e:
    print(f"\n❌ 방법 2 실패: {type(e).__name__}: {str(e)}")

print("\n" + "="*60)
print("❌ 모든 연결 방법이 실패했습니다.")
print("="*60)
sys.exit(1)



