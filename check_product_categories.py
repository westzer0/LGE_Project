#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import sys
import django

sys.path.insert(0, '.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from api.models import Product
from django.db.models import Count

# PRODUCT 테이블의 MAIN_CATEGORY 목록
categories = Product.objects.values_list('category', flat=True).distinct()
print('PRODUCT 테이블의 MAIN_CATEGORY 목록:')
for cat in sorted(categories):
    print(f'  - {cat}')

print(f'\n총 {len(categories)}개 카테고리')

# 카테고리별 제품 수
print('\n카테고리별 제품 수:')
counts = Product.objects.values('category').annotate(count=Count('id')).order_by('-count')
for item in counts:
    print(f'  - {item["category"]}: {item["count"]}개')

# 활성 제품만
print('\n활성 제품만 (is_active=True):')
active_counts = Product.objects.filter(is_active=True).values('category').annotate(count=Count('id')).order_by('-count')
for item in active_counts:
    print(f'  - {item["category"]}: {item["count"]}개')

