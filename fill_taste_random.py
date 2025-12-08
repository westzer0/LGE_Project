#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
MEMBER 테이블의 TASTE 칼럼을 1~120 범위의 난수로 채우는 스크립트
"""
import sys
import os
from pathlib import Path
import random

# 프로젝트 루트를 Python 경로에 추가
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

# dotenv 없이도 작동하도록 환경변수 직접 설정 (기본값 사용)
try:
    from dotenv import load_dotenv
    load_dotenv(BASE_DIR / ".env")
except ImportError:
    pass

# Oracle 클라이언트 직접 임포트
try:
    import oracledb
except ImportError:
    print("오류: oracledb 모듈이 설치되지 않았습니다.")
    print("다음 명령어로 설치하세요: pip install oracledb")
    sys.exit(1)

# Oracle 연결 정보 (기본값 사용)
ORACLE_USER = os.getenv("ORACLE_USER", "campus_24K_LG3_DX7_p3_4")
ORACLE_PASSWORD = os.getenv("ORACLE_PASSWORD", "smhrd4")
ORACLE_HOST = os.getenv("ORACLE_HOST", "project-db-campus.smhrd.com")
ORACLE_PORT = int(os.getenv("ORACLE_PORT", "1524"))
ORACLE_SID = "xe"

# Thick 모드 초기화 (Oracle 11g는 Thick 모드 필요)
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
    print(f"[Oracle] Thick 모드 초기화 실패: {repr(e)}")
    raise

DSN = oracledb.makedsn(ORACLE_HOST, ORACLE_PORT, sid=ORACLE_SID)

def get_connection():
    """새 Oracle 연결 생성."""
    return oracledb.connect(
        user=ORACLE_USER,
        password=ORACLE_PASSWORD,
        dsn=DSN,
    )


def main():
    print("=" * 60)
    print("MEMBER.TASTE 칼럼을 1~120 난수로 채우기")
    print("=" * 60)
    
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                # 1. 현재 상태 확인
                print("\n[1] 현재 상태 확인...")
                cur.execute("""
                    SELECT 
                        COUNT(*) as total,
                        COUNT(TASTE) as with_taste,
                        COUNT(*) - COUNT(TASTE) as null_count
                    FROM MEMBER
                """)
                result = cur.fetchone()
                total, with_taste, null_count = result
                
                print(f"  - 전체 회원 수: {total}")
                print(f"  - TASTE가 있는 회원: {with_taste}")
                print(f"  - TASTE가 NULL인 회원: {null_count}")
                
                if null_count == 0:
                    print("\n  ✓ 모든 회원의 TASTE 값이 이미 설정되어 있습니다.")
                    return
                
                # 2. TASTE가 NULL인 회원 수 확인
                print(f"\n[2] TASTE가 NULL인 {null_count}명의 회원에 난수 할당...")
                
                # Oracle의 DBMS_RANDOM을 사용하여 업데이트
                cur.execute("""
                    UPDATE MEMBER
                    SET TASTE = TRUNC(DBMS_RANDOM.VALUE(1, 121))
                    WHERE TASTE IS NULL
                """)
                
                updated_count = cur.rowcount
                conn.commit()
                
                print(f"  ✓ {updated_count}명의 회원에 TASTE 값 할당 완료")
                
                # 3. 결과 확인
                print("\n[3] 결과 확인...")
                cur.execute("""
                    SELECT 
                        COUNT(*) as total,
                        COUNT(TASTE) as with_taste,
                        MIN(TASTE) as min_taste,
                        MAX(TASTE) as max_taste,
                        ROUND(AVG(TASTE), 2) as avg_taste
                    FROM MEMBER
                """)
                result = cur.fetchone()
                total, with_taste, min_taste, max_taste, avg_taste = result
                
                print(f"  - 전체 회원 수: {total}")
                print(f"  - TASTE가 있는 회원: {with_taste}")
                print(f"  - 최소 TASTE: {min_taste}")
                print(f"  - 최대 TASTE: {max_taste}")
                print(f"  - 평균 TASTE: {avg_taste}")
                
                if min_taste >= 1 and max_taste <= 120:
                    print("  ✓ 모든 TASTE 값이 1~120 범위 내입니다")
                else:
                    print(f"  ✗ TASTE 값이 범위를 벗어남: {min_taste}~{max_taste}")
                
                # 4. 분포 확인
                print("\n[4] TASTE 값 분포 확인...")
                cur.execute("""
                    SELECT 
                        CASE 
                            WHEN TASTE IS NULL THEN 'NULL'
                            WHEN TASTE < 1 THEN '범위 밖 (< 1)'
                            WHEN TASTE > 120 THEN '범위 밖 (> 120)'
                            ELSE '정상 (1~120)'
                        END as taste_status,
                        COUNT(*) as count
                    FROM MEMBER
                    GROUP BY 
                        CASE 
                            WHEN TASTE IS NULL THEN 'NULL'
                            WHEN TASTE < 1 THEN '범위 밖 (< 1)'
                            WHEN TASTE > 120 THEN '범위 밖 (> 120)'
                            ELSE '정상 (1~120)'
                        END
                    ORDER BY taste_status
                """)
                
                for row in cur:
                    status, count = row
                    print(f"  - {status}: {count}명")
        
        print("\n" + "=" * 60)
        print("TASTE 칼럼 난수 채우기 완료!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n오류 발생: {str(e)}")
        import traceback
        print(traceback.format_exc())
        sys.exit(1)


if __name__ == '__main__':
    main()

