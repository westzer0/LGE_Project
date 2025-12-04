#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import sys
import django

sys.path.insert(0, '.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from api.db.oracle_client import get_connection

# Oracle DB에서 PRODUCT 테이블의 MAIN_CATEGORY 확인
with get_connection() as conn:
    with conn.cursor() as cur:
        # MAIN_CATEGORY 컬럼이 있는지 확인
        try:
            # 먼저 테이블 구조 확인
            cur.execute("""
                SELECT column_name, data_type 
                FROM user_tab_columns 
                WHERE table_name = 'PRODUCT' 
                AND column_name LIKE '%CATEGORY%'
                ORDER BY column_name
            """)
            columns = cur.fetchall()
            print("PRODUCT 테이블의 CATEGORY 관련 컬럼:")
            for col in columns:
                print(f"  - {col[0]}: {col[1]}")
            
            print("\n" + "="*80)
            
            # MAIN_CATEGORY 컬럼이 있으면 값 확인
            if any('MAIN_CATEGORY' in str(col[0]).upper() for col in columns):
                cur.execute("""
                    SELECT MAIN_CATEGORY, COUNT(*) as cnt
                    FROM PRODUCT
                    WHERE MAIN_CATEGORY IS NOT NULL
                    GROUP BY MAIN_CATEGORY
                    ORDER BY cnt DESC
                """)
                categories = cur.fetchall()
                print(f"\nMAIN_CATEGORY 목록 (총 {len(categories)}개):")
                for cat, cnt in categories:
                    print(f"  - {cat}: {cnt}개")
            else:
                # MAIN_CATEGORY가 없으면 다른 카테고리 컬럼 확인
                print("\nMAIN_CATEGORY 컬럼이 없습니다. 다른 카테고리 컬럼 확인:")
                for col_name, _ in columns:
                    cur.execute(f"""
                        SELECT DISTINCT {col_name}
                        FROM PRODUCT
                        WHERE {col_name} IS NOT NULL
                        ORDER BY {col_name}
                    """)
                    values = cur.fetchall()
                    print(f"\n{col_name} 값들:")
                    for val in values[:20]:  # 최대 20개만
                        print(f"  - {val[0]}")
                    if len(values) > 20:
                        print(f"  ... 외 {len(values) - 20}개")
        
        except Exception as e:
            print(f"오류 발생: {str(e)}")
            import traceback
            traceback.print_exc()

