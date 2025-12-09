"""엑셀 매칭 테스트"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from api.services.style_analyzer import StyleAnalyzer
from api.services.style_analysis_service import StyleAnalysisService

# 사용자 온보딩 답변
user_answers = {
    'q1_vibe': '모던 & 미니멀 (Modern & Minimal): 화이트/블랙 톤의 깔끔한 공간을 선호',
    'q2_mate': '2인 (커플/부부)',
    'q2_1_pet': '아니오',
    'q3_housing': '단독주택',
    'q3_1_space': '거실, 주방, 드레스룸',
    'q3_2_size': '6평',
    'q4_priority': 'AI/스마트 기능'
}

print("=" * 60)
print("엑셀 매칭 테스트")
print("=" * 60)

# StyleAnalyzer 직접 테스트
analyzer = StyleAnalyzer()
result = analyzer.get_result_message(user_answers)
print(f"\n[StyleAnalyzer 직접 테스트]")
print(f"매칭된 메시지: {result[:200] if result else '없음'}...")

# StyleAnalysisService를 통한 테스트
onboarding_data = {
    'vibe': 'modern',
    'household_size': 2,
    'housing_type': 'house',
    'pyung': 6,
    'priority': 'tech',
    'budget_level': 'medium',
    'has_pet': False,
    'cooking': 'sometimes',
    'laundry': 'weekly',
    'media': 'balanced',
    'main_space': ['living', 'kitchen', 'dressing']
}

print(f"\n[StyleAnalysisService 통합 테스트]")
style_analysis = StyleAnalysisService.generate_style_analysis(onboarding_data, {})
print(f"Title: {style_analysis.get('title')}")
print(f"Subtitle: {style_analysis.get('subtitle', '')[:200]}...")
print(f"Style Analysis Message: {style_analysis.get('style_analysis_message', '')[:200] if style_analysis.get('style_analysis_message') else '없음'}...")

