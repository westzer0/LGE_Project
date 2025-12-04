"""
필터링 결과 빠른 확인 스크립트
터미널에서 바로 결과 확인
"""
import os
import sys
import django

# Django 설정
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

import csv
from collections import defaultdict
from api.models import Product
from api.services.recommendation_engine import RecommendationEngine
from api.utils.product_filters import (
    filter_by_household_size,
    filter_by_housing_type,
    filter_by_lifestyle,
    filter_by_priority,
)
from django.db.models import Q

def analyze_filtering(limit=10):
    """필터링 분석"""
    csv_path = 'data/온보딩/taste_recommendations_768.csv'
    
    print("\n" + "="*80)
    print("📊 필터링 결과 분석")
    print("="*80)
    
    # CSV 읽기
    print(f"\n[1] CSV 파일 읽기: {csv_path}")
    data = []
    with open(csv_path, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            data.append(row)
    
    if limit:
        data = data[:limit]
    
    print(f"  ✅ {len(data)}개 케이스 로드")
    
    # 카테고리
    categories = sorted(list(Product.objects.values_list('category', flat=True).distinct()))
    print(f"  ✅ 카테고리: {categories}")
    
    # 엔진 초기화
    print(f"\n[2] 추천 엔진 초기화...")
    engine = RecommendationEngine()
    
    # 분석
    print(f"\n[3] 필터링 분석 중...")
    all_results = []
    filter_stats = defaultdict(int)
    
    for idx, row in enumerate(data, 1):
        print(f"  처리 중: {idx}/{len(data)} - taste_id {row.get('taste_id')}...", end=' ')
        
        try:
            result = analyze_single_case(engine, row, categories)
            all_results.append(result)
            
            # 통계 수집
            for excluded in result.get('excluded_products', []):
                for reason in excluded.get('reasons', []):
                    filter_stats[reason] += 1
            
            print(f"✅ (전:{result['products_before_count']} 후:{result['products_after_count']} 제외:{result['excluded_count']})")
        except Exception as e:
            print(f"❌ 오류: {e}")
            all_results.append({
                'taste_id': row.get('taste_id', '?'),
                'success': False,
                'error': str(e),
            })
    
    # 결과 출력
    print("\n" + "="*80)
    print("📊 필터링 결과 요약")
    print("="*80)
    
    successful = [r for r in all_results if r.get('success')]
    if not successful:
        print("\n❌ 성공한 케이스가 없습니다.")
        return
    
    total = len(successful)
    avg_before = sum(r.get('products_before_count', 0) for r in successful) / total
    avg_after = sum(r.get('products_after_count', 0) for r in successful) / total
    avg_excluded = sum(r.get('excluded_count', 0) for r in successful) / total
    
    print(f"\n✅ 총 케이스: {total}개")
    print(f"📦 평균 필터링 전: {avg_before:.1f}개")
    print(f"✅ 평균 필터링 후: {avg_after:.1f}개")
    print(f"❌ 평균 제외된 수: {avg_excluded:.1f}개")
    print(f"📉 필터링 효과: {(avg_excluded/avg_before*100):.1f}% 제외")
    
    # 필터별 통계
    print("\n" + "-"*80)
    print("🔍 필터별 제외 통계")
    print("-"*80)
    for filter_name, count in sorted(filter_stats.items(), key=lambda x: x[1], reverse=True):
        print(f"  {filter_name}: {count:,}개")
    
    # 케이스별 상세
    print("\n" + "-"*80)
    print("📋 케이스별 상세 결과")
    print("-"*80)
    print(f"{'ID':<6} {'인테리어':<25} {'가구':<20} {'전':<6} {'후':<6} {'제외':<6} {'추천':<6}")
    print("-"*80)
    
    for result in successful:
        taste_id = result.get('taste_id', '?')
        interior = result.get('interior_style', '')[:23]
        mate = result.get('mate', '')[:18]
        before = result.get('products_before_count', 0)
        after = result.get('products_after_count', 0)
        excluded = result.get('excluded_count', 0)
        rec_count = result.get('recommendations_count', 0)
        
        print(f"{taste_id:<6} {interior:<25} {mate:<20} {before:<6} {after:<6} {excluded:<6} {rec_count:<6}")
    
    # 제외된 제품 예시
    if successful:
        first = successful[0]
        excluded = first.get('excluded_products', [])
        if excluded:
            print("\n" + "-"*80)
            print(f"📌 케이스 {first.get('taste_id')}의 제외된 제품 예시 (최대 5개)")
            print("-"*80)
            for ep in excluded[:5]:
                reasons = ', '.join(ep.get('reasons', []))
                print(f"  ❌ {ep.get('product_name', '')[:50]}")
                print(f"     카테고리: {ep.get('category', '')}, 가격: {ep.get('price', 0):,}원")
                print(f"     제외 이유: {reasons}")
                print()
    
    print("="*80)

def analyze_single_case(engine, row, categories):
    """단일 케이스 분석"""
    taste_id = int(row.get('taste_id', 0))
    
    # user_profile 변환
    mate = row.get('메이트_구성', '')
    household_size = 2
    if '1인' in mate or '혼자' in mate:
        household_size = 1
    elif '2인' in mate or '신혼' in mate:
        household_size = 2
    elif '3~4인' in mate:
        household_size = 4
    elif '5인' in mate:
        household_size = 5
    
    priority_text = row.get('우선순위', '')
    priority = 'value'
    if '디자인' in priority_text:
        priority = 'design'
    elif 'AI' in priority_text or '스마트' in priority_text:
        priority = 'tech'
    elif '에너지' in priority_text:
        priority = 'eco'
    
    budget_text = row.get('예산_범위', '')
    budget_level = 'medium'
    if '500만원 미만' in budget_text:
        budget_level = 'low'
    elif '1,500만원' in budget_text or '고급형' in budget_text:
        budget_level = 'high'
    
    user_profile = {
        'vibe': 'modern',
        'household_size': household_size,
        'housing_type': 'apartment',
        'pyung': 25,
        'priority': priority,
        'budget_level': budget_level,
        'categories': categories,
        'has_pet': False,
        'cooking': 'sometimes',
        'laundry': 'weekly',
        'media': 'balanced',
    }
    
    # 기본 필터
    min_price, max_price = engine.budget_mapping.get(budget_level, engine.budget_mapping['medium'])
    products_before = (
        Product.objects
        .filter(
            is_active=True,
            category__in=categories,
            price__gte=min_price,
            price__lte=max_price,
            price__gt=0,
            spec__isnull=False,
        )
    )
    
    products_before_list = list(products_before)
    
    # 추가 필터 적용
    excluded_products = []
    for product in products_before_list:
        reasons = []
        
        if not filter_by_household_size(product, household_size):
            reasons.append('가족 구성')
        if not filter_by_housing_type(product, 'apartment', 25):
            reasons.append('주거 형태')
        if not filter_by_lifestyle(product, user_profile):
            reasons.append('생활 패턴')
        if not filter_by_priority(product, user_profile):
            reasons.append('우선순위')
        
        if reasons:
            excluded_products.append({
                'product_id': product.id,
                'product_name': product.name,
                'category': product.category,
                'price': float(product.price) if product.price else 0,
                'reasons': reasons,
            })
    
    products_after = [p for p in products_before_list if p.id not in [ep['product_id'] for ep in excluded_products]]
    
    return {
        'taste_id': taste_id,
        'interior_style': row.get('인테리어_스타일', ''),
        'mate': row.get('메이트_구성', ''),
        'priority': row.get('우선순위', ''),
        'products_before_count': len(products_before_list),
        'products_after_count': len(products_after),
        'excluded_count': len(excluded_products),
        'excluded_products': excluded_products,
        'recommendations_count': 0,
        'success': True,
    }

if __name__ == '__main__':
    import sys
    limit = int(sys.argv[1]) if len(sys.argv) > 1 else 10
    analyze_filtering(limit=limit)



