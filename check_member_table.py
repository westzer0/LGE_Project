#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
MEMBER 테이블 현황 확인
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

def check_member_table():
    """MEMBER 테이블 현황 확인"""
    print("=" * 80)
    print("MEMBER 테이블 현황")
    print("=" * 80)
    
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                # 1. 전체 레코드 수
                cur.execute("SELECT COUNT(*) FROM MEMBER")
                total_count = cur.fetchone()[0]
                print(f"\n[전체 레코드 수] {total_count}개")
                
                # 2. 테이블 스키마 확인
                print("\n[테이블 스키마]")
                print("-" * 80)
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
                
                columns = cur.fetchall()
                for col in columns:
                    col_name, data_type, data_length, data_precision, data_scale, nullable = col
                    type_info = f"{data_type}"
                    if data_precision:
                        if data_scale:
                            type_info += f"({data_precision},{data_scale})"
                        else:
                            type_info += f"({data_precision})"
                    elif data_length:
                        type_info += f"({data_length})"
                    print(f"  {col_name:30s} {type_info:20s} NULLABLE={nullable:5s}")
                
                # 3. 샘플 데이터 조회 (최대 10개)
                if total_count > 0:
                    print(f"\n[샘플 데이터 (최대 10개)]")
                    print("-" * 80)
                    cur.execute("""
                        SELECT 
                            MEMBER_ID,
                            NAME,
                            AGE,
                            GENDER,
                            CONTACT,
                            POINT,
                            CREATED_DATE,
                            TASTE
                        FROM MEMBER
                        WHERE ROWNUM <= 10
                        ORDER BY CREATED_DATE DESC
                    """)
                    
                    rows = cur.fetchall()
                    for idx, row in enumerate(rows, 1):
                        member_id, name, age, gender, contact, point, created_date, taste = row
                        print(f"\n[레코드 {idx}]")
                        print(f"  MEMBER_ID: {member_id}")
                        print(f"  NAME: {name}")
                        print(f"  AGE: {age} (타입: {type(age).__name__})")
                        print(f"  GENDER: {gender}")
                        print(f"  CONTACT: {contact}")
                        print(f"  POINT: {point} (타입: {type(point).__name__})")
                        print(f"  CREATED_DATE: {created_date}")
                        print(f"  TASTE: {taste} (타입: {type(taste).__name__})")
                    
                    # 4. 통계 정보
                    print(f"\n[통계 정보]")
                    print("-" * 80)
                    
                    # AGE 통계
                    cur.execute("""
                        SELECT 
                            MIN(AGE) as min_age,
                            MAX(AGE) as max_age,
                            AVG(AGE) as avg_age,
                            COUNT(*) as count
                        FROM MEMBER
                        WHERE AGE IS NOT NULL
                    """)
                    age_stats = cur.fetchone()
                    if age_stats and age_stats[3] > 0:
                        print(f"AGE: 최소={age_stats[0]}, 최대={age_stats[1]}, 평균={age_stats[2]:.2f}, 개수={age_stats[3]}")
                    
                    # POINT 통계
                    cur.execute("""
                        SELECT 
                            MIN(POINT) as min_point,
                            MAX(POINT) as max_point,
                            AVG(POINT) as avg_point,
                            COUNT(*) as count
                        FROM MEMBER
                        WHERE POINT IS NOT NULL
                    """)
                    point_stats = cur.fetchone()
                    if point_stats and point_stats[3] > 0:
                        print(f"POINT: 최소={point_stats[0]}, 최대={point_stats[1]}, 평균={point_stats[2]:.2f}, 개수={point_stats[3]}")
                    
                    # TASTE 타입 확인
                    cur.execute("""
                        SELECT 
                            COUNT(*) as total,
                            COUNT(TASTE) as not_null_count,
                            COUNT(CASE WHEN TASTE IS NULL THEN 1 END) as null_count
                        FROM MEMBER
                    """)
                    taste_stats = cur.fetchone()
                    if taste_stats:
                        print(f"TASTE: 전체={taste_stats[0]}, NULL이 아닌 값={taste_stats[1]}, NULL={taste_stats[2]}")
                        
                        # TASTE 값 샘플 (NULL이 아닌 경우)
                        if taste_stats[1] > 0:
                            cur.execute("""
                                SELECT DISTINCT TASTE
                                FROM MEMBER
                                WHERE TASTE IS NOT NULL
                                AND ROWNUM <= 5
                            """)
                            taste_samples = cur.fetchall()
                            print(f"  TASTE 샘플 값:")
                            for sample in taste_samples:
                                taste_val = sample[0]
                                print(f"    - {taste_val} (타입: {type(taste_val).__name__})")
                else:
                    print("\n[데이터 없음] MEMBER 테이블에 레코드가 없습니다.")
                
    except Exception as e:
        print(f"\n[오류 발생] {str(e)}")
        import traceback
        print(traceback.format_exc())

if __name__ == '__main__':
    check_member_table()
