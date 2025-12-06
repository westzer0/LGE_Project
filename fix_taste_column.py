#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
MEMBER 테이블의 TASTE 칼럼을 1~120 범위의 정수로 수정하는 스크립트
"""
import sys
import os
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

# dotenv 없이도 작동하도록 환경변수 직접 설정 (기본값 사용)
# .env 파일이 있으면 로드 시도
try:
    from dotenv import load_dotenv
    load_dotenv(BASE_DIR / ".env")
except ImportError:
    # dotenv가 없어도 기본값으로 작동
    pass

# Oracle 클라이언트 직접 임포트 (dotenv 의존성 제거)
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
# Oracle Instant Client 경로 설정 (config/settings.py와 동일)
ORACLE_INSTANT_CLIENT_PATH = os.getenv(
    "ORACLE_INSTANT_CLIENT_PATH",
    r"C:\oracle\instantclient-basic-windows.x64-21.19.0.0.0dbru\instantclient_21_19"
)

try:
    oracledb.init_oracle_client(lib_dir=ORACLE_INSTANT_CLIENT_PATH)
    print(f"[Oracle] Thick 모드 초기화 완료 (경로: {ORACLE_INSTANT_CLIENT_PATH})")
except oracledb.ProgrammingError:
    # 이미 초기화된 경우 무시
    print("[Oracle] Thick 모드 이미 초기화됨")
except Exception as e:
    print(f"[Oracle] Thick 모드 초기화 실패: {repr(e)}")
    print(f"   경로 확인: {ORACLE_INSTANT_CLIENT_PATH}")
    print("[Oracle] Oracle Instant Client가 설치되어 있는지 확인하세요.")
    print("[Oracle] 또는 ORACLE_INSTANT_CLIENT_PATH 환경변수를 설정하세요.")
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
    print("MEMBER.TASTE 칼럼 수정 시작")
    print("=" * 60)
    
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                # 1. 기존 TASTE 칼럼 삭제 시도
                print("\n[1] 기존 TASTE 칼럼 확인 및 삭제...")
                try:
                    cur.execute("ALTER TABLE MEMBER DROP COLUMN TASTE")
                    conn.commit()
                    print("  ✓ 기존 TASTE 칼럼 삭제 완료")
                except Exception as e:
                    error_code = str(e)
                    if 'ORA-00904' in error_code or '904' in error_code:
                        print("  - TASTE 칼럼이 존재하지 않습니다 (정상)")
                    else:
                        print(f"  - TASTE 칼럼 삭제 중 오류 (무시): {e}")
                
                # 2. TASTE 칼럼 추가 (NUMBER(3))
                print("\n[2] TASTE 칼럼 추가 (NUMBER(3))...")
                try:
                    cur.execute("ALTER TABLE MEMBER ADD (TASTE NUMBER(3))")
                    conn.commit()
                    print("  ✓ TASTE 칼럼 추가 완료")
                except Exception as e:
                    error_code = str(e)
                    if 'ORA-01430' in error_code or '1430' in error_code:
                        print("  - TASTE 칼럼이 이미 존재합니다")
                    else:
                        raise
                
                # 3. 기존 제약조건 삭제 시도
                print("\n[3] 기존 TASTE 제약조건 확인 및 삭제...")
                try:
                    cur.execute("ALTER TABLE MEMBER DROP CONSTRAINT CHK_TASTE_RANGE")
                    conn.commit()
                    print("  ✓ 기존 제약조건 삭제 완료")
                except Exception as e:
                    error_code = str(e)
                    if 'ORA-02443' in error_code or '2443' in error_code:
                        print("  - 제약조건이 존재하지 않습니다 (정상)")
                    else:
                        print(f"  - 제약조건 삭제 중 오류 (무시): {e}")
                
                # 4. CHECK 제약조건 추가 (1~120 범위)
                print("\n[4] TASTE 범위 제약조건 추가 (1~120)...")
                try:
                    cur.execute("""
                        ALTER TABLE MEMBER 
                        ADD CONSTRAINT CHK_TASTE_RANGE 
                        CHECK (TASTE IS NULL OR (TASTE >= 1 AND TASTE <= 120))
                    """)
                    conn.commit()
                    print("  ✓ TASTE 범위 제약조건 추가 완료 (1~120)")
                except Exception as e:
                    error_code = str(e)
                    if 'ORA-02264' in error_code or '2264' in error_code:
                        print("  - 제약조건이 이미 존재합니다")
                    else:
                        raise
                
                # 5. 기존 잘못된 데이터 정리
                print("\n[5] 기존 잘못된 TASTE 값 정리...")
                try:
                    # 범위를 벗어난 값 확인
                    cur.execute("""
                        SELECT COUNT(*) 
                        FROM MEMBER 
                        WHERE TASTE IS NOT NULL AND (TASTE < 1 OR TASTE > 120)
                    """)
                    invalid_count = cur.fetchone()[0]
                    
                    if invalid_count > 0:
                        print(f"  - 잘못된 TASTE 값 {invalid_count}개 발견")
                        # 범위를 벗어난 값을 NULL로 설정
                        cur.execute("""
                            UPDATE MEMBER 
                            SET TASTE = NULL 
                            WHERE TASTE IS NOT NULL AND (TASTE < 1 OR TASTE > 120)
                        """)
                        conn.commit()
                        print(f"  ✓ {invalid_count}개 값 정리 완료 (NULL로 설정)")
                    else:
                        print("  ✓ 잘못된 값 없음")
                except Exception as e:
                    print(f"  - 데이터 정리 중 오류 (무시): {e}")
                
                # 6. 최종 확인
                print("\n[6] 최종 확인...")
                cur.execute("""
                    SELECT 
                        COUNT(*) as total,
                        COUNT(TASTE) as with_taste,
                        MIN(TASTE) as min_taste,
                        MAX(TASTE) as max_taste
                    FROM MEMBER
                """)
                result = cur.fetchone()
                total, with_taste, min_taste, max_taste = result
                
                print(f"  - 전체 회원 수: {total}")
                print(f"  - TASTE가 있는 회원: {with_taste}")
                if min_taste is not None:
                    print(f"  - 최소 TASTE: {min_taste}")
                    print(f"  - 최대 TASTE: {max_taste}")
                    if min_taste >= 1 and max_taste <= 120:
                        print("  ✓ 모든 TASTE 값이 1~120 범위 내입니다")
                    else:
                        print(f"  ✗ TASTE 값이 범위를 벗어남: {min_taste}~{max_taste}")
                else:
                    print("  - TASTE 값이 없습니다")
        
        print("\n" + "=" * 60)
        print("MEMBER.TASTE 칼럼 수정 완료!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n오류 발생: {str(e)}")
        import traceback
        print(traceback.format_exc())
        sys.exit(1)


if __name__ == '__main__':
    main()

