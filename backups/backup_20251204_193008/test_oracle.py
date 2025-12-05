#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Oracle 직접 연결 테스트 (Thin 모드 강제)
SID 기반 연결 (SQL Developer에서 확인한 SID: xe)
"""
import oracledb
import os
from dotenv import load_dotenv
from pathlib import Path
import traceback

# .env 로드
BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

user = os.getenv("ORACLE_USER", "campus_24K_LG3_DX7_p3_4")
password = os.getenv("ORACLE_PASSWORD", "smhrd4")
host = os.getenv("ORACLE_HOST", "project-db-campus.smhrd.com")
port = int(os.getenv("ORACLE_PORT", "1524"))
sid = "xe"  # SQL Developer에서 확인한 SID

# SID 기반 DSN 생성
dsn = oracledb.makedsn(host=host, port=port, sid=sid)

print("="*60)
print("Oracle 데이터베이스 연결 확인 (SID 기반)")
print("="*60)
print("\n연결 설정:")
print(f"  USER: {user}")
print(f"  DSN:  {dsn}")
print(f"  Host: {host}")
print(f"  Port: {port}")
print(f"  SID:  {sid}")
print()

try:
    conn = oracledb.connect(user=user, password=password, dsn=dsn)
    print("✅ 연결 성공!")
    
    # 커서 테스트
    with conn.cursor() as cur:
        cur.execute("SELECT user FROM dual")
        row = cur.fetchone()
        print(f"현재 사용자: {row[0]}")
        
        # 추가 정보 확인
        cur.execute("SELECT USER, SYSDATE, '연결 성공!' FROM DUAL")
        result = cur.fetchone()
        
        print("\n" + "="*60)
        print("✅ 전체 테스트 성공!")
        print("="*60)
        print(f"사용자: {result[0]}")
        print(f"서버 시간: {result[1]}")
        print(f"상태: {result[2]}")
        print("="*60)
    
    conn.close()
    print("\n✅ 커서 테스트까지 완료!")
    exit(0)
    
except Exception as e:
    print("❌ 연결 또는 커서 테스트 실패!")
    print("\n" + "="*60)
    print("상세 에러 정보")
    print("="*60)
    print(f"repr(e): {repr(e)}")
    print(f"str(e): {str(e)}")
    print(f"type(e).__name__: {type(e).__name__}")
    
    # ORA 에러 코드 추출 시도
    error_str = str(e)
    if "ORA-" in error_str:
        import re
        ora_codes = re.findall(r'ORA-\d{5}', error_str)
        if ora_codes:
            print(f"\n발견된 ORA 에러 코드: {', '.join(set(ora_codes))}")
    
    print("\n" + "="*60)
    print("전체 traceback:")
    print("="*60)
    traceback.print_exc()
    
    # oracledb 버전 정보
    try:
        print(f"\noracledb 버전: {oracledb.__version__}")
    except:
        pass
    
    exit(1)
