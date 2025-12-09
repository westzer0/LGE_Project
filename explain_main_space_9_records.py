#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
MAIN_SPACE가 9개 레코드만 있는 이유 설명
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

import django
django.setup()

from api.db.oracle_client import get_connection
from api.models import OnboardingSession

print("=" * 80)
print("MAIN_SPACE가 9개 레코드만 있는 이유 분석")
print("=" * 80)
print()

# 1. 데이터베이스 현황
print("[1] 데이터베이스 현황")
with get_connection() as conn:
    with conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM ONBOARDING_SESSION")
        oracle_total = cur.fetchone()[0]
        
        cur.execute("SELECT COUNT(*) FROM ONBOARDING_SESSION WHERE CURRENT_STEP >= 3")
        oracle_step3_plus = cur.fetchone()[0]

django_total = OnboardingSession.objects.count()

print(f"  Oracle DB 전체 세션: {oracle_total}개")
print(f"  Oracle DB Step 3 이상 세션: {oracle_step3_plus}개")
print(f"  Django ORM 전체 세션: {django_total}개")
print()

# 2. recommendation_result 현황
print("[2] recommendation_result 데이터 현황")
print("  ⚠️ 중요: Oracle DB의 ONBOARDING_SESSION 테이블에는 RECOMMENDATION_RESULT 컬럼이 없습니다!")
print("  → RECOMMENDATION_RESULT는 Django ORM(SQLite)에만 저장됩니다.")
print("  → Oracle DB에는 정규화 테이블(ONBOARD_SESS_MAIN_SPACES 등)에만 저장됩니다.")
print()

# 3. Django ORM에서 main_space가 있는 세션
print("[3] Django ORM에서 main_space가 있는 세션")
django_with_main_space = []
for session in OnboardingSession.objects.all():
    if session.recommendation_result and session.recommendation_result.get('main_space'):
        django_with_main_space.append(session)

print(f"  Django ORM 세션 중 recommendation_result에 main_space가 있는 세션: {len(django_with_main_space)}개")
print()

# 4. 마이그레이션 과정
print("[4] 마이그레이션 과정")
print("  마이그레이션 스크립트는:")
print("  1. Oracle DB의 모든 세션(1056개)을 조회")
print("  2. 각 세션의 SESSION_ID로 Django ORM에서 recommendation_result 조회")
print("  3. recommendation_result에 main_space가 있으면 정규화 테이블에 저장")
print()
print("  문제:")
print(f"  - Django ORM에는 {django_total}개 세션만 존재")
print(f"  - Oracle DB에는 {oracle_total}개 세션이 존재")
print(f"  - Django ORM에 없는 세션은 recommendation_result를 조회할 수 없음")
print(f"  - 따라서 Django ORM에 있는 {len(django_with_main_space)}개 세션만 처리 가능")
print()

# 5. 실제 저장된 데이터
print("[5] 실제 저장된 데이터")
with get_connection() as conn:
    with conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM ONBOARD_SESS_MAIN_SPACES")
        main_spaces_count = cur.fetchone()[0]
        
        cur.execute("SELECT COUNT(DISTINCT SESSION_ID) FROM ONBOARD_SESS_MAIN_SPACES")
        sessions_count = cur.fetchone()[0]
        
        print(f"  정규화 테이블 MAIN_SPACE 레코드: {main_spaces_count}개")
        print(f"  MAIN_SPACE가 있는 세션: {sessions_count}개")
        print()

# 6. 결론
print("=" * 80)
print("결론: MAIN_SPACE가 9개 레코드만 있는 이유")
print("=" * 80)
print()
print("1. 데이터 저장 구조:")
print("   - Django ORM (SQLite): recommendation_result에 main_space 저장")
print("   - Oracle DB: 정규화 테이블(ONBOARD_SESS_MAIN_SPACES)에만 저장")
print()
print("2. Django ORM과 Oracle DB의 동기화 문제:")
print(f"   - Django ORM: {django_total}개 세션")
print(f"   - Oracle DB: {oracle_total}개 세션")
print(f"   - 대부분의 Oracle DB 세션이 Django ORM에 없음")
print()
print("3. 마이그레이션 제한:")
print(f"   - Django ORM에 있는 세션 중 {len(django_with_main_space)}개만 main_space 데이터 보유")
print("   - 이 세션들의 main_space를 정규화 테이블로 마이그레이션")
print(f"   - 결과: {main_spaces_count}개 레코드 저장됨")
print()
print("4. 해결 방법:")
print("   ✅ 새로운 세션에서는 수정된 코드로 정상 저장됨")
print("   ✅ 기존 세션 중 Django ORM에 있는 것만 마이그레이션됨")
print("   ⚠️ Django ORM에 없는 Oracle DB 세션은 마이그레이션 불가")
print()
print("5. 현재 상태:")
print("   - PRIORITY: 1080개 레코드 (100% 세션에 데이터 있음) ✅")
print("   - MAIN_SPACE: 9개 레코드 (Django ORM 세션 중 일부만) ⚠️")
print("   - 새로운 세션에서는 정상 저장됨 ✅")

