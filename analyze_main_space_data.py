#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
MAIN_SPACE 데이터가 9개만 있는 원인 분석
"""
import sys
import os
import json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

import django
django.setup()

from api.db.oracle_client import get_connection
from api.models import OnboardingSession

print("=" * 80)
print("MAIN_SPACE 데이터 분석")
print("=" * 80)
print()

# 1. Django ORM에서 recommendation_result에 main_space가 있는 세션 확인
print("[1] Django ORM - recommendation_result에 main_space가 있는 세션")
sessions_with_main_space = []
for session in OnboardingSession.objects.all():
    if session.recommendation_result and session.recommendation_result.get('main_space'):
        main_space = session.recommendation_result.get('main_space')
        sessions_with_main_space.append({
            'session_id': str(session.session_id),
            'main_space': main_space,
            'current_step': session.current_step,
            'status': session.status
        })

print(f"  총 {len(sessions_with_main_space)}개 세션에 main_space 데이터가 있습니다.")
print()
print("  [샘플 세션]")
for s in sessions_with_main_space[:5]:
    print(f"    {s['session_id']}: main_space={s['main_space']}, step={s['current_step']}, status={s['status']}")

print()

# 2. 전체 세션의 current_step 분포 확인
print("[2] 전체 세션의 current_step 분포")
from collections import Counter
step_distribution = Counter()
status_distribution = Counter()

for session in OnboardingSession.objects.all():
    step_distribution[session.current_step or 0] += 1
    status_distribution[session.status or 'unknown'] += 1

print("  [current_step 분포]")
for step, count in sorted(step_distribution.items()):
    print(f"    Step {step}: {count}개 세션")

print()
print("  [status 분포]")
for status, count in sorted(status_distribution.items()):
    print(f"    {status}: {count}개 세션")

print()

# 3. Step 3 이상 완료한 세션 중 main_space가 있는지 확인
print("[3] Step 3 이상 완료한 세션 중 main_space 데이터 확인")
step3_or_above = OnboardingSession.objects.filter(current_step__gte=3)
print(f"  Step 3 이상 세션: {step3_or_above.count()}개")

step3_with_main_space = 0
for session in step3_or_above:
    if session.recommendation_result and session.recommendation_result.get('main_space'):
        step3_with_main_space += 1

print(f"  Step 3 이상 세션 중 main_space가 있는 세션: {step3_with_main_space}개")
print(f"  비율: {step3_with_main_space/step3_or_above.count()*100:.1f}%")

print()

# 4. Oracle DB에서 직접 확인
print("[4] Oracle DB - ONBOARDING_SESSION 테이블 확인")
with get_connection() as conn:
    with conn.cursor() as cur:
        # 전체 세션 수
        cur.execute("SELECT COUNT(*) FROM ONBOARDING_SESSION")
        total_oracle = cur.fetchone()[0]
        print(f"  Oracle DB 전체 세션: {total_oracle}개")
        
        # Step 3 이상 세션 수
        cur.execute("SELECT COUNT(*) FROM ONBOARDING_SESSION WHERE CURRENT_STEP >= 3")
        step3_or_above_oracle = cur.fetchone()[0]
        print(f"  Oracle DB Step 3 이상 세션: {step3_or_above_oracle}개")
        
        # 정규화 테이블에 저장된 MAIN_SPACE 수
        cur.execute("SELECT COUNT(*) FROM ONBOARD_SESS_MAIN_SPACES")
        main_spaces_count = cur.fetchone()[0]
        print(f"  정규화 테이블 MAIN_SPACE 레코드: {main_spaces_count}개")
        
        # MAIN_SPACE가 있는 세션 수
        cur.execute("SELECT COUNT(DISTINCT SESSION_ID) FROM ONBOARD_SESS_MAIN_SPACES")
        sessions_with_main_space_oracle = cur.fetchone()[0]
        print(f"  MAIN_SPACE가 있는 세션: {sessions_with_main_space_oracle}개")

print()
print("=" * 80)
print("결론")
print("=" * 80)
print(f"1. Django ORM에서 recommendation_result에 main_space가 있는 세션: {len(sessions_with_main_space)}개")
print(f"2. Step 3 이상 완료한 세션: {step3_or_above.count()}개")
print(f"3. Step 3 이상 세션 중 main_space가 있는 세션: {step3_with_main_space}개")
print()
print("가능한 원인:")
print("- 대부분의 기존 세션이 Step 3를 완료하지 않았거나")
print("- Step 3를 완료했지만 main_space를 선택하지 않았거나")
print("- main_space가 recommendation_result에 저장되지 않았을 수 있습니다.")

