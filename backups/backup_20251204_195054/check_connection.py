#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Oracle 데이터베이스 연결 확인 (Django 사용)
Thick 모드 + SID 기반 연결
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# .env 파일 로드 (Django 설정 전에)
BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

# Thick 모드 활성화 (PATH에 있는 Oracle 클라이언트 사용)
try:
    import oracledb
    try:
        oracledb.init_oracle_client()  # PATH에서 oci.dll 찾게 함
        print("[Oracle] Thick 모드 활성화 완료")
    except Exception as e:
        error_msg = str(e).lower()
        if "already initialized" in error_msg:
            print("[Oracle] Thick 모드 이미 활성화됨")
        else:
            print(f"⚠️  Thick 모드 초기화 경고: {repr(e)}")
except ImportError:
    print("⚠️  oracledb 모듈을 찾을 수 없습니다.")

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

import django
django.setup()

from django.db import connection

print("="*60)
print("Oracle 데이터베이스 연결 확인 (Django)")
print("="*60)

db_config = connection.settings_dict
print(f"\n연결 설정:")
print(f"  NAME (DSN): {db_config.get('NAME')}")
print(f"  USER: {db_config.get('USER')}")
print(f"  HOST: {db_config.get('HOST')}")
print(f"  PORT: {db_config.get('PORT')}")
print(f"  SID: {db_config.get('NAME')}")

print("\n연결 테스트 중...")

try:
    with connection.cursor() as cursor:
        cursor.execute("SELECT USER, SYSDATE, '연결 성공!' FROM DUAL")
        result = cursor.fetchone()
        
        print("\n" + "="*60)
        print("✅ 연결 성공!")
        print("="*60)
        print(f"사용자: {result[0]}")
        print(f"서버 시간: {result[1]}")
        print(f"상태: {result[2]}")
        print("="*60)
        
        # 추가 정보 확인
        try:
            cursor.execute("SELECT banner FROM v$version WHERE ROWNUM = 1")
            version = cursor.fetchone()
            if version:
                print(f"\nOracle 버전: {version[0]}")
        except:
            pass
            
        sys.exit(0)
        
except Exception as e:
    print("\n" + "="*60)
    print("❌ 연결 실패!")
    print("="*60)
    print(f"오류: {type(e).__name__}: {str(e)}")
    print("="*60)
    
    # 상세 에러 정보
    import traceback
    print("\n상세 traceback:")
    traceback.print_exc()
    
    sys.exit(1)
