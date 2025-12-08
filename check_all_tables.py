#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Oracle DB의 모든 테이블 확인
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

def check_all_tables():
    """모든 테이블 목록 확인"""
    print("=" * 80)
    print("Oracle DB 테이블 목록")
    print("=" * 80)
    
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                # 모든 테이블 목록
                cur.execute("""
                    SELECT TABLE_NAME 
                    FROM USER_TABLES 
                    ORDER BY TABLE_NAME
                """)
                
                tables = cur.fetchall()
                
                print(f"\n총 {len(tables)}개 테이블:")
                print("-" * 80)
                for table in tables:
                    print(f"  - {table[0]}")
                
                # ONBOARDING 관련 테이블 상세 확인
                print("\n" + "=" * 80)
                print("ONBOARDING 관련 테이블 상세")
                print("=" * 80)
                
                for table in tables:
                    table_name = table[0]
                    if 'ONBOARDING' in table_name.upper() or 'SESSION' in table_name.upper():
                        print(f"\n[{table_name}]")
                        print("-" * 80)
                        
                        cur.execute(f"""
                            SELECT 
                                COLUMN_NAME,
                                DATA_TYPE,
                                DATA_LENGTH,
                                DATA_PRECISION,
                                DATA_SCALE,
                                NULLABLE
                            FROM USER_TAB_COLUMNS
                            WHERE TABLE_NAME = '{table_name}'
                            ORDER BY COLUMN_ID
                        """)
                        
                        columns = cur.fetchall()
                        for col in columns:
                            col_name, data_type, data_length, data_precision, data_scale, nullable = col
                            type_info = f"{data_type}"
                            if data_precision:
                                type_info += f"({data_precision}"
                                if data_scale:
                                    type_info += f",{data_scale}"
                                type_info += ")"
                            elif data_length:
                                type_info += f"({data_length})"
                            
                            print(f"  {col_name:30s} {type_info:20s} NULLABLE={nullable}")
                
    except Exception as e:
        print(f"오류 발생: {str(e)}")
        import traceback
        print(traceback.format_exc())

if __name__ == '__main__':
    check_all_tables()




