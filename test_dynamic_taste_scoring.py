#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
동적 Taste Scoring Logic 테스트
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

from api.utils.dynamic_taste_scoring import DynamicTasteScoring


def test_dynamic_scoring():
    """다양한 온보딩 데이터로 동적 scoring logic 생성 테스트"""
    print("=" * 60)
    print("동적 Taste Scoring Logic 생성 테스트")
    print("=" * 60)
    
    test_cases = [
        {
            'name': '1인 가구, 모던, 디자인 우선순위',
            'data': {
                'vibe': 'modern',
                'priority': ['design'],
                'budget_level': 'medium',
                'household_size': 1,
                'pyung': 20,
                'has_pet': False,
                'cooking': 'rarely',
                'laundry': 'weekly',
                'media': 'low',
            }
        },
        {
            'name': '4인 가족, 코지, 가성비 우선순위',
            'data': {
                'vibe': 'cozy',
                'priority': ['value'],
                'budget_level': 'low',
                'household_size': 4,
                'pyung': 35,
                'has_pet': True,
                'cooking': 'daily',
                'laundry': 'daily',
                'media': 'balanced',
            }
        },
        {
            'name': '2인 가구, 럭셔리, 기술 우선순위',
            'data': {
                'vibe': 'luxury',
                'priority': ['tech', 'design'],
                'budget_level': 'high',
                'household_size': 2,
                'pyung': 40,
                'has_pet': False,
                'cooking': 'sometimes',
                'laundry': 'weekly',
                'media': 'high',
            }
        },
    ]
    
    print("\n[테스트 케이스별 Scoring Logic 생성 결과]\n")
    for i, test_case in enumerate(test_cases, 1):
        print(f"{i}. {test_case['name']}")
        print("-" * 60)
        
        logic = DynamicTasteScoring.generate_scoring_logic(test_case['data'])
        
        # TV 가중치 출력
        print("\n[TV 가중치]")
        tv_weights = logic['weights']['TV']
        for attr, weight in sorted(tv_weights.items(), key=lambda x: x[1], reverse=True):
            print(f"  {attr:20s}: {weight:.4f}")
        
        # KITCHEN 가중치 출력
        print("\n[KITCHEN 가중치]")
        kitchen_weights = logic['weights']['KITCHEN']
        for attr, weight in sorted(kitchen_weights.items(), key=lambda x: x[1], reverse=True):
            print(f"  {attr:20s}: {weight:.4f}")
        
        # 보너스 출력
        if logic['bonuses']:
            print("\n[보너스]")
            for bonus in logic['bonuses']:
                print(f"  +{bonus['bonus']:.2f}: {bonus['condition']} ({bonus['reason']})")
        
        # 페널티 출력
        if logic['penalties']:
            print("\n[페널티]")
            for penalty in logic['penalties']:
                print(f"  {penalty['penalty']:.2f}: {penalty['condition']} ({penalty['reason']})")
        
        print("\n")
    
    print("=" * 60)
    print("✅ 테스트 완료!")
    print("=" * 60)


if __name__ == '__main__':
    test_dynamic_scoring()

