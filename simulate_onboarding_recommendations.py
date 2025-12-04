"""
온보딩 선택 결과별 추천 가전패키지 시뮬레이션

다양한 온보딩 시나리오에 대해 추천 결과를 생성하고 표로 정리합니다.
"""
import os
import sys
import django

# Django 설정
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from api.models import Product
from api.services.recommendation_engine import recommendation_engine
from api.services.playbook_recommendation_engine import playbook_recommendation_engine
from tabulate import tabulate
from collections import defaultdict


# 온보딩 시나리오 정의
SCENARIOS = [
    {
        'name': '1인 가구 원룸 (저예산)',
        'user_profile': {
            'vibe': 'modern',
            'household_size': 1,
            'housing_type': 'studio',
            'pyung': 15,
            'priority': 'value',
            'budget_level': 'low',
            'budget_amount': 500000,
            'categories': ['TV', 'KITCHEN', 'LIVING'],
        },
        'onboarding_data': {
            'cooking': 'rarely',
            'laundry': 'few_times',
            'media': 'balanced',
            'main_space': 'living',
        }
    },
    {
        'name': '신혼부부 아파트 (중예산)',
        'user_profile': {
            'vibe': 'modern',
            'household_size': 2,
            'housing_type': 'apartment',
            'pyung': 25,
            'priority': 'design',
            'budget_level': 'medium',
            'budget_amount': 2000000,
            'categories': ['TV', 'KITCHEN', 'LIVING'],
        },
        'onboarding_data': {
            'cooking': 'often',
            'laundry': 'weekly',
            'media': 'balanced',
            'main_space': 'all',
        }
    },
    {
        'name': '4인 가족 단독주택 (중예산)',
        'user_profile': {
            'vibe': 'cozy',
            'household_size': 4,
            'housing_type': 'detached',
            'pyung': 40,
            'priority': 'tech',
            'budget_level': 'medium',
            'budget_amount': 3000000,
            'categories': ['TV', 'KITCHEN', 'LIVING'],
        },
        'onboarding_data': {
            'cooking': 'high',
            'laundry': 'daily',
            'media': 'heavy',
            'main_space': 'all',
        }
    },
    {
        'name': '1인 가구 오피스텔 (중예산)',
        'user_profile': {
            'vibe': 'modern',
            'household_size': 1,
            'housing_type': 'officetel',
            'pyung': 20,
            'priority': 'tech',
            'budget_level': 'medium',
            'budget_amount': 1500000,
            'categories': ['TV', 'KITCHEN'],
        },
        'onboarding_data': {
            'cooking': 'sometimes',
            'laundry': 'few_times',
            'media': 'gaming',
            'main_space': 'living',
        }
    },
    {
        'name': '4인 가족 아파트 (고예산)',
        'user_profile': {
            'vibe': 'luxury',
            'household_size': 4,
            'housing_type': 'apartment',
            'pyung': 35,
            'priority': 'design',
            'budget_level': 'high',
            'budget_amount': 5000000,
            'categories': ['TV', 'KITCHEN', 'LIVING'],
        },
        'onboarding_data': {
            'cooking': 'high',
            'laundry': 'daily',
            'media': 'heavy',
            'main_space': 'all',
        }
    },
    {
        'name': '2인 가구 빌라 (중예산)',
        'user_profile': {
            'vibe': 'cozy',
            'household_size': 2,
            'housing_type': 'villa',
            'pyung': 30,
            'priority': 'eco',
            'budget_level': 'medium',
            'budget_amount': 2500000,
            'categories': ['TV', 'KITCHEN', 'LIVING'],
        },
        'onboarding_data': {
            'cooking': 'often',
            'laundry': 'weekly',
            'media': 'balanced',
            'main_space': 'kitchen',
        }
    },
    {
        'name': '3인 가족 아파트 (중예산, 미디어 중심)',
        'user_profile': {
            'vibe': 'modern',
            'household_size': 3,
            'housing_type': 'apartment',
            'pyung': 28,
            'priority': 'tech',
            'budget_level': 'medium',
            'budget_amount': 2200000,
            'categories': ['TV', 'LIVING'],
        },
        'onboarding_data': {
            'cooking': 'sometimes',
            'laundry': 'weekly',
            'media': 'gaming',
            'main_space': 'living',
        }
    },
    {
        'name': '2인 가구 원룸 (저예산)',
        'user_profile': {
            'vibe': 'modern',
            'household_size': 2,
            'housing_type': 'studio',
            'pyung': 18,
            'priority': 'value',
            'budget_level': 'low',
            'budget_amount': 800000,
            'categories': ['KITCHEN', 'LIVING'],
        },
        'onboarding_data': {
            'cooking': 'sometimes',
            'laundry': 'weekly',
            'media': 'none',
            'main_space': 'all',
        }
    },
]


