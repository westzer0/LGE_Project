#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import sys
import django

sys.path.insert(0, '.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from api.models import Product

# 가격 문제 확인
zero_price = Product.objects.filter(price=0, is_active=True).count()
null_price = Product.objects.filter(price__isnull=True, is_active=True).count()
total = Product.objects.filter(is_active=True).count()

print(f'가격 0원인 활성 제품: {zero_price}개')
print(f'가격 null인 활성 제품: {null_price}개')
print(f'전체 활성 제품: {total}개')

if zero_price > 0:
    print(f'\n가격 0원인 제품 샘플 (최대 10개):')
    for p in Product.objects.filter(price=0, is_active=True)[:10]:
        print(f'  - ID: {p.id}, 이름: {p.name}, 모델: {p.model_number}, 가격: {p.price}원, 카테고리: {p.category}')

if null_price > 0:
    print(f'\n가격 null인 제품 샘플 (최대 10개):')
    for p in Product.objects.filter(price__isnull=True, is_active=True)[:10]:
        print(f'  - ID: {p.id}, 이름: {p.name}, 모델: {p.model_number}, 가격: {p.price}, 카테고리: {p.category}')

