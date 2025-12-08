#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""TASTE_CONFIG 테이블 확인 스크립트"""

from api.db.oracle_client import get_connection

def main():
    conn = get_connection()
    cur = conn.cursor()
    
    try:
        # 현재 사용자 확인
        cur.execute("SELECT USER FROM DUAL")
        user = cur.fetchone()[0]
        print(f"현재 연결 사용자: {user}\n")
        
        # TASTE_CONFIG 테이블 존재 여부 확인
        cur.execute("""
            SELECT COUNT(*) 
            FROM USER_TABLES 
            WHERE TABLE_NAME = 'TASTE_CONFIG'
        """)
        table_exists = cur.fetchone()[0] > 0
        print(f"TASTE_CONFIG 테이블 존재: {table_exists}")
        
        if table_exists:
            # 레코드 수 확인
            cur.execute("SELECT COUNT(*) FROM TASTE_CONFIG")
            count = cur.fetchone()[0]
            print(f"레코드 수: {count}개\n")
            
            if count > 0:
                # 샘플 데이터 확인
                cur.execute("""
                    SELECT TASTE_ID, REPRESENTATIVE_VIBE, REPRESENTATIVE_HOUSEHOLD_SIZE,
                           REPRESENTATIVE_MAIN_SPACE, REPRESENTATIVE_HAS_PET
                    FROM TASTE_CONFIG 
                    WHERE ROWNUM <= 10
                    ORDER BY TASTE_ID
                """)
                rows = cur.fetchall()
                print("처음 10개 레코드:")
                for row in rows:
                    print(f"  Taste {row[0]}: {row[1]}, {row[2]}인, {row[3]}, 반려동물={'Y' if row[4]=='Y' else 'N'}")
            else:
                print("⚠️ 테이블은 존재하지만 데이터가 없습니다!")
        else:
            print("⚠️ TASTE_CONFIG 테이블이 현재 사용자 스키마에 없습니다!")
            # 다른 스키마에 있는지 확인
            cur.execute("""
                SELECT OWNER, TABLE_NAME 
                FROM ALL_TABLES 
                WHERE TABLE_NAME = 'TASTE_CONFIG'
            """)
            all_tables = cur.fetchall()
            if all_tables:
                print("\n다른 스키마에 있는 TASTE_CONFIG 테이블:")
                for owner, table_name in all_tables:
                    print(f"  {owner}.{table_name}")
            else:
                print("\n⚠️ TASTE_CONFIG 테이블이 어디에도 없습니다!")
                
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    main()

