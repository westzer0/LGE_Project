#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
백엔드 로직 정확도 검증 스크립트

검증 항목:
1. Oracle DB 연결 확인
2. 데이터 존재 여부 확인
3. 추천 엔진 로직 검증 (recommendation_engine 하나만 사용)
4. taste_id에 따른 scoring 로직 차이 확인
5. 실제 API 엔드포인트 동작 확인
"""

import os
import sys
import json
import traceback
import random
from datetime import datetime
from pathlib import Path

# Django 설정 로드
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

import django
django.setup()

from api.db.oracle_client import get_connection, fetch_all_dict, fetch_one
from api.services.recommendation_engine import recommendation_engine
from api.models import Product, ProductSpec


class BackendLogicVerifier:
    """백엔드 로직 검증 클래스"""
    
    def __init__(self):
        self.results = {
            'connection': {},
            'data_checks': {},
            'recommendation_tests': {},
            'api_tests': {},
            'summary': {}
        }
        self.errors = []
        self.warnings = []
    
    def run_all_checks(self):
        """모든 검증 실행"""
        print("=" * 80)
        print("백엔드 로직 정확도 검증 시작")
        print("=" * 80)
        print()
        
        # 1. Oracle DB 연결 확인
        print("[1/4] Oracle DB 연결 확인 중...")
        self.check_oracle_connection()
        print()
        
        # 2. 데이터 존재 여부 확인
        print("[2/4] 데이터 존재 여부 확인 중...")
        self.check_data_existence()
        print()
        
        # 3. 추천 엔진 로직 검증
        print("[3/4] 추천 엔진 로직 검증 중...")
        self.test_recommendation_engine()
        print()
        
        # 4. 실제 API 동작 확인
        print("[4/4] 실제 API 동작 확인 중...")
        self.test_api_endpoints()
        print()
        
        # 최종 리포트 생성
        self.generate_report()
    
    def check_oracle_connection(self):
        """Oracle DB 연결 확인"""
        try:
            with get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT 1 FROM DUAL")
                    result = cur.fetchone()
                    
            self.results['connection'] = {
                'status': 'success',
                'message': 'Oracle DB 연결 성공'
            }
            print("  ✓ Oracle DB 연결 성공")
            
        except Exception as e:
            self.results['connection'] = {
                'status': 'failed',
                'message': f'Oracle DB 연결 실패: {str(e)}'
            }
            self.errors.append(f"Oracle DB 연결 실패: {str(e)}")
            print(f"  ✗ Oracle DB 연결 실패: {str(e)}")
            return False
        
        return True
    
    def check_data_existence(self):
        """데이터 존재 여부 확인"""
        checks = {}
        
        try:
            # PRODUCT 테이블 확인
            product_count = fetch_one("SELECT COUNT(*) FROM PRODUCT")
            checks['product_count'] = product_count[0] if product_count else 0
            print(f"  ✓ PRODUCT 테이블: {checks['product_count']}개 제품")
            
            # PRODUCT_SPEC 테이블 확인
            spec_count = fetch_one("SELECT COUNT(*) FROM PRODUCT_SPEC")
            checks['spec_count'] = spec_count[0] if spec_count else 0
            print(f"  ✓ PRODUCT_SPEC 테이블: {checks['spec_count']}개 스펙")
            
            # MAIN_CATEGORY 확인
            categories = fetch_all_dict("""
                SELECT DISTINCT MAIN_CATEGORY, COUNT(*) as CNT
                FROM PRODUCT
                GROUP BY MAIN_CATEGORY
                ORDER BY CNT DESC
            """)
            checks['categories'] = categories
            print(f"  ✓ MAIN_CATEGORY: {len(categories)}개 카테고리")
            for cat in categories[:5]:
                print(f"    - {cat['MAIN_CATEGORY']}: {cat['CNT']}개")
            
            # Django 모델과의 동기화 확인
            django_product_count = Product.objects.count()
            checks['django_product_count'] = django_product_count
            print(f"  ✓ Django Product 모델: {django_product_count}개")
            
            if checks['product_count'] > 0 and checks['spec_count'] > 0:
                self.results['data_checks'] = {
                    'status': 'success',
                    'checks': checks
                }
            else:
                self.results['data_checks'] = {
                    'status': 'warning',
                    'checks': checks,
                    'message': '데이터가 부족할 수 있습니다.'
                }
                self.warnings.append("데이터가 부족할 수 있습니다.")
                
        except Exception as e:
            self.results['data_checks'] = {
                'status': 'failed',
                'error': str(e)
            }
            self.errors.append(f"데이터 확인 실패: {str(e)}")
            print(f"  ✗ 데이터 확인 실패: {str(e)}")
    
    def test_recommendation_engine(self):
        """추천 엔진 로직 검증 - recommendation_engine 하나만 사용, taste_id에 따라 scoring 로직 다름"""
        # Oracle DB에서 실제 MAIN_CATEGORY 목록 가져오기
        try:
            categories_data = fetch_all_dict("""
                SELECT DISTINCT MAIN_CATEGORY
                FROM PRODUCT
                WHERE MAIN_CATEGORY IS NOT NULL
                ORDER BY MAIN_CATEGORY
            """)
            actual_categories = [cat['MAIN_CATEGORY'] for cat in categories_data]
            print(f"  ✓ 실제 카테고리 {len(actual_categories)}개 로드: {', '.join(actual_categories[:10])}...")
        except Exception as e:
            print(f"  ⚠ 카테고리 로드 실패, 기본값 사용: {str(e)}")
            actual_categories = ['TV', '냉장고', '에어컨', '세탁', '청소기']
        
        # 상위 카테고리 선택
        top_categories = actual_categories[:5] if len(actual_categories) >= 5 else actual_categories
        
        # 고정 테스트 케이스 (4개)
        test_cases = [
            {
                'name': '1인 가구 저예산 (taste_id 있음)',
                'user_profile': {
                    'vibe': 'modern',
                    'household_size': 1,
                    'housing_type': 'apartment',
                    'pyung': 20,
                    'priority': 'value',
                    'budget_level': 'low',
                    'budget_amount': 500000,
                    'categories': top_categories[:2] if len(top_categories) >= 2 else top_categories,
                    'has_pet': False,
                    'onboarding_data': {
                        'cooking': 'rarely',
                        'laundry': 'few_times',
                        'media': 'balanced'
                    }
                },
                'taste_id': 1
            },
            {
                'name': '4인 가족 중예산 (taste_id 있음)',
                'user_profile': {
                    'vibe': 'modern',
                    'household_size': 4,
                    'housing_type': 'apartment',
                    'pyung': 30,
                    'priority': 'tech',
                    'budget_level': 'medium',
                    'budget_amount': 2000000,
                    'categories': top_categories[:3] if len(top_categories) >= 3 else top_categories,
                    'has_pet': False,
                    'onboarding_data': {
                        'cooking': 'high',
                        'laundry': 'daily',
                        'media': 'heavy'
                    }
                },
                'taste_id': 2
            },
            {
                'name': '2인 가구 중예산 (taste_id 없음)',
                'user_profile': {
                    'vibe': 'cozy',
                    'household_size': 2,
                    'housing_type': 'apartment',
                    'pyung': 25,
                    'priority': 'design',
                    'budget_level': 'medium',
                    'budget_amount': 1500000,
                    'categories': top_categories[:2] if len(top_categories) >= 2 else top_categories,
                    'has_pet': True,
                    'onboarding_data': {
                        'cooking': 'often',
                        'laundry': 'weekly',
                        'media': 'balanced'
                    }
                },
                'taste_id': None
            },
            {
                'name': '3인 가족 고예산 (taste_id 있음)',
                'user_profile': {
                    'vibe': 'luxury',
                    'household_size': 3,
                    'housing_type': 'detached',
                    'pyung': 35,
                    'priority': 'tech',
                    'budget_level': 'high',
                    'budget_amount': 5000000,
                    'categories': top_categories[:3] if len(top_categories) >= 3 else top_categories,
                    'has_pet': False,
                    'onboarding_data': {
                        'cooking': 'high',
                        'laundry': 'daily',
                        'media': 'gaming'
                    }
                },
                'taste_id': 4
            }
        ]
        
        # 100개 테스트 케이스 생성 (고정 4개 + 랜덤 96개)
        print(f"  테스트 케이스 생성 중... (총 100개)")
        
        # 랜덤 시나리오 생성 (96개)
        random_test_cases = []
        household_sizes = [1, 2, 3, 4, 5]
        budget_levels = ['low', 'medium', 'high']
        budget_amounts = {'low': 500000, 'medium': 2000000, 'high': 5000000}
        vibes = ['modern', 'cozy', 'pop', 'luxury']
        priorities = ['value', 'tech', 'design', 'eco']
        housing_types = ['apartment', 'detached', 'villa', 'officetel', 'studio']
        cooking_options = ['rarely', 'often', 'high']
        laundry_options = ['few_times', 'weekly', 'daily']
        media_options = ['balanced', 'heavy', 'gaming']
        
        # 시드 고정으로 재현 가능한 랜덤 생성
        random.seed(42)
        
        for i in range(96):
            household_size = random.choice(household_sizes)
            budget_level = random.choice(budget_levels)
            budget_amount = budget_amounts[budget_level]
            
            # 평수는 가구 구성에 맞게 조정
            if household_size == 1:
                pyung_range = (15, 25)
            elif household_size == 2:
                pyung_range = (20, 30)
            elif household_size == 3:
                pyung_range = (25, 35)
            elif household_size == 4:
                pyung_range = (30, 40)
            else:  # 5인 이상
                pyung_range = (35, 50)
            
            # 카테고리 개수 결정
            num_categories = 2
            if household_size >= 4:
                num_categories += 1
            if budget_level == 'high':
                num_categories += 1
            num_categories = min(num_categories, len(top_categories))
            
            # taste_id는 50% 확률로 있음
            taste_id = random.randint(1, 120) if random.random() < 0.5 else None
            
            random_test_cases.append({
                'name': f'랜덤 시나리오 {i+1}',
                'user_profile': {
                    'vibe': random.choice(vibes),
                    'household_size': household_size,
                    'housing_type': random.choice(housing_types),
                    'pyung': random.randint(pyung_range[0], pyung_range[1]),
                    'priority': random.choice(priorities),
                    'budget_level': budget_level,
                    'budget_amount': budget_amount,
                    'categories': random.sample(top_categories, num_categories) if len(top_categories) >= num_categories else top_categories,
                    'has_pet': random.choice([True, False]),
                    'onboarding_data': {
                        'cooking': random.choice(cooking_options),
                        'laundry': random.choice(laundry_options),
                        'media': random.choice(media_options)
                    }
                },
                'taste_id': taste_id
            })
        
        # 모든 테스트 케이스 합치기
        all_test_cases = test_cases + random_test_cases
        
        print(f"  ✓ 총 {len(all_test_cases)}개 테스트 케이스 생성 완료 (고정: {len(test_cases)}개, 랜덤: {len(random_test_cases)}개)")
        
        test_results = []
        total_tests = len(all_test_cases)
        
        for idx, test_case in enumerate(all_test_cases, 1):
            try:
                household_info = f"{test_case['user_profile']['household_size']}인"
                budget_info = f"{test_case['user_profile']['budget_level']} ({test_case['user_profile'].get('budget_amount', 0):,}원)"
                taste_info = f"taste_id: {test_case.get('taste_id', 'None')}"
                
                # 진행 상황 표시 (10개마다 또는 마지막)
                if idx % 10 == 0 or idx == total_tests:
                    print(f"  [{idx}/{total_tests}] 테스트 진행 중...")
                
                # 상세 로그는 처음 5개와 마지막 5개만 출력
                if idx <= 5 or idx > total_tests - 5:
                    print(f"  테스트: {test_case['name']} - {household_info}, 예산: {budget_info}, {taste_info}")
                
                # recommendation_engine 하나만 사용 (taste_id에 따라 내부에서 scoring 로직이 다르게 적용됨)
                final_result = None
                
                try:
                    if idx <= 5 or idx > total_tests - 5:
                        print(f"    → recommendation_engine 실행")
                    
                    final_result = recommendation_engine.get_recommendations(
                        user_profile=test_case['user_profile'],
                        taste_id=test_case.get('taste_id'),
                        limit=5
                    )
                    
                    if final_result.get('success'):
                        rec_count = final_result.get('count', 0)
                        if idx <= 5 or idx > total_tests - 5:
                            print(f"    ✓ 성공: {rec_count}개 추천")
                    else:
                        if idx <= 5 or idx > total_tests - 5:
                            print(f"    ✗ 실패: {final_result.get('message', 'Unknown error')}")
                        
                except Exception as rec_error:
                    if idx <= 5 or idx > total_tests - 5:
                        print(f"    ✗ 예외: {str(rec_error)}")
                    self.errors.append(f"{test_case['name']}: {str(rec_error)}")
                
                # 결과 검증
                validation = self._validate_recommendation_result(final_result, test_case['user_profile']) if final_result else {}
                
                test_results.append({
                    'name': test_case['name'],
                    'household_size': test_case['user_profile']['household_size'],
                    'budget_level': test_case['user_profile']['budget_level'],
                    'budget_amount': test_case['user_profile'].get('budget_amount', 0),
                    'taste_id': test_case.get('taste_id'),
                    'success': final_result.get('success', False) if final_result else False,
                    'count': final_result.get('count', 0) if final_result else 0,
                    'validation': validation,
                    'result': final_result
                })
                
            except Exception as e:
                test_results.append({
                    'name': test_case.get('name', 'Unknown'),
                    'household_size': test_case['user_profile'].get('household_size', 'N/A'),
                    'budget_level': test_case['user_profile'].get('budget_level', 'N/A'),
                    'budget_amount': test_case['user_profile'].get('budget_amount', 0),
                    'taste_id': test_case.get('taste_id'),
                    'success': False,
                    'error': str(e),
                    'traceback': traceback.format_exc()
                })
                print(f"    ✗ 예외 발생: {str(e)}")
                self.errors.append(f"{test_case.get('name', 'Unknown')}: {str(e)}")
        
        # 성공률 계산
        passed = sum(1 for r in test_results if r.get('success'))
        total = len(test_results)
        success_rate = (passed / total * 100) if total > 0 else 0
        
        # taste_id 사용 통계
        with_taste_id = sum(1 for r in test_results if r.get('taste_id') is not None)
        without_taste_id = total - with_taste_id
        with_taste_success = sum(1 for r in test_results if r.get('taste_id') is not None and r.get('success'))
        without_taste_success = sum(1 for r in test_results if r.get('taste_id') is None and r.get('success'))
        
        self.results['recommendation_tests'] = {
            'total': total,
            'passed': passed,
            'failed': total - passed,
            'success_rate': success_rate,
            'taste_id_usage': {
                'with_taste_id': with_taste_id,
                'without_taste_id': without_taste_id,
                'with_taste_success': with_taste_success,
                'without_taste_success': without_taste_success
            },
            'results': test_results
        }
        
        print(f"\n  추천 엔진 테스트 요약:")
        print(f"    총 테스트: {total}개")
        print(f"    성공: {passed}개 ({success_rate:.1f}%)")
        print(f"    실패: {total - passed}개")
        print(f"    taste_id 사용 통계:")
        print(f"      - taste_id 있음: {with_taste_id}개 (성공: {with_taste_success}개)")
        print(f"      - taste_id 없음: {without_taste_id}개 (성공: {without_taste_success}개)")
    
    def _validate_recommendation_result(self, result, user_profile):
        """추천 결과 검증"""
        validation = {
            'has_recommendations': False,
            'count_valid': False,
            'scores_valid': False,
            'scores_sorted': False,
            'price_within_budget': False,
            'categories_match': False
        }
        
        if not result.get('success'):
            return validation
        
        recommendations = result.get('recommendations', [])
        if not recommendations:
            return validation
        
        validation['has_recommendations'] = True
        validation['count_valid'] = len(recommendations) > 0
        
        # 점수 검증
        scores = [r.get('score', 0) for r in recommendations if 'score' in r]
        if scores:
            validation['scores_valid'] = all(0 <= s <= 1 for s in scores)
            validation['scores_sorted'] = scores == sorted(scores, reverse=True)
        
        # 예산 검증
        budget_level = user_profile.get('budget_level', 'medium')
        budget_mapping = {
            'low': (0, 500000),
            'medium': (500000, 2000000),
            'high': (2000000, 10000000),
        }
        max_price = budget_mapping.get(budget_level, (0, 2000000))[1]
        
        prices = [r.get('price', 0) for r in recommendations if 'price' in r]
        if prices:
            validation['price_within_budget'] = all(p <= max_price * 1.1 for p in prices)  # 10% 여유
        
        # 카테고리 검증
        expected_categories = user_profile.get('categories', [])
        if expected_categories:
            result_categories = [r.get('category', '') for r in recommendations if 'category' in r]
            validation['categories_match'] = any(
                cat in result_categories for cat in expected_categories
            ) if result_categories else False
        
        return validation
    
    def test_api_endpoints(self):
        """실제 API 엔드포인트 동작 확인"""
        from django.test import Client
        
        client = Client(HTTP_HOST='testserver')
        test_results = []
        
        # Oracle DB에서 실제 MAIN_CATEGORY 목록 가져오기
        try:
            categories_data = fetch_all_dict("""
                SELECT DISTINCT MAIN_CATEGORY
                FROM PRODUCT
                WHERE MAIN_CATEGORY IS NOT NULL
                ORDER BY MAIN_CATEGORY
            """)
            actual_categories = [cat['MAIN_CATEGORY'] for cat in categories_data]
        except Exception as e:
            actual_categories = ['TV', '냉장고', '에어컨', '세탁', '청소기']
        
        top_categories = actual_categories[:5] if len(actual_categories) >= 5 else actual_categories
        
        # API 테스트 케이스
        test_cases = [
            {
                'name': '기본 추천 API - 1인 가구 저예산 (taste_id 있음)',
                'endpoint': '/api/recommend/',
                'household_size': 1,
                'budget_level': 'low',
                'budget_amount': 500000,
                'data': {
                    'vibe': 'modern',
                    'household_size': 1,
                    'housing_type': 'apartment',
                    'pyung': 20,
                    'priority': 'value',
                    'budget_level': 'low',
                    'budget_amount': 500000,
                    'categories': top_categories[:2] if len(top_categories) >= 2 else top_categories,
                    'has_pet': False,
                    'onboarding_data': {
                        'cooking': 'rarely',
                        'laundry': 'few_times',
                        'media': 'balanced'
                    },
                    'taste_id': 1
                }
            },
            {
                'name': '기본 추천 API - 4인 가족 중예산 (taste_id 없음)',
                'endpoint': '/api/recommend/',
                'household_size': 4,
                'budget_level': 'medium',
                'budget_amount': 2000000,
                'data': {
                    'vibe': 'modern',
                    'household_size': 4,
                    'housing_type': 'apartment',
                    'pyung': 30,
                    'priority': 'tech',
                    'budget_level': 'medium',
                    'budget_amount': 2000000,
                    'categories': top_categories[:3] if len(top_categories) >= 3 else top_categories,
                    'has_pet': False
                }
            }
        ]
        
        for test_case in test_cases:
            try:
                household_info = f"{test_case.get('household_size', 'N/A')}인"
                budget_info = f"{test_case.get('budget_level', 'N/A')} ({test_case.get('budget_amount', 0):,}원)"
                print(f"  테스트: {test_case['name']} - {household_info}, 예산: {budget_info}")
                
                response = client.post(
                    test_case['endpoint'],
                    data=json.dumps(test_case['data']),
                    content_type='application/json'
                )
                
                if response.status_code == 200:
                    try:
                        data = json.loads(response.content)
                        test_results.append({
                            'name': test_case['name'],
                            'endpoint': test_case['endpoint'],
                            'household_size': test_case.get('household_size', 'N/A'),
                            'budget_level': test_case.get('budget_level', 'N/A'),
                            'budget_amount': test_case.get('budget_amount', 0),
                            'status': 'success',
                            'response_status': response.status_code,
                            'has_recommendations': data.get('success', False),
                            'count': data.get('count', 0)
                        })
                        print(f"    ✓ 성공: {response.status_code} (추천 {data.get('count', 0)}개)")
                    except json.JSONDecodeError:
                        test_results.append({
                            'name': test_case['name'],
                            'endpoint': test_case['endpoint'],
                            'status': 'warning',
                            'response_status': response.status_code,
                            'message': 'JSON 파싱 실패'
                        })
                        print(f"    ⚠ 경고: 응답이 JSON 형식이 아닙니다 ({response.status_code})")
                else:
                    try:
                        error_data = json.loads(response.content)
                        error_message = error_data.get('error', error_data.get('detail', 'Unknown error'))
                    except:
                        error_message = response.content.decode('utf-8')[:200]
                    
                    test_results.append({
                        'name': test_case['name'],
                        'endpoint': test_case['endpoint'],
                        'status': 'failed',
                        'response_status': response.status_code,
                        'error': error_message
                    })
                    print(f"    ✗ 실패: {response.status_code}")
                    print(f"      에러: {error_message}")
                    
            except Exception as e:
                test_results.append({
                    'name': test_case['name'],
                    'endpoint': test_case['endpoint'],
                    'status': 'failed',
                    'error': str(e)
                })
                print(f"    ✗ 예외 발생: {str(e)}")
        
        success_count = sum(1 for r in test_results if r.get('status') == 'success')
        total_count = len(test_results)
        
        self.results['api_tests'] = {
            'total': total_count,
            'success': success_count,
            'failed': total_count - success_count,
            'results': test_results
        }
    
    def generate_report(self):
        """최종 리포트 생성"""
        print("=" * 80)
        print("검증 결과 요약")
        print("=" * 80)
        print()
        
        # 연결 상태
        conn_status = self.results['connection'].get('status', 'unknown')
        print(f"Oracle DB 연결: {'✓ 성공' if conn_status == 'success' else '✗ 실패'}")
        
        # 데이터 확인
        data_status = self.results['data_checks'].get('status', 'unknown')
        print(f"데이터 확인: {'✓ 성공' if data_status == 'success' else '⚠ 경고' if data_status == 'warning' else '✗ 실패'}")
        
        # 추천 엔진 테스트
        rec_tests = self.results['recommendation_tests']
        if rec_tests:
            passed = rec_tests.get('passed', 0)
            total = rec_tests.get('total', 0)
            success_rate = rec_tests.get('success_rate', 0)
            print(f"추천 엔진 테스트: {passed}/{total} 통과 ({success_rate:.1f}%)")
            
            taste_stats = rec_tests.get('taste_id_usage', {})
            print(f"  - taste_id 있음: {taste_stats.get('with_taste_id', 0)}개 (성공: {taste_stats.get('with_taste_success', 0)}개)")
            print(f"  - taste_id 없음: {taste_stats.get('without_taste_id', 0)}개 (성공: {taste_stats.get('without_taste_success', 0)}개)")
            
            # 상세 결과 출력 (처음 10개만)
            print("\n  상세 결과 (처음 10개):")
            for result in rec_tests.get('results', [])[:10]:
                household_info = f"{result.get('household_size', 'N/A')}인"
                budget_info = f"{result.get('budget_level', 'N/A')}"
                if result.get('budget_amount'):
                    budget_info += f" ({result.get('budget_amount', 0):,}원)"
                taste_info = f"taste_id: {result.get('taste_id', 'None')}"
                status = "✓" if result.get('success') else "✗"
                print(f"    {status} {result.get('name', 'Unknown')} - {household_info}, 예산: {budget_info}, 추천: {result.get('count', 0)}개 ({taste_info})")
        
        # API 테스트
        api_tests = self.results['api_tests']
        if api_tests and 'total' in api_tests:
            success = api_tests.get('success', 0)
            total = api_tests.get('total', 0)
            print(f"API 엔드포인트: {success}/{total} 통과 ({success/total*100:.1f}%)")
        
        print()
        
        # 에러 및 경고
        if self.errors:
            print("에러:")
            for error in self.errors[:10]:  # 처음 10개만
                print(f"  ✗ {error}")
            if len(self.errors) > 10:
                print(f"  ... 외 {len(self.errors) - 10}개 에러")
            print()
        
        if self.warnings:
            print("경고:")
            for warning in self.warnings:
                print(f"  ⚠ {warning}")
            print()
        
        # 결과를 JSON 파일로 저장
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = BASE_DIR / f"backend_verification_report_{timestamp}.json"
        
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, ensure_ascii=False, indent=2, default=str)
        
        print(f"상세 리포트 저장: {report_file}")
        print()
        
        # 전체 성공 여부
        all_passed = (
            conn_status == 'success' and
            data_status in ['success', 'warning'] and
            rec_tests.get('passed', 0) == rec_tests.get('total', 0) and
            api_tests.get('success', 0) == api_tests.get('total', 0)
        )
        
        if all_passed:
            print("=" * 80)
            print("✓ 모든 검증 통과!")
            print("=" * 80)
        else:
            print("=" * 80)
            print("⚠ 일부 검증 실패. 위의 결과를 확인하세요.")
            print("=" * 80)


def main():
    """메인 함수"""
    verifier = BackendLogicVerifier()
    verifier.run_all_checks()


if __name__ == '__main__':
    main()

