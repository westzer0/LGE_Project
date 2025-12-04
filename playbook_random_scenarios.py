"""
Playbook 추천 엔진 - 랜덤 10개 시나리오별 추천 모델 산출
"""
import os
import sys
import django
import random
from datetime import datetime

# Django 설정
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from api.models import Product
from api.services.playbook_recommendation_engine import playbook_recommendation_engine
from api.utils.product_type_classifier import extract_product_type
from tabulate import tabulate
from collections import defaultdict


# 랜덤 시나리오 생성 함수
def generate_random_scenario(index: int) -> dict:
    """랜덤 온보딩 시나리오 생성"""
    
    vibes = ['modern', 'cozy', 'pop', 'luxury']
    housing_types = ['apartment', 'detached', 'villa', 'officetel', 'studio']
    priorities = ['design', 'tech', 'eco', 'value']
    budget_levels = ['low', 'medium', 'high']
    cooking_options = ['rarely', 'sometimes', 'often', 'high']
    laundry_options = ['rarely', 'few_times', 'weekly', 'daily']
    media_options = ['none', 'balanced', 'gaming', 'ott', 'movie', 'heavy']
    
    household_size = random.choice([1, 2, 3, 4, 5])
    pyung = random.choice([15, 18, 20, 25, 28, 30, 35, 40])
    
    # 예산 레벨에 따른 예산 금액
    budget_amounts = {
        'low': random.randint(300000, 800000),
        'medium': random.randint(1000000, 3000000),
        'high': random.randint(4000000, 8000000)
    }
    
    budget_level = random.choice(budget_levels)
    budget_amount = budget_amounts[budget_level]
    
    # 카테고리 선택 (1~3개)
    all_categories = ['TV', 'KITCHEN', 'LIVING', 'AIR']
    num_categories = random.randint(1, 3)
    categories = random.sample(all_categories, num_categories)
    
    scenario_name = f"시나리오 {index}: {household_size}인 {housing_types[0]} ({budget_level} 예산)"
    
    return {
        'name': scenario_name,
        'user_profile': {
            'vibe': random.choice(vibes),
            'household_size': household_size,
            'housing_type': random.choice(housing_types),
            'pyung': pyung,
            'priority': random.choice(priorities),
            'budget_level': budget_level,
            'budget_amount': budget_amount,
            'categories': categories,
        },
        'onboarding_data': {
            'cooking': random.choice(cooking_options),
            'laundry': random.choice(laundry_options),
            'media': random.choice(media_options),
            'main_space': random.choice(['living', 'kitchen', 'dressing', 'all']),
        }
    }


def format_price(price):
    """가격 포맷팅"""
    if price is None:
        return '-'
    return f"{int(price):,}원"


def simulate_playbook_recommendations(scenarios):
    """Playbook 추천 엔진으로 시나리오별 추천 실행"""
    results = []
    
    for idx, scenario in enumerate(scenarios, 1):
        print(f"\n[{idx}/{len(scenarios)}] {scenario['name']} 처리 중...")
        
        try:
            result = playbook_recommendation_engine.get_recommendations(
                user_profile=scenario['user_profile'],
                onboarding_data=scenario['onboarding_data'],
                limit=10  # 충분히 많이 가져오기
            )
            
            if result.get('success'):
                results.append({
                    'scenario': scenario,
                    'recommendations': result.get('recommendations', [])
                })
                print(f"  ✅ 추천 성공: {len(result.get('recommendations', []))}개")
            else:
                results.append({
                    'scenario': scenario,
                    'recommendations': []
                })
                print(f"  ❌ 추천 실패: {result.get('error', 'Unknown error')}")
        
        except Exception as e:
            print(f"  ❌ 오류 발생: {e}")
            results.append({
                'scenario': scenario,
                'recommendations': []
            })
    
    return results


