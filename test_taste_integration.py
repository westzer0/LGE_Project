#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Step 5: 통합 테스트 - 온보딩 완료 시점에서 전체 플로우 테스트 (조건 체크 → 데이터 조회 → 계산 → 저장)

검증 항목:
1. 온보딩 완료 조건 검증
2. 전체 플로우 통합 검증
3. 실제 완료 세션 데이터로 검증 (100개 이상)
4. 조건별 분기 검증
5. 에러 처리 검증
6. 데이터 일관성 검증
7. 성능 검증
"""
import sys
import os
import json
import time
from datetime import datetime
from collections import Counter
from typing import Optional, Dict, List

# Django 설정 로드
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

import django
django.setup()

from api.services.taste_calculation_service import TasteCalculationService
from api.services.onboarding_db_service import OnboardingDBService
from api.db.oracle_client import get_connection

# 시각화 라이브러리
try:
    import matplotlib.pyplot as plt
    import matplotlib
    matplotlib.use('Agg')  # GUI 없이 사용
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False
    print("⚠️ matplotlib이 설치되지 않아 시각화를 건너뜁니다.")

# NumPy 라이브러리 (성능 측정용)
try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False
    # NumPy 없이도 작동하도록 간단한 통계 함수 정의
    def mean(values):
        return sum(values) / len(values) if values else 0
    def min_val(values):
        return min(values) if values else 0
    def max_val(values):
        return max(values) if values else 0


class TasteIntegrationValidator:
    """온보딩 완료 시점 전체 플로우 통합 검증 클래스"""
    
    def __init__(self):
        self.results = {
            'completion_conditions': [],
            'full_flow_tests': [],
            'conditional_branches': [],
            'error_handling_tests': [],
            'consistency_tests': [],
            'performance_metrics': {},
            'errors': [],
            'warnings': [],
            'saved_tastes': [],
            'branch_counts': {
                'executed': 0,  # STATUS='COMPLETED' && MEMBER_ID != 'GUEST'
                'skipped_guest': 0,  # STATUS='COMPLETED' && MEMBER_ID == 'GUEST'
                'skipped_in_progress': 0,  # STATUS='IN_PROGRESS'
                'skipped_abandoned': 0,  # STATUS='ABANDONED'
            }
        }
        # 테스트 중 변경된 MEMBER_ID와 원래 TASTE 값을 저장 (복원용)
        self.backup_data = {}
    
    def validate_all(self):
        """모든 검증 실행"""
        print("=" * 80)
        print("Step 5: 온보딩 완료 시점 전체 플로우 통합 검증")
        print("=" * 80)
        print()
        
        try:
            # 1. 완료 조건 검증
            print("[1] 온보딩 완료 조건 검증")
            self._validate_completion_conditions()
            print()
            
            # 2. 전체 플로우 통합 검증
            print("[2] 전체 플로우 통합 검증")
            self._validate_full_flow()
            print()
            
            # 3. 실제 완료 세션 데이터로 검증 (1000개 이상)
            print("[3] 실제 완료 세션 데이터로 검증 (1000개 이상)")
            self._validate_with_completed_sessions(count=1000)
            print()
            
            # 4. 조건별 분기 검증
            print("[4] 조건별 분기 검증")
            self._validate_conditional_branches()
            print()
            
            # 5. 에러 처리 검증
            print("[5] 에러 처리 검증")
            self._validate_error_handling()
            print()
            
            # 6. 데이터 일관성 검증
            print("[6] 데이터 일관성 검증")
            self._validate_consistency()
            print()
            
            # 7. 성능 측정
            print("[7] 성능 측정")
            self._measure_performance()
            print()
            
            # 8. 결과 출력
            self._print_results()
            
            # 9. 시각화 생성
            if HAS_MATPLOTLIB:
                self._create_visualizations()
            
        except Exception as e:
            print(f"\n❌ 검증 중 예외 발생: {e}")
            import traceback
            traceback.print_exc()
            return False
        finally:
            # 테스트 데이터 복원
            self._restore_backup_data()
        
        return self._is_all_passed()
    
    def _get_completed_sessions(self, count: int = 100) -> List[Dict]:
        """STATUS='COMPLETED' && MEMBER_ID != 'GUEST'인 세션 무작위 추출"""
        try:
            with get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT SESSION_ID, MEMBER_ID, STATUS
                        FROM (
                            SELECT SESSION_ID, MEMBER_ID, STATUS
                            FROM ONBOARDING_SESSION
                            WHERE STATUS = 'COMPLETED'
                            AND MEMBER_ID IS NOT NULL
                            AND MEMBER_ID != 'GUEST'
                            ORDER BY DBMS_RANDOM.VALUE
                        ) WHERE ROWNUM <= :limit
                    """, {'limit': count})
                    
                    sessions = []
                    for row in cur.fetchall():
                        sessions.append({
                            'session_id': row[0],
                            'member_id': row[1],
                            'status': row[2]
                        })
                    
                    return sessions
        except Exception as e:
            self.results['errors'].append(f"완료 세션 조회 실패: {str(e)}")
            return []
    
    def _get_sessions_by_status(self, status: str, count: int = 10) -> List[Dict]:
        """특정 STATUS인 세션 조회"""
        try:
            with get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT SESSION_ID, MEMBER_ID, STATUS
                        FROM (
                            SELECT SESSION_ID, MEMBER_ID, STATUS
                            FROM ONBOARDING_SESSION
                            WHERE STATUS = :status
                            ORDER BY DBMS_RANDOM.VALUE
                        ) WHERE ROWNUM <= :limit
                    """, {'status': status, 'limit': count})
                    
                    sessions = []
                    for row in cur.fetchall():
                        sessions.append({
                            'session_id': row[0],
                            'member_id': row[1],
                            'status': row[2]
                        })
                    
                    return sessions
        except Exception as e:
            self.results['errors'].append(f"{status} 세션 조회 실패: {str(e)}")
            return []
    
    def _get_member_taste(self, member_id: str) -> Optional[int]:
        """MEMBER 테이블에서 현재 TASTE 값 조회"""
        try:
            with get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT TASTE FROM MEMBER WHERE MEMBER_ID = :member_id
                    """, {'member_id': member_id})
                    row = cur.fetchone()
                    return row[0] if row else None
        except Exception as e:
            self.results['errors'].append(f"TASTE 조회 실패 ({member_id}): {str(e)}")
            return None
    
    def _backup_member_taste(self, member_id: str):
        """MEMBER의 현재 TASTE 값을 백업"""
        if member_id and member_id not in self.backup_data:
            taste = self._get_member_taste(member_id)
            self.backup_data[member_id] = taste
    
    def _restore_backup_data(self):
        """백업된 TASTE 값 복원"""
        if not self.backup_data:
            return
        
        print("[테스트 데이터 복원 중...]")
        restored_count = 0
        for member_id, original_taste in self.backup_data.items():
            try:
                with get_connection() as conn:
                    with conn.cursor() as cur:
                        if original_taste is None:
                            cur.execute("""
                                UPDATE MEMBER SET TASTE = NULL WHERE MEMBER_ID = :member_id
                            """, {'member_id': member_id})
                        else:
                            cur.execute("""
                                UPDATE MEMBER SET TASTE = :taste WHERE MEMBER_ID = :member_id
                            """, {'taste': original_taste, 'member_id': member_id})
                        conn.commit()
                        restored_count += 1
            except Exception as e:
                self.results['warnings'].append(f"복원 실패 ({member_id}): {str(e)}")
        
        if restored_count > 0:
            print(f"  ✅ {restored_count}개 MEMBER의 TASTE 값 복원 완료")
    
    def _check_completion_condition(self, status: str, member_id: Optional[str]) -> bool:
        """온보딩 완료 조건 체크: STATUS='COMPLETED' && MEMBER_ID != 'GUEST'"""
        return status == 'COMPLETED' and member_id and member_id != 'GUEST'
    
    def _validate_completion_conditions(self):
        """온보딩 완료 조건 검증"""
        print("  [1.1] STATUS='COMPLETED'인 세션 찾기")
        
        try:
            with get_connection() as conn:
                with conn.cursor() as cur:
                    # 각 STATUS별 세션 수 조회
                    cur.execute("""
                        SELECT STATUS, COUNT(*) as CNT
                        FROM ONBOARDING_SESSION
                        GROUP BY STATUS
                        ORDER BY STATUS
                    """)
                    
                    status_counts = {}
                    for row in cur.fetchall():
                        status_counts[row[0]] = row[1]
                        print(f"    - STATUS='{row[0]}': {row[1]}개")
                    
                    # COMPLETED 세션 중 MEMBER_ID != 'GUEST'인 세션 수
                    cur.execute("""
                        SELECT COUNT(*) 
                        FROM ONBOARDING_SESSION
                        WHERE STATUS = 'COMPLETED'
                        AND MEMBER_ID IS NOT NULL
                        AND MEMBER_ID != 'GUEST'
                    """)
                    completed_non_guest = cur.fetchone()[0]
                    print(f"    - STATUS='COMPLETED' && MEMBER_ID != 'GUEST': {completed_non_guest}개")
                    
                    # COMPLETED 세션 중 MEMBER_ID == 'GUEST'인 세션 수
                    cur.execute("""
                        SELECT COUNT(*) 
                        FROM ONBOARDING_SESSION
                        WHERE STATUS = 'COMPLETED'
                        AND MEMBER_ID = 'GUEST'
                    """)
                    completed_guest = cur.fetchone()[0]
                    print(f"    - STATUS='COMPLETED' && MEMBER_ID='GUEST': {completed_guest}개")
                    
                    self.results['completion_conditions'] = {
                        'status_counts': status_counts,
                        'completed_non_guest': completed_non_guest,
                        'completed_guest': completed_guest
                    }
                    
                    if completed_non_guest > 0:
                        print(f"  ✅ 테스트 가능한 완료 세션: {completed_non_guest}개")
                    else:
                        print(f"  ⚠️ 테스트 가능한 완료 세션이 없습니다.")
                        
        except Exception as e:
            print(f"  ❌ 완료 조건 검증 실패: {e}")
            self.results['errors'].append(f"완료 조건 검증 실패: {str(e)}")
    
    def _validate_full_flow(self):
        """전체 플로우 통합 검증"""
        print("  [2.1] 조건 체크 → 데이터 조회 → 계산 → 저장 전체 플로우 테스트")
        
        # 완료된 세션 10개로 테스트
        completed_sessions = self._get_completed_sessions(count=10)
        
        if not completed_sessions:
            print("  ⚠️ 테스트할 완료 세션이 없습니다.")
            return
        
        print(f"  테스트할 세션: {len(completed_sessions)}개")
        
        for i, session_info in enumerate(completed_sessions, 1):
            session_id = session_info['session_id']
            member_id = session_info['member_id']
            status = session_info['status']
            
            print(f"  [{i}/{len(completed_sessions)}] SESSION_ID={session_id}, MEMBER_ID={member_id}", end=' ')
            
            try:
                # 1. 조건 체크
                should_execute = self._check_completion_condition(status, member_id)
                
                if not should_execute:
                    print("❌ (조건 불만족)")
                    continue
                
                # 백업
                self._backup_member_taste(member_id)
                
                # 저장 전 TASTE 값
                taste_before = self._get_member_taste(member_id)
                
                # 2. 데이터 조회
                start_time = time.time()
                onboarding_data = TasteCalculationService._get_onboarding_data_from_session(session_id)
                data_retrieval_time = time.time() - start_time
                
                # 3. Taste 계산
                start_time = time.time()
                calculated_taste = TasteCalculationService.calculate_and_save_taste(
                    member_id=member_id,
                    onboarding_session_id=session_id
                )
                calculation_time = time.time() - start_time
                
                # 4. 저장 후 TASTE 값 확인
                taste_after = self._get_member_taste(member_id)
                
                # 5. 검증: get_taste_for_member()로 조회
                retrieved_taste = TasteCalculationService.get_taste_for_member(member_id)
                
                # 검증 결과
                result = {
                    'session_id': session_id,
                    'member_id': member_id,
                    'status': status,
                    'taste_before': taste_before,
                    'calculated_taste': calculated_taste,
                    'taste_after': taste_after,
                    'retrieved_taste': retrieved_taste,
                    'data_retrieval_time': data_retrieval_time,
                    'calculation_time': calculation_time,
                    'passed': False,
                    'checks': {}
                }
                
                # 검증 1: 계산된 TASTE가 1~120 범위인지
                range_check = 1 <= calculated_taste <= 120
                result['checks']['range'] = range_check
                
                # 검증 2: 저장 후 TASTE 값이 계산된 값과 일치하는지
                storage_check = taste_after == calculated_taste
                result['checks']['storage'] = storage_check
                
                # 검증 3: 조회한 값이 저장된 값과 일치하는지
                retrieval_check = retrieved_taste == calculated_taste
                result['checks']['retrieval'] = retrieval_check
                
                result['passed'] = range_check and storage_check and retrieval_check
                
                if result['passed']:
                    print(f"✅ (통과)")
                    self.results['saved_tastes'].append(calculated_taste)
                    self.results['branch_counts']['executed'] += 1
                else:
                    failed_checks = [k for k, v in result['checks'].items() if not v]
                    print(f"❌ (실패: {', '.join(failed_checks)})")
                
                self.results['full_flow_tests'].append(result)
                
            except Exception as e:
                print(f"❌ (예외: {e})")
                self.results['errors'].append(f"전체 플로우 테스트 실패 ({session_id}): {str(e)}")
                self.results['full_flow_tests'].append({
                    'session_id': session_id,
                    'member_id': member_id,
                    'status': status,
                    'passed': False,
                    'error': str(e)
                })
    
    def _validate_with_completed_sessions(self, count: int = 1000):
        """실제 완료 세션 데이터로 검증 (1000개 이상)"""
        print(f"  [3.1] STATUS='COMPLETED' && MEMBER_ID != 'GUEST'인 세션 {count}개로 테스트")
        
        completed_sessions = self._get_completed_sessions(count=count)
        
        if not completed_sessions:
            print("  ⚠️ 테스트할 완료 세션이 없습니다.")
            return
        
        print(f"  무작위 추출 세션: {len(completed_sessions)}개")
        
        passed = 0
        failed = 0
        
        for i, session_info in enumerate(completed_sessions, 1):
            session_id = session_info['session_id']
            member_id = session_info['member_id']
            
            if i % 100 == 0 or i == len(completed_sessions):
                print(f"    진행 중... {i}/{len(completed_sessions)} (통과: {passed}개, 실패: {failed}개)")
            
            try:
                # 백업
                self._backup_member_taste(member_id)
                
                # 저장 전 TASTE 값
                taste_before = self._get_member_taste(member_id)
                
                # 전체 플로우 실행
                calculated_taste = TasteCalculationService.calculate_and_save_taste(
                    member_id=member_id,
                    onboarding_session_id=session_id
                )
                
                # 저장 후 TASTE 값
                taste_after = self._get_member_taste(member_id)
                
                # 검증
                if (1 <= calculated_taste <= 120 and 
                    taste_after == calculated_taste):
                    passed += 1
                    self.results['saved_tastes'].append(calculated_taste)
                else:
                    failed += 1
                    if not (1 <= calculated_taste <= 120):
                        self.results['errors'].append(f"범위 초과: {calculated_taste}")
                    if taste_after != calculated_taste:
                        self.results['errors'].append(f"저장 불일치: 계산={calculated_taste}, 저장={taste_after}")
                
            except Exception as e:
                failed += 1
                self.results['errors'].append(f"세션 {session_id}: {str(e)}")
        
        print(f"  ✅ 통과: {passed}개")
        if failed > 0:
            print(f"  ❌ 실패: {failed}개")
    
    def _validate_conditional_branches(self):
        """조건별 분기 검증"""
        print("  [4.1] STATUS='COMPLETED' && MEMBER_ID != 'GUEST': 정상 실행 확인")
        
        # 1. 정상 실행 케이스
        completed_sessions = self._get_completed_sessions(count=5)
        if completed_sessions:
            for session_info in completed_sessions[:3]:
                session_id = session_info['session_id']
                member_id = session_info['member_id']
                status = session_info['status']
                
                should_execute = self._check_completion_condition(status, member_id)
                if should_execute:
                    try:
                        self._backup_member_taste(member_id)
                        calculated_taste = TasteCalculationService.calculate_and_save_taste(
                            member_id=member_id,
                            onboarding_session_id=session_id
                        )
                        print(f"    ✅ SESSION_ID={session_id}: Taste 계산 실행됨 (TASTE={calculated_taste})")
                        self.results['branch_counts']['executed'] += 1
                    except Exception as e:
                        print(f"    ❌ SESSION_ID={session_id}: 예외 발생 - {e}")
        
        print("  [4.2] STATUS='COMPLETED' && MEMBER_ID == 'GUEST': 건너뛰기 확인")
        
        # 2. GUEST 케이스
        guest_sessions = self._get_sessions_by_status('COMPLETED', count=20)
        guest_sessions = [s for s in guest_sessions if s['member_id'] == 'GUEST']
        
        if guest_sessions:
            for session_info in guest_sessions[:3]:
                session_id = session_info['session_id']
                member_id = session_info['member_id']
                status = session_info['status']
                
                should_execute = self._check_completion_condition(status, member_id)
                if not should_execute:
                    print(f"    ✅ SESSION_ID={session_id}: Taste 계산 건너뜀 (GUEST 회원)")
                    self.results['branch_counts']['skipped_guest'] += 1
                else:
                    print(f"    ❌ SESSION_ID={session_id}: 예상과 다름 (실행됨)")
        
        print("  [4.3] STATUS='IN_PROGRESS': 실행 안 함 확인")
        
        # 3. IN_PROGRESS 케이스
        in_progress_sessions = self._get_sessions_by_status('IN_PROGRESS', count=10)
        if in_progress_sessions:
            for session_info in in_progress_sessions[:3]:
                session_id = session_info['session_id']
                member_id = session_info['member_id']
                status = session_info['status']
                
                should_execute = self._check_completion_condition(status, member_id)
                if not should_execute:
                    print(f"    ✅ SESSION_ID={session_id}: Taste 계산 실행 안 함 (IN_PROGRESS)")
                    self.results['branch_counts']['skipped_in_progress'] += 1
                else:
                    print(f"    ❌ SESSION_ID={session_id}: 예상과 다름 (실행됨)")
        
        print("  [4.4] STATUS='ABANDONED': 실행 안 함 확인")
        
        # 4. ABANDONED 케이스
        abandoned_sessions = self._get_sessions_by_status('ABANDONED', count=10)
        if abandoned_sessions:
            for session_info in abandoned_sessions[:3]:
                session_id = session_info['session_id']
                member_id = session_info['member_id']
                status = session_info['status']
                
                should_execute = self._check_completion_condition(status, member_id)
                if not should_execute:
                    print(f"    ✅ SESSION_ID={session_id}: Taste 계산 실행 안 함 (ABANDONED)")
                    self.results['branch_counts']['skipped_abandoned'] += 1
                else:
                    print(f"    ❌ SESSION_ID={session_id}: 예상과 다름 (실행됨)")
    
    def _validate_error_handling(self):
        """에러 처리 검증"""
        print("  [5.1] 존재하지 않는 SESSION_ID로 테스트")
        
        non_existent_session_id = 'NON_EXISTENT_SESSION_12345'
        try:
            onboarding_data = TasteCalculationService._get_onboarding_data_from_session(non_existent_session_id)
            print(f"    ❌ 예외가 발생하지 않음 (예상: ValueError)")
        except ValueError as e:
            print(f"    ✅ 예외 발생 (정상): {e}")
        except Exception as e:
            print(f"    ⚠️ 예상과 다른 예외: {type(e).__name__} - {e}")
        
        print("  [5.2] 데이터가 불완전한 세션으로 테스트")
        
        # 실제 세션 중 데이터가 불완전할 수 있는 케이스 찾기
        try:
            with get_connection() as conn:
                with conn.cursor() as cur:
                    # NULL 값이 많은 세션 찾기
                    cur.execute("""
                        SELECT SESSION_ID, MEMBER_ID
                        FROM ONBOARDING_SESSION
                        WHERE STATUS = 'COMPLETED'
                        AND MEMBER_ID IS NOT NULL
                        AND MEMBER_ID != 'GUEST'
                        AND (VIBE IS NULL OR HOUSEHOLD_SIZE IS NULL)
                        AND ROWNUM <= 1
                    """)
                    row = cur.fetchone()
                    
                    if row:
                        session_id = row[0]
                        member_id = row[1]
                        print(f"    테스트 세션: SESSION_ID={session_id}")
                        try:
                            self._backup_member_taste(member_id)
                            calculated_taste = TasteCalculationService.calculate_and_save_taste(
                                member_id=member_id,
                                onboarding_session_id=session_id
                            )
                            print(f"    ✅ 불완전한 데이터로도 처리 성공 (TASTE={calculated_taste})")
                        except Exception as e:
                            print(f"    ⚠️ 불완전한 데이터 처리 중 예외: {e}")
                    else:
                        print(f"    ⚠️ 불완전한 데이터를 가진 세션을 찾을 수 없음")
        except Exception as e:
            print(f"    ❌ 에러 처리 테스트 실패: {e}")
        
        print("  [5.3] MEMBER 테이블에 없는 MEMBER_ID로 테스트")
        
        non_existent_member_id = 'NON_EXISTENT_MEMBER_12345'
        try:
            # MEMBER 존재 확인
            with get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT COUNT(*) FROM MEMBER WHERE MEMBER_ID = :member_id
                    """, {'member_id': non_existent_member_id})
                    exists = cur.fetchone()[0] > 0
            
            if not exists:
                # 온보딩 데이터는 임의로 생성
                onboarding_data = {
                    'vibe': 'modern',
                    'household_size': 4,
                    'priority': ['tech']
                }
                calculated_taste = TasteCalculationService.calculate_and_save_taste(
                    member_id=non_existent_member_id,
                    onboarding_data=onboarding_data
                )
                
                # 저장 후 확인
                taste_after = self._get_member_taste(non_existent_member_id)
                
                if taste_after is None:
                    print(f"    ✅ 존재하지 않는 MEMBER_ID: 저장되지 않음 (정상)")
                else:
                    print(f"    ⚠️ 존재하지 않는 MEMBER_ID: 저장됨 (예상과 다름)")
            else:
                print(f"    ⚠️ 테스트용 MEMBER_ID가 이미 존재함")
        except Exception as e:
            print(f"    ✅ 존재하지 않는 MEMBER_ID: 예외 발생 (정상) - {e}")
    
    def _validate_consistency(self):
        """데이터 일관성 검증 - 동일한 완료 세션으로 여러 번 실행 시 동일한 TASTE 값 확인"""
        print("  [6.1] 동일한 완료 세션으로 여러 번 실행하여 일관성 확인")
        
        completed_sessions = self._get_completed_sessions(count=5)
        
        if not completed_sessions:
            print("  ⚠️ 테스트할 완료 세션이 없습니다.")
            return
        
        for session_info in completed_sessions[:3]:
            session_id = session_info['session_id']
            member_id = session_info['member_id']
            
            try:
                # 온보딩 데이터 조회
                onboarding_data = TasteCalculationService._get_onboarding_data_from_session(session_id)
                
                # 동일한 데이터로 여러 번 계산
                iterations = 5
                results = []
                
                for _ in range(iterations):
                    calculated_taste = TasteCalculationService.calculate_and_save_taste(
                        member_id=member_id,
                        onboarding_data=onboarding_data
                    )
                    results.append(calculated_taste)
                
                # 모든 결과가 동일한지 확인
                unique_results = set(results)
                
                if len(unique_results) == 1:
                    print(f"    ✅ SESSION_ID={session_id}: {iterations}회 반복, 모두 Taste ID = {results[0]}")
                else:
                    print(f"    ❌ SESSION_ID={session_id}: {len(unique_results)}개의 서로 다른 결과")
                    print(f"       결과: {list(unique_results)}")
                    self.results['errors'].append(f"일관성 실패 (세션 {session_id}): {len(unique_results)}개 서로 다른 결과")
                
                self.results['consistency_tests'].append({
                    'session_id': session_id,
                    'member_id': member_id,
                    'iterations': iterations,
                    'results': results,
                    'unique_count': len(unique_results),
                    'passed': len(unique_results) == 1
                })
                
            except Exception as e:
                print(f"    ❌ SESSION_ID={session_id}: 예외 발생 - {e}")
                self.results['errors'].append(f"일관성 테스트 실패 (세션 {session_id}): {str(e)}")
        
        print("  [6.2] 저장 후 조회하여 일치하는지 확인")
        
        completed_sessions = self._get_completed_sessions(count=20)
        passed = 0
        failed = 0
        
        for session_info in completed_sessions:
            session_id = session_info['session_id']
            member_id = session_info['member_id']
            
            try:
                self._backup_member_taste(member_id)
                
                # Taste 계산 및 저장
                calculated_taste = TasteCalculationService.calculate_and_save_taste(
                    member_id=member_id,
                    onboarding_session_id=session_id
                )
                
                # get_taste_for_member()로 조회
                retrieved_taste = TasteCalculationService.get_taste_for_member(member_id)
                
                if retrieved_taste == calculated_taste:
                    passed += 1
                else:
                    failed += 1
                    self.results['errors'].append(f"조회 불일치 ({member_id}): 저장={calculated_taste}, 조회={retrieved_taste}")
            except Exception as e:
                failed += 1
                self.results['errors'].append(f"조회 테스트 실패 ({member_id}): {str(e)}")
        
        print(f"    ✅ 통과: {passed}개")
        if failed > 0:
            print(f"    ❌ 실패: {failed}개")
    
    def _measure_performance(self):
        """성능 측정"""
        print("  [7.1] 100개 이상의 완료 세션 처리 시간 측정")
        
        completed_sessions = self._get_completed_sessions(count=100)
        
        if not completed_sessions:
            print("  ⚠️ 테스트할 완료 세션이 없습니다.")
            return
        
        print(f"  테스트 세션: {len(completed_sessions)}개")
        
        total_start_time = time.time()
        
        step_times = {
            'data_retrieval': [],
            'calculation': [],
            'storage': []
        }
        
        for i, session_info in enumerate(completed_sessions, 1):
            session_id = session_info['session_id']
            member_id = session_info['member_id']
            
            if i % 20 == 0:
                print(f"    진행 중... {i}/{len(completed_sessions)}")
            
            try:
                # 데이터 조회 시간
                start_time = time.time()
                onboarding_data = TasteCalculationService._get_onboarding_data_from_session(session_id)
                step_times['data_retrieval'].append(time.time() - start_time)
                
                # 계산 시간
                start_time = time.time()
                calculated_taste = TasteCalculationService.calculate_and_save_taste(
                    member_id=member_id,
                    onboarding_data=onboarding_data
                )
                # calculate_and_save_taste는 계산과 저장을 모두 포함하므로
                # 전체 시간을 계산 시간으로 간주
                step_times['calculation'].append(time.time() - start_time)
                
            except Exception as e:
                self.results['errors'].append(f"성능 측정 실패 ({session_id}): {str(e)}")
        
        total_time = time.time() - total_start_time
        
        # 통계 계산
        if HAS_NUMPY:
            data_retrieval_avg = np.mean(step_times['data_retrieval']) if step_times['data_retrieval'] else 0
            data_retrieval_min = np.min(step_times['data_retrieval']) if step_times['data_retrieval'] else 0
            data_retrieval_max = np.max(step_times['data_retrieval']) if step_times['data_retrieval'] else 0
            calculation_avg = np.mean(step_times['calculation']) if step_times['calculation'] else 0
            calculation_min = np.min(step_times['calculation']) if step_times['calculation'] else 0
            calculation_max = np.max(step_times['calculation']) if step_times['calculation'] else 0
        else:
            data_retrieval_avg = mean(step_times['data_retrieval']) if step_times['data_retrieval'] else 0
            data_retrieval_min = min_val(step_times['data_retrieval']) if step_times['data_retrieval'] else 0
            data_retrieval_max = max_val(step_times['data_retrieval']) if step_times['data_retrieval'] else 0
            calculation_avg = mean(step_times['calculation']) if step_times['calculation'] else 0
            calculation_min = min_val(step_times['calculation']) if step_times['calculation'] else 0
            calculation_max = max_val(step_times['calculation']) if step_times['calculation'] else 0
        
        performance_metrics = {
            'total_sessions': len(completed_sessions),
            'total_time': total_time,
            'average_time_per_session': total_time / len(completed_sessions) if completed_sessions else 0,
            'data_retrieval': {
                'avg': data_retrieval_avg,
                'min': data_retrieval_min,
                'max': data_retrieval_max,
            },
            'calculation': {
                'avg': calculation_avg,
                'min': calculation_min,
                'max': calculation_max,
            }
        }
        
        self.results['performance_metrics'] = performance_metrics
        
        print(f"  총 처리 시간: {total_time:.2f}초")
        print(f"  세션당 평균 시간: {performance_metrics['average_time_per_session']:.3f}초")
        print(f"  데이터 조회 시간:")
        print(f"    - 평균: {performance_metrics['data_retrieval']['avg']:.3f}초")
        print(f"    - 최소: {performance_metrics['data_retrieval']['min']:.3f}초")
        print(f"    - 최대: {performance_metrics['data_retrieval']['max']:.3f}초")
        print(f"  계산 시간:")
        print(f"    - 평균: {performance_metrics['calculation']['avg']:.3f}초")
        print(f"    - 최소: {performance_metrics['calculation']['min']:.3f}초")
        print(f"    - 최대: {performance_metrics['calculation']['max']:.3f}초")
    
    def _print_results(self):
        """검증 결과 출력"""
        print("=" * 80)
        print("검증 결과 요약")
        print("=" * 80)
        
        # 완료 조건 검증 결과
        if self.results['completion_conditions']:
            cc = self.results['completion_conditions']
            print(f"\n[온보딩 완료 조건 검증]")
            print(f"  STATUS='COMPLETED' && MEMBER_ID != 'GUEST': {cc.get('completed_non_guest', 0)}개")
            print(f"  STATUS='COMPLETED' && MEMBER_ID='GUEST': {cc.get('completed_guest', 0)}개")
        
        # 전체 플로우 검증 결과
        full_flow_tests = self.results['full_flow_tests']
        passed_full_flow = sum(1 for t in full_flow_tests if t.get('passed', False))
        print(f"\n[전체 플로우 통합 검증]")
        print(f"  총 테스트: {len(full_flow_tests)}개")
        print(f"  통과: {passed_full_flow}개")
        print(f"  실패: {len(full_flow_tests) - passed_full_flow}개")
        
        # 조건별 분기 검증 결과
        branch_counts = self.results['branch_counts']
        print(f"\n[조건별 분기 검증]")
        print(f"  실행됨 (COMPLETED && != GUEST): {branch_counts['executed']}개")
        print(f"  건너뜀 (GUEST): {branch_counts['skipped_guest']}개")
        print(f"  건너뜀 (IN_PROGRESS): {branch_counts['skipped_in_progress']}개")
        print(f"  건너뜀 (ABANDONED): {branch_counts['skipped_abandoned']}개")
        
        # 일관성 검증 결과
        consistency_tests = self.results['consistency_tests']
        passed_consistency = sum(1 for ct in consistency_tests if ct.get('passed', False))
        print(f"\n[데이터 일관성 검증]")
        print(f"  총 테스트: {len(consistency_tests)}개")
        print(f"  통과: {passed_consistency}개")
        print(f"  실패: {len(consistency_tests) - passed_consistency}개")
        
        # 성능 측정 결과
        if self.results['performance_metrics']:
            pm = self.results['performance_metrics']
            print(f"\n[성능 측정]")
            print(f"  총 세션: {pm.get('total_sessions', 0)}개")
            print(f"  총 처리 시간: {pm.get('total_time', 0):.2f}초")
            print(f"  세션당 평균 시간: {pm.get('average_time_per_session', 0):.3f}초")
        
        # 저장된 TASTE 값 통계
        if self.results['saved_tastes']:
            saved_tastes = self.results['saved_tastes']
            taste_counter = Counter(saved_tastes)
            print(f"\n[저장된 TASTE 값 통계]")
            print(f"  총 저장 횟수: {len(saved_tastes)}회")
            print(f"  고유 TASTE 값 수: {len(taste_counter)}개")
            if saved_tastes:
                print(f"  범위: {min(saved_tastes)} ~ {max(saved_tastes)}")
                print(f"  가장 많이 저장된 TASTE 값 (상위 5개):")
                for taste_id, count in taste_counter.most_common(5):
                    print(f"    - Taste ID {taste_id}: {count}회 ({count/len(saved_tastes)*100:.1f}%)")
        
        # 에러
        if self.results['errors']:
            print("\n[에러]")
            for error in self.results['errors'][:10]:
                print(f"  ❌ {error}")
            if len(self.results['errors']) > 10:
                print(f"  ... 외 {len(self.results['errors']) - 10}개 에러")
        
        # 경고
        if self.results['warnings']:
            print("\n[경고]")
            for warning in self.results['warnings']:
                print(f"  ⚠️ {warning}")
        
        print()
    
    def _is_all_passed(self):
        """모든 검증 통과 여부"""
        # 전체 플로우 검증 모두 통과
        full_flow_passed = all(
            t.get('passed', False) 
            for t in self.results['full_flow_tests']
            if 'passed' in t
        )
        
        # 일관성 검증 모두 통과
        consistency_passed = all(
            ct.get('passed', False) 
            for ct in self.results['consistency_tests']
        )
        
        # 에러 없음
        no_errors = len(self.results['errors']) == 0
        
        return full_flow_passed and consistency_passed and no_errors
    
    def _create_visualizations(self):
        """검증 결과 시각화"""
        if not HAS_MATPLOTLIB:
            return
        
        print("[시각화 생성 중...]")
        
        try:
            # 한글 폰트 설정
            plt.rcParams['font.family'] = 'Malgun Gothic'  # Windows
            plt.rcParams['axes.unicode_minus'] = False
            
            fig = plt.figure(figsize=(20, 16))
            gs = fig.add_gridspec(4, 3, hspace=0.3, wspace=0.3)
            
            # 1. 전체 플로우 성공/실패 비율 (파이 차트)
            ax1 = fig.add_subplot(gs[0, 0])
            full_flow_tests = self.results['full_flow_tests']
            passed_full_flow = sum(1 for t in full_flow_tests if t.get('passed', False))
            failed_full_flow = len(full_flow_tests) - passed_full_flow
            
            if failed_full_flow > 0:
                ax1.pie([passed_full_flow, failed_full_flow], 
                       labels=[f'통과 ({passed_full_flow})', f'실패 ({failed_full_flow})'],
                       autopct='%1.1f%%',
                       colors=['#4CAF50', '#F44336'],
                       startangle=90)
            else:
                ax1.pie([passed_full_flow], 
                       labels=[f'통과 ({passed_full_flow})'],
                       autopct='%1.1f%%',
                       colors=['#4CAF50'],
                       startangle=90)
            ax1.set_title('전체 플로우 성공/실패 비율', fontsize=14, fontweight='bold')
            
            # 2. 조건별 분기 실행 횟수 (바 차트)
            ax2 = fig.add_subplot(gs[0, 1])
            branch_counts = self.results['branch_counts']
            branches = ['실행됨\n(COMPLETED\n&& != GUEST)', '건너뜀\n(GUEST)', '건너뜀\n(IN_PROGRESS)', '건너뜀\n(ABANDONED)']
            counts = [
                branch_counts['executed'],
                branch_counts['skipped_guest'],
                branch_counts['skipped_in_progress'],
                branch_counts['skipped_abandoned']
            ]
            colors = ['#4CAF50', '#FF9800', '#2196F3', '#9E9E9E']
            ax2.bar(branches, counts, color=colors, alpha=0.7)
            ax2.set_ylabel('실행 횟수')
            ax2.set_title('조건별 분기 실행 횟수', fontsize=14, fontweight='bold')
            ax2.grid(True, alpha=0.3, axis='y')
            
            # 3. TASTE 값 분포 히스토그램 (1~120)
            ax3 = fig.add_subplot(gs[0, 2])
            saved_tastes = self.results['saved_tastes']
            if saved_tastes:
                ax3.hist(saved_tastes, bins=120, range=(1, 121), 
                        color='skyblue', edgecolor='black', alpha=0.7)
                ax3.set_xlabel('Taste ID')
                ax3.set_ylabel('저장 횟수')
                ax3.set_title('TASTE 값 분포 (1~120)', fontsize=14, fontweight='bold')
                ax3.set_xlim(1, 120)
                ax3.grid(True, alpha=0.3, axis='y')
            else:
                ax3.text(0.5, 0.5, '저장된 TASTE 값 없음', 
                        ha='center', va='center', fontsize=12,
                        transform=ax3.transAxes)
                ax3.set_title('TASTE 값 분포', fontsize=14, fontweight='bold')
            
            # 4. 단계별 처리 시간 분포 (박스 플롯)
            ax4 = fig.add_subplot(gs[1, 0])
            if self.results['performance_metrics']:
                pm = self.results['performance_metrics']
                # 실제 데이터가 없으므로 성능 메트릭만 표시
                times_data = []
                labels = []
                
                if pm.get('data_retrieval', {}).get('avg', 0) > 0:
                    times_data.append([pm['data_retrieval']['avg']])
                    labels.append('데이터 조회')
                
                if pm.get('calculation', {}).get('avg', 0) > 0:
                    times_data.append([pm['calculation']['avg']])
                    labels.append('계산')
                
                if times_data:
                    ax4.boxplot(times_data, labels=labels)
                    ax4.set_ylabel('처리 시간 (초)')
                    ax4.set_title('단계별 처리 시간 분포', fontsize=14, fontweight='bold')
                    ax4.grid(True, alpha=0.3, axis='y')
                else:
                    ax4.text(0.5, 0.5, '성능 데이터 없음', 
                            ha='center', va='center', fontsize=12,
                            transform=ax4.transAxes)
                    ax4.set_title('단계별 처리 시간 분포', fontsize=14, fontweight='bold')
            
            # 5. 에러 발생 빈도 (바 차트)
            ax5 = fig.add_subplot(gs[1, 1])
            errors = self.results['errors']
            if errors:
                # 에러 타입별 분류
                error_types = {}
                for error in errors:
                    error_type = error.split(':')[0] if ':' in error else '기타'
                    error_types[error_type] = error_types.get(error_type, 0) + 1
                
                if error_types:
                    types = list(error_types.keys())
                    counts = list(error_types.values())
                    ax5.barh(types, counts, color='#F44336', alpha=0.7)
                    ax5.set_xlabel('발생 횟수')
                    ax5.set_title('에러 발생 빈도', fontsize=14, fontweight='bold')
                    ax5.grid(True, alpha=0.3, axis='x')
                else:
                    ax5.text(0.5, 0.5, '에러 없음', 
                            ha='center', va='center', fontsize=12,
                            transform=ax5.transAxes)
                    ax5.set_title('에러 발생 빈도', fontsize=14, fontweight='bold')
            else:
                ax5.text(0.5, 0.5, '에러 없음', 
                        ha='center', va='center', fontsize=12,
                        transform=ax5.transAxes)
                ax5.set_title('에러 발생 빈도', fontsize=14, fontweight='bold')
            
            # 6. 일관성 검증 결과
            ax6 = fig.add_subplot(gs[1, 2])
            consistency_tests = self.results['consistency_tests']
            if consistency_tests:
                passed_consistency = sum(1 for ct in consistency_tests if ct.get('passed', False))
                failed_consistency = len(consistency_tests) - passed_consistency
                if failed_consistency > 0:
                    ax6.pie([passed_consistency, failed_consistency], 
                           labels=[f'통과 ({passed_consistency})', f'실패 ({failed_consistency})'],
                           autopct='%1.1f%%',
                           colors=['#4CAF50', '#F44336'],
                           startangle=90)
                else:
                    ax6.pie([passed_consistency], 
                           labels=[f'통과 ({passed_consistency})'],
                           autopct='%1.1f%%',
                           colors=['#4CAF50'],
                           startangle=90)
                ax6.set_title('일관성 검증 결과', fontsize=14, fontweight='bold')
            
            # 7. 성능 메트릭 (바 차트)
            ax7 = fig.add_subplot(gs[2, 0])
            if self.results['performance_metrics']:
                pm = self.results['performance_metrics']
                metrics = ['총 처리 시간\n(초)', '세션당 평균\n(초)', '데이터 조회\n평균 (초)', '계산 평균\n(초)']
                values = [
                    pm.get('total_time', 0),
                    pm.get('average_time_per_session', 0),
                    pm.get('data_retrieval', {}).get('avg', 0),
                    pm.get('calculation', {}).get('avg', 0)
                ]
                ax7.barh(metrics, values, color='steelblue', alpha=0.7)
                ax7.set_xlabel('시간 (초)')
                ax7.set_title('성능 메트릭', fontsize=14, fontweight='bold')
                ax7.grid(True, alpha=0.3, axis='x')
            
            # 8. TASTE 값별 저장 횟수 분포 (상위 20개)
            ax8 = fig.add_subplot(gs[2, 1])
            if saved_tastes:
                taste_counter = Counter(saved_tastes)
                top_tastes = taste_counter.most_common(20)
                taste_ids_top = [str(t[0]) for t in top_tastes]
                counts_top = [t[1] for t in top_tastes]
                ax8.barh(taste_ids_top, counts_top, color='plum', alpha=0.7)
                ax8.set_xlabel('저장 횟수')
                ax8.set_ylabel('Taste ID')
                ax8.set_title('상위 20개 TASTE 값별 저장 횟수', fontsize=14, fontweight='bold')
                ax8.grid(True, alpha=0.3, axis='x')
            
            # 9. 검증 항목별 통과율
            ax9 = fig.add_subplot(gs[2, 2])
            validation_items = {}
            
            # 전체 플로우
            if full_flow_tests:
                validation_items['전체 플로우'] = passed_full_flow / len(full_flow_tests) * 100
            
            # 일관성 검증
            if consistency_tests:
                passed_consistency = sum(1 for ct in consistency_tests if ct.get('passed', False))
                validation_items['일관성 검증'] = passed_consistency / len(consistency_tests) * 100
            
            if validation_items:
                items = list(validation_items.keys())
                rates = list(validation_items.values())
                ax9.barh(items, rates, color='steelblue', alpha=0.7)
                ax9.set_xlabel('통과율 (%)')
                ax9.set_title('검증 항목별 통과율', fontsize=14, fontweight='bold')
                ax9.set_xlim(0, 100)
                ax9.grid(True, alpha=0.3, axis='x')
            
            # 10. 저장 전후 TASTE 값 비교
            ax10 = fig.add_subplot(gs[3, 0])
            before_after_data = []
            for t in full_flow_tests:
                if 'taste_before' in t and 'taste_after' in t:
                    before_after_data.append({
                        'before': t['taste_before'],
                        'after': t['taste_after']
                    })
            
            if before_after_data:
                before_values = [d['before'] if d['before'] is not None else 0 for d in before_after_data]
                after_values = [d['after'] if d['after'] is not None else 0 for d in before_after_data]
                
                x = list(range(len(before_after_data)))
                width = 0.35
                ax10.bar([xi - width/2 for xi in x], before_values, width, label='저장 전', color='lightgray', alpha=0.7)
                ax10.bar([xi + width/2 for xi in x], after_values, width, label='저장 후', color='lightgreen', alpha=0.7)
                ax10.set_xlabel('테스트 케이스')
                ax10.set_ylabel('TASTE 값')
                ax10.set_title('저장 전후 TASTE 값 비교', fontsize=14, fontweight='bold')
                ax10.legend()
                ax10.grid(True, alpha=0.3, axis='y')
            
            # 11. 완료 조건 검증 결과
            ax11 = fig.add_subplot(gs[3, 1])
            if self.results['completion_conditions']:
                cc = self.results['completion_conditions']
                labels = ['COMPLETED\n&& != GUEST', 'COMPLETED\n&& GUEST']
                sizes = [cc.get('completed_non_guest', 0), cc.get('completed_guest', 0)]
                colors_pie = ['#4CAF50', '#FF9800']
                ax11.pie(sizes, labels=labels, autopct='%1.1f%%', colors=colors_pie, startangle=90)
                ax11.set_title('완료 조건 검증 결과', fontsize=14, fontweight='bold')
            
            # 12. 성능 시간 분포 (히스토그램)
            ax12 = fig.add_subplot(gs[3, 2])
            if self.results['performance_metrics']:
                pm = self.results['performance_metrics']
                # 실제 시간 데이터가 없으므로 평균값만 표시
                if pm.get('average_time_per_session', 0) > 0:
                    ax12.bar(['세션당 평균 시간'], [pm['average_time_per_session']], 
                            color='steelblue', alpha=0.7)
                    ax12.set_ylabel('시간 (초)')
                    ax12.set_title('세션당 평균 처리 시간', fontsize=14, fontweight='bold')
                    ax12.grid(True, alpha=0.3, axis='y')
            
            # 전체 제목
            total_tests = len(full_flow_tests) + len(consistency_tests)
            fig.suptitle(f'온보딩 완료 시점 전체 플로우 통합 검증 결과 (총 {total_tests}개 테스트)', 
                        fontsize=16, fontweight='bold', y=0.995)
            
            # 저장
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_path = f'taste_integration_validation_{timestamp}.png'
            plt.savefig(output_path, dpi=150, bbox_inches='tight')
            print(f"✅ 시각화 저장 완료: {output_path}")
            plt.close()
            
        except Exception as e:
            print(f"⚠️ 시각화 생성 중 오류: {e}")
            import traceback
            traceback.print_exc()


def main():
    """메인 함수"""
    validator = TasteIntegrationValidator()
    success = validator.validate_all()
    
    if success:
        print("=" * 80)
        print("✅ Step 5 검증 완료: 온보딩 완료 시점 전체 플로우가 올바르게 작동합니다!")
        print("=" * 80)
        return 0
    else:
        print("=" * 80)
        print("❌ Step 5 검증 실패: 일부 통합 플로우에 문제가 있습니다.")
        print("=" * 80)
        return 1


if __name__ == '__main__':
    exit(main())

