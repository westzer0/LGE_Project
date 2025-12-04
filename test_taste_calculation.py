#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Taste 계산 로직 테스트
"""
import os
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

# Django 설정
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
import django
django.setup()

from api.utils.taste_classifier import taste_classifier


def test_taste_calculation():
    """다양한 온보딩 데이터로 taste 계산 테스트"""
    print("=" * 60)
    print("Taste 계산 로직 테스트")
    print("=" * 60)
    
    test_cases = [
        {
            'name': '1인 가구, 모던, 소형',
            'data': {
                'vibe': 'modern',
                'household_size': 1,
                'housing_type': 'apartment',
                'pyung': 15,
                'budget_level': 'low',
                'priority': ['design'],
                'has_pet': False,
                'main_space': ['living'],
                'cooking': 'rarely',
                'laundry': 'weekly',
                'media': 'balanced',
            }
        },
        {
            'name': '4인 가구, 클래식, 대형',
            'data': {
                'vibe': 'classic',
                'household_size': 4,
                'housing_type': 'house',
                'pyung': 45,
                'budget_level': 'high',
                'priority': ['performance', 'value'],
                'has_pet': True,
                'main_space': ['living', 'kitchen'],
                'cooking': 'daily',
                'laundry': 'daily',
                'media': 'high',
            }
        },
        {
            'name': '2인 가구, 미니멀, 중형',
            'data': {
                'vibe': 'minimal',
                'household_size': 2,
                'housing_type': 'apartment',
                'pyung': 30,
                'budget_level': 'medium',
                'priority': ['design', 'value'],
                'has_pet': False,
                'main_space': ['living'],
                'cooking': 'sometimes',
                'laundry': 'weekly',
                'media': 'balanced',
            }
        },
    ]
    
    print("\n[테스트 케이스별 Taste 계산 결과]\n")
    for i, test_case in enumerate(test_cases, 1):
        taste_id = taste_classifier.calculate_taste_from_onboarding(test_case['data'])
        print(f"{i}. {test_case['name']}")
        print(f"   Taste ID: {taste_id}")
        print(f"   설명: {taste_classifier.get_taste_description(taste_id)}")
        print()
    
    # 동일한 데이터로 재계산 (일관성 확인)
    print("\n[일관성 테스트]")
    test_data = test_cases[0]['data']
    taste_id_1 = taste_classifier.calculate_taste_from_onboarding(test_data)
    taste_id_2 = taste_classifier.calculate_taste_from_onboarding(test_data)
    print(f"첫 번째 계산: {taste_id_1}")
    print(f"두 번째 계산: {taste_id_2}")
    print(f"일관성: {'✓ 일치' if taste_id_1 == taste_id_2 else '✗ 불일치'}")
    
    print("\n" + "=" * 60)
    print("✅ 테스트 완료!")
    print("=" * 60)


if __name__ == '__main__':
    test_taste_calculation()

