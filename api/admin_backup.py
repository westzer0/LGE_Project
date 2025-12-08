from django.contrib import admin
from .models import (
    Product, ProductSpec, UserSample, OnboardingSession, Reservation, Portfolio, Cart, Wishlist, TasteConfig,
    # ERD 기반 새 모델들
    Member, CartNew, CartItem, Orders, OrderDetail, Payment,
    OnboardingQuestion, OnboardingAnswer, OnboardingUserResponse,
    OnboardingSessionCategories, OnboardingSessionMainSpaces, OnboardingSessionPriorities,
    OnboardSessRecProducts, PortfolioSession, PortfolioProduct,
    Estimate, Consultation, ProductImage, ProductSpecNew, ProductReviewNew,
    ProdDemoFamilyTypes, ProdDemoHouseSizes, ProdDemoHouseTypes,
    TasteCategoryScores, TasteRecommendedProducts,
    UserSamplePurchasedItems, UserSampleRecommendations, CategoryCommonSpec
)

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


# ============================================================
# ERD 기반 새 모델 Admin 등록
# ============================================================

@admin.register(Member)
class MemberAdmin(admin.ModelAdmin):
    list_display = ('member_id', 'name', 'age', 'gender', 'point', 'taste', 'created_date')
    search_fields = ('member_id', 'name', 'contact')
    list_filter = ('gender', 'created_date')


@admin.register(CartNew)
class CartNewAdmin(admin.ModelAdmin):
    list_display = ('cart_id', 'member', 'created_date')
    search_fields = ('member__member_id',)


@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ('cart_item_id', 'cart', 'product', 'quantity')
    search_fields = ('product__product_name',)


@admin.register(Orders)
class OrdersAdmin(admin.ModelAdmin):
    list_display = ('order_id', 'member', 'order_date', 'total_amount', 'order_status', 'payment_status')
    search_fields = ('member__member_id',)
    list_filter = ('order_status', 'payment_status', 'order_date')


@admin.register(OrderDetail)
class OrderDetailAdmin(admin.ModelAdmin):
    list_display = ('detail_id', 'order', 'product', 'quantity')
    search_fields = ('product__product_name',)


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('payment_id', 'order', 'payment_date', 'payment_status', 'method')
    list_filter = ('payment_status', 'method', 'payment_date')


@admin.register(OnboardingQuestion)
class OnboardingQuestionAdmin(admin.ModelAdmin):
    list_display = ('question_code', 'question_text', 'question_type', 'is_required')
    search_fields = ('question_code', 'question_text')
    list_filter = ('question_type', 'is_required')


@admin.register(OnboardingAnswer)
class OnboardingAnswerAdmin(admin.ModelAdmin):
    list_display = ('answer_id', 'question', 'answer_value', 'answer_text')
    search_fields = ('answer_text', 'answer_value')
    list_filter = ('question__question_type',)


@admin.register(OnboardingUserResponse)
class OnboardingUserResponseAdmin(admin.ModelAdmin):
    list_display = ('response_id', 'session', 'question', 'answer', 'input_value')
    search_fields = ('question__question_code',)


@admin.register(TasteConfig)
class TasteConfigAdmin(admin.ModelAdmin):
    list_display = ('taste_id', 'description', 'is_active', 'auto_generated', 'created_at')
    search_fields = ('description',)
    list_filter = ('is_active', 'auto_generated')


@admin.register(TasteCategoryScores)
class TasteCategoryScoresAdmin(admin.ModelAdmin):
    list_display = ('taste', 'category_name', 'score', 'is_recommended', 'is_ill_suited')
    list_filter = ('is_recommended', 'is_ill_suited', 'category_name')


@admin.register(TasteRecommendedProducts)
class TasteRecommendedProductsAdmin(admin.ModelAdmin):
    list_display = ('taste', 'category_name', 'product', 'score', 'rank_order')
    list_filter = ('category_name', 'rank_order')


@admin.register(PortfolioProduct)
class PortfolioProductAdmin(admin.ModelAdmin):
    list_display = ('id', 'portfolio', 'product', 'priority', 'recommend_reason')
    search_fields = ('product__product_name',)


@admin.register(Estimate)
class EstimateAdmin(admin.ModelAdmin):
    list_display = ('estimate_id', 'portfolio', 'total_price', 'discount_price', 'rental_monthly', 'created_date')
    search_fields = ('portfolio__portfolio_id',)


@admin.register(Consultation)
class ConsultationAdmin(admin.ModelAdmin):
    list_display = ('consult_id', 'member', 'portfolio', 'store_name', 'reservation_date', 'created_date')
    search_fields = ('store_name', 'member__member_id')
    list_filter = ('created_date',)


@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):
    list_display = ('product_image_id', 'product', 'image_url')
    search_fields = ('product__product_name',)


@admin.register(ProductSpecNew)
class ProductSpecNewAdmin(admin.ModelAdmin):
    list_display = ('spec_id', 'product', 'spec_key', 'spec_value', 'spec_type')
    search_fields = ('spec_key', 'spec_value')


@admin.register(ProductReviewNew)
class ProductReviewNewAdmin(admin.ModelAdmin):
    list_display = ('product', 'reason_text')
    search_fields = ('product__product_name', 'reason_text')
