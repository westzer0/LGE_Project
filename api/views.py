from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils import timezone
import json
from .models import Product, OnboardingSession, Portfolio, ProductReview
from .rule_engine import build_profile, recommend_products
from .services.recommendation_engine import recommendation_engine
from .services.playbook_recommendation_engine import playbook_recommendation_engine
from .services.column_based_recommendation_engine import column_based_recommendation_engine
from .services.chatgpt_service import chatgpt_service


def index_view(request):
    """
    루트 페이지: 온보딩 설문 + 추천 결과를 보여주는 기본 화면.
    """
    return render(request, "index.html")


def main_page(request):
    """메인 랜딩 페이지 - LG 홈스타일링"""
    from django.conf import settings
    return render(request, "main.html", {
        'kakao_js_key': getattr(settings, 'KAKAO_JS_KEY', '')
    })


def fake_lg_main_page(request):
    """LG전자 메인페이지 복제 - 패키지추천 버튼 포함"""
    return render(request, "fake_lg_main.html")


def onboarding_page(request):
    """온보딩 페이지 렌더링 (1단계)"""
    return render(request, "onboarding.html")


def onboarding_step2_page(request):
    """온보딩 페이지 렌더링 (2단계)"""
    return render(request, "onboarding_step2.html")


def onboarding_step3_page(request):
    """온보딩 페이지 렌더링 (3단계)"""
    return render(request, "onboarding_step3.html")


def onboarding_step4_page(request):
    """온보딩 페이지 렌더링 (4단계)"""
    return render(request, "onboarding_step4.html")


def onboarding_step5_page(request):
    """온보딩 페이지 렌더링 (5단계)"""
    return render(request, "onboarding_step5.html")


def onboarding_step6_page(request):
    """온보딩 페이지 렌더링 (6단계)"""
    return render(request, "onboarding_step6.html")


def onboarding_step7_page(request):
    """온보딩 페이지 렌더링 (7단계)"""
    return render(request, "onboarding_step7.html")


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
def recommend_playbook_view(request):
    """
    POST /api/recommend/playbook/ - Playbook 설계 기반 추천 API
    
    요청:
    {
        "vibe": "modern",
        "household_size": 4,
        "housing_type": "apartment",
        "pyung": 30,
        "priority": ["tech", "design"],  # 배열로 우선순위
        "budget_level": "medium",
        "budget_amount": 2000000,
        "categories": ["TV", "KITCHEN"],
        "onboarding_data": {
            "cooking": "high",
            "laundry": "weekly",
            "media": "gaming"
        },
        "options": {
            "top_n": 3
        }
    }
    
    응답:
    {
        "success": true,
        "count": 3,
        "user_profile_summary": "...",
        "recommendations": [
            {
                "product_id": 1,
                "total_score": 87.2,
                "score_breakdown": {
                    "SpecScore": 32,
                    "PreferenceScore": 18,
                    "LifestyleScore": 20,
                    "ReviewScore": 9,
                    "PriceScore": 8,
                    "TotalScore": 87.2
                },
                "explanation": {
                    "why_summary": "...",
                    "lifestyle_message": "...",
                    "design_message": "...",
                    "review_highlight": "..."
                }
            }
        ]
    }
    """
    try:
        if hasattr(request, 'data'):
            data = request.data
        else:
            data = json.loads(request.body.decode("utf-8"))
        
        user_profile = {
            'vibe': data.get('vibe', 'modern'),
            'household_size': int(data.get('household_size', 2)),
            'housing_type': data.get('housing_type', 'apartment'),
            'pyung': int(data.get('pyung', 25)),
            'priority': data.get('priority', 'value'),  # 배열 또는 문자열
            'budget_level': data.get('budget_level', 'medium'),
            'budget_amount': data.get('budget_amount', 0),
            'categories': data.get('categories', data.get('target_categories', [])),
            'main_space': data.get('main_space', 'living'),
            'space_size': data.get('space_size', 'medium'),
            'has_pet': data.get('has_pet', False),
        }
        
        onboarding_data = data.get('onboarding_data', {
            'cooking': data.get('cooking', 'sometimes'),
            'laundry': data.get('laundry', 'weekly'),
            'media': data.get('media', 'balanced'),
        })
        
        options = data.get('options', {})
        limit = options.get('top_n', 3)
        
        print(f"\n[Playbook API] 추천 요청: {user_profile}")
        print(f"[Playbook API] 온보딩 데이터: {onboarding_data}")
        
        # Playbook 추천 엔진 호출
        result = playbook_recommendation_engine.get_recommendations(
            user_profile=user_profile,
            limit=limit,
            onboarding_data=onboarding_data
        )
        
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
        import traceback
        return JsonResponse({
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc()
        }, json_dumps_params={'ensure_ascii': False}, status=400)


