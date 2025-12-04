#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
테이블 구조 확인
"""
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

from api.db.oracle_client import get_connection, fetch_all_dict


def check_structure():
    """테이블 구조 확인"""
    print("=" * 60)
    print("테이블 구조 확인")
    print("=" * 60)
    
    try:
        conn = get_connection()
        print("\n[1] Oracle DB 연결 성공!")
        
        # ONBOARDING_QUESTION 테이블 구조 확인
        print("\n[2] ONBOARDING_QUESTION 테이블 구조:")
        with conn.cursor() as cur:
            cur.execute("""
                SELECT COLUMN_NAME, DATA_TYPE, DATA_LENGTH, NULLABLE
                FROM USER_TAB_COLUMNS
                WHERE TABLE_NAME = 'ONBOARDING_QUESTION'
                ORDER BY COLUMN_ID
            """)
            cols = cur.fetchall()
            for col in cols:
                print(f"  - {col[0]}: {col[1]}({col[2] if col[2] else 'N/A'}) - {'NULL' if col[3] == 'Y' else 'NOT NULL'}")
        
        # ONBOARDING_SESSION 테이블 구조 확인
        print("\n[3] ONBOARDING_SESSION 테이블 구조:")
        with conn.cursor() as cur:
            cur.execute("""
                SELECT COLUMN_NAME, DATA_TYPE, DATA_LENGTH, NULLABLE
                FROM USER_TAB_COLUMNS
                WHERE TABLE_NAME = 'ONBOARDING_SESSION'
                ORDER BY COLUMN_ID
            """)
            cols = cur.fetchall()
            for col in cols:
                print(f"  - {col[0]}: {col[1]}({col[2] if col[2] else 'N/A'}) - {'NULL' if col[3] == 'Y' else 'NOT NULL'}")
        
        # 현재 질문 개수
        print("\n[4] 현재 질문 개수:")
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM ONBOARDING_QUESTION")
            count = cur.fetchone()[0]
            print(f"  - {count}개")
            
            if count > 0:
                questions = fetch_all_dict("""
                    SELECT * FROM ONBOARDING_QUESTION ORDER BY QUESTION_ID
                """)
                print("\n[5] 현재 질문 목록:")
                for q in questions:
                    print(f"  - ID: {q.get('QUESTION_ID')}, Step: {q.get('STEP_NUMBER', 'N/A')}, Type: {q.get('QUESTION_TYPE', 'N/A')}")
        
        conn.close()
        
    except Exception as e:
        print(f"\n✗ 오류 발생: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    check_structure()

