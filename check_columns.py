"""TASTE_CONFIG 테이블 컬럼 확인"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from api.db.oracle_client import get_connection

try:
    with get_connection() as conn:
        with conn.cursor() as cur:
            # 모든 컬럼 조회
            cur.execute("""
                SELECT column_name, data_type, data_length, nullable
                FROM user_tab_columns 
                WHERE table_name = 'TASTE_CONFIG' 
                ORDER BY column_id
            """)
            columns = cur.fetchall()
            
            print(f"\n=== TASTE_CONFIG 테이블 컬럼 목록 (총 {len(columns)}개) ===\n")
            for col in columns:
                col_name, data_type, data_length, nullable = col
                print(f"{col_name:40s} {data_type:15s} {str(data_length):10s} {'NULL' if nullable == 'Y' else 'NOT NULL'}")
            
            # ILL_SUITED_CATEGORIES 컬럼 확인
            cur.execute("""
                SELECT COUNT(*) 
                FROM user_tab_columns 
                WHERE table_name = 'TASTE_CONFIG' 
                AND column_name = 'ILL_SUITED_CATEGORIES'
            """)
            count = cur.fetchone()[0]
            
            print(f"\n=== ILL_SUITED_CATEGORIES 컬럼 확인 ===")
            if count > 0:
                print("✓ ILL_SUITED_CATEGORIES 컬럼이 존재합니다.")
            else:
                print("✗ ILL_SUITED_CATEGORIES 컬럼이 존재하지 않습니다.")
                print("\n컬럼 추가를 시도합니다...")
                try:
                    cur.execute("ALTER TABLE TASTE_CONFIG ADD ILL_SUITED_CATEGORIES CLOB")
                    conn.commit()
                    print("✓ ILL_SUITED_CATEGORIES 컬럼 추가 완료!")
                except Exception as e:
                    print(f"✗ 컬럼 추가 실패: {str(e)}")
                    
except Exception as e:
    print(f'오류 발생: {str(e)}')
    import traceback
    traceback.print_exc()



