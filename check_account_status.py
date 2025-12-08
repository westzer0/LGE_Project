#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Oracle 계정 상태 확인 및 잠금 해제 시도
"""

import os
import sys
from pathlib import Path

# 출력 버퍼링 비활성화
sys.stdout.reconfigure(encoding='utf-8')

try:
    import oracledb
except ImportError:
    print("오류: oracledb 모듈이 설치되지 않았습니다.", flush=True)
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
    print("[Oracle] Thick 모드 초기화 완료", flush=True)
except oracledb.ProgrammingError:
    pass
except Exception as e:
    error_msg = str(e).lower()
    if "already initialized" not in error_msg:
        print(f"[경고] Thick 모드 초기화 실패: {e}", flush=True)

# 계정 정보
ORACLE_USER = "campus_24K_LG3_DX7_p3_4"
ORACLE_PASSWORD = "smhrd4"
ORACLE_HOST = "project-db-campus.smhrd.com"
ORACLE_PORT = 1524
ORACLE_SID = "xe"

DSN = oracledb.makedsn(ORACLE_HOST, ORACLE_PORT, sid=ORACLE_SID)

print("=" * 60, flush=True)
print("Oracle 계정 상태 확인", flush=True)
print("=" * 60, flush=True)
print(f"사용자: {ORACLE_USER}", flush=True)
print(f"호스트: {ORACLE_HOST}:{ORACLE_PORT}", flush=True)
print(f"SID: {ORACLE_SID}", flush=True)
print(flush=True)

# 1. 제공된 계정으로 직접 연결 시도
print("[1단계] 제공된 계정으로 연결 시도...", flush=True)
try:
    conn = oracledb.connect(
        user=ORACLE_USER,
        password=ORACLE_PASSWORD,
        dsn=DSN
    )
    print("✅ 연결 성공! 계정이 잠겨있지 않습니다.", flush=True)
    conn.close()
    sys.exit(0)
except oracledb.Error as e:
    error_obj, = e.args
    print(f"❌ 연결 실패: {error_obj}", flush=True)
    
    if error_obj.code == 28000:
        print("\n[확인] 계정이 잠겨있습니다 (ORA-28000)", flush=True)
        print("\n[해결 방법]", flush=True)
        print("계정 잠금을 해제하려면 DBA 권한이 필요합니다.", flush=True)
        print("다음 중 하나를 선택하세요:", flush=True)
        print(flush=True)
        print("1. DBA 계정 정보가 있는 경우:", flush=True)
        print("   .env 파일에 추가:", flush=True)
        print("   ORACLE_DBA_USER=system", flush=True)
        print("   ORACLE_DBA_PASSWORD=your_dba_password", flush=True)
        print("   그 다음 python unlock_oracle_account.py 실행", flush=True)
        print(flush=True)
        print("2. DB 관리자에게 요청:", flush=True)
        print("   다음 SQL을 실행해달라고 요청:", flush=True)
        print(f"   ALTER USER {ORACLE_USER.upper()} ACCOUNT UNLOCK;", flush=True)
        print(flush=True)
        print("3. 자동 해제 대기:", flush=True)
        print("   PASSWORD_LOCK_TIME이 지나면 자동으로 해제됩니다 (보통 24시간)", flush=True)
    elif error_obj.code == 1017:
        print("\n[확인] 비밀번호가 잘못되었습니다 (ORA-01017)", flush=True)
        print("비밀번호를 확인하세요.", flush=True)
    else:
        print(f"\n[확인] 오류 코드: {error_obj.code}", flush=True)
        print(f"오류 메시지: {error_obj.message}", flush=True)
