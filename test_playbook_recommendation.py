"""
Playbook 추천 엔진 테스트 스크립트
"""
import os
import sys
import django
import json

# Django 설정
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from api.services.playbook_recommendation_engine import playbook_recommendation_engine

def test_recommendation():
    """추천 엔진 테스트"""
    
    # 테스트 시나리오 1: 4인 가족 아파트
    print("=" * 80)
    print("테스트 시나리오 1: 4인 가족 아파트 (중예산)")
    print("=" * 80)
    
    user_profile = {
        'vibe': 'modern',
        'household_size': 4,
        'housing_type': 'apartment',
        'pyung': 30,
        'priority': ['tech', 'design'],
        'budget_level': 'medium',
        'budget_amount': 2000000,
        'categories': ['TV', 'KITCHEN'],
        'main_space': 'living',
        'space_size': 'medium',
        'has_pet': False,
    }
    
    onboarding_data = {
        'cooking': 'sometimes',
        'laundry': 'weekly',
        'media': 'balanced',
    }
    
    result = playbook_recommendation_engine.get_recommendations(
        user_profile=user_profile,
        limit=6,
        onboarding_data=onboarding_data
    )
    
    print(f"\n✅ 성공: {result['success']}")
    print(f"📊 추천 개수: {result['count']}")
    print(f"\n추천 결과:")
    print("-" * 80)
    
    for idx, rec in enumerate(result['recommendations'], 1):
        print(f"\n{idx}. {rec.get('name', 'N/A')}")
        print(f"   카테고리: {rec.get('category', 'N/A')}")
        print(f"   가격: {rec.get('price', 0):,}원")
        print(f"   총점: {rec.get('total_score', 0):.1f}")
        breakdown = rec.get('score_breakdown', {})
        print(f"   - Spec: {breakdown.get('SpecScore', 0):.1f}")
        print(f"   - Preference: {breakdown.get('PreferenceScore', 0):.1f}")
        print(f"   - Lifestyle: {breakdown.get('LifestyleScore', 0):.1f}")
        print(f"   - Review: {breakdown.get('ReviewScore', 0):.1f}")
        print(f"   - Price: {breakdown.get('PriceScore', 0):.1f}")
    
    # 중복 체크
    product_ids = [rec.get('product_id') for rec in result['recommendations']]
    product_names = [rec.get('name') for rec in result['recommendations']]
    
    print("\n" + "=" * 80)
    print("중복 체크:")
    print(f"  - 제품 ID 중복: {len(product_ids) != len(set(product_ids))}")
    print(f"  - 제품명 중복: {len(product_names) != len(set(product_names))}")
    
    if len(product_ids) != len(set(product_ids)):
        print(f"  ⚠️ 중복 제품 ID 발견: {[pid for pid in product_ids if product_ids.count(pid) > 1]}")
    if len(product_names) != len(set(product_names)):
        print(f"  ⚠️ 중복 제품명 발견: {[name for name in product_names if product_names.count(name) > 1]}")
    
    print("=" * 80)
    
    # 테스트 시나리오 2: 2인 가구 원룸
    print("\n" + "=" * 80)
    print("테스트 시나리오 2: 2인 가구 원룸 (저예산)")
    print("=" * 80)
    
    user_profile2 = {
        'vibe': 'modern',
        'household_size': 2,
        'housing_type': 'studio',
        'pyung': 18,
        'priority': ['value'],
        'budget_level': 'low',
        'budget_amount': 800000,
        'categories': ['KITCHEN', 'LIVING'],
        'main_space': 'living',
        'space_size': 'small',
        'has_pet': False,
    }
    
    onboarding_data2 = {
        'cooking': 'sometimes',
        'laundry': 'weekly',
        'media': 'none',
    }
    
    result2 = playbook_recommendation_engine.get_recommendations(
        user_profile=user_profile2,
        limit=6,
        onboarding_data=onboarding_data2
    )
    
    print(f"\n✅ 성공: {result2['success']}")
    print(f"📊 추천 개수: {result2['count']}")
    print(f"\n추천 결과:")
    print("-" * 80)
    
    for idx, rec in enumerate(result2['recommendations'], 1):
        print(f"\n{idx}. {rec.get('name', 'N/A')}")
        print(f"   카테고리: {rec.get('category', 'N/A')}")
        print(f"   가격: {rec.get('price', 0):,}원")
        print(f"   총점: {rec.get('total_score', 0):.1f}")
        breakdown = rec.get('score_breakdown', {})
        print(f"   - Spec: {breakdown.get('SpecScore', 0):.1f}")
        print(f"   - Preference: {breakdown.get('PreferenceScore', 0):.1f}")
        print(f"   - Lifestyle: {breakdown.get('LifestyleScore', 0):.1f}")
        print(f"   - Review: {breakdown.get('ReviewScore', 0):.1f}")
        print(f"   - Price: {breakdown.get('PriceScore', 0):.1f}")
    
    # 중복 체크
    product_ids2 = [rec.get('product_id') for rec in result2['recommendations']]
    product_names2 = [rec.get('name') for rec in result2['recommendations']]
    
    print("\n" + "=" * 80)
    print("중복 체크:")
    print(f"  - 제품 ID 중복: {len(product_ids2) != len(set(product_ids2))}")
    print(f"  - 제품명 중복: {len(product_names2) != len(set(product_names2))}")
    
    if len(product_ids2) != len(set(product_ids2)):
        print(f"  ⚠️ 중복 제품 ID 발견: {[pid for pid in product_ids2 if product_ids2.count(pid) > 1]}")
    if len(product_names2) != len(set(product_names2)):
        print(f"  ⚠️ 중복 제품명 발견: {[name for name in product_names2 if product_names2.count(name) > 1]}")
    
    print("=" * 80)
    print("\n✅ 테스트 완료!")

if __name__ == '__main__':
    test_recommendation()


