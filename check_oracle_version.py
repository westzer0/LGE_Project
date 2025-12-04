#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Oracle 데이터베이스 버전 확인 스크립트
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# .env 파일 로드
BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

# Oracle 연결 정보 가져오기
ORACLE_USER = os.environ.get('ORACLE_USER') or os.environ.get('DB_USER')
ORACLE_PASSWORD = os.environ.get('ORACLE_PASSWORD') or os.environ.get('DB_PASSWORD')
ORACLE_HOST = os.environ.get('ORACLE_HOST') or os.environ.get('DB_HOST')
ORACLE_PORT = os.environ.get('ORACLE_PORT') or os.environ.get('DB_PORT', '1521')
ORACLE_SID = os.environ.get('ORACLE_SID') or os.environ.get('DB_SERVICE_NAME')

print("="*60)
print("Oracle 데이터베이스 버전 확인")
print("="*60)
print(f"호스트: {ORACLE_HOST}")
print(f"포트: {ORACLE_PORT}")
print(f"SID/Service: {ORACLE_SID}")
print(f"사용자: {ORACLE_USER}")
print("-"*60)

# Thick 모드 활성화 시도
try:
    import oracledb
    try:
        instant_client_path = os.environ.get('ORACLE_INSTANT_CLIENT_PATH')
        if instant_client_path and Path(instant_client_path).exists():
            oracledb.init_oracle_client(lib_dir=instant_client_path)
            print("[Oracle] Thick 모드 활성화 완료")
        else:
            try:
                oracledb.init_oracle_client()
                print("[Oracle] Thick 모드 활성화 완료 (PATH에서 자동 감지)")
            except:
                print("[Oracle] Thin 모드 사용 (Thick 모드 초기화 실패)")
    except Exception as e:
        error_msg = str(e).lower()
        if "already initialized" in error_msg:
            print("[Oracle] Thick 모드 이미 활성화됨")
        else:
            print(f"[Oracle] Thin 모드 사용: {e}")
except ImportError:
    print("❌ oracledb 모듈을 찾을 수 없습니다.")
    sys.exit(1)

# 연결 시도
try:
    # SID 기반 연결
    dsn = oracledb.makedsn(host=ORACLE_HOST, port=int(ORACLE_PORT), sid=ORACLE_SID)
    
    print("\n연결 시도 중...")
    connection = oracledb.connect(
        user=ORACLE_USER,
        password=ORACLE_PASSWORD,
        dsn=dsn
    )
    
    print("✅ 연결 성공!\n")
    
    # 버전 정보 조회
    cursor = connection.cursor()
    
    # Oracle 버전 확인
    cursor.execute("SELECT banner FROM v$version WHERE banner LIKE 'Oracle%'")
    version = cursor.fetchone()
    if version:
        print(f"Oracle 버전: {version[0]}")
    
    # 전체 버전 정보
    print("\n전체 버전 정보:")
    cursor.execute("SELECT banner FROM v$version")
    versions = cursor.fetchall()
    for v in versions:
        print(f"  - {v[0]}")
    
    # 추가 정보 (권한이 있는 경우에만)
    try:
        cursor.execute("SELECT * FROM v$instance")
        instance_info = cursor.fetchone()
        if instance_info:
            print(f"\n인스턴스 정보:")
            print(f"  인스턴스명: {instance_info[0]}")
            print(f"  호스트명: {instance_info[1]}")
            print(f"  버전: {instance_info[2]}")
            print(f"  시작 시간: {instance_info[3]}")
            print(f"  상태: {instance_info[4]}")
    except Exception:
        pass  # v$instance 접근 권한이 없는 경우 스킵
    
    cursor.close()
    connection.close()
    
    print("\n" + "="*60)
    
except Exception as e:
    print(f"\n❌ 연결 실패!")
    print(f"오류: {type(e).__name__}: {str(e)}")
    print("="*60)
    import traceback
    traceback.print_exc()
    sys.exit(1)

