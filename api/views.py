from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils import timezone
import json
# from openai import OpenAI  # OpenAI 사용 안 함
from .models import Product, OnboardingSession
from .rule_engine import build_profile, recommend_products
from .services.recommendation_engine import recommendation_engine

# client = OpenAI(api_key="환경변수에서_불러오기")  # OpenAI 사용 안 함


def index_view(request):
    """
    루트 페이지: 온보딩 설문 + 추천 결과를 보여주는 기본 화면.
    """
    return render(request, "index.html")


def onboarding_page(request):
    """온보딩 페이지 렌더링"""
    return render(request, "onboarding.html")


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
