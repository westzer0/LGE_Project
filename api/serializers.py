"""
Django REST Framework Serializers

데이터 검증 및 변환을 위한 Serializer 클래스들
"""
from rest_framework import serializers
from .models import (
    Product, Portfolio, OnboardingSession,
    Member, CartNew, CartItem, Orders, OrderDetail, Payment,
    OnboardingQuestion, OnboardingAnswer, OnboardingUserResponse,
    OnboardingSessionCategories, OnboardingSessionMainSpaces, OnboardingSessionPriorities,
    OnboardSessRecProducts, PortfolioSession, PortfolioProduct,
    Estimate, Consultation, ProductImage, ProductSpecNew, ProductReviewNew,
    ProdDemoFamilyTypes, ProdDemoHouseSizes, ProdDemoHouseTypes,
    TasteCategoryScores, TasteRecommendedProducts,
    UserSamplePurchasedItems, UserSampleRecommendations, CategoryCommonSpec,
    TasteConfig
)


# ============================================================
# 추천 API Serializers
# ============================================================

class RecommendRequestSerializer(serializers.Serializer):
    """추천 요청 데이터 검증"""
    vibe = serializers.ChoiceField(
        choices=['modern', 'cozy', 'natural', 'luxury'],
        required=False,
        default='modern',
        help_text='스타일 (modern/cozy/natural/luxury)'
    )
    household_size = serializers.IntegerField(
        min_value=1,
        max_value=10,
        required=True,
        help_text='가족 인원수 (1-10명)'
    )
    housing_type = serializers.ChoiceField(
        choices=['apartment', 'house', 'officetel'],
        required=False,
        default='apartment',
        help_text='주거 형태'
    )
    pyung = serializers.IntegerField(
        min_value=10,
        max_value=100,
        required=False,
        default=25,
        help_text='평수 (10-100평)'
    )
    priority = serializers.ChoiceField(
        choices=['tech', 'design', 'price', 'value', 'balance'],
        required=False,
        default='value',
        help_text='우선순위'
    )
    budget_level = serializers.ChoiceField(
        choices=['low', 'medium', 'high', 'budget', 'standard', 'premium', 'luxury'],
        required=False,
        default='medium',
        help_text='예산 수준'
    )
    categories = serializers.ListField(
        child=serializers.CharField(),
        allow_empty=False,
        required=True,
        help_text='추천받을 카테고리 리스트'
    )
    main_space = serializers.ChoiceField(
        choices=['living', 'kitchen', 'bedroom'],
        required=False,
        default='living',
        help_text='주 공간'
    )
    space_size = serializers.ChoiceField(
        choices=['small', 'medium', 'large'],
        required=False,
        default='medium',
        help_text='공간 크기'
    )
    has_pet = serializers.BooleanField(
        required=False,
        default=False,
        help_text='반려동물 여부'
    )
    cooking = serializers.ChoiceField(
        choices=['daily', 'sometimes', 'rarely'],
        required=False,
        default='sometimes',
        help_text='요리 빈도'
    )
    laundry = serializers.ChoiceField(
        choices=['daily', 'weekly', 'biweekly'],
        required=False,
        default='weekly',
        help_text='세탁 빈도'
    )
    media = serializers.ChoiceField(
        choices=['frequent', 'balanced', 'rare'],
        required=False,
        default='balanced',
        help_text='미디어 사용 빈도'
    )
    
    def validate_household_size(self, value):
        """가족 인원수 검증"""
        if value < 1 or value > 10:
            raise serializers.ValidationError("가족 인원수는 1명 이상 10명 이하여야 합니다.")
        return value
    
    def validate_categories(self, value):
        """카테고리 검증"""
        if not value:
            raise serializers.ValidationError("최소 1개 이상의 카테고리를 선택해야 합니다.")
        return value


class ProductSerializer(serializers.ModelSerializer):
    """제품 정보 Serializer"""
    class Meta:
        model = Product
        fields = [
            'product_id',
            'model',
            'name',
            'category',
            'price',
            'discount_price',
            'image_url',
            'description',
        ]
        read_only_fields = ['product_id']


