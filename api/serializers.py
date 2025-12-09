"""
Django REST Framework Serializers

데이터 검증 및 변환을 위한 Serializer 클래스들
"""
from rest_framework import serializers
from .models import Product, PortfolioSession as Portfolio, OnboardingSession


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
    """온보딩 세션 Serializer"""
    class Meta:
        model = OnboardingSession
        fields = [
            'session_id',
            'current_step',
            'status',
            'vibe',
            'household_size',
            'housing_type',
            'pyung',
            'priority',
            'budget_level',
            'selected_categories',
            'has_pet',
            'created_at',
            'completed_at',
        ]
        read_only_fields = ['session_id', 'created_at', 'completed_at']

