#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Step 2: 온보딩 데이터 조회 로직 검증

검증 항목:
1. ONBOARDING_SESSION 테이블에서 기본 데이터 읽기 성공
2. ONBOARD_SESS_MAIN_SPACES 테이블에서 MAIN_SPACE 배열 읽기 성공
3. ONBOARD_SESS_PRIORITIES 테이블에서 PRIORITY 배열 읽기 성공
4. 데이터 형식 변환 정확성 확인 (예: HAS_PET 'Y' → True)
5. NULL 값 처리 확인
6. 빈 배열 처리 확인
"""
import sys
import os
import json
from datetime import datetime
from collections import Counter

# Django 설정 로드
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

import django
django.setup()

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


class TasteDataRetrievalValidator:
    """온보딩 데이터 조회 로직 검증 클래스"""
    
    def __init__(self):
        self.results = {
            'test_sessions': [],
            'errors': [],
            'warnings': []
        }
    
    def validate_all(self):
        """모든 검증 실행"""
        print("=" * 80)
        print("Step 2: 온보딩 데이터 조회 로직 검증")
        print("=" * 80)
        print()
        
        try:
            # 1. 실제 SESSION_ID 샘플 조회
            sample_sessions = self._get_sample_sessions()
            
            if not sample_sessions:
                print("⚠️ 테스트할 세션이 없습니다. ONBOARDING_SESSION 테이블에 데이터가 있는지 확인하세요.")
                return False
            
            print(f"[1] 테스트할 세션 {len(sample_sessions)}개 발견")
            print()
            
            # 2. 각 세션별로 데이터 조회 검증
            test_count = min(20, len(sample_sessions))
            print(f"총 {test_count}개 세션 검증 시작...")
            print()
            
            for i, session_id in enumerate(sample_sessions[:test_count], 1):
                print(f"[{i}/{test_count}] SESSION_ID: {session_id} 검증 중...", end=' ')
                result = self._validate_session_data(session_id)
                self.results['test_sessions'].append(result)
                if result.get('passed', False):
                    print("✅")
                else:
                    print("❌")
            
            print()
            
            # 3. 특수 케이스 검증 (NULL, 빈 배열 등)
            print("[특수 케이스 검증]")
            self._validate_edge_cases()
            print()
            
            # 4. 결과 출력
            self._print_results()
            
            # 5. 시각화 생성
            if HAS_MATPLOTLIB:
                self._create_visualizations()
            
        except Exception as e:
            print(f"\n❌ 검증 중 예외 발생: {e}")
            import traceback
            traceback.print_exc()
            return False
        
        return self._is_all_passed()
    
    def _get_sample_sessions(self, count=20):
        """실제 DB에서 테스트할 SESSION_ID 샘플 조회"""
        try:
            with get_connection() as conn:
                with conn.cursor() as cur:
                    # 실제 SESSION_ID 샘플 우선 조회
                    sample_ids = ['1764840383702', '1764840384247', '1764840384743']
                    
                    # 샘플 ID 중 존재하는 것만 필터링
                    existing_sessions = []
                    for session_id in sample_ids:
                        cur.execute("""
                            SELECT COUNT(*) FROM ONBOARDING_SESSION WHERE SESSION_ID = :session_id
                        """, {'session_id': session_id})
                        if cur.fetchone()[0] > 0:
                            existing_sessions.append(session_id)
                    
                    # 필요한 만큼 추가로 가져오기
                    if len(existing_sessions) < count:
                        # IN 절을 위한 플레이스홀더 생성
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
                        """, {'limit': count - len(existing_sessions)})
                        additional_sessions = [row[0] for row in cur.fetchall()]
                        existing_sessions.extend(additional_sessions)
                    
                    return existing_sessions[:count]
        except Exception as e:
            self.results['errors'].append(f"샘플 세션 조회 실패: {str(e)}")
            return []
    
    def _validate_session_data(self, session_id: str) -> dict:
        """특정 세션의 데이터 조회 검증"""
        result = {
            'session_id': session_id,
            'passed': False,
            'checks': {},
            'raw_data': None,
            'retrieved_data': None,
            'errors': []
        }
        
        try:
            # 1. 원본 데이터 조회 (직접 SQL)
            raw_data = self._get_raw_session_data(session_id)
            result['raw_data'] = raw_data
            
            if not raw_data:
                result['errors'].append("세션을 찾을 수 없습니다")
                print(f"  ❌ 세션을 찾을 수 없습니다")
                return result
            
            # 2. TasteCalculationService를 통한 데이터 조회
            try:
                retrieved_data = TasteCalculationService._get_onboarding_data_from_session(session_id)
                result['retrieved_data'] = retrieved_data
            except Exception as e:
                result['errors'].append(f"데이터 조회 실패: {str(e)}")
                print(f"  ❌ 데이터 조회 실패: {e}")
                return result
            
            # 3. 각 검증 항목 확인
            checks = {}
            
            # 3.1 기본 필드 검증
            checks['basic_fields'] = self._check_basic_fields(raw_data, retrieved_data)
            
            # 3.2 MAIN_SPACE 배열 검증
            checks['main_space'] = self._check_main_space(session_id, retrieved_data)
            
            # 3.3 PRIORITY 배열 검증
            checks['priority'] = self._check_priority(session_id, retrieved_data)
            
            # 3.4 데이터 형식 변환 검증
            checks['data_conversion'] = self._check_data_conversion(raw_data, retrieved_data)
            
            # 3.5 NULL 값 처리 검증
            checks['null_handling'] = self._check_null_handling(retrieved_data)
            
            result['checks'] = checks
            
            # 전체 통과 여부
            all_passed = all(
                check.get('passed', False) 
                for check in checks.values()
            )
            result['passed'] = all_passed
            
            # 결과 출력 (간소화)
            if not all_passed:
                failed_checks = [name for name, check in checks.items() if not check.get('passed', False)]
                result['failed_checks'] = failed_checks
            
        except Exception as e:
            result['errors'].append(f"검증 중 예외: {str(e)}")
            print(f"  ❌ 검증 중 예외: {e}")
            import traceback
            traceback.print_exc()
        
        return result
    
    def _get_raw_session_data(self, session_id: str) -> dict:
        """원본 세션 데이터 직접 조회"""
        try:
            with get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT 
                            SESSION_ID,
                            VIBE,
                            HOUSEHOLD_SIZE,
                            HOUSING_TYPE,
                            PYUNG,
                            BUDGET_LEVEL,
                            PRIORITY,
                            HAS_PET,
                            COOKING,
                            LAUNDRY,
                            MEDIA
                        FROM ONBOARDING_SESSION
                        WHERE SESSION_ID = :session_id
                    """, {'session_id': session_id})
                    
                    cols = [c[0] for c in cur.description]
                    row = cur.fetchone()
                    
                    if row:
                        return dict(zip(cols, row))
                    return None
        except Exception as e:
            self.results['errors'].append(f"원본 데이터 조회 실패 ({session_id}): {str(e)}")
            return None
    
    def _check_basic_fields(self, raw_data: dict, retrieved_data: dict) -> dict:
        """기본 필드 검증"""
        check = {
            'passed': True,
            'message': '기본 필드 검증 통과',
            'details': []
        }
        
        fields_to_check = [
            ('VIBE', 'vibe'),
            ('HOUSEHOLD_SIZE', 'household_size'),
            ('HOUSING_TYPE', 'housing_type'),
            ('PYUNG', 'pyung'),
            ('BUDGET_LEVEL', 'budget_level'),
            ('COOKING', 'cooking'),
            ('LAUNDRY', 'laundry'),
            ('MEDIA', 'media'),
        ]
        
        for raw_key, retrieved_key in fields_to_check:
            raw_value = raw_data.get(raw_key)
            retrieved_value = retrieved_data.get(retrieved_key)
            
            # NULL 값은 기본값으로 처리될 수 있으므로 별도 검증
            if raw_value is None:
                # NULL인 경우 기본값이 설정되었는지 확인
                if retrieved_key in ['cooking', 'laundry', 'media']:
                    if retrieved_value is None:
                        check['passed'] = False
                        check['details'].append(f"{retrieved_key}: NULL인데 기본값이 설정되지 않음")
                else:
                    if retrieved_value != raw_value:
                        check['passed'] = False
                        check['details'].append(f"{retrieved_key}: NULL 값 불일치")
            else:
                if retrieved_value != raw_value:
                    check['passed'] = False
                    check['details'].append(f"{retrieved_key}: 값 불일치 (원본: {raw_value}, 조회: {retrieved_value})")
        
        if check['details']:
            check['message'] = f"기본 필드 검증 실패: {', '.join(check['details'])}"
        
        return check
    
    def _check_main_space(self, session_id: str, retrieved_data: dict) -> dict:
        """MAIN_SPACE 배열 검증"""
        check = {
            'passed': True,
            'message': 'MAIN_SPACE 배열 검증 통과',
            'details': []
        }
        
        try:
            # 정규화 테이블에서 직접 조회
            with get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT MAIN_SPACE 
                        FROM ONBOARD_SESS_MAIN_SPACES
                        WHERE SESSION_ID = :session_id
                        ORDER BY MAIN_SPACE
                    """, {'session_id': session_id})
                    
                    expected_main_spaces = [row[0] for row in cur.fetchall()]
                    retrieved_main_spaces = retrieved_data.get('main_space', [])
                    
                    # 빈 배열 처리 확인
                    if not expected_main_spaces and not retrieved_main_spaces:
                        check['message'] = 'MAIN_SPACE: 빈 배열 (정상)'
                    elif not expected_main_spaces and retrieved_main_spaces:
                        check['passed'] = False
                        check['message'] = f'MAIN_SPACE: 예상 빈 배열인데 조회된 값: {retrieved_main_spaces}'
                    elif expected_main_spaces != retrieved_main_spaces:
                        check['passed'] = False
                        check['message'] = f'MAIN_SPACE 불일치 (예상: {expected_main_spaces}, 조회: {retrieved_main_spaces})'
                    else:
                        check['message'] = f'MAIN_SPACE 일치: {retrieved_main_spaces}'
        except Exception as e:
            check['passed'] = False
            check['message'] = f'MAIN_SPACE 검증 중 오류: {str(e)}'
        
        return check
    
    def _check_priority(self, session_id: str, retrieved_data: dict) -> dict:
        """PRIORITY 배열 검증"""
        check = {
            'passed': True,
            'message': 'PRIORITY 배열 검증 통과',
            'details': []
        }
        
        try:
            # 정규화 테이블에서 직접 조회
            with get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT PRIORITY 
                        FROM ONBOARD_SESS_PRIORITIES
                        WHERE SESSION_ID = :session_id
                        ORDER BY PRIORITY_ORDER
                    """, {'session_id': session_id})
                    
                    expected_priorities = [row[0] for row in cur.fetchall()]
                    retrieved_priorities = retrieved_data.get('priority', [])
                    
                    # 정규화 테이블에 데이터가 있는 경우
                    if expected_priorities:
                        if expected_priorities != retrieved_priorities:
                            check['passed'] = False
                            check['message'] = f'PRIORITY 불일치 (예상: {expected_priorities}, 조회: {retrieved_priorities})'
                        else:
                            check['message'] = f'PRIORITY 일치: {retrieved_priorities}'
                    else:
                        # 정규화 테이블이 비어있으면 ONBOARDING_SESSION의 PRIORITY 컬럼 확인
                        cur.execute("""
                            SELECT PRIORITY 
                            FROM ONBOARDING_SESSION
                            WHERE SESSION_ID = :session_id
                        """, {'session_id': session_id})
                        row = cur.fetchone()
                        raw_priority = row[0] if row else None
                        
                        # 원본 PRIORITY가 있으면 배열로 변환되어야 함
                        if raw_priority:
                            expected = [raw_priority]
                            if retrieved_priorities == expected:
                                check['message'] = f'PRIORITY: 단일 값에서 배열로 변환됨: {retrieved_priorities}'
                            else:
                                check['passed'] = False
                                check['message'] = f'PRIORITY: 단일 값 변환 실패 (예상: {expected}, 조회: {retrieved_priorities})'
                        else:
                            # 원본도 NULL이면 빈 배열이어야 함
                            if retrieved_priorities == []:
                                check['message'] = 'PRIORITY: 빈 배열 (정상)'
                            else:
                                check['passed'] = False
                                check['message'] = f'PRIORITY: 예상 빈 배열인데 조회된 값: {retrieved_priorities}'
        except Exception as e:
            check['passed'] = False
            check['message'] = f'PRIORITY 검증 중 오류: {str(e)}'
        
        return check
    
    def _check_data_conversion(self, raw_data: dict, retrieved_data: dict) -> dict:
        """데이터 형식 변환 검증"""
        check = {
            'passed': True,
            'message': '데이터 형식 변환 검증 통과',
            'details': []
        }
        
        # HAS_PET 변환 확인 ('Y' → True, 'N' → False, NULL → False)
        raw_has_pet = raw_data.get('HAS_PET')
        retrieved_has_pet = retrieved_data.get('has_pet')
        
        expected_has_pet = False
        if raw_has_pet == 'Y':
            expected_has_pet = True
        elif raw_has_pet == 'N':
            expected_has_pet = False
        elif raw_has_pet is None:
            expected_has_pet = False
        
        if retrieved_has_pet != expected_has_pet:
            check['passed'] = False
            check['message'] = f'HAS_PET 변환 실패 (원본: {raw_has_pet}, 예상: {expected_has_pet}, 조회: {retrieved_has_pet})'
        else:
            check['message'] = f'HAS_PET 변환 성공 (원본: {raw_has_pet} → {retrieved_has_pet})'
        
        return check
    
    def _check_null_handling(self, retrieved_data: dict) -> dict:
        """NULL 값 처리 검증"""
        check = {
            'passed': True,
            'message': 'NULL 값 처리 검증 통과',
            'details': []
        }
        
        # 필수 필드는 None이 아니어야 함 (기본값 처리 확인)
        required_fields_with_defaults = {
            'cooking': 'sometimes',
            'laundry': 'weekly',
            'media': 'balanced'
        }
        
        for field, default_value in required_fields_with_defaults.items():
            value = retrieved_data.get(field)
            if value is None:
                check['passed'] = False
                check['details'].append(f"{field}: NULL인데 기본값({default_value})이 설정되지 않음")
            elif value == default_value:
                check['details'].append(f"{field}: 기본값({default_value}) 정상 설정")
        
        # 배열 필드는 빈 배열로 처리되어야 함
        array_fields = ['main_space', 'priority']
        for field in array_fields:
            value = retrieved_data.get(field)
            if value is None:
                check['passed'] = False
                check['details'].append(f"{field}: NULL인데 빈 배열로 변환되지 않음")
            elif not isinstance(value, list):
                check['passed'] = False
                check['details'].append(f"{field}: 배열이 아님 (타입: {type(value)})")
        
        if check['details']:
            check['message'] = f"NULL 값 처리 검증: {', '.join(check['details'])}"
        
        return check
    
    def _validate_edge_cases(self):
        """특수 케이스 검증 (NULL, 빈 배열 등)"""
        try:
            with get_connection() as conn:
                with conn.cursor() as cur:
                    # NULL 값이 많은 세션 찾기
                    cur.execute("""
                        SELECT SESSION_ID 
                        FROM ONBOARDING_SESSION
                        WHERE (HAS_PET IS NULL OR COOKING IS NULL OR LAUNDRY IS NULL)
                           AND ROWNUM <= 3
                    """)
                    
                    null_sessions = [row[0] for row in cur.fetchall()]
                    
                    if null_sessions:
                        print(f"  NULL 값이 있는 세션 {len(null_sessions)}개 발견")
                        for session_id in null_sessions[:2]:  # 최대 2개만 테스트
                            print(f"    - SESSION_ID: {session_id}")
                            try:
                                data = TasteCalculationService._get_onboarding_data_from_session(session_id)
                                print(f"      ✅ NULL 값 처리 성공")
                                print(f"        has_pet: {data.get('has_pet')} (타입: {type(data.get('has_pet'))})")
                                print(f"        cooking: {data.get('cooking')} (기본값: sometimes)")
                                print(f"        laundry: {data.get('laundry')} (기본값: weekly)")
                                print(f"        media: {data.get('media')} (기본값: balanced)")
                            except Exception as e:
                                print(f"      ❌ NULL 값 처리 실패: {e}")
                    else:
                        print("  ⚠️ NULL 값이 있는 세션을 찾을 수 없습니다")
                    
                    # 정규화 테이블이 비어있는 세션 찾기
                    cur.execute("""
                        SELECT s.SESSION_ID 
                        FROM ONBOARDING_SESSION s
                        WHERE NOT EXISTS (
                            SELECT 1 FROM ONBOARD_SESS_MAIN_SPACES m 
                            WHERE m.SESSION_ID = s.SESSION_ID
                        )
                        AND NOT EXISTS (
                            SELECT 1 FROM ONBOARD_SESS_PRIORITIES p 
                            WHERE p.SESSION_ID = s.SESSION_ID
                        )
                        AND ROWNUM <= 2
                    """)
                    
                    empty_normalized_sessions = [row[0] for row in cur.fetchall()]
                    
                    if empty_normalized_sessions:
                        print(f"  정규화 테이블이 비어있는 세션 {len(empty_normalized_sessions)}개 발견")
                        for session_id in empty_normalized_sessions[:1]:  # 최대 1개만 테스트
                            print(f"    - SESSION_ID: {session_id}")
                            try:
                                data = TasteCalculationService._get_onboarding_data_from_session(session_id)
                                main_space = data.get('main_space', [])
                                priority = data.get('priority', [])
                                
                                if isinstance(main_space, list) and isinstance(priority, list):
                                    print(f"      ✅ 빈 배열 처리 성공")
                                    print(f"        main_space: {main_space} (타입: {type(main_space)})")
                                    print(f"        priority: {priority} (타입: {type(priority)})")
                                else:
                                    print(f"      ❌ 빈 배열 처리 실패 (main_space: {type(main_space)}, priority: {type(priority)})")
                            except Exception as e:
                                print(f"      ❌ 빈 배열 처리 실패: {e}")
                    else:
                        print("  ⚠️ 정규화 테이블이 비어있는 세션을 찾을 수 없습니다")
        except Exception as e:
            print(f"  ❌ 특수 케이스 검증 중 오류: {e}")
            import traceback
            traceback.print_exc()
    
    def _print_results(self):
        """검증 결과 출력"""
        print("=" * 80)
        print("검증 결과 요약")
        print("=" * 80)
        
        total_sessions = len(self.results['test_sessions'])
        passed_sessions = sum(1 for r in self.results['test_sessions'] if r.get('passed', False))
        
        print(f"\n[세션 검증]")
        print(f"  총 테스트 세션: {total_sessions}개")
        print(f"  통과: {passed_sessions}개")
        print(f"  실패: {total_sessions - passed_sessions}개")
        
        if passed_sessions == total_sessions:
            print("  ✅ 모든 세션 검증 통과")
        else:
            print("  ⚠️ 일부 세션 검증 실패")
            for result in self.results['test_sessions']:
                if not result.get('passed', False):
                    print(f"\n  [실패 세션: {result.get('session_id')}]")
                    for check_name, check_result in result.get('checks', {}).items():
                        if not check_result.get('passed', False):
                            print(f"    - {check_name}: {check_result.get('message', '실패')}")
        
        # 에러
        if self.results['errors']:
            print("\n[에러]")
            for error in self.results['errors']:
                print(f"  ❌ {error}")
        
        # 경고
        if self.results['warnings']:
            print("\n[경고]")
            for warning in self.results['warnings']:
                print(f"  ⚠️ {warning}")
        
        print()
    
    def _is_all_passed(self):
        """모든 검증 통과 여부"""
        if not self.results['test_sessions']:
            return False
        
        return all(
            result.get('passed', False) 
            for result in self.results['test_sessions']
        )
    
    def _create_visualizations(self):
        """검증 결과 시각화"""
        if not HAS_MATPLOTLIB:
            return
        
        print("[시각화 생성 중...]")
        
        try:
            # 한글 폰트 설정
            plt.rcParams['font.family'] = 'Malgun Gothic'  # Windows
            plt.rcParams['axes.unicode_minus'] = False
            
            # 결과 데이터 수집
            test_sessions = self.results['test_sessions']
            total_count = len(test_sessions)
            passed_count = sum(1 for r in test_sessions if r.get('passed', False))
            failed_count = total_count - passed_count
            
            # 검증 항목별 통과/실패 통계
            check_stats = {
                'basic_fields': {'passed': 0, 'failed': 0},
                'main_space': {'passed': 0, 'failed': 0},
                'priority': {'passed': 0, 'failed': 0},
                'data_conversion': {'passed': 0, 'failed': 0},
                'null_handling': {'passed': 0, 'failed': 0},
            }
            
            # 데이터 분포 수집
            vibes = []
            household_sizes = []
            housing_types = []
            budget_levels = []
            priorities_list = []
            main_spaces_list = []
            has_pets = []
            
            for result in test_sessions:
                # 검증 항목별 통계
                for check_name in check_stats.keys():
                    check_result = result.get('checks', {}).get(check_name, {})
                    if check_result.get('passed', False):
                        check_stats[check_name]['passed'] += 1
                    else:
                        check_stats[check_name]['failed'] += 1
                
                # 데이터 분포
                retrieved_data = result.get('retrieved_data', {})
                if retrieved_data:
                    if retrieved_data.get('vibe'):
                        vibes.append(retrieved_data['vibe'])
                    if retrieved_data.get('household_size') is not None:
                        household_sizes.append(retrieved_data['household_size'])
                    if retrieved_data.get('housing_type'):
                        housing_types.append(retrieved_data['housing_type'])
                    if retrieved_data.get('budget_level'):
                        budget_levels.append(retrieved_data['budget_level'])
                    if retrieved_data.get('priority'):
                        priorities_list.extend(retrieved_data['priority'])
                    if retrieved_data.get('main_space'):
                        main_spaces_list.extend(retrieved_data['main_space'])
                    if retrieved_data.get('has_pet') is not None:
                        has_pets.append('반려동물 있음' if retrieved_data['has_pet'] else '반려동물 없음')
            
            # 시각화 생성
            fig = plt.figure(figsize=(20, 14))
            gs = fig.add_gridspec(3, 3, hspace=0.3, wspace=0.3)
            
            # 1. 전체 검증 결과 (파이 차트)
            ax1 = fig.add_subplot(gs[0, 0])
            if failed_count > 0:
                ax1.pie([passed_count, failed_count], 
                       labels=[f'통과 ({passed_count})', f'실패 ({failed_count})'],
                       autopct='%1.1f%%',
                       colors=['#4CAF50', '#F44336'],
                       startangle=90)
            else:
                ax1.pie([passed_count], 
                       labels=[f'통과 ({passed_count})'],
                       autopct='%1.1f%%',
                       colors=['#4CAF50'],
                       startangle=90)
            ax1.set_title('전체 검증 결과', fontsize=14, fontweight='bold')
            
            # 2. 검증 항목별 통과율 (바 차트)
            ax2 = fig.add_subplot(gs[0, 1])
            check_names = list(check_stats.keys())
            check_names_kr = {
                'basic_fields': '기본 필드',
                'main_space': 'MAIN_SPACE',
                'priority': 'PRIORITY',
                'data_conversion': '데이터 변환',
                'null_handling': 'NULL 처리'
            }
            check_labels = [check_names_kr.get(name, name) for name in check_names]
            passed_counts = [check_stats[name]['passed'] for name in check_names]
            failed_counts = [check_stats[name]['failed'] for name in check_names]
            
            x = np.arange(len(check_labels))
            width = 0.35
            ax2.bar(x - width/2, passed_counts, width, label='통과', color='#4CAF50', alpha=0.8)
            ax2.bar(x + width/2, failed_counts, width, label='실패', color='#F44336', alpha=0.8)
            ax2.set_xlabel('검증 항목')
            ax2.set_ylabel('세션 수')
            ax2.set_title('검증 항목별 통과/실패 현황', fontsize=14, fontweight='bold')
            ax2.set_xticks(x)
            ax2.set_xticklabels(check_labels, rotation=15, ha='right')
            ax2.legend()
            ax2.grid(True, alpha=0.3, axis='y')
            
            # 3. VIBE 분포
            ax3 = fig.add_subplot(gs[0, 2])
            if vibes:
                vibe_counts = Counter(vibes)
                vibes_sorted = sorted(vibe_counts.items(), key=lambda x: x[1], reverse=True)
                ax3.barh([v[0] for v in vibes_sorted], [v[1] for v in vibes_sorted], color='skyblue')
                ax3.set_xlabel('세션 수')
                ax3.set_title('VIBE 분포', fontsize=14, fontweight='bold')
                ax3.grid(True, alpha=0.3, axis='x')
            
            # 4. 가구 인원수 분포
            ax4 = fig.add_subplot(gs[1, 0])
            if household_sizes:
                ax4.hist(household_sizes, bins=range(1, max(household_sizes)+2), 
                        color='lightcoral', edgecolor='black', alpha=0.7)
                ax4.set_xlabel('가구 인원수')
                ax4.set_ylabel('세션 수')
                ax4.set_title('가구 인원수 분포', fontsize=14, fontweight='bold')
                ax4.grid(True, alpha=0.3, axis='y')
            
            # 5. 주거 형태 분포
            ax5 = fig.add_subplot(gs[1, 1])
            if housing_types:
                housing_counts = Counter(housing_types)
                housing_sorted = sorted(housing_counts.items(), key=lambda x: x[1], reverse=True)
                ax5.bar([h[0] for h in housing_sorted], [h[1] for h in housing_sorted], 
                       color='lightgreen')
                ax5.set_xlabel('주거 형태')
                ax5.set_ylabel('세션 수')
                ax5.set_title('주거 형태 분포', fontsize=14, fontweight='bold')
                ax5.tick_params(axis='x', rotation=15)
                ax5.grid(True, alpha=0.3, axis='y')
            
            # 6. 예산 수준 분포
            ax6 = fig.add_subplot(gs[1, 2])
            if budget_levels:
                budget_counts = Counter(budget_levels)
                budget_sorted = sorted(budget_counts.items(), key=lambda x: x[1], reverse=True)
                ax6.bar([b[0] for b in budget_sorted], [b[1] for b in budget_sorted], 
                       color='orange')
                ax6.set_xlabel('예산 수준')
                ax6.set_ylabel('세션 수')
                ax6.set_title('예산 수준 분포', fontsize=14, fontweight='bold')
                ax6.grid(True, alpha=0.3, axis='y')
            
            # 7. PRIORITY 분포
            ax7 = fig.add_subplot(gs[2, 0])
            if priorities_list:
                priority_counts = Counter(priorities_list)
                priority_sorted = sorted(priority_counts.items(), key=lambda x: x[1], reverse=True)
                ax7.barh([p[0] for p in priority_sorted], [p[1] for p in priority_sorted], 
                        color='plum')
                ax7.set_xlabel('세션 수')
                ax7.set_title('PRIORITY 분포', fontsize=14, fontweight='bold')
                ax7.grid(True, alpha=0.3, axis='x')
            
            # 8. MAIN_SPACE 분포
            ax8 = fig.add_subplot(gs[2, 1])
            if main_spaces_list:
                space_counts = Counter(main_spaces_list)
                space_sorted = sorted(space_counts.items(), key=lambda x: x[1], reverse=True)
                ax8.barh([s[0] for s in space_sorted], [s[1] for s in space_sorted], 
                        color='khaki')
                ax8.set_xlabel('세션 수')
                ax8.set_title('MAIN_SPACE 분포', fontsize=14, fontweight='bold')
                ax8.grid(True, alpha=0.3, axis='x')
            
            # 9. 반려동물 여부 분포
            ax9 = fig.add_subplot(gs[2, 2])
            if has_pets:
                pet_counts = Counter(has_pets)
                pet_sorted = sorted(pet_counts.items(), key=lambda x: x[1], reverse=True)
                ax9.pie([p[1] for p in pet_sorted], 
                       labels=[p[0] for p in pet_sorted],
                       autopct='%1.1f%%',
                       colors=['#FF9800', '#2196F3'],
                       startangle=90)
                ax9.set_title('반려동물 여부 분포', fontsize=14, fontweight='bold')
            
            # 전체 제목
            fig.suptitle(f'온보딩 데이터 조회 로직 검증 결과 (총 {total_count}개 세션)', 
                        fontsize=16, fontweight='bold', y=0.995)
            
            # 저장
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_path = f'taste_data_retrieval_validation_{timestamp}.png'
            plt.savefig(output_path, dpi=150, bbox_inches='tight')
            print(f"✅ 시각화 저장 완료: {output_path}")
            plt.close()
            
        except Exception as e:
            print(f"⚠️ 시각화 생성 중 오류: {e}")
            import traceback
            traceback.print_exc()


def main():
    """메인 함수"""
    validator = TasteDataRetrievalValidator()
    success = validator.validate_all()
    
    if success:
        print("=" * 80)
        print("✅ Step 2 검증 완료: 온보딩 데이터 조회 로직이 올바르게 작동합니다!")
        print("=" * 80)
        return 0
    else:
        print("=" * 80)
        print("❌ Step 2 검증 실패: 일부 데이터 조회 로직에 문제가 있습니다.")
        print("=" * 80)
        return 1


if __name__ == '__main__':
    exit(main())

