#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
MEMBER 테이블의 MEMBER_ID 확인
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

def check_member_ids():
    """MEMBER 테이블의 MEMBER_ID 확인"""
    print("=" * 80)
    print("MEMBER 테이블의 MEMBER_ID 확인")
    print("=" * 80)
    
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                # MEMBER 테이블의 MEMBER_ID 조회
                cur.execute("SELECT MEMBER_ID FROM MEMBER ORDER BY MEMBER_ID")
                member_ids = cur.fetchall()
                
                print(f"\n총 {len(member_ids)}개 MEMBER:")
                print("-" * 80)
                
                # 처음 10개와 마지막 10개만 출력
                if len(member_ids) > 20:
                    for i in range(10):
                        print(f"  {member_ids[i][0]}")
                    print("  ...")
                    for i in range(len(member_ids) - 10, len(member_ids)):
                        print(f"  {member_ids[i][0]}")
                else:
                    for member_id in member_ids:
                        print(f"  {member_id[0]}")
                
                # user_0001 형식이 있는지 확인
                cur.execute("SELECT COUNT(*) FROM MEMBER WHERE MEMBER_ID LIKE 'user_%'")
                user_count = cur.fetchone()[0]
                print(f"\nuser_ 형식 MEMBER 수: {user_count}개")
                
    except Exception as e:
        print(f"오류 발생: {str(e)}")
        import traceback
        print(traceback.format_exc())

if __name__ == '__main__':
    check_member_ids()




