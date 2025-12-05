from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from api.views import (
    index_view, recommend, products, recommend_view, product_spec_view, product_image_by_name_view,
    onboarding_page, onboarding_step2_page, onboarding_step3_page, onboarding_step4_page, onboarding_step5_page, onboarding_step6_page, onboarding_step7_page, main_page, onboarding_new_page, result_page,
    fake_lg_main_page, reservation_status_page, other_recommendations_page, mypage,
    onboarding_step_view, onboarding_complete_view, onboarding_session_view,
    portfolio_save_view, portfolio_detail_view, portfolio_list_view, portfolio_share_view,
    ai_recommendation_reason_view, ai_style_message_view, ai_review_summary_view,
    ai_chat_view, ai_status_view,
)
from api.views_drf import convert_figma_to_code

# DRF ViewSet 라우터
# from api.views_drf import RecommendAPIView, PortfolioViewSet, OnboardingSessionViewSet

# router = DefaultRouter()
# router.register(r'portfolios', PortfolioViewSet, basename='portfolio')
# router.register(r'onboarding-sessions', OnboardingSessionViewSet, basename='onboarding-session')

urlpatterns = [
    # 메인 페이지
    path('', main_page, name='main'),
    path('home/', main_page, name='home'),
    path('lge/', fake_lg_main_page, name='fake_lg_main'),  # LG전자 메인페이지 복제
    path('old/', index_view, name='index'),  # 기존 페이지 (백업)
    
    # 온보딩 페이지
    path('onboarding/', onboarding_page, name='onboarding'),
    path('onboarding/step2/', onboarding_step2_page, name='onboarding_step2'),
    path('onboarding/step3/', onboarding_step3_page, name='onboarding_step3'),
    path('onboarding/step4/', onboarding_step4_page, name='onboarding_step4'),
    path('onboarding/step5/', onboarding_step5_page, name='onboarding_step5'),
    path('onboarding/step6/', onboarding_step6_page, name='onboarding_step6'),
    path('onboarding/step7/', onboarding_step7_page, name='onboarding_step7'),
    path('onboarding/old/', onboarding_page, name='onboarding_old'),
    
    # 결과 페이지
    path('result/', result_page, name='result'),
    path('portfolio/<str:portfolio_id>/', result_page, name='portfolio_detail_page'),
    
    # 예약 조회/변경 페이지
    path('reservation/status/', reservation_status_page, name='reservation_status'),
    
    # 다른 추천 후보 확인 페이지
    path('other-recommendations/', other_recommendations_page, name='other_recommendations'),
    
    # 마이페이지
    path('my-page/', mypage, name='mypage'),
    
    # Admin
    path('admin/', admin.site.urls),
    
    # API 엔드포인트 (기존 - 하위 호환성 유지)
    path('api/recommend/', recommend_view, name='recommend'),
    path('api/products/', products, name='products'),
    path('api/products/<int:product_id>/spec/', product_spec_view, name='product_spec'),
    path('api/products/image-by-name/', product_image_by_name_view, name='product_image_by_name'),
    path('api/onboarding/step/', onboarding_step_view, name='onboarding_step'),
    path('api/onboarding/complete/', onboarding_complete_view, name='onboarding_complete'),
    path('api/onboarding/session/<str:session_id>/', onboarding_session_view, name='onboarding_session'),
    
    # 포트폴리오 API (기존 - 하위 호환성 유지)
    path('api/portfolio/save/', portfolio_save_view, name='portfolio_save'),
    path('api/portfolio/list/', portfolio_list_view, name='portfolio_list'),
    path('api/portfolio/<str:portfolio_id>/', portfolio_detail_view, name='portfolio_detail'),
    path('api/portfolio/<str:portfolio_id>/share/', portfolio_share_view, name='portfolio_share'),
    
    # DRF API 엔드포인트 (새로운 방식)
    # path('api/drf/recommend/', RecommendAPIView.as_view(), name='drf_recommend'),
    # path('api/drf/', include(router.urls)),  # /api/drf/portfolios/, /api/drf/onboarding-sessions/
    
    # AI (ChatGPT) API
    path('api/ai/status/', ai_status_view, name='ai_status'),
    path('api/ai/recommendation-reason/', ai_recommendation_reason_view, name='ai_recommendation_reason'),
    path('api/ai/style-message/', ai_style_message_view, name='ai_style_message'),
    path('api/ai/review-summary/', ai_review_summary_view, name='ai_review_summary'),
    path('api/ai/chat/', ai_chat_view, name='ai_chat'),
    
    # Figma 이미지 → 코드 변환 API
    path('api/figma-to-code/', convert_figma_to_code, name='figma_to_code'),
]
