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
            for i, session_id in enumerate(sample_sessions[:5], 1):  # 최대 5개만 테스트
                print(f"[{i}] SESSION_ID: {session_id} 검증 중...")
                result = self._validate_session_data(session_id)
                self.results['test_sessions'].append(result)
                print()
            
            # 3. 특수 케이스 검증 (NULL, 빈 배열 등)
            print("[특수 케이스 검증]")
            self._validate_edge_cases()
            print()
            
            # 4. 결과 출력
            self._print_results()
            
        except Exception as e:
            print(f"\n❌ 검증 중 예외 발생: {e}")
            import traceback
            traceback.print_exc()
            return False
        
        return self._is_all_passed()
    
    def _get_sample_sessions(self):
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
                    
                    # 샘플이 없으면 랜덤으로 5개 조회
                    if not existing_sessions:
                        cur.execute("""
                            SELECT SESSION_ID 
                            FROM (
                                SELECT SESSION_ID 
                                FROM ONBOARDING_SESSION 
                                ORDER BY DBMS_RANDOM.VALUE
                            ) WHERE ROWNUM <= 5
                        """)
                        existing_sessions = [row[0] for row in cur.fetchall()]
                    
                    return existing_sessions
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
            
            # 결과 출력
            if all_passed:
                print(f"  ✅ 모든 검증 통과")
            else:
                print(f"  ⚠️ 일부 검증 실패")
                for check_name, check_result in checks.items():
                    if not check_result.get('passed', False):
                        print(f"    - {check_name}: {check_result.get('message', '실패')}")
            
            # 상세 데이터 출력
            print(f"  [조회된 데이터]")
            print(f"    vibe: {retrieved_data.get('vibe')}")
            print(f"    household_size: {retrieved_data.get('household_size')}")
            print(f"    housing_type: {retrieved_data.get('housing_type')}")
            print(f"    pyung: {retrieved_data.get('pyung')}")
            print(f"    budget_level: {retrieved_data.get('budget_level')}")
            print(f"    priority: {retrieved_data.get('priority')}")
            print(f"    main_space: {retrieved_data.get('main_space')}")
            print(f"    has_pet: {retrieved_data.get('has_pet')} (원본: {raw_data.get('HAS_PET')})")
            print(f"    cooking: {retrieved_data.get('cooking')}")
            print(f"    laundry: {retrieved_data.get('laundry')}")
            print(f"    media: {retrieved_data.get('media')}")
            
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

