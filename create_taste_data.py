#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""새로운 취향 데이터 생성 스크립트"""
import csv
import os
from itertools import product

# 각 단계별 옵션 정의
vibes = ['modern', 'cozy', 'pop', 'luxury']
mates = ['1인', '2인', '3~4인', '5인 이상']
pets = ['yes', 'no']
housing_types = ['apartment', 'officetel', 'detached', 'studio']
pyungs = ['20평 이하', '20~30평', '30평 이상']
laundries = ['weekly', 'few_times', 'daily', 'none']
priorities = ['design', 'performance', 'efficiency', 'value']
budget_levels = ['budget', 'standard', 'premium', 'luxury']

# 모든 조합 생성
print("조합 생성 중...")
all_combinations = list(product(
    vibes, mates, pets, housing_types, pyungs, laundries, priorities, budget_levels
))

total = len(all_combinations)
print(f"총 {total:,}개 조합 생성됨")

# CSV 파일 생성
output_path = 'data/온보딩/taste_recommendations_v2.csv'
os.makedirs(os.path.dirname(output_path), exist_ok=True)

print(f"\nCSV 파일 생성 중: {output_path}")

with open(output_path, 'w', encoding='utf-8-sig', newline='') as f:
    writer = csv.writer(f)
    
    # 헤더 작성
    headers = [
        'taste_id',
        '분위기',
        '메이트_구성',
        '반려동물',
        '주거형태',
        '공간_크기',
        '세탁_주기',
        '우선순위',
        '예산_범위',
        '리뷰_기반_추천문구',
        'AI_기반_추천문구',
    ]
    writer.writerow(headers)
    
    # 데이터 작성
    for idx, combo in enumerate(all_combinations, 1):
        vibe, mate, pet, housing_type, pyung, laundry, priority, budget_level = combo
        
        # taste_id는 1부터 시작
        taste_id = idx
        
        # 추천문구는 나중에 생성 (일단 빈 값)
        review_reason = ''
        ai_reason = ''
        
        writer.writerow([
            taste_id,
            vibe,
            mate,
            pet,
            housing_type,
            pyung,
            laundry,
            priority,
            budget_level,
            review_reason,
            ai_reason,
        ])
        
        if idx % 1000 == 0:
            print(f"  진행 중: {idx:,}/{total:,}...")

print(f"\n[완료] {total:,}개 취향 데이터 생성 완료!")
print(f"[FILE] {output_path}")

# 통계 출력
print(f"\n[통계]")
print(f"  - 분위기: {len(vibes)}개 옵션")
print(f"  - 메이트 구성: {len(mates)}개 옵션")
print(f"  - 반려동물: {len(pets)}개 옵션")
print(f"  - 주거형태: {len(housing_types)}개 옵션")
print(f"  - 공간 크기: {len(pyungs)}개 옵션")
print(f"  - 세탁 주기: {len(laundries)}개 옵션")
print(f"  - 우선순위: {len(priorities)}개 옵션")
print(f"  - 예산 범위: {len(budget_levels)}개 옵션")
print(f"  - 총 조합: {total:,}개")