@csrf_exempt
@require_http_methods(["POST"])
def recommend_column_based_view(request):
    """
    POST /api/recommend/column-based/ - 칼럼 점수 기반 추천 API
    
    Oracle DB PRODUCT SPEC 테이블의 SPEC_TYPE(COMMON/VARIANT)과 SPEC_KEY 기반 추천
    
    요청:
    {
        "vibe": "modern",
        "household_size": 4,
        "housing_type": "apartment",
        "pyung": 30,
        "priority": "tech",
        "budget_level": "medium",
        "budget_amount": 2000000,
        "categories": ["TV", "KITCHEN", "LIVING"],
        "onboarding_data": {
            "cooking": "high",
            "laundry": "daily",
            "media": "gaming"
        }
    }
    
    응답:
    {
        "success": true,
        "count": 15,
        "product_types": ["냉장고", "TV", "세탁기", "청소기", "식기세척기"],
        "column_scores": {
            "냉장고": 0.92,
            "TV": 0.88,
            "세탁기": 0.85,
            ...
        },
        "recommendations": [
            {
                "product_id": 1,
                "product_type": "냉장고",
                "name": "LG 디오스 냉장고",
                "score": 0.92,
                ...
            },
            // 각 제품 종류별 상위 3개씩
        ]
    }
    """
    try:
        if hasattr(request, 'data'):
            data = request.data
        else:
            data = json.loads(request.body.decode("utf-8"))
        
        user_profile = {
            'vibe': data.get('vibe', 'modern'),
            'household_size': int(data.get('household_size', 2)),
            'housing_type': data.get('housing_type', 'apartment'),
            'pyung': int(data.get('pyung', 25)),
            'priority': data.get('priority', 'value'),
            'budget_level': data.get('budget_level', 'medium'),
            'budget_amount': data.get('budget_amount', 0),
            'categories': data.get('categories', []),
            'main_space': data.get('main_space', 'living'),
            'space_size': data.get('space_size', 'medium'),
            'has_pet': data.get('has_pet', False),
        }
        
        onboarding_data = data.get('onboarding_data', {
            'cooking': data.get('cooking', 'sometimes'),
            'laundry': data.get('laundry', 'weekly'),
            'media': data.get('media', 'balanced'),
        })
        
        taste_id = data.get('taste_id')
        
        print(f"\n[Column-Based API] 추천 요청:")
        print(f"  사용자 프로필: {user_profile}")
        print(f"  온보딩 데이터: {onboarding_data}")
        
        result = column_based_recommendation_engine.get_recommendations(
            user_profile=user_profile,
            onboarding_data=onboarding_data,
            taste_id=taste_id
        )
        
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
        import traceback
        logger.error(f"Column-Based Recommendation Error: {str(e)}", exc_info=True)
        return JsonResponse({
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc()
        }, json_dumps_params={'ensure_ascii': False}, status=400)


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
            'has_pet': data.get('has_pet', False),  # 반려동물 정보 추가
            'cooking': data.get('cooking', 'sometimes'),
            'laundry': data.get('laundry', 'weekly'),
            'media': data.get('media', 'balanced'),
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


