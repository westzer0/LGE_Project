"""스타일 분석 서비스 통합 테스트"""
import os
import django

# Django 설정
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from api.services.style_analysis_service import StyleAnalysisService

# 테스트 데이터
test_data = {
    'vibe': 'modern',
    'household_size': 2,
    'housing_type': 'apartment',
    'pyung': 30,
    'priority': 'design',
    'budget_level': 'medium',
    'has_pet': False,
    'cooking': 'sometimes',
    'laundry': 'weekly',
    'media': 'balanced',
    'main_space': 'living'
}

print("=" * 60)
print("스타일 분석 서비스 통합 테스트")
print("=" * 60)

result = StyleAnalysisService.generate_style_analysis(test_data, {})

print("\n[결과]")
print(f"Title: {result.get('title')}")
print(f"Subtitle: {result.get('subtitle', '')[:150]}...")
if result.get('style_analysis_message'):
    print(f"Style Analysis Message: {result.get('style_analysis_message')[:150]}...")
if result.get('style_name'):
    print(f"Style Name: {result.get('style_name')}")
print(f"Style Type: {result.get('style_type')}")

