#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Step 4: MEMBER 테이블 저장 로직 검증 - TasteCalculationService가 MEMBER.TASTE에 올바르게 저장하는지 테스트

검증 항목:
1. MEMBER 테이블 저장 성공
2. TASTE 값 범위 검증 (1~120)
3. 전체 플로우 검증 (온보딩 데이터 조회 → Taste 계산 → MEMBER 테이블 저장)
4. MEMBER_ID 검증 (존재하는/존재하지 않는/NULL)
5. 데이터 일관성 검증
6. 트랜잭션 검증
7. NULL 값 처리
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


class TasteMemberStorageValidator:
    """MEMBER 테이블 저장 로직 검증 클래스"""
    
    def __init__(self):
        self.results = {
            'test_sessions': [],
            'member_id_tests': [],
            'consistency_tests': [],
            'range_tests': [],
            'null_tests': [],
            'errors': [],
            'warnings': [],
            'saved_tastes': []  # 저장된 TASTE 값들
        }
        # 테스트 중 변경된 MEMBER_ID와 원래 TASTE 값을 저장 (복원용)
        self.backup_data = {}
    
    def validate_all(self):
        """모든 검증 실행"""
        print("=" * 80)
        print("Step 4: MEMBER 테이블 저장 로직 검증")
        print("=" * 80)
        print()
        
        try:
            # 1. 기본 케이스: 실제 SESSION_ID와 MEMBER_ID로 전체 플로우 테스트
            print("[1] 기본 케이스: 실제 세션 데이터로 전체 플로우 테스트")
            self._validate_basic_flow()
            print()
            
            # 2. TASTE 값 범위 검증
            print("[2] TASTE 값 범위 검증 (1~120)")
            self._validate_taste_range()
            print()
            
            # 3. MEMBER_ID 검증
            print("[3] MEMBER_ID 검증")
            self._validate_member_ids()
            print()
            
            # 4. 데이터 일관성 검증
            print("[4] 데이터 일관성 검증")
            self._validate_consistency()
            print()
            
            # 5. NULL 값 처리 검증
            print("[5] NULL 값 처리 검증")
            self._validate_null_handling()
            print()
            
            # 6. 저장 후 조회 검증
            print("[6] 저장 후 조회 검증")
            self._validate_retrieval()
            print()
            
            # 7. 결과 출력
            self._print_results()
            
            # 8. 시각화 생성
            if HAS_MATPLOTLIB:
                self._create_visualizations()
            
            # 9. 테스트 데이터 복원 (선택적)
            # 실제 운영 환경에서는 복원하지 않을 수도 있음
            # self._restore_backup_data()
            
        except Exception as e:
            print(f"\n❌ 검증 중 예외 발생: {e}")
            import traceback
            traceback.print_exc()
            return False
        finally:
            # 테스트 데이터 복원
            self._restore_backup_data()
        
        return self._is_all_passed()
    
    def _get_sample_sessions(self, count=20):
        """실제 DB에서 테스트할 SESSION_ID와 MEMBER_ID 샘플 조회"""
        try:
            with get_connection() as conn:
                with conn.cursor() as cur:
                    # 실제 SESSION_ID 샘플 우선 조회
                    sample_ids = ['1764840383702', '1764840384247', '1764840384743']
                    
                    # 샘플 ID 중 존재하는 것만 필터링
                    existing_sessions = []
                    for session_id in sample_ids:
                        cur.execute("""
                            SELECT SESSION_ID, MEMBER_ID
                            FROM ONBOARDING_SESSION 
                            WHERE SESSION_ID = :session_id
                        """, {'session_id': session_id})
                        row = cur.fetchone()
                        if row:
                            existing_sessions.append({'session_id': row[0], 'member_id': row[1]})
                    
                    # 필요한 만큼 추가로 가져오기
                    if len(existing_sessions) < count:
                        placeholders = ','.join([f"'{s['session_id']}'" for s in existing_sessions])
                        where_clause = f"WHERE SESSION_ID NOT IN ({placeholders})" if existing_sessions else ""
                        
                        cur.execute(f"""
                            SELECT SESSION_ID, MEMBER_ID
                            FROM (
                                SELECT SESSION_ID, MEMBER_ID
                                FROM ONBOARDING_SESSION 
                                {where_clause}
                                ORDER BY DBMS_RANDOM.VALUE
                            ) WHERE ROWNUM <= :limit
                        """, {'limit': count - len(existing_sessions)})
                        additional_sessions = [
                            {'session_id': row[0], 'member_id': row[1]} 
                            for row in cur.fetchall()
                        ]
                        existing_sessions.extend(additional_sessions)
                    
                    return existing_sessions[:count]
        except Exception as e:
            self.results['errors'].append(f"샘플 세션 조회 실패: {str(e)}")
            return []
    
    def _get_member_taste(self, member_id: str):
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
        if member_id not in self.backup_data:
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
    
    def _validate_basic_flow(self):
        """기본 케이스: 실제 SESSION_ID와 MEMBER_ID로 전체 플로우 테스트"""
        sample_sessions = self._get_sample_sessions(100)
        
        if not sample_sessions:
            print("  ⚠️ 테스트할 세션이 없습니다.")
            return
        
        print(f"  테스트할 세션: {len(sample_sessions)}개")
        
        for i, session_info in enumerate(sample_sessions, 1):
            session_id = session_info['session_id']
            member_id = session_info['member_id']
            
            if not member_id:
                if i % 10 == 0 or i == len(sample_sessions):
                    print(f"  [{i}/{len(sample_sessions)}] 진행 중... (MEMBER_ID NULL 건너뜀)")
                continue
            
            if i % 10 == 0 or i == len(sample_sessions):
                print(f"  [{i}/{len(sample_sessions)}] 진행 중...", end=' ')
            else:
                print("", end="")  # 출력 없음
            
            try:
                # 백업
                self._backup_member_taste(member_id)
                
                # 저장 전 TASTE 값
                taste_before = self._get_member_taste(member_id)
                
                # 전체 플로우 실행: 온보딩 데이터 조회 → Taste 계산 → MEMBER 테이블 저장
                calculated_taste = TasteCalculationService.calculate_and_save_taste(
                    member_id=member_id,
                    onboarding_session_id=session_id
                )
                
                # 저장 후 TASTE 값
                taste_after = self._get_member_taste(member_id)
                
                # 검증
                result = {
                    'session_id': session_id,
                    'member_id': member_id,
                    'taste_before': taste_before,
                    'calculated_taste': calculated_taste,
                    'taste_after': taste_after,
                    'passed': False,
                    'checks': {}
                }
                
                # 검증 1: 계산된 TASTE가 1~120 범위인지
                range_check = 1 <= calculated_taste <= 120
                result['checks']['range'] = range_check
                
                # 검증 2: 저장 후 TASTE 값이 계산된 값과 일치하는지
                storage_check = taste_after == calculated_taste
                result['checks']['storage'] = storage_check
                
                # 검증 3: 반환값이 올바른지
                return_check = calculated_taste == taste_after
                result['checks']['return'] = return_check
                
                result['passed'] = range_check and storage_check and return_check
                
                if result['passed']:
                    if i % 10 == 0 or i == len(sample_sessions):
                        print(f"✅ (통과: {i}개)")
                    self.results['saved_tastes'].append(calculated_taste)
                else:
                    failed_checks = [k for k, v in result['checks'].items() if not v]
                    print(f"❌ (실패: {', '.join(failed_checks)})")
                    if not range_check:
                        self.results['errors'].append(f"범위 초과: {calculated_taste}")
                    if not storage_check:
                        self.results['errors'].append(f"저장 불일치: 계산={calculated_taste}, 저장={taste_after}")
                
                self.results['test_sessions'].append(result)
                
            except Exception as e:
                if i % 10 == 0 or i == len(sample_sessions):
                    print(f"❌ 예외 발생: {e}")
                self.results['errors'].append(f"세션 {session_id}: {str(e)}")
                self.results['test_sessions'].append({
                    'session_id': session_id,
                    'member_id': member_id,
                    'passed': False,
                    'error': str(e)
                })
    
    def _validate_taste_range(self):
        """TASTE 값 범위 검증"""
        # 실제 세션 데이터로 여러 번 테스트하여 범위 검증
        sample_sessions = self._get_sample_sessions(500)
        
        if not sample_sessions:
            print("  ⚠️ 테스트할 세션이 없습니다.")
            return
        
        out_of_range = []
        in_range = []
        
        print(f"  무작위 추출 세션: {len(sample_sessions)}개")
        
        for i, session_info in enumerate(sample_sessions, 1):
            session_id = session_info['session_id']
            member_id = session_info['member_id']
            
            if not member_id:
                continue
            
            try:
                # 백업
                self._backup_member_taste(member_id)
                
                # Taste 계산 및 저장
                calculated_taste = TasteCalculationService.calculate_and_save_taste(
                    member_id=member_id,
                    onboarding_session_id=session_id
                )
                
                if 1 <= calculated_taste <= 120:
                    in_range.append(calculated_taste)
                else:
                    out_of_range.append({
                        'session_id': session_id,
                        'member_id': member_id,
                        'taste': calculated_taste
                    })
                
                # 진행 상황 표시 (50개마다)
                if i % 50 == 0 or i == len(sample_sessions):
                    print(f"    진행 중... {i}/{len(sample_sessions)} (범위 내: {len(in_range)}개, 범위 초과: {len(out_of_range)}개)")
                
            except Exception as e:
                out_of_range.append({
                    'session_id': session_id,
                    'member_id': member_id,
                    'error': str(e)
                })
        
        if out_of_range:
            print(f"  ❌ 범위를 벗어난 케이스: {len(out_of_range)}개")
            for case in out_of_range[:5]:
                if 'error' in case:
                    print(f"    - 예외: {case['error']}")
                else:
                    print(f"    - Taste ID: {case['taste']} (범위: 1~120)")
            self.results['errors'].extend([f"범위 초과: {len(out_of_range)}개 케이스"])
        else:
            print(f"  ✅ {len(in_range)}개 테스트 모두 1~120 범위 내")
            print(f"     범위: {min(in_range)} ~ {max(in_range)}")
        
        self.results['range_tests'] = {
            'total': len(sample_sessions),
            'in_range': len(in_range),
            'out_of_range': len(out_of_range),
            'taste_values': in_range
        }
    
    def _validate_member_ids(self):
        """MEMBER_ID 검증"""
        # 1. 존재하는 MEMBER_ID로 저장 테스트
        print("  [1.1] 존재하는 MEMBER_ID로 저장 테스트")
        sample_sessions = self._get_sample_sessions(5)
        
        if sample_sessions:
            for session_info in sample_sessions[:3]:  # 최대 3개만 테스트
                member_id = session_info['member_id']
                if not member_id:
                    continue
                
                try:
                    # MEMBER 존재 확인
                    with get_connection() as conn:
                        with conn.cursor() as cur:
                            cur.execute("""
                                SELECT COUNT(*) FROM MEMBER WHERE MEMBER_ID = :member_id
                            """, {'member_id': member_id})
                            exists = cur.fetchone()[0] > 0
                    
                    if exists:
                        self._backup_member_taste(member_id)
                        taste_before = self._get_member_taste(member_id)
                        calculated_taste = TasteCalculationService.calculate_and_save_taste(
                            member_id=member_id,
                            onboarding_session_id=session_info['session_id']
                        )
                        taste_after = self._get_member_taste(member_id)
                        
                        if taste_after == calculated_taste:
                            print(f"    ✅ MEMBER_ID {member_id}: 저장 성공 (TASTE: {taste_before} → {taste_after})")
                        else:
                            print(f"    ❌ MEMBER_ID {member_id}: 저장 실패 (계산={calculated_taste}, 저장={taste_after})")
                    else:
                        print(f"    ⚠️ MEMBER_ID {member_id}: MEMBER 테이블에 존재하지 않음")
                        
                except Exception as e:
                    print(f"    ❌ MEMBER_ID {member_id}: 예외 발생 - {e}")
        
        # 2. 존재하지 않는 MEMBER_ID 처리 확인
        print("  [1.2] 존재하지 않는 MEMBER_ID 처리 확인")
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
                # 존재하지 않는 MEMBER_ID로 저장 시도
                # 이 경우 UPDATE 쿼리는 실행되지만 영향을 받는 행이 0개
                # 실제로는 에러가 발생하지 않지만, 저장은 되지 않음
                try:
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
                        
                except Exception as e:
                    print(f"    ✅ 존재하지 않는 MEMBER_ID: 예외 발생 (정상) - {e}")
            else:
                print(f"    ⚠️ 테스트용 MEMBER_ID가 이미 존재함")
                
        except Exception as e:
            print(f"    ❌ 존재하지 않는 MEMBER_ID 테스트 중 오류: {e}")
        
        # 3. GUEST MEMBER_ID로 저장 테스트
        print("  [1.3] GUEST MEMBER_ID로 저장 테스트")
        guest_member_id = 'GUEST'
        
        try:
            # GUEST MEMBER 존재 확인
            with get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT COUNT(*) FROM MEMBER WHERE MEMBER_ID = :member_id
                    """, {'member_id': guest_member_id})
                    exists = cur.fetchone()[0] > 0
            
            if exists:
                self._backup_member_taste(guest_member_id)
                taste_before = self._get_member_taste(guest_member_id)
                
                # 온보딩 데이터는 임의로 생성
                onboarding_data = {
                    'vibe': 'modern',
                    'household_size': 2,
                    'priority': ['design']
                }
                calculated_taste = TasteCalculationService.calculate_and_save_taste(
                    member_id=guest_member_id,
                    onboarding_data=onboarding_data
                )
                taste_after = self._get_member_taste(guest_member_id)
                
                if taste_after == calculated_taste:
                    print(f"    ✅ GUEST MEMBER_ID: 저장 성공 (TASTE: {taste_before} → {taste_after})")
                else:
                    print(f"    ❌ GUEST MEMBER_ID: 저장 실패 (계산={calculated_taste}, 저장={taste_after})")
            else:
                print(f"    ⚠️ GUEST MEMBER_ID가 MEMBER 테이블에 존재하지 않음")
                
        except Exception as e:
            print(f"    ❌ GUEST MEMBER_ID 테스트 중 오류: {e}")
    
    def _validate_consistency(self):
        """데이터 일관성 검증 - 동일한 온보딩 데이터로 여러 번 계산 시 동일한 TASTE 값 확인"""
        sample_sessions = self._get_sample_sessions(5)
        
        if not sample_sessions:
            print("  ⚠️ 테스트할 세션이 없습니다.")
            return
        
        for session_info in sample_sessions[:3]:  # 최대 3개만 테스트
            session_id = session_info['session_id']
            member_id = session_info['member_id']
            
            if not member_id:
                continue
            
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
                    print(f"    ✅ SESSION_ID {session_id}: {iterations}회 반복, 모두 Taste ID = {results[0]}")
                else:
                    print(f"    ❌ SESSION_ID {session_id}: {len(unique_results)}개의 서로 다른 결과")
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
                print(f"    ❌ SESSION_ID {session_id}: 예외 발생 - {e}")
                self.results['errors'].append(f"일관성 테스트 실패 (세션 {session_id}): {str(e)}")
    
    def _validate_null_handling(self):
        """NULL 값 처리 검증"""
        # TASTE가 NULL인 MEMBER 찾기
        try:
            with get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT MEMBER_ID 
                        FROM MEMBER 
                        WHERE TASTE IS NULL 
                        AND ROWNUM <= 3
                    """)
                    null_members = [row[0] for row in cur.fetchall()]
            
            if null_members:
                print(f"  TASTE가 NULL인 MEMBER {len(null_members)}개 발견")
                
                for member_id in null_members[:2]:  # 최대 2개만 테스트
                    try:
                        # 온보딩 데이터는 임의로 생성
                        onboarding_data = {
                            'vibe': 'classic',
                            'household_size': 3,
                            'priority': ['value']
                        }
                        
                        self._backup_member_taste(member_id)
                        calculated_taste = TasteCalculationService.calculate_and_save_taste(
                            member_id=member_id,
                            onboarding_data=onboarding_data
                        )
                        taste_after = self._get_member_taste(member_id)
                        
                        if taste_after is not None and taste_after == calculated_taste:
                            print(f"    ✅ MEMBER_ID {member_id}: NULL → {taste_after} 저장 성공")
                        else:
                            print(f"    ❌ MEMBER_ID {member_id}: NULL 처리 실패 (저장={taste_after})")
                        
                        self.results['null_tests'].append({
                            'member_id': member_id,
                            'taste_before': None,
                            'taste_after': taste_after,
                            'passed': taste_after is not None and taste_after == calculated_taste
                        })
                        
                    except Exception as e:
                        print(f"    ❌ MEMBER_ID {member_id}: 예외 발생 - {e}")
                        self.results['errors'].append(f"NULL 처리 테스트 실패 ({member_id}): {str(e)}")
            else:
                print("  ⚠️ TASTE가 NULL인 MEMBER를 찾을 수 없습니다")
                
        except Exception as e:
            print(f"  ❌ NULL 값 처리 검증 중 오류: {e}")
            self.results['errors'].append(f"NULL 값 처리 검증 실패: {str(e)}")
    
    def _validate_retrieval(self):
        """저장 후 조회 검증 - get_taste_for_member()로 올바른 값이 반환되는지 확인"""
        sample_sessions = self._get_sample_sessions(100)
        
        if not sample_sessions:
            print("  ⚠️ 테스트할 세션이 없습니다.")
            return
        
        passed = 0
        failed = 0
        
        print(f"  무작위 추출 세션: {len(sample_sessions)}개")
        
        for i, session_info in enumerate(sample_sessions, 1):
            session_id = session_info['session_id']
            member_id = session_info['member_id']
            
            if not member_id:
                continue
            
            try:
                # 백업
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
                    print(f"    ❌ MEMBER_ID {member_id}: 불일치 (저장={calculated_taste}, 조회={retrieved_taste})")
                    self.results['errors'].append(f"조회 불일치 ({member_id}): 저장={calculated_taste}, 조회={retrieved_taste}")
                
                # 진행 상황 표시 (10개마다)
                if i % 10 == 0 or i == len(sample_sessions):
                    print(f"    진행 중... {i}/{len(sample_sessions)} (통과: {passed}개, 실패: {failed}개)")
                
            except Exception as e:
                failed += 1
                print(f"    ❌ MEMBER_ID {member_id}: 예외 발생 - {e}")
                self.results['errors'].append(f"조회 테스트 실패 ({member_id}): {str(e)}")
        
        print(f"  ✅ 통과: {passed}개")
        if failed > 0:
            print(f"  ❌ 실패: {failed}개")
    
    def _print_results(self):
        """검증 결과 출력"""
        print("=" * 80)
        print("검증 결과 요약")
        print("=" * 80)
        
        # 기본 플로우 검증 결과
        test_sessions = self.results['test_sessions']
        passed_sessions = sum(1 for ts in test_sessions if ts.get('passed', False))
        print(f"\n[기본 플로우 검증]")
        print(f"  총 테스트 세션: {len(test_sessions)}개")
        print(f"  통과: {passed_sessions}개")
        print(f"  실패: {len(test_sessions) - passed_sessions}개")
        
        # 범위 검증 결과
        if self.results['range_tests']:
            range_tests = self.results['range_tests']
            print(f"\n[TASTE 값 범위 검증]")
            print(f"  총 테스트: {range_tests.get('total', 0)}개")
            print(f"  범위 내: {range_tests.get('in_range', 0)}개")
            print(f"  범위 초과: {range_tests.get('out_of_range', 0)}개")
            if range_tests.get('taste_values'):
                taste_values = range_tests['taste_values']
                print(f"  범위: {min(taste_values)} ~ {max(taste_values)}")
        
        # 일관성 검증 결과
        consistency_tests = self.results['consistency_tests']
        passed_consistency = sum(1 for ct in consistency_tests if ct.get('passed', False))
        print(f"\n[데이터 일관성 검증]")
        print(f"  총 테스트: {len(consistency_tests)}개")
        print(f"  통과: {passed_consistency}개")
        print(f"  실패: {len(consistency_tests) - passed_consistency}개")
        
        # NULL 값 처리 검증 결과
        null_tests = self.results['null_tests']
        passed_null = sum(1 for nt in null_tests if nt.get('passed', False))
        print(f"\n[NULL 값 처리 검증]")
        print(f"  총 테스트: {len(null_tests)}개")
        print(f"  통과: {passed_null}개")
        print(f"  실패: {len(null_tests) - passed_null}개")
        
        # 저장된 TASTE 값 통계
        if self.results['saved_tastes']:
            saved_tastes = self.results['saved_tastes']
            taste_counter = Counter(saved_tastes)
            print(f"\n[저장된 TASTE 값 통계]")
            print(f"  총 저장 횟수: {len(saved_tastes)}회")
            print(f"  고유 TASTE 값 수: {len(taste_counter)}개")
            print(f"  범위: {min(saved_tastes)} ~ {max(saved_tastes)}")
            print(f"  가장 많이 저장된 TASTE 값 (상위 5개):")
            for taste_id, count in taste_counter.most_common(5):
                print(f"    - Taste ID {taste_id}: {count}회 ({count/len(saved_tastes)*100:.1f}%)")
        
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
        # 기본 플로우 검증 모두 통과
        test_sessions_passed = all(
            ts.get('passed', False) 
            for ts in self.results['test_sessions']
            if 'passed' in ts
        )
        
        # 범위 검증 통과 (범위 초과가 없어야 함)
        range_passed = self.results['range_tests'].get('out_of_range', 0) == 0
        
        # 일관성 검증 모두 통과
        consistency_passed = all(
            ct.get('passed', False) 
            for ct in self.results['consistency_tests']
        )
        
        # 에러 없음
        no_errors = len(self.results['errors']) == 0
        
        return test_sessions_passed and range_passed and consistency_passed and no_errors
    
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
            test_sessions = self.results['test_sessions']
            passed_sessions = sum(1 for ts in test_sessions if ts.get('passed', False))
            failed_sessions = len(test_sessions) - passed_sessions
            
            if failed_sessions > 0:
                ax1.pie([passed_sessions, failed_sessions], 
                       labels=[f'통과 ({passed_sessions})', f'실패 ({failed_sessions})'],
                       autopct='%1.1f%%',
                       colors=['#4CAF50', '#F44336'],
                       startangle=90)
            else:
                ax1.pie([passed_sessions], 
                       labels=[f'통과 ({passed_sessions})'],
                       autopct='%1.1f%%',
                       colors=['#4CAF50'],
                       startangle=90)
            ax1.set_title('전체 검증 결과', fontsize=14, fontweight='bold')
            
            # 2. 저장된 TASTE 값 분포 히스토그램
            ax2 = fig.add_subplot(gs[0, 1])
            saved_tastes = self.results['saved_tastes']
            if saved_tastes:
                ax2.hist(saved_tastes, bins=120, range=(1, 121), 
                        color='skyblue', edgecolor='black', alpha=0.7)
                ax2.set_xlabel('Taste ID')
                ax2.set_ylabel('저장 횟수')
                ax2.set_title('저장된 TASTE 값 분포 (1~120)', fontsize=14, fontweight='bold')
                ax2.set_xlim(1, 120)
                ax2.grid(True, alpha=0.3, axis='y')
            else:
                ax2.text(0.5, 0.5, '저장된 TASTE 값 없음', 
                        ha='center', va='center', fontsize=12,
                        transform=ax2.transAxes)
                ax2.set_title('저장된 TASTE 값 분포', fontsize=14, fontweight='bold')
            
            # 3. 저장 성공/실패 비율
            ax3 = fig.add_subplot(gs[0, 2])
            if test_sessions:
                success_count = passed_sessions
                failure_count = failed_sessions
                if failure_count > 0:
                    ax3.pie([success_count, failure_count], 
                           labels=[f'성공 ({success_count})', f'실패 ({failure_count})'],
                           autopct='%1.1f%%',
                           colors=['#4CAF50', '#F44336'],
                           startangle=90)
                else:
                    ax3.pie([success_count], 
                           labels=[f'성공 ({success_count})'],
                           autopct='%1.1f%%',
                           colors=['#4CAF50'],
                           startangle=90)
                ax3.set_title('저장 성공/실패 비율', fontsize=14, fontweight='bold')
            
            # 4. TASTE 값 범위 분포
            ax4 = fig.add_subplot(gs[1, 0])
            if self.results['range_tests'] and self.results['range_tests'].get('taste_values'):
                taste_values = self.results['range_tests']['taste_values']
                ax4.hist(taste_values, bins=120, range=(1, 121), 
                        color='lightcoral', edgecolor='black', alpha=0.7)
                ax4.set_xlabel('Taste ID')
                ax4.set_ylabel('빈도')
                ax4.set_title('TASTE 값 범위 분포 (1~120)', fontsize=14, fontweight='bold')
                ax4.set_xlim(1, 120)
                ax4.grid(True, alpha=0.3, axis='y')
            
            # 5. 저장 전후 TASTE 값 비교
            ax5 = fig.add_subplot(gs[1, 1])
            before_after_data = []
            for ts in test_sessions:
                if 'taste_before' in ts and 'taste_after' in ts:
                    before_after_data.append({
                        'before': ts['taste_before'],
                        'after': ts['taste_after']
                    })
            
            if before_after_data:
                before_values = [d['before'] if d['before'] is not None else 0 for d in before_after_data]
                after_values = [d['after'] if d['after'] is not None else 0 for d in before_after_data]
                
                x = np.arange(len(before_after_data))
                width = 0.35
                ax5.bar(x - width/2, before_values, width, label='저장 전', color='lightgray', alpha=0.7)
                ax5.bar(x + width/2, after_values, width, label='저장 후', color='lightgreen', alpha=0.7)
                ax5.set_xlabel('테스트 케이스')
                ax5.set_ylabel('TASTE 값')
                ax5.set_title('저장 전후 TASTE 값 비교', fontsize=14, fontweight='bold')
                ax5.legend()
                ax5.grid(True, alpha=0.3, axis='y')
            
            # 6. 검증 항목별 통과율
            ax6 = fig.add_subplot(gs[1, 2])
            validation_items = {}
            
            # 기본 플로우
            if test_sessions:
                validation_items['기본 플로우'] = passed_sessions / len(test_sessions) * 100
            
            # 범위 검증
            if self.results['range_tests']:
                range_tests = self.results['range_tests']
                if range_tests.get('total', 0) > 0:
                    validation_items['범위 검증'] = range_tests.get('in_range', 0) / range_tests.get('total', 1) * 100
            
            # 일관성 검증
            consistency_tests = self.results['consistency_tests']
            if consistency_tests:
                passed_consistency = sum(1 for ct in consistency_tests if ct.get('passed', False))
                validation_items['일관성 검증'] = passed_consistency / len(consistency_tests) * 100
            
            # NULL 처리 검증
            null_tests = self.results['null_tests']
            if null_tests:
                passed_null = sum(1 for nt in null_tests if nt.get('passed', False))
                validation_items['NULL 처리'] = passed_null / len(null_tests) * 100 if null_tests else 0
            
            if validation_items:
                items = list(validation_items.keys())
                rates = list(validation_items.values())
                ax6.barh(items, rates, color='steelblue', alpha=0.7)
                ax6.set_xlabel('통과율 (%)')
                ax6.set_title('검증 항목별 통과율', fontsize=14, fontweight='bold')
                ax6.set_xlim(0, 100)
                ax6.grid(True, alpha=0.3, axis='x')
            
            # 7. TASTE 값별 저장 횟수 분포 (상위 20개)
            ax7 = fig.add_subplot(gs[2, 0])
            if saved_tastes:
                taste_counter = Counter(saved_tastes)
                top_tastes = taste_counter.most_common(20)
                taste_ids_top = [str(t[0]) for t in top_tastes]
                counts_top = [t[1] for t in top_tastes]
                ax7.barh(taste_ids_top, counts_top, color='plum', alpha=0.7)
                ax7.set_xlabel('저장 횟수')
                ax7.set_ylabel('Taste ID')
                ax7.set_title('상위 20개 TASTE 값별 저장 횟수', fontsize=14, fontweight='bold')
                ax7.grid(True, alpha=0.3, axis='x')
            
            # 8. 일관성 검증 결과
            ax8 = fig.add_subplot(gs[2, 1])
            consistency_tests = self.results['consistency_tests']
            if consistency_tests:
                passed_consistency = sum(1 for ct in consistency_tests if ct.get('passed', False))
                failed_consistency = len(consistency_tests) - passed_consistency
                if failed_consistency > 0:
                    ax8.pie([passed_consistency, failed_consistency], 
                           labels=[f'통과 ({passed_consistency})', f'실패 ({failed_consistency})'],
                           autopct='%1.1f%%',
                           colors=['#4CAF50', '#F44336'],
                           startangle=90)
                else:
                    ax8.pie([passed_consistency], 
                           labels=[f'통과 ({passed_consistency})'],
                           autopct='%1.1f%%',
                           colors=['#4CAF50'],
                           startangle=90)
                ax8.set_title('일관성 검증 결과', fontsize=14, fontweight='bold')
            
            # 9. NULL 처리 검증 결과
            ax9 = fig.add_subplot(gs[2, 2])
            null_tests = self.results['null_tests']
            if null_tests:
                passed_null = sum(1 for nt in null_tests if nt.get('passed', False))
                failed_null = len(null_tests) - passed_null
                if failed_null > 0:
                    ax9.pie([passed_null, failed_null], 
                           labels=[f'통과 ({passed_null})', f'실패 ({failed_null})'],
                           autopct='%1.1f%%',
                           colors=['#4CAF50', '#F44336'],
                           startangle=90)
                else:
                    ax9.pie([passed_null], 
                           labels=[f'통과 ({passed_null})'],
                           autopct='%1.1f%%',
                           colors=['#4CAF50'],
                           startangle=90)
                ax9.set_title('NULL 처리 검증 결과', fontsize=14, fontweight='bold')
            
            # 전체 제목
            total_tests = len(test_sessions) + len(consistency_tests) + len(null_tests)
            fig.suptitle(f'MEMBER 테이블 저장 로직 검증 결과 (총 {total_tests}개 테스트)', 
                        fontsize=16, fontweight='bold', y=0.995)
            
            # 저장
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_path = f'taste_member_storage_validation_{timestamp}.png'
            plt.savefig(output_path, dpi=150, bbox_inches='tight')
            print(f"✅ 시각화 저장 완료: {output_path}")
            plt.close()
            
        except Exception as e:
            print(f"⚠️ 시각화 생성 중 오류: {e}")
            import traceback
            traceback.print_exc()


def main():
    """메인 함수"""
    validator = TasteMemberStorageValidator()
    success = validator.validate_all()
    
    if success:
        print("=" * 80)
        print("✅ Step 4 검증 완료: MEMBER 테이블 저장 로직이 올바르게 작동합니다!")
        print("=" * 80)
        return 0
    else:
        print("=" * 80)
        print("❌ Step 4 검증 실패: 일부 MEMBER 테이블 저장 로직에 문제가 있습니다.")
        print("=" * 80)
        return 1


if __name__ == '__main__':
    exit(main())

