#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Oracle Thick 모드 연결 테스트
DB 버전이 낮아서 Thin 모드가 지원되지 않는 경우 (DPY-3010)
"""
import oracledb
import os
from dotenv import load_dotenv
from pathlib import Path
import traceback

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

user = os.getenv("ORACLE_USER", "campus_24K_LG3_DX7_p3_4")
password = os.getenv("ORACLE_PASSWORD", "smhrd4")
host = os.getenv("ORACLE_HOST", "project-db-campus.smhrd.com")
port = int(os.getenv("ORACLE_PORT", "1524"))
sid = "xe"

# Oracle Instant Client 경로 설정
# 실제 설치 경로로 변경하세요
# 예: r"C:\oracle\instantclient_19_23" 또는 r"C:\oracle\instantclient_21_8"
instant_client_path = os.getenv("ORACLE_INSTANT_CLIENT_PATH")

if instant_client_path:
    print(f"Oracle Instant Client 경로: {instant_client_path}")
    try:
        oracledb.init_oracle_client(lib_dir=instant_client_path)
        print("✅ Thick 모드 활성화 성공!")
    except Exception as e:
        print(f"❌ Thick 모드 활성화 실패: {e}")
        print("\n확인 사항:")
        print("  1. Oracle Instant Client가 설치되어 있는지 확인")
        print("  2. ORACLE_INSTANT_CLIENT_PATH 환경 변수나 .env 파일에 경로가 올바른지 확인")
        print("  3. 경로에 oci.dll 파일이 있는지 확인")
        exit(1)
else:
    print("="*60)
    print("⚠️  Oracle Instant Client 경로가 설정되지 않았습니다!")
    print("="*60)
    print("\nThick 모드를 사용하려면 Oracle Instant Client가 필요합니다.")
    print("\n설정 방법:")
    print("  1. .env 파일에 다음 추가:")
    print("     ORACLE_INSTANT_CLIENT_PATH=C:\\oracle\\instantclient_19_23")
    print("\n  2. 또는 이 스크립트에서 직접 경로 지정:")
    print("     instant_client_path = r'C:\\oracle\\instantclient_19_23'")
    print("\n  3. 또는 시스템 PATH에 Instant Client 경로 추가")
    print("="*60)
    
    # 자동으로 PATH에서 찾기 시도
    print("\n시스템 PATH에서 Oracle Instant Client 찾기 시도...")
    import sys
    path_dirs = os.environ.get("PATH", "").split(os.pathsep)
    found_clients = []
    for path_dir in path_dirs:
        oci_dll = os.path.join(path_dir, "oci.dll")
        if os.path.exists(oci_dll):
            found_clients.append(path_dir)
    
    if found_clients:
        print(f"✅ PATH에서 Oracle Instant Client 발견: {found_clients[0]}")
        try:
            oracledb.init_oracle_client(lib_dir=found_clients[0])
            print("✅ Thick 모드 활성화 성공!")
        except Exception as e:
            print(f"❌ Thick 모드 활성화 실패: {e}")
            exit(1)
    else:
        print("❌ PATH에서 Oracle Instant Client를 찾을 수 없습니다.")
        print("\n다음 중 하나를 실행하세요:")
        print("  1. Oracle Instant Client 설치")
        print("  2. .env 파일에 ORACLE_INSTANT_CLIENT_PATH 설정")
        exit(1)

# SID 기반 DSN 생성
dsn = oracledb.makedsn(host=host, port=port, sid=sid)

print("\n" + "="*60)
print("연결 설정:")
print("="*60)
print(f"  USER: {user}")
print(f"  DSN:  {dsn}")
print(f"  Host: {host}")
print(f"  Port: {port}")
print(f"  SID:  {sid}")
print()

try:
    conn = oracledb.connect(user=user, password=password, dsn=dsn)
    print("✅ Thick 모드로 연결 성공!")
    
    # 커서 테스트
    with conn.cursor() as cur:
        cur.execute("SELECT user FROM dual")
        row = cur.fetchone()
        print(f"현재 사용자: {row[0]}")
        
        # 추가 정보 확인
        cur.execute("SELECT USER, SYSDATE, 'Thick 모드 연결 성공!' FROM DUAL")
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
    print("❌ Thick 모드 연결 또는 커서 테스트 실패!")
    print("\n" + "="*60)
    print("상세 에러 정보")
    print("="*60)
    print(f"repr(e): {repr(e)}")
    print(f"str(e): {str(e)}")
    print(f"type(e).__name__: {type(e).__name__}")
    
    # ORA 에러 코드 추출
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



