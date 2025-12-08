#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
MEMBER 테이블을 완전히 비우고 1000개의 랜덤 데이터로 채우는 스크립트
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
from generate_member_dummy_data import (
    generate_members,
    insert_members,
    NUM_MEMBERS
)


def main():
    """1000개 랜덤 데이터 생성 및 삽입"""
    print("=" * 80)
    print("MEMBER 테이블에 1000개 랜덤 데이터 생성")
    print("=" * 80)
    
    # 기존 데이터 확인
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT COUNT(*) FROM MEMBER")
                existing_count = cur.fetchone()[0]
                print(f"\n[정보] 현재 MEMBER 테이블 레코드 수: {existing_count}개")
    except Exception as e:
        print(f"[경고] 기존 데이터 확인 중 오류: {e}")
        print("계속 진행합니다...")
    
    # 새 데이터 생성
    print("\n" + "=" * 80)
    print(f"{NUM_MEMBERS}개 랜덤 데이터 생성 중...")
    print("=" * 80)
    
    members = generate_members(NUM_MEMBERS)
    print(f"✓ {NUM_MEMBERS}개 데이터 생성 완료")
    
    # DB에 삽입
    print("\n" + "=" * 80)
    print("Oracle DB에 데이터 삽입 중...")
    print("=" * 80)
    
    success = insert_members(members)
    
    if success:
        print("\n" + "=" * 80)
        print("✓ 완료! MEMBER 테이블에 1000개 데이터가 성공적으로 삽입되었습니다.")
        print("=" * 80)
        
        # 최종 확인
        try:
            with get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT COUNT(*) FROM MEMBER")
                    final_count = cur.fetchone()[0]
                    print(f"\n[확인] 현재 MEMBER 테이블 레코드 수: {final_count}개")
        except Exception as e:
            print(f"[경고] 최종 확인 중 오류: {e}")
    else:
        print("\n" + "=" * 80)
        print("✗ 실패! 데이터 삽입 중 오류가 발생했습니다.")
        print("=" * 80)
        return False
    
    return True


if __name__ == '__main__':
    main()

