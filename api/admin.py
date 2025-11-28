from django.contrib import admin
from .models import Product, ProductSpec, UserSample, OnboardingSession

class ProductSpecInline(admin.StackedInline):
    model = ProductSpec
    extra = 0
    fields = ("source", "spec_json", "ingested_at")
    readonly_fields = ("ingested_at",)

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("id", "category", "name", "model_number", "price")
    search_fields = ("name", "model_number")
    list_filter = ("category",)
    inlines = [ProductSpecInline]

@admin.register(UserSample)
class UserSampleAdmin(admin.ModelAdmin):
    list_display = ("user_id", "household_size", "space_type", "budget_range", "created_at")
    search_fields = ("user_id",)
    list_filter = ("household_size", "space_type", "budget_range", "created_at")

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
        'created_at',
    ]
    
    list_filter = ['status', 'priority', 'budget_level', 'created_at']
    search_fields = ['session_id']
    readonly_fields = ['session_id', 'created_at', 'updated_at', 'completed_at']
    
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
            'fields': ('created_at', 'updated_at', 'completed_at'),
            'classes': ('collapse',)
        }),
    )
