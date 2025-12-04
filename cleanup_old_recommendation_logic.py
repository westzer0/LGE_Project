#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
기존 recommendation_engine.py의 제품 타입별 로직 정리

사용자가 원하는 새로운 로직 (MAIN CATEGORY별 추천)으로 완전히 교체하기 전에
기존 코드를 정리합니다.
"""
import os
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

print("=" * 80)
print("기존 추천 로직 정리 계획")
print("=" * 80)

print("\n[삭제 대상]")
print("1. api/utils/product_type_classifier.py")
print("   - recommendation_engine에서만 사용")
print("   - 새로운 taste_based_recommendation_engine에서는 사용 안 함")
print("   - 제품 타입별 세분화 로직 (세탁기, 냉장고 등)")

print("\n[수정 대상]")
print("1. api/services/recommendation_engine.py")
print("   - 제품 타입별 그룹화 로직 제거")
print("   - _score_products_by_type() 메서드 삭제")
print("   - _get_product_type_multiplier() 메서드 삭제")
print("   - get_recommendations()의 제품 타입별 로직을 MAIN CATEGORY별로 변경")
print("   - 또는 taste_based_recommendation_engine을 사용하도록 변경")

print("\n2. api/views.py")
print("   - recommendation_engine → taste_based_recommendation_engine으로 교체")
print("   - taste_id를 전달하도록 수정")

print("\n[보관 대상]")
print("1. playbook_recommendation_engine.py")
print("   - views.py에서 사용 중이므로 유지")

print("2. column_based_recommendation_engine.py")
print("   - views.py에서 사용 중이므로 유지")

print("\n" + "=" * 80)
print("정리 계획 수립 완료")
print("=" * 80)
print("\n실제 삭제/수정을 진행하시겠습니까?")
print("(이 스크립트는 계획만 보여줍니다)")

