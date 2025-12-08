#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Oracle DB 연결 상태 및 설정 확인 스크립트
"""
import sys
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

print("=" * 70)
print("Oracle DB 연결 상태 확인")
print("=" * 70)

# 1. 환경 변수 확인
print("\n[1] 환경 변수 확인:")
print("-" * 70)
env_vars = {
    'USE_ORACLE': os.getenv('USE_ORACLE', 'false'),
    'DISABLE_DB': os.getenv('DISABLE_DB', 'false'),
    'ORACLE_USER': os.getenv('ORACLE_USER', '미설정'),
    'ORACLE_HOST': os.getenv('ORACLE_HOST', '미설정'),
    'ORACLE_PORT': os.getenv('ORACLE_PORT', '미설정'),
    'ORACLE_SID': os.getenv('ORACLE_SID', '미설정'),
    'ORACLE_INSTANT_CLIENT_PATH': os.getenv('ORACLE_INSTANT_CLIENT_PATH', '미설정'),
}
for key, value in env_vars.items():
    if 'PASSWORD' not in key:
        print(f"  {key}: {value}")

# 2. oracledb 모듈 확인
print("\n[2] oracledb 모듈 확인:")
print("-" * 70)
try:
    import oracledb
    print(f"  ✅ oracledb 모듈 설치됨 (버전: {oracledb.__version__})")
except ImportError:
    print("  ❌ oracledb 모듈이 설치되지 않았습니다.")
    print("     설치: pip install oracledb")
    sys.exit(1)

# 3. Oracle Instant Client 확인
print("\n[3] Oracle Instant Client 확인:")
print("-" * 70)
try:
    # Thick 모드 초기화 시도
    instant_client_path = os.getenv(
        'ORACLE_INSTANT_CLIENT_PATH',
        r'C:\oracle\instantclient-basic-windows.x64-21.19.0.0.0dbru\instantclient_21_19'
    )
    
    if os.path.exists(instant_client_path):
        print(f"  ✅ Oracle Instant Client 경로 존재: {instant_client_path}")
    else:
        print(f"  ⚠️ Oracle Instant Client 경로 없음: {instant_client_path}")
    
    try:
        oracledb.init_oracle_client(lib_dir=instant_client_path)
        print("  ✅ Thick 모드 초기화 성공")
    except oracledb.ProgrammingError:
        print("  ✅ Thick 모드 이미 초기화됨")
    except Exception as e:
        print(f"  ⚠️ Thick 모드 초기화 실패: {e}")
        print("     Thin 모드로 시도합니다...")
except Exception as e:
    print(f"  ⚠️ Oracle Instant Client 확인 실패: {e}")

# 4. DB 연결 정보 확인
print("\n[4] DB 연결 정보:")
print("-" * 70)
from api.db.oracle_client import ORACLE_USER, ORACLE_HOST, ORACLE_PORT, ORACLE_SID, DSN, DISABLE_DB

if DISABLE_DB:
    print("  ⚠️ DB 연결이 비활성화되어 있습니다. (DISABLE_DB=true)")
    print("     연결 테스트를 건너뜁니다.")
    sys.exit(0)

print(f"  사용자: {ORACLE_USER}")
print(f"  호스트: {ORACLE_HOST}:{ORACLE_PORT}")
print(f"  SID: {ORACLE_SID}")
print(f"  DSN: {DSN}")

# 5. 연결 테스트
print("\n[5] DB 연결 테스트:")
print("-" * 70)
try:
    from api.db.oracle_client import get_connection
    
    with get_connection() as conn:
        with conn.cursor() as cur:
            # DB 버전 확인
            cur.execute("SELECT * FROM v$version WHERE banner LIKE 'Oracle%'")
            version = cur.fetchone()
            if version:
                print(f"  ✅ 연결 성공!")
                print(f"     DB 버전: {version[0]}")
            
            # 현재 시간 확인
            cur.execute("SELECT SYSDATE FROM DUAL")
            db_time = cur.fetchone()
            if db_time:
                print(f"     DB 시간: {db_time[0]}")
            
            # 테이블 목록 확인
            cur.execute("""
                SELECT table_name 
                FROM user_tables 
                ORDER BY table_name
            """)
            tables = cur.fetchall()
            print(f"     테이블 수: {len(tables)}개")
            
            if tables:
                print("\n     주요 테이블:")
                for i, (table_name,) in enumerate(tables[:10], 1):
                    # 각 테이블의 행 수 확인
                    try:
                        cur.execute(f"SELECT COUNT(*) FROM {table_name}")
                        count = cur.fetchone()[0]
                        print(f"       {i}. {table_name}: {count}개 행")
                    except:
                        print(f"       {i}. {table_name}: (조회 불가)")
            
            # MEMBER 테이블 상세
            try:
                cur.execute("SELECT COUNT(*) FROM MEMBER")
                member_count = cur.fetchone()[0]
                print(f"\n     MEMBER 테이블: {member_count}개 행")
            except Exception as e:
                print(f"\n     MEMBER 테이블: 없음 또는 접근 불가 ({e})")
            
            # PRODUCT 테이블 상세
            try:
                cur.execute("SELECT COUNT(*) FROM PRODUCT")
                product_count = cur.fetchone()[0]
                print(f"     PRODUCT 테이블: {product_count}개 행")
            except Exception as e:
                print(f"     PRODUCT 테이블: 없음 또는 접근 불가 ({e})")
                
except Exception as e:
    print(f"  ❌ 연결 실패: {e}")
    print("\n  가능한 원인:")
    print("    1. Oracle DB 서버가 실행 중이 아닐 수 있습니다.")
    print("    2. 네트워크 연결 문제")
    print("    3. 잘못된 인증 정보")
    print("    4. Oracle Instant Client 미설치 또는 경로 오류")
    sys.exit(1)

print("\n" + "=" * 70)
print("확인 완료!")
print("=" * 70)
