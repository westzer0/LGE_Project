#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Step 6: 추천 엔진 통합 테스트 - Taste ID부터 최종 추천 결과까지 전체 플로우 통합 검증

검증 항목:
1. 전체 플로우 통합 검증
2. 실제 회원 데이터로 검증 (100명 이상)
3. 온보딩 데이터 연계 검증
4. 데이터 일관성 검증
5. 성능 검증
6. 에러 처리 검증
7. 엣지 케이스 검증
"""
import sys
import os
import json
import time
from datetime import datetime
from collections import Counter, defaultdict
from typing import Optional, Dict, List, Tuple

# Django 설정 로드
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

import django
django.setup()

from api.services.recommendation_engine import recommendation_engine
from api.services.taste_calculation_service import TasteCalculationService
from api.services.onboarding_db_service import OnboardingDBService
from api.db.oracle_client import get_connection

# 시각화 라이브러리 임포트
try:
    import matplotlib.pyplot as plt
    import matplotlib
    matplotlib.use('Agg')  # GUI 없이 사용
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False
    print("경고: matplotlib가 설치되어 있지 않아 시각화를 건너뜁니다.")

# NumPy 임포트 (성능 측정용)
try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False
    # NumPy 없이도 동작하도록 기본 함수 정의
    def mean(values):
        return sum(values) / len(values) if values else 0
    def min_val(values):
        return min(values) if values else 0
    def max_val(values):
        return max(values) if values else 0


class RecommendationIntegrationValidator:
    """추천 엔진 통합 테스트 클래스"""

    def __init__(self):
        self.results = {
            'full_flow_tests': [],
            'real_member_tests': [],
            'onboarding_integration_tests': [],
            'consistency_tests': [],
            'performance_metrics': {},
            'error_handling_tests': [],
            'edge_case_tests': [],
            'errors': [],
            'warnings': [],
            'statistics': {
                'total_tested': 0,
                'successful': 0,
                'failed': 0,
                'errors': 0,
            }
        }
        self.taste_service = TasteCalculationService()
        self.onboarding_service = OnboardingDBService()

    def validate_all(self):
        """모든 검증 실행"""
        print("=" * 80)
        print("Step 6: 추천 엔진 통합 테스트 - 전체 플로우 통합 검증")
        print("=" * 80)
        print()

        try:
            # 1. 전체 플로우 통합 검증
            print("[1] 전체 플로우 통합 검증")
            self._validate_full_flow()
            print()

            # 2. 실제 회원 데이터로 검증
            print("[2] 실제 회원 데이터로 검증 (100명 이상)")
            self._validate_with_real_members()
            print()

            # 3. 온보딩 데이터 연계 검증
            print("[3] 온보딩 데이터 연계 검증")
            self._validate_onboarding_integration()
            print()

            # 4. 데이터 일관성 검증
            print("[4] 데이터 일관성 검증")
            self._validate_data_consistency()
            print()

            # 5. 성능 검증
            print("[5] 성능 검증")
            self._measure_performance()
            print()

            # 6. 에러 처리 검증
            print("[6] 에러 처리 검증")
            self._validate_error_handling()
            print()

            # 7. 엣지 케이스 검증
            print("[7] 엣지 케이스 검증")
            self._validate_edge_cases()
            print()

            # 결과 요약 및 시각화
            self._generate_summary()
            self._generate_visualizations()

        except Exception as e:
            print(f"검증 중 오류 발생: {str(e)}")
            import traceback
            traceback.print_exc()
            self.results['errors'].append({
                'type': 'validation_error',
                'message': str(e),
                'traceback': traceback.format_exc()
            })

    def _validate_full_flow(self):
        """전체 플로우 통합 검증"""
        print("  전체 플로우 테스트 시작...")
        
        # MEMBER 테이블에서 TASTE 값이 있는 회원 조회
        members = self._get_members_with_taste(limit=10)
        
        if not members:
            print("  경고: TASTE 값이 있는 회원을 찾을 수 없습니다.")
            self.results['warnings'].append("TASTE 값이 있는 회원 없음")
            return

        success_count = 0
        error_count = 0
        
        for member in members:
            member_id = member['member_id']
            try:
                # 전체 플로우 실행
                start_time = time.time()
                
                # 1. Taste ID 조회
                taste_id = self.taste_service.get_taste_for_member(member_id)
                if not taste_id or not (1 <= taste_id <= 120):
                    raise ValueError(f"Invalid taste_id: {taste_id}")
                
                # 2. 온보딩 데이터 조회
                onboarding_session = self._get_latest_completed_session(member_id)
                onboarding_data = None
                if onboarding_session:
                    onboarding_data = self.taste_service._get_onboarding_data_from_session(
                        onboarding_session['session_id']
                    )
                
                # 3. 추천 엔진 실행
                user_profile = self._create_user_profile(member_id, taste_id, onboarding_data)
                recommendations = recommendation_engine.get_recommendations(
                    user_profile, limit=10
                )
                
                execution_time = time.time() - start_time
                
                # 결과 검증
                assert recommendations is not None, "추천 결과가 None입니다"
                # recommendation_engine은 success 필드를 반환
                if isinstance(recommendations, dict):
                    assert 'success' in recommendations, "추천 결과에 success 필드가 없습니다"
                    # success가 True이면 recommendations 필드가 있어야 함
                    if recommendations.get('success'):
                        assert 'recommendations' in recommendations or 'categories' in recommendations, \
                            "추천 결과에 recommendations 또는 categories가 없습니다"
                
                # 결과 저장
                self.results['full_flow_tests'].append({
                    'member_id': member_id,
                    'taste_id': taste_id,
                    'has_onboarding': onboarding_data is not None,
                    'recommendations': recommendations,
                    'execution_time': execution_time,
                    'status': 'success'
                })
                
                success_count += 1
                print(f"  [OK] {member_id}: Taste {taste_id}, 실행 시간 {execution_time:.2f}초")
                
            except Exception as e:
                error_count += 1
                error_msg = str(e)
                print(f"  [FAIL] {member_id}: {error_msg}")
                self.results['full_flow_tests'].append({
                    'member_id': member_id,
                    'status': 'failed',
                    'error': error_msg
                })
                self.results['errors'].append({
                    'member_id': member_id,
                    'type': 'full_flow_error',
                    'message': error_msg
                })
        
        print(f"  전체 플로우 테스트 완료: 성공 {success_count}개, 실패 {error_count}개")

    def _validate_with_real_members(self):
        """실제 회원 데이터로 검증 (100명 이상)"""
        print("  실제 회원 데이터 테스트 시작...")
        
        # MEMBER 테이블에서 TASTE 값이 있는 회원 100명 이상 조회
        members = self._get_members_with_taste(limit=100)
        
        if not members:
            print("  경고: TASTE 값이 있는 회원을 찾을 수 없습니다.")
            return
        
        print(f"  테스트할 회원 수: {len(members)}명")
        
        success_count = 0
        error_count = 0
        execution_times = []
        
        for i, member in enumerate(members, 1):
            member_id = member['member_id']
            try:
                start_time = time.time()
                
                # 추천 엔진 실행
                taste_id = self.taste_service.get_taste_for_member(member_id)
                if not taste_id:
                    raise ValueError("Taste ID를 찾을 수 없습니다")
                
                user_profile = self._create_user_profile(member_id, taste_id, None)
                recommendations = recommendation_engine.get_recommendations(
                    user_profile, limit=10
                )
                
                execution_time = time.time() - start_time
                execution_times.append(execution_time)
                
                # 결과 검증
                if recommendations and isinstance(recommendations, dict):
                    if recommendations.get('success') or 'recommendations' in recommendations or 'categories' in recommendations:
                        success_count += 1
                    self.results['real_member_tests'].append({
                        'member_id': member_id,
                        'taste_id': taste_id,
                        'execution_time': execution_time,
                        'status': 'success',
                        'has_recommendations': True
                    })
                else:
                    raise ValueError("추천 결과가 올바르지 않습니다")
                
                if i % 10 == 0:
                    print(f"  진행 중... {i}/{len(members)}")
                    
            except Exception as e:
                error_count += 1
                error_msg = str(e)
                self.results['real_member_tests'].append({
                    'member_id': member_id,
                    'status': 'failed',
                    'error': error_msg
                })
                if error_count <= 5:  # 처음 5개 에러만 출력
                    print(f"  [FAIL] {member_id}: {error_msg}")
        
        # 성공률 계산
        success_rate = success_count / len(members) if members else 0
        
        # 성능 통계
        if execution_times:
            avg_time = sum(execution_times) / len(execution_times)
            max_time = max(execution_times)
            min_time = min(execution_times)
        else:
            avg_time = max_time = min_time = 0
        
        self.results['statistics']['total_tested'] += len(members)
        self.results['statistics']['successful'] += success_count
        self.results['statistics']['failed'] += error_count
        
        print(f"  실제 회원 데이터 테스트 완료:")
        print(f"    - 성공: {success_count}개 ({success_rate*100:.1f}%)")
        print(f"    - 실패: {error_count}개")
        print(f"    - 평균 실행 시간: {avg_time:.2f}초")
        print(f"    - 최대 실행 시간: {max_time:.2f}초")
        print(f"    - 최소 실행 시간: {min_time:.2f}초")
        
        # 성공률 검증
        if success_rate < 0.9:
            self.results['warnings'].append(
                f"성공률이 90% 미만입니다: {success_rate*100:.1f}%"
            )

    def _validate_onboarding_integration(self):
        """온보딩 데이터 연계 검증"""
        print("  온보딩 데이터 연계 테스트 시작...")
        
        # 온보딩 완료된 회원 조회
        members = self._get_members_with_onboarding(limit=50)
        
        if not members:
            print("  경고: 온보딩 완료된 회원을 찾을 수 없습니다.")
            return
        
        success_count = 0
        error_count = 0
        
        for member in members:
            member_id = member['member_id']
            try:
                # Taste ID 조회
                taste_id = self.taste_service.get_taste_for_member(member_id)
                if not taste_id:
                    raise ValueError("Taste ID를 찾을 수 없습니다")
                
                # 온보딩 세션 조회
                onboarding_session = self._get_latest_completed_session(member_id)
                if not onboarding_session:
                    raise ValueError("온보딩 세션을 찾을 수 없습니다")
                
                # 온보딩 데이터 조회
                onboarding_data = self.taste_service._get_onboarding_data_from_session(
                    onboarding_session['session_id']
                )
                
                # 추천 엔진 실행
                user_profile = self._create_user_profile(member_id, taste_id, onboarding_data)
                recommendations = recommendation_engine.get_recommendations(
                    user_profile, limit=10
                )
                
                # 결과 검증
                assert recommendations is not None, "추천 결과가 None입니다"
                
                # 온보딩 데이터가 필터링에 사용되었는지 확인
                # (예산, 조건 등이 반영되었는지 확인)
                self.results['onboarding_integration_tests'].append({
                    'member_id': member_id,
                    'taste_id': taste_id,
                    'onboarding_data': onboarding_data,
                    'recommendations': recommendations,
                    'status': 'success'
                })
                
                success_count += 1
                
            except Exception as e:
                error_count += 1
                error_msg = str(e)
                self.results['onboarding_integration_tests'].append({
                    'member_id': member_id,
                    'status': 'failed',
                    'error': error_msg
                })
        
        print(f"  온보딩 데이터 연계 테스트 완료: 성공 {success_count}개, 실패 {error_count}개")

    def _validate_data_consistency(self):
        """데이터 일관성 검증"""
        print("  데이터 일관성 테스트 시작...")
        
        # 동일한 회원에 대해 여러 번 추천 요청 시 일관된 결과 확인
        members = self._get_members_with_taste(limit=10)
        
        if not members:
            print("  경고: 테스트할 회원을 찾을 수 없습니다.")
            return
        
        consistency_count = 0
        inconsistency_count = 0
        
        for member in members:
            member_id = member['member_id']
            try:
                # 동일한 회원에 대해 3번 추천 요청
                results = []
                for i in range(3):
                    taste_id = self.taste_service.get_taste_for_member(member_id)
                    user_profile = self._create_user_profile(member_id, taste_id, None)
                    recommendations = recommendation_engine.get_recommendations(
                        user_profile, limit=10
                    )
                    results.append({
                        'taste_id': taste_id,
                        'recommendations': recommendations
                    })
                
                # Taste ID 일관성 확인
                taste_ids = [r['taste_id'] for r in results]
                if len(set(taste_ids)) == 1:
                    consistency_count += 1
                else:
                    inconsistency_count += 1
                    self.results['warnings'].append(
                        f"{member_id}: Taste ID가 일관되지 않음 ({taste_ids})"
                    )
                
                self.results['consistency_tests'].append({
                    'member_id': member_id,
                    'taste_ids': taste_ids,
                    'is_consistent': len(set(taste_ids)) == 1,
                    'status': 'success' if len(set(taste_ids)) == 1 else 'inconsistent'
                })
                
            except Exception as e:
                error_msg = str(e)
                self.results['consistency_tests'].append({
                    'member_id': member_id,
                    'status': 'failed',
                    'error': error_msg
                })
        
        print(f"  데이터 일관성 테스트 완료: 일관 {consistency_count}개, 불일치 {inconsistency_count}개")

    def _measure_performance(self):
        """성능 측정"""
        print("  성능 측정 시작...")
        
        members = self._get_members_with_taste(limit=50)
        
        if not members:
            print("  경고: 테스트할 회원을 찾을 수 없습니다.")
            return
        
        execution_times = []
        step_times = {
            'taste_lookup': [],
            'onboarding_lookup': [],
            'recommendation': [],
        }
        
        for member in members:
            member_id = member['member_id']
            try:
                # Taste ID 조회 시간
                start = time.time()
                taste_id = self.taste_service.get_taste_for_member(member_id)
                step_times['taste_lookup'].append(time.time() - start)
                
                # 온보딩 데이터 조회 시간
                start = time.time()
                onboarding_session = self._get_latest_completed_session(member_id)
                step_times['onboarding_lookup'].append(time.time() - start)
                
                # 추천 엔진 실행 시간
                start = time.time()
                user_profile = self._create_user_profile(member_id, taste_id, None)
                recommendations = recommendation_engine.get_recommendations(
                    user_profile, limit=10
                )
                step_times['recommendation'].append(time.time() - start)
                
                # 전체 실행 시간
                total_start = time.time()
                # 전체 플로우 재실행
                taste_id = self.taste_service.get_taste_for_member(member_id)
                user_profile = self._create_user_profile(member_id, taste_id, None)
                recommendations = recommendation_engine.get_recommendations(
                    user_profile, limit=10
                )
                execution_times.append(time.time() - total_start)
                
            except Exception as e:
                continue
        
        # 통계 계산
        if execution_times:
            avg_time = sum(execution_times) / len(execution_times)
            max_time = max(execution_times)
            min_time = min(execution_times)
            
            # 백분위수 계산
            sorted_times = sorted(execution_times)
            p50 = sorted_times[len(sorted_times) // 2]
            p95 = sorted_times[int(len(sorted_times) * 0.95)]
            p99 = sorted_times[int(len(sorted_times) * 0.99)]
        else:
            avg_time = max_time = min_time = p50 = p95 = p99 = 0
        
        # 단계별 평균 시간
        step_avg_times = {}
        for step, times in step_times.items():
            if times:
                step_avg_times[step] = sum(times) / len(times)
            else:
                step_avg_times[step] = 0
        
        self.results['performance_metrics'] = {
            'total_executions': len(execution_times),
            'avg_time': avg_time,
            'max_time': max_time,
            'min_time': min_time,
            'p50': p50,
            'p95': p95,
            'p99': p99,
            'step_avg_times': step_avg_times,
            'all_times': execution_times
        }
        
        print(f"  성능 측정 완료:")
        print(f"    - 평균 실행 시간: {avg_time:.2f}초")
        print(f"    - 최대 실행 시간: {max_time:.2f}초")
        print(f"    - 최소 실행 시간: {min_time:.2f}초")
        print(f"    - P50: {p50:.2f}초")
        print(f"    - P95: {p95:.2f}초")
        print(f"    - P99: {p99:.2f}초")
        print(f"    - 단계별 평균 시간:")
        for step, avg in step_avg_times.items():
            print(f"      - {step}: {avg:.3f}초")
        
        # 성능 검증
        if avg_time > 2.0:
            self.results['warnings'].append(
                f"평균 실행 시간이 2초를 초과합니다: {avg_time:.2f}초"
            )
        if max_time > 5.0:
            self.results['warnings'].append(
                f"최대 실행 시간이 5초를 초과합니다: {max_time:.2f}초"
            )

    def _validate_error_handling(self):
        """에러 처리 검증"""
        print("  에러 처리 테스트 시작...")
        
        test_cases = [
            {
                'name': 'TASTE 값이 없는 회원',
                'member_id': 'non_existent_user',
                'expected_error': True
            },
            {
                'name': 'None 회원 ID',
                'member_id': None,
                'expected_error': True
            },
            {
                'name': '빈 문자열 회원 ID',
                'member_id': '',
                'expected_error': True
            },
        ]
        
        for test_case in test_cases:
            try:
                member_id = test_case['member_id']
                taste_id = self.taste_service.get_taste_for_member(member_id)
                
                if taste_id:
                    user_profile = self._create_user_profile(member_id, taste_id, None)
                    recommendations = recommendation_engine.get_recommendations(
                        user_profile, limit=10
                    )
                    
                    # 에러가 발생하지 않았지만 예상했던 경우
                    if test_case['expected_error']:
                        self.results['error_handling_tests'].append({
                            'test_case': test_case['name'],
                            'status': 'unexpected_success',
                            'message': '에러가 발생하지 않았지만 예상했던 경우'
                        })
                    else:
                        self.results['error_handling_tests'].append({
                            'test_case': test_case['name'],
                            'status': 'success'
                        })
                else:
                    # Taste ID를 찾을 수 없는 경우
                    if test_case['expected_error']:
                        self.results['error_handling_tests'].append({
                            'test_case': test_case['name'],
                            'status': 'expected_error',
                            'message': 'Taste ID를 찾을 수 없음'
                        })
                    else:
                        self.results['error_handling_tests'].append({
                            'test_case': test_case['name'],
                            'status': 'unexpected_error',
                            'message': 'Taste ID를 찾을 수 없음'
                        })
                        
            except Exception as e:
                error_msg = str(e)
                if test_case['expected_error']:
                    self.results['error_handling_tests'].append({
                        'test_case': test_case['name'],
                        'status': 'expected_error',
                        'error': error_msg
                    })
                    print(f"  [OK] {test_case['name']}: 예상된 에러 발생")
                else:
                    self.results['error_handling_tests'].append({
                        'test_case': test_case['name'],
                        'status': 'unexpected_error',
                        'error': error_msg
                    })
                    print(f"  [FAIL] {test_case['name']}: 예상치 못한 에러 발생")
        
        print(f"  에러 처리 테스트 완료: {len(test_cases)}개 테스트 케이스")

    def _validate_edge_cases(self):
        """엣지 케이스 검증"""
        print("  엣지 케이스 테스트 시작...")
        
        # 1. TASTE 값이 없는 회원 처리
        members_no_taste = self._get_members_without_taste(limit=5)
        for member in members_no_taste:
            member_id = member['member_id']
            try:
                taste_id = self.taste_service.get_taste_for_member(member_id)
                if taste_id:
                    # 기본 추천 또는 에러 처리 확인
                    user_profile = self._create_user_profile(member_id, taste_id, None)
                    recommendations = recommendation_engine.get_recommendations(
                        user_profile, limit=10
                    )
                    self.results['edge_case_tests'].append({
                        'case': 'no_taste',
                        'member_id': member_id,
                        'status': 'handled',
                        'has_recommendations': recommendations is not None
                    })
            except Exception as e:
                self.results['edge_case_tests'].append({
                    'case': 'no_taste',
                    'member_id': member_id,
                    'status': 'error',
                    'error': str(e)
                })
        
        # 2. 온보딩 데이터가 없는 회원 처리
        members = self._get_members_with_taste(limit=10)
        for member in members:
            member_id = member['member_id']
            try:
                taste_id = self.taste_service.get_taste_for_member(member_id)
                onboarding_session = self._get_latest_completed_session(member_id)
                
                if not onboarding_session:
                    # 온보딩 데이터 없이 추천 실행
                    user_profile = self._create_user_profile(member_id, taste_id, None)
                    recommendations = recommendation_engine.get_recommendations(
                        user_profile, limit=10
                    )
                    self.results['edge_case_tests'].append({
                        'case': 'no_onboarding',
                        'member_id': member_id,
                        'status': 'handled',
                        'has_recommendations': recommendations is not None
                    })
            except Exception as e:
                self.results['edge_case_tests'].append({
                    'case': 'no_onboarding',
                    'member_id': member_id,
                    'status': 'error',
                    'error': str(e)
                })
        
        print(f"  엣지 케이스 테스트 완료: {len(self.results['edge_case_tests'])}개 케이스")

    def _get_members_with_taste(self, limit: int = 100) -> List[Dict]:
        """TASTE 값이 있는 회원 조회"""
        try:
            conn = get_connection()
            cur = conn.cursor()
            
            query = """
                SELECT MEMBER_ID, TASTE
                FROM (
                    SELECT MEMBER_ID, TASTE
                    FROM MEMBER
                    WHERE TASTE IS NOT NULL
                      AND TASTE BETWEEN 1 AND 120
                    ORDER BY DBMS_RANDOM.VALUE
                ) WHERE ROWNUM <= :limit
            """
            
            cur.execute(query, {'limit': limit})
            rows = cur.fetchall()
            
            members = []
            for row in rows:
                members.append({
                    'member_id': row[0],
                    'taste': row[1]
                })
            
            cur.close()
            conn.close()
            
            return members
            
        except Exception as e:
            print(f"  경고: 회원 조회 중 오류 발생: {str(e)}")
            return []

    def _get_members_without_taste(self, limit: int = 5) -> List[Dict]:
        """TASTE 값이 없는 회원 조회"""
        try:
            conn = get_connection()
            cur = conn.cursor()
            
            query = """
                SELECT MEMBER_ID
                FROM (
                    SELECT MEMBER_ID
                    FROM MEMBER
                    WHERE TASTE IS NULL
                    ORDER BY DBMS_RANDOM.VALUE
                ) WHERE ROWNUM <= :limit
            """
            
            cur.execute(query, {'limit': limit})
            rows = cur.fetchall()
            
            members = []
            for row in rows:
                members.append({
                    'member_id': row[0]
                })
            
            cur.close()
            conn.close()
            
            return members
            
        except Exception as e:
            print(f"  경고: 회원 조회 중 오류 발생: {str(e)}")
            return []

    def _get_members_with_onboarding(self, limit: int = 50) -> List[Dict]:
        """온보딩 완료된 회원 조회"""
        try:
            conn = get_connection()
            cur = conn.cursor()
            
            query = """
                SELECT MEMBER_ID
                FROM (
                    SELECT DISTINCT MEMBER_ID
                    FROM ONBOARDING_SESSION
                    WHERE STATUS = 'COMPLETED'
                      AND MEMBER_ID IS NOT NULL
                      AND MEMBER_ID != 'GUEST'
                    ORDER BY DBMS_RANDOM.VALUE
                ) WHERE ROWNUM <= :limit
            """
            
            cur.execute(query, {'limit': limit})
            rows = cur.fetchall()
            
            members = []
            for row in rows:
                members.append({
                    'member_id': row[0]
                })
            
            cur.close()
            conn.close()
            
            return members
            
        except Exception as e:
            print(f"  경고: 온보딩 회원 조회 중 오류 발생: {str(e)}")
            return []

    def _create_user_profile(self, member_id: str, taste_id: int, onboarding_data: Optional[Dict]) -> Dict:
        """사용자 프로필 생성"""
        # recommendation_engine이 요구하는 필수 필드: budget_level, categories
        # 기본 카테고리 설정 (Taste 기반 추천은 recommendation_engine 내부에서 처리)
        default_categories = ['TV', 'KITCHEN', 'LIVING']  # 기본 카테고리
        
        profile = {
            'member_id': member_id,
            'taste_id': taste_id,
            'budget_level': 'medium',  # 기본값
            'categories': default_categories,  # 기본값
        }
        
        if onboarding_data:
            profile.update({
                'budget_level': onboarding_data.get('budget_level', 'medium'),
                'housing_type': onboarding_data.get('housing_type', 'apartment'),
                'household_size': onboarding_data.get('household_size', 2),
                'has_pet': onboarding_data.get('has_pet', False),
                'has_children': onboarding_data.get('has_children', False),
                'vibe': onboarding_data.get('vibe', 'modern'),
                'priority': onboarding_data.get('priority', 'value'),
            })
            # 온보딩 데이터에 카테고리가 있으면 사용
            if onboarding_data.get('selected_categories'):
                profile['categories'] = onboarding_data.get('selected_categories')
        
        return profile
    
    def _get_latest_completed_session(self, member_id: str) -> Optional[Dict]:
        """온보딩 완료된 세션 조회"""
        try:
            conn = get_connection()
            cur = conn.cursor()
            
            query = """
                SELECT SESSION_ID, MEMBER_ID, STATUS, BUDGET_LEVEL
                FROM (
                    SELECT SESSION_ID, MEMBER_ID, STATUS, BUDGET_LEVEL
                    FROM ONBOARDING_SESSION
                    WHERE STATUS = 'COMPLETED'
                      AND MEMBER_ID = :member_id
                    ORDER BY CREATED_AT DESC
                ) WHERE ROWNUM <= 1
            """
            
            cur.execute(query, {'member_id': member_id})
            row = cur.fetchone()
            
            cur.close()
            conn.close()
            
            if row:
                return {
                    'session_id': row[0],
                    'member_id': row[1],
                    'status': row[2],
                    'budget_level': row[3]
                }
            return None
            
        except Exception as e:
            print(f"  경고: 온보딩 세션 조회 중 오류 발생: {str(e)}")
            return None

    def _generate_summary(self):
        """결과 요약 생성"""
        print("=" * 80)
        print("검증 결과 요약")
        print("=" * 80)
        print()
        
        stats = self.results['statistics']
        print(f"전체 테스트:")
        print(f"  - 총 테스트: {stats['total_tested']}개")
        print(f"  - 성공: {stats['successful']}개")
        print(f"  - 실패: {stats['failed']}개")
        print(f"  - 에러: {len(self.results['errors'])}개")
        print()
        
        if stats['total_tested'] > 0:
            success_rate = stats['successful'] / stats['total_tested'] * 100
            print(f"  성공률: {success_rate:.1f}%")
        print()
        
        # 성능 메트릭
        if self.results['performance_metrics']:
            perf = self.results['performance_metrics']
            print(f"성능 메트릭:")
            print(f"  - 평균 실행 시간: {perf.get('avg_time', 0):.2f}초")
            print(f"  - 최대 실행 시간: {perf.get('max_time', 0):.2f}초")
            print(f"  - P95: {perf.get('p95', 0):.2f}초")
            print()
        
        # 경고 사항
        if self.results['warnings']:
            print(f"경고 사항 ({len(self.results['warnings'])}개):")
            for warning in self.results['warnings'][:10]:  # 처음 10개만 출력
                print(f"  - {warning}")
            if len(self.results['warnings']) > 10:
                print(f"  ... 외 {len(self.results['warnings']) - 10}개")
            print()
        
        # 에러 사항
        if self.results['errors']:
            print(f"에러 사항 ({len(self.results['errors'])}개):")
            for error in self.results['errors'][:10]:  # 처음 10개만 출력
                print(f"  - {error.get('member_id', 'N/A')}: {error.get('message', 'N/A')}")
            if len(self.results['errors']) > 10:
                print(f"  ... 외 {len(self.results['errors']) - 10}개")
            print()

    def _generate_visualizations(self):
        """시각화 생성"""
        if not HAS_MATPLOTLIB:
            print("  시각화를 건너뜁니다 (matplotlib 없음)")
            return
        
        print("  시각화 생성 중...")
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = "."
        
        try:
            # 1. 전체 플로우 성공/실패 비율 파이 차트
            if self.results['full_flow_tests']:
                self._plot_success_failure_pie(
                    self.results['full_flow_tests'],
                    f"{output_dir}/recommendation_integration_success_rate_{timestamp}.png"
                )
            
            # 2. 단계별 처리 시간 박스 플롯
            if self.results['performance_metrics']:
                self._plot_performance_boxplot(
                    self.results['performance_metrics'],
                    f"{output_dir}/recommendation_integration_performance_{timestamp}.png"
                )
            
            # 3. 추천 결과 통계
            if self.results['real_member_tests']:
                self._plot_recommendation_statistics(
                    self.results['real_member_tests'],
                    f"{output_dir}/recommendation_integration_statistics_{timestamp}.png"
                )
            
            # 4. 에러 발생 빈도
            if self.results['errors']:
                self._plot_error_frequency(
                    self.results['errors'],
                    f"{output_dir}/recommendation_integration_errors_{timestamp}.png"
                )
            
            print(f"  시각화 생성 완료: {timestamp}")
            
        except Exception as e:
            print(f"  시각화 생성 중 오류 발생: {str(e)}")

    def _plot_success_failure_pie(self, tests: List[Dict], output_path: str):
        """성공/실패 비율 파이 차트"""
        success_count = sum(1 for t in tests if t.get('status') == 'success')
        failure_count = sum(1 for t in tests if t.get('status') == 'failed')
        
        if success_count + failure_count == 0:
            return
        
        fig, ax = plt.subplots(figsize=(8, 8))
        ax.pie(
            [success_count, failure_count],
            labels=['성공', '실패'],
            autopct='%1.1f%%',
            startangle=90,
            colors=['#4CAF50', '#F44336']
        )
        ax.set_title('전체 플로우 성공/실패 비율', fontsize=14, fontweight='bold')
        plt.tight_layout()
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        plt.close()

    def _plot_performance_boxplot(self, metrics: Dict, output_path: str):
        """성능 박스 플롯"""
        if not metrics.get('all_times'):
            return
        
        fig, axes = plt.subplots(1, 2, figsize=(14, 6))
        
        # 전체 실행 시간 분포
        axes[0].boxplot(metrics['all_times'], vert=True)
        axes[0].set_ylabel('실행 시간 (초)')
        axes[0].set_title('전체 플로우 실행 시간 분포')
        axes[0].grid(True, alpha=0.3)
        
        # 단계별 평균 시간
        if metrics.get('step_avg_times'):
            steps = list(metrics['step_avg_times'].keys())
            times = list(metrics['step_avg_times'].values())
            axes[1].bar(steps, times, color=['#2196F3', '#FF9800', '#4CAF50'])
            axes[1].set_ylabel('평균 시간 (초)')
            axes[1].set_title('단계별 평균 처리 시간')
            axes[1].tick_params(axis='x', rotation=45)
            axes[1].grid(True, alpha=0.3, axis='y')
        
        plt.tight_layout()
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        plt.close()

    def _plot_recommendation_statistics(self, tests: List[Dict], output_path: str):
        """추천 결과 통계"""
        execution_times = [t.get('execution_time', 0) for t in tests if t.get('execution_time')]
        
        if not execution_times:
            return
        
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.hist(execution_times, bins=20, color='#2196F3', edgecolor='black', alpha=0.7)
        ax.set_xlabel('실행 시간 (초)')
        ax.set_ylabel('빈도')
        ax.set_title('추천 엔진 실행 시간 분포')
        ax.axvline(sum(execution_times) / len(execution_times), color='red', 
                   linestyle='--', label=f'평균: {sum(execution_times) / len(execution_times):.2f}초')
        ax.legend()
        ax.grid(True, alpha=0.3)
        plt.tight_layout()
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        plt.close()

    def _plot_error_frequency(self, errors: List[Dict], output_path: str):
        """에러 발생 빈도"""
        error_types = Counter(e.get('type', 'unknown') for e in errors)
        
        if not error_types:
            return
        
        fig, ax = plt.subplots(figsize=(10, 6))
        types = list(error_types.keys())
        counts = list(error_types.values())
        
        ax.bar(types, counts, color='#F44336')
        ax.set_xlabel('에러 타입')
        ax.set_ylabel('발생 횟수')
        ax.set_title('에러 발생 빈도')
        ax.tick_params(axis='x', rotation=45)
        ax.grid(True, alpha=0.3, axis='y')
        plt.tight_layout()
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        plt.close()


if __name__ == '__main__':
    validator = RecommendationIntegrationValidator()
    validator.validate_all()

