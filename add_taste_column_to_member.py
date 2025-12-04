#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
MEMBER 테이블에 TASTE 칼럼 추가
"""
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

from api.db.oracle_client import get_connection


def add_taste_column():
    """TASTE 칼럼 추가"""
    print("=" * 60)
    print("MEMBER 테이블에 TASTE 칼럼 추가")
    print("=" * 60)
    
    try:
        conn = get_connection()
        print("\n[1] Oracle DB 연결 성공!")
        
        # TASTE 칼럼 추가
        print("\n[2] TASTE 칼럼 추가 중...")
        with conn.cursor() as cur:
            try:
                cur.execute("""
                    ALTER TABLE MEMBER ADD (TASTE NUMBER(10))
                """)
                print("  ✓ TASTE 칼럼 추가 완료")
            except Exception as e:
                error_msg = str(e)
                if '01430' in error_msg or 'already exists' in error_msg.lower() or 'name is already used' in error_msg.lower():
                    print("  ⚠ TASTE 칼럼이 이미 존재합니다")
                else:
                    print(f"  ✗ TASTE 칼럼 추가 실패: {str(e)}")
                    raise
        
        conn.commit()
        
        # 칼럼 확인
        print("\n[3] 최종 확인:")
        with conn.cursor() as cur:
            cur.execute("""
                SELECT COLUMN_NAME, DATA_TYPE, DATA_LENGTH, NULLABLE
                FROM USER_TAB_COLUMNS
                WHERE TABLE_NAME = 'MEMBER' AND COLUMN_NAME = 'TASTE'
            """)
            result = cur.fetchone()
            if result:
                col_name, data_type, data_length, nullable = result
                print(f"  ✓ TASTE 칼럼: {data_type}({data_length if data_length else 'N/A'}) - {'NULL' if nullable == 'Y' else 'NOT NULL'}")
            else:
                print("  ⚠ TASTE 칼럼을 찾을 수 없습니다")
        
        conn.close()
        print("\n" + "=" * 60)
        print("✅ 완료!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n✗ 오류 발생: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    add_taste_column()

