#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Taste 기반 추천 일관성 검증 테스트

랜덤으로 30개의 taste를 선택하여 추천을 실행하고,
100번 반복하여 동일한 결과가 나오는지 검증합니다.
"""
import os
import sys
import random
import hashlib
import json
from pathlib import Path
from datetime import datetime
from collections import defaultdict

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

# Django 설정
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
import django
django.setup()

from api.services.taste_based_recommendation_engine import taste_based_recommendation_engine
from api.utils.taste_classifier import taste_classifier

# UTF-8 인코딩 설정 (Windows)
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# 온보딩 데이터 옵션
VIBE_OPTIONS = ['modern', 'classic', 'cozy', 'luxury', 'minimal', 'pop']
HOUSING_TYPE_OPTIONS = ['apartment', 'house', 'studio', 'officetel', 'detached']
PRIORITY_OPTIONS = ['design', 'tech', 'value', 'eco', 'performance', 'comfort']
BUDGET_LEVEL_OPTIONS = ['low', 'medium', 'high']
COOKING_OPTIONS = ['rarely', 'sometimes', 'daily', 'often']
LAUNDRY_OPTIONS = ['rarely', 'weekly', 'daily']
MEDIA_OPTIONS = ['none', 'low', 'balanced', 'high', 'gaming']
MAIN_SPACE_OPTIONS = ['living', 'kitchen', 'bedroom', 'dining', 'study']


def generate_random_onboarding_data() -> dict:
    """랜덤 온보딩 데이터 생성"""
    household_size = random.choice([1, 2, 3, 4, 5])
    pyung = random.choice([10, 15, 20, 25, 30, 35, 40, 45, 50])
    has_pet = random.choice([True, False])
    main_space_count = random.randint(1, 3)
    main_space = random.sample(MAIN_SPACE_OPTIONS, main_space_count)
    priority_count = random.randint(1, 2)
    priority = random.sample(PRIORITY_OPTIONS, priority_count)
    
    return {
        'vibe': random.choice(VIBE_OPTIONS),
        'household_size': household_size,
        'housing_type': random.choice(HOUSING_TYPE_OPTIONS),
        'pyung': pyung,
        'has_pet': has_pet,
        'main_space': main_space,
        'priority': priority,
        'budget_level': random.choice(BUDGET_LEVEL_OPTIONS),
        'cooking': random.choice(COOKING_OPTIONS),
        'laundry': random.choice(LAUNDRY_OPTIONS),
        'media': random.choice(MEDIA_OPTIONS),
    }


def generate_30_tastes():
    """30개의 랜덤 taste 생성"""
    tastes = []
    for _ in range(30):
        onboarding_data = generate_random_onboarding_data()
        taste_id = taste_classifier.calculate_taste_from_onboarding(onboarding_data)
        tastes.append({
            'taste_id': taste_id,
            'onboarding_data': onboarding_data
        })
    return tastes


def get_recommendation_hash(result: dict) -> str:
    """
    추천 결과를 해시값으로 변환
    
    Args:
        result: 추천 결과 딕셔너리
    
    Returns:
        해시값 문자열
    """
    if not result.get('success'):
        return 'FAILED'
    
    # 카테고리와 제품 ID 리스트로 정규화
    recommendations = result.get('recommendations', [])
    
    # 카테고리별 제품 ID 정렬
    category_products = defaultdict(list)
    for rec in recommendations:
        category = rec.get('category', 'UNKNOWN')
        product_id = rec.get('product_id', 'UNKNOWN')
        category_products[category].append(product_id)
    
    # 정렬하여 일관성 보장
    sorted_data = {
        'categories': sorted(result.get('categories', [])),
        'category_products': {
            cat: sorted(products) 
            for cat, products in sorted(category_products.items())
        },
        'count': result.get('count', 0)
    }
    
    # JSON 문자열로 변환 후 해시
    json_str = json.dumps(sorted_data, sort_keys=True, ensure_ascii=False)
    return hashlib.md5(json_str.encode('utf-8')).hexdigest()


def run_consistency_test(num_iterations=100):
    """일관성 검증 테스트 실행"""
    print("=" * 80)
    print("Taste 기반 추천 일관성 검증 테스트")
    print("=" * 80)
    print(f"테스트 설정:")
    print(f"  - Taste 개수: 30개")
    print(f"  - 반복 횟수: {num_iterations}번")
    print(f"  - 시작 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # 30개의 taste 생성
    print("1. 30개의 랜덤 taste 생성 중...")
    tastes = generate_30_tastes()
    print(f"   ✓ {len(tastes)}개 taste 생성 완료")
    print()
    
    # 각 taste별로 추천 결과 저장
    taste_results = {}
    
    print("2. 각 taste별 추천 실행 중...")
    for i, taste_info in enumerate(tastes, 1):
        taste_id = taste_info['taste_id']
        onboarding_data = taste_info['onboarding_data']
        
        # User profile 생성
        user_profile = {
            'vibe': onboarding_data.get('vibe', 'modern'),
            'household_size': onboarding_data.get('household_size', 2),
            'housing_type': onboarding_data.get('housing_type', 'apartment'),
            'priority': onboarding_data.get('priority', ['value']),
            'budget_level': onboarding_data.get('budget_level', 'medium'),
            'pyung': onboarding_data.get('pyung', 25),
            'has_pet': onboarding_data.get('has_pet', False),
            'cooking': onboarding_data.get('cooking', 'sometimes'),
            'laundry': onboarding_data.get('laundry', 'weekly'),
            'media': onboarding_data.get('media', 'balanced'),
            'onboarding_data': onboarding_data
        }
        
        # 추천 실행
        result = taste_based_recommendation_engine.get_recommendations(
            user_profile=user_profile,
            taste_id=taste_id,
            limit_per_category=3
        )
        
        # 결과 해시 저장
        result_hash = get_recommendation_hash(result)
        taste_results[taste_id] = {
            'onboarding_data': onboarding_data,
            'first_result_hash': result_hash,
            'first_result': result
        }
        
        if i % 10 == 0:
            print(f"   진행: {i}/{len(tastes)}")
    
    print(f"   ✓ {len(tastes)}개 taste 추천 완료")
    print()
    
    # 100번 반복하여 일관성 검증
    print("3. 일관성 검증 중 (100번 반복)...")
    inconsistencies = []
    
    # User profile 생성 함수 (재사용)
    def create_user_profile(onboarding_data):
        return {
            'vibe': onboarding_data.get('vibe', 'modern'),
            'household_size': onboarding_data.get('household_size', 2),
            'housing_type': onboarding_data.get('housing_type', 'apartment'),
            'priority': onboarding_data.get('priority', ['value']),
            'budget_level': onboarding_data.get('budget_level', 'medium'),
            'pyung': onboarding_data.get('pyung', 25),
            'has_pet': onboarding_data.get('has_pet', False),
            'cooking': onboarding_data.get('cooking', 'sometimes'),
            'laundry': onboarding_data.get('laundry', 'weekly'),
            'media': onboarding_data.get('media', 'balanced'),
            'onboarding_data': onboarding_data
        }
    
    for iteration in range(1, num_iterations + 1):
        iteration_inconsistencies = []
        
        for taste_info in tastes:
            taste_id = taste_info['taste_id']
            onboarding_data = taste_info['onboarding_data']
            
            # User profile 생성
            user_profile = create_user_profile(onboarding_data)
            
            # 추천 실행
            result = taste_based_recommendation_engine.get_recommendations(
                user_profile=user_profile,
                taste_id=taste_id,
                limit_per_category=3
            )
            
            # 결과 해시 비교
            result_hash = get_recommendation_hash(result)
            first_hash = taste_results[taste_id]['first_result_hash']
            
            if result_hash != first_hash:
                iteration_inconsistencies.append({
                    'taste_id': taste_id,
                    'first_hash': first_hash,
                    'current_hash': result_hash,
                    'iteration': iteration
                })
        
        if iteration_inconsistencies:
            inconsistencies.append({
                'iteration': iteration,
                'count': len(iteration_inconsistencies),
                'details': iteration_inconsistencies
            })
        
        # 진행 상황 출력 (5번마다)
        if iteration % 5 == 0 or iteration == num_iterations:
            status = "✓" if not iteration_inconsistencies else "✗"
            print(f"   반복 {iteration}/{num_iterations}: {status} ({len(iteration_inconsistencies)}개 불일치)")
    
    print()
    
    # 결과 리포트
    print("=" * 80)
    print("검증 결과 리포트")
    print("=" * 80)
    
    total_tests = num_iterations * len(tastes)
    total_inconsistencies = sum(inc['count'] for inc in inconsistencies)
    consistency_rate = (1 - total_inconsistencies / total_tests) * 100 if total_tests > 0 else 0
    
    print(f"총 테스트: {total_tests:,}개 (30 taste × {num_iterations} 반복)")
    print(f"불일치 발생: {total_inconsistencies}개")
    print(f"일관성 비율: {consistency_rate:.2f}%")
    print()
    
    if inconsistencies:
        print("⚠️  불일치 발생!")
        print()
        print("불일치 상세:")
        for inc in inconsistencies[:10]:  # 최대 10개만 출력
            print(f"  반복 {inc['iteration']}: {inc['count']}개 taste 불일치")
            for detail in inc['details'][:3]:  # 각 반복당 최대 3개만 출력
                print(f"    - Taste {detail['taste_id']}: 해시 불일치")
                print(f"      첫 번째: {detail['first_hash'][:16]}...")
                print(f"      현재:   {detail['current_hash'][:16]}...")
        
        if len(inconsistencies) > 10:
            print(f"  ... (총 {len(inconsistencies)}개 반복에서 불일치 발생)")
    else:
        print("✓ 모든 테스트 통과! 완벽한 일관성을 보입니다.")
    
    print()
    print(f"종료 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    
    # 결과를 파일로 저장
    output_file = f"consistency_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("=" * 80 + "\n")
        f.write("Taste 기반 추천 일관성 검증 테스트 결과\n")
        f.write("=" * 80 + "\n\n")
        f.write(f"테스트 설정:\n")
        f.write(f"  - Taste 개수: 30개\n")
        f.write(f"  - 반복 횟수: {num_iterations}번\n")
        f.write(f"  - 시작 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write(f"검증 결과:\n")
        f.write(f"  - 총 테스트: {total_tests:,}개\n")
        f.write(f"  - 불일치 발생: {total_inconsistencies}개\n")
        f.write(f"  - 일관성 비율: {consistency_rate:.2f}%\n\n")
        
        if inconsistencies:
            f.write("불일치 상세:\n")
            for inc in inconsistencies:
                f.write(f"\n반복 {inc['iteration']}: {inc['count']}개 taste 불일치\n")
                for detail in inc['details']:
                    f.write(f"  - Taste {detail['taste_id']}:\n")
                    f.write(f"    첫 번째 해시: {detail['first_hash']}\n")
                    f.write(f"    현재 해시:   {detail['current_hash']}\n")
        else:
            f.write("✓ 모든 테스트 통과! 완벽한 일관성을 보입니다.\n")
    
    print(f"\n결과 파일 저장: {output_file}")
    
    return {
        'total_tests': total_tests,
        'total_inconsistencies': total_inconsistencies,
        'consistency_rate': consistency_rate,
        'inconsistencies': inconsistencies
    }


if __name__ == '__main__':
    try:
        result = run_consistency_test(num_iterations=100)
        sys.exit(0 if result['total_inconsistencies'] == 0 else 1)
    except KeyboardInterrupt:
        print("\n\n테스트가 중단되었습니다.")
        sys.exit(1)
    except Exception as e:
        import traceback
        print(f"\n\n오류 발생: {str(e)}")
        print(traceback.format_exc())
        sys.exit(1)

