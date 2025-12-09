from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from api.views import (
    index_view, recommend, products, recommend_view, product_spec_view, product_image_by_name_view, product_reviews_view,
    product_recommend_reason_view, product_demographics_view,
    onboarding_page, onboarding_step2_page, onboarding_step3_page, onboarding_step4_page, onboarding_step5_page, onboarding_step6_page, onboarding_step7_page, main_page, onboarding_new_page, result_page,
    fake_lg_main_page, react_app_view, health_check_view, oracle_test_view,reservation_status_page, other_recommendations_page, mypage,
    onboarding_step_view, onboarding_complete_view, onboarding_session_view,
    portfolio_save_view, portfolio_detail_view, portfolio_list_view, portfolio_share_view,
    portfolio_refresh_view, portfolio_alternatives_view, portfolio_add_to_cart_view,
    portfolio_edit_view, portfolio_estimate_view,
    bestshop_consultation_view,
    ai_recommendation_reason_view, ai_style_message_view, ai_review_summary_view,
    ai_chat_view, ai_status_view, ai_natural_recommend_view, ai_chat_recommend_view, ai_product_compare_view,
    cart_add_view, cart_remove_view, cart_list_view,
    product_detail_page,
    search_view, product_compare_view,
    wishlist_add_view, wishlist_remove_view, wishlist_list_view,
    reservation_list_view, reservation_detail_view, reservation_update_view, reservation_cancel_view,
    other_recommendations_page, mypage, reservation_status_page,
    kakao_login_view, kakao_callback_view, kakao_logout_view, kakao_user_info_view, kakao_send_message_view,
)
from api.views_drf import convert_figma_to_code
from api.views_auth import kakao_login_view as jwt_kakao_login_view, jwt_refresh_view, jwt_me_view
from api.views_recommendations import taste_recommendations_view, portfolio_generate_view

# DRF ViewSet ?�우??
from api.viewsets_erd import (
    MemberViewSet, CartViewSet, CartItemViewSet,
    OrderViewSet, OrderDetailViewSet, PaymentViewSet,
    OnboardingQuestionViewSet, OnboardingAnswerViewSet, OnboardingUserResponseViewSet,
    TasteConfigViewSet, TasteCategoryScoresViewSet, TasteRecommendedProductsViewSet,
    PortfolioProductViewSet, EstimateViewSet, ConsultationViewSet,
    ProductImageViewSet, ProductSpecNewViewSet, ProductReviewNewViewSet
)

# ERD 기반 ViewSet ?�우??
router = DefaultRouter()
router.register(r'members', MemberViewSet, basename='member')
router.register(r'carts', CartViewSet, basename='cart')
router.register(r'cart-items', CartItemViewSet, basename='cart-item')
router.register(r'orders', OrderViewSet, basename='order')
router.register(r'order-details', OrderDetailViewSet, basename='order-detail')
router.register(r'payments', PaymentViewSet, basename='payment')
router.register(r'onboarding-questions', OnboardingQuestionViewSet, basename='onboarding-question')
router.register(r'onboarding-answers', OnboardingAnswerViewSet, basename='onboarding-answer')
router.register(r'onboarding-user-responses', OnboardingUserResponseViewSet, basename='onboarding-user-response')
router.register(r'taste-configs', TasteConfigViewSet, basename='taste-config')
router.register(r'taste-category-scores', TasteCategoryScoresViewSet, basename='taste-category-score')
router.register(r'taste-recommended-products', TasteRecommendedProductsViewSet, basename='taste-recommended-product')
router.register(r'portfolio-products', PortfolioProductViewSet, basename='portfolio-product')
router.register(r'estimates', EstimateViewSet, basename='estimate')
router.register(r'consultations', ConsultationViewSet, basename='consultation')
router.register(r'product-images', ProductImageViewSet, basename='product-image')
router.register(r'product-specs', ProductSpecNewViewSet, basename='product-spec')
router.register(r'product-reviews', ProductReviewNewViewSet, basename='product-review')

