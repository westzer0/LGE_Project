from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils import timezone
import json
from .models import Product, OnboardingSession, Portfolio, ProductReview
from .rule_engine import build_profile, recommend_products
from .services.recommendation_engine import recommendation_engine
from .services.chatgpt_service import chatgpt_service


def index_view(request):
    """
    루트 페이지: 온보딩 설문 + 추천 결과를 보여주는 기본 화면.
    """
    return render(request, "index.html")


def main_page(request):
    """메인 랜딩 페이지 - LG 홈스타일링"""
    return render(request, "main.html")


def onboarding_page(request):
    """온보딩 페이지 렌더링"""
    return render(request, "onboarding.html")


def onboarding_new_page(request):
    """새 온보딩 페이지 (4단계 설문)"""
    return render(request, "onboarding_new.html")


def result_page(request):
    """포트폴리오 결과 페이지"""
    from django.conf import settings
    return render(request, "result.html", {
        'kakao_js_key': getattr(settings, 'KAKAO_JS_KEY', '')
    })


@csrf_exempt
def recommend(request):
    """
    OpenAI 기반 추천 API (현재 사용 안 함)
    recommend_view를 사용하세요.
    """
    # OpenAI 사용 안 함 - recommend_view를 사용하세요
    return JsonResponse({
        "detail": "This endpoint is deprecated. Use /api/recommend/ instead."
    }, status=410)
    
    # if request.method != "POST":
    #     return JsonResponse({"detail": "POST only"}, status=405)
    #
    # try:
    #     data = json.loads(request.body.decode("utf-8"))
    # except json.JSONDecodeError:
    #     return JsonResponse({"detail": "Invalid JSON"}, status=400)
    #
    # household = data.get("household", 2)
    # budget = data.get("budget", 300)
    #
    # # 여기서 OpenAI 호출 (예: Responses API)
    # # response = client.responses.create(
    # #     model="gpt-4.1-mini",
    # #     input=(
    # #         f"{household}인 가구, 예산 {budget}만원, "
    # #         f"이사 가전 포트폴리오 추천 JSON 만들어줘 ..."
    # #     ),
    # #     response_format={"type": "json_object"},
    # # )
    # #
    # # result = json.loads(response.output[0].content[0].text)
    # #
    # # return JsonResponse(result)


@csrf_exempt
@require_http_methods(["POST"])
def recommend_view(request):
    """
    POST /api/recommend/ - 추천 API 엔드포인트
    
    요청:
    {
        "vibe": "modern",
        "household_size": 4,
        "housing_type": "apartment",
        "pyung": 30,
        "priority": "tech",
        "budget_level": "medium",
        "categories": ["TV"]
    }
    
    응답:
    {
        "success": true,
        "count": 3,
        "recommendations": [...]
    }
    """
    try:
        # 1. 요청 데이터 추출
        if hasattr(request, 'data'):  # DRF 사용 시
            data = request.data
        else:  # 일반 Django view
            data = json.loads(request.body.decode("utf-8"))
        
        user_profile = {
            'vibe': data.get('vibe', 'modern'),
            'household_size': int(data.get('household_size', 2)),
            'housing_type': data.get('housing_type', 'apartment'),
            'pyung': int(data.get('pyung', 25)),
            'priority': data.get('priority', 'value'),
            'budget_level': data.get('budget_level', 'medium'),
            'categories': data.get('categories', data.get('target_categories', [])),
            'main_space': data.get('main_space', 'living'),
            'space_size': data.get('space_size', 'medium'),
        }
        
        print(f"\n[API] 추천 요청: {user_profile}")
        
        # 2. Service 호출 (모든 로직은 Service에서)
        result = recommendation_engine.get_recommendations(user_profile)
        
        # 3. 응답
        if result['success']:
            return JsonResponse(result, json_dumps_params={'ensure_ascii': False}, status=200)
        else:
            return JsonResponse(result, json_dumps_params={'ensure_ascii': False}, status=404)
    
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON',
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e),
        }, json_dumps_params={'ensure_ascii': False}, status=400)


