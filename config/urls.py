from django.contrib import admin
from django.urls import path
from api.views import (
    index_view, recommend, products, recommend_view,
    onboarding_page,
    onboarding_step_view, onboarding_complete_view, onboarding_session_view
)

urlpatterns = [
    path('', index_view, name='index'),
    path('onboarding/', onboarding_page, name='onboarding_page'),
    path('admin/', admin.site.urls),
    path('api/recommend/', recommend_view, name='recommend'),
    path('api/products/', products, name='products'),
    # 온보딩 API
    path('api/onboarding/step/', onboarding_step_view, name='onboarding_step'),
    path('api/onboarding/complete/', onboarding_complete_view, name='onboarding_complete'),
    path('api/onboarding/session/<str:session_id>/', onboarding_session_view, name='onboarding_session'),
]
