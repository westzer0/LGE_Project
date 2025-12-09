"""
추천 엔진 API 엔드포인트

엔드포인트:
- POST /api/v1/onboarding/complete/ - 온보딩 완료 → TASTE_ID 할당
- GET /api/v1/recommendations/taste/{taste_id}/ - Taste별 카테고리별 TOP3 추천
- POST /api/v1/portfolio/generate/ - 최종 포트폴리오 생성
"""
from rest_framework import status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.shortcuts import get_object_or_404
from django.utils import timezone
import logging

from api.models import (
    OnboardingSession, Member, TasteConfig, Product,
    TasteRecommendedProducts, Portfolio, PortfolioProduct
)

logger = logging.getLogger(__name__)


@api_view(['POST'])
@permission_classes([AllowAny])
def onboarding_complete_view(request):
    """
    온보딩 완료 → TASTE_ID 할당
    
    POST /api/v1/onboarding/complete/
    
    Request Body:
    {
        "session_id": 123  # 또는 "session_uuid": "abc123"
    }
    
    Response:
    {
        "success": true,
        "session_id": 123,
        "taste_id": 23,
        "taste": {
            "taste_id": 23,
            "description": "...",
            "recommended_categories": ["TV", "냉장고", "세탁기"]
        },
        "member": {
            "member_id": "kakao_123456",
            "taste": 23
        }
    }
    """
    print(f"[Onboarding Complete (views_recommendations)] 요청 시작...", flush=True)
    print(f"[Onboarding Complete (views_recommendations)] request.data: {request.data}", flush=True)
    try:
        session_id = request.data.get('session_id')
        session_uuid = request.data.get('session_uuid')
        
        print(f"[Onboarding Complete (views_recommendations)] session_id={session_id}, session_uuid={session_uuid}", flush=True)
        
        if not session_id and not session_uuid:
            return Response({
                'success': False,
                'error': 'session_id 또는 session_uuid가 필요합니다.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # 온보딩 세션 조회
        if session_id:
            session = get_object_or_404(OnboardingSession, session_id=session_id)
        else:
            session = get_object_or_404(OnboardingSession, session_uuid=session_uuid)
        
        # 온보딩 완료 처리
        session.status = 'completed'
        session.current_step = 6
        session.completed_at = timezone.now()
        session.save()
        
        # Taste 매칭 로직 (간단한 예시 - 실제로는 더 복잡한 알고리즘 필요)
        # 온보딩 데이터 기반으로 가장 적합한 Taste 찾기
        taste = _match_taste_from_onboarding(session)
        
        if not taste:
            return Response({
                'success': False,
                'error': '적합한 Taste를 찾을 수 없습니다.'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # 회원에 Taste 할당
        if session.member:
            session.member.taste = taste.taste_id
            session.member.save()
        
        return Response({
            'success': True,
            'session_id': session.session_id,
            'taste_id': taste.taste_id,
            'taste': {
                'taste_id': taste.taste_id,
                'description': taste.description,
                'recommended_categories': taste.recommended_categories,
                'recommended_categories_with_scores': taste.recommended_categories_with_scores,
            },
            'member': {
                'member_id': session.member.member_id if session.member else None,
                'taste': taste.taste_id if session.member else None,
            }
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"[Onboarding Complete] 오류: {str(e)}", exc_info=True)
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_400_BAD_REQUEST)


def _match_taste_from_onboarding(session):
    """
    온보딩 세션 데이터로부터 가장 적합한 Taste 찾기
    
    Args:
        session: OnboardingSession 객체
        
    Returns:
        TasteConfig 객체 또는 None
    """
    # 간단한 매칭 로직 (실제로는 더 복잡한 알고리즘 필요)
    # 1. 활성화된 Taste 중에서
    # 2. 온보딩 데이터와 가장 유사한 Taste 찾기
    
    active_tastes = TasteConfig.objects.filter(is_active=True)
    
    if not active_tastes.exists():
        return None
    
    # 온보딩 데이터 추출
    vibe = session.vibe or 'modern'
    household_size = session.household_size or 2
    priority = session.priority or 'value'
    budget_level = session.budget_level or 'medium'
    
    # 가장 유사한 Taste 찾기 (간단한 예시)
    best_match = None
    best_score = 0
    
    for taste in active_tastes:
        score = 0
        
        # Vibe 매칭
        if taste.representative_vibe == vibe:
            score += 30
        
        # Household size 매칭 (범위 내)
        if taste.representative_household_size:
            if abs(taste.representative_household_size - household_size) <= 1:
                score += 20
        
        # Priority 매칭
        if taste.representative_priority == priority:
            score += 25
        
        # Budget level 매칭
        if taste.representative_budget_level == budget_level:
            score += 25
        
        if score > best_score:
            best_score = score
            best_match = taste
    
    return best_match if best_match else active_tastes.first()


@api_view(['GET'])
@permission_classes([AllowAny])
def taste_recommendations_view(request, taste_id):
    """
    Taste별 카테고리별 TOP3 추천 제품 조회
    
    GET /api/v1/recommendations/taste/{taste_id}/
    Query Parameters:
        - category: 카테고리 필터 (선택, 예: ?category=TV)
    
    Response:
    {
        "success": true,
        "taste_id": 23,
        "recommendations": {
            "TV": [
                {
                    "product_id": 1,
                    "product_name": "OLED65C3",
                    "price": 2500000,
                    "rank_order": 1,
                    "score": 95.5
                },
                ...
            ],
            "냉장고": [...],
            ...
        }
    }
    """
    try:
        taste = get_object_or_404(TasteConfig, taste_id=taste_id, is_active=True)
        category_filter = request.query_params.get('category')
        
        # TasteRecommendedProducts에서 추천 제품 조회
        if category_filter:
            recommendations = TasteRecommendedProducts.objects.filter(
                taste=taste,
                category_name=category_filter
            ).order_by('rank_order')[:3]
        else:
            # 모든 카테고리별 TOP3
            recommendations = TasteRecommendedProducts.objects.filter(
                taste=taste
            ).order_by('category_name', 'rank_order')
        
        # 카테고리별로 그룹화
        recommendations_by_category = {}
        for rec in recommendations:
            category = rec.category_name
            if category not in recommendations_by_category:
                recommendations_by_category[category] = []
            
            # 제품 정보 포함
            product_data = {
                'product_id': rec.product.product_id,
                'product_name': rec.product.product_name or rec.product.name,
                'model_code': rec.product.model_code or rec.product.model_number,
                'price': float(rec.product.price) if rec.product.price else None,
                'discount_price': float(rec.product.discount_price) if rec.product.discount_price else None,
                'image_url': rec.product.image_url or '',
                'main_category': rec.product.main_category or rec.product.category,
                'rank_order': rec.rank_order,
                'score': float(rec.score) if rec.score else None,
            }
            
            # 카테고리별 최대 3개만
            if len(recommendations_by_category[category]) < 3:
                recommendations_by_category[category].append(product_data)
        
        # TasteConfig의 recommended_products JSON도 활용 (없는 경우)
        if not recommendations_by_category and taste.recommended_products:
            for category, product_ids in taste.recommended_products.items():
                if category_filter and category != category_filter:
                    continue
                
                recommendations_by_category[category] = []
                for idx, product_id in enumerate(product_ids[:3], 1):
                    try:
                        product = Product.objects.get(product_id=product_id)
                        recommendations_by_category[category].append({
                            'product_id': product.product_id,
                            'product_name': product.product_name or product.name,
                            'model_code': product.model_code or product.model_number,
                            'price': float(product.price) if product.price else None,
                            'discount_price': float(product.discount_price) if product.discount_price else None,
                            'image_url': product.image_url or '',
                            'main_category': product.main_category or product.category,
                            'rank_order': idx,
                            'score': None,
                        })
                    except Product.DoesNotExist:
                        continue
        
        return Response({
            'success': True,
            'taste_id': taste_id,
            'taste_description': taste.description,
            'recommended_categories': taste.recommended_categories,
            'recommendations': recommendations_by_category,
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"[Taste Recommendations] 오류: {str(e)}", exc_info=True)
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def portfolio_generate_view(request):
    """
    최종 포트폴리오 생성
    
    POST /api/v1/portfolio/generate/
    Header: Authorization: Bearer {access_token}
    
    Request Body:
    {
        "session_id": 123,  # 또는 "taste_id": 23
        "selected_products": [  # 선택한 제품 ID 목록 (선택)
            {"product_id": 1, "category": "TV"},
            {"product_id": 2, "category": "냉장고"}
        ]
    }
    
    Response:
    {
        "success": true,
        "portfolio": {
            "portfolio_id": "PF-ABC123",
            "style_type": "modern",
            "products": [...],
            "total_original_price": 5000000,
            "total_discount_price": 4500000
        }
    }
    """
    try:
        session_id = request.data.get('session_id')
        taste_id = request.data.get('taste_id')
        selected_products = request.data.get('selected_products', [])
        
        # 사용자 정보 (JWT에서)
        user = request.user
        user_id = user.username  # kakao_123456 형식
        
        # 온보딩 세션 또는 Taste 조회
        session = None
        taste = None
        
        if session_id:
            session = get_object_or_404(OnboardingSession, session_id=session_id)
            if session.member:
                taste_id = session.member.taste
        
        if taste_id:
            taste = get_object_or_404(TasteConfig, taste_id=taste_id, is_active=True)
        
        if not session and not taste:
            return Response({
                'success': False,
                'error': 'session_id 또는 taste_id가 필요합니다.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # 포트폴리오 생성
        portfolio = Portfolio.objects.create(
            user_id=user_id,
            onboarding_session=session,
            style_type=session.vibe if session else 'modern',
            style_title=_generate_portfolio_title(taste or session),
            onboarding_data=_extract_onboarding_data(session),
        )
        
        # 제품 추가
        products_data = []
        total_original = 0
        total_discount = 0
        
        if selected_products:
            # 사용자가 선택한 제품
            for item in selected_products:
                product_id = item.get('product_id')
                try:
                    product = Product.objects.get(product_id=product_id)
                    products_data.append({
                        'product_id': product.product_id,
                        'product_name': product.product_name or product.name,
                        'model_code': product.model_code or product.model_number,
                        'price': float(product.price) if product.price else 0,
                        'discount_price': float(product.discount_price or product.price) if product.price else 0,
                        'image_url': product.image_url or '',
                        'main_category': product.main_category or product.category,
                    })
                    total_original += float(product.price) if product.price else 0
                    total_discount += float(product.discount_price or product.price) if product.price else 0
                    
                    # PortfolioProduct 모델에도 저장
                    PortfolioProduct.objects.create(
                        portfolio=portfolio,
                        product=product,
                        priority=len(products_data),
                    )
                except Product.DoesNotExist:
                    continue
        else:
            # Taste 기반 자동 추천
            if taste:
                for category in taste.recommended_categories[:3]:  # 상위 3개 카테고리
                    recs = TasteRecommendedProducts.objects.filter(
                        taste=taste,
                        category_name=category
                    ).order_by('rank_order')[:1]  # 카테고리당 1개
                    
                    for rec in recs:
                        product = rec.product
                        products_data.append({
                            'product_id': product.product_id,
                            'product_name': product.product_name or product.name,
                            'model_code': product.model_code or product.model_number,
                            'price': float(product.price) if product.price else 0,
                            'discount_price': float(product.discount_price or product.price) if product.price else 0,
                            'image_url': product.image_url or '',
                            'main_category': product.main_category or product.category,
                        })
                        total_original += float(product.price) if product.price else 0
                        total_discount += float(product.discount_price or product.price) if product.price else 0
                        
                        PortfolioProduct.objects.create(
                            portfolio=portfolio,
                            product=product,
                            priority=len(products_data),
                        )
        
        # 포트폴리오 업데이트
        portfolio.products = products_data
        portfolio.total_original_price = total_original
        portfolio.total_discount_price = total_discount
        portfolio.status = 'saved'
        portfolio.save()
        
        return Response({
            'success': True,
            'portfolio': {
                'portfolio_id': portfolio.portfolio_id,
                'internal_key': portfolio.internal_key,
                'style_type': portfolio.style_type,
                'style_title': portfolio.style_title,
                'products': products_data,
                'total_original_price': total_original,
                'total_discount_price': total_discount,
                'match_score': portfolio.match_score,
                'created_at': portfolio.created_at,
            }
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"[Portfolio Generate] 오류: {str(e)}", exc_info=True)
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_400_BAD_REQUEST)


def _generate_portfolio_title(taste_or_session):
    """포트폴리오 타이틀 생성"""
    if hasattr(taste_or_session, 'taste_id'):
        # TasteConfig
        return f"Taste {taste_or_session.taste_id} 기반 추천 포트폴리오"
    else:
        # OnboardingSession
        vibe_map = {
            'modern': '모던 & 미니멀',
            'cozy': '따뜻한 코지',
            'pop': '팝 & 생기있는',
            'luxury': '럭셔리 & 프리미엄',
        }
        vibe_name = vibe_map.get(taste_or_session.vibe, '모던')
        return f"{vibe_name} 스타일 포트폴리오"


def _extract_onboarding_data(session):
    """온보딩 세션에서 데이터 추출 (정규화 테이블 사용)"""
    if not session:
        return {}
    
    # 정규화 테이블에서 main_space와 selected_categories 읽기
    main_spaces = []
    selected_categories = []
    
    try:
        from api.services.onboarding_db_service import onboarding_db_service
        session_data = onboarding_db_service.get_session(session.session_id)
        
        if session_data:
            # main_space 정규화 테이블에서 읽기
            if 'MAIN_SPACE' in session_data and session_data['MAIN_SPACE']:
                import json
                try:
                    main_space_str = session_data['MAIN_SPACE']
                    main_spaces = json.loads(main_space_str) if isinstance(main_space_str, str) else main_space_str
                except:
                    main_spaces = []
            
            # selected_categories 정규화 테이블에서 읽기
            if 'SELECTED_CATEGORIES' in session_data:
                selected_categories = session_data['SELECTED_CATEGORIES']
                if not isinstance(selected_categories, list):
                    selected_categories = [selected_categories] if selected_categories else []
    except Exception as e:
        print(f"[views_recommendations] 정규화 테이블 읽기 실패: {e}")
        # 기본값 사용
        main_spaces = ['living']
        selected_categories = []
    
    return {
        'vibe': session.vibe,
        'household_size': session.household_size,
        'has_pet': session.has_pet,
        'housing_type': session.housing_type,
        'pyung': session.pyung,
        'main_space': main_spaces[0] if main_spaces else 'living',
        'cooking': session.cooking,
        'laundry': session.laundry,
        'media': session.media,
        'priority': session.priority,
        'budget_level': session.budget_level,
        'selected_categories': selected_categories,
    }
