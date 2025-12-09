"""
Step 5: 추천 결과 포맷팅 및 반환 검증
- 추천 결과를 적절한 형식으로 포맷팅하고 반환하는 로직 검증
"""

import os
import sys
import django
import json
import traceback
from datetime import datetime
from typing import Dict, List, Any, Optional
from collections import defaultdict

# Django 설정
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.test import Client
from api.services.taste_based_recommendation_engine import TasteBasedRecommendationEngine
from api.services.taste_calculation_service import TasteCalculationService
from api.db.oracle_client import get_connection


class RecommendationFormattingValidator:
    """추천 결과 포맷팅 및 반환 검증 클래스"""
    
    def __init__(self):
        self.engine = TasteBasedRecommendationEngine()
        self.client = Client()
        self.results = {
            'structure_validation': {},
            'category_grouping': {},
            'top_products_selection': {},
            'sorting_validation': {},
            'api_response': {},
            'real_data_validation': {},
            'errors': [],
            'summary': {}
        }
        
    def validate_all(self):
        """모든 검증 실행"""
        print("=" * 80)
        print("Step 5: 추천 결과 포맷팅 및 반환 검증 시작")
        print("=" * 80)
        
        try:
            # 1. 추천 결과 데이터 구조 검증
            print("\n[1/6] 추천 결과 데이터 구조 검증...")
            self._validate_result_structure()
            
            # 2. 카테고리별 제품 그룹화 검증
            print("\n[2/6] 카테고리별 제품 그룹화 검증...")
            self._validate_category_grouping()
            
            # 3. 상위 제품 선택 검증
            print("\n[3/6] 상위 제품 선택 검증...")
            self._validate_top_products_selection()
            
            # 4. 추천 결과 정렬 검증
            print("\n[4/6] 추천 결과 정렬 검증...")
            self._validate_sorting()
            
            # 5. API 응답 형식 검증
            print("\n[5/6] API 응답 형식 검증...")
            self._validate_api_response()
            
            # 6. 실제 데이터로 검증
            print("\n[6/6] 실제 데이터로 검증...")
            self._validate_with_real_data()
            
            # 결과 요약
            self._generate_summary()
            
        except Exception as e:
            error_msg = f"검증 중 오류 발생: {str(e)}\n{traceback.format_exc()}"
            print(f"\n❌ {error_msg}")
            self.results['errors'].append(error_msg)
        
        return self.results
    
    def _validate_result_structure(self):
        """추천 결과 데이터 구조 검증"""
        try:
            # 실제 회원 데이터로 테스트
            members = self._get_members_with_taste(limit=10)
            
            if not members:
                self.results['structure_validation']['status'] = 'skipped'
                self.results['structure_validation']['message'] = '테스트할 회원 데이터가 없습니다.'
                print("  ⚠️  테스트할 회원 데이터가 없습니다.")
                return
            
            validation_results = {
                'total_tested': 0,
                'passed': 0,
                'failed': 0,
                'issues': []
            }
            
            for member in members:
                member_id = member.get('member_id')
                if not member_id:
                    continue
                
                try:
                    # 온보딩 데이터 조회 및 user_profile 구성
                    user_profile = self._get_user_profile_from_member(member_id)
                    taste_id = member.get('taste_id')
                    
                    if not user_profile or not taste_id:
                        validation_results['failed'] += 1
                        validation_results['issues'].append({
                            'member_id': member_id,
                            'issue': 'user_profile 또는 taste_id를 가져올 수 없습니다.'
                        })
                        continue
                    
                    recommendations = self.engine.get_recommendations(
                        user_profile=user_profile,
                        taste_id=taste_id
                    )
                    validation_results['total_tested'] += 1
                    
                    # 기본 구조 확인
                    if not isinstance(recommendations, dict):
                        validation_results['failed'] += 1
                        validation_results['issues'].append({
                            'member_id': member_id,
                            'issue': '추천 결과가 dict 형식이 아닙니다.',
                            'type': recommendations.__class__.__name__
                        })
                        continue
                    
                    # 필수 필드 확인
                    has_categories = 'categories' in recommendations
                    has_products = 'products' in recommendations
                    
                    if not (has_categories or has_products):
                        validation_results['failed'] += 1
                        validation_results['issues'].append({
                            'member_id': member_id,
                            'issue': 'categories 또는 products 필드가 없습니다.',
                            'keys': list(recommendations.keys())
                        })
                        continue
                    
                    # 카테고리 구조 확인
                    if has_categories:
                        categories = recommendations.get('categories', [])
                        if not isinstance(categories, list):
                            validation_results['failed'] += 1
                            validation_results['issues'].append({
                                'member_id': member_id,
                                'issue': 'categories가 list 형식이 아닙니다.',
                                'type': categories.__class__.__name__
                            })
                            continue
                        
                        # 각 카테고리 구조 확인
                        for idx, category in enumerate(categories):
                            if not isinstance(category, dict):
                                validation_results['failed'] += 1
                                validation_results['issues'].append({
                                    'member_id': member_id,
                                    'category_index': idx,
                                    'issue': '카테고리가 dict 형식이 아닙니다.'
                                })
                                continue
                            
                            # 카테고리 필수 필드
                            if 'category_id' not in category:
                                validation_results['failed'] += 1
                                validation_results['issues'].append({
                                    'member_id': member_id,
                                    'category_index': idx,
                                    'issue': 'category_id 필드가 없습니다.'
                                })
                            
                            if 'products' not in category:
                                validation_results['failed'] += 1
                                validation_results['issues'].append({
                                    'member_id': member_id,
                                    'category_index': idx,
                                    'issue': 'products 필드가 없습니다.'
                                })
                            elif not isinstance(category.get('products'), list):
                                validation_results['failed'] += 1
                                validation_results['issues'].append({
                                    'member_id': member_id,
                                    'category_index': idx,
                                    'issue': 'products가 list 형식이 아닙니다.'
                                })
                            
                            # 제품 정보 완전성 확인
                            for p_idx, product in enumerate(category.get('products', [])):
                                required_fields = ['product_id', 'name', 'price']
                                for field in required_fields:
                                    if field not in product:
                                        validation_results['failed'] += 1
                                        validation_results['issues'].append({
                                            'member_id': member_id,
                                            'category_index': idx,
                                            'product_index': p_idx,
                                            'issue': f'제품에 {field} 필드가 없습니다.'
                                        })
                    
                    # 모든 검증 통과
                    if not validation_results['issues']:
                        validation_results['passed'] += 1
                    
                except Exception as e:
                    validation_results['failed'] += 1
                    validation_results['issues'].append({
                        'member_id': member_id,
                        'issue': f'추천 결과 조회 중 오류: {str(e)}'
                    })
            
            self.results['structure_validation'] = validation_results
            
            # 결과 출력
            print(f"  ✓ 테스트한 회원 수: {validation_results['total_tested']}")
            print(f"  ✓ 통과: {validation_results['passed']}")
            print(f"  ✗ 실패: {validation_results['failed']}")
            if validation_results['issues']:
                print(f"  ⚠️  발견된 이슈 수: {len(validation_results['issues'])}")
                for issue in validation_results['issues'][:5]:  # 처음 5개만 출력
                    print(f"     - {issue.get('member_id', 'N/A')}: {issue.get('issue', 'N/A')}")
            
        except Exception as e:
            error_msg = f"구조 검증 중 오류: {str(e)}"
            print(f"  ❌ {error_msg}")
            self.results['structure_validation']['error'] = error_msg
            self.results['errors'].append(error_msg)
    
    def _validate_category_grouping(self):
        """카테고리별 제품 그룹화 검증"""
        try:
            members = self._get_members_with_taste(limit=20)
            
            if not members:
                self.results['category_grouping']['status'] = 'skipped'
                print("  ⚠️  테스트할 회원 데이터가 없습니다.")
                return
            
            validation_results = {
                'total_tested': 0,
                'category_counts': defaultdict(int),
                'product_counts_per_category': defaultdict(list),
                'issues': []
            }
            
            for member in members:
                member_id = member.get('member_id')
                if not member_id:
                    continue
                
                try:
                    user_profile = self._get_user_profile_from_member(member_id)
                    taste_id = member.get('taste_id')
                    
                    if not user_profile or not taste_id:
                        continue
                    
                    recommendations = self.engine.get_recommendations(
                        user_profile=user_profile,
                        taste_id=taste_id
                    )
                    validation_results['total_tested'] += 1
                    
                    if 'categories' not in recommendations:
                        validation_results['issues'].append({
                            'member_id': member_id,
                            'issue': 'categories 필드가 없습니다.'
                        })
                        continue
                    
                    categories = recommendations.get('categories', [])
                    validation_results['category_counts'][len(categories)] += 1
                    
                    # 각 카테고리별 제품 수 확인
                    for category in categories:
                        category_id = category.get('category_id')
                        products = category.get('products', [])
                        product_count = len(products)
                        
                        validation_results['product_counts_per_category'][category_id].append(product_count)
                        
                        # 카테고리별 최대 제품 수 확인 (예: 상위 10개)
                        if product_count > 10:
                            validation_results['issues'].append({
                                'member_id': member_id,
                                'category_id': category_id,
                                'issue': f'카테고리별 제품 수가 10개를 초과합니다: {product_count}개'
                            })
                    
                except Exception as e:
                    validation_results['issues'].append({
                        'member_id': member_id,
                        'issue': f'검증 중 오류: {str(e)}'
                    })
            
            self.results['category_grouping'] = validation_results
            
            # 결과 출력
            print(f"  ✓ 테스트한 회원 수: {validation_results['total_tested']}")
            print(f"  ✓ 카테고리 수 분포:")
            for count, freq in sorted(validation_results['category_counts'].items()):
                print(f"     - {count}개 카테고리: {freq}명")
            
            print(f"  ✓ 카테고리별 평균 제품 수:")
            for cat_id, counts in list(validation_results['product_counts_per_category'].items())[:10]:
                avg = sum(counts) / len(counts) if counts else 0
                print(f"     - 카테고리 {cat_id}: 평균 {avg:.1f}개 (최소 {min(counts)}, 최대 {max(counts)})")
            
            if validation_results['issues']:
                print(f"  ⚠️  발견된 이슈 수: {len(validation_results['issues'])}")
            
        except Exception as e:
            error_msg = f"카테고리 그룹화 검증 중 오류: {str(e)}"
            print(f"  ❌ {error_msg}")
            self.results['category_grouping']['error'] = error_msg
            self.results['errors'].append(error_msg)
    
    def _validate_top_products_selection(self):
        """상위 제품 선택 검증"""
        try:
            members = self._get_members_with_taste(limit=15)
            
            if not members:
                self.results['top_products_selection']['status'] = 'skipped'
                print("  ⚠️  테스트할 회원 데이터가 없습니다.")
                return
            
            validation_results = {
                'total_tested': 0,
                'sorted_correctly': 0,
                'sorted_incorrectly': 0,
                'issues': []
            }
            
            for member in members:
                member_id = member.get('member_id')
                if not member_id:
                    continue
                
                try:
                    user_profile = self._get_user_profile_from_member(member_id)
                    taste_id = member.get('taste_id')
                    
                    if not user_profile or not taste_id:
                        continue
                    
                    recommendations = self.engine.get_recommendations(
                        user_profile=user_profile,
                        taste_id=taste_id
                    )
                    validation_results['total_tested'] += 1
                    
                    if 'categories' not in recommendations:
                        continue
                    
                    all_sorted = True
                    for category in recommendations.get('categories', []):
                        products = category.get('products', [])
                        
                        if len(products) <= 1:
                            continue
                        
                        # 추천 점수로 정렬 확인
                        scores = []
                        for product in products:
                            score = product.get('recommendation_score') or product.get('score') or 0
                            scores.append(score)
                        
                        # 내림차순 정렬 확인
                        if scores != sorted(scores, reverse=True):
                            all_sorted = False
                            validation_results['issues'].append({
                                'member_id': member_id,
                                'category_id': category.get('category_id'),
                                'issue': '제품이 추천 점수 내림차순으로 정렬되지 않았습니다.'
                            })
                    
                    if all_sorted:
                        validation_results['sorted_correctly'] += 1
                    else:
                        validation_results['sorted_incorrectly'] += 1
                    
                except Exception as e:
                    validation_results['issues'].append({
                        'member_id': member_id,
                        'issue': f'검증 중 오류: {str(e)}'
                    })
            
            self.results['top_products_selection'] = validation_results
            
            # 결과 출력
            print(f"  ✓ 테스트한 회원 수: {validation_results['total_tested']}")
            print(f"  ✓ 정렬 정확: {validation_results['sorted_correctly']}")
            print(f"  ✗ 정렬 오류: {validation_results['sorted_incorrectly']}")
            if validation_results['issues']:
                print(f"  ⚠️  발견된 이슈 수: {len(validation_results['issues'])}")
            
        except Exception as e:
            error_msg = f"상위 제품 선택 검증 중 오류: {str(e)}"
            print(f"  ❌ {error_msg}")
            self.results['top_products_selection']['error'] = error_msg
            self.results['errors'].append(error_msg)
    
    def _validate_sorting(self):
        """추천 결과 정렬 검증"""
        try:
            members = self._get_members_with_taste(limit=10)
            
            if not members:
                self.results['sorting_validation']['status'] = 'skipped'
                print("  ⚠️  테스트할 회원 데이터가 없습니다.")
                return
            
            validation_results = {
                'total_tested': 0,
                'category_order_valid': 0,
                'product_order_valid': 0,
                'issues': []
            }
            
            for member in members:
                member_id = member.get('member_id')
                if not member_id:
                    continue
                
                try:
                    user_profile = self._get_user_profile_from_member(member_id)
                    taste_id = member.get('taste_id')
                    
                    if not user_profile or not taste_id:
                        continue
                    
                    recommendations = self.engine.get_recommendations(
                        user_profile=user_profile,
                        taste_id=taste_id
                    )
                    validation_results['total_tested'] += 1
                    
                    if 'categories' not in recommendations:
                        continue
                    
                    categories = recommendations.get('categories', [])
                    
                    # 카테고리별 정렬 확인 (예: 우선순위 순서)
                    category_valid = True
                    for i in range(len(categories) - 1):
                        curr_cat = categories[i]
                        next_cat = categories[i + 1]
                        
                        # 카테고리 우선순위나 제품 수로 정렬 확인
                        curr_priority = curr_cat.get('priority', 0) or len(curr_cat.get('products', []))
                        next_priority = next_cat.get('priority', 0) or len(next_cat.get('products', []))
                        
                        # 우선순위가 높은 카테고리가 먼저 와야 함
                        if curr_priority < next_priority:
                            category_valid = False
                            break
                    
                    if category_valid:
                        validation_results['category_order_valid'] += 1
                    
                    # 카테고리 내 제품 정렬 확인
                    product_valid = True
                    for category in categories:
                        products = category.get('products', [])
                        if len(products) <= 1:
                            continue
                        
                        scores = [p.get('recommendation_score') or p.get('score') or 0 for p in products]
                        if scores != sorted(scores, reverse=True):
                            product_valid = False
                            break
                    
                    if product_valid:
                        validation_results['product_order_valid'] += 1
                    
                except Exception as e:
                    validation_results['issues'].append({
                        'member_id': member_id,
                        'issue': f'검증 중 오류: {str(e)}'
                    })
            
            self.results['sorting_validation'] = validation_results
            
            # 결과 출력
            print(f"  ✓ 테스트한 회원 수: {validation_results['total_tested']}")
            print(f"  ✓ 카테고리 정렬 정확: {validation_results['category_order_valid']}")
            print(f"  ✓ 제품 정렬 정확: {validation_results['product_order_valid']}")
            
        except Exception as e:
            error_msg = f"정렬 검증 중 오류: {str(e)}"
            print(f"  ❌ {error_msg}")
            self.results['sorting_validation']['error'] = error_msg
            self.results['errors'].append(error_msg)
    
    def _validate_api_response(self):
        """API 응답 형식 검증"""
        try:
            members = self._get_members_with_taste(limit=5)
            
            if not members:
                self.results['api_response']['status'] = 'skipped'
                print("  ⚠️  테스트할 회원 데이터가 없습니다.")
                return
            
            validation_results = {
                'total_tested': 0,
                'successful': 0,
                'failed': 0,
                'status_codes': defaultdict(int),
                'issues': []
            }
            
            # API 엔드포인트 확인
            endpoint_patterns = [
                '/api/recommendations/',
                '/api/taste/recommendations/',
                '/api/member/recommendations/'
            ]
            
            for member in members:
                member_id = member.get('member_id')
                if not member_id:
                    continue
                
                # 각 엔드포인트 패턴 시도
                tested = False
                for endpoint_pattern in endpoint_patterns:
                    try:
                        endpoint = f"{endpoint_pattern}{member_id}"
                        response = self.client.get(endpoint)
                        validation_results['total_tested'] += 1
                        tested = True
                        
                        validation_results['status_codes'][response.status_code] += 1
                        
                        if response.status_code == 200:
                            try:
                                data = response.json()
                                if isinstance(data, dict):
                                    # JSON 형식 확인
                                    if 'categories' in data or 'products' in data:
                                        validation_results['successful'] += 1
                                    else:
                                        validation_results['failed'] += 1
                                        validation_results['issues'].append({
                                            'member_id': member_id,
                                            'endpoint': endpoint,
                                            'issue': '응답에 categories 또는 products 필드가 없습니다.',
                                            'keys': list(data.keys())
                                        })
                                else:
                                    validation_results['failed'] += 1
                                    validation_results['issues'].append({
                                        'member_id': member_id,
                                        'endpoint': endpoint,
                                        'issue': '응답이 dict 형식이 아닙니다.'
                                    })
                            except json.JSONDecodeError:
                                validation_results['failed'] += 1
                                validation_results['issues'].append({
                                    'member_id': member_id,
                                    'endpoint': endpoint,
                                    'issue': '응답이 유효한 JSON 형식이 아닙니다.'
                                })
                        else:
                            validation_results['failed'] += 1
                            validation_results['issues'].append({
                                'member_id': member_id,
                                'endpoint': endpoint,
                                'status_code': response.status_code,
                                'issue': f'HTTP 상태 코드가 200이 아닙니다: {response.status_code}'
                            })
                        
                        break  # 성공한 엔드포인트 찾으면 중단
                        
                    except Exception as e:
                        continue
                
                if not tested:
                    validation_results['issues'].append({
                        'member_id': member_id,
                        'issue': '유효한 API 엔드포인트를 찾을 수 없습니다.'
                    })
            
            self.results['api_response'] = validation_results
            
            # 결과 출력
            print(f"  ✓ 테스트한 회원 수: {validation_results['total_tested']}")
            print(f"  ✓ 성공: {validation_results['successful']}")
            print(f"  ✗ 실패: {validation_results['failed']}")
            print(f"  ✓ HTTP 상태 코드 분포:")
            for code, count in sorted(validation_results['status_codes'].items()):
                print(f"     - {code}: {count}회")
            
        except Exception as e:
            error_msg = f"API 응답 검증 중 오류: {str(e)}"
            print(f"  ❌ {error_msg}")
            self.results['api_response']['error'] = error_msg
            self.results['errors'].append(error_msg)
    
    def _validate_with_real_data(self):
        """실제 데이터로 검증"""
        try:
            members = self._get_members_with_taste(limit=50)
            
            if not members:
                self.results['real_data_validation']['status'] = 'skipped'
                print("  ⚠️  테스트할 회원 데이터가 없습니다.")
                return
            
            validation_results = {
                'total_tested': 0,
                'successful': 0,
                'failed': 0,
                'total_products_recommended': 0,
                'categories_with_products': 0,
                'issues': [],
                'sample_results': []
            }
            
            for member in members:
                member_id = member.get('member_id')
                if not member_id:
                    continue
                
                try:
                    user_profile = self._get_user_profile_from_member(member_id)
                    taste_id = member.get('taste_id')
                    
                    if not user_profile or not taste_id:
                        validation_results['failed'] += 1
                        continue
                    
                    recommendations = self.engine.get_recommendations(
                        user_profile=user_profile,
                        taste_id=taste_id
                    )
                    validation_results['total_tested'] += 1
                    
                    # 기본 구조 확인
                    if not isinstance(recommendations, dict):
                        validation_results['failed'] += 1
                        continue
                    
                    has_categories = 'categories' in recommendations
                    has_products = 'products' in recommendations
                    
                    if not (has_categories or has_products):
                        validation_results['failed'] += 1
                        continue
                    
                    # 제품 수 계산
                    if has_categories:
                        categories = recommendations.get('categories', [])
                        total_products = 0
                        categories_with_products_count = 0
                        
                        for category in categories:
                            products = category.get('products', [])
                            product_count = len(products)
                            total_products += product_count
                            
                            if product_count > 0:
                                categories_with_products_count += 1
                        
                        validation_results['total_products_recommended'] += total_products
                        validation_results['categories_with_products'] += categories_with_products_count
                        
                        # 샘플 결과 저장 (처음 3개만)
                        if len(validation_results['sample_results']) < 3:
                            validation_results['sample_results'].append({
                                'member_id': member_id,
                                'categories_count': len(categories),
                                'total_products': total_products,
                                'categories': [
                                    {
                                        'category_id': cat.get('category_id'),
                                        'category_name': cat.get('category_name', 'N/A'),
                                        'products_count': len(cat.get('products', []))
                                    }
                                    for cat in categories[:5]  # 처음 5개 카테고리만
                                ]
                            })
                    
                    validation_results['successful'] += 1
                    
                except Exception as e:
                    validation_results['failed'] += 1
                    validation_results['issues'].append({
                        'member_id': member_id,
                        'issue': f'검증 중 오류: {str(e)}'
                    })
            
            # 평균 계산
            if validation_results['successful'] > 0:
                validation_results['avg_products_per_member'] = (
                    validation_results['total_products_recommended'] / validation_results['successful']
                )
                validation_results['avg_categories_with_products'] = (
                    validation_results['categories_with_products'] / validation_results['successful']
                )
            
            self.results['real_data_validation'] = validation_results
            
            # 결과 출력
            print(f"  ✓ 테스트한 회원 수: {validation_results['total_tested']}")
            print(f"  ✓ 성공: {validation_results['successful']}")
            print(f"  ✗ 실패: {validation_results['failed']}")
            if validation_results.get('avg_products_per_member'):
                print(f"  ✓ 회원당 평균 추천 제품 수: {validation_results['avg_products_per_member']:.1f}개")
            if validation_results.get('avg_categories_with_products'):
                print(f"  ✓ 회원당 평균 카테고리 수: {validation_results['avg_categories_with_products']:.1f}개")
            
            # 샘플 결과 출력
            if validation_results['sample_results']:
                print(f"\n  📋 샘플 결과 (처음 {len(validation_results['sample_results'])}개):")
                for idx, sample in enumerate(validation_results['sample_results'], 1):
                    print(f"     [{idx}] 회원 ID: {sample['member_id']}")
                    print(f"         - 카테고리 수: {sample['categories_count']}")
                    print(f"         - 총 제품 수: {sample['total_products']}")
                    for cat in sample['categories'][:3]:
                        print(f"           • {cat['category_name']} (ID: {cat['category_id']}): {cat['products_count']}개")
            
        except Exception as e:
            error_msg = f"실제 데이터 검증 중 오류: {str(e)}"
            print(f"  ❌ {error_msg}")
            self.results['real_data_validation']['error'] = error_msg
            self.results['errors'].append(error_msg)
    
    def _get_members_with_taste(self, limit: int = 50) -> List[Dict]:
        """Taste가 있는 회원 조회"""
        try:
            with get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("""
                        SELECT DISTINCT MEMBER_ID, TASTE
                        FROM MEMBER
                        WHERE TASTE IS NOT NULL
                        AND ROWNUM <= :limit
                    """, {'limit': limit})
                    
                    rows = cursor.fetchall()
                    return [
                        {'member_id': row[0], 'taste_id': int(row[1]) if row[1] else None}
                        for row in rows if row[1] is not None
                    ]
        except Exception as e:
            print(f"  ⚠️  회원 데이터 조회 중 오류: {str(e)}")
            return []
    
    def _get_user_profile_from_member(self, member_id: str) -> Optional[Dict]:
        """회원 ID로부터 user_profile 구성"""
        try:
            # 온보딩 세션 조회
            with get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("""
                        SELECT * FROM (
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
                            WHERE MEMBER_ID = :member_id
                            AND STATUS = 'COMPLETED'
                            ORDER BY CREATED_AT DESC
                        ) WHERE ROWNUM <= 1
                    """, {'member_id': member_id})
                    
                    cols = [c[0] for c in cursor.description]
                    row = cursor.fetchone()
                    
                    if not row:
                        # 기본값으로 user_profile 구성
                        return {
                            'vibe': 'modern',
                            'household_size': 2,
                            'housing_type': 'apartment',
                            'pyung': 25,
                            'priority': 'value',
                            'budget_level': 'medium',
                            'has_pet': False,
                            'cooking': 'sometimes',
                            'laundry': 'weekly',
                            'media': 'balanced',
                            'onboarding_data': {}
                        }
                    
                    session = dict(zip(cols, row))
                    
                    # user_profile 구성
                    user_profile = {
                        'vibe': session.get('VIBE', 'modern'),
                        'household_size': int(session.get('HOUSEHOLD_SIZE', 2)) if session.get('HOUSEHOLD_SIZE') else 2,
                        'housing_type': session.get('HOUSING_TYPE', 'apartment'),
                        'pyung': int(session.get('PYUNG', 25)) if session.get('PYUNG') else 25,
                        'priority': session.get('PRIORITY', 'value'),
                        'budget_level': session.get('BUDGET_LEVEL', 'medium'),
                        'has_pet': session.get('HAS_PET') == 'Y' if session.get('HAS_PET') else False,
                        'cooking': session.get('COOKING', 'sometimes'),
                        'laundry': session.get('LAUNDRY', 'weekly'),
                        'media': session.get('MEDIA', 'balanced'),
                        'onboarding_data': {
                            'vibe': session.get('VIBE'),
                            'household_size': session.get('HOUSEHOLD_SIZE'),
                            'housing_type': session.get('HOUSING_TYPE'),
                            'pyung': session.get('PYUNG'),
                            'budget_level': session.get('BUDGET_LEVEL'),
                            'priority': session.get('PRIORITY'),
                            'has_pet': session.get('HAS_PET') == 'Y' if session.get('HAS_PET') else False,
                            'cooking': session.get('COOKING'),
                            'laundry': session.get('LAUNDRY'),
                            'media': session.get('MEDIA'),
                        }
                    }
                    
                    return user_profile
        except Exception as e:
            print(f"  ⚠️  user_profile 구성 중 오류 ({member_id}): {str(e)}")
            return None
    
    def _generate_summary(self):
        """검증 결과 요약 생성"""
        summary = {
            'timestamp': datetime.now().isoformat(),
            'total_validations': 6,
            'completed': 0,
            'skipped': 0,
            'errors': len(self.results['errors']),
            'overall_status': 'unknown'
        }
        
        # 각 검증 항목 상태 확인
        validations = [
            'structure_validation',
            'category_grouping',
            'top_products_selection',
            'sorting_validation',
            'api_response',
            'real_data_validation'
        ]
        
        for validation in validations:
            if validation in self.results:
                if 'status' in self.results[validation] and self.results[validation]['status'] == 'skipped':
                    summary['skipped'] += 1
                elif 'error' in self.results[validation]:
                    summary['errors'] += 1
                else:
                    summary['completed'] += 1
        
        # 전체 상태 결정
        if summary['errors'] == 0 and summary['completed'] > 0:
            summary['overall_status'] = 'success'
        elif summary['errors'] > 0:
            summary['overall_status'] = 'partial'
        else:
            summary['overall_status'] = 'failed'
        
        self.results['summary'] = summary
        
        # 요약 출력
        print("\n" + "=" * 80)
        print("검증 결과 요약")
        print("=" * 80)
        print(f"  완료된 검증: {summary['completed']}/{summary['total_validations']}")
        print(f"  건너뛴 검증: {summary['skipped']}")
        print(f"  오류 발생: {summary['errors']}")
        print(f"  전체 상태: {summary['overall_status']}")
        print("=" * 80)
    
    def save_results(self, filename: Optional[str] = None):
        """검증 결과를 JSON 파일로 저장"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"recommendation_formatting_validation_{timestamp}.json"
        
        filepath = os.path.join(os.path.dirname(__file__), filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, ensure_ascii=False, indent=2, default=str)
        
        print(f"\n검증 결과가 저장되었습니다: {filepath}")
        return filepath


def main():
    """메인 실행 함수"""
    validator = RecommendationFormattingValidator()
    results = validator.validate_all()
    validator.save_results()
    
    # 종료 코드 결정
    if results['summary'].get('overall_status') == 'success':
        sys.exit(0)
    elif results['summary'].get('overall_status') == 'partial':
        sys.exit(1)
    else:
        sys.exit(2)


if __name__ == '__main__':
    main()

