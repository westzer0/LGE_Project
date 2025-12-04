#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Taste별 제품 추천 시뮬레이션

랜덤으로 20개 taste를 선택하여 각 taste별로 제품 추천을 수행하고
결과를 테이블 형식으로 출력합니다.
"""
import os
import sys
import random
from pathlib import Path
from datetime import datetime
from tabulate import tabulate

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

# Django 설정
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
import django
django.setup()

from api.services.taste_based_recommendation_engine import taste_based_recommendation_engine
from api.utils.taste_classifier import taste_classifier


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
        'budget_level': random.choice(BUDGET_LEVEL_OPTIONS),
        'priority': priority,
        'has_pet': has_pet,
        'main_space': main_space,
        'cooking': random.choice(COOKING_OPTIONS),
        'laundry': random.choice(LAUNDRY_OPTIONS),
        'media': random.choice(MEDIA_OPTIONS),
    }


def format_price(price: int) -> str:
    """가격 포맷팅"""
    if price >= 10000:
        return f"{price/10000:.0f}만원"
    return f"{price:,}원"


def get_budget_display(budget_level: str, total_price: int = None) -> str:
    """예산 표시"""
    if total_price:
        return f"{budget_level} ({format_price(total_price)})"
    return budget_level


def simulate_taste_recommendations(num_scenarios: int = 20):
    """Taste별 추천 시뮬레이션 실행"""
    print("=" * 80)
    print("Taste별 제품 추천 시뮬레이션")
    print("=" * 80)
    print(f"랜덤 {num_scenarios}개 taste 선택하여 추천 수행\n")
    
    # 랜덤 taste_id 선택 (1-120)
    selected_taste_ids = random.sample(range(1, 121), num_scenarios)
    
    all_results = []
    
    for idx, taste_id in enumerate(selected_taste_ids, 1):
        print(f"[{idx}/{num_scenarios}] Taste ID {taste_id} 처리 중...")
        
        # 랜덤 온보딩 데이터 생성
        onboarding_data = generate_random_onboarding_data()
        
        # taste_id 검증 (생성된 온보딩 데이터로 계산한 taste_id와 일치하는지 확인)
        calculated_taste_id = taste_classifier.calculate_taste_from_onboarding(onboarding_data)
        
        # 만약 계산된 taste_id가 선택한 taste_id와 다르면 온보딩 데이터 조정
        # (간단하게 계산된 taste_id를 사용)
        actual_taste_id = calculated_taste_id
        
        # User profile 생성
        # 카테고리는 모든 카테고리를 포함하도록 설정
        user_profile = {
            'vibe': onboarding_data['vibe'],
            'household_size': onboarding_data['household_size'],
            'housing_type': onboarding_data['housing_type'],
            'pyung': onboarding_data['pyung'],
            'priority': onboarding_data['priority'],
            'budget_level': onboarding_data['budget_level'],
            'categories': ['TV', 'KITCHEN', 'LIVING'],  # 모든 카테고리 포함
            'onboarding_data': onboarding_data,  # 동적 scoring에 사용
        }
        
        # Taste 기반 추천 엔진 실행
        try:
            result = taste_based_recommendation_engine.get_recommendations(
                user_profile=user_profile,
                taste_id=actual_taste_id,
                num_categories=None,  # 자동 결정
                limit_per_category=3  # 카테고리당 3개
            )
            
            if result['success'] and result['recommendations']:
                recommendations = result['recommendations']
                
                # 카테고리별로 그룹화하여 정렬 (카테고리 순서 유지)
                from collections import OrderedDict
                by_category = OrderedDict()
                categories_order = result.get('categories', [])
                
                for cat in categories_order:
                    by_category[cat] = []
                
                for rec in recommendations:
                    cat = rec.get('category', '기타')
                    if cat not in by_category:
                        by_category[cat] = []
                    by_category[cat].append(rec)
                
                # 카테고리별로 정렬된 추천 리스트 생성
                top_recommendations = []
                for cat in categories_order:
                    if cat in by_category:
                        sorted_products = sorted(
                            by_category[cat],
                            key=lambda x: x.get('score', 0),
                            reverse=True
                        )
                        top_recommendations.extend(sorted_products)
                
                # 총액 계산
                total_price = sum(rec.get('price', 0) for rec in top_recommendations)
                
                all_results.append({
                    'scenario_num': idx,
                    'taste_id': actual_taste_id,
                    'onboarding_data': onboarding_data,
                    'recommendations': top_recommendations,
                    'total_price': total_price,
                    'count': len(top_recommendations),
                    'categories': result.get('categories', []),
                })
                
                print(f"  [OK] {len(top_recommendations)}개 제품 추천 완료")
            else:
                print(f"  [FAIL] 추천 실패: {result.get('message', '알 수 없음')}")
                all_results.append({
                    'scenario_num': idx,
                    'taste_id': actual_taste_id,
                    'onboarding_data': onboarding_data,
                    'recommendations': [],
                    'total_price': 0,
                    'count': 0,
                    'categories': result.get('categories', []),
                })
        except Exception as e:
            print(f"  [ERROR] 오류 발생: {str(e)}")
            all_results.append({
                'scenario_num': idx,
                'taste_id': actual_taste_id,
                'onboarding_data': onboarding_data,
                'recommendations': [],
                'total_price': 0,
                'count': 0,
            })
    
    # 결과 출력
    output_lines = []
    output_lines.append("Taste별 제품 추천 시뮬레이션 결과")
    output_lines.append("=" * 80)
    output_lines.append("")
    
    # 상세 추천 결과
    output_lines.append("[상세 추천 결과]")
    output_lines.append("=" * 80)
    
    for result in all_results:
        scenario_num = result['scenario_num']
        taste_id = result['taste_id']
        onboarding_data = result['onboarding_data']
        recommendations = result['recommendations']
        
        # 시나리오 헤더
        household_size = onboarding_data['household_size']
        housing_type = onboarding_data['housing_type']
        budget_level = onboarding_data['budget_level']
        total_price = result['total_price']
        selected_categories = result.get('categories', [])
        
        housing_type_kr = {
            'apartment': 'apartment',
            'house': 'house',
            'studio': 'studio',
            'officetel': 'officetel',
            'detached': 'detached',
        }.get(housing_type, housing_type)
        
        budget_display = get_budget_display(budget_level, total_price)
        
        output_lines.append(f"시나리오: 시나리오 {scenario_num}: {household_size}인 {housing_type_kr} (Taste {taste_id}, {budget_display})")
        output_lines.append(f"- 가구구성: {household_size}인")
        output_lines.append(f"- 주거형태: {housing_type_kr}")
        output_lines.append(f"- 평수: {onboarding_data['pyung']}평")
        output_lines.append(f"- 예산: {budget_display}")
        output_lines.append(f"- 우선순위: {', '.join(onboarding_data['priority']) if isinstance(onboarding_data['priority'], list) else onboarding_data['priority']}")
        output_lines.append(f"- 요리빈도: {onboarding_data['cooking']}")
        output_lines.append(f"- 세탁빈도: {onboarding_data['laundry']}")
        output_lines.append(f"- 미디어: {onboarding_data['media']}")
        output_lines.append(f"- Taste ID: {taste_id}")
        output_lines.append(f"- 선택된 카테고리: {', '.join(selected_categories)} ({len(selected_categories)}개)")
        output_lines.append("")
        
        if recommendations:
            # 테이블 데이터 준비 (카테고리별로 그룹화)
            table_data = []
            rank = 1
            current_category = None
            
            for rec in recommendations:
                category = rec.get('category', '기타')
                product_name = rec.get('model', rec.get('name', '알 수 없음'))
                price = rec.get('price', 0)
                score = rec.get('score', 0)
                
                # 카테고리 변경 시 구분선 추가 (선택적)
                if current_category != category:
                    current_category = category
                
                table_data.append([
                    rank,
                    category,  # MAIN CATEGORY 표시
                    product_name[:40],  # 제품명 길이 제한
                    format_price(price),
                    int(score * 100) if score else 0,
                ])
                rank += 1
            
            # 테이블 출력
            headers = ['순위', '카테고리', '제품명', '가격', '점수']
            table = tabulate(table_data, headers=headers, tablefmt='grid', stralign='left')
            output_lines.append(table)
        else:
            output_lines.append("추천 제품 없음")
        
        output_lines.append("")
        output_lines.append("")
    
    # 결과를 파일로 저장
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"taste_recommendations_{timestamp}.txt"
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(output_lines))
    
    print("\n" + "=" * 80)
    print(f"[완료] 시뮬레이션 완료!")
    print(f"[파일] 결과 파일: {output_file}")
    print("=" * 80)
    
    # 콘솔에도 출력
    print("\n" + '\n'.join(output_lines[:200]))  # 처음 200줄만 출력
    if len(output_lines) > 200:
        print(f"\n... (총 {len(output_lines)}줄, 전체 내용은 {output_file} 파일 참조)")


if __name__ == '__main__':
    simulate_taste_recommendations(num_scenarios=20)

