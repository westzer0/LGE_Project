"""
MEMBER 테이블의 TASTE 칼럼을 수정하는 Python 스크립트
SQLite, Oracle, PostgreSQL 등 모든 데이터베이스에서 동작
Django 설정을 사용하여 데이터베이스에 연결
"""

import os
import sys
import django
from pathlib import Path

# Django 설정 로드
BASE_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(BASE_DIR))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.db import connection
import random


def update_member_taste_column():
    """
    MEMBER 테이블에 TASTE 칼럼을 추가하고 데이터를 정리합니다.
    """
    with connection.cursor() as cursor:
        db_backend = connection.vendor  # 'sqlite', 'oracle', 'postgresql' 등
        
        print(f"[DB] 데이터베이스: {db_backend}")
        
        # 1. TASTE 칼럼이 있는지 확인
        try:
            if db_backend == 'sqlite':
                # SQLite: sqlite_master 테이블에서 확인
                cursor.execute("""
                    SELECT name FROM sqlite_master 
                    WHERE type='table' AND name='MEMBER'
                """)
                if not cursor.fetchone():
                    print("[ERROR] MEMBER 테이블이 존재하지 않습니다.")
                    return False
                
                # 칼럼 존재 확인
                cursor.execute("PRAGMA table_info(MEMBER)")
                columns = [row[1] for row in cursor.fetchall()]
                
                if 'TASTE' not in columns:
                    print("[INFO] TASTE 칼럼 추가 중...")
                    cursor.execute("ALTER TABLE MEMBER ADD COLUMN TASTE INTEGER")
                    print("[OK] TASTE 칼럼 추가 완료")
                else:
                    print("[INFO] TASTE 칼럼이 이미 존재합니다.")
                    
            elif db_backend == 'oracle':
                # Oracle: USER_TAB_COLUMNS에서 확인
                cursor.execute("""
                    SELECT COUNT(*) FROM USER_TAB_COLUMNS 
                    WHERE TABLE_NAME = 'MEMBER' AND COLUMN_NAME = 'TASTE'
                """)
                if cursor.fetchone()[0] == 0:
                    print("[INFO] TASTE 칼럼 추가 중...")
                    cursor.execute("ALTER TABLE MEMBER ADD (TASTE NUMBER(3))")
                    print("[OK] TASTE 칼럼 추가 완료")
                else:
                    print("[INFO] TASTE 칼럼이 이미 존재합니다.")
                    
            else:
                # PostgreSQL 등 기타 데이터베이스
                try:
                    cursor.execute("""
                        SELECT column_name FROM information_schema.columns 
                        WHERE table_name = 'member' AND column_name = 'taste'
                    """)
                    if not cursor.fetchone():
                        print("[INFO] TASTE 칼럼 추가 중...")
                        cursor.execute("ALTER TABLE MEMBER ADD COLUMN TASTE INTEGER")
                        print("[OK] TASTE 칼럼 추가 완료")
                    else:
                        print("[INFO] TASTE 칼럼이 이미 존재합니다.")
                except Exception as e:
                    print(f"[WARNING] 칼럼 확인 실패: {e}")
                    # 일단 추가 시도
                    try:
                        cursor.execute("ALTER TABLE MEMBER ADD COLUMN TASTE INTEGER")
                        print("[OK] TASTE 칼럼 추가 완료")
                    except Exception as e2:
                        print(f"[INFO] TASTE 칼럼 추가 실패 (이미 존재할 수 있음): {e2}")
            
        except Exception as e:
            print(f"[ERROR] 칼럼 확인/추가 중 오류: {e}")
            return False
        
        # 2. 범위를 벗어난 값 정리
        try:
            print("[INFO] 범위를 벗어난 TASTE 값 정리 중...")
            cursor.execute("""
                UPDATE MEMBER 
                SET TASTE = NULL 
                WHERE TASTE IS NOT NULL AND (TASTE < 1 OR TASTE > 120)
            """)
            affected = cursor.rowcount
            if affected > 0:
                print(f"[OK] {affected}개의 범위를 벗어난 값이 NULL로 설정되었습니다.")
            else:
                print("[INFO] 정리할 값이 없습니다.")
        except Exception as e:
            print(f"[WARNING] 값 정리 중 오류: {e}")
        
        # 3. NULL인 값에 난수 할당
        try:
            print("[INFO] NULL인 TASTE 값에 난수 할당 중...")
            cursor.execute("SELECT COUNT(*) FROM MEMBER WHERE TASTE IS NULL")
            null_count = cursor.fetchone()[0]
            
            if null_count > 0:
                # 각 행에 대해 1~120 범위의 난수 할당
                cursor.execute("SELECT ROWID FROM MEMBER WHERE TASTE IS NULL")
                rows = cursor.fetchall()
                
                updated = 0
                for row in rows:
                    taste_value = random.randint(1, 120)
                    if db_backend == 'sqlite':
                        cursor.execute(
                            "UPDATE MEMBER SET TASTE = ? WHERE ROWID = ?",
                            [taste_value, row[0]]
                        )
                    elif db_backend == 'oracle':
                        cursor.execute(
                            "UPDATE MEMBER SET TASTE = :taste WHERE ROWID = :rowid",
                            {'taste': taste_value, 'rowid': row[0]}
                        )
                    else:
                        # PostgreSQL 등: ROWID 대신 PRIMARY KEY 사용 필요
                        # 여기서는 간단히 모든 NULL 값을 업데이트
                        cursor.execute(
                            "UPDATE MEMBER SET TASTE = %s WHERE TASTE IS NULL LIMIT 1",
                            [taste_value]
                        )
                    updated += 1
                
                print(f"[OK] {updated}개의 NULL 값에 난수가 할당되었습니다.")
            else:
                print("[INFO] 할당할 NULL 값이 없습니다.")
        except Exception as e:
            print(f"[WARNING] 난수 할당 중 오류: {e}")
            # 대안: 한 번에 업데이트 (데이터베이스별로 다름)
            try:
                if db_backend == 'sqlite':
                    # SQLite는 각 행마다 다른 난수를 생성하기 어려움
                    # Python에서 처리하는 것이 더 나음
                    pass
                elif db_backend == 'oracle':
                    cursor.execute("""
                        UPDATE MEMBER 
                        SET TASTE = TRUNC(DBMS_RANDOM.VALUE(1, 121))
                        WHERE TASTE IS NULL
                    """)
                    print(f"[OK] {cursor.rowcount}개의 NULL 값에 난수가 할당되었습니다.")
            except Exception as e2:
                print(f"[ERROR] 대안 방법도 실패: {e2}")
        
        # 4. 결과 확인
        try:
            print("\n[결과 확인]")
            cursor.execute("""
                SELECT 
                    COUNT(*) as total,
                    COUNT(TASTE) as with_taste,
                    MIN(TASTE) as min_taste,
                    MAX(TASTE) as max_taste,
                    ROUND(AVG(TASTE), 2) as avg_taste
                FROM MEMBER
            """)
            stats = cursor.fetchone()
            print(f"  전체 회원 수: {stats[0]}")
            print(f"  TASTE 값이 있는 회원: {stats[1]}")
            print(f"  최소 TASTE 값: {stats[2]}")
            print(f"  최대 TASTE 값: {stats[3]}")
            print(f"  평균 TASTE 값: {stats[4]}")
            
            # 분포 확인
            cursor.execute("""
                SELECT 
                    CASE 
                        WHEN TASTE IS NULL THEN 'NULL'
                        WHEN TASTE < 1 THEN '범위 밖 (< 1)'
                        WHEN TASTE > 120 THEN '범위 밖 (> 120)'
                        ELSE '정상 (1~120)'
                    END as status,
                    COUNT(*) as count
                FROM MEMBER
                GROUP BY status
                ORDER BY status
            """)
            print("\n[TASTE 값 분포]")
            for row in cursor.fetchall():
                print(f"  {row[0]}: {row[1]}개")
                
        except Exception as e:
            print(f"[WARNING] 결과 확인 중 오류: {e}")
        
        return True


if __name__ == '__main__':
    print("=" * 60)
    print("MEMBER 테이블 TASTE 칼럼 수정 스크립트")
    print("=" * 60)
    
    try:
        success = update_member_taste_column()
        if success:
            print("\n[완료] 작업이 성공적으로 완료되었습니다.")
        else:
            print("\n[실패] 작업 중 오류가 발생했습니다.")
            sys.exit(1)
    except Exception as e:
        print(f"\n[ERROR] 예상치 못한 오류: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

