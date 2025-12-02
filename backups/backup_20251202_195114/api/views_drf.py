"""
Django REST Framework Views

기존 views.py의 API 엔드포인트를 DRF로 변환
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework import viewsets
from rest_framework.decorators import action
from django.shortcuts import get_object_or_404
from django.utils import timezone

from .serializers import (
    RecommendRequestSerializer,
    RecommendResponseSerializer,
    PortfolioSerializer,
    PortfolioCreateSerializer,
    OnboardingSessionSerializer,
)
from .models import Portfolio, OnboardingSession
from .services.recommendation_engine import recommendation_engine


# ============================================================
# 추천 API (DRF)
# ============================================================

class RecommendAPIView(APIView):
    """
    POST /api/recommend/ - 추천 API (DRF 버전)
    
    기존 recommend_view를 DRF로 변환
    """
    def post(self, request):
        serializer = RecommendRequestSerializer(data=request.data)
        
        if serializer.is_valid():
            # 검증된 데이터로 백엔드 로직 호출
            user_profile = serializer.validated_data
            result = recommendation_engine.get_recommendations(user_profile)
            
            # 응답 Serializer로 포맷팅
            response_serializer = RecommendResponseSerializer(result)
            return Response(
                response_serializer.data,
                status=status.HTTP_200_OK if result.get('success') else status.HTTP_404_NOT_FOUND
            )
        
        # 검증 실패 시 에러 반환
        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )


# ============================================================
# 포트폴리오 API (DRF ViewSet)
# ============================================================

class PortfolioViewSet(viewsets.ModelViewSet):
    """
    포트폴리오 CRUD API
    
    자동 생성되는 엔드포인트:
    - GET    /api/portfolios/          - 리스트
    - POST   /api/portfolios/          - 생성
    - GET    /api/portfolios/{id}/     - 상세
    - PUT    /api/portfolios/{id}/     - 전체 수정
    - PATCH  /api/portfolios/{id}/     - 부분 수정
    - DELETE /api/portfolios/{id}/     - 삭제
    """
    queryset = Portfolio.objects.all()
    serializer_class = PortfolioSerializer
    lookup_field = 'portfolio_id'
    lookup_value_regex = '[^/]+'
    
    def get_queryset(self):
        """쿼리셋 필터링 (user_id로 필터링 가능)"""
        queryset = Portfolio.objects.all()
        user_id = self.request.query_params.get('user_id', None)
        
        if user_id:
            queryset = queryset.filter(user_id=user_id)
        
        return queryset.order_by('-created_at')
    
    def create(self, request):
        """포트폴리오 생성"""
        create_serializer = PortfolioCreateSerializer(data=request.data)
        
        if create_serializer.is_valid():
            portfolio_data = create_serializer.validated_data
            
            # Portfolio 생성
            portfolio = Portfolio.objects.create(
                user_id=portfolio_data.get('user_id', f"guest_{timezone.now().strftime('%Y%m%d%H%M%S')}"),
                style_type=portfolio_data['style_type'],
                style_title=portfolio_data.get('style_title', ''),
                style_subtitle=portfolio_data.get('style_subtitle', ''),
                onboarding_data=portfolio_data.get('onboarding_data', {}),
                products=portfolio_data['products'],
                match_score=portfolio_data.get('match_score', 0),
                status='saved'
            )
            
            # 가격 합계 계산
            portfolio.calculate_totals()
            
            serializer = PortfolioSerializer(portfolio)
            return Response({
                'success': True,
                'portfolio_id': portfolio.portfolio_id,
                'message': '포트폴리오가 저장되었습니다.',
                'share_url': f'/portfolio/{portfolio.portfolio_id}/',
                'portfolio': serializer.data
            }, status=status.HTTP_201_CREATED)
        
        return Response(create_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def share(self, request, portfolio_id=None):
        """포트폴리오 공유 (커스텀 엔드포인트: /api/portfolios/{id}/share/)"""
        portfolio = self.get_object()
        
        # 공유 횟수 증가
        portfolio.share_count += 1
        portfolio.save()
        
        return Response({
            'success': True,
            'portfolio_id': portfolio.portfolio_id,
            'share_url': portfolio.share_url or f'/portfolio/{portfolio.portfolio_id}/',
            'share_count': portfolio.share_count
        }, status=status.HTTP_200_OK)
    
    def list(self, request):
        """사용자별 포트폴리오 리스트 (user_id 쿼리 파라미터 지원)"""
        user_id = request.query_params.get('user_id')
        queryset = self.get_queryset()
        
        # user_id가 제공되면 필터링 (get_queryset에서 이미 처리됨)
        serializer = self.get_serializer(queryset, many=True)
        
        return Response({
            'success': True,
            'count': len(serializer.data),
            'portfolios': serializer.data
        }, status=status.HTTP_200_OK)


# ============================================================
# 온보딩 세션 API (DRF)
# ============================================================

class OnboardingSessionViewSet(viewsets.ReadOnlyModelViewSet):
    """
    온보딩 세션 조회 API (읽기 전용)
    
    자동 생성되는 엔드포인트:
    - GET /api/onboarding-sessions/         - 리스트
    - GET /api/onboarding-sessions/{id}/    - 상세
    """
    queryset = OnboardingSession.objects.all()
    serializer_class = OnboardingSessionSerializer
    lookup_field = 'session_id'
    lookup_value_regex = '[^/]+'

