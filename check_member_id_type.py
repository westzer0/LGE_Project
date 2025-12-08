#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
MEMBER 테이블의 MEMBER_ID 컬럼 타입 확인
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

def check_member_id_type():
    """MEMBER_ID 컬럼 타입 확인"""
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT 
                        COLUMN_NAME,
                        DATA_TYPE,
                        DATA_LENGTH,
                        DATA_PRECISION,
                        DATA_SCALE,
                        NULLABLE
                    FROM USER_TAB_COLUMNS
                    WHERE TABLE_NAME = 'MEMBER'
                    ORDER BY COLUMN_ID
                """)
                
                print("=" * 80)
                print("MEMBER 테이블 스키마")
                print("=" * 80)
                print(f"{'컬럼명':<20} {'타입':<15} {'길이':<10} {'정밀도':<10} {'스케일':<10} {'NULL':<10}")
                print("-" * 80)
                
                for row in cur.fetchall():
                    col_name, data_type, data_length, data_precision, data_scale, nullable = row
                    precision_str = str(data_precision) if data_precision else ''
                    scale_str = str(data_scale) if data_scale else ''
                    length_str = str(data_length) if data_length else ''
                    
                    print(f"{col_name:<20} {data_type:<15} {length_str:<10} {precision_str:<10} {scale_str:<10} {nullable:<10}")
                    
                    if col_name == 'MEMBER_ID':
                        print(f"\n[중요] MEMBER_ID 타입: {data_type}")
                        if data_type == 'NUMBER':
                            print("  → NUMBER 타입이므로 숫자만 사용 가능합니다.")
                        else:
                            print("  → VARCHAR2 타입이므로 문자열 사용 가능합니다.")
                
    except Exception as e:
        print(f"오류 발생: {str(e)}")
        import traceback
        print(traceback.format_exc())

if __name__ == '__main__':
    check_member_id_type()