class RecommendResponseSerializer(serializers.Serializer):
    """추천 응답 Serializer"""
    success = serializers.BooleanField()
    count = serializers.IntegerField()
    recommendations = serializers.ListField(
        child=serializers.DictField(),
        allow_empty=True
    )
    message = serializers.CharField(required=False, allow_blank=True)


# ============================================================
# 포트폴리오 Serializers
# ============================================================

class PortfolioSerializer(serializers.ModelSerializer):
    """포트폴리오 Serializer"""
    class Meta:
        model = Portfolio
        fields = [
            'portfolio_id',
            'user_id',
            'style_type',
            'style_title',
            'style_subtitle',
            'onboarding_data',
            'products',
            'total_original_price',
            'total_discount_price',
            'match_score',
            'status',
            'share_url',
            'share_count',
            'created_at',
        ]
        read_only_fields = ['portfolio_id', 'created_at', 'share_url', 'share_count']


class PortfolioCreateSerializer(serializers.Serializer):
    """포트폴리오 생성 Serializer"""
    user_id = serializers.CharField(
        max_length=100,
        required=False,
        allow_blank=True,
        help_text='사용자 ID (선택사항)'
    )
    style_type = serializers.ChoiceField(
        choices=['modern', 'cozy', 'natural', 'luxury'],
        required=True,
        help_text='스타일 유형'
    )
    style_title = serializers.CharField(
        max_length=200,
        required=False,
        allow_blank=True,
        help_text='스타일 타이틀'
    )
    style_subtitle = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text='스타일 설명'
    )
    onboarding_data = serializers.DictField(
        required=False,
        allow_empty=True,
        help_text='온보딩 데이터'
    )
    products = serializers.ListField(
        child=serializers.DictField(),
        required=True,
        allow_empty=False,
        help_text='추천 제품 리스트'
    )
    match_score = serializers.FloatField(
        min_value=0,
        max_value=100,
        required=False,
        default=0,
        help_text='매칭 점수'
    )


# ============================================================
# 온보딩 Serializers
# ============================================================

class OnboardingSessionSerializer(serializers.ModelSerializer):
    """온보딩 세션 Serializer (정규화 테이블 사용)"""
    main_spaces = serializers.SerializerMethodField()
    priorities = serializers.SerializerMethodField()
    selected_categories = serializers.SerializerMethodField()
    recommended_products = serializers.SerializerMethodField()
    
    class Meta:
        model = OnboardingSession
        fields = [
            'session_id',
            'session_uuid',
            'member',
            'current_step',
            'status',
            'vibe',
            'household_size',
            'housing_type',
            'pyung',
            'priority',
            'budget_level',
            'has_pet',
            'cooking',
            'laundry',
            'media',
            'main_spaces',
            'priorities',
            'selected_categories',
            'recommended_products',
            'created_at',
            'completed_at',
        ]
        read_only_fields = ['session_id', 'session_uuid', 'created_at', 'completed_at']
    
    def get_main_spaces(self, obj):
        """정규화 테이블에서 main_spaces 읽기"""
        try:
            from api.services.onboarding_db_service import onboarding_db_service
            session_data = onboarding_db_service.get_session(obj.session_id)
            if session_data and 'MAIN_SPACE' in session_data:
                import json
                main_space_str = session_data['MAIN_SPACE']
                if main_space_str:
                    return json.loads(main_space_str) if isinstance(main_space_str, str) else main_space_str
        except:
            pass
        return []
    
    def get_priorities(self, obj):
        """정규화 테이블에서 priorities 읽기"""
        try:
            from api.services.onboarding_db_service import onboarding_db_service
            session_data = onboarding_db_service.get_session(obj.session_id)
            if session_data and 'PRIORITY_LIST' in session_data:
                import json
                priority_str = session_data['PRIORITY_LIST']
                if priority_str:
                    return json.loads(priority_str) if isinstance(priority_str, str) else priority_str
        except:
            pass
        return []
    
    def get_selected_categories(self, obj):
        """정규화 테이블에서 selected_categories 읽기"""
        try:
            from api.services.onboarding_db_service import onboarding_db_service
            session_data = onboarding_db_service.get_session(obj.session_id)
            if session_data and 'SELECTED_CATEGORIES' in session_data:
                return session_data['SELECTED_CATEGORIES']
        except:
            pass
        return []
    
    def get_recommended_products(self, obj):
        """정규화 테이블에서 recommended_products 읽기"""
        try:
            from api.services.onboarding_db_service import onboarding_db_service
            session_data = onboarding_db_service.get_session(obj.session_id)
            if session_data and 'RECOMMENDED_PRODUCTS' in session_data:
                return session_data['RECOMMENDED_PRODUCTS']
        except:
            pass
        return []