urlpatterns = [
    # 메인 ?�이지 (루트 경로)
    path('', main_page, name='main'),
    
    # React ??(백업??
    path('app/', react_app_view, name='react_app'),
    path('react/', react_app_view, name='react_app_alt'),
    
    # 기존 메인 ?�이지 (별칭)
    path('main/', main_page, name='main_alt'),
    path('home/', main_page, name='home'),
    path('lge/', fake_lg_main_page, name='fake_lg_main'),  # LG?�자 메인?�이지 복제
    path('old/', index_view, name='index'),  # 기존 ?�이지 (백업)
    
    # ?�보???�이지
    path('onboarding/', onboarding_page, name='onboarding'),
    path('onboarding/step2/', onboarding_step2_page, name='onboarding_step2'),
    path('onboarding/step3/', onboarding_step3_page, name='onboarding_step3'),
    path('onboarding/step4/', onboarding_step4_page, name='onboarding_step4'),
    path('onboarding/step5/', onboarding_step5_page, name='onboarding_step5'),
    path('onboarding/step6/', onboarding_step6_page, name='onboarding_step6'),
    path('onboarding/step7/', onboarding_step7_page, name='onboarding_step7'),
    # path('onboarding/old/', onboarding_page, name='onboarding_old'),
    path('api/onboarding/complete/', onboarding_complete_view, name='onboarding-complete'),
    
    # 결과 ?�이지
    path('result/', result_page, name='result'),
    path('portfolio/<str:portfolio_id>/', result_page, name='portfolio_detail_page'),
    
    # ?�론?�엔???�이지
    path('other-recommendations/', other_recommendations_page, name='other_recommendations'),
    path('my-page/', mypage, name='mypage'),
    path('reservation-status/', reservation_status_page, name='reservation_status'),
    
    # ?�품 ?�세 ?�이지
    path('products/<int:product_id>/', product_detail_page, name='product_detail'),
    
    # Admin
    path('admin/', admin.site.urls),
    
    # ?�스체크 ?�드?�인??
    path('api/health/', health_check_view, name='health_check'),
    
    # Oracle DB ?�스???�드?�인??
    path('api/oracle/test/', oracle_test_view, name='oracle_test'),
    
    # API ?�드?�인??
    path('api/recommend/', recommend_view, name='recommend'),
    path('api/products/', products, name='products'),
    path('api/products/<int:product_id>/spec/', product_spec_view, name='product_spec'),
    path('api/products/<int:product_id>/reviews/', product_reviews_view, name='product_reviews'),  # LGDX-40
    path('api/products/<int:product_id>/recommend-reason/', product_recommend_reason_view, name='product_recommend_reason'),
    path('api/products/<int:product_id>/demographics/', product_demographics_view, name='product_demographics'),
    path('api/products/image-by-name/', product_image_by_name_view, name='product_image_by_name'),
    path('api/onboarding/step/', onboarding_step_view, name='onboarding_step'),
    path('api/onboarding/complete/', onboarding_complete_view, name='onboarding_complete'),
    path('api/onboarding/session/<str:session_id>/', onboarding_session_view, name='onboarding_session'),
    
    # ?�트?�리??API (기존 - ?�위 ?�환???��?)
    path('api/portfolio/save/', portfolio_save_view, name='portfolio_save'),
    path('api/portfolio/list/', portfolio_list_view, name='portfolio_list'),
    path('api/portfolio/<str:portfolio_id>/', portfolio_detail_view, name='portfolio_detail'),
    path('api/portfolio/<str:portfolio_id>/share/', portfolio_share_view, name='portfolio_share'),
    path('api/portfolio/<str:portfolio_id>/refresh/', portfolio_refresh_view, name='portfolio_refresh'),  # PRD: 2-4
    path('api/portfolio/<str:portfolio_id>/alternatives/', portfolio_alternatives_view, name='portfolio_alternatives'),  # PRD: 2-6
    path('api/portfolio/<str:portfolio_id>/add-to-cart/', portfolio_add_to_cart_view, name='portfolio_add_to_cart'),  # PRD: 2-3
    path('api/portfolio/<str:portfolio_id>/edit/', portfolio_edit_view, name='portfolio_edit'),  # ?�트?�리???�집
    path('api/portfolio/<str:portfolio_id>/estimate/', portfolio_estimate_view, name='portfolio_estimate'),  # ?�시�?견적 계산
    
    # 베스?�샵 ?�담 ?�약 API
    path('api/bestshop/consultation/', bestshop_consultation_view, name='bestshop_consultation'),  # PRD: 2-5
    
    # ?�약 조회/변�?API - PRD ?�구?�항
    path('api/reservation/list/', reservation_list_view, name='reservation_list'),
    path('api/reservation/<str:reservation_id>/', reservation_detail_view, name='reservation_detail'),
    path('api/reservation/<str:reservation_id>/update/', reservation_update_view, name='reservation_update'),
    path('api/reservation/<str:reservation_id>/cancel/', reservation_cancel_view, name='reservation_cancel'),
    
    # ?�바구니 API - LGDX-12
    path('api/cart/add/', cart_add_view, name='cart_add'),
    path('api/cart/remove/', cart_remove_view, name='cart_remove'),
    path('api/cart/list/', cart_list_view, name='cart_list'),
    
    # 검??API
    path('api/search/', search_view, name='search'),
    
    # ?�품 비교 API
    path('api/products/compare/', product_compare_view, name='product_compare'),
    
    # 찜하�??�시리스??API
    path('api/wishlist/add/', wishlist_add_view, name='wishlist_add'),
    path('api/wishlist/remove/', wishlist_remove_view, name='wishlist_remove'),
    path('api/wishlist/list/', wishlist_list_view, name='wishlist_list'),
    
    # DRF API ?�드?�인??(ERD 기반 ?�전??REST API)
    path('api/v1/', include(router.urls)),  # /api/v1/members/, /api/v1/carts/, etc.
    
    # AI (ChatGPT) API
    path('api/ai/status/', ai_status_view, name='ai_status'),
    path('api/ai/recommendation-reason/', ai_recommendation_reason_view, name='ai_recommendation_reason'),
    path('api/ai/style-message/', ai_style_message_view, name='ai_style_message'),
    path('api/ai/review-summary/', ai_review_summary_view, name='ai_review_summary'),
    path('api/ai/chat/', ai_chat_view, name='ai_chat'),
    path('api/ai/natural-recommend/', ai_natural_recommend_view, name='ai_natural_recommend'),
    path('api/ai/chat-recommend/', ai_chat_recommend_view, name='ai_chat_recommend'),
    path('api/ai/product-compare/', ai_product_compare_view, name='ai_product_compare'),
    
    # 카카???�증 API (기존 - ?�위 ?�환??
    path('api/auth/kakao/login/', kakao_login_view, name='kakao_login'),
    path('api/auth/kakao/callback/', kakao_callback_view, name='kakao_callback'),
    path('api/auth/kakao/logout/', kakao_logout_view, name='kakao_logout'),
    path('api/auth/kakao/user/', kakao_user_info_view, name='kakao_user_info'),
    
    # JWT + Kakao OAuth API (?�로??REST API)
    path('api/v1/auth/kakao/', jwt_kakao_login_view, name='jwt_kakao_login'),
    path('api/v1/auth/refresh/', jwt_refresh_view, name='jwt_refresh'),
    path('api/v1/auth/me/', jwt_me_view, name='jwt_me'),
    
    # 추천 ?�진 API
    path('api/v1/onboarding/complete/', onboarding_complete_view, name='onboarding_complete'),
    path('api/v1/recommendations/taste/<int:taste_id>/', taste_recommendations_view, name='taste_recommendations'),
    path('api/v1/portfolio/generate/', portfolio_generate_view, name='portfolio_generate'),
    
    # 카카??메시지 API
    path('api/kakao/send-message/', kakao_send_message_view, name='kakao_send_message'),
    
    # Figma ?��?지 ??코드 변??API
    path('api/figma-to-code/', convert_figma_to_code, name='figma_to_code'),
]
