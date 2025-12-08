#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
ONBOARDING_SESSION 테이블에 필요한 컬럼 추가
"""

import os
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

import django
django.setup()

from api.db.oracle_client import get_connection

def alter_table():
    """ONBOARDING_SESSION 테이블에 컬럼 추가"""
    print("=" * 80)
    print("ONBOARDING_SESSION 테이블 ALTER")
    print("=" * 80)
    
    alter_statements = [
        # Step 1: Vibe
        "ALTER TABLE ONBOARDING_SESSION ADD VIBE VARCHAR2(20)",
        
        # Step 2: Household
        "ALTER TABLE ONBOARDING_SESSION ADD HOUSEHOLD_SIZE NUMBER",
        "ALTER TABLE ONBOARDING_SESSION ADD HAS_PET CHAR(1)",
        
        # Step 3: Space
        "ALTER TABLE ONBOARDING_SESSION ADD HOUSING_TYPE VARCHAR2(20)",
        "ALTER TABLE ONBOARDING_SESSION ADD PYUNG NUMBER",
        "ALTER TABLE ONBOARDING_SESSION ADD MAIN_SPACE CLOB",
        
        # Step 4: Lifestyle
        "ALTER TABLE ONBOARDING_SESSION ADD COOKING VARCHAR2(20)",
        "ALTER TABLE ONBOARDING_SESSION ADD LAUNDRY VARCHAR2(20)",
        "ALTER TABLE ONBOARDING_SESSION ADD MEDIA VARCHAR2(20)",
        
        # Step 5: Priority
        "ALTER TABLE ONBOARDING_SESSION ADD PRIORITY VARCHAR2(20)",
        "ALTER TABLE ONBOARDING_SESSION ADD PRIORITY_LIST CLOB",
        
        # Step 6: Budget
        "ALTER TABLE ONBOARDING_SESSION ADD BUDGET_LEVEL VARCHAR2(20)",
        
        # 기타
        "ALTER TABLE ONBOARDING_SESSION ADD SELECTED_CATEGORIES CLOB",
        "ALTER TABLE ONBOARDING_SESSION ADD RECOMMENDED_PRODUCTS CLOB",
        "ALTER TABLE ONBOARDING_SESSION ADD RECOMMENDATION_RESULT CLOB",
        "ALTER TABLE ONBOARDING_SESSION ADD CURRENT_STEP NUMBER DEFAULT 1",
        "ALTER TABLE ONBOARDING_SESSION ADD STATUS VARCHAR2(20) DEFAULT 'IN_PROGRESS'",
        "ALTER TABLE ONBOARDING_SESSION ADD COMPLETED_AT DATE",
        "ALTER TABLE ONBOARDING_SESSION ADD USER_ID VARCHAR2(100)",
    ]
    
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                for idx, sql in enumerate(alter_statements, 1):
                    try:
                        print(f"[{idx}/{len(alter_statements)}] 실행 중: {sql[:60]}...")
                        cur.execute(sql)
                        print(f"  [OK] 성공")
                    except Exception as e:
                        error_msg = str(e)
                        if 'ORA-01442' in error_msg or 'already exists' in error_msg.lower():
                            print(f"  [SKIP] 컬럼이 이미 존재합니다")
                        else:
                            print(f"  [ERROR] {error_msg}")
                
                conn.commit()
                print("\n" + "=" * 80)
                print("ALTER 완료!")
                print("=" * 80)
                
    except Exception as e:
        print(f"\n오류 발생: {str(e)}")
        import traceback
        print(traceback.format_exc())

if __name__ == '__main__':
    alter_table()