# ============================================================
# ERD 기반 추가 Serializers
# ============================================================

class MemberSerializer(serializers.ModelSerializer):
    """회원 Serializer"""
    class Meta:
        model = Member
        fields = [
            'member_id', 'name', 'age', 'gender', 'contact',
            'point', 'created_at', 'taste'
        ]
        read_only_fields = ['member_id', 'created_at']
        extra_kwargs = {'password': {'write_only': True}}


class CartSerializer(serializers.ModelSerializer):
    """장바구니 Serializer"""
    items = serializers.SerializerMethodField()
    
    class Meta:
        model = CartNew
        fields = ['cart_id', 'member', 'created_at', 'items']
        read_only_fields = ['cart_id', 'created_at']
    
    def get_items(self, obj):
        return CartItemSerializer(obj.items.all(), many=True).data


class CartItemSerializer(serializers.ModelSerializer):
    """장바구니 항목 Serializer"""
    product_name = serializers.CharField(source='product.product_name', read_only=True)
    product_price = serializers.DecimalField(source='product.price', max_digits=12, decimal_places=0, read_only=True)
    
    class Meta:
        model = CartItem
        fields = ['cart_item_id', 'cart', 'product', 'product_name', 'product_price', 'quantity']
        read_only_fields = ['cart_item_id']


class OrderSerializer(serializers.ModelSerializer):
    """주문 Serializer"""
    details = serializers.SerializerMethodField()
    
    class Meta:
        model = Orders
        fields = [
            'order_id', 'member', 'order_date', 'total_amount',
            'order_status', 'payment_status', 'details'
        ]
        read_only_fields = ['order_id', 'order_date']
    
    def get_details(self, obj):
        return OrderDetailSerializer(obj.details.all(), many=True).data


class OrderDetailSerializer(serializers.ModelSerializer):
    """주문 상세 Serializer"""
    product_name = serializers.CharField(source='product.product_name', read_only=True)
    
    class Meta:
        model = OrderDetail
        fields = ['detail_id', 'order', 'product', 'product_name', 'quantity']
        read_only_fields = ['detail_id']


class PaymentSerializer(serializers.ModelSerializer):
    """결제 Serializer"""
    class Meta:
        model = Payment
        fields = [
            'payment_id', 'payment_date', 'order', 'payment_status', 'method'
        ]
        read_only_fields = ['payment_id', 'payment_date']


class OnboardingQuestionSerializer(serializers.ModelSerializer):
    """온보딩 질문 Serializer"""
    answers = serializers.SerializerMethodField()
    
    class Meta:
        model = OnboardingQuestion
        fields = [
            'question_code', 'question_text', 'question_type',
            'is_required', 'created_at', 'answers'
        ]
        read_only_fields = ['created_at']
    
    def get_answers(self, obj):
        return OnboardingAnswerSerializer(obj.answers.all(), many=True).data


