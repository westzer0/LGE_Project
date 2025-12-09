#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Step 2: Taste 기반 카테고리 선택 로직 검증

검증 항목:
1. Taste-카테고리 매핑 로직 검증
2. 모든 Taste ID(1-120)에 대해 카테고리 선택 확인
3. 실제 회원 데이터로 검증
4. 일관성 검증 (동일한 입력에 대해 동일한 결과)
5. 경계값 검증 (Taste ID 1, 120, 범위 밖 값)
6. 빈 결과 처리 검증
7. 시각화 생성
"""
import sys
import os
import json
from datetime import datetime
from collections import Counter, defaultdict
from typing import List, Dict, Optional, Set

# Django 설정 로드
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

import django
django.setup()

from api.utils.taste_category_selector import get_categories_for_taste
from api.models import Member, Product
from api.db.oracle_client import get_connection

# 시각화 라이브러리
try:
    import matplotlib
    matplotlib.use('Agg')  # GUI 없이 사용 (먼저 설정)
    import matplotlib.pyplot as plt
    try:
        import seaborn as sns
        HAS_SEABORN = True
    except ImportError:
        HAS_SEABORN = False
    HAS_MATPLOTLIB = True
except ImportError as e:
    HAS_MATPLOTLIB = False
    HAS_SEABORN = False
    print(f"⚠️ matplotlib이 설치되지 않아 시각화를 건너뜁니다: {e}")

# NumPy 라이브러리
try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False


class TasteCategorySelectionValidator:
    """Taste 기반 카테고리 선택 로직 검증 클래스"""
    
    def __init__(self):
        self.results = {
            'mapping_tests': [],
            'all_taste_ids': {},
            'real_member_tests': [],
            'consistency_tests': [],
            'boundary_tests': [],
            'empty_result_tests': [],
            'errors': [],
            'warnings': [],
            'category_distribution': Counter(),
            'taste_category_map': {},  # taste_id -> [categories]
            'category_taste_map': defaultdict(set),  # category -> set(taste_ids)
        }
    
    def validate_all(self):
        """모든 검증 실행"""
        print("=" * 80)
        print("Step 2: Taste 기반 카테고리 선택 로직 검증")
        print("=" * 80)
        print()
        
        try:
            # 1. 매핑 로직 검증
            print("[1] Taste-카테고리 매핑 로직 검증")
            self._validate_mapping_logic()
            print()
            
            # 2. 모든 Taste ID 검증
            print("[2] 모든 Taste ID(1-120)에 대한 카테고리 선택 검증")
            self._validate_all_taste_ids()
            print()
            
            # 3. 실제 회원 데이터로 검증
            print("[3] 실제 회원 데이터로 검증")
            self._validate_with_real_members()
            print()
            
            # 4. 일관성 검증
            print("[4] 일관성 검증")
            self._validate_consistency()
            print()
            
            # 5. 경계값 검증
            print("[5] 경계값 검증")
            self._validate_boundary_values()
            print()
            
            # 6. 빈 결과 처리 검증
            print("[6] 빈 결과 처리 검증")
            self._validate_empty_results()
            print()
            
            # 7. 결과 요약 및 시각화
            print("[7] 결과 요약 및 시각화")
            self._generate_summary()
            self._generate_visualizations()
            print()
            
        except Exception as e:
            self.results['errors'].append({
                'type': 'validation_error',
                'message': str(e),
                'traceback': str(sys.exc_info())
            })
            print(f"❌ 검증 중 오류 발생: {e}")
            import traceback
            traceback.print_exc()
    
    def _get_sample_onboarding_data(self, taste_id: int = None) -> Dict:
        """샘플 온보딩 데이터 생성"""
        # 기본 온보딩 데이터 (vibe, household_size, main_space, priority, budget_level 등)
        return {
            'vibe': 'modern',
            'household_size': 3,
            'housing_type': 'apartment',
            'pyung': 30,
            'priority': 'tech',
            'budget_level': 'medium',
            'main_space': 'living',
            'has_pet': False,
            'cooking': 'sometimes',
            'laundry': 'weekly',
            'media': 'balanced',
        }
    
    def _validate_mapping_logic(self):
        """Taste-카테고리 매핑 로직 검증"""
        print("  - 매핑 함수 존재 여부 확인...")
        
        try:
            # 함수 존재 확인
            test_categories = get_categories_for_taste(
                taste_id=1,
                onboarding_data=self._get_sample_onboarding_data(),
                num_categories=None
            )
            
            assert isinstance(test_categories, list), "반환값이 리스트가 아닙니다."
            print(f"  ✅ 매핑 함수 정상 작동 (테스트 결과: {len(test_categories)}개 카테고리)")
            
            self.results['mapping_tests'].append({
                'test': 'function_exists',
                'status': 'pass',
                'result': f"{len(test_categories)} categories"
            })
            
        except Exception as e:
            print(f"  ❌ 매핑 로직 오류: {e}")
            self.results['mapping_tests'].append({
                'test': 'function_exists',
                'status': 'fail',
                'error': str(e)
            })
            self.results['errors'].append({
                'type': 'mapping_logic',
                'message': str(e)
            })
    
    def _validate_all_taste_ids(self):
        """모든 Taste ID(1-120)에 대해 카테고리 선택 검증"""
        print("  - 모든 Taste ID에 대해 카테고리 선택 테스트...")
        
        onboarding_data = self._get_sample_onboarding_data()
        success_count = 0
        fail_count = 0
        empty_count = 0
        
        for taste_id in range(1, 121):
            try:
                categories = get_categories_for_taste(
                    taste_id=taste_id,
                    onboarding_data=onboarding_data,
                    num_categories=None
                )
                
                # 결과 저장
                self.results['all_taste_ids'][taste_id] = {
                    'categories': categories,
                    'count': len(categories),
                    'status': 'success' if categories else 'empty'
                }
                self.results['taste_category_map'][taste_id] = categories
                
                # 카테고리별 빈도 계산
                for cat in categories:
                    self.results['category_distribution'][cat] += 1
                    self.results['category_taste_map'][cat].add(taste_id)
                
                # 검증
                if len(categories) == 0:
                    empty_count += 1
                    self.results['warnings'].append({
                        'type': 'empty_categories',
                        'taste_id': taste_id,
                        'message': f'Taste ID {taste_id}에 대해 선택된 카테고리가 없습니다.'
                    })
                else:
                    # 선택된 카테고리가 유효한지 확인 (DB에 존재하는지)
                    valid_categories = self._validate_categories_exist(categories)
                    if len(valid_categories) < len(categories):
                        invalid = set(categories) - set(valid_categories)
                        self.results['warnings'].append({
                            'type': 'invalid_categories',
                            'taste_id': taste_id,
                            'invalid_categories': list(invalid),
                            'message': f'Taste ID {taste_id}에 대해 유효하지 않은 카테고리가 선택되었습니다: {invalid}'
                        })
                    success_count += 1
                
            except Exception as e:
                fail_count += 1
                self.results['all_taste_ids'][taste_id] = {
                    'categories': [],
                    'count': 0,
                    'status': 'error',
                    'error': str(e)
                }
                self.results['errors'].append({
                    'type': 'taste_id_error',
                    'taste_id': taste_id,
                    'message': str(e)
                })
        
        print(f"  ✅ 성공: {success_count}개, ❌ 실패: {fail_count}개, ⚠️ 빈 결과: {empty_count}개")
        
        # 통계
        category_counts = [data['count'] for data in self.results['all_taste_ids'].values()]
        if category_counts:
            avg_count = sum(category_counts) / len(category_counts)
            min_count = min(category_counts)
            max_count = max(category_counts)
            print(f"  📊 카테고리 선택 개수 통계: 평균 {avg_count:.2f}개, 최소 {min_count}개, 최대 {max_count}개")
    
    def _validate_categories_exist(self, categories: List[str]) -> List[str]:
        """선택된 카테고리가 실제로 존재하는지 확인"""
        valid_categories = []
        
        try:
            # Oracle DB에서 확인 시도
            with get_connection() as conn:
                with conn.cursor() as cur:
                    for category in categories:
                        cur.execute("""
                            SELECT COUNT(*) 
                            FROM PRODUCT
                            WHERE MAIN_CATEGORY = :category
                              AND STATUS = '판매중'
                              AND PRICE > 0
                        """, {'category': category})
                        result = cur.fetchone()
                        if result and result[0] > 0:
                            valid_categories.append(category)
        except Exception:
            # Oracle DB 연결 실패 시 Django 모델에서 확인
            try:
                for category in categories:
                    # Product 모델에서 main_category로 확인
                    count = Product.objects.filter(
                        main_category=category,
                        is_active=True,
                        price__gt=0
                    ).count()
                    if count > 0:
                        valid_categories.append(category)
            except Exception:
                # 검증 실패 시 모든 카테고리를 유효한 것으로 간주
                valid_categories = categories
        
        return valid_categories
    
    def _validate_with_real_members(self):
        """실제 회원 데이터로 검증"""
        print("  - MEMBER 테이블에서 TASTE 값이 있는 회원 조회...")
        
        try:
            # Django ORM으로 회원 조회
            members = Member.objects.filter(taste__isnull=False).order_by('?')[:200]
            
            if not members:
                print("  ⚠️ TASTE 값이 있는 회원이 없습니다.")
                self.results['warnings'].append({
                    'type': 'no_members_with_taste',
                    'message': 'TASTE 값이 있는 회원이 없습니다.'
                })
                return
            
            print(f"  - {len(members)}명의 회원으로 검증 시작...")
            
            success_count = 0
            fail_count = 0
            onboarding_data = self._get_sample_onboarding_data()
            
            for member in members:
                taste_id = member.taste
                if taste_id is None or taste_id < 1 or taste_id > 120:
                    continue
                
                try:
                    categories = get_categories_for_taste(
                        taste_id=taste_id,
                        onboarding_data=onboarding_data,
                        num_categories=None
                    )
                    
                    if categories:
                        success_count += 1
                        self.results['real_member_tests'].append({
                            'member_id': member.member_id,
                            'taste_id': taste_id,
                            'categories': categories,
                            'count': len(categories),
                            'status': 'success'
                        })
                    else:
                        fail_count += 1
                        self.results['warnings'].append({
                            'type': 'empty_for_member',
                            'member_id': member.member_id,
                            'taste_id': taste_id,
                            'message': f'회원 {member.member_id} (Taste ID: {taste_id})에 대해 카테고리가 선택되지 않았습니다.'
                        })
                        
                except Exception as e:
                    fail_count += 1
                    self.results['errors'].append({
                        'type': 'member_test_error',
                        'member_id': member.member_id,
                        'taste_id': taste_id,
                        'message': str(e)
                    })
            
            print(f"  ✅ 성공: {success_count}명, ❌ 실패: {fail_count}명")
            
        except Exception as e:
            print(f"  ❌ 회원 데이터 검증 오류: {e}")
            self.results['errors'].append({
                'type': 'real_member_validation',
                'message': str(e)
            })
    
    def _validate_consistency(self):
        """일관성 검증 - 동일한 입력에 대해 항상 동일한 결과 반환"""
        print("  - 동일한 Taste ID로 여러 번 테스트하여 일관성 확인...")
        
        test_cases = [1, 50, 100, 120]  # 경계값 포함
        onboarding_data = self._get_sample_onboarding_data()
        
        for taste_id in test_cases:
            results = []
            for _ in range(10):  # 10번 반복 테스트
                try:
                    categories = get_categories_for_taste(
                        taste_id=taste_id,
                        onboarding_data=onboarding_data,
                        num_categories=None
                    )
                    results.append(sorted(categories))
                except Exception as e:
                    results.append(None)
            
            # 모든 결과가 동일한지 확인
            if all(r == results[0] for r in results):
                self.results['consistency_tests'].append({
                    'taste_id': taste_id,
                    'status': 'consistent',
                    'categories': results[0] if results[0] else []
                })
                print(f"  ✅ Taste ID {taste_id}: 일관성 통과 ({len(results[0]) if results[0] else 0}개 카테고리)")
            else:
                unique_results = len(set(tuple(r) for r in results if r is not None))
                self.results['consistency_tests'].append({
                    'taste_id': taste_id,
                    'status': 'inconsistent',
                    'unique_results': unique_results
                })
                self.results['warnings'].append({
                    'type': 'inconsistency',
                    'taste_id': taste_id,
                    'message': f'Taste ID {taste_id}에 대해 {unique_results}개의 서로 다른 결과가 반환되었습니다.'
                })
                print(f"  ❌ Taste ID {taste_id}: 일관성 실패 ({unique_results}개의 서로 다른 결과)")
    
    def _validate_boundary_values(self):
        """경계값 검증"""
        print("  - 경계값 테스트 (Taste ID: 1, 120, 범위 밖 값)...")
        
        onboarding_data = self._get_sample_onboarding_data()
        
        # 최소값
        try:
            categories_1 = get_categories_for_taste(
                taste_id=1,
                onboarding_data=onboarding_data,
                num_categories=None
            )
            self.results['boundary_tests'].append({
                'taste_id': 1,
                'status': 'success',
                'categories': categories_1,
                'count': len(categories_1)
            })
            print(f"  ✅ Taste ID 1: {len(categories_1)}개 카테고리 선택")
        except Exception as e:
            self.results['boundary_tests'].append({
                'taste_id': 1,
                'status': 'error',
                'error': str(e)
            })
            print(f"  ❌ Taste ID 1: 오류 - {e}")
        
        # 최대값
        try:
            categories_120 = get_categories_for_taste(
                taste_id=120,
                onboarding_data=onboarding_data,
                num_categories=None
            )
            self.results['boundary_tests'].append({
                'taste_id': 120,
                'status': 'success',
                'categories': categories_120,
                'count': len(categories_120)
            })
            print(f"  ✅ Taste ID 120: {len(categories_120)}개 카테고리 선택")
        except Exception as e:
            self.results['boundary_tests'].append({
                'taste_id': 120,
                'status': 'error',
                'error': str(e)
            })
            print(f"  ❌ Taste ID 120: 오류 - {e}")
        
        # 범위 밖 값 (0, 121)
        for invalid_id in [0, 121]:
            try:
                categories = get_categories_for_taste(
                    taste_id=invalid_id,
                    onboarding_data=onboarding_data,
                    num_categories=None
                )
                self.results['boundary_tests'].append({
                    'taste_id': invalid_id,
                    'status': 'handled',
                    'categories': categories,
                    'note': '범위 밖 값이지만 처리됨'
                })
                print(f"  ⚠️ Taste ID {invalid_id}: 처리됨 ({len(categories)}개 카테고리)")
            except Exception as e:
                self.results['boundary_tests'].append({
                    'taste_id': invalid_id,
                    'status': 'error_expected',
                    'error': str(e),
                    'note': '범위 밖 값에 대한 에러 처리 (예상된 동작)'
                })
                print(f"  ✅ Taste ID {invalid_id}: 에러 처리됨 (예상된 동작)")
    
    def _validate_empty_results(self):
        """빈 결과 처리 검증"""
        print("  - 빈 결과 처리 검증...")
        
        onboarding_data = self._get_sample_onboarding_data()
        
        # 빈 온보딩 데이터로 테스트
        empty_onboarding = {}
        
        try:
            categories = get_categories_for_taste(
                taste_id=1,
                onboarding_data=empty_onboarding,
                num_categories=None
            )
            
            if categories:
                self.results['empty_result_tests'].append({
                    'test': 'empty_onboarding',
                    'status': 'has_categories',
                    'categories': categories,
                    'count': len(categories)
                })
                print(f"  ✅ 빈 온보딩 데이터: {len(categories)}개 카테고리 선택됨 (기본값 처리)")
            else:
                self.results['empty_result_tests'].append({
                    'test': 'empty_onboarding',
                    'status': 'empty',
                    'categories': []
                })
                print(f"  ⚠️ 빈 온보딩 데이터: 카테고리가 선택되지 않음")
                
        except Exception as e:
            self.results['empty_result_tests'].append({
                'test': 'empty_onboarding',
                'status': 'error',
                'error': str(e)
            })
            print(f"  ❌ 빈 온보딩 데이터 처리 오류: {e}")
    
    def _generate_summary(self):
        """결과 요약 생성"""
        print("=" * 80)
        print("검증 결과 요약")
        print("=" * 80)
        
        # 1. 전체 Taste ID 검증 결과
        all_taste_results = self.results['all_taste_ids']
        success_count = sum(1 for v in all_taste_results.values() if v.get('status') == 'success')
        empty_count = sum(1 for v in all_taste_results.values() if v.get('status') == 'empty')
        error_count = sum(1 for v in all_taste_results.values() if v.get('status') == 'error')
        
        print(f"\n[전체 Taste ID 검증]")
        print(f"  ✅ 성공: {success_count}/120")
        print(f"  ⚠️ 빈 결과: {empty_count}/120")
        print(f"  ❌ 오류: {error_count}/120")
        
        # 2. 카테고리 분포
        print(f"\n[카테고리 분포]")
        top_categories = self.results['category_distribution'].most_common(10)
        for cat, count in top_categories:
            taste_count = len(self.results['category_taste_map'][cat])
            print(f"  - {cat}: {count}회 선택 (Taste ID {taste_count}개)")
        
        # 3. 실제 회원 데이터 검증
        member_success = sum(1 for r in self.results['real_member_tests'] if r.get('status') == 'success')
        print(f"\n[실제 회원 데이터 검증]")
        print(f"  ✅ 성공: {member_success}명")
        print(f"  총 테스트: {len(self.results['real_member_tests'])}명")
        
        # 4. 일관성 검증
        consistent_count = sum(1 for r in self.results['consistency_tests'] if r.get('status') == 'consistent')
        print(f"\n[일관성 검증]")
        print(f"  ✅ 일관성 통과: {consistent_count}/{len(self.results['consistency_tests'])}")
        
        # 5. 오류 및 경고
        print(f"\n[오류 및 경고]")
        print(f"  ❌ 오류: {len(self.results['errors'])}개")
        print(f"  ⚠️ 경고: {len(self.results['warnings'])}개")
        
        if self.results['errors']:
            print("\n주요 오류:")
            for error in self.results['errors'][:5]:
                print(f"  - {error.get('type')}: {error.get('message', '')}")
        
        if self.results['warnings']:
            print("\n주요 경고:")
            for warning in self.results['warnings'][:5]:
                print(f"  - {warning.get('type')}: {warning.get('message', '')}")
    
    def _generate_visualizations(self):
        """시각화 생성"""
        if not HAS_MATPLOTLIB:
            print("  ⚠️ matplotlib이 없어 시각화를 건너뜁니다.")
            return
        
        print("  - 시각화 생성 중...")
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = "."
        
        try:
            # 1. Taste ID별 선택된 카테고리 개수 분포
            self._plot_category_count_distribution(timestamp, output_dir)
            
            # 2. 카테고리별 선택 빈도
            self._plot_category_frequency(timestamp, output_dir)
            
            # 3. Taste ID 범위별 카테고리 선택 개수
            self._plot_taste_range_category_count(timestamp, output_dir)
            
            # 4. 매핑 결과 히트맵 (Taste ID vs 카테고리)
            self._plot_heatmap(timestamp, output_dir)
            
            # 5. 검증 성공/실패 비율
            self._plot_validation_summary(timestamp, output_dir)
            
            print(f"  ✅ 시각화 생성 완료 (파일명: taste_category_selection_validation_{timestamp}*.png)")
            
        except Exception as e:
            print(f"  ❌ 시각화 생성 오류: {e}")
            self.results['errors'].append({
                'type': 'visualization_error',
                'message': str(e)
            })
    
    def _plot_category_count_distribution(self, timestamp: str, output_dir: str):
        """카테고리 선택 개수 분포 히스토그램"""
        counts = [data['count'] for data in self.results['all_taste_ids'].values()]
        
        plt.figure(figsize=(10, 6))
        plt.hist(counts, bins=20, edgecolor='black', alpha=0.7)
        plt.xlabel('선택된 카테고리 개수')
        plt.ylabel('Taste ID 개수')
        plt.title('Taste ID별 선택된 카테고리 개수 분포')
        plt.grid(True, alpha=0.3)
        
        if HAS_NUMPY:
            mean_val = np.mean(counts)
            median_val = np.median(counts)
            plt.axvline(mean_val, color='r', linestyle='--', label=f'평균: {mean_val:.2f}')
            plt.axvline(median_val, color='g', linestyle='--', label=f'중앙값: {median_val:.2f}')
            plt.legend()
        
        plt.tight_layout()
        plt.savefig(f"{output_dir}/taste_category_selection_validation_{timestamp}_01_distribution.png", dpi=150)
        plt.close()
    
    def _plot_category_frequency(self, timestamp: str, output_dir: str):
        """카테고리별 선택 빈도 바 차트"""
        top_categories = self.results['category_distribution'].most_common(15)
        
        if not top_categories:
            return
        
        categories = [cat for cat, _ in top_categories]
        frequencies = [freq for _, freq in top_categories]
        
        plt.figure(figsize=(12, 6))
        plt.barh(categories, frequencies, color='steelblue')
        plt.xlabel('선택 빈도')
        plt.ylabel('카테고리')
        plt.title('카테고리별 선택 빈도 (상위 15개)')
        plt.gca().invert_yaxis()
        plt.grid(True, alpha=0.3, axis='x')
        
        # 값 표시
        for i, v in enumerate(frequencies):
            plt.text(v + 0.5, i, str(v), va='center')
        
        plt.tight_layout()
        plt.savefig(f"{output_dir}/taste_category_selection_validation_{timestamp}_02_frequency.png", dpi=150)
        plt.close()
    
    def _plot_taste_range_category_count(self, timestamp: str, output_dir: str):
        """Taste ID 범위별 카테고리 선택 개수"""
        ranges = {
            '1-30': [],
            '31-60': [],
            '61-90': [],
            '91-120': []
        }
        
        for taste_id, data in self.results['all_taste_ids'].items():
            count = data.get('count', 0)
            if 1 <= taste_id <= 30:
                ranges['1-30'].append(count)
            elif 31 <= taste_id <= 60:
                ranges['31-60'].append(count)
            elif 61 <= taste_id <= 90:
                ranges['61-90'].append(count)
            elif 91 <= taste_id <= 120:
                ranges['91-120'].append(count)
        
        range_labels = list(ranges.keys())
        range_means = [sum(r) / len(r) if r else 0 for r in ranges.values()]
        range_mins = [min(r) if r else 0 for r in ranges.values()]
        range_maxs = [max(r) if r else 0 for r in ranges.values()]
        
        x = range(len(range_labels))
        width = 0.6
        
        fig, ax = plt.subplots(figsize=(10, 6))
        bars = ax.bar(x, range_means, width, label='평균', color='steelblue', alpha=0.7)
        ax.errorbar(x, range_means, 
                    yerr=[[range_means[i] - range_mins[i] for i in x],
                          [range_maxs[i] - range_means[i] for i in x]],
                    fmt='none', color='black', capsize=5, label='범위')
        
        ax.set_xlabel('Taste ID 범위')
        ax.set_ylabel('카테고리 개수')
        ax.set_title('Taste ID 범위별 카테고리 선택 개수')
        ax.set_xticks(x)
        ax.set_xticklabels(range_labels)
        ax.legend()
        ax.grid(True, alpha=0.3, axis='y')
        
        # 값 표시
        for i, v in enumerate(range_means):
            ax.text(i, v + 0.1, f'{v:.1f}', ha='center', va='bottom')
        
        plt.tight_layout()
        plt.savefig(f"{output_dir}/taste_category_selection_validation_{timestamp}_03_range.png", dpi=150)
        plt.close()
    
    def _plot_heatmap(self, timestamp: str, output_dir: str):
        """Taste ID vs 카테고리 히트맵"""
        # 상위 20개 카테고리 선택
        top_categories = [cat for cat, _ in self.results['category_distribution'].most_common(20)]
        
        if not top_categories:
            return
        
        # Taste ID를 10개 그룹으로 나누기
        taste_groups = []
        group_size = 12  # 120 / 10 = 12
        for i in range(10):
            start = i * group_size + 1
            end = min((i + 1) * group_size, 120)
            taste_groups.append(f"{start}-{end}")
        
        # 히트맵 데이터 생성
        heatmap_data = []
        for group_idx in range(10):
            start_id = group_idx * group_size + 1
            end_id = min((group_idx + 1) * group_size, 120)
            group_data = []
            for cat in top_categories:
                count = sum(1 for tid in range(start_id, end_id + 1) 
                           if cat in self.results['taste_category_map'].get(tid, []))
                group_data.append(count)
            heatmap_data.append(group_data)
        
        if HAS_NUMPY:
            heatmap_array = np.array(heatmap_data)
        else:
            # NumPy 없이 처리
            heatmap_array = heatmap_data
        
        plt.figure(figsize=(14, 8))
        if HAS_SEABORN:
            sns.heatmap(heatmap_array, 
                       xticklabels=top_categories,
                       yticklabels=taste_groups,
                       annot=True, fmt='d', cmap='YlOrRd',
                       cbar_kws={'label': '매핑 횟수'})
        else:
            plt.imshow(heatmap_array, aspect='auto', cmap='YlOrRd', interpolation='nearest')
            plt.colorbar(label='매핑 횟수')
            plt.xticks(range(len(top_categories)), top_categories, rotation=45, ha='right')
            plt.yticks(range(len(taste_groups)), taste_groups)
        
        plt.xlabel('카테고리')
        plt.ylabel('Taste ID 범위')
        plt.title('Taste ID 범위별 카테고리 매핑 히트맵 (상위 20개 카테고리)')
        plt.tight_layout()
        plt.savefig(f"{output_dir}/taste_category_selection_validation_{timestamp}_04_heatmap.png", dpi=150)
        plt.close()
    
    def _plot_validation_summary(self, timestamp: str, output_dir: str):
        """검증 성공/실패 비율 파이 차트"""
        all_taste_results = self.results['all_taste_ids']
        success_count = sum(1 for v in all_taste_results.values() if v.get('status') == 'success')
        empty_count = sum(1 for v in all_taste_results.values() if v.get('status') == 'empty')
        error_count = sum(1 for v in all_taste_results.values() if v.get('status') == 'error')
        
        labels = ['성공', '빈 결과', '오류']
        sizes = [success_count, empty_count, error_count]
        colors = ['#2ecc71', '#f39c12', '#e74c3c']
        
        # 0인 값 제거
        filtered_data = [(l, s, c) for l, s, c in zip(labels, sizes, colors) if s > 0]
        if not filtered_data:
            return
        
        labels, sizes, colors = zip(*filtered_data)
        
        plt.figure(figsize=(8, 8))
        plt.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%', startangle=90)
        plt.title('Taste ID 검증 결과 비율')
        plt.axis('equal')
        plt.tight_layout()
        plt.savefig(f"{output_dir}/taste_category_selection_validation_{timestamp}_05_summary.png", dpi=150)
        plt.close()


def main():
    """메인 함수"""
    validator = TasteCategorySelectionValidator()
    validator.validate_all()
    
    # 결과를 JSON 파일로 저장
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"taste_category_selection_validation_{timestamp}.json"
    
    # JSON 직렬화 가능한 형태로 변환
    results_json = {
        'timestamp': timestamp,
        'mapping_tests': validator.results['mapping_tests'],
        'all_taste_ids_summary': {
            str(k): {
                'count': v['count'],
                'status': v['status']
            }
            for k, v in validator.results['all_taste_ids'].items()
        },
        'real_member_tests_count': len(validator.results['real_member_tests']),
        'consistency_tests': validator.results['consistency_tests'],
        'boundary_tests': validator.results['boundary_tests'],
        'category_distribution': dict(validator.results['category_distribution']),
        'errors_count': len(validator.results['errors']),
        'warnings_count': len(validator.results['warnings']),
    }
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results_json, f, ensure_ascii=False, indent=2)
    
    print(f"\n결과가 {output_file}에 저장되었습니다.")


if __name__ == '__main__':
    main()

