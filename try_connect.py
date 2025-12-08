#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Oracle 계정 연결 시도 및 상태 확인
"""

import os
import sys
from pathlib import Path

try:
    import oracledb
except ImportError:
    print("오류: oracledb 모듈이 설치되지 않았습니다.")
    sys.exit(1)

# .env 파일 로드
try:
    from dotenv import load_dotenv
    BASE_DIR = Path(__file__).resolve().parent
    load_dotenv(BASE_DIR / ".env")
except ImportError:
    pass
except Exception as e:
    print(f"[경고] .env 파일 로드 실패: {e}")

# Oracle Instant Client 초기화
ORACLE_INSTANT_CLIENT_PATH = os.getenv(
    "ORACLE_INSTANT_CLIENT_PATH",
    r"C:\oracle\instantclient-basic-windows.x64-21.19.0.0.0dbru\instantclient_21_19"
)

try:
    oracledb.init_oracle_client(lib_dir=ORACLE_INSTANT_CLIENT_PATH)
    print("[Oracle] Thick 모드 초기화 완료")
except oracledb.ProgrammingError:
    pass
except Exception as e:
    error_msg = str(e).lower()
    if "already initialized" not in error_msg:
        print(f"[경고] Thick 모드 초기화 실패: {e}")

# 계정 정보
ORACLE_USER = "campus_24K_LG3_DX7_p3_4"
ORACLE_PASSWORD = "smhrd4"
ORACLE_HOST = "project-db-campus.smhrd.com"
ORACLE_PORT = 1524
ORACLE_SID = "xe"

DSN = oracledb.makedsn(ORACLE_HOST, ORACLE_PORT, sid=ORACLE_SID)

print("=" * 60)
print("Oracle 계정 연결 시도")
print("=" * 60)
print(f"사용자: {ORACLE_USER}")
print(f"호스트: {ORACLE_HOST}:{ORACLE_PORT}")
print(f"SID: {ORACLE_SID}")
print()

# 연결 시도
print("[연결 시도 중...]")
try:
    conn = oracledb.connect(
        user=ORACLE_USER,
        password=ORACLE_PASSWORD,
        dsn=DSN
    )
    print("✅ 연결 성공! 계정이 잠겨있지 않습니다.")
    print()
    
    # 간단한 쿼리 테스트
    cursor = conn.cursor()
    cursor.execute("SELECT SYSDATE FROM DUAL")
    result = cursor.fetchone()
    print(f"✅ 데이터베이스 시간: {result[0]}")
    print()
    print("🎉 계정이 정상적으로 작동합니다!")
    
    cursor.close()
    conn.close()
    sys.exit(0)
    
except oracledb.Error as e:
    error_obj, = e.args
    print(f"❌ 연결 실패: {error_obj}")
    print()
    
    if error_obj.code == 28000:
        print("[확인] 계정이 여전히 잠겨있습니다 (ORA-28000)")
        print()
        print("=" * 60)
        print("해결 방법")
        print("=" * 60)
        print()
        print("일반 사용자 계정 정보만으로는 계정 잠금을 해제할 수 없습니다.")
        print("다음 중 하나의 방법이 필요합니다:")
        print()
        print("1. DBA 계정 정보 필요")
        print("   - SYSTEM 또는 SYS 계정으로 접속")
        print("   - ALTER USER CAMPUS_24K_LG3_DX7_P3_4 ACCOUNT UNLOCK; 실행")
        print()
        print("2. DB 관리자에게 요청")
        print("   - SEND_REQUEST_EMAIL.txt 파일의 내용을 전달")
        print("   - 또는 unlock_account_request.sql 파일 전달")
        print()
        print("3. 자동 해제 대기")
        print("   - PASSWORD_LOCK_TIME이 지나면 자동으로 해제됩니다")
        print("   - 보통 24시간 후 자동 해제")
        print()
        print("=" * 60)
        
    elif error_obj.code == 1017:
        print("[확인] 비밀번호가 잘못되었습니다 (ORA-01017)")
        print("비밀번호를 확인하세요.")
    else:
        print(f"[확인] 오류 코드: {error_obj.code}")
        print(f"오류 메시지: {error_obj.message}")
