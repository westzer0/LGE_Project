"""
로봇청소기_SCORE 컬럼 삭제 스크립트
"""
from api.db.oracle_client import get_connection

def delete_robot_vacuum_column():
    """로봇청소기_SCORE 컬럼 삭제"""
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                # 컬럼 존재 확인
                cur.execute("""
                    SELECT COLUMN_NAME 
                    FROM USER_TAB_COLUMNS 
                    WHERE TABLE_NAME = 'TASTE_CONFIG' 
                      AND COLUMN_NAME LIKE '%로봇%'
                """)
                columns = cur.fetchall()
                
                if columns:
                    print(f"발견된 로봇청소기 관련 컬럼: {[col[0] for col in columns]}")
                    
                    # 로봇청소기_SCORE 컬럼 삭제
                    column_name = '"로봇청소기_SCORE"'
                    print(f"\n{column_name} 컬럼 삭제 중...")
                    
                    try:
                        cur.execute(f'ALTER TABLE TASTE_CONFIG DROP COLUMN {column_name}')
                        conn.commit()
                        print(f"✓ {column_name} 컬럼 삭제 완료")
                    except Exception as e:
                        error_str = str(e).upper()
                        if 'ORA-01430' in error_str or 'DOES NOT EXIST' in error_str or 'NOT FOUND' in error_str:
                            print(f"⚠ {column_name} 컬럼이 이미 존재하지 않습니다.")
                        else:
                            print(f"✗ 오류 발생: {str(e)}")
                            raise
                else:
                    print("로봇청소기 관련 컬럼을 찾을 수 없습니다.")
                    
    except Exception as e:
        print(f"오류 발생: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    print("=== 로봇청소기_SCORE 컬럼 삭제 ===\n")
    delete_robot_vacuum_column()
    print("\n=== 완료 ===")

