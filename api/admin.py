from django.contrib import admin
from .models import Product, ProductSpec, UserSample, OnboardingSession, Reservation

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

@admin.register(Reservation)
class ReservationAdmin(admin.ModelAdmin):
    """Reservation 관리자 페이지"""
    
    list_display = [
        'reservation_id',
        'user_id',
        'status',
        'consultation_purpose',
        'preferred_date',
        'preferred_time',
        'store_location',
        'created_at',
    ]
    
    list_filter = ['status', 'consultation_purpose', 'store_location', 'created_at']
    search_fields = ['reservation_id', 'user_id', 'contact_name', 'contact_phone', 'contact_email']
    readonly_fields = ['reservation_id', 'created_at', 'updated_at', 'confirmed_at', 'cancelled_at']
    
    fieldsets = (
        ('예약 정보', {
            'fields': ('reservation_id', 'user_id', 'status', 'portfolio')
        }),
        ('상담 정보', {
            'fields': (
                'consultation_purpose',
                'preferred_date', 'preferred_time',
                'store_location'
            )
        }),
        ('연락처 정보', {
            'fields': ('contact_name', 'contact_phone', 'contact_email', 'memo')
        }),
        ('외부 시스템 연동', {
            'fields': ('external_reservation_id', 'external_system_url'),
            'classes': ('collapse',)
        }),
        ('타임스탬프', {
            'fields': ('created_at', 'updated_at', 'confirmed_at', 'cancelled_at'),
            'classes': ('collapse',)
        }),
    )
