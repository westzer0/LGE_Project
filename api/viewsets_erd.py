"""
ERD 기반 Django REST Framework ViewSets

34개 테이블에 대한 완전한 CRUD API 제공
"""
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.shortcuts import get_object_or_404
from django.utils import timezone
from .models import (
    Member, CartNew, CartItem, Orders, OrderDetail, Payment,
    OnboardingQuestion, OnboardingAnswer, OnboardingUserResponse,
    OnboardingSessionCategories, OnboardingSessionMainSpaces, OnboardingSessionPriorities,
    OnboardSessRecProducts, PortfolioSession, PortfolioProduct,
    Estimate, Consultation, ProductImage, ProductSpecNew, ProductReviewNew,
    ProdDemoFamilyTypes, ProdDemoHouseSizes, ProdDemoHouseTypes,
    TasteCategoryScores, TasteRecommendedProducts,
    UserSamplePurchasedItems, UserSampleRecommendations, CategoryCommonSpec,
    TasteConfig, Product, OnboardingSession, Portfolio
)
from .serializers import (
    MemberSerializer, CartSerializer, CartItemSerializer,
    OrderSerializer, OrderDetailSerializer, PaymentSerializer,
    OnboardingQuestionSerializer, OnboardingAnswerSerializer, OnboardingUserResponseSerializer,
    TasteConfigSerializer, TasteCategoryScoresSerializer, TasteRecommendedProductsSerializer,
    PortfolioProductSerializer, EstimateSerializer, ConsultationSerializer,
    ProductImageSerializer, ProductSpecNewSerializer, ProductReviewNewSerializer
)


# ============================================================
# 회원/인증 ViewSets
# ============================================================