def create_summary_table(scenarios, results):
    """요약 표 생성"""
    table_data = []
    
    for scenario, result in zip(scenarios, results):
        recs = result['recommendations']
        
        if not recs:
            table_data.append([
                scenario['name'],
                scenario['user_profile']['household_size'],
                scenario['user_profile']['housing_type'],
                scenario['user_profile']['budget_level'],
                '-',
                '-',
                '추천 실패'
            ])
            continue
        
        # 제품 타입별 정리
        by_type = defaultdict(list)
        total_price = 0
        
        for rec in recs:
            # product_type이 있으면 사용, 없으면 제품명에서 추출
            product_type = rec.get('product_type')
            if not product_type:
                from api.models import Product
                product_id = rec.get('product_id')
                if product_id:
                    try:
                        product = Product.objects.get(id=product_id)
                        product_type = extract_product_type(product) or '기타'
                    except:
                        product_type = '기타'
                else:
                    product_type = '기타'
            
            name = rec.get('name', rec.get('model', 'Unknown'))
            price = rec.get('price', 0) or rec.get('discount_price', 0) or 0
            score = rec.get('total_score', rec.get('score', 0))
            
            by_type[product_type].append({
                'name': name,
                'price': price,
                'score': score
            })
            total_price += float(price) if price else 0
        
        # 제품 타입별 개수
        type_counts = {k: len(v) for k, v in by_type.items()}
        types_str = ', '.join([f"{k}: {v}개" for k, v in type_counts.items()])
        
        # 상위 3개 제품명
        top_products = [rec.get('name', rec.get('model', 'Unknown'))[:25] for rec in recs[:3]]
        products_str = ', '.join(top_products) if top_products else '-'
        
        table_data.append([
            scenario['name'],
            f"{scenario['user_profile']['household_size']}인",
            scenario['user_profile']['housing_type'],
            scenario['user_profile']['budget_level'],
            format_price(total_price),
            len(recs),
            types_str,
            products_str
        ])
    
    headers = [
        '시나리오',
        '가구구성',
        '주거형태',
        '예산수준',
        '총액',
        '추천수',
        '제품종류별',
        '상위3개 제품'
    ]
    
    return tabulate(table_data, headers=headers, tablefmt='grid', stralign='left')


def create_detailed_table(scenarios, results):
    """상세 표 생성 - 제품 타입별 세분화 그룹화"""
    all_tables = []
    
    # 제품 타입 우선순위 정의 (사용자가 요청한 순서)
    product_type_order = [
        'TV', '에어컨', 'CONDITIONER', 'LAUNDRY', '공기청정기', '제습기', '가습기',
        '안마의자', '워시콤보', '의류건조기', '청소기', '식기세척기', '와인셀러',
        '전기레인지', '정수기', '맥주제조기', '광파오븐전자레인지', '김치냉장고', '냉장고',
        '세탁기', '건조기', '워시타워', '오븐', '전자레인지', '스타일러', '홈브루'
    ]
    
    for scenario, result in zip(scenarios, results):
        recs = result['recommendations']
        
        if not recs:
            continue
        
        # 시나리오 정보
        scenario_info = f"""시나리오: {scenario['name']}
- 가구구성: {scenario['user_profile']['household_size']}인
- 주거형태: {scenario['user_profile']['housing_type']}
- 평수: {scenario['user_profile'].get('pyung', '-')}평
- 예산: {scenario['user_profile']['budget_level']} ({format_price(scenario['user_profile'].get('budget_amount', 0))})
- 우선순위: {scenario['user_profile'].get('priority', '-')}
- 요리빈도: {scenario['onboarding_data'].get('cooking', '-')}
- 세탁빈도: {scenario['onboarding_data'].get('laundry', '-')}
- 미디어: {scenario['onboarding_data'].get('media', '-')}
"""
        
        # 제품 타입별로 그룹화
        by_product_type = defaultdict(list)
        for rec in recs:
            # product_type이 있으면 사용, 없으면 제품명에서 추출
            product_type = rec.get('product_type')
            if not product_type:
                # 제품명에서 추출 시도
                from api.models import Product
                product_id = rec.get('product_id')
                if product_id:
                    try:
                        product = Product.objects.get(id=product_id)
                        product_type = extract_product_type(product) or '기타'
                    except:
                        product_type = '기타'
                else:
                    product_type = '기타'
            
            by_product_type[product_type].append(rec)
        
        # 제품 타입별로 정렬된 전체 추천 리스트 생성
        table_data = []
        rank = 1
        
        # 우선순위 순서대로 처리
        for product_type in product_type_order:
            if product_type not in by_product_type:
                continue
            
            type_recs = sorted(
                by_product_type[product_type],
                key=lambda x: float(x.get('total_score', x.get('score', 0)) or 0),
                reverse=True
            )
            
            # 각 제품 타입별 상위 3개만
            for rec in type_recs[:3]:
                score = rec.get('total_score', rec.get('score', 0))
                name = rec.get('name', rec.get('model', 'Unknown'))
                price = rec.get('price', 0) or rec.get('discount_price', 0) or 0
                
                table_data.append([
                    rank,
                    product_type,
                    name,
                    format_price(price),
                    int(float(score)) if score else 0
                ])
                rank += 1
        
        # 나머지 제품 타입들도 처리
        for product_type in sorted(by_product_type.keys()):
            if product_type in product_type_order:
                continue
            
            type_recs = sorted(
                by_product_type[product_type],
                key=lambda x: float(x.get('total_score', x.get('score', 0)) or 0),
                reverse=True
            )
            
            for rec in type_recs[:3]:
                score = rec.get('total_score', rec.get('score', 0))
                name = rec.get('name', rec.get('model', 'Unknown'))
                price = rec.get('price', 0) or rec.get('discount_price', 0) or 0
                
                table_data.append([
                    rank,
                    product_type,
                    name,
                    format_price(price),
                    int(float(score)) if score else 0
                ])
                rank += 1
        
        if table_data:
            headers = ['순위', '제품타입', '제품명', '가격', '점수']
            table = tabulate(table_data, headers=headers, tablefmt='grid', stralign='left')
            all_tables.append(f"{scenario_info}\n{table}\n\n")
    
    return '\n'.join(all_tables)