class OnboardingAnswerSerializer(serializers.ModelSerializer):
    """온보딩 답변 선택지 Serializer"""
    class Meta:
        model = OnboardingAnswer
        fields = ['answer_id', 'question', 'answer_value', 'answer_text', 'created_at']
        read_only_fields = ['answer_id', 'created_at']


class OnboardingUserResponseSerializer(serializers.ModelSerializer):
    """온보딩 사용자 응답 Serializer"""
    class Meta:
        model = OnboardingUserResponse
        fields = [
            'response_id', 'session', 'question', 'answer', 'input_value', 'created_at'
        ]
        read_only_fields = ['response_id', 'created_at']


class TasteConfigSerializer(serializers.ModelSerializer):
    """Taste 설정 Serializer"""
    category_scores = serializers.SerializerMethodField()
    recommended_products_list = serializers.SerializerMethodField()
    
    class Meta:
        model = TasteConfig
        fields = [
            'taste_id', 'description', 'representative_vibe',
            'representative_household_size', 'representative_main_space',
            'representative_has_pet', 'representative_priority',
            'representative_budget_level', 'recommended_categories',
            'recommended_categories_with_scores', 'ill_suited_categories',
            'recommended_products', 'is_active', 'auto_generated',
            'last_simulation_date', 'created_at', 'updated_at',
            'category_scores', 'recommended_products_list'
        ]
        read_only_fields = ['taste_id', 'created_at', 'updated_at']
    
    def get_category_scores(self, obj):
        return TasteCategoryScoresSerializer(obj.category_scores.all(), many=True).data
    
    def get_recommended_products_list(self, obj):
        return TasteRecommendedProductsSerializer(obj.recommended_products_new.all(), many=True).data


class TasteCategoryScoresSerializer(serializers.ModelSerializer):
    """Taste 카테고리 점수 Serializer"""
    class Meta:
        model = TasteCategoryScores
        fields = [
            'taste', 'category_name', 'score', 'is_recommended',
            'is_ill_suited', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']


class TasteRecommendedProductsSerializer(serializers.ModelSerializer):
    """Taste 추천 제품 Serializer"""
    product_name = serializers.CharField(source='product.product_name', read_only=True)
    
    class Meta:
        model = TasteRecommendedProducts
        fields = [
            'taste', 'category_name', 'product', 'product_name',
            'score', 'rank_order', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']


class PortfolioProductSerializer(serializers.ModelSerializer):
    """포트폴리오 제품 Serializer"""
    product_name = serializers.CharField(source='product.product_name', read_only=True)
    
    class Meta:
        model = PortfolioProduct
        fields = ['id', 'portfolio', 'product', 'product_name', 'recommend_reason', 'priority']


class EstimateSerializer(serializers.ModelSerializer):
    """견적 Serializer"""
    class Meta:
        model = Estimate
        fields = [
            'estimate_id', 'portfolio', 'total_price', 'discount_price',
            'rental_monthly', 'created_at'
        ]
        read_only_fields = ['estimate_id', 'created_at']


class ConsultationSerializer(serializers.ModelSerializer):
    """상담 Serializer"""
    class Meta:
        model = Consultation
        fields = [
            'consult_id', 'member', 'portfolio', 'store_name',
            'reservation_date', 'created_at'
        ]
        read_only_fields = ['consult_id', 'created_at']


class ProductImageSerializer(serializers.ModelSerializer):
    """제품 이미지 Serializer"""
    class Meta:
        model = ProductImage
        fields = ['product_image_id', 'product', 'image_url']


class ProductSpecNewSerializer(serializers.ModelSerializer):
    """제품 스펙 Serializer (ERD)"""
    class Meta:
        model = ProductSpecNew
        fields = ['spec_id', 'product', 'spec_key', 'spec_value', 'spec_type']


class ProductReviewNewSerializer(serializers.ModelSerializer):
    """제품 리뷰 Serializer (ERD)"""
    class Meta:
        model = ProductReviewNew
        fields = [
            'product', 'review_vector', 'family_list',
            'size_list', 'house_list', 'reason_text'
        ]

