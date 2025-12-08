"""ILL_SUITED_CATEGORIES 컬럼 강제 추가"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from api.db.oracle_client import get_connection

try:
    with get_connection() as conn:
        with conn.cursor() as cur:
            # 먼저 컬럼이 존재하는지 확인
            cur.execute("""
                SELECT COUNT(*) 
                FROM user_tab_columns 
                WHERE table_name = 'TASTE_CONFIG' 
                AND UPPER(column_name) = 'ILL_SUITED_CATEGORIES'
            """)
            exists = cur.fetchone()[0] > 0
            
            print(f"\n=== ILL_SUITED_CATEGORIES 컬럼 상태 확인 ===")
            print(f"현재 존재 여부: {'존재함' if exists else '존재하지 않음'}")
            
            if not exists:
                print("\n컬럼을 추가합니다...")
                cur.execute("ALTER TABLE TASTE_CONFIG ADD ILL_SUITED_CATEGORIES CLOB")
                conn.commit()
                print("✓ ILL_SUITED_CATEGORIES 컬럼 추가 완료!")
            else:
                print("\n컬럼이 이미 존재합니다.")
                # 주석 추가
                try:
                    cur.execute("""
                        COMMENT ON COLUMN TASTE_CONFIG.ILL_SUITED_CATEGORIES IS 
                        '온보딩 답변과 완전히 부적합한 카테고리 리스트 (JSON 배열)'
                    """)
                    conn.commit()
                    print("✓ 컬럼 주석 추가 완료!")
                except Exception as e:
                    print(f"주석 추가 실패 (무시): {str(e)}")
            
            # 최종 확인
            cur.execute("""
                SELECT column_name, data_type, data_length, nullable
                FROM user_tab_columns 
                WHERE table_name = 'TASTE_CONFIG' 
                AND UPPER(column_name) = 'ILL_SUITED_CATEGORIES'
            """)
            result = cur.fetchone()
            
            if result:
                col_name, data_type, data_length, nullable = result
                print(f"\n=== 최종 확인 ===")
                print(f"컬럼명: {col_name}")
                print(f"데이터 타입: {data_type}")
                print(f"길이: {data_length}")
                print(f"NULL 허용: {nullable}")
                print("\n✓ ILL_SUITED_CATEGORIES 컬럼이 정상적으로 존재합니다!")
            else:
                print("\n✗ 컬럼을 찾을 수 없습니다.")
                
except Exception as e:
    print(f'오류 발생: {str(e)}')
    import traceback
    traceback.print_exc()



