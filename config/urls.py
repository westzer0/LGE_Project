from django.contrib import admin
from django.urls import path
from api.views import (
    index_view, recommend, products, recommend_view,
    onboarding_page, main_page, onboarding_new_page, result_page,
    onboarding_step_view, onboarding_complete_view, onboarding_session_view,
    portfolio_save_view, portfolio_detail_view, portfolio_list_view, portfolio_share_view,
    ai_recommendation_reason_view, ai_style_message_view, ai_review_summary_view,
    ai_chat_view, ai_status_view,
)

urlpatterns = [
    # 메인 페이지
    path('', main_page, name='main'),
    path('home/', main_page, name='home'),
    path('old/', index_view, name='index'),  # 기존 페이지 (백업)
    
    # 온보딩 페이지
    path('onboarding/', onboarding_new_page, name='onboarding'),
    path('onboarding/old/', onboarding_page, name='onboarding_old'),
    
    # 결과 페이지
    path('result/', result_page, name='result'),
    path('portfolio/<str:portfolio_id>/', result_page, name='portfolio_detail_page'),
    
    # Admin
    path('admin/', admin.site.urls),
    
    # API 엔드포인트
    path('api/recommend/', recommend_view, name='recommend'),
    path('api/products/', products, name='products'),
    path('api/onboarding/step/', onboarding_step_view, name='onboarding_step'),
    path('api/onboarding/complete/', onboarding_complete_view, name='onboarding_complete'),
    path('api/onboarding/session/<str:session_id>/', onboarding_session_view, name='onboarding_session'),
    
    # 포트폴리오 API
    path('api/portfolio/save/', portfolio_save_view, name='portfolio_save'),
    path('api/portfolio/list/', portfolio_list_view, name='portfolio_list'),
    path('api/portfolio/<str:portfolio_id>/', portfolio_detail_view, name='portfolio_detail'),
    path('api/portfolio/<str:portfolio_id>/share/', portfolio_share_view, name='portfolio_share'),
    
    # AI (ChatGPT) API
    path('api/ai/status/', ai_status_view, name='ai_status'),
    path('api/ai/recommendation-reason/', ai_recommendation_reason_view, name='ai_recommendation_reason'),
    path('api/ai/style-message/', ai_style_message_view, name='ai_style_message'),
    path('api/ai/review-summary/', ai_review_summary_view, name='ai_review_summary'),
    path('api/ai/chat/', ai_chat_view, name='ai_chat'),
]