def format_price(price):
    """가격 포맷팅"""
    if price is None:
        return '-'
    return f"{int(price):,}원"


def simulate_recommendations(scenario, use_playbook=False):
    """시나리오별 추천 실행"""
    try:
        if use_playbook:
            result = playbook_recommendation_engine.get_recommendations(
                user_profile=scenario['user_profile'],
                onboarding_data=scenario['onboarding_data'],
                limit=5
            )
        else:
            result = recommendation_engine.get_recommendations(
                user_profile=scenario['user_profile'],
                limit=5
            )
        
        if result.get('success'):
            return result['recommendations']
        else:
            return []
    except Exception as e:
        print(f"[오류] {scenario['name']}: {e}")
        return []


def create_summary_table(scenarios, results, use_playbook=False):
    """요약 표 생성"""
    table_data = []
    
    for i, (scenario, recs) in enumerate(zip(scenarios, results), 1):
        if not recs:
            table_data.append([
                i,
                scenario['name'],
                scenario['user_profile']['household_size'],
                scenario['user_profile']['housing_type'],
                scenario['user_profile']['budget_level'],
                '-',
                '-',
                '-',
                '추천 실패'
            ])
            continue
        
        # 카테고리별 제품 정리
        by_category = defaultdict(list)
        total_price = 0
        
        for rec in recs:
            category = rec.get('category', rec.get('category_display', 'UNKNOWN'))
            name = rec.get('name', rec.get('model', 'Unknown'))
            price = rec.get('price', 0) or rec.get('discount_price', 0) or 0
            by_category[category].append(f"{name} ({format_price(price)})")
            total_price += float(price) if price else 0
        
        # 카테고리별 항목 문자열
        items = []
        if 'TV' in by_category:
            items.append(f"TV: {len(by_category['TV'])}개")
        if 'KITCHEN' in by_category or '주방가전' in by_category:
            items.append(f"주방: {len(by_category.get('KITCHEN', by_category.get('주방가전', [])))}개")
        if 'LIVING' in by_category or '생활가전' in by_category:
            items.append(f"생활: {len(by_category.get('LIVING', by_category.get('생활가전', [])))}개")
        
        items_str = ', '.join(items) if items else '-'
        
        # 추천 제품명 (상위 3개)
        top_products = [rec.get('name', rec.get('model', 'Unknown'))[:30] for rec in recs[:3]]
        products_str = ', '.join(top_products) if top_products else '-'
        
        table_data.append([
            i,
            scenario['name'],
            f"{scenario['user_profile']['household_size']}인",
            scenario['user_profile']['housing_type'],
            scenario['user_profile']['budget_level'],
            format_price(total_price),
            len(recs),
            items_str,
            products_str
        ])
    
    headers = [
        '번호',
        '시나리오',
        '가구구성',
        '주거형태',
        '예산수준',
        '총액',
        '추천수',
        '카테고리별',
        '추천제품 (상위3)'
    ]
    
    return tabulate(table_data, headers=headers, tablefmt='grid', stralign='left')