@require_http_methods(["GET"])
def product_spec_view(request, product_id):
    """GET /api/products/<product_id>/spec/ - 제품 스펙 조회"""
    import json
    try:
        product = Product.objects.get(id=product_id)
        
        # ProductSpec이 있으면 스펙 정보 반환
        if hasattr(product, 'spec') and product.spec.spec_json:
            try:
                specs = json.loads(product.spec.spec_json)
            except:
                specs = {}
        else:
            specs = {}
        
        return JsonResponse({
            'success': True,
            'product_id': product.id,
            'product_name': product.name,
            'specs': specs
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


@require_http_methods(["GET"])
def product_image_by_name_view(request):
    """GET /api/products/image-by-name/?name=제품명 - 제품명으로 이미지 URL 조회"""
    from .utils import get_image_url_from_csv
    
    product_name = request.GET.get('name', '').strip()
    category_hint = request.GET.get('category', None)  # 선택적 카테고리 힌트
    
    if not product_name:
        return JsonResponse({
            'success': False,
            'error': '제품명이 필요합니다.'
        }, json_dumps_params={'ensure_ascii': False}, status=400)
    
    try:
        # 유틸리티 함수를 사용하여 이미지 URL 가져오기
        image_url = get_image_url_from_csv(product_name, category_hint=category_hint)
        
        if not image_url or image_url.startswith('https://via.placeholder.com'):
            return JsonResponse({
                'success': False,
                'error': f'제품을 찾을 수 없습니다: {product_name}',
                'image_url': image_url  # placeholder URL 반환
            }, json_dumps_params={'ensure_ascii': False}, status=404)
        
        return JsonResponse({
            'success': True,
            'product_name': product_name,
            'image_url': image_url
        }, json_dumps_params={'ensure_ascii': False})
    
    except Exception as e:
        import traceback
        return JsonResponse({
            'success': False,
            'error': f'오류 발생: {str(e)}',
            'traceback': traceback.format_exc()
        }, json_dumps_params={'ensure_ascii': False}, status=500)


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
        # 요청 데이터 파싱
        try:
            if hasattr(request, 'data'):
                data = request.data
            else:
                body_str = request.body.decode("utf-8")
                if body_str:
                    data = json.loads(body_str)
                else:
                    data = {}
        except json.JSONDecodeError as e:
            return JsonResponse({
                'success': False,
                'error': f'JSON 파싱 오류: {str(e)}'
            }, status=400)
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': f'요청 데이터 처리 오류: {str(e)}'
            }, status=400)
        
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
            # household_size 또는 mate 값 처리
            household_size = step_data.get('household_size')
            mate = step_data.get('mate')  # 2단계에서 전달되는 mate 값
            pet = step_data.get('pet')  # 반려동물 정보
            
            if household_size:
                session.household_size = int(household_size)
            elif mate:
                # mate 값을 household_size로 변환
                mate_to_size = {
                    'alone': 1,
                    'couple': 2,
                    'family_3_4': 4,  # 3~4인 가족은 평균 4로 설정
                    'family_5plus': 5  # 5인 이상은 5로 설정
                }
                session.household_size = mate_to_size.get(mate, 2)
            
            # 반려동물 정보를 recommendation_result에 저장 (임시)
            if pet:
                if not session.recommendation_result:
                    session.recommendation_result = {}
                session.recommendation_result['has_pet'] = (pet == 'yes')
                session.recommendation_result['pet'] = pet
        elif step == 3:
            session.housing_type = step_data.get('housing_type')
            pyung = step_data.get('pyung')
            if pyung:
                session.pyung = int(pyung)
            
            # 주요 공간 정보 저장 (recommendation_result에 저장)
            main_space = step_data.get('main_space')
            if main_space:
                if not session.recommendation_result:
                    session.recommendation_result = {}
                session.recommendation_result['main_space'] = main_space
        elif step == 4:
            # 생활 패턴 정보 저장 (요리, 세탁, 미디어)
            cooking = step_data.get('cooking')
            laundry = step_data.get('laundry')
            media = step_data.get('media')
            main_space = step_data.get('main_space')  # 3단계에서 선택한 주요 공간
            
            # recommendation_result에 저장
            if not session.recommendation_result:
                session.recommendation_result = {}
            
            # 생활 패턴 데이터 저장
            if cooking:
                session.recommendation_result['cooking'] = cooking
            if laundry:
                session.recommendation_result['laundry'] = laundry
            if media:
                session.recommendation_result['media'] = media
            if main_space:
                session.recommendation_result['main_space'] = main_space
            
            print(f"[Step 4 저장] 요리: {cooking}, 세탁: {laundry}, 미디어: {media}")
        elif step == 5:
            # 우선순위 정보 저장
            priority = step_data.get('priority', [])  # 우선순위 순서 배열
            priority_map = step_data.get('priority_map', {})  # 우선순위 맵
            
            # recommendation_result에 저장
            if not session.recommendation_result:
                session.recommendation_result = {}
            
            session.recommendation_result['priority'] = priority
            session.recommendation_result['priority_map'] = priority_map
            
            # priority 필드에 첫 번째 우선순위 저장 (기존 필드 호환성)
            if priority and len(priority) > 0:
                session.priority = priority[0]
        elif step == 6:
            # 예산 범위 정보 저장
            budget = step_data.get('budget')
            
            # recommendation_result에 저장
            if not session.recommendation_result:
                session.recommendation_result = {}
            
            session.recommendation_result['budget'] = budget
            
            # budget_level 필드에 저장 (기존 필드 호환성)
            budget_mapping = {
                'budget': 'budget',
                'standard': 'standard',
                'premium': 'premium',
                'high_end': 'high_end'
            }
            session.budget_level = budget_mapping.get(budget, 'standard')
            
            # 온보딩 완료 처리
            session.is_completed = True
        
        # 진행 상태 업데이트
        session.current_step = step
        session.updated_at = timezone.now()
        session.save()
        
        print(f"\n[온보딩 저장 성공]")
        print(f"  세션 ID: {session_id}")
        print(f"  단계: {step}")
        print(f"  저장된 데이터: {step_data}")
        print(f"  현재 단계: {session.current_step}")
        print(f"  상태: {session.status}")
        
        return JsonResponse({
            'success': True,
            'session_id': session_id,
            'current_step': step,
            'next_step': min(step + 1, 6),
            'saved_data': step_data,  # 저장된 데이터 확인용
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
        
        # 2. user_profile 생성 (온보딩 데이터 포함)
        # 온보딩 데이터에서 추가 정보 추출
        onboarding_data = {
            'pet': data.get('pet'),
            'cooking': data.get('cooking'),
            'laundry': data.get('laundry'),
            'media': data.get('media'),
            'family_size': data.get('family_size', data.get('household_size')),
        }
        
        user_profile = {
            'vibe': session.vibe or 'modern',
            'household_size': session.household_size or 2,
            'housing_type': session.housing_type or 'apartment',
            'pyung': session.pyung or 25,
            'priority': session.priority or 'value',
            'budget_level': session.budget_level or 'medium',
            'categories': session.selected_categories or [],
            'main_space': 'living',
            'space_size': 'medium',
            'has_pet': onboarding_data.get('pet') == 'yes',
            'cooking': onboarding_data.get('cooking', 'sometimes'),
            'laundry': onboarding_data.get('laundry', 'weekly'),
            'media': onboarding_data.get('media', 'balanced'),
        }
        
        print(f"\n[Onboarding Complete] Session: {session_id}")
        print(f"[Profile] {user_profile}")
        
        # 3. 추천 엔진 호출
        result = recommendation_engine.get_recommendations(user_profile, limit=3)
        
        # 4. 추천 결과 저장 (온보딩 데이터 포함)
        if result['success']:
            session.recommended_products = [
                r['product_id'] for r in result['recommendations']
            ]
            # 추천 결과에 온보딩 데이터도 함께 저장
            result_with_data = result.copy()
            result_with_data['onboarding_data'] = onboarding_data
            session.recommendation_result = result_with_data
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
                'recommendation_result': session.recommendation_result,
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