@require_http_methods(["GET"])
def products(request):
    """GET /api/products/ - 제품 리스트 조회 (category 쿼리 파라미터 지원)"""
    category = request.GET.get('category', None)
    
    queryset = Product.objects.filter(is_active=True)
    
    if category:
        queryset = queryset.filter(category=category)
    
    products_list = []
    for product in queryset:
        products_list.append({
            'id': product.id,
            'name': product.name,
            'model_number': product.model_number,
            'category': product.category,
            'category_display': product.get_category_display(),
            'description': product.description,
            'price': float(product.price),
            'discount_price': float(product.discount_price) if product.discount_price else None,
            'image_url': product.image_url,
            'created_at': product.created_at.isoformat(),
        })
    
    return JsonResponse({
        'count': len(products_list),
        'results': products_list
    }, json_dumps_params={'ensure_ascii': False})


@csrf_exempt
@require_http_methods(["POST"])
def onboarding_step_view(request):
    """
    온보딩 단계별 저장
    
    요청:
    POST /api/onboarding/step/
    {
        "session_id": "abc12345",
        "step": 2,
        "data": {
            "household_size": 4,
            "vibe": "modern"
        }
    }
    
    응답:
    {
        "success": true,
        "session_id": "abc12345",
        "current_step": 2,
        "next_step": 3
    }
    """
    try:
        if hasattr(request, 'data'):
            data = request.data
        else:
            data = json.loads(request.body.decode("utf-8"))
        
        session_id = data.get('session_id')
        step = int(data.get('step', 1))
        step_data = data.get('data', {})
        
        if not session_id:
            return JsonResponse({
                'success': False,
                'error': 'session_id 필수'
            }, status=400)
        
        # 세션 생성 또는 조회
        session, created = OnboardingSession.objects.get_or_create(
            session_id=session_id,
            defaults={'current_step': 1, 'status': 'in_progress'}
        )
        
        # Step별 데이터 저장
        if step == 1:
            session.vibe = step_data.get('vibe')
        elif step == 2:
            household_size = step_data.get('household_size')
            if household_size:
                session.household_size = int(household_size)
        elif step == 3:
            session.housing_type = step_data.get('housing_type')
            pyung = step_data.get('pyung')
            if pyung:
                session.pyung = int(pyung)
        elif step == 4:
            session.priority = step_data.get('priority', 'value')
        elif step == 5:
            session.budget_level = step_data.get('budget_level', 'medium')
            session.selected_categories = step_data.get('selected_categories', [])
        
        # 진행 상태 업데이트
        session.current_step = step
        session.updated_at = timezone.now()
        session.save()
        
        return JsonResponse({
            'success': True,
            'session_id': session_id,
            'current_step': step,
            'next_step': min(step + 1, 6),
        }, json_dumps_params={'ensure_ascii': False})
    
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, json_dumps_params={'ensure_ascii': False}, status=400)