class MemberViewSet(viewsets.ModelViewSet):
    """
    회원 관리 ViewSet
    GET /api/v1/members/ - 회원 목록 (인증 불필요)
    POST /api/v1/members/ - 회원 가입 (인증 불필요)
    GET /api/v1/members/{id}/ - 회원 상세 (인증 불필요)
    PUT /api/v1/members/{id}/ - 회원 수정 (인증 필요)
    DELETE /api/v1/members/{id}/ - 회원 삭제 (인증 필요)
    """
    queryset = Member.objects.all()
    serializer_class = MemberSerializer
    # IsAuthenticatedOrReadOnly: 읽기는 모두 허용, 쓰기는 인증 필요 (settings.py 기본값)
    
    @action(detail=False, methods=['post'])
    def kakao_login(self, request):
        """
        카카오 로그인
        POST /api/members/kakao_login/
        """
        kakao_id = request.data.get('kakao_id')
        if not kakao_id:
            return Response(
                {'error': 'kakao_id가 필요합니다.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # 카카오 ID로 회원 조회 또는 생성
        member, created = Member.objects.get_or_create(
            member_id=kakao_id,
            defaults={
                'name': request.data.get('name', ''),
                'password': '',  # 카카오 로그인은 비밀번호 없음
            }
        )
        
        serializer = self.get_serializer(member)
        return Response({
            'success': True,
            'member': serializer.data,
            'created': created
        })


# ============================================================
# 장바구니 ViewSets
# ============================================================

class CartViewSet(viewsets.ModelViewSet):
    """
    장바구니 관리 ViewSet
    """
    queryset = CartNew.objects.all()
    serializer_class = CartSerializer
    # IsAuthenticatedOrReadOnly: 읽기는 모두 허용, 쓰기는 인증 필요 (settings.py 기본값)
    
    @action(detail=True, methods=['post'])
    def add_item(self, request, pk=None):
        """
        장바구니에 제품 추가
        POST /api/carts/{id}/add_item/
        """
        cart = self.get_object()
        product_id = request.data.get('product_id')
        quantity = request.data.get('quantity', 1)
        
        if not product_id:
            return Response(
                {'error': 'product_id가 필요합니다.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        product = get_object_or_404(Product, product_id=product_id)
        cart_item, created = CartItem.objects.get_or_create(
            cart=cart,
            product=product,
            defaults={'quantity': quantity}
        )
        
        if not created:
            cart_item.quantity += quantity
            cart_item.save()
        
        return Response({
            'success': True,
            'cart_item': CartItemSerializer(cart_item).data
        })
    
    @action(detail=True, methods=['delete'])
    def remove_item(self, request, pk=None):
        """
        장바구니에서 제품 제거
        DELETE /api/carts/{id}/remove_item/
        """
        cart = self.get_object()
        product_id = request.data.get('product_id')
        
        if not product_id:
            return Response(
                {'error': 'product_id가 필요합니다.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        CartItem.objects.filter(cart=cart, product_id=product_id).delete()
        return Response({'success': True})


class CartItemViewSet(viewsets.ModelViewSet):
    """
    장바구니 항목 관리 ViewSet
    """
    queryset = CartItem.objects.all()
    serializer_class = CartItemSerializer
    # IsAuthenticatedOrReadOnly 기본값 사용 (settings.py)


# ============================================================
# 주문/결제 ViewSets
# ============================================================

class OrderViewSet(viewsets.ModelViewSet):
    """
    주문 관리 ViewSet
    """
    queryset = Orders.objects.all()
    serializer_class = OrderSerializer
    # IsAuthenticatedOrReadOnly 기본값 사용 (settings.py)
    
    @action(detail=True, methods=['post'])
    def create_from_cart(self, request, pk=None):
        """
        장바구니에서 주문 생성
        POST /api/orders/{id}/create_from_cart/
        """
        cart_id = request.data.get('cart_id')
        if not cart_id:
            return Response(
                {'error': 'cart_id가 필요합니다.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        cart = get_object_or_404(CartNew, cart_id=cart_id)
        
        # 주문 생성
        order = Orders.objects.create(
            member=cart.member,
            order_status='주문완료',
            payment_status='결제대기'
        )
        
        # 장바구니 항목을 주문 상세로 변환
        total_amount = 0
        for cart_item in cart.items.all():
            OrderDetail.objects.create(
                order=order,
                product=cart_item.product,
                quantity=cart_item.quantity
            )
            total_amount += (cart_item.product.price or 0) * cart_item.quantity
        
        order.total_amount = total_amount
        order.save()
        
        # 장바구니 비우기
        cart.items.all().delete()
        
        return Response({
            'success': True,
            'order': OrderSerializer(order).data
        })


class OrderDetailViewSet(viewsets.ModelViewSet):
    """
    주문 상세 관리 ViewSet
    """
    queryset = OrderDetail.objects.all()
    serializer_class = OrderDetailSerializer
    # IsAuthenticatedOrReadOnly 기본값 사용 (settings.py)


class PaymentViewSet(viewsets.ModelViewSet):
    """
    결제 관리 ViewSet
    """
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer
    # IsAuthenticatedOrReadOnly 기본값 사용 (settings.py)


# ============================================================
# 온보딩 ViewSets
# ============================================================

class OnboardingQuestionViewSet(viewsets.ReadOnlyModelViewSet):
    """
    온보딩 질문 조회 ViewSet (읽기 전용)
    """
    queryset = OnboardingQuestion.objects.all()
    serializer_class = OnboardingQuestionSerializer
    # IsAuthenticatedOrReadOnly 기본값 사용 (settings.py) - 읽기 전용이므로 인증 불필요
    
    @action(detail=False, methods=['get'])
    def by_type(self, request):
        """
        질문 유형별 조회
        GET /api/onboarding-questions/by_type/?question_type=vibe
        """
        question_type = request.query_params.get('question_type')
        if question_type:
            questions = self.queryset.filter(question_type=question_type)
        else:
            questions = self.queryset.all()
        
        serializer = self.get_serializer(questions, many=True)
        return Response(serializer.data)


class OnboardingAnswerViewSet(viewsets.ReadOnlyModelViewSet):
    """
    온보딩 답변 선택지 조회 ViewSet (읽기 전용)
    """
    queryset = OnboardingAnswer.objects.all()
    serializer_class = OnboardingAnswerSerializer
    # IsAuthenticatedOrReadOnly 기본값 사용 (settings.py) - 읽기 전용이므로 인증 불필요


class OnboardingUserResponseViewSet(viewsets.ModelViewSet):
    """
    온보딩 사용자 응답 관리 ViewSet
    """
    queryset = OnboardingUserResponse.objects.all()
    serializer_class = OnboardingUserResponseSerializer
    # IsAuthenticatedOrReadOnly 기본값 사용 (settings.py)


# ============================================================
# Taste 추천 ViewSets
# ============================================================

class TasteConfigViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Taste 설정 조회 ViewSet (읽기 전용)
    """
    queryset = TasteConfig.objects.filter(is_active=True)
    serializer_class = TasteConfigSerializer
    # IsAuthenticatedOrReadOnly 기본값 사용 (settings.py) - 읽기 전용이므로 인증 불필요
    
    @action(detail=True, methods=['get'])
    def recommendations(self, request, pk=None):
        """
        Taste별 추천 제품 조회
        GET /api/taste-configs/{id}/recommendations/
        """
        taste = self.get_object()
        category_name = request.query_params.get('category')
        
        if category_name:
            recommendations = TasteRecommendedProducts.objects.filter(
                taste=taste,
                category_name=category_name
            ).order_by('rank_order')
        else:
            recommendations = TasteRecommendedProducts.objects.filter(
                taste=taste
            ).order_by('category_name', 'rank_order')
        
        serializer = TasteRecommendedProductsSerializer(recommendations, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'])
    def match_taste(self, request):
        """
        온보딩 결과로 Taste 매칭
        POST /api/taste-configs/match_taste/
        """
        # 온보딩 세션 ID 또는 온보딩 데이터 필요
        session_id = request.data.get('session_id')
        if not session_id:
            return Response(
                {'error': 'session_id가 필요합니다.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        session = get_object_or_404(OnboardingSession, session_id=session_id)
        
        # Taste 매칭 로직 (간단한 예시)
        # 실제로는 더 복잡한 알고리즘 필요
        taste = TasteConfig.objects.filter(is_active=True).first()
        
        if not taste:
            return Response(
                {'error': '활성화된 Taste를 찾을 수 없습니다.'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # 회원에 Taste 할당
        if session.member:
            session.member.taste = taste.taste_id
            session.member.save()
        
        return Response({
            'success': True,
            'taste_id': taste.taste_id,
            'taste': TasteConfigSerializer(taste).data
        })


class TasteCategoryScoresViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Taste 카테고리 점수 조회 ViewSet
    """
    queryset = TasteCategoryScores.objects.all()
    serializer_class = TasteCategoryScoresSerializer
    # IsAuthenticatedOrReadOnly 기본값 사용 (settings.py) - 읽기 전용이므로 인증 불필요


class TasteRecommendedProductsViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Taste 추천 제품 조회 ViewSet
    """
    queryset = TasteRecommendedProducts.objects.all()
    serializer_class = TasteRecommendedProductsSerializer
    # IsAuthenticatedOrReadOnly 기본값 사용 (settings.py) - 읽기 전용이므로 인증 불필요


# ============================================================
# 포트폴리오 ViewSets
# ============================================================

class PortfolioProductViewSet(viewsets.ModelViewSet):
    """
    포트폴리오 제품 관리 ViewSet
    """
    queryset = PortfolioProduct.objects.all()
    serializer_class = PortfolioProductSerializer
    # IsAuthenticatedOrReadOnly 기본값 사용 (settings.py)


class EstimateViewSet(viewsets.ModelViewSet):
    """
    견적 관리 ViewSet
    """
    queryset = Estimate.objects.all()
    serializer_class = EstimateSerializer
    # IsAuthenticatedOrReadOnly 기본값 사용 (settings.py)
    
    @action(detail=False, methods=['post'])
    def create_from_portfolio(self, request):
        """
        포트폴리오로부터 견적 생성
        POST /api/estimates/create_from_portfolio/
        """
        portfolio_id = request.data.get('portfolio_id')
        if not portfolio_id:
            return Response(
                {'error': 'portfolio_id가 필요합니다.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        portfolio = get_object_or_404(Portfolio, portfolio_id=portfolio_id)
        
        # 견적 생성
        estimate = Estimate.objects.create(
            portfolio=portfolio,
            total_price=portfolio.total_original_price,
            discount_price=portfolio.total_discount_price
        )
        
        return Response({
            'success': True,
            'estimate': EstimateSerializer(estimate).data
        })


class ConsultationViewSet(viewsets.ModelViewSet):
    """
    상담 관리 ViewSet
    """
    queryset = Consultation.objects.all()
    serializer_class = ConsultationSerializer
    permission_classes = [AllowAny]


# ============================================================
# 제품 관련 ViewSets
# ============================================================

class ProductImageViewSet(viewsets.ModelViewSet):
    """
    제품 이미지 관리 ViewSet
    """
    queryset = ProductImage.objects.all()
    serializer_class = ProductImageSerializer
    # IsAuthenticatedOrReadOnly 기본값 사용 (settings.py)


class ProductSpecNewViewSet(viewsets.ModelViewSet):
    """
    제품 스펙 관리 ViewSet (ERD)
    """
    queryset = ProductSpecNew.objects.all()
    serializer_class = ProductSpecNewSerializer
    # IsAuthenticatedOrReadOnly 기본값 사용 (settings.py)


class ProductReviewNewViewSet(viewsets.ReadOnlyModelViewSet):
    """
    제품 리뷰 조회 ViewSet (ERD, 읽기 전용)
    """
    queryset = ProductReviewNew.objects.all()
    serializer_class = ProductReviewNewSerializer
    # IsAuthenticatedOrReadOnly 기본값 사용 (settings.py) - 읽기 전용이므로 인증 불필요
