#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Oracle 계정 잠금 해제 스크립트

ORA-28000 오류가 발생했을 때 계정 잠금을 해제하는 도구입니다.
"""

import os
import sys
from pathlib import Path

try:
    import oracledb
except ImportError:
    print("오류: oracledb 모듈이 설치되지 않았습니다.")
    print("다음 명령어로 설치하세요: pip install oracledb")
    sys.exit(1)

# .env 파일 로드
try:
    from dotenv import load_dotenv
    BASE_DIR = Path(__file__).resolve().parent
    load_dotenv(BASE_DIR / ".env")
except ImportError:
    print("[경고] python-dotenv가 설치되지 않았습니다.")
except Exception as e:
    print(f"[경고] .env 파일 로드 실패: {e}")

# Oracle Instant Client 초기화
ORACLE_INSTANT_CLIENT_PATH = os.getenv(
    "ORACLE_INSTANT_CLIENT_PATH",
    r"C:\oracle\instantclient-basic-windows.x64-21.19.0.0.0dbru\instantclient_21_19"
)

try:
    oracledb.init_oracle_client(lib_dir=ORACLE_INSTANT_CLIENT_PATH)
    print(f"[Oracle] Thick 모드 초기화 완료")
except oracledb.ProgrammingError:
    print("[Oracle] Thick 모드 이미 초기화됨")
except Exception as e:
    error_msg = str(e).lower()
    if "already initialized" in error_msg:
        print("[Oracle] Thick 모드 이미 초기화됨")
    else:
        print(f"[경고] Thick 모드 초기화 실패: {e}")
        print("  Thin 모드로 시도합니다...")

# 잠긴 계정 정보
LOCKED_USER = os.getenv("ORACLE_USER", "campus_24K_LG3_DX7_p3_4")
ORACLE_HOST = os.getenv("ORACLE_HOST", "project-db-campus.smhrd.com")
ORACLE_PORT = int(os.getenv("ORACLE_PORT", "1524"))
ORACLE_SID = os.getenv("ORACLE_SID", "xe")

# DBA 계정 정보 (SYSTEM 또는 SYS 계정 필요)
# 주의: 실제 DBA 계정 정보를 입력해야 합니다
DBA_USER = os.getenv("ORACLE_DBA_USER", "system")
DBA_PASSWORD = os.getenv("ORACLE_DBA_PASSWORD", "")

DSN = oracledb.makedsn(ORACLE_HOST, ORACLE_PORT, sid=ORACLE_SID)


def check_account_status(username):
    """계정 상태 확인"""
    try:
        conn = oracledb.connect(user=DBA_USER, password=DBA_PASSWORD, dsn=DSN)
        cursor = conn.cursor()
        
        # 계정 상태 확인
        query = """
        SELECT username, account_status, lock_date, expiry_date
        FROM dba_users
        WHERE username = UPPER(:username)
        """
        cursor.execute(query, {"username": username})
        result = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        if result:
            username_db, status, lock_date, expiry_date = result
            print(f"\n[계정 상태 확인]", flush=True)
            print(f"  사용자명: {username_db}", flush=True)
            print(f"  상태: {status}", flush=True)
            print(f"  잠금일시: {lock_date if lock_date else '없음'}", flush=True)
            print(f"  만료일시: {expiry_date if expiry_date else '없음'}", flush=True)
            return status
        else:
            print(f"\n[오류] 사용자 '{username}'를 찾을 수 없습니다.", flush=True)
            return None
            
    except oracledb.Error as e:
        error_obj, = e.args
        if error_obj.code == 1017:  # ORA-01017: invalid username/password
            print(f"\n[오류] DBA 계정 인증 실패 (ORA-01017)")
            print(f"  DBA_USER: {DBA_USER}")
            print(f"  DBA_PASSWORD이 올바른지 확인하세요.")
        elif error_obj.code == 1031:  # ORA-01031: insufficient privileges
            print(f"\n[오류] 권한 부족 (ORA-01031)")
            print(f"  DBA 권한이 있는 계정(SYSTEM, SYS 등)을 사용해야 합니다.")
        else:
            print(f"\n[오류] 계정 상태 확인 실패: {error_obj}")
        return None


def unlock_account(username):
    """계정 잠금 해제"""
    try:
        conn = oracledb.connect(user=DBA_USER, password=DBA_PASSWORD, dsn=DSN)
        cursor = conn.cursor()
        
        # 계정 잠금 해제
        unlock_sql = f"ALTER USER {username.upper()} ACCOUNT UNLOCK"
        cursor.execute(unlock_sql)
        conn.commit()
        
        cursor.close()
        conn.close()
        
        print(f"\n[성공] 계정 '{username}' 잠금 해제 완료!", flush=True)
        return True
        
    except oracledb.Error as e:
        error_obj, = e.args
        if error_obj.code == 1017:  # ORA-01017
            print(f"\n[오류] DBA 계정 인증 실패 (ORA-01017)")
            print(f"  .env 파일에 ORACLE_DBA_USER와 ORACLE_DBA_PASSWORD를 설정하세요.")
        elif error_obj.code == 1031:  # ORA-01031
            print(f"\n[오류] 권한 부족 (ORA-01031)")
            print(f"  DBA 권한이 있는 계정을 사용해야 합니다.")
        else:
            print(f"\n[오류] 계정 잠금 해제 실패: {error_obj}")
        return False


def main():
    import sys
    sys.stdout.reconfigure(encoding='utf-8')
    
    print("=" * 60, flush=True)
    print("Oracle 계정 잠금 해제 도구", flush=True)
    print("=" * 60, flush=True)
    print(f"\n[연결 정보]", flush=True)
    print(f"  호스트: {ORACLE_HOST}:{ORACLE_PORT}", flush=True)
    print(f"  SID: {ORACLE_SID}", flush=True)
    print(f"  잠긴 계정: {LOCKED_USER}", flush=True)
    print(f"  DBA 계정: {DBA_USER}", flush=True)
    
    # 먼저 잠긴 계정으로 연결 시도해서 상태 확인
    print(f"\n[0단계] 잠긴 계정 연결 시도 중...", flush=True)
    try:
        test_conn = oracledb.connect(
            user=LOCKED_USER,
            password=os.getenv("ORACLE_PASSWORD", "smhrd4"),
            dsn=DSN
        )
        print("✅ 계정이 잠겨있지 않습니다! 연결 성공!", flush=True)
        test_conn.close()
        return
    except oracledb.Error as e:
        error_obj, = e.args
        if error_obj.code == 28000:
            print(f"❌ 계정이 잠겨있습니다 (ORA-28000)", flush=True)
        else:
            print(f"❌ 연결 실패: {error_obj}", flush=True)
            if error_obj.code != 28000:
                return
    
    if not DBA_PASSWORD:
        print(f"\n[경고] DBA_PASSWORD가 설정되지 않았습니다.", flush=True)
        print(f"  .env 파일에 다음을 추가하세요:", flush=True)
        print(f"  ORACLE_DBA_USER=system", flush=True)
        print(f"  ORACLE_DBA_PASSWORD=your_dba_password", flush=True)
        print(f"\n  또는 환경 변수로 설정하세요:", flush=True)
        print(f"  $env:ORACLE_DBA_PASSWORD='your_dba_password'", flush=True)
        print(f"\n[중요] 원격 DB이므로 DBA 계정 정보가 필요합니다.", flush=True)
        print(f"  DB 관리자에게 다음 SQL 실행을 요청하세요:", flush=True)
        print(f"  ALTER USER {LOCKED_USER.upper()} ACCOUNT UNLOCK;", flush=True)
        
        # 사용자 입력으로 비밀번호 받기
        try:
            dba_pwd = input(f"\nDBA 계정 비밀번호를 입력하세요 (Enter로 취소): ")
            if not dba_pwd:
                print("취소되었습니다.", flush=True)
                return
            global DBA_PASSWORD
            DBA_PASSWORD = dba_pwd
        except KeyboardInterrupt:
            print("\n취소되었습니다.", flush=True)
            return
    
    # 1. 계정 상태 확인
    print(f"\n[1단계] 계정 상태 확인 중...", flush=True)
    status = check_account_status(LOCKED_USER)
    
    if status is None:
        return
    
    # 2. 잠금 상태인지 확인
    if "LOCKED" not in status.upper():
        print(f"\n[정보] 계정이 잠겨있지 않습니다. 상태: {status}", flush=True)
        print(f"  다른 문제일 수 있습니다. 비밀번호를 확인하세요.", flush=True)
        return
    
    # 3. 잠금 해제
    print(f"\n[2단계] 계정 잠금 해제 중...", flush=True)
    if unlock_account(LOCKED_USER):
        # 4. 해제 후 상태 확인
        print(f"\n[3단계] 해제 후 상태 확인 중...", flush=True)
        check_account_status(LOCKED_USER)
        print(f"\n[완료] 이제 '{LOCKED_USER}' 계정으로 로그인할 수 있습니다.", flush=True)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n취소되었습니다.")
    except Exception as e:
        print(f"\n[오류] 예상치 못한 오류 발생: {e}")
        import traceback
        traceback.print_exc()