@csrf_exempt
@require_http_methods(["POST"])
def onboarding_complete_view(request):
    """
    온보딩 완료 → 자동 추천 실행
    
    요청:
    POST /api/onboarding/complete/
    {
        "session_id": "abc12345",
        "vibe": "modern",
        "household_size": 4,
        "housing_type": "apartment",
        "pyung": 30,
        "priority": "tech",
        "budget_level": "medium",
        "selected_categories": ["TV", "KITCHEN"]
    }
    
    응답:
    {
        "success": true,
        "session_id": "abc12345",
        "recommendations": [...]
    }
    """
    try:
        if hasattr(request, 'data'):
            data = request.data
        else:
            data = json.loads(request.body.decode("utf-8"))
        
        session_id = data.get('session_id')
        
        if not session_id:
            return JsonResponse({
                'success': False,
                'error': 'session_id 필수'
            }, json_dumps_params={'ensure_ascii': False}, status=400)
        
        # 1. OnboardingSession 저장
        session, _ = OnboardingSession.objects.update_or_create(
            session_id=session_id,
            defaults={
                'vibe': data.get('vibe'),
                'household_size': int(data.get('household_size', 2)),
                'housing_type': data.get('housing_type'),
                'pyung': int(data.get('pyung', 25)),
                'priority': data.get('priority', 'value'),
                'budget_level': data.get('budget_level', 'medium'),
                'selected_categories': data.get('selected_categories', []),
                'current_step': 5,
                'status': 'completed',
                'completed_at': timezone.now(),
            }
        )
        
        # 2. user_profile 생성
        user_profile = session.to_user_profile()
        
        print(f"\n[Onboarding Complete] Session: {session_id}")
        print(f"[Profile] {user_profile}")
        
        # 3. 추천 엔진 호출
        result = recommendation_engine.get_recommendations(user_profile, limit=3)
        
        # 4. 추천 결과 저장
        if result['success']:
            session.recommended_products = [
                r['product_id'] for r in result['recommendations']
            ]
            session.recommendation_result = result
            session.save()
            
            print(f"[Success] {len(result['recommendations'])}개 제품 추천됨")
            
            return JsonResponse({
                'success': True,
                'session_id': session_id,
                'recommendations': result['recommendations'],
            }, json_dumps_params={'ensure_ascii': False})
        else:
            print(f"[Error] {result.get('error', '알 수 없는 오류')}")
            
            return JsonResponse({
                'success': False,
                'error': result.get('error', '추천 실패'),
                'recommendations': [],
            }, json_dumps_params={'ensure_ascii': False}, status=404)
    
    except Exception as e:
        import traceback
        print(f"[Exception] {traceback.format_exc()}")
        
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, json_dumps_params={'ensure_ascii': False}, status=400)


@require_http_methods(["GET"])
def onboarding_session_view(request, session_id):
    """
    온보딩 세션 조회 (진행 상황 확인)
    
    요청:
    GET /api/onboarding/session/<session_id>/
    
    응답:
    {
        "success": true,
        "session": {
            "session_id": "abc12345",
            "current_step": 3,
            "status": "in_progress",
            "vibe": "modern",
            "household_size": 4,
            ...
        }
    }
    """
    try:
        session = OnboardingSession.objects.get(session_id=session_id)
        
        return JsonResponse({
            'success': True,
            'session': {
                'session_id': session.session_id,
                'current_step': session.current_step,
                'status': session.status,
                'vibe': session.vibe,
                'household_size': session.household_size,
                'housing_type': session.housing_type,
                'pyung': session.pyung,
                'priority': session.priority,
                'budget_level': session.budget_level,
                'selected_categories': session.selected_categories,
                'created_at': session.created_at.isoformat(),
                'completed_at': session.completed_at.isoformat() if session.completed_at else None,
            }
        }, json_dumps_params={'ensure_ascii': False})
    
    except OnboardingSession.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': '세션을 찾을 수 없습니다.'
        }, json_dumps_params={'ensure_ascii': False}, status=404)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, json_dumps_params={'ensure_ascii': False}, status=400)


# ============================================================
# 포트폴리오 API
# ============================================================

@csrf_exempt
@require_http_methods(["POST"])
def portfolio_save_view(request):
    """
    포트폴리오 저장 API
    
    POST /api/portfolio/save/
    {
        "user_id": "kakao_12345" 또는 "session_xxx",
        "style_type": "modern",
        "style_title": "모던 & 미니멀 라이프를 위한 오브제 스타일",
        "style_subtitle": "...",
        "onboarding_data": {...},
        "products": [{...}, {...}],
        "match_score": 93
    }
    """
    try:
        data = json.loads(request.body.decode('utf-8'))
        
        user_id = data.get('user_id', f"guest_{timezone.now().strftime('%Y%m%d%H%M%S')}")
        
        # 포트폴리오 생성
        portfolio = Portfolio.objects.create(
            user_id=user_id,
            style_type=data.get('style_type', 'modern'),
            style_title=data.get('style_title', ''),
            style_subtitle=data.get('style_subtitle', ''),
            onboarding_data=data.get('onboarding_data', {}),
            products=data.get('products', []),
            match_score=data.get('match_score', 0),
            status='saved'
        )
        
        # 가격 합계 계산
        portfolio.calculate_totals()
        
        return JsonResponse({
            'success': True,
            'portfolio_id': portfolio.portfolio_id,
            'message': '포트폴리오가 저장되었습니다.',
            'share_url': f'/portfolio/{portfolio.portfolio_id}/'
        }, json_dumps_params={'ensure_ascii': False})
    
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, json_dumps_params={'ensure_ascii': False}, status=400)


