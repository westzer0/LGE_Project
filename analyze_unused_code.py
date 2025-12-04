#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
사용되지 않는 코드 분석

기존 recommendation_engine.py와 새로운 taste_based_recommendation_engine.py의
사용 여부를 확인하고, 중복되거나 사용되지 않는 로직을 찾습니다.
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

print("=" * 80)
print("사용되지 않는 코드 분석")
print("=" * 80)

# 1. views.py에서 어떤 엔진을 사용하는지 확인
print("\n[1] views.py에서 사용하는 추천 엔진:")
with open('api/views.py', 'r', encoding='utf-8') as f:
    content = f.read()
    
    if 'recommendation_engine.get_recommendations' in content:
        print("  - recommendation_engine.get_recommendations: 사용 중")
        # 사용 위치 찾기
        import re
        matches = re.finditer(r'recommendation_engine\.get_recommendations[^\n]*', content)
        for match in matches:
            line_num = content[:match.start()].count('\n') + 1
            print(f"    Line {line_num}: {match.group()[:60]}")
    else:
        print("  - recommendation_engine.get_recommendations: 사용 안 함")
    
    if 'playbook_recommendation_engine.get_recommendations' in content:
        print("  - playbook_recommendation_engine.get_recommendations: 사용 중")
    else:
        print("  - playbook_recommendation_engine.get_recommendations: 사용 안 함")
    
    if 'column_based_recommendation_engine.get_recommendations' in content:
        print("  - column_based_recommendation_engine.get_recommendations: 사용 중")
    else:
        print("  - column_based_recommendation_engine.get_recommendations: 사용 안 함")
    
    if 'taste_based_recommendation_engine.get_recommendations' in content:
        print("  - taste_based_recommendation_engine.get_recommendations: 사용 중")
    else:
        print("  - taste_based_recommendation_engine.get_recommendations: 사용 안 함 (새로 만든 엔진)")

# 2. recommendation_engine.py의 주요 메서드 확인
print("\n[2] recommendation_engine.py 주요 메서드:")
with open('api/services/recommendation_engine.py', 'r', encoding='utf-8') as f:
    content = f.read()
    
    methods = [
        'get_recommendations',
        '_filter_products',
        '_score_products',
        '_score_products_by_type',
        'group_products_by_type',
    ]
    
    for method in methods:
        if f'def {method}' in content or f'    def {method}' in content:
            print(f"  - {method}: 존재")
        else:
            print(f"  - {method}: 없음")

# 3. product_type_classifier 사용 여부
print("\n[3] product_type_classifier 사용 여부:")
import subprocess
result = subprocess.run(
    ['grep', '-r', 'product_type_classifier', 'api'],
    capture_output=True,
    text=True,
    shell=True
)
if result.stdout:
    print("  - 사용 중인 파일:")
    for line in result.stdout.strip().split('\n')[:10]:
        if line:
            print(f"    {line[:80]}")
else:
    print("  - 사용 안 함")

# 4. 중복된 로직 확인
print("\n[4] 중복 가능성이 있는 로직:")
print("  - recommendation_engine.py: 제품 타입별 그룹화 및 추천")
print("  - taste_based_recommendation_engine.py: 카테고리별 추천 (새로운 방식)")
print("  - playbook_recommendation_engine.py: Playbook 방식 추천")
print("  - column_based_recommendation_engine.py: 컬럼 기반 추천")

print("\n" + "=" * 80)
print("분석 완료")
print("=" * 80)

