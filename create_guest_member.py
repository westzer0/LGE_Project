#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
MEMBER 테이블에 GUEST 레코드 생성
외래키 제약조건을 만족하기 위해 필요
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

def create_guest_member():
    """MEMBER 테이블에 GUEST 레코드 생성"""
    print("=" * 80)
    print("MEMBER 테이블에 GUEST 레코드 생성")
    print("=" * 80)
    
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                # 1. GUEST 레코드가 이미 존재하는지 확인
                cur.execute("SELECT COUNT(*) FROM MEMBER WHERE MEMBER_ID = 'GUEST'")
                exists = cur.fetchone()[0] > 0
                
                if exists:
                    print("\n[정보] GUEST 레코드가 이미 존재합니다.")
                    return True
                
                # 2. MEMBER 테이블 스키마 확인 (필수 컬럼 파악)
                cur.execute("""
                    SELECT COLUMN_NAME, NULLABLE, DATA_DEFAULT
                    FROM USER_TAB_COLUMNS
                    WHERE TABLE_NAME = 'MEMBER'
                    ORDER BY COLUMN_ID
                """)
                
                columns = cur.fetchall()
                required_columns = []
                optional_columns = []
                
                for col_name, nullable, data_default in columns:
                    if nullable == 'N' and not data_default:
                        required_columns.append(col_name)
                    else:
                        optional_columns.append(col_name)
                
                print(f"\n[필수 컬럼] {', '.join(required_columns)}")
                print(f"[선택 컬럼] {', '.join(optional_columns)}")
                
                # 3. MEMBER_ID 타입 확인
                cur.execute("""
                    SELECT DATA_TYPE, DATA_LENGTH
                    FROM USER_TAB_COLUMNS
                    WHERE TABLE_NAME = 'MEMBER' AND COLUMN_NAME = 'MEMBER_ID'
                """)
                member_id_info = cur.fetchone()
                
                if not member_id_info:
                    print("\n[오류] MEMBER_ID 컬럼을 찾을 수 없습니다.")
                    return False
                
                data_type, data_length = member_id_info
                print(f"\n[MEMBER_ID 타입] {data_type}({data_length})")
                
                # 4. GUEST 레코드 생성
                # 최소한의 필수 컬럼만으로 생성
                try:
                    # MEMBER_ID가 VARCHAR2인 경우
                    if 'VARCHAR' in data_type.upper():
                        cur.execute("""
                            INSERT INTO MEMBER (MEMBER_ID, CREATED_DATE, CREATED_AT) 
                            VALUES ('GUEST', SYSDATE, SYSDATE)
                        """)
                    else:
                        # MEMBER_ID가 NUMBER인 경우 - 시퀀스나 다른 방법 필요
                        print("\n[경고] MEMBER_ID가 NUMBER 타입입니다. GUEST를 문자열로 생성할 수 없습니다.")
                        print("대신 기존 MEMBER_ID를 사용하거나, MEMBER_ID를 NULL 허용으로 변경해야 합니다.")
                        return False
                    
                    conn.commit()
                    print("\n[성공] GUEST 레코드가 생성되었습니다.")
                    return True
                    
                except Exception as insert_error:
                    print(f"\n[오류] GUEST 레코드 생성 실패: {insert_error}")
                    print("\n[대안] MEMBER 테이블에 기존 레코드가 있는지 확인하세요.")
                    return False
                    
    except Exception as e:
        print(f"\n[오류] 데이터베이스 연결 또는 쿼리 실행 실패: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = create_guest_member()
    if success:
        print("\n" + "=" * 80)
        print("완료")
        print("=" * 80)
    else:
        print("\n" + "=" * 80)
        print("실패 - 수동으로 확인이 필요합니다")
        print("=" * 80)
        sys.exit(1)

