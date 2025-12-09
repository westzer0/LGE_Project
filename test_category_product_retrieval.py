#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Step 3: 카테고리별 제품 조회 로직 검증 - 선택된 카테고리로 제품을 조회하는 로직 검증

검증 항목:
1. 카테고리별 제품 조회 기능 검증
2. 여러 카테고리 처리 검증
3. 제품 정렬 로직 검증
4. 제품 제한 로직 검증
5. 실제 카테고리 데이터로 검증
6. 빈 결과 처리 검증
7. 성능 검증
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

from api.services.taste_based_recommendation_engine import TasteBasedRecommendationEngine
from api.utils.taste_category_selector import get_categories_for_taste
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


class CategoryProductRetrievalValidator:
    """카테고리별 제품 조회 로직 검증 클래스"""
    
    def __init__(self):
        self.engine = TasteBasedRecommendationEngine()
        self.results = {
            'single_category_tests': [],
            'multiple_categories_tests': [],
            'sorting_tests': [],
            'limit_tests': [],
            'real_category_tests': [],
            'empty_result_tests': [],
            'performance_metrics': {},
            'errors': [],
            'warnings': []
        }
    
    def validate_all(self):
        """모든 검증 실행"""
        print("=" * 80)
        print("Step 3: 카테고리별 제품 조회 로직 검증")
        print("=" * 80)
        print()
        
        try:
            # 1. 카테고리별 제품 조회 기능 검증
            print("[1] 카테고리별 제품 조회 기능 검증")
            self._validate_single_category_retrieval()
            print()
            
            # 2. 여러 카테고리 처리 검증
            print("[2] 여러 카테고리 처리 검증")
            self._validate_multiple_categories_retrieval()
            print()
            
            # 3. 제품 정렬 로직 검증
            print("[3] 제품 정렬 로직 검증")
            self._validate_sorting_logic()
            print()
            
            # 4. 제품 제한 로직 검증
            print("[4] 제품 제한 로직 검증")
            self._validate_limit_logic()
            print()
            
            # 5. 실제 카테고리 데이터로 검증
            print("[5] 실제 카테고리 데이터로 검증")
            self._validate_with_real_categories()
            print()
            
            # 6. 빈 결과 처리 검증
            print("[6] 빈 결과 처리 검증")
            self._validate_empty_results()
            print()
            
            # 7. 성능 검증
            print("[7] 성능 검증")
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
        
        return self._is_all_passed()
    
    def _get_available_categories(self) -> List[str]:
        """사용 가능한 카테고리 목록 조회"""
        try:
            with get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT DISTINCT MAIN_CATEGORY
                        FROM PRODUCT
                        WHERE STATUS = '판매중'
                        AND PRICE > 0
                        AND PRICE IS NOT NULL
                        ORDER BY MAIN_CATEGORY
                    """)
                    categories = [row[0] for row in cur.fetchall() if row[0]]
                    return categories
        except Exception as e:
            self.results['errors'].append(f"카테고리 목록 조회 실패: {str(e)}")
            return []
    
    def _validate_single_category_retrieval(self):
        """단일 카테고리 제품 조회 검증"""
        print("  [1.1] 단일 카테고리로 제품 조회 테스트")
        
        # 사용 가능한 카테고리 가져오기
        available_categories = self._get_available_categories()
        
        if not available_categories:
            print("  ⚠️ 사용 가능한 카테고리가 없습니다.")
            return
        
        print(f"  사용 가능한 카테고리: {len(available_categories)}개")
        print(f"  샘플 카테고리: {available_categories[:5]}")
        
        # 테스트할 카테고리 선택 (최대 10개)
        test_categories = available_categories[:10]
        
        user_profile = {
            'budget_level': 'medium',
            'vibe': 'modern',
            'household_size': 2,
            'housing_type': 'apartment',
            'priority': 'value'
        }
        
        passed = 0
        failed = 0
        
        for category in test_categories:
            try:
                # 제품 조회
                start_time = time.time()
                products = self.engine._filter_products_by_category(
                    category=category,
                    user_profile=user_profile
                )
                retrieval_time = time.time() - start_time
                
                # 검증
                result = {
                    'category': category,
                    'product_count': len(products),
                    'retrieval_time': retrieval_time,
                    'passed': False,
                    'checks': {}
                }
                
                # 검증 1: 제품이 조회되었는지 확인
                has_products = len(products) > 0
                result['checks']['has_products'] = has_products
                
                # 검증 2: 조회된 제품이 해당 카테고리에 속하는지 확인
                correct_category = True
                if products:
                    for product in products:
                        if product.get('MAIN_CATEGORY') != category:
                            correct_category = False
                            break
                result['checks']['correct_category'] = correct_category
                
                # 검증 3: 필수 필드 존재 확인
                required_fields = ['PRODUCT_ID', 'PRODUCT_NAME', 'MAIN_CATEGORY', 'PRICE']
                has_required_fields = True
                if products:
                    for product in products[:5]:  # 처음 5개만 확인
                        for field in required_fields:
                            if field not in product:
                                has_required_fields = False
                                break
                        if not has_required_fields:
                            break
                result['checks']['has_required_fields'] = has_required_fields
                
                # 검증 4: 가격이 유효한지 확인
                valid_prices = True
                if products:
                    for product in products[:5]:  # 처음 5개만 확인
                        price = product.get('PRICE')
                        if price is None or price <= 0:
                            valid_prices = False
                            break
                result['checks']['valid_prices'] = valid_prices
                
                result['passed'] = all(result['checks'].values())
                
                if result['passed']:
                    passed += 1
                    print(f"    ✅ {category}: {len(products)}개 제품 조회 성공 ({retrieval_time:.3f}초)")
                else:
                    failed += 1
                    failed_checks = [k for k, v in result['checks'].items() if not v]
                    print(f"    ❌ {category}: 검증 실패 ({', '.join(failed_checks)})")
                
                self.results['single_category_tests'].append(result)
                
            except Exception as e:
                failed += 1
                print(f"    ❌ {category}: 예외 발생 - {e}")
                self.results['errors'].append(f"단일 카테고리 조회 실패 ({category}): {str(e)}")
        
        print(f"  ✅ 통과: {passed}개")
        if failed > 0:
            print(f"  ❌ 실패: {failed}개")
    
    def _validate_multiple_categories_retrieval(self):
        """여러 카테고리 제품 조회 검증"""
        print("  [2.1] 여러 카테고리로 제품 조회 테스트")
        
        available_categories = self._get_available_categories()
        
        if len(available_categories) < 3:
            print("  ⚠️ 테스트할 카테고리가 부족합니다 (최소 3개 필요).")
            return
        
        # 테스트할 카테고리 선택 (3~5개)
        test_categories = available_categories[:5]
        
        user_profile = {
            'budget_level': 'medium',
            'vibe': 'modern',
            'household_size': 2,
            'housing_type': 'apartment',
            'priority': 'value'
        }
        
        try:
            # 각 카테고리별로 제품 조회
            all_products = []
            category_product_counts = {}
            category_products_map = {}
            
            for category in test_categories:
                start_time = time.time()
                products = self.engine._filter_products_by_category(
                    category=category,
                    user_profile=user_profile
                )
                retrieval_time = time.time() - start_time
                
                category_product_counts[category] = len(products)
                category_products_map[category] = products
                all_products.extend(products)
            
            # 검증
            result = {
                'categories': test_categories,
                'category_product_counts': category_product_counts,
                'total_products': len(all_products),
                'passed': False,
                'checks': {}
            }
            
            # 검증 1: 모든 카테고리에서 제품이 조회되었는지 확인
            all_have_products = all(count > 0 for count in category_product_counts.values())
            result['checks']['all_have_products'] = all_have_products
            
            # 검증 2: 중복 제품 확인 (PRODUCT_ID 기준)
            product_ids = [p.get('PRODUCT_ID') for p in all_products if p.get('PRODUCT_ID')]
            unique_product_ids = set(product_ids)
            has_duplicates = len(product_ids) != len(unique_product_ids)
            result['checks']['has_duplicates'] = has_duplicates
            result['duplicate_count'] = len(product_ids) - len(unique_product_ids)
            
            # 검증 3: 각 카테고리별 제품이 올바른 카테고리에 속하는지 확인
            correct_categories = True
            for category, products in category_products_map.items():
                for product in products:
                    if product.get('MAIN_CATEGORY') != category:
                        correct_categories = False
                        break
                if not correct_categories:
                    break
            result['checks']['correct_categories'] = correct_categories
            
            result['passed'] = all([
                result['checks']['all_have_products'],
                result['checks']['correct_categories']
            ])
            
            if result['passed']:
                print(f"    ✅ {len(test_categories)}개 카테고리: 총 {len(all_products)}개 제품 조회 성공")
                print(f"      카테고리별 제품 수:")
                for category, count in category_product_counts.items():
                    print(f"        - {category}: {count}개")
                if has_duplicates:
                    print(f"      ⚠️ 중복 제품: {result['duplicate_count']}개")
            else:
                failed_checks = [k for k, v in result['checks'].items() if not v]
                print(f"    ❌ 검증 실패 ({', '.join(failed_checks)})")
            
            self.results['multiple_categories_tests'].append(result)
            
        except Exception as e:
            print(f"    ❌ 예외 발생: {e}")
            self.results['errors'].append(f"여러 카테고리 조회 실패: {str(e)}")
    
    def _validate_sorting_logic(self):
        """제품 정렬 로직 검증"""
        print("  [3.1] 제품 정렬 로직 검증")
        
        available_categories = self._get_available_categories()
        
        if not available_categories:
            print("  ⚠️ 사용 가능한 카테고리가 없습니다.")
            return
        
        # 테스트할 카테고리 선택
        test_category = available_categories[0]
        
        user_profile = {
            'budget_level': 'medium',
            'vibe': 'modern',
            'household_size': 2,
            'housing_type': 'apartment',
            'priority': 'value'
        }
        
        try:
            products = self.engine._filter_products_by_category(
                category=test_category,
                user_profile=user_profile
            )
            
            if len(products) < 2:
                print(f"    ⚠️ {test_category}: 제품이 부족하여 정렬 검증을 건너뜁니다 ({len(products)}개)")
                return
            
            # 정렬 확인: 코드에서 ORDER BY PRICE로 정렬되어 있음
            prices = [p.get('PRICE', 0) for p in products if p.get('PRICE')]
            
            result = {
                'category': test_category,
                'product_count': len(products),
                'passed': False,
                'checks': {}
            }
            
            # 검증: 가격이 오름차순으로 정렬되어 있는지 확인
            is_sorted_asc = prices == sorted(prices)
            result['checks']['is_sorted_asc'] = is_sorted_asc
            
            # 가격 분포 확인
            if prices:
                result['min_price'] = min(prices)
                result['max_price'] = max(prices)
                result['avg_price'] = sum(prices) / len(prices) if prices else 0
            
            result['passed'] = is_sorted_asc
            
            if result['passed']:
                print(f"    ✅ {test_category}: 가격 오름차순 정렬 확인 ({len(products)}개 제품)")
                if prices:
                    print(f"      가격 범위: {result['min_price']:,}원 ~ {result['max_price']:,}원")
            else:
                print(f"    ❌ {test_category}: 정렬 검증 실패")
            
            self.results['sorting_tests'].append(result)
            
        except Exception as e:
            print(f"    ❌ 예외 발생: {e}")
            self.results['errors'].append(f"정렬 로직 검증 실패: {str(e)}")
    
    def _validate_limit_logic(self):
        """제품 제한 로직 검증"""
        print("  [4.1] 제품 제한 로직 검증")
        
        # 제한 로직은 _filter_products_by_category에서 직접 구현되지 않음
        # 대신 get_recommendations에서 limit_per_category로 제한됨
        # 따라서 get_recommendations를 사용하여 검증
        
        available_categories = self._get_available_categories()
        
        if not available_categories:
            print("  ⚠️ 사용 가능한 카테고리가 없습니다.")
            return
        
        # 테스트용 taste_id와 user_profile
        taste_id = 50
        user_profile = {
            'budget_level': 'medium',
            'vibe': 'modern',
            'household_size': 2,
            'housing_type': 'apartment',
            'priority': 'value',
            'onboarding_data': {}
        }
        
        try:
            # limit_per_category를 3으로 설정하여 테스트
            limit_per_category = 3
            result = self.engine.get_recommendations(
                user_profile=user_profile,
                taste_id=taste_id,
                num_categories=3,
                limit_per_category=limit_per_category
            )
            
            if not result.get('success'):
                print(f"    ⚠️ 추천 실패: {result.get('message', 'Unknown error')}")
                return
            
            categories = result.get('categories', [])
            recommendations = result.get('recommendations', [])
            
            # 카테고리별 제품 수 확인
            category_counts = defaultdict(int)
            for rec in recommendations:
                category_counts[rec.get('category')] += 1
            
            result_data = {
                'limit_per_category': limit_per_category,
                'categories': categories,
                'category_counts': dict(category_counts),
                'total_products': len(recommendations),
                'passed': False,
                'checks': {}
            }
            
            # 검증: 각 카테고리별 제품 수가 limit_per_category 이하인지 확인
            all_within_limit = all(
                count <= limit_per_category 
                for count in category_counts.values()
            )
            result_data['checks']['all_within_limit'] = all_within_limit
            
            result_data['passed'] = all_within_limit
            
            if result_data['passed']:
                print(f"    ✅ limit_per_category={limit_per_category}: 모든 카테고리가 제한 내 ({len(recommendations)}개 제품)")
                print(f"      카테고리별 제품 수:")
                for category, count in category_counts.items():
                    print(f"        - {category}: {count}개")
            else:
                print(f"    ❌ 제한 로직 검증 실패")
                for category, count in category_counts.items():
                    if count > limit_per_category:
                        print(f"      - {category}: {count}개 (제한 초과)")
            
            self.results['limit_tests'].append(result_data)
            
        except Exception as e:
            print(f"    ❌ 예외 발생: {e}")
            self.results['errors'].append(f"제한 로직 검증 실패: {str(e)}")
    
    def _validate_with_real_categories(self):
        """실제 카테고리 데이터로 검증 (Step 2에서 선택된 카테고리 사용)"""
        print("  [5.1] Step 2에서 선택된 실제 카테고리로 제품 조회 테스트")
        
        # 여러 taste_id로 테스트
        test_taste_ids = [1, 25, 50, 75, 100]
        
        user_profile = {
            'budget_level': 'medium',
            'vibe': 'modern',
            'household_size': 2,
            'housing_type': 'apartment',
            'priority': 'value',
            'onboarding_data': {}
        }
        
        passed = 0
        failed = 0
        
        for taste_id in test_taste_ids:
            try:
                # Step 2: Taste별로 카테고리 선택
                selected_categories = get_categories_for_taste(
                    taste_id=taste_id,
                    onboarding_data=user_profile.get('onboarding_data', {}),
                    num_categories=5
                )
                
                if not selected_categories:
                    print(f"    ⚠️ Taste ID {taste_id}: 선택된 카테고리 없음")
                    continue
                
                # 각 카테고리별로 제품 조회
                category_product_counts = {}
                all_products_count = 0
                
                for category in selected_categories:
                    products = self.engine._filter_products_by_category(
                        category=category,
                        user_profile=user_profile
                    )
                    category_product_counts[category] = len(products)
                    all_products_count += len(products)
                
                result = {
                    'taste_id': taste_id,
                    'categories': selected_categories,
                    'category_product_counts': category_product_counts,
                    'total_products': all_products_count,
                    'passed': False,
                    'checks': {}
                }
                
                # 검증: 모든 카테고리에 대해 제품이 조회되었는지 확인
                all_have_products = all(count > 0 for count in category_product_counts.values())
                result['checks']['all_have_products'] = all_have_products
                
                # 검증: 각 카테고리별로 최소 1개 이상의 제품 존재
                min_products_per_category = min(category_product_counts.values()) if category_product_counts else 0
                result['checks']['min_products_per_category'] = min_products_per_category >= 1
                
                result['passed'] = all_have_products and min_products_per_category >= 1
                
                if result['passed']:
                    passed += 1
                    print(f"    ✅ Taste ID {taste_id}: {len(selected_categories)}개 카테고리, 총 {all_products_count}개 제품")
                    for category, count in category_product_counts.items():
                        print(f"        - {category}: {count}개")
                else:
                    failed += 1
                    failed_checks = [k for k, v in result['checks'].items() if not v]
                    print(f"    ❌ Taste ID {taste_id}: 검증 실패 ({', '.join(failed_checks)})")
                
                self.results['real_category_tests'].append(result)
                
            except Exception as e:
                failed += 1
                print(f"    ❌ Taste ID {taste_id}: 예외 발생 - {e}")
                self.results['errors'].append(f"실제 카테고리 검증 실패 (Taste ID {taste_id}): {str(e)}")
        
        print(f"  ✅ 통과: {passed}개")
        if failed > 0:
            print(f"  ❌ 실패: {failed}개")
    
    def _validate_empty_results(self):
        """빈 결과 처리 검증"""
        print("  [6.1] 제품이 없는 카테고리 처리 확인")
        
        # 존재하지 않는 카테고리로 테스트
        non_existent_category = 'NON_EXISTENT_CATEGORY_12345'
        
        user_profile = {
            'budget_level': 'medium',
            'vibe': 'modern',
            'household_size': 2,
            'housing_type': 'apartment',
            'priority': 'value'
        }
        
        try:
            products = self.engine._filter_products_by_category(
                category=non_existent_category,
                user_profile=user_profile
            )
            
            result = {
                'category': non_existent_category,
                'product_count': len(products),
                'passed': False,
                'checks': {}
            }
            
            # 검증: 빈 리스트 반환 확인
            is_empty_list = isinstance(products, list) and len(products) == 0
            result['checks']['is_empty_list'] = is_empty_list
            
            # 검증: 에러가 발생하지 않아야 함
            no_error = True
            result['checks']['no_error'] = no_error
            
            result['passed'] = is_empty_list and no_error
            
            if result['passed']:
                print(f"    ✅ 존재하지 않는 카테고리: 빈 리스트 반환 (정상)")
            else:
                print(f"    ❌ 빈 결과 처리 검증 실패")
            
            self.results['empty_result_tests'].append(result)
            
        except Exception as e:
            print(f"    ❌ 예외 발생: {e}")
            self.results['errors'].append(f"빈 결과 처리 검증 실패: {str(e)}")
        
        print("  [6.2] 빈 카테고리 리스트 처리 확인")
        
        # 빈 카테고리 리스트로 테스트
        try:
            result = self.engine.get_recommendations(
                user_profile=user_profile,
                taste_id=1,
                num_categories=0  # 0개 카테고리
            )
            
            # 빈 카테고리 리스트는 get_categories_for_taste에서 처리되므로
            # success=False가 반환되어야 함
            is_handled = not result.get('success', True)
            
            if is_handled:
                print(f"    ✅ 빈 카테고리 리스트: 적절히 처리됨")
            else:
                print(f"    ⚠️ 빈 카테고리 리스트: 예상과 다른 처리")
            
        except Exception as e:
            print(f"    ⚠️ 빈 카테고리 리스트 처리 중 예외: {e}")
    
    def _measure_performance(self):
        """성능 측정"""
        print("  [7.1] 단일 카테고리 조회 시간 측정")
        
        available_categories = self._get_available_categories()
        
        if not available_categories:
            print("  ⚠️ 사용 가능한 카테고리가 없습니다.")
            return
        
        # 테스트할 카테고리 선택 (10개)
        test_categories = available_categories[:10]
        
        user_profile = {
            'budget_level': 'medium',
            'vibe': 'modern',
            'household_size': 2,
            'housing_type': 'apartment',
            'priority': 'value'
        }
        
        single_times = []
        
        for category in test_categories:
            try:
                start_time = time.time()
                products = self.engine._filter_products_by_category(
                    category=category,
                    user_profile=user_profile
                )
                elapsed = time.time() - start_time
                single_times.append(elapsed)
            except Exception as e:
                self.results['errors'].append(f"성능 측정 실패 ({category}): {str(e)}")
        
        if single_times:
            if HAS_NUMPY:
                avg_time = np.mean(single_times)
                min_time = np.min(single_times)
                max_time = np.max(single_times)
            else:
                avg_time = mean(single_times)
                min_time = min_val(single_times)
                max_time = max_val(single_times)
            
            print(f"    단일 카테고리 조회 시간:")
            print(f"      - 평균: {avg_time:.3f}초")
            print(f"      - 최소: {min_time:.3f}초")
            print(f"      - 최대: {max_time:.3f}초")
            
            # 성능 기준: 평균 < 1초
            if avg_time < 1.0:
                print(f"    ✅ 성능 기준 통과 (평균 < 1초)")
            else:
                print(f"    ⚠️ 성능 기준 미달 (평균 >= 1초)")
        
        print("  [7.2] 여러 카테고리 동시 조회 시간 측정")
        
        if len(available_categories) >= 5:
            test_categories = available_categories[:5]
            
            try:
                start_time = time.time()
                all_products = []
                for category in test_categories:
                    products = self.engine._filter_products_by_category(
                        category=category,
                        user_profile=user_profile
                    )
                    all_products.extend(products)
                elapsed = time.time() - start_time
                
                print(f"    {len(test_categories)}개 카테고리 조회 시간: {elapsed:.3f}초")
                print(f"    총 {len(all_products)}개 제품 조회")
                
                # 성능 기준: 여러 카테고리 < 3초
                if elapsed < 3.0:
                    print(f"    ✅ 성능 기준 통과 (여러 카테고리 < 3초)")
                else:
                    print(f"    ⚠️ 성능 기준 미달 (여러 카테고리 >= 3초)")
                
                self.results['performance_metrics'] = {
                    'single_category': {
                        'avg': avg_time if single_times else 0,
                        'min': min_time if single_times else 0,
                        'max': max_time if single_times else 0,
                    },
                    'multiple_categories': {
                        'time': elapsed,
                        'category_count': len(test_categories),
                        'total_products': len(all_products)
                    }
                }
                
            except Exception as e:
                print(f"    ❌ 예외 발생: {e}")
                self.results['errors'].append(f"여러 카테고리 성능 측정 실패: {str(e)}")
    
    def _print_results(self):
        """검증 결과 출력"""
        print("=" * 80)
        print("검증 결과 요약")
        print("=" * 80)
        
        # 단일 카테고리 검증 결과
        single_tests = self.results['single_category_tests']
        passed_single = sum(1 for t in single_tests if t.get('passed', False))
        print(f"\n[단일 카테고리 제품 조회 검증]")
        print(f"  총 테스트: {len(single_tests)}개")
        print(f"  통과: {passed_single}개")
        print(f"  실패: {len(single_tests) - passed_single}개")
        
        # 여러 카테고리 검증 결과
        multiple_tests = self.results['multiple_categories_tests']
        passed_multiple = sum(1 for t in multiple_tests if t.get('passed', False))
        print(f"\n[여러 카테고리 제품 조회 검증]")
        print(f"  총 테스트: {len(multiple_tests)}개")
        print(f"  통과: {passed_multiple}개")
        print(f"  실패: {len(multiple_tests) - passed_multiple}개")
        
        # 정렬 로직 검증 결과
        sorting_tests = self.results['sorting_tests']
        passed_sorting = sum(1 for t in sorting_tests if t.get('passed', False))
        print(f"\n[제품 정렬 로직 검증]")
        print(f"  총 테스트: {len(sorting_tests)}개")
        print(f"  통과: {passed_sorting}개")
        print(f"  실패: {len(sorting_tests) - passed_sorting}개")
        
        # 제한 로직 검증 결과
        limit_tests = self.results['limit_tests']
        passed_limit = sum(1 for t in limit_tests if t.get('passed', False))
        print(f"\n[제품 제한 로직 검증]")
        print(f"  총 테스트: {len(limit_tests)}개")
        print(f"  통과: {passed_limit}개")
        print(f"  실패: {len(limit_tests) - passed_limit}개")
        
        # 실제 카테고리 검증 결과
        real_tests = self.results['real_category_tests']
        passed_real = sum(1 for t in real_tests if t.get('passed', False))
        print(f"\n[실제 카테고리 데이터 검증]")
        print(f"  총 테스트: {len(real_tests)}개")
        print(f"  통과: {passed_real}개")
        print(f"  실패: {len(real_tests) - passed_real}개")
        
        # 빈 결과 처리 검증 결과
        empty_tests = self.results['empty_result_tests']
        passed_empty = sum(1 for t in empty_tests if t.get('passed', False))
        print(f"\n[빈 결과 처리 검증]")
        print(f"  총 테스트: {len(empty_tests)}개")
        print(f"  통과: {passed_empty}개")
        print(f"  실패: {len(empty_tests) - passed_empty}개")
        
        # 성능 측정 결과
        if self.results['performance_metrics']:
            pm = self.results['performance_metrics']
            print(f"\n[성능 측정]")
            if 'single_category' in pm:
                sc = pm['single_category']
                print(f"  단일 카테고리 조회:")
                print(f"    - 평균: {sc.get('avg', 0):.3f}초")
                print(f"    - 최소: {sc.get('min', 0):.3f}초")
                print(f"    - 최대: {sc.get('max', 0):.3f}초")
            if 'multiple_categories' in pm:
                mc = pm['multiple_categories']
                print(f"  여러 카테고리 조회:")
                print(f"    - 시간: {mc.get('time', 0):.3f}초")
                print(f"    - 카테고리 수: {mc.get('category_count', 0)}개")
                print(f"    - 총 제품 수: {mc.get('total_products', 0)}개")
        
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
        # 모든 테스트가 통과했는지 확인
        all_passed = (
            all(t.get('passed', False) for t in self.results['single_category_tests']) and
            all(t.get('passed', False) for t in self.results['multiple_categories_tests']) and
            all(t.get('passed', False) for t in self.results['sorting_tests']) and
            all(t.get('passed', False) for t in self.results['limit_tests']) and
            all(t.get('passed', False) for t in self.results['real_category_tests']) and
            all(t.get('passed', False) for t in self.results['empty_result_tests']) and
            len(self.results['errors']) == 0
        )
        return all_passed
    
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
            
            # 1. 카테고리별 제품 수 분포 (바 차트)
            ax1 = fig.add_subplot(gs[0, 0])
            single_tests = self.results['single_category_tests']
            if single_tests:
                categories = [t['category'] for t in single_tests]
                counts = [t['product_count'] for t in single_tests]
                ax1.barh(categories, counts, color='steelblue', alpha=0.7)
                ax1.set_xlabel('제품 수')
                ax1.set_title('카테고리별 제품 수 분포', fontsize=14, fontweight='bold')
                ax1.grid(True, alpha=0.3, axis='x')
            
            # 2. 조회 성공/실패 비율 (파이 차트)
            ax2 = fig.add_subplot(gs[0, 1])
            passed_single = sum(1 for t in single_tests if t.get('passed', False))
            failed_single = len(single_tests) - passed_single
            if failed_single > 0:
                ax2.pie([passed_single, failed_single], 
                       labels=[f'통과 ({passed_single})', f'실패 ({failed_single})'],
                       autopct='%1.1f%%',
                       colors=['#4CAF50', '#F44336'],
                       startangle=90)
            else:
                ax2.pie([passed_single], 
                       labels=[f'통과 ({passed_single})'],
                       autopct='%1.1f%%',
                       colors=['#4CAF50'],
                       startangle=90)
            ax2.set_title('조회 성공/실패 비율', fontsize=14, fontweight='bold')
            
            # 3. 조회 시간 분포 (히스토그램)
            ax3 = fig.add_subplot(gs[0, 2])
            if single_tests:
                times = [t['retrieval_time'] for t in single_tests if 'retrieval_time' in t]
                if times:
                    ax3.hist(times, bins=10, color='skyblue', edgecolor='black', alpha=0.7)
                    ax3.set_xlabel('조회 시간 (초)')
                    ax3.set_ylabel('빈도')
                    ax3.set_title('조회 시간 분포', fontsize=14, fontweight='bold')
                    ax3.grid(True, alpha=0.3, axis='y')
            
            # 4. 여러 카테고리 제품 수 비교
            ax4 = fig.add_subplot(gs[1, 0])
            multiple_tests = self.results['multiple_categories_tests']
            if multiple_tests:
                for test in multiple_tests:
                    category_counts = test.get('category_product_counts', {})
                    if category_counts:
                        categories = list(category_counts.keys())
                        counts = list(category_counts.values())
                        ax4.bar(categories, counts, color='plum', alpha=0.7)
                        ax4.set_ylabel('제품 수')
                        ax4.set_title('여러 카테고리 제품 수 비교', fontsize=14, fontweight='bold')
                        ax4.tick_params(axis='x', rotation=45)
                        ax4.grid(True, alpha=0.3, axis='y')
                        break
            
            # 5. 실제 카테고리 검증 결과
            ax5 = fig.add_subplot(gs[1, 1])
            real_tests = self.results['real_category_tests']
            if real_tests:
                taste_ids = [t['taste_id'] for t in real_tests]
                total_products = [t['total_products'] for t in real_tests]
                ax5.bar(taste_ids, total_products, color='lightgreen', alpha=0.7)
                ax5.set_xlabel('Taste ID')
                ax5.set_ylabel('총 제품 수')
                ax5.set_title('실제 카테고리 검증 결과', fontsize=14, fontweight='bold')
                ax5.grid(True, alpha=0.3, axis='y')
            
            # 6. 제품 가격 분포 (카테고리별)
            ax6 = fig.add_subplot(gs[1, 2])
            if single_tests:
                # 첫 번째 카테고리의 제품 가격 분포
                for test in single_tests[:1]:
                    # 가격 데이터는 직접 조회해야 하므로 샘플만 표시
                    if 'product_count' in test and test['product_count'] > 0:
                        ax6.text(0.5, 0.5, f"제품 수: {test['product_count']}개\n(가격 데이터는\n별도 조회 필요)", 
                                ha='center', va='center', fontsize=12,
                                transform=ax6.transAxes)
                        ax6.set_title('제품 가격 분포 (샘플)', fontsize=14, fontweight='bold')
                        break
            
            # 7. 성능 메트릭
            ax7 = fig.add_subplot(gs[2, 0])
            if self.results['performance_metrics']:
                pm = self.results['performance_metrics']
                if 'single_category' in pm:
                    sc = pm['single_category']
                    metrics = ['평균', '최소', '최대']
                    values = [sc.get('avg', 0), sc.get('min', 0), sc.get('max', 0)]
                    ax7.bar(metrics, values, color='steelblue', alpha=0.7)
                    ax7.set_ylabel('시간 (초)')
                    ax7.set_title('단일 카테고리 조회 성능', fontsize=14, fontweight='bold')
                    ax7.grid(True, alpha=0.3, axis='y')
            
            # 8. 검증 항목별 통과율
            ax8 = fig.add_subplot(gs[2, 1])
            validation_items = {}
            
            if single_tests:
                passed_single = sum(1 for t in single_tests if t.get('passed', False))
                validation_items['단일 카테고리'] = passed_single / len(single_tests) * 100 if single_tests else 0
            
            if multiple_tests:
                passed_multiple = sum(1 for t in multiple_tests if t.get('passed', False))
                validation_items['여러 카테고리'] = passed_multiple / len(multiple_tests) * 100 if multiple_tests else 0
            
            if real_tests:
                passed_real = sum(1 for t in real_tests if t.get('passed', False))
                validation_items['실제 카테고리'] = passed_real / len(real_tests) * 100 if real_tests else 0
            
            if validation_items:
                items = list(validation_items.keys())
                rates = list(validation_items.values())
                ax8.barh(items, rates, color='steelblue', alpha=0.7)
                ax8.set_xlabel('통과율 (%)')
                ax8.set_title('검증 항목별 통과율', fontsize=14, fontweight='bold')
                ax8.set_xlim(0, 100)
                ax8.grid(True, alpha=0.3, axis='x')
            
            # 9. 카테고리별 평균 제품 수
            ax9 = fig.add_subplot(gs[2, 2])
            if single_tests:
                categories = [t['category'] for t in single_tests]
                counts = [t['product_count'] for t in single_tests]
                if counts:
                    avg_count = sum(counts) / len(counts)
                    ax9.bar(['평균 제품 수'], [avg_count], color='lightcoral', alpha=0.7)
                    ax9.set_ylabel('제품 수')
                    ax9.set_title('카테고리별 평균 제품 수', fontsize=14, fontweight='bold')
                    ax9.grid(True, alpha=0.3, axis='y')
            
            # 10. 정렬 로직 검증 결과
            ax10 = fig.add_subplot(gs[3, 0])
            sorting_tests = self.results['sorting_tests']
            if sorting_tests:
                passed_sorting = sum(1 for t in sorting_tests if t.get('passed', False))
                failed_sorting = len(sorting_tests) - passed_sorting
                if failed_sorting > 0:
                    ax10.pie([passed_sorting, failed_sorting], 
                           labels=[f'통과 ({passed_sorting})', f'실패 ({failed_sorting})'],
                           autopct='%1.1f%%',
                           colors=['#4CAF50', '#F44336'],
                           startangle=90)
                else:
                    ax10.pie([passed_sorting], 
                           labels=[f'통과 ({passed_sorting})'],
                           autopct='%1.1f%%',
                           colors=['#4CAF50'],
                           startangle=90)
                ax10.set_title('정렬 로직 검증 결과', fontsize=14, fontweight='bold')
            
            # 11. 제한 로직 검증 결과
            ax11 = fig.add_subplot(gs[3, 1])
            limit_tests = self.results['limit_tests']
            if limit_tests:
                passed_limit = sum(1 for t in limit_tests if t.get('passed', False))
                failed_limit = len(limit_tests) - passed_limit
                if failed_limit > 0:
                    ax11.pie([passed_limit, failed_limit], 
                           labels=[f'통과 ({passed_limit})', f'실패 ({failed_limit})'],
                           autopct='%1.1f%%',
                           colors=['#4CAF50', '#F44336'],
                           startangle=90)
                else:
                    ax11.pie([passed_limit], 
                           labels=[f'통과 ({passed_limit})'],
                           autopct='%1.1f%%',
                           colors=['#4CAF50'],
                           startangle=90)
                ax11.set_title('제한 로직 검증 결과', fontsize=14, fontweight='bold')
            
            # 12. 전체 검증 요약
            ax12 = fig.add_subplot(gs[3, 2])
            total_tests = (
                len(single_tests) + len(multiple_tests) + len(sorting_tests) + 
                len(limit_tests) + len(real_tests) + len(self.results['empty_result_tests'])
            )
            total_passed = (
                sum(1 for t in single_tests if t.get('passed', False)) +
                sum(1 for t in multiple_tests if t.get('passed', False)) +
                sum(1 for t in sorting_tests if t.get('passed', False)) +
                sum(1 for t in limit_tests if t.get('passed', False)) +
                sum(1 for t in real_tests if t.get('passed', False)) +
                sum(1 for t in self.results['empty_result_tests'] if t.get('passed', False))
            )
            
            if total_tests > 0:
                pass_rate = total_passed / total_tests * 100
                ax12.bar(['통과율'], [pass_rate], color='steelblue', alpha=0.7)
                ax12.set_ylabel('통과율 (%)')
                ax12.set_title(f'전체 검증 요약\n({total_passed}/{total_tests} 통과)', fontsize=14, fontweight='bold')
                ax12.set_ylim(0, 100)
                ax12.grid(True, alpha=0.3, axis='y')
            
            # 전체 제목
            fig.suptitle(f'카테고리별 제품 조회 로직 검증 결과 (총 {total_tests}개 테스트)', 
                        fontsize=16, fontweight='bold', y=0.995)
            
            # 저장
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_path = f'category_product_retrieval_validation_{timestamp}.png'
            plt.savefig(output_path, dpi=150, bbox_inches='tight')
            print(f"✅ 시각화 저장 완료: {output_path}")
            plt.close()
            
        except Exception as e:
            print(f"⚠️ 시각화 생성 중 오류: {e}")
            import traceback
            traceback.print_exc()


def main():
    """메인 함수"""
    validator = CategoryProductRetrievalValidator()
    success = validator.validate_all()
    
    if success:
        print("=" * 80)
        print("✅ Step 3 검증 완료: 카테고리별 제품 조회 로직이 올바르게 작동합니다!")
        print("=" * 80)
        return 0
    else:
        print("=" * 80)
        print("❌ Step 3 검증 실패: 일부 카테고리별 제품 조회 로직에 문제가 있습니다.")
        print("=" * 80)
        return 1


if __name__ == '__main__':
    exit(main())

