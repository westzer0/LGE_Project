#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
기존 ONBOARDING_SESSION의 recommendation_result에서 데이터를 추출하여
정규화 테이블(ONBOARD_SESS_MAIN_SPACES, ONBOARD_SESS_PRIORITIES)에 저장
"""
import sys
import os
import json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

import django
django.setup()

from api.db.oracle_client import get_connection
import json

print("=" * 80)
print("기존 세션 데이터를 정규화 테이블로 마이그레이션")
print("=" * 80)
print()

try:
    with get_connection() as conn:
        with conn.cursor() as cur:
            # Oracle DB에서 직접 세션 조회 (Django ORM과 동기화 문제 방지)
            cur.execute("""
                SELECT SESSION_ID 
                FROM ONBOARDING_SESSION
                ORDER BY CREATED_AT DESC
            """)
            session_rows = cur.fetchall()
            total_count = len(session_rows)
            migrated_main_space = 0
            migrated_priority = 0
            skipped = 0
            error_count = 0
            
            print(f"총 {total_count}개 세션 처리 시작...")
            print()
            
            for idx, (session_id_row,) in enumerate(session_rows, 1):
                session_id = str(session_id_row)
                
                # Django ORM으로 recommendation_result 조회
                try:
                    from api.models import OnboardingSession
                    session = OnboardingSession.objects.get(session_id=session_id)
                    recommendation_result = session.recommendation_result or {}
                except:
                    # Django ORM에 없으면 recommendation_result 없음
                    recommendation_result = {}
                
                # MAIN_SPACE 추출 및 저장
                main_spaces = []
                if recommendation_result.get('main_space'):
                    main_spaces = recommendation_result.get('main_space')
                    if not isinstance(main_spaces, list):
                        main_spaces = [main_spaces]
                
                if main_spaces:
                    # 기존 데이터 삭제
                    cur.execute("DELETE FROM ONBOARD_SESS_MAIN_SPACES WHERE SESSION_ID = :session_id", 
                              {'session_id': session_id})
                    
                    # 새 데이터 삽입
                    for space in main_spaces:
                        try:
                            # SESSION_ID가 ONBOARDING_SESSION에 존재하는지 확인
                            cur.execute("SELECT COUNT(*) FROM ONBOARDING_SESSION WHERE SESSION_ID = :session_id", 
                                      {'session_id': session_id})
                            if cur.fetchone()[0] > 0:
                                cur.execute("""
                                    INSERT INTO ONBOARD_SESS_MAIN_SPACES (SESSION_ID, MAIN_SPACE, CREATED_AT)
                                    VALUES (:session_id, :main_space, SYSDATE)
                                """, {'session_id': session_id, 'main_space': str(space)})
                                migrated_main_space += 1
                            else:
                                error_count += 1
                        except Exception as e:
                            error_count += 1
                            if idx <= 10:  # 처음 10개만 상세 로그
                                print(f"  ⚠️ {session_id} MAIN_SPACE 저장 실패: {e}")
                
                # PRIORITY 추출 및 저장
                priorities = []
                if recommendation_result.get('priority'):
                    priorities = recommendation_result.get('priority')
                    if not isinstance(priorities, list):
                        priorities = [priorities]
                else:
                    # recommendation_result에 없으면 Oracle DB에서 직접 조회
                    try:
                        cur.execute("SELECT PRIORITY FROM ONBOARDING_SESSION WHERE SESSION_ID = :session_id", 
                                  {'session_id': session_id})
                        priority_row = cur.fetchone()
                        if priority_row and priority_row[0]:
                            priority_value = priority_row[0]
                            priorities = [priority_value] if isinstance(priority_value, str) else [str(priority_value)]
                    except:
                        pass
                
                if priorities:
                    # 기존 데이터 삭제
                    cur.execute("DELETE FROM ONBOARD_SESS_PRIORITIES WHERE SESSION_ID = :session_id", 
                              {'session_id': session_id})
                    
                    # 새 데이터 삽입
                    for idx_priority, priority in enumerate(priorities, start=1):
                        try:
                            # SESSION_ID가 ONBOARDING_SESSION에 존재하는지 확인
                            cur.execute("SELECT COUNT(*) FROM ONBOARDING_SESSION WHERE SESSION_ID = :session_id", 
                                      {'session_id': session_id})
                            if cur.fetchone()[0] > 0:
                                cur.execute("""
                                    INSERT INTO ONBOARD_SESS_PRIORITIES (SESSION_ID, PRIORITY, PRIORITY_ORDER, CREATED_AT)
                                    VALUES (:session_id, :priority, :priority_order, SYSDATE)
                                """, {
                                    'session_id': session_id, 
                                    'priority': str(priority), 
                                    'priority_order': idx_priority
                                })
                                migrated_priority += 1
                            else:
                                error_count += 1
                        except Exception as e:
                            error_count += 1
                            if idx <= 10:  # 처음 10개만 상세 로그
                                print(f"  ⚠️ {session_id} PRIORITY 저장 실패: {e}")
                
                if not main_spaces and not priorities:
                    skipped += 1
                
                if idx % 100 == 0:
                    print(f"  진행: {idx}/{total_count}... (main_space: {migrated_main_space}, priority: {migrated_priority})")
            
            conn.commit()
            
            print()
            print("=" * 80)
            print("마이그레이션 완료")
            print("=" * 80)
            print(f"  총 세션: {total_count}개")
            print(f"  MAIN_SPACE 레코드: {migrated_main_space}개")
            print(f"  PRIORITY 레코드: {migrated_priority}개")
            print(f"  데이터 없는 세션: {skipped}개")
            if error_count > 0:
                print(f"  오류 발생: {error_count}개 (FK 제약조건 위반 등)")
            
            # 결과 확인
            cur.execute("SELECT COUNT(*) FROM ONBOARD_SESS_MAIN_SPACES")
            main_spaces_count = cur.fetchone()[0]
            cur.execute("SELECT COUNT(*) FROM ONBOARD_SESS_PRIORITIES")
            priorities_count = cur.fetchone()[0]
            
            print()
            print("  [정규화 테이블 현황]")
            print(f"    ONBOARD_SESS_MAIN_SPACES: {main_spaces_count}개 레코드")
            print(f"    ONBOARD_SESS_PRIORITIES: {priorities_count}개 레코드")
            
except Exception as e:
    print(f"\n❌ 오류 발생: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

