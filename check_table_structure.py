"""ONBOARDING_SESSION 테이블 구조 확인"""
from api.db.oracle_client import get_connection

with get_connection() as conn:
    with conn.cursor() as cur:
        cur.execute("""
            SELECT COLUMN_NAME, DATA_TYPE, DATA_LENGTH, DATA_PRECISION, DATA_SCALE
            FROM USER_TAB_COLUMNS 
            WHERE TABLE_NAME = 'ONBOARDING_SESSION'
            ORDER BY COLUMN_ID
        """)
        print("ONBOARDING_SESSION 테이블 구조:")
        for row in cur.fetchall():
            print(f"  {row[0]}: {row[1]}({row[2]})")