def create_detailed_table(scenarios, results, use_playbook=False):
    """상세 표 생성"""
    all_tables = []
    
    for scenario, recs in zip(scenarios, results):
        if not recs:
            continue
        
        table_data = []
        
        # 시나리오 정보
        scenario_info = f"""
시나리오: {scenario['name']}
- 가구구성: {scenario['user_profile']['household_size']}인
- 주거형태: {scenario['user_profile']['housing_type']}
- 평수: {scenario['user_profile'].get('pyung', '-')}평
- 예산: {scenario['user_profile']['budget_level']} ({format_price(scenario['user_profile'].get('budget_amount', 0))})
- 우선순위: {scenario['user_profile'].get('priority', '-')}
- 요리빈도: {scenario['onboarding_data'].get('cooking', '-')}
- 세탁빈도: {scenario['onboarding_data'].get('laundry', '-')}
- 미디어: {scenario['onboarding_data'].get('media', '-')}
"""
        
        for idx, rec in enumerate(recs, 1):
            score = rec.get('score', rec.get('total_score', 0))
            category = rec.get('category', rec.get('category_display', 'UNKNOWN'))
            name = rec.get('name', rec.get('model', 'Unknown'))
            price = rec.get('price', 0) or rec.get('discount_price', 0) or 0
            
            table_data.append([
                idx,
                category,
                name[:40],
                format_price(price),
                f"{float(score):.1f}" if score else '-'
            ])
        
        headers = ['순위', '카테고리', '제품명', '가격', '점수']
        table = tabulate(table_data, headers=headers, tablefmt='grid', stralign='left')
        
        all_tables.append(scenario_info + '\n' + table + '\n')
    
    return '\n' + '='*80 + '\n'.join(all_tables)


def main():
    """메인 실행"""
    print("="*80)
    print("온보딩 선택 결과별 추천 가전패키지 시뮬레이션")
    print("="*80)
    print()
    
    # 기존 추천 엔진 사용
    print("[1단계] 기존 추천 엔진 시뮬레이션 실행 중...")
    results_original = []
    for scenario in SCENARIOS:
        print(f"  - {scenario['name']} 처리 중...")
        recs = simulate_recommendations(scenario, use_playbook=False)
        results_original.append(recs)
    
    print()
    print("="*80)
    print("📊 요약 표 (기존 추천 엔진)")
    print("="*80)
    summary_table = create_summary_table(SCENARIOS, results_original, use_playbook=False)
    print(summary_table)
    print()
    
    # Playbook 추천 엔진 사용
    print()
    print("[2단계] Playbook 추천 엔진 시뮬레이션 실행 중...")
    results_playbook = []
    for scenario in SCENARIOS:
        print(f"  - {scenario['name']} 처리 중...")
        recs = simulate_recommendations(scenario, use_playbook=True)
        results_playbook.append(recs)
    
    print()
    print("="*80)
    print("📊 요약 표 (Playbook 추천 엔진)")
    print("="*80)
    summary_table_pb = create_summary_table(SCENARIOS, results_playbook, use_playbook=True)
    print(summary_table_pb)
    print()
    
    # 상세 표 생성
    print("="*80)
    print("📋 상세 추천 결과 (기존 추천 엔진)")
    print("="*80)
    detailed_table = create_detailed_table(SCENARIOS, results_original, use_playbook=False)
    print(detailed_table)
    
    print()
    print("="*80)
    print("📋 상세 추천 결과 (Playbook 추천 엔진)")
    print("="*80)
    detailed_table_pb = create_detailed_table(SCENARIOS, results_playbook, use_playbook=True)
    print(detailed_table_pb)
    
    # 결과를 파일로 저장
    output_file = 'onboarding_simulation_results.txt'
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("온보딩 선택 결과별 추천 가전패키지 시뮬레이션 결과\n")
        f.write("="*80 + "\n\n")
        f.write("📊 요약 표 (기존 추천 엔진)\n")
        f.write("="*80 + "\n")
        f.write(summary_table + "\n\n")
        f.write("📊 요약 표 (Playbook 추천 엔진)\n")
        f.write("="*80 + "\n")
        f.write(summary_table_pb + "\n\n")
        f.write(detailed_table + "\n")
        f.write(detailed_table_pb + "\n")
    
    print()
    print(f"✅ 결과가 '{output_file}' 파일로 저장되었습니다.")


if __name__ == '__main__':
    main()


