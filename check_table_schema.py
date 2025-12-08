#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Oracle DB 테이블 스키마 확인
"""

import os
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

import django
django.setup()

from api.db.oracle_client import get_connection, fetch_all_dict

def check_schema():
    """ONBOARDING_SESSION 테이블 스키마 확인"""
    print("=" * 80)
    print("ONBOARDING_SESSION 테이블 스키마 확인")
    print("=" * 80)
    
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                # 테이블 컬럼 정보 조회
                cur.execute("""
                    SELECT 
                        COLUMN_NAME,
                        DATA_TYPE,
                        DATA_LENGTH,
                        DATA_PRECISION,
                        DATA_SCALE,
                        NULLABLE,
                        DATA_DEFAULT
                    FROM USER_TAB_COLUMNS
                    WHERE TABLE_NAME = 'ONBOARDING_SESSION'
                    ORDER BY COLUMN_ID
                """)
                
                columns = cur.fetchall()
                
                print("\n컬럼 정보:")
                print("-" * 80)
                for col in columns:
                    col_name, data_type, data_length, data_precision, data_scale, nullable, data_default = col
                    print(f"  {col_name:30s} {data_type:15s} "
                          f"LENGTH={data_length or 'N/A':>5} "
                          f"PRECISION={data_precision or 'N/A':>5} "
                          f"SCALE={data_scale or 'N/A':>5} "
                          f"NULLABLE={nullable}")
                
                # NUMBER 타입 컬럼만 별도 확인
                print("\nNUMBER 타입 컬럼:")
                print("-" * 80)
                for col in columns:
                    col_name, data_type, data_length, data_precision, data_scale, nullable, data_default = col
                    if data_type == 'NUMBER':
                        print(f"  {col_name}: NUMBER({data_precision or 'N/A'},{data_scale or 'N/A'})")
                
    except Exception as e:
        print(f"오류 발생: {str(e)}")
        import traceback
        print(traceback.format_exc())

if __name__ == '__main__':
    check_schema()




