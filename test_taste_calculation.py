#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Step 3: Taste 계산 로직 검증 - TasteClassifier가 올바른 Taste ID(1~120)를 반환하는지 테스트

검증 항목:
1. 입력 데이터 형식 검증
2. Taste ID 범위 검증 (1~120)
3. 일관성 검증 (동일 입력 → 동일 출력)
4. 다양한 입력 조합 검증
5. 실제 세션 데이터로 검증
6. 분포 검증
"""
import sys
import os
import json
from datetime import datetime
from collections import Counter
import random

# Django 설정 로드
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

import django
django.setup()

from api.utils.taste_classifier import TasteClassifier
from api.services.taste_calculation_service import TasteCalculationService
from api.db.oracle_client import get_connection

# 시각화 라이브러리
try:
    import matplotlib.pyplot as plt
    import matplotlib
    matplotlib.use('Agg')  # GUI 없이 사용
    import numpy as np
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False
    print("⚠️ matplotlib이 설치되지 않아 시각화를 건너뜁니다.")


class TasteCalculationValidator:
    """Taste 계산 로직 검증 클래스"""
    
    def __init__(self):
        self.results = {
            'test_cases': [],
            'real_sessions': [],
            'consistency_tests': [],
            'distribution_tests': [],
            'errors': [],
            'warnings': []
        }
        self.taste_classifier = TasteClassifier()
    
    def validate_all(self):
        """모든 검증 실행"""
        print("=" * 80)
        print("Step 3: Taste 계산 로직 검증")
        print("=" * 80)
        print()
        
        try:
            # 1. 입력 데이터 형식 검증
            print("[1] 입력 데이터 형식 검증")
            self._validate_input_format()
            print()
            
            # 2. Taste ID 범위 검증
            print("[2] Taste ID 범위 검증")
            self._validate_taste_id_range()
            print()
            
            # 3. 일관성 검증
            print("[3] 일관성 검증 (동일 입력 → 동일 출력)")
            self._validate_consistency()
            print()
            
            # 4. 다양한 입력 조합 검증
            print("[4] 다양한 입력 조합 검증")
            self._validate_various_combinations()
            print()
            
            # 5. 실제 세션 데이터로 검증
            print("[5] 실제 세션 데이터로 검증")
            self._validate_real_sessions()
            print()
            
            # 6. 분포 검증
            print("[6] 분포 검증")
            self._validate_distribution()
            print()
            
            # 7. 결과 출력
            self._print_results()
            
            # 8. 시각화 생성
            if HAS_MATPLOTLIB:
                self._create_visualizations()
            
        except Exception as e:
            print(f"\n❌ 검증 중 예외 발생: {e}")
            import traceback
            traceback.print_exc()
            return False
        
        return self._is_all_passed()
    
    def _validate_input_format(self):
        """입력 데이터 형식 검증"""
        test_cases = [
            {
                'name': '기본 케이스 - 모든 필드 채워짐',
                'data': {
                    'vibe': 'modern',
                    'household_size': 4,
                    'housing_type': 'apartment',
                    'pyung': 30,
                    'budget_level': 'medium',
                    'priority': ['tech', 'design'],
                    'main_space': ['living', 'kitchen'],
                    'has_pet': False,
                    'cooking': 'frequently',
                    'laundry': 'weekly',
                    'media': 'balanced'
                }
            },
            {
                'name': 'NULL 값 케이스 - 일부 필드 NULL',
                'data': {
                    'vibe': 'modern',
                    'household_size': None,
                    'housing_type': None,
                    'pyung': None,
                    'budget_level': None,
                    'priority': None,
                    'main_space': None,
                    'has_pet': None,
                    'cooking': None,
                    'laundry': None,
                    'media': None
                }
            },
            {
                'name': '빈 배열 케이스',
                'data': {
                    'vibe': 'classic',
                    'household_size': 2,
                    'priority': [],
                    'main_space': []
                }
            },
            {
                'name': '최소값 케이스',
                'data': {
                    'vibe': 'minimal',
                    'household_size': 1,
                    'pyung': 1,
                    'budget_level': 'low'
                }
            },
            {
                'name': '최대값 케이스',
                'data': {
                    'vibe': 'luxury',
                    'household_size': 10,
                    'pyung': 100,
                    'budget_level': 'high'
                }
            },
            {
                'name': '빈 딕셔너리 케이스',
                'data': {}
            }
        ]
        
        for test_case in test_cases:
            try:
                taste_id = self.taste_classifier.calculate_taste_from_onboarding(test_case['data'])
                result = {
                    'name': test_case['name'],
                    'input': test_case['data'],
                    'taste_id': taste_id,
                    'passed': True,
                    'message': f'Taste ID: {taste_id}'
                }
                
                # 범위 검증
                if not (1 <= taste_id <= 120):
                    result['passed'] = False
                    result['message'] = f'Taste ID 범위 초과: {taste_id} (1~120 범위여야 함)'
                
                self.results['test_cases'].append(result)
                
                if result['passed']:
                    print(f"  ✅ {test_case['name']}: Taste ID = {taste_id}")
                else:
                    print(f"  ❌ {test_case['name']}: {result['message']}")
                    
            except Exception as e:
                result = {
                    'name': test_case['name'],
                    'input': test_case['data'],
                    'passed': False,
                    'message': f'예외 발생: {str(e)}'
                }
                self.results['test_cases'].append(result)
                self.results['errors'].append(f"{test_case['name']}: {str(e)}")
                print(f"  ❌ {test_case['name']}: 예외 발생 - {e}")
    
    def _validate_taste_id_range(self):
        """Taste ID 범위 검증"""
        # 다양한 입력으로 1000번 테스트
        test_count = 1000
        out_of_range = []
        
        vibes = ['modern', 'classic', 'minimal', 'luxury']
        household_sizes = [1, 2, 3, 4, 5, 6, 7, 8]
        housing_types = ['apartment', 'house', 'villa', 'officetel']
        pyungs = [10, 20, 30, 40, 50, 60, 70, 80, 90, 100]
        budget_levels = ['low', 'medium', 'high']
        priorities_list = [['tech'], ['design'], ['value'], ['tech', 'design'], ['tech', 'value'], []]
        main_spaces_list = [['living'], ['kitchen'], ['bedroom'], ['living', 'kitchen'], []]
        
        for i in range(test_count):
            test_data = {
                'vibe': random.choice(vibes),
                'household_size': random.choice(household_sizes),
                'housing_type': random.choice(housing_types),
                'pyung': random.choice(pyungs),
                'budget_level': random.choice(budget_levels),
                'priority': random.choice(priorities_list),
                'main_space': random.choice(main_spaces_list),
                'has_pet': random.choice([True, False]),
                'cooking': random.choice(['rarely', 'sometimes', 'frequently']),
                'laundry': random.choice(['daily', 'weekly', 'monthly']),
                'media': random.choice(['minimal', 'balanced', 'intensive', 'none'])
            }
            
            try:
                taste_id = self.taste_classifier.calculate_taste_from_onboarding(test_data)
                if not (1 <= taste_id <= 120):
                    out_of_range.append({
                        'input': test_data,
                        'taste_id': taste_id
                    })
            except Exception as e:
                out_of_range.append({
                    'input': test_data,
                    'error': str(e)
                })
        
        if out_of_range:
            print(f"  ❌ 범위를 벗어난 케이스: {len(out_of_range)}개")
            for case in out_of_range[:5]:  # 최대 5개만 출력
                if 'error' in case:
                    print(f"    - 예외: {case['error']}")
                else:
                    print(f"    - Taste ID: {case['taste_id']} (범위: 1~120)")
            self.results['errors'].extend([f"범위 초과: {len(out_of_range)}개 케이스"])
        else:
            print(f"  ✅ {test_count}개 테스트 모두 1~120 범위 내")
    
    def _validate_consistency(self):
        """일관성 검증 - 동일 입력에 대해 항상 동일한 결과 반환"""
        test_inputs = [
            {
                'vibe': 'modern',
                'household_size': 4,
                'housing_type': 'apartment',
                'pyung': 30,
                'budget_level': 'medium',
                'priority': ['tech', 'design'],
                'main_space': ['living', 'kitchen'],
                'has_pet': False,
                'cooking': 'frequently',
                'laundry': 'weekly',
                'media': 'balanced'
            },
            {
                'vibe': 'classic',
                'household_size': 2,
                'priority': [],
                'main_space': []
            },
            {}
        ]
        
        for test_input in test_inputs:
            # 동일 입력으로 100번 반복 계산
            iterations = 100
            results = []
            
            for _ in range(iterations):
                try:
                    taste_id = self.taste_classifier.calculate_taste_from_onboarding(test_input)
                    results.append(taste_id)
                except Exception as e:
                    results.append(f"ERROR: {str(e)}")
            
            # 모든 결과가 동일한지 확인
            unique_results = set(results)
            
            result = {
                'input': test_input,
                'iterations': iterations,
                'results': results,
                'unique_count': len(unique_results),
                'passed': len(unique_results) == 1
            }
            
            if result['passed']:
                print(f"  ✅ 일관성 검증 통과: {iterations}회 반복, 모두 Taste ID = {results[0]}")
            else:
                print(f"  ❌ 일관성 검증 실패: {len(unique_results)}개의 서로 다른 결과")
                print(f"     결과: {list(unique_results)[:10]}")  # 최대 10개만 출력
                self.results['errors'].append(f"일관성 실패: {len(unique_results)}개 서로 다른 결과")
            
            self.results['consistency_tests'].append(result)
    
    def _validate_various_combinations(self):
        """다양한 입력 조합 검증"""
        combinations = [
            # Vibe 조합
            {'vibe': 'modern'},
            {'vibe': 'classic'},
            {'vibe': 'minimal'},
            {'vibe': 'luxury'},
            
            # Household size 조합
            {'household_size': 1},
            {'household_size': 2},
            {'household_size': 4},
            {'household_size': 8},
            
            # Housing type 조합
            {'housing_type': 'apartment'},
            {'housing_type': 'house'},
            {'housing_type': 'villa'},
            {'housing_type': 'officetel'},
            
            # Pyung 조합
            {'pyung': 10},
            {'pyung': 20},
            {'pyung': 30},
            {'pyung': 50},
            {'pyung': 100},
            
            # Budget level 조합
            {'budget_level': 'low'},
            {'budget_level': 'medium'},
            {'budget_level': 'high'},
            
            # Priority 조합
            {'priority': ['tech']},
            {'priority': ['design']},
            {'priority': ['value']},
            {'priority': ['tech', 'design']},
            {'priority': ['tech', 'design', 'value']},
            {'priority': []},
            
            # Main space 조합
            {'main_space': ['living']},
            {'main_space': ['kitchen']},
            {'main_space': ['bedroom']},
            {'main_space': ['living', 'kitchen']},
            {'main_space': ['living', 'kitchen', 'bedroom']},
            {'main_space': []},
            
            # Has pet 조합
            {'has_pet': True},
            {'has_pet': False},
            
            # 복합 조합
            {
                'vibe': 'modern',
                'household_size': 4,
                'housing_type': 'apartment',
                'pyung': 30,
                'budget_level': 'medium',
                'priority': ['tech', 'design'],
                'main_space': ['living', 'kitchen'],
                'has_pet': True,
                'cooking': 'frequently',
                'laundry': 'weekly',
                'media': 'balanced'
            }
        ]
        
        passed = 0
        failed = 0
        
        for combo in combinations:
            try:
                taste_id = self.taste_classifier.calculate_taste_from_onboarding(combo)
                if 1 <= taste_id <= 120:
                    passed += 1
                else:
                    failed += 1
                    print(f"  ❌ 범위 초과: Taste ID = {taste_id}, 입력: {combo}")
            except Exception as e:
                failed += 1
                print(f"  ❌ 예외 발생: {e}, 입력: {combo}")
        
        print(f"  ✅ 통과: {passed}개")
        if failed > 0:
            print(f"  ❌ 실패: {failed}개")
    
    def _validate_real_sessions(self):
        """실제 세션 데이터로 검증"""
        # Step 2에서 사용한 실제 SESSION_ID 샘플
        sample_ids = ['1764840383702', '1764840384247', '1764840384743']
        
        try:
            with get_connection() as conn:
                with conn.cursor() as cur:
                    # 샘플 ID 중 존재하는 것만 필터링
                    existing_sessions = []
                    for session_id in sample_ids:
                        cur.execute("""
                            SELECT COUNT(*) FROM ONBOARDING_SESSION WHERE SESSION_ID = :session_id
                        """, {'session_id': session_id})
                        if cur.fetchone()[0] > 0:
                            existing_sessions.append(session_id)
                    
                    # 필요한 만큼 추가로 가져오기
                    if len(existing_sessions) < 20:
                        placeholders = ','.join([f"'{sid}'" for sid in existing_sessions])
                        where_clause = f"WHERE SESSION_ID NOT IN ({placeholders})" if existing_sessions else ""
                        
                        cur.execute(f"""
                            SELECT SESSION_ID 
                            FROM (
                                SELECT SESSION_ID 
                                FROM ONBOARDING_SESSION 
                                {where_clause}
                                ORDER BY DBMS_RANDOM.VALUE
                            ) WHERE ROWNUM <= :limit
                        """, {'limit': 20 - len(existing_sessions)})
                        additional_sessions = [row[0] for row in cur.fetchall()]
                        existing_sessions.extend(additional_sessions)
                    
                    test_sessions = existing_sessions[:20]
                    
                    print(f"  테스트할 세션: {len(test_sessions)}개")
                    
                    for session_id in test_sessions:
                        try:
                            # 온보딩 데이터 조회
                            onboarding_data = TasteCalculationService._get_onboarding_data_from_session(session_id)
                            
                            # Taste 계산
                            taste_id = self.taste_classifier.calculate_taste_from_onboarding(onboarding_data)
                            
                            result = {
                                'session_id': session_id,
                                'onboarding_data': onboarding_data,
                                'taste_id': taste_id,
                                'passed': 1 <= taste_id <= 120
                            }
                            
                            if result['passed']:
                                print(f"    ✅ SESSION_ID {session_id}: Taste ID = {taste_id}")
                            else:
                                print(f"    ❌ SESSION_ID {session_id}: Taste ID = {taste_id} (범위 초과)")
                                self.results['errors'].append(f"세션 {session_id}: 범위 초과 Taste ID {taste_id}")
                            
                            self.results['real_sessions'].append(result)
                            
                        except Exception as e:
                            print(f"    ❌ SESSION_ID {session_id}: 예외 발생 - {e}")
                            self.results['errors'].append(f"세션 {session_id}: {str(e)}")
                            self.results['real_sessions'].append({
                                'session_id': session_id,
                                'passed': False,
                                'error': str(e)
                            })
        
        except Exception as e:
            print(f"  ❌ 실제 세션 검증 중 오류: {e}")
            import traceback
            traceback.print_exc()
            self.results['errors'].append(f"실제 세션 검증 실패: {str(e)}")
    
    def _validate_distribution(self):
        """분포 검증 - 다양한 입력에 대해 Taste ID 분포 확인"""
        # 다양한 입력 조합 1000개 생성
        test_count = 1000
        taste_ids = []
        
        vibes = ['modern', 'classic', 'minimal', 'luxury']
        household_sizes = list(range(1, 9))
        housing_types = ['apartment', 'house', 'villa', 'officetel']
        pyungs = [10, 15, 20, 25, 30, 35, 40, 50, 60, 70, 80, 90, 100]
        budget_levels = ['low', 'medium', 'high']
        priorities_options = [
            ['tech'], ['design'], ['value'], 
            ['tech', 'design'], ['tech', 'value'], ['design', 'value'],
            ['tech', 'design', 'value'], []
        ]
        main_spaces_options = [
            ['living'], ['kitchen'], ['bedroom'], ['bathroom'],
            ['living', 'kitchen'], ['living', 'bedroom'], ['kitchen', 'bedroom'],
            ['living', 'kitchen', 'bedroom'], []
        ]
        
        for _ in range(test_count):
            test_data = {
                'vibe': random.choice(vibes),
                'household_size': random.choice(household_sizes),
                'housing_type': random.choice(housing_types),
                'pyung': random.choice(pyungs),
                'budget_level': random.choice(budget_levels),
                'priority': random.choice(priorities_options),
                'main_space': random.choice(main_spaces_options),
                'has_pet': random.choice([True, False]),
                'cooking': random.choice(['rarely', 'sometimes', 'frequently']),
                'laundry': random.choice(['daily', 'weekly', 'monthly']),
                'media': random.choice(['minimal', 'balanced', 'intensive', 'none'])
            }
            
            try:
                taste_id = self.taste_classifier.calculate_taste_from_onboarding(test_data)
                if 1 <= taste_id <= 120:
                    taste_ids.append(taste_id)
            except Exception as e:
                self.results['errors'].append(f"분포 테스트 중 예외: {str(e)}")
        
        if taste_ids:
            # 분포 통계
            taste_counter = Counter(taste_ids)
            unique_taste_count = len(taste_counter)
            min_taste_id = min(taste_ids)
            max_taste_id = max(taste_ids)
            most_common = taste_counter.most_common(5)
            
            print(f"  테스트 입력 수: {test_count}개")
            print(f"  계산 성공: {len(taste_ids)}개")
            print(f"  고유 Taste ID 수: {unique_taste_count}개 (1~120 중)")
            print(f"  Taste ID 범위: {min_taste_id} ~ {max_taste_id}")
            print(f"  가장 많이 나타난 Taste ID (상위 5개):")
            for taste_id, count in most_common:
                print(f"    - Taste ID {taste_id}: {count}회 ({count/len(taste_ids)*100:.1f}%)")
            
            # 분포가 적절한지 확인 (모든 Taste ID가 최소 1번 이상 나타나는지는 선택적)
            # 실제로는 해시 기반이므로 완벽한 균등 분포는 기대하기 어려움
            coverage = unique_taste_count / 120 * 100
            print(f"  Taste ID 커버리지: {coverage:.1f}% ({unique_taste_count}/120)")
            
            if coverage < 50:
                self.results['warnings'].append(f"Taste ID 커버리지가 낮습니다: {coverage:.1f}%")
            
            self.results['distribution_tests'] = {
                'total_tests': test_count,
                'successful_calculations': len(taste_ids),
                'unique_taste_count': unique_taste_count,
                'min_taste_id': min_taste_id,
                'max_taste_id': max_taste_id,
                'taste_distribution': dict(taste_counter),
                'coverage': coverage
            }
        else:
            print(f"  ❌ 분포 테스트 실패: 계산된 Taste ID가 없습니다")
            self.results['errors'].append("분포 테스트 실패: 계산된 Taste ID 없음")
    
    def _print_results(self):
        """검증 결과 출력"""
        print("=" * 80)
        print("검증 결과 요약")
        print("=" * 80)
        
        # 테스트 케이스 결과
        test_cases = self.results['test_cases']
        passed_cases = sum(1 for tc in test_cases if tc.get('passed', False))
        print(f"\n[입력 데이터 형식 검증]")
        print(f"  총 테스트 케이스: {len(test_cases)}개")
        print(f"  통과: {passed_cases}개")
        print(f"  실패: {len(test_cases) - passed_cases}개")
        
        # 일관성 테스트 결과
        consistency_tests = self.results['consistency_tests']
        passed_consistency = sum(1 for ct in consistency_tests if ct.get('passed', False))
        print(f"\n[일관성 검증]")
        print(f"  총 테스트: {len(consistency_tests)}개")
        print(f"  통과: {passed_consistency}개")
        print(f"  실패: {len(consistency_tests) - passed_consistency}개")
        
        # 실제 세션 검증 결과
        real_sessions = self.results['real_sessions']
        passed_sessions = sum(1 for rs in real_sessions if rs.get('passed', False))
        print(f"\n[실제 세션 검증]")
        print(f"  총 테스트 세션: {len(real_sessions)}개")
        print(f"  통과: {passed_sessions}개")
        print(f"  실패: {len(real_sessions) - passed_sessions}개")
        
        # 분포 검증 결과
        if self.results['distribution_tests']:
            dist = self.results['distribution_tests']
            print(f"\n[분포 검증]")
            print(f"  테스트 입력 수: {dist.get('total_tests', 0)}개")
            print(f"  계산 성공: {dist.get('successful_calculations', 0)}개")
            print(f"  고유 Taste ID 수: {dist.get('unique_taste_count', 0)}개")
            print(f"  커버리지: {dist.get('coverage', 0):.1f}%")
        
        # 에러
        if self.results['errors']:
            print("\n[에러]")
            for error in self.results['errors'][:10]:  # 최대 10개만 출력
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
        # 테스트 케이스 모두 통과
        test_cases_passed = all(
            tc.get('passed', False) 
            for tc in self.results['test_cases']
        )
        
        # 일관성 테스트 모두 통과
        consistency_passed = all(
            ct.get('passed', False) 
            for ct in self.results['consistency_tests']
        )
        
        # 실제 세션 검증 모두 통과
        real_sessions_passed = all(
            rs.get('passed', False) 
            for rs in self.results['real_sessions']
        )
        
        # 에러 없음
        no_errors = len(self.results['errors']) == 0
        
        return test_cases_passed and consistency_passed and real_sessions_passed and no_errors
    
    def _create_visualizations(self):
        """검증 결과 시각화"""
        if not HAS_MATPLOTLIB:
            return
        
        print("[시각화 생성 중...]")
        
        try:
            # 한글 폰트 설정
            plt.rcParams['font.family'] = 'Malgun Gothic'  # Windows
            plt.rcParams['axes.unicode_minus'] = False
            
            fig = plt.figure(figsize=(20, 14))
            gs = fig.add_gridspec(3, 3, hspace=0.3, wspace=0.3)
            
            # 1. 전체 검증 결과 (파이 차트)
            ax1 = fig.add_subplot(gs[0, 0])
            test_cases = self.results['test_cases']
            passed_cases = sum(1 for tc in test_cases if tc.get('passed', False))
            failed_cases = len(test_cases) - passed_cases
            
            if failed_cases > 0:
                ax1.pie([passed_cases, failed_cases], 
                       labels=[f'통과 ({passed_cases})', f'실패 ({failed_cases})'],
                       autopct='%1.1f%%',
                       colors=['#4CAF50', '#F44336'],
                       startangle=90)
            else:
                ax1.pie([passed_cases], 
                       labels=[f'통과 ({passed_cases})'],
                       autopct='%1.1f%%',
                       colors=['#4CAF50'],
                       startangle=90)
            ax1.set_title('입력 데이터 형식 검증 결과', fontsize=14, fontweight='bold')
            
            # 2. Taste ID 범위 분포 (히스토그램)
            ax2 = fig.add_subplot(gs[0, 1])
            all_taste_ids = []
            
            # 테스트 케이스에서 Taste ID 수집
            for tc in test_cases:
                if 'taste_id' in tc:
                    all_taste_ids.append(tc['taste_id'])
            
            # 실제 세션에서 Taste ID 수집
            for rs in self.results['real_sessions']:
                if 'taste_id' in rs:
                    all_taste_ids.append(rs['taste_id'])
            
            # 분포 테스트에서 Taste ID 수집
            if self.results['distribution_tests']:
                dist = self.results['distribution_tests']
                taste_dist = dist.get('taste_distribution', {})
                for taste_id, count in taste_dist.items():
                    all_taste_ids.extend([taste_id] * count)
            
            if all_taste_ids:
                ax2.hist(all_taste_ids, bins=120, range=(1, 121), 
                        color='skyblue', edgecolor='black', alpha=0.7)
                ax2.set_xlabel('Taste ID')
                ax2.set_ylabel('빈도')
                ax2.set_title('Taste ID 분포 (1~120)', fontsize=14, fontweight='bold')
                ax2.set_xlim(1, 120)
                ax2.grid(True, alpha=0.3, axis='y')
            else:
                ax2.text(0.5, 0.5, 'Taste ID 데이터 없음', 
                        ha='center', va='center', fontsize=12,
                        transform=ax2.transAxes)
                ax2.set_title('Taste ID 분포', fontsize=14, fontweight='bold')
            
            # 3. 실제 세션 검증 결과
            ax3 = fig.add_subplot(gs[0, 2])
            real_sessions = self.results['real_sessions']
            passed_sessions = sum(1 for rs in real_sessions if rs.get('passed', False))
            failed_sessions = len(real_sessions) - passed_sessions
            
            if failed_sessions > 0:
                ax3.pie([passed_sessions, failed_sessions], 
                       labels=[f'통과 ({passed_sessions})', f'실패 ({failed_sessions})'],
                       autopct='%1.1f%%',
                       colors=['#4CAF50', '#F44336'],
                       startangle=90)
            else:
                ax3.pie([passed_sessions], 
                       labels=[f'통과 ({passed_sessions})'],
                       autopct='%1.1f%%',
                       colors=['#4CAF50'],
                       startangle=90)
            ax3.set_title('실제 세션 검증 결과', fontsize=14, fontweight='bold')
            
            # 4. 입력 속성별 Taste ID 분포 - Vibe
            ax4 = fig.add_subplot(gs[1, 0])
            vibe_taste_map = {}
            
            for rs in real_sessions:
                if rs.get('passed', False) and 'onboarding_data' in rs:
                    vibe = rs['onboarding_data'].get('vibe')
                    taste_id = rs.get('taste_id')
                    if vibe and taste_id:
                        if vibe not in vibe_taste_map:
                            vibe_taste_map[vibe] = []
                        vibe_taste_map[vibe].append(taste_id)
            
            if vibe_taste_map:
                vibes = list(vibe_taste_map.keys())
                taste_means = [np.mean(vibe_taste_map[v]) for v in vibes]
                ax4.bar(vibes, taste_means, color='lightcoral', alpha=0.7)
                ax4.set_xlabel('Vibe')
                ax4.set_ylabel('평균 Taste ID')
                ax4.set_title('Vibe별 평균 Taste ID', fontsize=14, fontweight='bold')
                ax4.grid(True, alpha=0.3, axis='y')
            
            # 5. 입력 속성별 Taste ID 분포 - Household Size
            ax5 = fig.add_subplot(gs[1, 1])
            household_taste_map = {}
            
            for rs in real_sessions:
                if rs.get('passed', False) and 'onboarding_data' in rs:
                    household_size = rs['onboarding_data'].get('household_size')
                    taste_id = rs.get('taste_id')
                    if household_size is not None and taste_id:
                        if household_size not in household_taste_map:
                            household_taste_map[household_size] = []
                        household_taste_map[household_size].append(taste_id)
            
            if household_taste_map:
                household_sizes = sorted(household_taste_map.keys())
                taste_means = [np.mean(household_taste_map[hs]) for hs in household_sizes]
                ax5.plot(household_sizes, taste_means, marker='o', color='lightgreen', linewidth=2)
                ax5.set_xlabel('가구 인원수')
                ax5.set_ylabel('평균 Taste ID')
                ax5.set_title('가구 인원수별 평균 Taste ID', fontsize=14, fontweight='bold')
                ax5.grid(True, alpha=0.3)
            
            # 6. 입력 속성별 Taste ID 분포 - Budget Level
            ax6 = fig.add_subplot(gs[1, 2])
            budget_taste_map = {}
            
            for rs in real_sessions:
                if rs.get('passed', False) and 'onboarding_data' in rs:
                    budget_level = rs['onboarding_data'].get('budget_level')
                    taste_id = rs.get('taste_id')
                    if budget_level and taste_id:
                        if budget_level not in budget_taste_map:
                            budget_taste_map[budget_level] = []
                        budget_taste_map[budget_level].append(taste_id)
            
            if budget_taste_map:
                budget_levels = list(budget_taste_map.keys())
                taste_means = [np.mean(budget_taste_map[bl]) for bl in budget_levels]
                ax6.bar(budget_levels, taste_means, color='orange', alpha=0.7)
                ax6.set_xlabel('예산 수준')
                ax6.set_ylabel('평균 Taste ID')
                ax6.set_title('예산 수준별 평균 Taste ID', fontsize=14, fontweight='bold')
                ax6.grid(True, alpha=0.3, axis='y')
            
            # 7. 분포 테스트 결과 - Taste ID 커버리지
            ax7 = fig.add_subplot(gs[2, 0])
            if self.results['distribution_tests']:
                dist = self.results['distribution_tests']
                coverage = dist.get('coverage', 0)
                ax7.bar(['커버리지'], [coverage], color='plum', alpha=0.7)
                ax7.set_ylabel('커버리지 (%)')
                ax7.set_title(f'Taste ID 커버리지 ({coverage:.1f}%)', fontsize=14, fontweight='bold')
                ax7.set_ylim(0, 100)
                ax7.grid(True, alpha=0.3, axis='y')
            
            # 8. 분포 테스트 결과 - 상위 10개 Taste ID
            ax8 = fig.add_subplot(gs[2, 1])
            if self.results['distribution_tests']:
                dist = self.results['distribution_tests']
                taste_dist = dist.get('taste_distribution', {})
                if taste_dist:
                    sorted_tastes = sorted(taste_dist.items(), key=lambda x: x[1], reverse=True)[:10]
                    taste_ids_top = [str(t[0]) for t in sorted_tastes]
                    counts_top = [t[1] for t in sorted_tastes]
                    ax8.barh(taste_ids_top, counts_top, color='khaki', alpha=0.7)
                    ax8.set_xlabel('빈도')
                    ax8.set_ylabel('Taste ID')
                    ax8.set_title('상위 10개 Taste ID', fontsize=14, fontweight='bold')
                    ax8.grid(True, alpha=0.3, axis='x')
            
            # 9. 검증 항목별 통과율
            ax9 = fig.add_subplot(gs[2, 2])
            consistency_tests = self.results['consistency_tests']
            validation_items = {
                '입력 형식': sum(1 for tc in test_cases if tc.get('passed', False)) / len(test_cases) * 100 if test_cases else 0,
                '일관성': sum(1 for ct in consistency_tests if ct.get('passed', False)) / len(consistency_tests) * 100 if consistency_tests else 0,
                '실제 세션': passed_sessions / len(real_sessions) * 100 if real_sessions else 0,
            }
            
            items = list(validation_items.keys())
            rates = list(validation_items.values())
            ax9.barh(items, rates, color='steelblue', alpha=0.7)
            ax9.set_xlabel('통과율 (%)')
            ax9.set_title('검증 항목별 통과율', fontsize=14, fontweight='bold')
            ax9.set_xlim(0, 100)
            ax9.grid(True, alpha=0.3, axis='x')
            
            # 전체 제목
            total_tests = len(test_cases) + len(consistency_tests) + len(real_sessions)
            fig.suptitle(f'Taste 계산 로직 검증 결과 (총 {total_tests}개 테스트)', 
                        fontsize=16, fontweight='bold', y=0.995)
            
            # 저장
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_path = f'taste_calculation_validation_{timestamp}.png'
            plt.savefig(output_path, dpi=150, bbox_inches='tight')
            print(f"✅ 시각화 저장 완료: {output_path}")
            plt.close()
            
        except Exception as e:
            print(f"⚠️ 시각화 생성 중 오류: {e}")
            import traceback
            traceback.print_exc()


def main():
    """메인 함수"""
    validator = TasteCalculationValidator()
    success = validator.validate_all()
    
    if success:
        print("=" * 80)
        print("✅ Step 3 검증 완료: Taste 계산 로직이 올바르게 작동합니다!")
        print("=" * 80)
        return 0
    else:
        print("=" * 80)
        print("❌ Step 3 검증 실패: 일부 Taste 계산 로직에 문제가 있습니다.")
        print("=" * 80)
        return 1


if __name__ == '__main__':
    exit(main())

