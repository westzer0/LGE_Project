#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
SESSION_ID 생성 및 변환 경로 추적
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
import uuid


def check_session_id_flow():
    """SESSION_ID 생성 및 변환 경로 확인"""
    print("=" * 80)
    print("SESSION_ID 생성 및 변환 경로 추적")
    print("=" * 80)
    
    # 사용자가 제공한 SESSION_ID 목록
    session_ids = [
        '888f6879-56eb-4f0b-874a-ae6708894cf5',
        '1765270756659',
        '1ea06eea-20e5-439d-92d2-661b5c2d3b8d',
        '878004ad-e252-424f-a153-4d0e07b060c4',
        '76ed9a72-85d5-4a54-8d5c-540b768775d4',
        'cdb5e052-c4ea-453c-a1f0-e2a8e7d185b8',
        'ab828df6-659f-4892-a518-c763883779b3',
        'c9e6182b-866c-479f-86ac-fdf27ca1401f',
        'ac0bef8a-c795-4bc3-8376-180d4126b0e6',
        '1d0ac51c-3695-4671-a07a-a0750baf475e',
        'ae929fa8-4f4a-4646-8416-1bd243a700af',
        'f3ae7ec7-a09d-4bd9-8af4-66d0a29fd689',
        '52fceefe-c0a5-4295-b732-79ef947b2fa4',
        '3bb6d076-3c44-4342-b1c2-4540ced5b4b4',
        'dbdadbb8-25f0-4331-822e-5f26a4f91db1'
    ]
    
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                print("\n[1] 각 SESSION_ID의 실제 저장 상태 확인...")
                print("-" * 80)
                
                for session_id in session_ids:
                    try:
                        # SESSION_ID가 숫자인지 확인
                        is_numeric = False
                        try:
                            timestamp = int(session_id)
                            is_numeric = True
                        except (ValueError, TypeError):
                            pass
                        
                        # UUID 형식인지 확인
                        is_uuid = False
                        try:
                            uuid_obj = uuid.UUID(session_id)
                            is_uuid = True
                        except (ValueError, TypeError):
                            pass
                        
                        # views.py의 변환 로직 시뮬레이션
                        converted_session_id = session_id
                        if is_numeric:
                            namespace = uuid.UUID('6ba7b810-9dad-11d1-80b4-00c04fd430c8')
                            converted_session_id = str(uuid.uuid5(namespace, f"onboarding_session_{timestamp}"))
                        
                        # DB에서 조회
                        cur.execute("""
                            SELECT 
                                SESSION_ID,
                                MEMBER_ID,
                                TO_CHAR(CREATED_AT, 'YYYY-MM-DD HH24:MI:SS') AS CREATED_AT,
                                CURRENT_STEP,
                                STATUS,
                                VIBE,
                                HOUSING_TYPE,
                                PYUNG,
                                PRIORITY,
                                BUDGET_LEVEL
                            FROM ONBOARDING_SESSION
                            WHERE SESSION_ID = :session_id
                        """, {'session_id': session_id})
                        row = cur.fetchone()
                        
                        if row:
                            print(f"\n✅ [SESSION_ID: {session_id}]")
                            print(f"   타입: {'타임스탬프' if is_numeric else 'UUID' if is_uuid else '알 수 없음'}")
                            if is_numeric:
                                print(f"   변환된 UUID: {converted_session_id}")
                            print(f"   MEMBER_ID: {row[1]}")
                            print(f"   CREATED_AT: {row[2]}")
                            print(f"   CURRENT_STEP: {row[3]}")
                            print(f"   STATUS: {row[4]}")
                            print(f"   VIBE: {row[5]}")
                            print(f"   HOUSING_TYPE: {row[6]}")
                            print(f"   PYUNG: {row[7]}")
                            print(f"   PRIORITY: {row[8]}")
                            print(f"   BUDGET_LEVEL: {row[9]}")
                            
                            # 변환된 UUID로도 조회해보기
                            if is_numeric and converted_session_id != session_id:
                                cur.execute("""
                                    SELECT SESSION_ID, MEMBER_ID, TO_CHAR(CREATED_AT, 'YYYY-MM-DD HH24:MI:SS')
                                    FROM ONBOARDING_SESSION
                                    WHERE SESSION_ID = :session_id
                                """, {'session_id': converted_session_id})
                                converted_row = cur.fetchone()
                                if converted_row:
                                    print(f"   ⚠️ 변환된 UUID로도 레코드가 존재함: {converted_session_id}")
                                    print(f"      MEMBER_ID: {converted_row[1]}, CREATED_AT: {converted_row[2]}")
                        else:
                            print(f"\n❌ [SESSION_ID: {session_id}] - 레코드를 찾을 수 없습니다")
                            if is_numeric:
                                print(f"   타입: 타임스탬프")
                                print(f"   변환된 UUID: {converted_session_id}")
                                # 변환된 UUID로 조회해보기
                                cur.execute("""
                                    SELECT SESSION_ID, MEMBER_ID, TO_CHAR(CREATED_AT, 'YYYY-MM-DD HH24:MI:SS')
                                    FROM ONBOARDING_SESSION
                                    WHERE SESSION_ID = :session_id
                                """, {'session_id': converted_session_id})
                                converted_row = cur.fetchone()
                                if converted_row:
                                    print(f"   ✅ 변환된 UUID로는 레코드가 존재함: {converted_session_id}")
                                    print(f"      MEMBER_ID: {converted_row[1]}, CREATED_AT: {converted_row[2]}")
                    except Exception as e:
                        print(f"\n⚠️ [SESSION_ID: {session_id}] - 조회 중 오류: {e}")
                
                print("\n" + "=" * 80)
                print("[2] 타임스탬프 기반 SESSION_ID와 변환된 UUID 매칭 확인...")
                print("-" * 80)
                
                # 타임스탬프 기반 SESSION_ID 찾기
                cur.execute("""
                    SELECT SESSION_ID, MEMBER_ID, TO_CHAR(CREATED_AT, 'YYYY-MM-DD HH24:MI:SS')
                    FROM ONBOARDING_SESSION
                    WHERE REGEXP_LIKE(SESSION_ID, '^[0-9]+$')
                      AND LENGTH(SESSION_ID) >= 10
                    ORDER BY CREATED_AT DESC
                """)
                timestamp_sessions = cur.fetchall()
                
                print(f"\n타임스탬프 기반 SESSION_ID: {len(timestamp_sessions)}개 발견")
                for row in timestamp_sessions[:5]:  # 최대 5개만 표시
                    session_id = row[0]
                    timestamp = int(session_id)
                    namespace = uuid.UUID('6ba7b810-9dad-11d1-80b4-00c04fd430c8')
                    converted_uuid = str(uuid.uuid5(namespace, f"onboarding_session_{timestamp}"))
                    
                    print(f"\n  타임스탬프: {session_id}")
                    print(f"  변환된 UUID: {converted_uuid}")
                    
                    # 변환된 UUID로 조회
                    cur.execute("""
                        SELECT SESSION_ID, MEMBER_ID, TO_CHAR(CREATED_AT, 'YYYY-MM-DD HH24:MI:SS')
                        FROM ONBOARDING_SESSION
                        WHERE SESSION_ID = :session_id
                    """, {'session_id': converted_uuid})
                    converted_row = cur.fetchone()
                    if converted_row:
                        print(f"  ⚠️ 변환된 UUID로도 레코드 존재: {converted_row[0]}")
                        print(f"     MEMBER_ID: {converted_row[1]}, CREATED_AT: {converted_row[2]}")
                    else:
                        print(f"  ✅ 변환된 UUID로는 레코드 없음 (정상)")
                
                print("\n" + "=" * 80)
                print("분석 완료!")
                print("=" * 80)
                
    except Exception as e:
        print(f"\n오류 발생: {str(e)}")
        import traceback
        print(traceback.format_exc())
        sys.exit(1)


if __name__ == '__main__':
    check_session_id_flow()

