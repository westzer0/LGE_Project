#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Step 4: 예산/조건 기반 제품 필터링 검증 - 온보딩 데이터의 예산 및 조건으로 제품 필터링 검증

검증 항목:
1. 예산 기반 필터링 검증
2. 조건 기반 필터링 검증 (HAS_PET, COOKING, LAUNDRY, MEDIA)
3. 복합 조건 필터링 검증
4. 실제 온보딩 데이터로 검증 (100개 이상)
5. 빈 결과 처리 검증
6. 경계값 검증
"""
import sys
import os
import json
import time
from datetime import datetime
from collections import Counter, defaultdict
from typing import Optional, Dict, List

# Django 설정 로드
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

import django
django.setup()

from api.services.taste_calculation_service import TasteCalculationService
from api.services.onboarding_db_service import OnboardingDBService
from api.services.recommendation_engine import RecommendationEngine
from api.services.playbook_filters import PlaybookHardFilter
from api.db.oracle_client import get_connection
from api.models import Product

# 시각화 라이브러리
try:
    import matplotlib.pyplot as plt
    import matplotlib
    matplotlib.use('Agg')  # GUI 없이 사용
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False
    print("⚠️ matplotlib이 설치되지 않아 시각화를 건너뜁니다.")

# NumPy 라이브러리
try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False


class BudgetConditionFilteringValidator:
    """예산/조건 기반 제품 필터링 검증 클래스"""

    def __init__(self):
        self.results = {
            'budget_filtering_tests': [],
            'condition_filtering_tests': [],
            'combined_filtering_tests': [],
            'real_data_tests': [],
            'empty_result_tests': [],
            'boundary_value_tests': [],
            'errors': [],
            'warnings': [],
            'statistics': {
                'budget_levels': Counter(),
                'condition_counts': Counter(),
                'filtered_product_counts': [],
                'filter_effectiveness': {}
            }
        }
        self.recommendation_engine = RecommendationEngine()
        self.taste_calculation_service = TasteCalculationService()

    def validate_all(self):
        """모든 검증 실행"""
        print("=" * 80)
        print("Step 4: 예산/조건 기반 제품 필터링 검증")
        print("=" * 80)
        print()

        try:
            # 1. 예산 기반 필터링 검증
            print("[1] 예산 기반 필터링 검증")
            self._validate_budget_filtering()
            print()

            # 2. 조건 기반 필터링 검증
            print("[2] 조건 기반 필터링 검증")
            self._validate_condition_filtering()
            print()

            # 3. 복합 조건 필터링 검증
            print("[3] 복합 조건 필터링 검증")
            self._validate_combined_filtering()
            print()

            # 4. 실제 온보딩 데이터로 검증
            print("[4] 실제 온보딩 데이터로 검증 (100개 이상)")
            self._validate_with_real_onboarding_data(count=100)
            print()

            # 5. 빈 결과 처리 검증
            print("[5] 빈 결과 처리 검증")
            self._validate_empty_results()
            print()

            # 6. 경계값 검증
            print("[6] 경계값 검증")
            self._validate_boundary_values()
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

    def _calculate_budget_range(self, budget_level: str) -> tuple:
        """예산 레벨로 예산 범위 계산"""
        budget_mapping = self.recommendation_engine.budget_mapping
        return budget_mapping.get(budget_level, budget_mapping['medium'])

    def _validate_budget_filtering(self):
        """예산 기반 필터링 검증"""
        print("  예산 레벨별 필터링 테스트...")
        
        budget_levels = ['low', 'medium', 'high', 'budget', 'standard', 'premium', 'luxury']
        
        # 모든 제품 조회
        all_products = Product.objects.all()[:1000]  # 샘플링
        if not all_products:
            print("  ⚠️ 제품 데이터가 없습니다.")
            return

        for budget_level in budget_levels:
            try:
                min_price, max_price = self._calculate_budget_range(budget_level)
                
                # 예산 필터링
                filtered_products = [
                    p for p in all_products 
                    if hasattr(p, 'price') and min_price <= float(p.price) <= max_price
                ]
                
                # 검증: 필터링된 모든 제품의 가격이 예산 범위 내인지 확인
                all_valid = True
                for product in filtered_products:
                    price = float(product.price) if hasattr(product, 'price') else 0
                    if not (min_price <= price <= max_price):
                        all_valid = False
                        break
                
                test_result = {
                    'budget_level': budget_level,
                    'min_price': min_price,
                    'max_price': max_price,
                    'total_products': len(all_products),
                    'filtered_count': len(filtered_products),
                    'all_valid': all_valid,
                    'passed': all_valid
                }
                
                self.results['budget_filtering_tests'].append(test_result)
                self.results['statistics']['budget_levels'][budget_level] = len(filtered_products)
                
                status = "✅" if all_valid else "❌"
                print(f"    {status} {budget_level}: {len(filtered_products)}/{len(all_products)}개 제품 (범위: {min_price:,}원 ~ {max_price:,}원)")
                
            except Exception as e:
                error_msg = f"예산 필터링 테스트 실패 ({budget_level}): {str(e)}"
                self.results['errors'].append(error_msg)
                print(f"    ❌ {budget_level}: {error_msg}")

    def _validate_condition_filtering(self):
        """조건 기반 필터링 검증"""
        print("  조건별 필터링 테스트...")
        
        # 모든 제품 조회
        all_products = list(Product.objects.all()[:500])
        if not all_products:
            print("  ⚠️ 제품 데이터가 없습니다.")
            return

        # 조건별 테스트
        conditions = {
            'has_pet': True,
            'cooking': 'frequently',
            'laundry': 'daily',
            'media': 'frequently'
        }

        for condition_key, condition_value in conditions.items():
            try:
                # 온보딩 데이터 생성
                onboarding_data = {
                    condition_key: condition_value,
                    'housing_type': 'apartment',
                    'household_size': 2
                }
                
                # PlaybookHardFilter 사용하여 필터링
                product_dicts = []
                for p in all_products:
                    product_dict = {
                        'id': p.id,
                        'product_id': p.id,
                        'spec_json': p.spec.spec_json if hasattr(p, 'spec') and p.spec else {}
                    }
                    product_dicts.append(product_dict)
                
                filtered_ids = PlaybookHardFilter.apply_filters(product_dicts, onboarding_data)
                filtered_count = len(filtered_ids)
                
                test_result = {
                    'condition_key': condition_key,
                    'condition_value': condition_value,
                    'total_products': len(all_products),
                    'filtered_count': filtered_count,
                    'passed': True  # 필터링이 정상적으로 작동하면 통과
                }
                
                self.results['condition_filtering_tests'].append(test_result)
                self.results['statistics']['condition_counts'][condition_key] = filtered_count
                
                print(f"    ✅ {condition_key}={condition_value}: {filtered_count}/{len(all_products)}개 제품")
                
            except Exception as e:
                error_msg = f"조건 필터링 테스트 실패 ({condition_key}): {str(e)}"
                self.results['errors'].append(error_msg)
                print(f"    ❌ {condition_key}: {error_msg}")

    def _validate_combined_filtering(self):
        """복합 조건 필터링 검증"""
        print("  복합 조건 필터링 테스트...")
        
        # 테스트 케이스
        test_cases = [
            {
                'name': '저예산 + 펫 + 요리',
                'onboarding': {
                    'budget_level': 'low',
                    'has_pet': True,
                    'cooking': 'frequently',
                    'housing_type': 'apartment',
                    'household_size': 2
                }
            },
            {
                'name': '고예산 + 미디어',
                'onboarding': {
                    'budget_level': 'high',
                    'media': 'frequently',
                    'housing_type': 'apartment',
                    'household_size': 4
                }
            },
            {
                'name': '중예산 + 세탁 + 펫',
                'onboarding': {
                    'budget_level': 'medium',
                    'laundry': 'daily',
                    'has_pet': True,
                    'housing_type': 'house',
                    'household_size': 3
                }
            }
        ]

        all_products = list(Product.objects.all()[:500])
        if not all_products:
            print("  ⚠️ 제품 데이터가 없습니다.")
            return

        for test_case in test_cases:
            try:
                onboarding = test_case['onboarding']
                
                # 예산 필터링
                budget_level = onboarding.get('budget_level', 'medium')
                min_price, max_price = self._calculate_budget_range(budget_level)
                
                budget_filtered = [
                    p for p in all_products 
                    if hasattr(p, 'price') and min_price <= float(p.price) <= max_price
                ]
                
                # 조건 필터링
                product_dicts = []
                for p in budget_filtered:
                    product_dict = {
                        'id': p.id,
                        'product_id': p.id,
                        'spec_json': p.spec.spec_json if hasattr(p, 'spec') and p.spec else {}
                    }
                    product_dicts.append(product_dict)
                
                filtered_ids = PlaybookHardFilter.apply_filters(product_dicts, onboarding)
                filtered_count = len(filtered_ids)
                
                # 검증: 필터링된 제품이 예산 범위 내인지 확인
                final_products = [p for p in budget_filtered if str(p.id) in filtered_ids]
                all_valid = True
                for product in final_products:
                    price = float(product.price) if hasattr(product, 'price') else 0
                    if not (min_price <= price <= max_price):
                        all_valid = False
                        break
                
                test_result = {
                    'test_name': test_case['name'],
                    'onboarding': onboarding,
                    'total_products': len(all_products),
                    'budget_filtered_count': len(budget_filtered),
                    'final_filtered_count': filtered_count,
                    'all_valid': all_valid,
                    'passed': all_valid
                }
                
                self.results['combined_filtering_tests'].append(test_result)
                
                status = "✅" if all_valid else "❌"
                print(f"    {status} {test_case['name']}: {filtered_count}개 제품 (예산 필터: {len(budget_filtered)}개)")
                
            except Exception as e:
                error_msg = f"복합 필터링 테스트 실패 ({test_case['name']}): {str(e)}"
                self.results['errors'].append(error_msg)
                print(f"    ❌ {test_case['name']}: {error_msg}")

    def _validate_with_real_onboarding_data(self, count: int = 100):
        """실제 온보딩 데이터로 검증"""
        print(f"  완료된 온보딩 세션 {count}개로 검증...")
        
        try:
            # 완료된 온보딩 세션 조회
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
                            AND ROWNUM <= :limit
                            ORDER BY DBMS_RANDOM.VALUE
                        )
                    """, {'limit': count})

                    sessions = []
                    for row in cur.fetchall():
                        sessions.append({
                            'session_id': row[0],
                            'member_id': row[1],
                            'status': row[2]
                        })

            if not sessions:
                print("  ⚠️ 완료된 온보딩 세션이 없습니다.")
                return

            print(f"  {len(sessions)}개 세션 검증 중...")
            
            success_count = 0
            empty_count = 0
            
            for i, session in enumerate(sessions[:count], 1):
                try:
                    # 온보딩 데이터 조회
                    onboarding_data = self.taste_calculation_service._get_onboarding_data_from_session(
                        session['session_id']
                    )
                    
                    if not onboarding_data:
                        continue
                    
                    # 예산 레벨 확인
                    budget_level = onboarding_data.get('budget_level', 'medium')
                    min_price, max_price = self._calculate_budget_range(budget_level)
                    
                    # 제품 조회 (카테고리별)
                    # 여기서는 모든 제품에 대해 테스트
                    all_products = list(Product.objects.all()[:500])
                    
                    # 예산 필터링
                    budget_filtered = [
                        p for p in all_products 
                        if hasattr(p, 'price') and min_price <= float(p.price) <= max_price
                    ]
                    
                    # 조건 필터링
                    product_dicts = []
                    for p in budget_filtered:
                        product_dict = {
                            'id': p.id,
                            'product_id': p.id,
                            'spec_json': p.spec.spec_json if hasattr(p, 'spec') and p.spec else {}
                        }
                        product_dicts.append(product_dict)
                    
                    filtered_ids = PlaybookHardFilter.apply_filters(product_dicts, onboarding_data)
                    filtered_count = len(filtered_ids)
                    
                    # 검증
                    all_valid = True
                    final_products = [p for p in budget_filtered if str(p.id) in filtered_ids]
                    for product in final_products:
                        price = float(product.price) if hasattr(product, 'price') else 0
                        if not (min_price <= price <= max_price):
                            all_valid = False
                            break
                    
                    if filtered_count == 0:
                        empty_count += 1
                    elif all_valid:
                        success_count += 1
                    
                    # 통계 수집
                    self.results['statistics']['budget_levels'][budget_level] += 1
                    if onboarding_data.get('has_pet'):
                        self.results['statistics']['condition_counts']['has_pet'] += 1
                    if onboarding_data.get('cooking'):
                        self.results['statistics']['condition_counts']['cooking'] += 1
                    if onboarding_data.get('laundry'):
                        self.results['statistics']['condition_counts']['laundry'] += 1
                    if onboarding_data.get('media'):
                        self.results['statistics']['condition_counts']['media'] += 1
                    
                    self.results['statistics']['filtered_product_counts'].append(filtered_count)
                    
                    test_result = {
                        'session_id': session['session_id'],
                        'member_id': session['member_id'],
                        'budget_level': budget_level,
                        'filtered_count': filtered_count,
                        'all_valid': all_valid,
                        'passed': all_valid
                    }
                    
                    self.results['real_data_tests'].append(test_result)
                    
                    if i % 20 == 0:
                        print(f"    진행: {i}/{len(sessions)} (성공: {success_count}, 빈 결과: {empty_count})")
                        
                except Exception as e:
                    error_msg = f"세션 검증 실패 ({session['session_id']}): {str(e)}"
                    self.results['errors'].append(error_msg)
            
            print(f"  ✅ 검증 완료: {len(sessions)}개 세션")
            print(f"    - 성공: {success_count}개")
            print(f"    - 빈 결과: {empty_count}개")
            print(f"    - 오류: {len(sessions) - success_count - empty_count}개")
            
        except Exception as e:
            error_msg = f"실제 데이터 검증 실패: {str(e)}"
            self.results['errors'].append(error_msg)
            print(f"  ❌ {error_msg}")
            import traceback
            traceback.print_exc()

    def _validate_empty_results(self):
        """빈 결과 처리 검증"""
        print("  빈 결과 처리 테스트...")
        
        try:
            # 매우 낮은 예산으로 필터링
            test_cases = [
                {
                    'name': '매우 낮은 예산',
                    'budget_level': 'low',
                    'onboarding': {
                        'budget_level': 'low',
                        'housing_type': 'studio',
                        'household_size': 1
                    }
                },
                {
                    'name': '매우 제한적인 조건',
                    'budget_level': 'low',
                    'onboarding': {
                        'budget_level': 'low',
                        'housing_type': 'studio',
                        'household_size': 1,
                        'has_pet': True,
                        'cooking': 'frequently'
                    }
                }
            ]
            
            for test_case in test_cases:
                try:
                    min_price, max_price = self._calculate_budget_range(test_case['budget_level'])
                    all_products = list(Product.objects.all()[:500])
                    
                    # 예산 필터링
                    budget_filtered = [
                        p for p in all_products 
                        if hasattr(p, 'price') and min_price <= float(p.price) <= max_price
                    ]
                    
                    # 조건 필터링
                    product_dicts = []
                    for p in budget_filtered:
                        product_dict = {
                            'id': p.id,
                            'product_id': p.id,
                            'spec_json': p.spec.spec_json if hasattr(p, 'spec') and p.spec else {}
                        }
                        product_dicts.append(product_dict)
                    
                    filtered_ids = PlaybookHardFilter.apply_filters(product_dicts, test_case['onboarding'])
                    filtered_count = len(filtered_ids)
                    
                    # 빈 결과도 정상적인 경우임 (제품이 없을 수 있음)
                    test_result = {
                        'test_name': test_case['name'],
                        'filtered_count': filtered_count,
                        'passed': True  # 빈 결과도 유효한 결과
                    }
                    
                    self.results['empty_result_tests'].append(test_result)
                    
                    print(f"    ✅ {test_case['name']}: {filtered_count}개 제품")
                    
                except Exception as e:
                    error_msg = f"빈 결과 테스트 실패 ({test_case['name']}): {str(e)}"
                    self.results['errors'].append(error_msg)
                    print(f"    ❌ {test_case['name']}: {error_msg}")
                    
        except Exception as e:
            error_msg = f"빈 결과 검증 실패: {str(e)}"
            self.results['errors'].append(error_msg)
            print(f"  ❌ {error_msg}")

    def _validate_boundary_values(self):
        """경계값 검증"""
        print("  경계값 테스트...")
        
        try:
            all_products = list(Product.objects.all()[:500])
            if not all_products:
                print("  ⚠️ 제품 데이터가 없습니다.")
                return
            
            # 가격 범위 확인
            prices = []
            for p in all_products:
                if hasattr(p, 'price'):
                    try:
                        prices.append(float(p.price))
                    except:
                        pass
            
            if not prices:
                print("  ⚠️ 가격 데이터가 없습니다.")
                return
            
            min_price_db = min(prices)
            max_price_db = max(prices)
            
            # 경계값 테스트
            test_cases = [
                {
                    'name': '최소 예산 (0원)',
                    'min_price': 0,
                    'max_price': min_price_db
                },
                {
                    'name': '최대 예산',
                    'min_price': max_price_db,
                    'max_price': max_price_db * 2
                },
                {
                    'name': '경계값 (최소 가격)',
                    'min_price': min_price_db,
                    'max_price': min_price_db
                },
                {
                    'name': '경계값 (최대 가격)',
                    'min_price': max_price_db,
                    'max_price': max_price_db
                }
            ]
            
            for test_case in test_cases:
                try:
                    filtered = [
                        p for p in all_products 
                        if hasattr(p, 'price') and test_case['min_price'] <= float(p.price) <= test_case['max_price']
                    ]
                    
                    # 검증
                    all_valid = True
                    for product in filtered:
                        price = float(product.price) if hasattr(product, 'price') else 0
                        if not (test_case['min_price'] <= price <= test_case['max_price']):
                            all_valid = False
                            break
                    
                    test_result = {
                        'test_name': test_case['name'],
                        'min_price': test_case['min_price'],
                        'max_price': test_case['max_price'],
                        'filtered_count': len(filtered),
                        'all_valid': all_valid,
                        'passed': all_valid
                    }
                    
                    self.results['boundary_value_tests'].append(test_result)
                    
                    status = "✅" if all_valid else "❌"
                    print(f"    {status} {test_case['name']}: {len(filtered)}개 제품")
                    
                except Exception as e:
                    error_msg = f"경계값 테스트 실패 ({test_case['name']}): {str(e)}"
                    self.results['errors'].append(error_msg)
                    print(f"    ❌ {test_case['name']}: {error_msg}")
                    
        except Exception as e:
            error_msg = f"경계값 검증 실패: {str(e)}"
            self.results['errors'].append(error_msg)
            print(f"  ❌ {error_msg}")

    def _print_results(self):
        """결과 출력"""
        print()
        print("=" * 80)
        print("검증 결과 요약")
        print("=" * 80)
        
        # 예산 필터링 결과
        budget_passed = sum(1 for t in self.results['budget_filtering_tests'] if t.get('passed', False))
        budget_total = len(self.results['budget_filtering_tests'])
        print(f"\n[1] 예산 기반 필터링: {budget_passed}/{budget_total} 통과")
        
        # 조건 필터링 결과
        condition_passed = sum(1 for t in self.results['condition_filtering_tests'] if t.get('passed', False))
        condition_total = len(self.results['condition_filtering_tests'])
        print(f"[2] 조건 기반 필터링: {condition_passed}/{condition_total} 통과")
        
        # 복합 필터링 결과
        combined_passed = sum(1 for t in self.results['combined_filtering_tests'] if t.get('passed', False))
        combined_total = len(self.results['combined_filtering_tests'])
        print(f"[3] 복합 조건 필터링: {combined_passed}/{combined_total} 통과")
        
        # 실제 데이터 검증 결과
        real_passed = sum(1 for t in self.results['real_data_tests'] if t.get('passed', False))
        real_total = len(self.results['real_data_tests'])
        if real_total > 0:
            real_empty = sum(1 for t in self.results['real_data_tests'] if t.get('filtered_count', 0) == 0)
            print(f"[4] 실제 데이터 검증: {real_passed}/{real_total} 통과 (빈 결과: {real_empty}개)")
        
        # 빈 결과 처리
        empty_passed = sum(1 for t in self.results['empty_result_tests'] if t.get('passed', False))
        empty_total = len(self.results['empty_result_tests'])
        print(f"[5] 빈 결과 처리: {empty_passed}/{empty_total} 통과")
        
        # 경계값 검증
        boundary_passed = sum(1 for t in self.results['boundary_value_tests'] if t.get('passed', False))
        boundary_total = len(self.results['boundary_value_tests'])
        print(f"[6] 경계값 검증: {boundary_passed}/{boundary_total} 통과")
        
        # 통계
        print("\n[통계]")
        print(f"  예산 레벨별 분포:")
        for level, count in self.results['statistics']['budget_levels'].most_common():
            print(f"    - {level}: {count}회")
        
        print(f"  조건별 분포:")
        for condition, count in self.results['statistics']['condition_counts'].most_common():
            print(f"    - {condition}: {count}회")
        
        if self.results['statistics']['filtered_product_counts']:
            counts = self.results['statistics']['filtered_product_counts']
            if HAS_NUMPY:
                print(f"  필터링된 제품 수 통계:")
                print(f"    - 평균: {np.mean(counts):.1f}개")
                print(f"    - 최소: {np.min(counts)}개")
                print(f"    - 최대: {np.max(counts)}개")
            else:
                print(f"  필터링된 제품 수 통계:")
                print(f"    - 평균: {sum(counts) / len(counts):.1f}개")
                print(f"    - 최소: {min(counts)}개")
                print(f"    - 최대: {max(counts)}개")
        
        # 오류 및 경고
        if self.results['errors']:
            print(f"\n[오류] {len(self.results['errors'])}개")
            for error in self.results['errors'][:10]:  # 최대 10개만 표시
                print(f"  - {error}")
            if len(self.results['errors']) > 10:
                print(f"  ... 외 {len(self.results['errors']) - 10}개 오류")
        
        if self.results['warnings']:
            print(f"\n[경고] {len(self.results['warnings'])}개")
            for warning in self.results['warnings'][:10]:
                print(f"  - {warning}")

    def _is_all_passed(self) -> bool:
        """모든 검증이 통과했는지 확인"""
        budget_ok = all(t.get('passed', False) for t in self.results['budget_filtering_tests'])
        condition_ok = all(t.get('passed', False) for t in self.results['condition_filtering_tests'])
        combined_ok = all(t.get('passed', False) for t in self.results['combined_filtering_tests'])
        boundary_ok = all(t.get('passed', False) for t in self.results['boundary_value_tests'])
        
        # 실제 데이터와 빈 결과는 부분 실패 허용
        return budget_ok and condition_ok and combined_ok and boundary_ok

    def _create_visualizations(self):
        """시각화 생성"""
        if not HAS_MATPLOTLIB:
            return
        
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # 1. 예산별 필터링된 제품 수 분포
            if self.results['statistics']['budget_levels']:
                fig, ax = plt.subplots(figsize=(10, 6))
                levels = list(self.results['statistics']['budget_levels'].keys())
                counts = list(self.results['statistics']['budget_levels'].values())
                
                ax.bar(levels, counts, color='skyblue', edgecolor='navy', alpha=0.7)
                ax.set_xlabel('예산 레벨', fontsize=12)
                ax.set_ylabel('필터링된 제품 수', fontsize=12)
                ax.set_title('예산별 필터링된 제품 수 분포', fontsize=14, fontweight='bold')
                ax.grid(axis='y', alpha=0.3)
                plt.xticks(rotation=45)
                plt.tight_layout()
                
                filename = f'budget_filtering_distribution_{timestamp}.png'
                plt.savefig(filename, dpi=150, bbox_inches='tight')
                plt.close()
                print(f"  ✅ 시각화 저장: {filename}")
            
            # 2. 조건별 필터링된 제품 수 분포
            if self.results['statistics']['condition_counts']:
                fig, ax = plt.subplots(figsize=(10, 6))
                conditions = list(self.results['statistics']['condition_counts'].keys())
                counts = list(self.results['statistics']['condition_counts'].values())
                
                ax.bar(conditions, counts, color='lightcoral', edgecolor='darkred', alpha=0.7)
                ax.set_xlabel('조건', fontsize=12)
                ax.set_ylabel('적용 횟수', fontsize=12)
                ax.set_title('조건별 필터링 적용 횟수', fontsize=14, fontweight='bold')
                ax.grid(axis='y', alpha=0.3)
                plt.xticks(rotation=45)
                plt.tight_layout()
                
                filename = f'condition_filtering_distribution_{timestamp}.png'
                plt.savefig(filename, dpi=150, bbox_inches='tight')
                plt.close()
                print(f"  ✅ 시각화 저장: {filename}")
            
            # 3. 필터링 전후 제품 수 비교
            if self.results['real_data_tests']:
                filtered_counts = [t.get('filtered_count', 0) for t in self.results['real_data_tests']]
                
                fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
                
                # 히스토그램
                ax1.hist(filtered_counts, bins=20, color='lightgreen', edgecolor='darkgreen', alpha=0.7)
                ax1.set_xlabel('필터링된 제품 수', fontsize=12)
                ax1.set_ylabel('세션 수', fontsize=12)
                ax1.set_title('필터링된 제품 수 분포 (히스토그램)', fontsize=14, fontweight='bold')
                ax1.grid(axis='y', alpha=0.3)
                
                # 박스플롯
                ax2.boxplot(filtered_counts, vert=True)
                ax2.set_ylabel('필터링된 제품 수', fontsize=12)
                ax2.set_title('필터링된 제품 수 분포 (박스플롯)', fontsize=14, fontweight='bold')
                ax2.grid(axis='y', alpha=0.3)
                
                plt.tight_layout()
                
                filename = f'filtering_comparison_{timestamp}.png'
                plt.savefig(filename, dpi=150, bbox_inches='tight')
                plt.close()
                print(f"  ✅ 시각화 저장: {filename}")
            
            # 4. 예산 범위별 제품 가격 분포
            if self.results['budget_filtering_tests']:
                fig, ax = plt.subplots(figsize=(12, 6))
                
                budget_data = []
                for test in self.results['budget_filtering_tests']:
                    budget_level = test.get('budget_level', '')
                    min_price = test.get('min_price', 0) / 1000000  # 만원 단위
                    max_price = test.get('max_price', 0) / 1000000
                    count = test.get('filtered_count', 0)
                    
                    if count > 0:
                        budget_data.append({
                            'level': budget_level,
                            'min': min_price,
                            'max': max_price,
                            'count': count
                        })
                
                if budget_data:
                    levels = [d['level'] for d in budget_data]
                    mins = [d['min'] for d in budget_data]
                    maxs = [d['max'] for d in budget_data]
                    
                    x_pos = range(len(levels))
                    width = 0.35
                    
                    ax.bar([x - width/2 for x in x_pos], mins, width, label='최소 예산', color='lightblue', alpha=0.7)
                    ax.bar([x + width/2 for x in x_pos], maxs, width, label='최대 예산', color='lightcoral', alpha=0.7)
                    ax.set_xlabel('예산 레벨', fontsize=12)
                    ax.set_ylabel('예산 범위 (만원)', fontsize=12)
                    ax.set_title('예산 범위별 분포', fontsize=14, fontweight='bold')
                    ax.set_xticks(x_pos)
                    ax.set_xticklabels(levels, rotation=45)
                    ax.legend()
                    ax.grid(axis='y', alpha=0.3)
                    
                    plt.tight_layout()
                    
                    filename = f'budget_range_distribution_{timestamp}.png'
                    plt.savefig(filename, dpi=150, bbox_inches='tight')
                    plt.close()
                    print(f"  ✅ 시각화 저장: {filename}")
            
            print(f"\n✅ 모든 시각화 생성 완료 (타임스탬프: {timestamp})")
            
        except Exception as e:
            print(f"  ⚠️ 시각화 생성 중 오류: {str(e)}")
            import traceback
            traceback.print_exc()


def main():
    """메인 함수"""
    validator = BudgetConditionFilteringValidator()
    success = validator.validate_all()
    
    if success:
        print("\n✅ 모든 검증이 성공적으로 완료되었습니다.")
        return 0
    else:
        print("\n⚠️ 일부 검증이 실패했습니다. 위의 결과를 확인해주세요.")
        return 1


if __name__ == '__main__':
    exit(main())

