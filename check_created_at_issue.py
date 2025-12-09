#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
created_at 칼럼의 쓰레기값 원인 추적
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


def check_created_at_issue():
    """ONBOARDING_SESSION 테이블의 created_at 칼럼 문제 확인"""
    print("=" * 80)
    print("ONBOARDING_SESSION 테이블 created_at 칼럼 문제 추적")
    print("=" * 80)
    
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                # 1. CREATED_AT 컬럼 타입 확인
                print("\n[1] CREATED_AT 컬럼 타입 확인...")
                cur.execute("""
                    SELECT COLUMN_NAME, DATA_TYPE, DATA_LENGTH, NULLABLE, DATA_DEFAULT
                    FROM USER_TAB_COLUMNS
                    WHERE TABLE_NAME = 'ONBOARDING_SESSION' 
                      AND COLUMN_NAME = 'CREATED_AT'
                """)
                col_info = cur.fetchone()
                if col_info:
                    print(f"  컬럼명: {col_info[0]}")
                    print(f"  데이터 타입: {col_info[1]}")
                    print(f"  데이터 길이: {col_info[2]}")
                    print(f"  NULL 허용: {col_info[3]}")
                    print(f"  기본값: {col_info[4]}")
                else:
                    print("  ⚠️ CREATED_AT 컬럼을 찾을 수 없습니다!")
                
                # 2. 문제가 있는 데이터 샘플 조회 (사용자가 제공한 SESSION_ID 포함)
                print("\n[2] 문제가 있는 데이터 샘플 조회...")
                # 사용자가 제공한 SESSION_ID들
                user_session_ids = [
                    '1765271034356', '1765270584060', '1765270756659',
                    '1ea06eea-20e5-439d-92d2-661b5c2d3b8d',
                    'ac0bef8a-c795-4bc3-8376-180d4126b0e6',
                    '76ed9a72-85d5-4a54-8d5c-540b768775d4',
                    'cdb5e052-c4ea-453c-a1f0-e2a8e7d185b8',
                    'ab828df6-659f-4892-a518-c763883779b3',
                    'c9e6182b-866c-479f-86ac-fdf27ca1401f',
                    '878004ad-e252-424f-a153-4d0e07b060c4'
                ]
                
                for session_id in user_session_ids:
                    try:
                        cur.execute("""
                            SELECT 
                                SESSION_ID,
                                MEMBER_ID,
                                TO_CHAR(CREATED_AT, 'YYYY-MM-DD HH24:MI:SS') AS CREATED_AT_FORMATTED,
                                TO_CHAR(CREATED_AT, 'YY/MM/DD HH24:MI:SS') AS CREATED_AT_SHORT,
                                CREATED_AT AS CREATED_AT_RAW,
                                DUMP(CREATED_AT) AS CREATED_AT_DUMP,
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
                            print(f"\n  [SESSION_ID: {session_id}]")
                            print(f"    MEMBER_ID: {row[1]}")
                            print(f"    CREATED_AT (YYYY-MM-DD): {row[2]}")
                            print(f"    CREATED_AT (YY/MM/DD): {row[3]}")
                            print(f"    CREATED_AT (RAW): {row[4]} (타입: {type(row[4]).__name__})")
                            print(f"    CREATED_AT (DUMP): {row[5]}")
                            print(f"    CURRENT_STEP: {row[6]}")
                            print(f"    STATUS: {row[7]}")
                            print(f"    VIBE: {row[8]}")
                            print(f"    HOUSING_TYPE: {row[9]}")
                            print(f"    PYUNG: {row[10]}")
                            print(f"    PRIORITY: {row[11]}")
                            print(f"    BUDGET_LEVEL: {row[12]}")
                        else:
                            print(f"\n  [SESSION_ID: {session_id}] - 레코드를 찾을 수 없습니다")
                    except Exception as e:
                        print(f"\n  [SESSION_ID: {session_id}] - 조회 중 오류: {e}")
                
                # 일반 샘플도 조회
                print("\n[2-2] 일반 데이터 샘플 조회 (최근 5개)...")
                cur.execute("""
                    SELECT 
                        SESSION_ID,
                        MEMBER_ID,
                        TO_CHAR(CREATED_AT, 'YYYY-MM-DD HH24:MI:SS') AS CREATED_AT_FORMATTED,
                        TO_CHAR(CREATED_AT, 'YY/MM/DD HH24:MI:SS') AS CREATED_AT_SHORT,
                        CURRENT_STEP,
                        STATUS
                    FROM (
                        SELECT 
                            SESSION_ID,
                            MEMBER_ID,
                            CREATED_AT,
                            CURRENT_STEP,
                            STATUS
                        FROM ONBOARDING_SESSION
                        ORDER BY CREATED_AT DESC
                    )
                    WHERE ROWNUM <= 5
                """)
                rows = cur.fetchall()
                print(f"  총 {len(rows)}개 레코드 조회")
                
                for idx, row in enumerate(rows, 1):
                    print(f"\n  [레코드 {idx}]")
                    print(f"    SESSION_ID: {row[0]} (타입: {type(row[0]).__name__})")
                    print(f"    MEMBER_ID: {row[1]}")
                    print(f"    CREATED_AT (포맷팅): {row[2]}")
                    print(f"    CREATED_AT (RAW): {row[3]} (타입: {type(row[3]).__name__})")
                    print(f"    CREATED_AT (DUMP): {row[4]}")
                    print(f"    CURRENT_STEP: {row[5]}")
                    print(f"    STATUS: {row[6]}")
                    print(f"    VIBE: {row[7]}")
                    print(f"    HOUSING_TYPE: {row[8]}")
                    print(f"    PYUNG: {row[9]}")
                    print(f"    PRIORITY: {row[10]}")
                    print(f"    BUDGET_LEVEL: {row[11]}")
                
                # 3. 타임스탬프 기반 SESSION_ID 확인
                print("\n[3] 타임스탬프 기반 SESSION_ID 확인...")
                cur.execute("""
                    SELECT 
                        SESSION_ID,
                        TO_CHAR(CREATED_AT, 'YY/MM/DD HH24:MI:SS') AS CREATED_AT_SHORT,
                        LENGTH(SESSION_ID) AS SESSION_ID_LENGTH
                    FROM (
                        SELECT 
                            SESSION_ID,
                            CREATED_AT,
                            LENGTH(SESSION_ID) AS SESSION_ID_LENGTH
                        FROM ONBOARDING_SESSION
                        WHERE REGEXP_LIKE(SESSION_ID, '^[0-9]+$')
                          AND LENGTH(SESSION_ID) >= 10
                        ORDER BY CREATED_AT DESC
                    )
                    WHERE ROWNUM <= 10
                """)
                timestamp_rows = cur.fetchall()
                print(f"  타임스탬프 기반 SESSION_ID: {len(timestamp_rows)}개 발견")
                for row in timestamp_rows:
                    print(f"    SESSION_ID: {row[0]}, CREATED_AT: {row[1]}, 길이: {row[2]}")
                
                # 4. CREATED_AT이 문자열로 저장된 경우 확인
                print("\n[4] CREATED_AT이 문자열로 저장된 경우 확인...")
                cur.execute("""
                    SELECT 
                        SESSION_ID,
                        CREATED_AT,
                        DUMP(CREATED_AT) AS CREATED_AT_DUMP
                    FROM (
                        SELECT 
                            SESSION_ID,
                            CREATED_AT,
                            DUMP(CREATED_AT) AS CREATED_AT_DUMP
                        FROM ONBOARDING_SESSION
                        WHERE CREATED_AT IS NOT NULL
                          AND TO_CHAR(CREATED_AT, 'YY/MM/DD') LIKE '25/%'
                        ORDER BY CREATED_AT DESC
                    )
                    WHERE ROWNUM <= 5
                """)
                suspicious_rows = cur.fetchall()
                print(f"  '25/...' 형식의 CREATED_AT: {len(suspicious_rows)}개 발견")
                for row in suspicious_rows:
                    print(f"    SESSION_ID: {row[0]}")
                    print(f"    CREATED_AT: {row[1]}")
                    print(f"    DUMP: {row[2]}")
                
                # 5. 최근 삽입된 데이터 확인
                print("\n[5] 최근 삽입된 데이터 확인 (최근 5개)...")
                cur.execute("""
                    SELECT 
                        SESSION_ID,
                        MEMBER_ID,
                        TO_CHAR(CREATED_AT, 'YYYY-MM-DD HH24:MI:SS') AS CREATED_AT,
                        TO_CHAR(UPDATED_AT, 'YYYY-MM-DD HH24:MI:SS') AS UPDATED_AT,
                        CURRENT_STEP,
                        STATUS
                    FROM (
                        SELECT 
                            SESSION_ID,
                            MEMBER_ID,
                            CREATED_AT,
                            UPDATED_AT,
                            CURRENT_STEP,
                            STATUS
                        FROM ONBOARDING_SESSION
                        ORDER BY CREATED_AT DESC
                    )
                    WHERE ROWNUM <= 5
                """)
                recent_rows = cur.fetchall()
                for row in recent_rows:
                    print(f"    SESSION_ID: {row[0]}, CREATED_AT: {row[2]}, STATUS: {row[5]}")
                
                print("\n" + "=" * 80)
                print("확인 완료!")
                print("=" * 80)
                
    except Exception as e:
        print(f"\n오류 발생: {str(e)}")
        import traceback
        print(traceback.format_exc())
        sys.exit(1)


if __name__ == '__main__':
    check_created_at_issue()