@require_http_methods(["GET"])
def portfolio_detail_view(request, portfolio_id):
    """
    포트폴리오 상세 조회 API
    
    GET /api/portfolio/<portfolio_id>/
    """
    try:
        portfolio = Portfolio.objects.get(portfolio_id=portfolio_id)
        
        return JsonResponse({
            'success': True,
            'portfolio': {
                'portfolio_id': portfolio.portfolio_id,
                'user_id': portfolio.user_id,
                'style_type': portfolio.style_type,
                'style_title': portfolio.style_title,
                'style_subtitle': portfolio.style_subtitle,
                'onboarding_data': portfolio.onboarding_data,
                'products': portfolio.products,
                'total_original_price': float(portfolio.total_original_price),
                'total_discount_price': float(portfolio.total_discount_price),
                'match_score': portfolio.match_score,
                'status': portfolio.status,
                'share_url': portfolio.share_url,
                'share_count': portfolio.share_count,
                'created_at': portfolio.created_at.isoformat(),
            }
        }, json_dumps_params={'ensure_ascii': False})
    
    except Portfolio.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': '포트폴리오를 찾을 수 없습니다.'
        }, json_dumps_params={'ensure_ascii': False}, status=404)


@require_http_methods(["GET"])
def portfolio_list_view(request):
    """
    사용자 포트폴리오 목록 조회 API
    
    GET /api/portfolio/list/?user_id=xxx
    """
    user_id = request.GET.get('user_id')
    
    if not user_id:
        return JsonResponse({
            'success': False,
            'error': 'user_id 필수'
        }, status=400)
    
    portfolios = Portfolio.objects.filter(user_id=user_id).order_by('-created_at')
    
    portfolio_list = []
    for p in portfolios:
        portfolio_list.append({
            'portfolio_id': p.portfolio_id,
            'style_type': p.style_type,
            'style_title': p.style_title,
            'total_discount_price': float(p.total_discount_price),
            'match_score': p.match_score,
            'product_count': len(p.products),
            'status': p.status,
            'created_at': p.created_at.isoformat(),
        })
    
    return JsonResponse({
        'success': True,
        'count': len(portfolio_list),
        'portfolios': portfolio_list
    }, json_dumps_params={'ensure_ascii': False})


@csrf_exempt
@require_http_methods(["POST"])
def portfolio_share_view(request, portfolio_id):
    """
    포트폴리오 공유 API (카카오톡 공유 시 호출)
    
    POST /api/portfolio/<portfolio_id>/share/
    """
    try:
        portfolio = Portfolio.objects.get(portfolio_id=portfolio_id)
        
        # 공유 횟수 증가
        portfolio.share_count += 1
        portfolio.status = 'shared'
        portfolio.share_url = f"https://homestyling.lge.co.kr/portfolio/{portfolio_id}/"
        portfolio.save()
        
        return JsonResponse({
            'success': True,
            'share_url': portfolio.share_url,
            'share_count': portfolio.share_count,
            # 카카오톡 공유용 메타 데이터
            'kakao_share_data': {
                'title': f"LG 홈스타일링 - {portfolio.style_title}",
                'description': portfolio.style_subtitle[:100] if portfolio.style_subtitle else '나에게 딱 맞는 LG 가전 패키지를 추천받았어요!',
                'image_url': 'https://www.lge.co.kr/kr/images/brand/objet-collection/2024/visual/kv_visual_bg_w.webp',
                'link': portfolio.share_url,
            }
        }, json_dumps_params={'ensure_ascii': False})
    
    except Portfolio.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': '포트폴리오를 찾을 수 없습니다.'
        }, json_dumps_params={'ensure_ascii': False}, status=404)


# ============================================================
# ChatGPT AI API
# ============================================================