def main():
    """메인 실행"""
    print("="*80)
    print("Playbook 추천 엔진 - 랜덤 10개 시나리오별 추천 모델 산출")
    print("="*80)
    print()
    
    # 랜덤 시드 설정 (재현 가능하도록)
    random.seed(42)
    
    # 랜덤 10개 시나리오 생성
    print("[1단계] 랜덤 10개 시나리오 생성 중...")
    scenarios = [generate_random_scenario(i) for i in range(1, 11)]
    
    print("\n생성된 시나리오:")
    for idx, scenario in enumerate(scenarios, 1):
        print(f"  {idx}. {scenario['name']}")
        print(f"     - {scenario['user_profile']['household_size']}인, {scenario['user_profile']['housing_type']}, {scenario['user_profile']['budget_level']}")
        print(f"     - 요리: {scenario['onboarding_data']['cooking']}, 세탁: {scenario['onboarding_data']['laundry']}, 미디어: {scenario['onboarding_data']['media']}")
    
    print()
    print("[2단계] Playbook 추천 엔진으로 추천 실행 중...")
    results = simulate_playbook_recommendations(scenarios)
    
    print()
    print("="*80)
    print("📊 요약 표")
    print("="*80)
    summary_table = create_summary_table(scenarios, results)
    print(summary_table)
    print()
    
    print("="*80)
    print("📋 상세 추천 결과")
    print("="*80)
    detailed_table = create_detailed_table(scenarios, results)
    print(detailed_table)
    
    # 결과를 파일로 저장
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f'playbook_random_scenarios_{timestamp}.txt'
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("Playbook 추천 엔진 - 랜덤 10개 시나리오별 추천 모델 산출 결과\n")
        f.write("="*80 + "\n\n")
        f.write("📊 요약 표\n")
        f.write("="*80 + "\n")
        f.write(summary_table + "\n\n")
        f.write("📋 상세 추천 결과\n")
        f.write("="*80 + "\n")
        f.write(detailed_table + "\n")
    
    print()
    print(f"✅ 결과가 '{output_file}' 파일로 저장되었습니다.")


if __name__ == '__main__':
    main()

