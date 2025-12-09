from django.contrib import admin
from .models import Product, ProductSpec, OnboardingSession

class ProductSpecInline(admin.StackedInline):
    model = ProductSpec
    extra = 0
    fields = ("spec_key", "spec_value")
    readonly_fields = ()

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("product_id", "product_name", "main_category", "sub_category")
    search_fields = ("product_name",)
    list_filter = ("main_category",)
    # inlines = [ProductSpecInline]  # ProductSpec에 ForeignKey가 없어서 주석 처리

@admin.register(OnboardingSession)
class OnboardingSessionAdmin(admin.ModelAdmin):
    """OnboardingSession 관리자 페이지"""
    
    list_display = [
        'session_id',
        'vibe',
        'priority',
        'budget_level',
        'status',
        'current_step',
        'created_date',
    ]
    
    list_filter = ['status', 'priority', 'budget_level', 'created_date']
    search_fields = ['session_id']
    readonly_fields = ['session_id', 'created_date', 'updated_date', 'completed_at']
    
    fieldsets = (
        ('세션 정보', {
            'fields': ('session_id', 'status', 'current_step')
        }),
        ('온보딩 답변', {
            'fields': (
                'vibe', 'household_size', 'housing_type', 'pyung',
                'priority', 'budget_level', 'selected_categories'
            )
        }),
        ('추천 결과', {
            'fields': ('recommended_products', 'recommendation_result')
        }),
        ('타임스탬프', {
            'fields': ('created_date', 'updated_date', 'completed_at'),
            'classes': ('collapse',)
        }),
    )

# Reservation 모델이 없어서 주석 처리
# @admin.register(Reservation)
# class ReservationAdmin(admin.ModelAdmin):
#     ...