@csrf_exempt
@require_http_methods(["POST"])
def ai_recommendation_reason_view(request):
    """
    AI 추천 이유 생성 API
    
    POST /api/ai/recommendation-reason/
    {
        "product_info": {"name": "...", "category": "...", "specs": "..."},
        "user_profile": {"household_size": 4, "style": "modern", ...}
    }
    """
    try:
        data = json.loads(request.body.decode('utf-8'))
        
        product_info = data.get('product_info', {})
        user_profile = data.get('user_profile', {})
        
        reason = chatgpt_service.generate_recommendation_reason(product_info, user_profile)
        
        return JsonResponse({
            'success': True,
            'reason': reason,
            'ai_generated': chatgpt_service.is_available()
        }, json_dumps_params={'ensure_ascii': False})
    
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, json_dumps_params={'ensure_ascii': False}, status=400)


@csrf_exempt
@require_http_methods(["POST"])
def ai_style_message_view(request):
    """
    AI 스타일 메시지 생성 API
    
    POST /api/ai/style-message/
    {
        "user_profile": {"household_size": 4, "style": "modern", ...}
    }
    """
    try:
        data = json.loads(request.body.decode('utf-8'))
        user_profile = data.get('user_profile', {})
        
        result = chatgpt_service.generate_style_message(user_profile)
        
        return JsonResponse({
            'success': True,
            'title': result['title'],
            'subtitle': result['subtitle'],
            'ai_generated': chatgpt_service.is_available()
        }, json_dumps_params={'ensure_ascii': False})
    
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, json_dumps_params={'ensure_ascii': False}, status=400)


@csrf_exempt
@require_http_methods(["POST"])
def ai_review_summary_view(request):
    """
    AI 리뷰 요약 API
    
    POST /api/ai/review-summary/
    {
        "product_id": 123,  # 또는
        "reviews": ["리뷰1", "리뷰2", ...]
    }
    """
    try:
        data = json.loads(request.body.decode('utf-8'))
        
        product_id = data.get('product_id')
        reviews = data.get('reviews', [])
        product_name = data.get('product_name', '')
        
        # product_id가 있으면 DB에서 리뷰 가져오기
        if product_id and not reviews:
            product = Product.objects.get(id=product_id)
            product_name = product.name
            review_objs = ProductReview.objects.filter(product=product)[:20]
            reviews = [r.review_text for r in review_objs if r.review_text]
        
        if not reviews:
            return JsonResponse({
                'success': True,
                'summary': '아직 리뷰가 없어요.',
                'review_count': 0
            }, json_dumps_params={'ensure_ascii': False})
        
        summary = chatgpt_service.summarize_reviews(reviews, product_name)
        
        return JsonResponse({
            'success': True,
            'summary': summary,
            'review_count': len(reviews),
            'ai_generated': chatgpt_service.is_available()
        }, json_dumps_params={'ensure_ascii': False})
    
    except Product.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': '제품을 찾을 수 없습니다.'
        }, json_dumps_params={'ensure_ascii': False}, status=404)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, json_dumps_params={'ensure_ascii': False}, status=400)


@csrf_exempt
@require_http_methods(["POST"])
def ai_chat_view(request):
    """
    AI 상담 챗봇 API
    
    POST /api/ai/chat/
    {
        "message": "냉장고 추천해주세요",
        "context": {"history": [...]}  # 선택
    }
    """
    try:
        data = json.loads(request.body.decode('utf-8'))
        
        user_message = data.get('message', '')
        context = data.get('context', {})
        
        if not user_message:
            return JsonResponse({
                'success': False,
                'error': '메시지를 입력해주세요.'
            }, status=400)
        
        response = chatgpt_service.chat_response(user_message, context)
        
        return JsonResponse({
            'success': True,
            'response': response,
            'ai_generated': chatgpt_service.is_available()
        }, json_dumps_params={'ensure_ascii': False})
    
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, json_dumps_params={'ensure_ascii': False}, status=400)


@require_http_methods(["GET"])
def ai_status_view(request):
    """
    AI 서비스 상태 확인 API
    
    GET /api/ai/status/
    """
    return JsonResponse({
        'success': True,
        'chatgpt_available': chatgpt_service.is_available(),
        'model': chatgpt_service.MODEL if chatgpt_service.is_available() else None
    })
