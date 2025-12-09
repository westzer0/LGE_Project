#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
ONBOARD_SESS_MAIN_SPACES 테이블 데이터 확인 및 문제 진단
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

import django
django.setup()

from api.db.oracle_client import get_connection
from api.services.taste_calculation_service import TasteCalculationService

print("=" * 80)
print("ONBOARD_SESS_MAIN_SPACES 데이터 확인")
print("=" * 80)
print()

with get_connection() as conn:
    with conn.cursor() as cur:
        # 1. 정규화 테이블 데이터 확인
        cur.execute("SELECT COUNT(*) FROM ONBOARD_SESS_MAIN_SPACES")
        main_spaces_count = cur.fetchone()[0]
        print(f"[1] ONBOARD_SESS_MAIN_SPACES 레코드 수: {main_spaces_count}")
        
        # 2. 전체 세션 수
        cur.execute("SELECT COUNT(*) FROM ONBOARDING_SESSION")
        total_sessions = cur.fetchone()[0]
        print(f"[2] 전체 ONBOARDING_SESSION 레코드 수: {total_sessions}")
        
        # 3. 샘플 세션들의 main_space 확인
        print(f"\n[3] 샘플 세션들의 main_space 확인:")
        cur.execute("SELECT SESSION_ID FROM ONBOARDING_SESSION WHERE ROWNUM <= 10")
        sample_sessions = [row[0] for row in cur.fetchall()]
        
        for session_id in sample_sessions[:5]:
            try:
                data = TasteCalculationService._get_onboarding_data_from_session(session_id)
                main_space = data.get('main_space', [])
                print(f"  {session_id}: main_space = {main_space} (타입: {type(main_space)})")
            except Exception as e:
                print(f"  {session_id}: 오류 - {e}")
        
        # 4. ONBOARDING_SESSION 테이블에 MAIN_SPACE 컬럼이 있는지 확인
        print(f"\n[4] ONBOARDING_SESSION 테이블 구조 확인:")
        cur.execute("""
            SELECT COLUMN_NAME, DATA_TYPE 
            FROM USER_TAB_COLUMNS 
            WHERE TABLE_NAME = 'ONBOARDING_SESSION' 
            AND COLUMN_NAME LIKE '%SPACE%'
            ORDER BY COLUMN_NAME
        """)
        space_columns = cur.fetchall()
        if space_columns:
            for col_name, col_type in space_columns:
                print(f"  {col_name}: {col_type}")
        else:
            print("  MAIN_SPACE 관련 컬럼 없음 (정규화 테이블 사용)")
        
        # 5. 최근 생성된 세션 확인
        print(f"\n[5] 최근 생성된 세션 확인 (정규화 테이블에 데이터가 있는지):")
        cur.execute("""
            SELECT s.SESSION_ID, s.CREATED_AT,
                   (SELECT COUNT(*) FROM ONBOARD_SESS_MAIN_SPACES m WHERE m.SESSION_ID = s.SESSION_ID) as main_space_count
            FROM (
                SELECT SESSION_ID, CREATED_AT 
                FROM ONBOARDING_SESSION 
                ORDER BY CREATED_AT DESC
            ) s
            WHERE ROWNUM <= 5
        """)
        recent_sessions = cur.fetchall()
        for session_id, created_at, main_space_count in recent_sessions:
            print(f"  {session_id} (생성: {created_at}): main_space 레코드 {main_space_count}개")

print()
print("=" * 80)
print("결론:")
print("=" * 80)
if main_spaces_count == 0:
    print("⚠️ 문제 발견: ONBOARD_SESS_MAIN_SPACES 테이블에 데이터가 없습니다!")
    print()
    print("가능한 원인:")
    print("1. 기존 세션들이 정규화 테이블로 마이그레이션되지 않았을 수 있습니다.")
    print("   → 해결: python manage.py migrate_all_to_normalized 실행")
    print()
    print("2. 새로운 온보딩 세션에서 main_space가 저장되지 않고 있을 수 있습니다.")
    print("   → 해결: onboarding_db_service.py의 저장 로직 확인 필요")
    print()
    print("3. 실제로 사용자가 main_space를 선택하지 않았을 수 있습니다.")
    print("   → 해결: 프론트엔드에서 main_space 선택이 제대로 전달되는지 확인")
else:
    print(f"✅ 정상: ONBOARD_SESS_MAIN_SPACES 테이블에 {main_spaces_count}개 레코드가 있습니다.")

