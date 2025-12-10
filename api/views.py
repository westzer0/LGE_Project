from django.http import JsonResponse, HttpResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils import timezone
import json
from .models import Product, OnboardingSession, Portfolio, ProductReview, Cart, Wishlist, ProductRecommendReason, ProductDemographics, Reservation, ProductSpec
from .views_erd_helpers import (
    save_onboarding_to_erd_models as _save_onboarding_to_erd_models,
    save_recommended_products_to_erd as _save_recommended_products_to_erd
)
from .rule_engine import build_profile, recommend_products
from .services.recommendation_engine import recommendation_engine
from .services.chatgpt_service import chatgpt_service
from .services.onboarding_db_service import onboarding_db_service
from .services.taste_calculation_service import taste_calculation_service
from .services.portfolio_service import portfolio_service
from .services.kakao_auth_service import kakao_auth_service
from .services.kakao_message_service import kakao_message_service
from .services.ai_recommendation_service import ai_recommendation_service
from .services.product_comparison_service import product_comparison_service
from .db.oracle_client import DatabaseDisabledError


def _generate_installation_notes(product_data: dict, onboarding_data: dict) -> list:
    """
    PRD: 도면 기반 설치 유의사항 자동 출력
    제품 치수 + 유저가 입력한 공간 데이터 기반으로 설치 유의사항 생성
    
    Args:
        product_data: 제품 정보
        onboarding_data: 온보딩 데이터 (공간 정보 포함)
        
    Returns:
        설치 유의사항 리스트
    """
    notes = []
    
    # 온보딩 데이터에서 공간 정보 추출
    housing_type = onboarding_data.get('housing_type', 'apartment')
    pyung = onboarding_data.get('pyung', 25)
    main_space = onboarding_data.get('main_space', 'living')
    
    # 제품 스펙 정보 확인
    product_id = product_data.get('product_id') or product_data.get('id')
    if product_id:
        try:
            product = Product.objects.get(id=product_id)
            if hasattr(product, 'spec') and product.spec:
                spec_json = product.spec.spec_json
                if isinstance(spec_json, str):
                    import json
                    try:
                        spec = json.loads(spec_json)
                    except:
                        spec = {}
                else:
                    spec = spec_json or {}
                
                # 제품 치수 정보 추출
                width = spec.get('폭', spec.get('가로', spec.get('width', 0)))
                depth = spec.get('깊이', spec.get('세로', spec.get('depth', 0)))
                height = spec.get('높이', spec.get('height', 0))
                
                # 주거 형태별 유의사항
                if housing_type == 'studio':
                    if width and width > 600:
                        notes.append("⚠️ 원룸 공간에 맞춰 600mm 이하 컴팩트 모델을 권장합니다.")
                    notes.append("원룸은 공간 효율성을 최우선으로 고려하여 설치 위치를 확인해주세요.")
                elif housing_type == 'officetel':
                    notes.append("오피스텔의 경우 엘리베이터 및 복도 폭을 확인하여 대형 가전 진입 가능 여부를 사전에 확인하세요.")
                
                # 평수 기반 유의사항
                if pyung and pyung < 20:
                    if width and width > 700:
                        notes.append("작은 공간에서는 슬림형 모델을 권장합니다.")
                elif pyung and pyung > 40:
                    notes.append("넓은 공간에서는 대형 모델도 설치 가능합니다.")
                
                # 주요 공간별 유의사항
                if isinstance(main_space, list):
                    if 'kitchen' in main_space:
                        if width and width > 900:
                            notes.append("주방 폭을 확인하여 냉장고 설치 가능 여부를 확인하세요.")
                    if 'dressing' in main_space:
                        notes.append("드레스룸의 경우 배수 및 전기 배선 위치를 확인하세요.")
        
        except Product.DoesNotExist:
            pass
        except Exception as e:
            print(f"[Installation Notes] 오류: {e}")
    
    # 기본 안내
    if not notes:
        notes.append("설치 전 현장 측량을 통해 정확한 설치 가능 여부를 확인하세요.")
    
    return notes


def health_check_view(request):
    """
    헬스체크 엔드포인트 - 배포 플랫폼에서 서버 상태 확인용
    GET /api/health/
    """
    from django.db import connection
    from django.conf import settings
    
    try:
        # 데이터베이스 연결 확인
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        
        return JsonResponse({
            'status': 'healthy',
            'database': 'connected',
            'debug': settings.DEBUG,
            'version': '1.0.0'
        }, json_dumps_params={'ensure_ascii': False})
    except Exception as e:
        return JsonResponse({
            'status': 'unhealthy',
            'database': 'disconnected',
            'error': str(e)
        }, json_dumps_params={'ensure_ascii': False}, status=503)


@require_http_methods(["GET"])
def oracle_test_view(request):
    """
    Oracle DB 연결 및 테이블 조회 테스트
    GET /api/oracle/test/
    """
    from .db.oracle_client import get_connection, fetch_all_dict, fetch_one, DatabaseDisabledError
    
    result = {
        'success': False,
        'connection': False,
        'tables': [],
        'product_count': 0,
        'member_count': 0,
        'onboarding_count': 0,
        'error': None
    }
    
    try:
        # 1. 연결 테스트
        try:
            with get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT SYSDATE FROM DUAL")
                    db_time = cur.fetchone()[0]
                    result['connection'] = True
                    result['db_time'] = str(db_time)
        except DatabaseDisabledError:
            result['error'] = 'Oracle DB가 비활성화되어 있습니다. (DISABLE_DB=true)'
            return JsonResponse(result, json_dumps_params={'ensure_ascii': False}, status=503)
        except Exception as e:
            result['error'] = f'연결 실패: {str(e)}'
            return JsonResponse(result, json_dumps_params={'ensure_ascii': False}, status=503)
        
        # 2. 테이블 목록 조회
        try:
            sql = "SELECT table_name FROM user_tables ORDER BY table_name"
            tables = fetch_all_dict(sql)
            result['tables'] = [t['TABLE_NAME'] for t in tables[:20]]  # 최대 20개
            result['table_count'] = len(tables)
        except Exception as e:
            result['table_error'] = str(e)
        
        # 3. PRODUCT 테이블 조회
        try:
            sql = "SELECT COUNT(*) as cnt FROM PRODUCT"
            count_result = fetch_one(sql)
            if count_result:
                result['product_count'] = count_result[0]
                
                # 샘플 데이터
                sql_sample = "SELECT PRODUCT_ID, PRODUCT_NAME FROM PRODUCT WHERE ROWNUM <= 3"
                samples = fetch_all_dict(sql_sample)
                result['product_samples'] = [
                    {'id': s.get('PRODUCT_ID'), 'name': s.get('PRODUCT_NAME', 'N/A')[:50]}
                    for s in samples
                ]
        except Exception as e:
            result['product_error'] = str(e)
        
        # 4. MEMBER 테이블 조회
        try:
            sql = "SELECT COUNT(*) as cnt FROM MEMBER"
            count_result = fetch_one(sql)
            if count_result:
                result['member_count'] = count_result[0]
        except Exception as e:
            result['member_error'] = str(e)
        
        # 5. ONBOARDING 테이블 조회
        try:
            sql = "SELECT COUNT(*) as cnt FROM ONBOARDING"
            count_result = fetch_one(sql)
            if count_result:
                result['onboarding_count'] = count_result[0]
        except Exception as e:
            result['onboarding_error'] = str(e)
        
        result['success'] = True
        return JsonResponse(result, json_dumps_params={'ensure_ascii': False})
        
    except Exception as e:
        result['error'] = str(e)
        return JsonResponse(result, json_dumps_params={'ensure_ascii': False}, status=500)


def index_view(request):
    """
    루트 페이지: 온보딩 설문 + 추천 결과를 보여주는 기본 화면.
    """
    return render(request, "index.html")


def react_app_view(request):
    """
    React 앱 서빙 (프로덕션)
    React 빌드 파일을 Django에서 서빙
    """
    from django.conf import settings
    from pathlib import Path
    import os
    
    # 1순위: React 빌드된 index.html 경로 (프로덕션)
    react_index_path = Path(settings.BASE_DIR) / 'staticfiles' / 'react' / 'index.html'
    if react_index_path.exists():
        with open(react_index_path, 'r', encoding='utf-8') as f:
            return HttpResponse(f.read(), content_type='text/html')
    
    # 2순위: 기본 템플릿 사용
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
    import json
    from django.utils import timezone
    from api.db.oracle_client import get_connection
    
    # 기본 컨텍스트
    context = {
        'kakao_js_key': getattr(settings, 'KAKAO_JS_KEY', ''),
        'taste_config_data': None,
        'style_analysis_message': None,
        'session_id': None
    }
    
    try:
        # session_id 또는 portfolio_id로 온보딩 세션 정보 가져오기
        session_id = request.GET.get('session_id')
        
        # context에 session_id와 portfolio_id 추가
        context['session_id'] = session_id
        
        print(f"[result_page] 요청 파라미터: session_id={session_id}", flush=True)
        
        # Oracle DB에서 온보딩 세션 정보 조회
        session_data = None
        
        with get_connection() as conn:
            with conn.cursor() as cur:
        
                # session_id로 ONBOARDING_SESSION 조회
                if session_id:
                    print(f"[result_page] Oracle DB에서 온보딩 세션 조회: session_id={session_id}", flush=True)
                    cur.execute("""
                        SELECT 
                            TASTE_ID
                        FROM ONBOARDING_SESSION
                        WHERE SESSION_ID = :session_id
                    """, {'session_id': session_id})
                    
                    row = cur.fetchone()
                    print(f"[result_page] row: {row}", flush=True)
                    if row:
                        # TASTE_ID 추출 (row[0]에서 첫 번째 컬럼 값)
                        taste_id_value = row[0] if row else None
                        taste_id = int(taste_id_value) if taste_id_value is not None else None
                        
                        session_data = {
                            'session_id': session_id,
                            'taste_id': taste_id,
                            'member_id': None,
                            'status': None,
                            'completed_at': None,
                            'recommendation_result': None
                        }
                        print(f"[result_page] 온보딩 세션 조회 성공: session_id={session_id}, taste_id={session_data['taste_id']}", flush=True)
                        
                    
        
        if session_data:
            # 먼저 recommendation_result에서 taste_config 데이터 확인 (온보딩 완료 시 저장된 데이터)
            taste_config_data_from_result = None
            
            taste_id = session_data['taste_id']
            
            if taste_id:    
                print(f"[result_page] Oracle DB에서 TASTE_ID 조회 시작: session_id={session_data['session_id']}, taste_id={taste_id}", flush=True)
                
            
                print(f"[result_page] TASTE_ID={taste_id}로 TASTE_CONFIG 조회 시작", flush=True)
                try:
                    with get_connection() as conn:
                        with conn.cursor() as cur:
                            # TASTE_CONFIG에서 모든 데이터 조회
                            cur.execute("""
                                SELECT 
                                    DESCRIPTION,
                                    RECOMMENDED_CATEGORIES,
                                    RECOMMENDED_PRODUCTS,
                                    RECOMMENDED_PRODUCT_SCORES
                                FROM TASTE_CONFIG
                                WHERE TASTE_ID = :taste_id
                            """, {'taste_id': taste_id})
                            
                            row = cur.fetchone()
                            if row:
                                # DESCRIPTION 읽기
                                description = row[0] or ""
                                
                                # RECOMMENDED_CATEGORIES CLOB 읽기
                                recommended_categories = []
                                recommended_categories_text = ""
                                if row[1]:
                                    try:
                                        clob_data = row[1]
                                        if hasattr(clob_data, 'read'):
                                            recommended_categories_text = clob_data.read()
                                        else:
                                            recommended_categories_text = str(clob_data)
                                        
                                        if recommended_categories_text and recommended_categories_text.strip():
                                            recommended_categories = json.loads(recommended_categories_text)
                                            if not isinstance(recommended_categories, list):
                                                recommended_categories = []
                                    except Exception as e:
                                        print(f"[result_page] RECOMMENDED_CATEGORIES 파싱 실패: {e}", flush=True)
                                        recommended_categories = []
                                
                                # RECOMMENDED_PRODUCTS CLOB 읽기
                                recommended_products = {}
                                if row[2]:
                                    try:
                                        clob_data = row[2]
                                        if hasattr(clob_data, 'read'):
                                            products_text = clob_data.read()
                                        else:
                                            products_text = str(clob_data)
                                        if products_text:
                                            recommended_products = json.loads(products_text)
                                            if not isinstance(recommended_products, dict):
                                                recommended_products = {}
                                    except Exception as e:
                                        print(f"[result_page] RECOMMENDED_PRODUCTS 파싱 실패: {e}", flush=True)
                                
                                # RECOMMENDED_PRODUCT_SCORES CLOB 읽기
                                recommended_product_scores = {}
                                if row[3]:
                                    try:
                                        clob_data = row[3]
                                        if hasattr(clob_data, 'read'):
                                            scores_text = clob_data.read()
                                        else:
                                            scores_text = str(clob_data)
                                        if scores_text:
                                            recommended_product_scores = json.loads(scores_text)
                                            if not isinstance(recommended_product_scores, dict):
                                                recommended_product_scores = {}
                                    except Exception as e:
                                        print(f"[result_page] RECOMMENDED_PRODUCT_SCORES 파싱 실패: {e}", flush=True)
                                
                                # recommended_categories_text 생성
                                if recommended_categories:
                                    recommended_categories_text = json.dumps(recommended_categories, ensure_ascii=False)
                                
                                print(f"[result_page] ✅ TASTE_CONFIG 조회 성공: taste_id={taste_id}, categories={len(recommended_categories)}", flush=True)
                                
                                context['taste_config_data'] = json.dumps({
                                    'description': description,
                                    'recommended_categories': recommended_categories,
                                    'recommended_categories_text': recommended_categories_text,
                                    'recommended_products': recommended_products,
                                    'recommended_product_scores': recommended_product_scores
                                }, ensure_ascii=False)
                            else:
                                print(f"[result_page] ⚠️ TASTE_CONFIG 테이블에 TASTE_ID={taste_id} 레코드가 없습니다.", flush=True)
                                context['taste_config_data'] = json.dumps({
                                    'description': '',
                                    'recommended_categories': [],
                                    'recommended_categories_text': '',
                                    'recommended_products': {},
                                    'recommended_product_scores': {}
                                }, ensure_ascii=False)
                except Exception as e:
                    print(f"[result_page] ⚠️ TASTE_CONFIG 조회 실패: {e}", flush=True)
                    import traceback
                    traceback.print_exc()
                    context['taste_config_data'] = json.dumps({
                        'description': '',
                        'recommended_categories': [],
                        'recommended_categories_text': '',
                        'recommended_products': {},
                        'recommended_product_scores': {}
                    }, ensure_ascii=False)
            else:
                print(f"[result_page] ⚠️ TASTE_ID가 None입니다. ONBOARDING_SESSION 테이블의 TASTE_ID 컬럼이 설정되지 않았을 수 있습니다.", flush=True)
                context['taste_config_data'] = json.dumps({
                    'description': '',
                    'recommended_categories': [],
                    'recommended_categories_text': '',
                    'recommended_products': {},
                    'recommended_product_scores': {}
                }, ensure_ascii=False)
        else:
            print(f"[result_page] ⚠️ 온보딩 세션을 찾을 수 없음: session_id={session_id}", flush=True)
            print(f"[result_page] ⚠️ taste_config_data가 빈 객체로 설정됩니다.", flush=True)
            # 온보딩 세션이 없어도 빈 객체라도 전달 (JavaScript에서 null 체크 방지)
            context['taste_config_data'] = json.dumps({
                'description': '',
                'recommended_categories': [],
                'recommended_categories_text': '',
                'recommended_products': {},
                'recommended_product_scores': {}
            }, ensure_ascii=False)
    
    except Exception as e:
        print(f"[result_page] 오류 발생: {e}", flush=True)
        import traceback
        traceback.print_exc()
        # 오류 발생 시에도 빈 객체라도 전달
        context['taste_config_data'] = json.dumps({
            'description': '',
            'recommended_categories': [],
            'recommended_categories_text': '',
            'recommended_products': {},
            'recommended_product_scores': {}
        }, ensure_ascii=False)
    
    # 최종 확인: taste_config_data가 설정되었는지 확인
    if context.get('taste_config_data'):
        print(f"[result_page] ✅ 최종 taste_config_data 설정 완료: {context['taste_config_data'][:1000]}...", flush=True)
    else:
        print(f"[result_page] ⚠️ taste_config_data가 None입니다! 빈 객체로 설정합니다.", flush=True)
        context['taste_config_data'] = json.dumps({
            'description': '',
            'recommended_categories': [],
            'recommended_categories_text': '',
            'recommended_products': {},
            'recommended_product_scores': {}
        }, ensure_ascii=False)
    
    return render(request, "result.html", context)


def other_recommendations_page(request):
    """다른 추천 포트폴리오 페이지"""
    return render(request, "other_recommendations.html")


def mypage(request):
    """마이페이지"""
    return render(request, "mypage.html")


def reservation_status_page(request):
    """예약 조회/변경 페이지"""
    return render(request, "reservation_status.html")


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
            'has_pet': data.get('has_pet', False),  # 반려동물 정보 추가
            'cooking': data.get('cooking', 'sometimes'),
            'laundry': data.get('laundry', 'weekly'),
            'media': data.get('media', 'balanced'),
        }
        
        print(f"\n[API] 추천 요청: {user_profile}")
        
        # 2. Service 호출 (모든 로직은 Service에서)
        # taste_id가 있으면 taste 기반 추천, 없으면 기본 추천
        taste_id = None
        if 'member_id' in data:
            from .services.taste_calculation_service import taste_calculation_service
            member_id = data.get('member_id')
            taste_id = taste_calculation_service.get_taste_for_member(member_id)
        
        result = recommendation_engine.get_recommendations(
            user_profile=user_profile,
            taste_id=taste_id
        )
        
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
    except DatabaseDisabledError as e:
        return JsonResponse({
            'success': False,
            'error': '데이터베이스 연결이 비활성화되었습니다. (DISABLE_DB=true)',
            'message': 'DB 없이 서버가 실행 중입니다. 일부 기능은 작동하지 않을 수 있습니다.',
        }, json_dumps_params={'ensure_ascii': False}, status=503)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e),
        }, json_dumps_params={'ensure_ascii': False}, status=400)


@csrf_exempt
@require_http_methods(["GET"])
def products(request):
    """
    GET /api/products/ - 제품 리스트 조회 (category, search, id 쿼리 파라미터 지원)
    
    쿼리 파라미터:
    - category: 제품 카테고리 필터
    - search: 검색어
    - id: 특정 제품 ID
    - page: 페이지 번호 (기본값: 1)
    - page_size: 페이지당 항목 수 (기본값: 20)
    """
    from django.db.models import Q
    
    category = request.GET.get('category', None)
    search_query = request.GET.get('search', None)
    product_id = request.GET.get('id', None)
    page = int(request.GET.get('page', 1))
    page_size = int(request.GET.get('page_size', 20))
    
    queryset = Product.objects.filter(is_active=True)
    
    # 제품 ID 필터 (단일 제품 조회)
    if product_id:
        try:
            product_id_int = int(product_id)
            queryset = queryset.filter(id=product_id_int)
        except ValueError:
            return JsonResponse({
                'count': 0,
                'total_count': 0,
                'page': 1,
                'page_size': page_size,
                'total_pages': 0,
                'results': []
            }, json_dumps_params={'ensure_ascii': False})
    
    # 카테고리 필터
    if category:
        queryset = queryset.filter(category=category)
    
    # 검색 필터 (제품명, 모델명, 설명에서 검색)
    if search_query:
        queryset = queryset.filter(
            Q(name__icontains=search_query) |
            Q(model_number__icontains=search_query) |
            Q(description__icontains=search_query)
        )
    
    # 총 개수
    total_count = queryset.count()
    
    # 페이지네이션
    start = (page - 1) * page_size
    end = start + page_size
    queryset = queryset.order_by('-created_at')[start:end]
    
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
        'total_count': total_count,
        'page': page,
        'page_size': page_size,
        'total_pages': (total_count + page_size - 1) // page_size,
        'results': products_list
    }, json_dumps_params={'ensure_ascii': False})


@csrf_exempt
@require_http_methods(["GET"])
def product_spec_view(request, product_id):
    """
    GET /api/products/<product_id>/spec/ - 제품 스펙 조회
    
    응답:
    {
        "success": true,
        "product_id": 1,
        "spec": {...}
    }
    """
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
def product_reviews_view(request, product_id):
    """GET /api/products/<product_id>/reviews/ - 제품 리뷰 조회 (최대 3개) - LGDX-40"""
    try:
        product = Product.objects.get(id=product_id)
        
        # 최대 3개의 리뷰만 가져오기
        reviews = ProductReview.objects.filter(product=product).order_by('-created_at')[:3]
        
        reviews_list = []
        for review in reviews:
            reviews_list.append({
                'id': review.id,
                'star': review.star,
                'review_text': review.review_text,
                'created_at': review.created_at.isoformat() if review.created_at else None,
            })
        
        return JsonResponse({
            'success': True,
            'product_id': product.id,
            'product_name': product.name,
            'count': len(reviews_list),
            'reviews': reviews_list
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
def product_recommend_reason_view(request, product_id):
    """GET /api/products/<product_id>/recommend-reason/ - 제품 추천 이유 조회"""
    try:
        product = Product.objects.get(id=product_id)
        
        # ProductRecommendReason이 있으면 반환
        if hasattr(product, 'recommend_reason') and product.recommend_reason.reason_text:
            return JsonResponse({
                'success': True,
                'product_id': product.id,
                'product_name': product.name,
                'reason_text': product.recommend_reason.reason_text,
                'source': product.recommend_reason.source,
                'created_at': product.recommend_reason.created_at.isoformat() if product.recommend_reason.created_at else None,
            }, json_dumps_params={'ensure_ascii': False})
        else:
            return JsonResponse({
                'success': True,
                'product_id': product.id,
                'product_name': product.name,
                'reason_text': '',
                'message': '추천 이유가 아직 생성되지 않았습니다.'
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
def product_demographics_view(request, product_id):
    """GET /api/products/<product_id>/demographics/ - 제품 인구통계 조회"""
    try:
        product = Product.objects.get(id=product_id)
        
        # ProductDemographics가 있으면 반환
        if hasattr(product, 'demographics'):
            demographics = product.demographics
            
            # 정규화 테이블에서 데이터 가져오기 시도
            family_types = demographics.get_family_types_from_normalized()
            house_sizes = demographics.get_house_sizes_from_normalized()
            house_types = demographics.get_house_types_from_normalized()
            
            # 정규화 테이블에 데이터가 없으면 JSONField에서 가져오기
            if not family_types:
                family_types = demographics.family_types if isinstance(demographics.family_types, list) else []
            if not house_sizes:
                house_sizes = demographics.house_sizes if isinstance(demographics.house_sizes, list) else []
            if not house_types:
                house_types = demographics.house_types if isinstance(demographics.house_types, list) else []
            
            return JsonResponse({
                'success': True,
                'product_id': product.id,
                'product_name': product.name,
                'family_types': family_types,
                'house_sizes': house_sizes,
                'house_types': house_types,
                'source': demographics.source,
                'updated_at': demographics.updated_at.isoformat() if demographics.updated_at else None,
            }, json_dumps_params={'ensure_ascii': False})
        else:
            return JsonResponse({
                'success': True,
                'product_id': product.id,
                'product_name': product.name,
                'family_types': [],
                'house_sizes': [],
                'house_types': [],
                'message': '인구통계 정보가 아직 없습니다.'
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
    """
    GET /api/products/image-by-name/?name=제품명 - 제품명으로 이미지 URL 조회
    Oracle DB의 PRODUCT_IMAGE 테이블에서 이미지 가져오기
    """
    from .utils.product_image_loader import get_image_url_from_product_image_table
    from .utils import get_image_url_from_csv  # fallback용
    
    product_name = request.GET.get('name', '').strip()
    product_id = request.GET.get('product_id', None)  # 선택적 product_id
    category_hint = request.GET.get('category', None)  # 선택적 카테고리 힌트
    
    if not product_name and not product_id:
        return JsonResponse({
            'success': False,
            'error': '제품명 또는 product_id가 필요합니다.'
        }, json_dumps_params={'ensure_ascii': False}, status=400)
    
    try:
        # 1. Oracle DB의 PRODUCT_IMAGE 테이블에서 이미지 가져오기 (우선)
        image_url = ''
        
        # product_id가 있으면 직접 조회
        if product_id:
            try:
                image_url = get_image_url_from_product_image_table(product_id=int(product_id))
            except (ValueError, TypeError):
                pass
        
        # product_id로 못 찾았거나 없으면 제품명으로 조회
        if not image_url and product_name:
            image_url = get_image_url_from_product_image_table(product_name=product_name)
        
        # 2. PRODUCT_IMAGE 테이블에 없으면 CSV에서 가져오기 (fallback)
        if not image_url and product_name:
            image_url = get_image_url_from_csv(product_name, category_hint=category_hint)
        
        # 3. 여전히 없으면 placeholder
        if not image_url or image_url.startswith('https://via.placeholder.com'):
            return JsonResponse({
                'success': False,
                'error': f'제품 이미지를 찾을 수 없습니다: {product_name or product_id}',
                'image_url': image_url if image_url else 'https://via.placeholder.com/800x600?text=Image+Not+Found'
            }, json_dumps_params={'ensure_ascii': False}, status=404)
        
        return JsonResponse({
            'success': True,
            'product_name': product_name,
            'product_id': product_id,
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
    print(f"[Onboarding Step] 요청 시작...", flush=True)
    try:
        # 요청 데이터 파싱
        try:
            print(f"[Onboarding Step] 요청 데이터 파싱 시작...", flush=True)
            if hasattr(request, 'data'):
                data = request.data
                print(f"[Onboarding Step] request.data 사용: {data}", flush=True)
            else:
                body_str = request.body.decode("utf-8")
                print(f"[Onboarding Step] request.body: {body_str[:500]}", flush=True)
                if body_str:
                    data = json.loads(body_str)
                else:
                    data = {}
        except json.JSONDecodeError as e:
            print(f"[Onboarding Step] JSON 파싱 오류: {e}", flush=True)
            return JsonResponse({
                'success': False,
                'error': f'JSON 파싱 오류: {str(e)}'
            }, status=400)
        except Exception as e:
            print(f"[Onboarding Step] 요청 데이터 처리 오류: {e}", flush=True)
            return JsonResponse({
                'success': False,
                'error': f'요청 데이터 처리 오류: {str(e)}'
            }, status=400)
        
        session_id = data.get('session_id')
        step = int(data.get('step', 1))
        step_data = data.get('data', {})
        
        print(f"[Onboarding Step] 파싱 완료 - session_id={session_id}, step={step}, step_data={step_data}", flush=True)
        
        # Step 4인 경우 laundry, media 값 상세 확인
        if step == 4:
            print(f"\n{'='*80}", flush=True)
            print(f"[DEBUG] Step 4 데이터 상세 확인", flush=True)
            print(f"{'='*80}", flush=True)
            print(f"  전체 step_data: {step_data}", flush=True)
            print(f"  step_data 타입: {type(step_data).__name__}", flush=True)
            print(f"  step_data.keys(): {list(step_data.keys()) if isinstance(step_data, dict) else 'N/A'}", flush=True)
            print(f"  step_data.get('laundry'): {step_data.get('laundry')} (타입: {type(step_data.get('laundry')).__name__})", flush=True)
            print(f"  step_data.get('media'): {step_data.get('media')} (타입: {type(step_data.get('media')).__name__})", flush=True)
            print(f"  step_data.get('cooking'): {step_data.get('cooking')} (타입: {type(step_data.get('cooking')).__name__})", flush=True)
            print(f"  'laundry' in step_data: {'laundry' in step_data if isinstance(step_data, dict) else False}", flush=True)
            print(f"  'media' in step_data: {'media' in step_data if isinstance(step_data, dict) else False}", flush=True)
            if isinstance(step_data, dict):
                for key, value in step_data.items():
                    print(f"    step_data['{key}'] = {value} (타입: {type(value).__name__})", flush=True)
            print(f"{'='*80}\n", flush=True)
        
        # 세션 ID 처리
        if not session_id:
            if step == 1:
                # Step 1: 타임스탬프 기반 정수 생성
                import time
                session_id = str(int(time.time() * 1000))  # 밀리초 단위 타임스탬프
                print(f"[Onboarding Step] Step 1: session_id가 없어서 타임스탬프로 생성: {session_id}", flush=True)
            else:
                # Step 2~7: session_id가 없으면 Step 1에서 생성된 세션을 찾아서 사용
                # Step 1에서 생성된 세션 (current_step=1 또는 가장 최근 IN_PROGRESS 세션)
                try:
                    # Step 1 세션 찾기 (current_step=1이고 IN_PROGRESS인 가장 최근 세션)
                    step1_session = OnboardingSession.objects.filter(
                        current_step=1,
                        status='in_progress'
                    ).order_by('-created_at').first()
                    
                    if step1_session:
                        session_id = step1_session.session_id
                        print(f"[Onboarding Step] Step {step}: session_id가 없어서 Step 1 세션 사용: {session_id}", flush=True)
                    else:
                        # Step 1 세션이 없으면 가장 최근 IN_PROGRESS 세션 사용
                        latest_session = OnboardingSession.objects.filter(
                            status='in_progress'
                        ).order_by('-created_at').first()
                        
                        if latest_session:
                            session_id = latest_session.session_id
                            print(f"[Onboarding Step] Step {step}: session_id가 없어서 가장 최근 세션 사용: {session_id}", flush=True)
                        else:
                            # 세션이 전혀 없으면 에러 반환
                            print(f"[Onboarding Step] ❌ Step {step}: session_id가 없고 Step 1 세션도 없습니다.", flush=True)
                            return JsonResponse({
                                'success': False,
                                'error': f'세션이 없습니다. Step 1부터 다시 시작해주세요.'
                            }, status=400)
                except Exception as e:
                    print(f"[Onboarding Step] ⚠️ Step {step}: 세션 조회 실패: {e}", flush=True)
                    return JsonResponse({
                        'success': False,
                        'error': f'세션 조회 실패: {str(e)}'
                    }, status=500)
        
        # session_id를 문자열로 변환 (VARCHAR2 타입 호환성)
        session_id = str(session_id)
        
        # 숫자 문자열인 경우 그대로 사용 (UUID 변환하지 않음)
        if session_id.isdigit():
            print(f"[Onboarding Step] 타임스탬프 기반 session_id 사용: {session_id}", flush=True)
        else:
            # UUID 형식이거나 다른 형식이면 그대로 사용
            print(f"[Onboarding Step] 기존 session_id 형식 사용: {session_id}", flush=True)
        
        # 세션 조회 또는 생성
        print(f"[Onboarding Step] 세션 조회/생성 시작 - session_id={session_id}", flush=True)
        
        if step == 1:
            # Step 1: INSERT (없으면 생성, 있으면 조회)
            session, created = OnboardingSession.objects.get_or_create(
                session_id=session_id,
                defaults={'current_step': 1, 'status': 'in_progress'}
            )
            print(f"[Onboarding Step] Step 1: 세션 {'생성됨 (INSERT)' if created else '조회됨 (이미 존재)'} - current_step={session.current_step}, status={session.status}", flush=True)
        else:
            # Step 2~7: UPDATE만 (Step 1에서 생성된 세션을 찾아서 업데이트)
            try:
                session = OnboardingSession.objects.get(session_id=session_id)
                print(f"[Onboarding Step] Step {step}: 기존 세션 조회 성공 - current_step={session.current_step}, status={session.status}", flush=True)
            except OnboardingSession.DoesNotExist:
                print(f"[Onboarding Step] ❌ Step {step}: session_id={session_id}에 해당하는 세션을 찾을 수 없습니다.", flush=True)
                return JsonResponse({
                    'success': False,
                    'error': f'세션을 찾을 수 없습니다. Step 1부터 다시 시작해주세요. (session_id: {session_id})'
                }, status=404)
        
        # 세션에서 조회한 기존 데이터 확인
        print(f"\n{'='*80}", flush=True)
        print(f"[Onboarding Step] 세션에서 조회한 기존 데이터", flush=True)
        print(f"{'='*80}", flush=True)
        print(f"  vibe: {session.vibe}", flush=True)
        print(f"  household_size: {session.household_size}", flush=True)
        print(f"  housing_type: {session.housing_type}", flush=True)
        print(f"  pyung: {session.pyung}", flush=True)
        print(f"  priority: {session.priority}", flush=True)
        print(f"  budget_level: {session.budget_level}", flush=True)
        print(f"  recommendation_result: {session.recommendation_result}", flush=True)
        if session.recommendation_result:
            print(f"    - priority: {session.recommendation_result.get('priority')}", flush=True)
            print(f"    - priority_map: {session.recommendation_result.get('priority_map')}", flush=True)
        print(f"{'='*80}\n", flush=True)
        
        # Step별 데이터 저장
        print(f"\n{'='*80}", flush=True)
        print(f"[Onboarding Step] Step {step} 데이터 저장 시작...", flush=True)
        print(f"{'='*80}", flush=True)
        print(f"  [전달받은 step_data]", flush=True)
        print(f"    step_data 전체: {step_data} (타입: {type(step_data).__name__})", flush=True)
        if step_data and isinstance(step_data, dict):
            for key, value in step_data.items():
                print(f"    {key}: {value} (타입: {type(value).__name__})", flush=True)
        else:
            print(f"    ⚠️ 경고: step_data가 dict가 아니거나 None입니다!", flush=True)
        print(f"{'='*80}\n", flush=True)
        if step == 1:
            print(f"  [Step 1] vibe 정보 저장 시작", flush=True)
            vibe = step_data.get('vibe')
            print(f"    step_data에서 가져온 vibe: {vibe} (타입: {type(vibe).__name__})", flush=True)
            session.vibe = vibe
            print(f"  [Step 1] 저장 완료 - session.vibe={session.vibe}", flush=True)
        elif step == 2:
            print(f"  [Step 2] 가구 정보 저장 시작", flush=True)
            # household_size 또는 mate 값 처리
            household_size = step_data.get('household_size')
            mate = step_data.get('mate')  # 2단계에서 전달되는 mate 값
            pet = step_data.get('pet')  # 반려동물 정보
            
            print(f"    step_data에서 가져온 household_size: {household_size}", flush=True)
            print(f"    step_data에서 가져온 mate: {mate}", flush=True)
            print(f"    step_data에서 가져온 pet: {pet}", flush=True)
            
            if household_size:
                session.household_size = int(household_size)
                print(f"    household_size 직접 설정: {session.household_size}", flush=True)
            elif mate:
                # mate 값을 household_size로 변환
                mate_to_size = {
                    'alone': 1,
                    'couple': 2,
                    'family_3_4': 4,  # 3~4인 가족은 평균 4로 설정
                    'family_5plus': 5  # 5인 이상은 5로 설정
                }
                session.household_size = mate_to_size.get(mate, 2)
                print(f"    mate에서 변환한 household_size: {session.household_size} (mate={mate})", flush=True)
            
            # 반려동물 정보 저장 (recommendation_result와 session.has_pet 모두에 저장)
            if pet:
                if not session.recommendation_result:
                    session.recommendation_result = {}
                has_pet_bool = (pet == 'yes')
                session.recommendation_result['has_pet'] = has_pet_bool
                session.recommendation_result['pet'] = pet
                # session.has_pet 필드에도 저장 (TasteConfig 매칭 시 필요)
                session.has_pet = has_pet_bool
                print(f"    pet 정보 저장: has_pet={has_pet_bool}, pet={pet}", flush=True)
            print(f"  [Step 2] 저장 완료 - household_size={session.household_size}, pet={pet}, session.has_pet={session.has_pet}", flush=True)
        elif step == 3:
            print(f"  [Step 3] 주거 정보 저장 시작", flush=True)
            housing_type = step_data.get('housing_type')
            pyung = step_data.get('pyung')
            main_space = step_data.get('main_space')
            
            print(f"    step_data에서 가져온 housing_type: {housing_type}", flush=True)
            print(f"    step_data에서 가져온 pyung: {pyung} (타입: {type(pyung).__name__})", flush=True)
            print(f"    step_data에서 가져온 main_space: {main_space} (타입: {type(main_space).__name__})", flush=True)
            
            session.housing_type = housing_type
            if pyung:
                session.pyung = int(pyung)
                print(f"    pyung 변환 후: {session.pyung}", flush=True)
            
            # 주요 공간 정보 저장 (recommendation_result에 저장)
            if main_space:
                if not session.recommendation_result:
                    session.recommendation_result = {}
                session.recommendation_result['main_space'] = main_space
                print(f"    main_space 저장: {session.recommendation_result['main_space']}", flush=True)
            print(f"  [Step 3] 저장 완료 - housing_type={session.housing_type}, pyung={session.pyung}, main_space={main_space}", flush=True)
        elif step == 4:
            print(f"\n{'='*80}", flush=True)
            print(f"  [Step 4] 생활 패턴 정보 저장 시작", flush=True)
            print(f"{'='*80}", flush=True)
            # 생활 패턴 정보 저장 (요리, 세탁, 미디어)
            cooking = step_data.get('cooking')
            laundry = step_data.get('laundry')
            media = step_data.get('media')
            main_space = step_data.get('main_space')  # 3단계에서 선택한 주요 공간
            
            print(f"    [DEBUG] step_data에서 직접 추출:", flush=True)
            print(f"      cooking = {cooking} (타입: {type(cooking).__name__}, None 여부: {cooking is None})", flush=True)
            print(f"      laundry = {laundry} (타입: {type(laundry).__name__}, None 여부: {laundry is None})", flush=True)
            print(f"      media = {media} (타입: {type(media).__name__}, None 여부: {media is None})", flush=True)
            print(f"      main_space = {main_space} (타입: {type(main_space).__name__})", flush=True)
            
            # 빈 문자열 체크
            if laundry == '':
                print(f"      ⚠️ WARNING: laundry가 빈 문자열('')입니다!", flush=True)
            if media == '':
                print(f"      ⚠️ WARNING: media가 빈 문자열('')입니다!", flush=True)
            
            # recommendation_result에 저장
            if not session.recommendation_result:
                session.recommendation_result = {}
            
            # 생활 패턴 데이터 저장 (None이 아니고 빈 문자열이 아닌 경우만 저장)
            if cooking is not None and cooking != '':
                session.recommendation_result['cooking'] = cooking
                print(f"    cooking 저장: {cooking}", flush=True)
            else:
                print(f"    ⚠️ cooking 저장 안됨: cooking={cooking} (None 또는 빈 문자열)", flush=True)
            if laundry is not None and laundry != '':
                session.recommendation_result['laundry'] = laundry
                print(f"    laundry 저장: {laundry}", flush=True)
            else:
                print(f"    ⚠️ laundry 저장 안됨: laundry={laundry} (None 또는 빈 문자열)", flush=True)
            if media is not None and media != '':
                session.recommendation_result['media'] = media
                print(f"    media 저장: {media}", flush=True)
            else:
                print(f"    ⚠️ media 저장 안됨: media={media} (None 또는 빈 문자열)", flush=True)
            if main_space:
                session.recommendation_result['main_space'] = main_space
                print(f"    main_space 저장: {main_space}", flush=True)
            
            print(f"  [Step 4] 저장 완료 - 요리: {cooking}, 세탁: {laundry}, 미디어: {media}", flush=True)
        elif step == 5:
            # 우선순위 정보 저장
            print(f"  [Step 5] 우선순위 정보 저장 시작", flush=True)
            priority = step_data.get('priority', [])  # 우선순위 순서 배열
            priority_map = step_data.get('priority_map', {})  # 우선순위 맵
            
            print(f"    step_data에서 가져온 priority: {priority} (타입: {type(priority).__name__})", flush=True)
            print(f"    step_data에서 가져온 priority_map: {priority_map} (타입: {type(priority_map).__name__})", flush=True)
            
            # recommendation_result에 저장
            if not session.recommendation_result:
                session.recommendation_result = {}
                print(f"    recommendation_result 초기화됨", flush=True)
            
            print(f"    저장 전 recommendation_result['priority']: {session.recommendation_result.get('priority')}", flush=True)
            session.recommendation_result['priority'] = priority
            session.recommendation_result['priority_map'] = priority_map
            print(f"    저장 후 recommendation_result['priority']: {session.recommendation_result.get('priority')}", flush=True)
            print(f"    저장 후 recommendation_result['priority_map']: {session.recommendation_result.get('priority_map')}", flush=True)
            
            # priority 필드에 첫 번째 우선순위 저장 (기존 필드 호환성)
            if priority and len(priority) > 0:
                session.priority = priority[0]
                print(f"    session.priority에 첫 번째 값 저장: {session.priority}", flush=True)
            else:
                print(f"    ⚠️ 경고: priority가 비어있거나 유효하지 않음", flush=True)
            
            print(f"  [Step 5] 저장 완료 - session.priority={session.priority}, priority_list={priority}", flush=True)
        elif step == 6:
            # 예산 범위 정보 저장
            print(f"  [Step 6] 예산 범위 정보 저장 시작", flush=True)
            budget = step_data.get('budget')
            
            print(f"    step_data에서 가져온 budget: {budget} (타입: {type(budget).__name__})", flush=True)
            print(f"    step_data에서 가져온 priority: {step_data.get('priority')} (타입: {type(step_data.get('priority')).__name__})", flush=True)
            
            # recommendation_result에 저장
            if not session.recommendation_result:
                session.recommendation_result = {}
                print(f"    recommendation_result 초기화됨", flush=True)
            
            # Step 5에서 저장한 priority가 있는지 확인
            existing_priority = session.recommendation_result.get('priority')
            existing_priority_map = session.recommendation_result.get('priority_map')
            print(f"    세션에서 조회한 기존 priority: {existing_priority}", flush=True)
            print(f"    세션에서 조회한 기존 priority_map: {existing_priority_map}", flush=True)
            
            # step_data에 priority가 없거나 비어있으면 기존 값 유지
            step_priority = step_data.get('priority', [])
            if not step_priority or len(step_priority) == 0:
                if existing_priority:
                    print(f"    ⚠️ step_data의 priority가 비어있음. 기존 priority 유지: {existing_priority}", flush=True)
                else:
                    print(f"    ⚠️ 경고: step_data와 세션 모두 priority가 없음!", flush=True)
            else:
                print(f"    step_data의 priority 사용: {step_priority}", flush=True)
                session.recommendation_result['priority'] = step_priority
            
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
            print(f"  [Step 6] 저장 완료 - budget_level={session.budget_level}, is_completed={session.is_completed}", flush=True)
            print(f"    최종 recommendation_result['priority']: {session.recommendation_result.get('priority')}", flush=True)
        elif step == 7:
            # Step 7: 제품 라인업 선택 (온보딩 최종 완료)
            print(f"  [Step 7] 제품 라인업 정보 저장 시작", flush=True)
            lineup = step_data.get('lineup')
            
            if lineup:
                if not session.recommendation_result:
                    session.recommendation_result = {}
                session.recommendation_result['lineup'] = lineup
                print(f"    lineup 저장: {lineup}", flush=True)
            
            # 온보딩 최종 완료 처리 및 taste_id 매칭
            session.is_completed = True
            session.status = 'completed'
            
            # Taste Config 매칭 전에 필수 필드 확인 및 보정
            print(f"  [Step 7] Taste Config 매칭 전 필드 확인...", flush=True)
            print(f"    session.vibe: {session.vibe}", flush=True)
            print(f"    session.household_size: {session.household_size}", flush=True)
            print(f"    session.has_pet: {session.has_pet}", flush=True)
            print(f"    session.priority: {session.priority}", flush=True)
            print(f"    session.budget_level: {session.budget_level}", flush=True)
            
            # has_pet이 None이면 recommendation_result에서 가져오기
            if session.has_pet is None:
                if session.recommendation_result and 'has_pet' in session.recommendation_result:
                    session.has_pet = session.recommendation_result['has_pet']
                    print(f"    ⚠️ session.has_pet이 None이어서 recommendation_result에서 복원: {session.has_pet}", flush=True)
                elif session.recommendation_result and 'pet' in session.recommendation_result:
                    pet_value = session.recommendation_result['pet']
                    session.has_pet = (pet_value == 'yes')
                    print(f"    ⚠️ session.has_pet이 None이어서 recommendation_result['pet']에서 복원: {session.has_pet}", flush=True)
            
            # Taste Config 매칭 및 taste_id 저장
            try:
                from api.services.taste_config_matching_service import TasteConfigMatchingService
                print(f"  [Step 7] Taste Config 매칭 시작...", flush=True)
                print(f"    매칭 조건: vibe={session.vibe}, household_size={session.household_size}, has_pet={session.has_pet}, priority={session.priority}, budget_level={session.budget_level}", flush=True)
                taste_config_data = TasteConfigMatchingService.get_taste_config_by_onboarding(session)
                
                if taste_config_data and taste_config_data.get('taste_id'):
                    session.taste_id = taste_config_data['taste_id']
                    print(f"  [Step 7] ✅ taste_id 저장: {session.taste_id}", flush=True)
                else:
                    print(f"  [Step 7] ⚠️ Taste Config 매칭 실패 또는 taste_id 없음", flush=True)
                    print(f"    taste_config_data: {taste_config_data}", flush=True)
            except Exception as taste_config_error:
                print(f"  [Step 7] ⚠️ Taste Config 매칭 중 오류 발생: {taste_config_error}", flush=True)
                import traceback
                traceback.print_exc()
            
            print(f"  [Step 7] 저장 완료 - lineup={lineup}, is_completed={session.is_completed}, taste_id={session.taste_id}", flush=True)
        
        # 진행 상태 업데이트
        print(f"\n{'='*80}", flush=True)
        print(f"[Onboarding Step] Django ORM 저장 시작...", flush=True)
        print(f"{'='*80}", flush=True)
        print(f"  저장 전 상태:", flush=True)
        print(f"    current_step: {session.current_step} -> {step}", flush=True)
        print(f"    priority: {session.priority}", flush=True)
        print(f"    recommendation_result['priority']: {session.recommendation_result.get('priority') if session.recommendation_result else None}", flush=True)
        
        session.current_step = step
        session.updated_at = timezone.now()
        session.save()
        
        print(f"  저장 후 상태:", flush=True)
        print(f"    current_step: {session.current_step}", flush=True)
        print(f"    status: {session.status}", flush=True)
        print(f"    priority: {session.priority}", flush=True)
        print(f"    recommendation_result['priority']: {session.recommendation_result.get('priority') if session.recommendation_result else None}", flush=True)
        print(f"{'='*80}\n", flush=True)
        
        # ============================================================
        # Oracle DB에도 저장
        # ============================================================
        try:
            print(f"[Onboarding Step] Oracle DB 저장 시작...", flush=True)
            # 세션 정보 준비
            session_status = 'IN_PROGRESS'
            if step == 6 or step == 7:
                session_status = 'COMPLETED'
            elif session.status == 'abandoned':
                session_status = 'ABANDONED'
            
            print(f"[Onboarding Step] Oracle DB 세션 정보 - session_id={session_id}, step={step}, status={session_status}", flush=True)
            print(f"[Onboarding Step] Oracle DB 저장 데이터 - vibe={session.vibe}, household_size={session.household_size}, housing_type={session.housing_type}, pyung={session.pyung}", flush=True)
            
            # main_space와 priority_list 추출 (recommendation_result에서 또는 step_data에서)
            main_space_list = []
            if step_data.get('main_space'):
                main_space_list = step_data.get('main_space') if isinstance(step_data.get('main_space'), list) else [step_data.get('main_space')]
            elif session.recommendation_result and session.recommendation_result.get('main_space'):
                main_space_list = session.recommendation_result.get('main_space')
                if not isinstance(main_space_list, list):
                    main_space_list = [main_space_list]
            
            priority_list = []
            if step_data.get('priority'):
                priority_list = step_data.get('priority') if isinstance(step_data.get('priority'), list) else [step_data.get('priority')]
            elif session.recommendation_result and session.recommendation_result.get('priority'):
                priority_list = session.recommendation_result.get('priority')
                if not isinstance(priority_list, list):
                    priority_list = [priority_list]
            
            # has_pet 추출 (recommendation_result에서)
            has_pet_value = None
            if session.recommendation_result and 'has_pet' in session.recommendation_result:
                has_pet_value = session.recommendation_result.get('has_pet')
            elif step_data.get('pet'):
                has_pet_value = (step_data.get('pet') == 'yes')
            
            # cooking, laundry, media 추출
            # Step 4에서 직접 전달된 값을 우선 사용, 없으면 recommendation_result에서 가져옴
            print(f"\n{'='*80}", flush=True)
            print(f"[Oracle DB 저장] Step {step} - cooking, laundry, media 추출 시작", flush=True)
            print(f"{'='*80}", flush=True)
            
            # 모든 step에서 step_data와 recommendation_result 확인
            print(f"  [전체 확인] step_data와 recommendation_result 상태:", flush=True)
            print(f"    step_data 타입: {type(step_data).__name__}, 내용: {step_data}", flush=True)
            print(f"    step_data.get('cooking'): {step_data.get('cooking')}", flush=True)
            print(f"    step_data.get('laundry'): {step_data.get('laundry')}", flush=True)
            print(f"    step_data.get('media'): {step_data.get('media')}", flush=True)
            print(f"    session.recommendation_result 존재: {session.recommendation_result is not None}", flush=True)
            if session.recommendation_result:
                print(f"    recommendation_result.get('cooking'): {session.recommendation_result.get('cooking')}", flush=True)
                print(f"    recommendation_result.get('laundry'): {session.recommendation_result.get('laundry')}", flush=True)
                print(f"    recommendation_result.get('media'): {session.recommendation_result.get('media')}", flush=True)
            
            if step == 4:
                # Step 4: step_data에서 직접 가져오고, 없으면 recommendation_result에서 가져옴
                print(f"  [1단계] step_data에서 직접 추출:", flush=True)
                cooking_value = step_data.get('cooking')
                print(f"    step_data.get('cooking') = {cooking_value} (타입: {type(cooking_value).__name__}, is None: {cooking_value is None})", flush=True)
                
                laundry_value = step_data.get('laundry')
                print(f"    step_data.get('laundry') = {laundry_value} (타입: {type(laundry_value).__name__}, is None: {laundry_value is None})", flush=True)
                
                media_value = step_data.get('media')
                print(f"    step_data.get('media') = {media_value} (타입: {type(media_value).__name__}, is None: {media_value is None})", flush=True)
                
                print(f"  [2단계] recommendation_result에서 fallback 확인:", flush=True)
                print(f"    session.recommendation_result 존재 여부: {session.recommendation_result is not None}", flush=True)
                if session.recommendation_result:
                    print(f"    recommendation_result 내용: {session.recommendation_result}", flush=True)
                    print(f"    recommendation_result.get('cooking'): {session.recommendation_result.get('cooking')}", flush=True)
                    print(f"    recommendation_result.get('laundry'): {session.recommendation_result.get('laundry')}", flush=True)
                    print(f"    recommendation_result.get('media'): {session.recommendation_result.get('media')}", flush=True)
                
                # Step 4: step_data에서 None이거나 빈 문자열이면 recommendation_result에서 가져옴
                if (cooking_value is None or (isinstance(cooking_value, str) and cooking_value.strip() == '')) and session.recommendation_result:
                    cooking_value = session.recommendation_result.get('cooking')
                    print(f"    cooking_value를 recommendation_result에서 가져옴: {cooking_value}", flush=True)
                
                if (laundry_value is None or (isinstance(laundry_value, str) and laundry_value.strip() == '')) and session.recommendation_result:
                    laundry_value = session.recommendation_result.get('laundry')
                    print(f"    laundry_value를 recommendation_result에서 가져옴: {laundry_value}", flush=True)
                
                if (media_value is None or (isinstance(media_value, str) and media_value.strip() == '')) and session.recommendation_result:
                    media_value = session.recommendation_result.get('media')
                    print(f"    media_value를 recommendation_result에서 가져옴: {media_value}", flush=True)
                
                print(f"  [3단계] 최종 추출된 값:", flush=True)
                print(f"    cooking_value = {cooking_value} (타입: {type(cooking_value).__name__})", flush=True)
                print(f"    laundry_value = {laundry_value} (타입: {type(laundry_value).__name__})", flush=True)
                print(f"    media_value = {media_value} (타입: {type(media_value).__name__})", flush=True)
                
                if laundry_value is None:
                    print(f"    ⚠️ ERROR: laundry_value가 None입니다! step_data와 recommendation_result 모두 확인했지만 값이 없습니다.", flush=True)
                if media_value is None:
                    print(f"    ⚠️ ERROR: media_value가 None입니다! step_data와 recommendation_result 모두 확인했지만 값이 없습니다.", flush=True)
            else:
                # Step 4가 아닌 경우: step_data에서 유효한 값이 있으면 사용, 없으면 recommendation_result에서 가져옴
                # 빈 문자열은 무시하고 이전에 저장된 값을 유지
                print(f"  [Step {step}] step_data와 recommendation_result에서 추출:", flush=True)
                
                # step_data에서 빈 문자열이 아닌 유효한 값 확인
                cooking_from_step_data = step_data.get('cooking')
                if cooking_from_step_data and cooking_from_step_data.strip() != '':
                    cooking_value = cooking_from_step_data
                    print(f"    cooking을 step_data에서 가져옴: {cooking_value}", flush=True)
                else:
                    # step_data에 값이 없거나 빈 문자열이면 recommendation_result에서 가져옴
                    cooking_value = session.recommendation_result.get('cooking') if session.recommendation_result else None
                    print(f"    cooking을 recommendation_result에서 가져옴: {cooking_value}", flush=True)
                
                laundry_from_step_data = step_data.get('laundry')
                if laundry_from_step_data and laundry_from_step_data.strip() != '':
                    laundry_value = laundry_from_step_data
                    print(f"    laundry를 step_data에서 가져옴: {laundry_value}", flush=True)
                else:
                    # step_data에 값이 없거나 빈 문자열이면 recommendation_result에서 가져옴
                    laundry_value = session.recommendation_result.get('laundry') if session.recommendation_result else None
                    print(f"    laundry를 recommendation_result에서 가져옴: {laundry_value}", flush=True)
                
                media_from_step_data = step_data.get('media')
                if media_from_step_data and media_from_step_data.strip() != '':
                    media_value = media_from_step_data
                    print(f"    media를 step_data에서 가져옴: {media_value}", flush=True)
                else:
                    # step_data에 값이 없거나 빈 문자열이면 recommendation_result에서 가져옴
                    media_value = session.recommendation_result.get('media') if session.recommendation_result else None
                    print(f"    media를 recommendation_result에서 가져옴: {media_value}", flush=True)
                
                print(f"  [Step {step}] 최종 추출된 값:", flush=True)
                print(f"    cooking_value = {cooking_value} (타입: {type(cooking_value).__name__})", flush=True)
                print(f"    laundry_value = {laundry_value} (타입: {type(laundry_value).__name__})", flush=True)
                print(f"    media_value = {media_value} (타입: {type(media_value).__name__})", flush=True)
                if laundry_value is None:
                    print(f"    ⚠️ WARNING: laundry_value가 None입니다! step_data와 recommendation_result 모두에 값이 없습니다.", flush=True)
                if media_value is None:
                    print(f"    ⚠️ WARNING: media_value가 None입니다! step_data와 recommendation_result 모두에 값이 없습니다.", flush=True)
            
            # 모든 step에서 최종 값 출력
            print(f"  [최종 추출 결과] Step {step}:", flush=True)
            print(f"    cooking_value = {cooking_value} (타입: {type(cooking_value).__name__})", flush=True)
            print(f"    laundry_value = {laundry_value} (타입: {type(laundry_value).__name__})", flush=True)
            print(f"    media_value = {media_value} (타입: {type(media_value).__name__})", flush=True)
            print(f"{'='*80}\n", flush=True)
            
            # Oracle DB 세션 저장/업데이트
            print(f"\n{'='*80}", flush=True)
            print(f"[Oracle DB 저장] create_or_update_session 호출 전 최종 확인", flush=True)
            print(f"{'='*80}", flush=True)
            print(f"  전달할 파라미터:", flush=True)
            print(f"    session_id = {session_id}", flush=True)
            print(f"    current_step = {step}", flush=True)
            print(f"    cooking = {cooking_value} (타입: {type(cooking_value).__name__})", flush=True)
            print(f"    laundry = {laundry_value} (타입: {type(laundry_value).__name__})", flush=True)
            print(f"    media = {media_value} (타입: {type(media_value).__name__})", flush=True)
            print(f"{'='*80}\n", flush=True)
            
            onboarding_db_service.create_or_update_session(
                session_id=session_id,
                user_id=data.get('user_id'),
                member_id=data.get('member_id'),
                current_step=step,
                status=session_status,
                vibe=session.vibe,
                household_size=session.household_size,
                housing_type=session.housing_type,
                pyung=session.pyung,
                priority=session.priority,
                budget_level=session.budget_level,
                has_pet=has_pet_value,  # 정규화 테이블에 저장하기 위해 추가
                main_space=main_space_list,  # 정규화 테이블에 저장하기 위해 추가
                priority_list=priority_list,  # 정규화 테이블에 저장하기 위해 추가
                cooking=cooking_value,  # 생활 패턴 저장
                laundry=laundry_value,
                media=media_value,
                selected_categories=getattr(session, 'selected_categories', []),
                recommended_products=getattr(session, 'recommended_products', []),
                recommendation_result=session.recommendation_result,
                taste_id=session.taste_id  # Step 7에서 매칭된 taste_id 저장
            )
            
            # Step별 사용자 응답 저장
            if step == 1:
                # Step 1: vibe
                if step_data.get('vibe'):
                    onboarding_db_service.save_user_response(
                        session_id=session_id,
                        step_number=1,
                        question_type='vibe',
                        answer_value=step_data.get('vibe')
                    )
            
            elif step == 2:
                # Step 2: mate
                if step_data.get('mate'):
                    onboarding_db_service.save_user_response(
                        session_id=session_id,
                        step_number=2,
                        question_type='mate',
                        answer_value=step_data.get('mate')
                    )
                # Step 2: pet
                if step_data.get('pet'):
                    onboarding_db_service.save_user_response(
                        session_id=session_id,
                        step_number=2,
                        question_type='pet',
                        answer_value=step_data.get('pet')
                    )
            
            elif step == 3:
                # Step 3: housing_type
                if step_data.get('housing_type'):
                    onboarding_db_service.save_user_response(
                        session_id=session_id,
                        step_number=3,
                        question_type='housing_type',
                        answer_value=step_data.get('housing_type')
                    )
                # Step 3: main_space (다중 선택)
                if step_data.get('main_space'):
                    main_spaces = step_data.get('main_space')
                    if isinstance(main_spaces, list):
                        onboarding_db_service.save_multiple_responses(
                            session_id=session_id,
                            step_number=3,
                            question_type='main_space',
                            answer_values=main_spaces
                        )
                    else:
                        onboarding_db_service.save_user_response(
                            session_id=session_id,
                            step_number=3,
                            question_type='main_space',
                            answer_value=main_spaces
                        )
                # Step 3: pyung (텍스트 입력)
                if step_data.get('pyung'):
                    onboarding_db_service.save_user_response(
                        session_id=session_id,
                        step_number=3,
                        question_type='pyung',
                        answer_value=str(step_data.get('pyung')),
                        answer_text=str(step_data.get('pyung'))
                    )
            
            elif step == 4:
                # Step 4: cooking
                if step_data.get('cooking'):
                    onboarding_db_service.save_user_response(
                        session_id=session_id,
                        step_number=4,
                        question_type='cooking',
                        answer_value=step_data.get('cooking')
                    )
                # Step 4: laundry
                if step_data.get('laundry'):
                    onboarding_db_service.save_user_response(
                        session_id=session_id,
                        step_number=4,
                        question_type='laundry',
                        answer_value=step_data.get('laundry')
                    )
                # Step 4: media
                if step_data.get('media'):
                    onboarding_db_service.save_user_response(
                        session_id=session_id,
                        step_number=4,
                        question_type='media',
                        answer_value=step_data.get('media')
                    )
            
            elif step == 5:
                # Step 5: priority (다중 선택, 순서 중요)
                if step_data.get('priority'):
                    priorities = step_data.get('priority')
                    if isinstance(priorities, list):
                        onboarding_db_service.save_multiple_responses(
                            session_id=session_id,
                            step_number=5,
                            question_type='priority',
                            answer_values=priorities
                        )
                    else:
                        onboarding_db_service.save_user_response(
                            session_id=session_id,
                            step_number=5,
                            question_type='priority',
                            answer_value=priorities
                        )
            
            elif step == 6:
                # Step 6: budget
                if step_data.get('budget'):
                    onboarding_db_service.save_user_response(
                        session_id=session_id,
                        step_number=6,
                        question_type='budget',
                        answer_value=step_data.get('budget')
                    )
            
            print(f"[Onboarding Step] Oracle DB 사용자 응답 저장 완료 (Step {step})", flush=True)
            print(f"\n{'='*80}", flush=True)
            print(f"[Onboarding Step] ✅ Oracle DB 저장 성공", flush=True)
            print(f"{'='*80}", flush=True)
            print(f"  세션 ID: {session_id}", flush=True)
            print(f"  단계: {step}", flush=True)
            print(f"{'='*80}\n", flush=True)
        
        except Exception as oracle_error:
            # Oracle DB 저장 실패해도 Django DB 저장은 성공했으므로 계속 진행
            error_type = type(oracle_error).__name__
            error_message = str(oracle_error)
            # Oracle 에러 코드 추출 (예: ORA-00904)
            error_code = ""
            if "ORA-" in error_message:
                import re
                match = re.search(r'ORA-\d+', error_message)
                if match:
                    error_code = match.group()
            
            print(f"\n{'='*80}", flush=True)
            print(f"[Onboarding Step] ❌ Oracle DB 저장 실패", flush=True)
            print(f"{'='*80}", flush=True)
            print(f"  세션 ID: {session_id}", flush=True)
            print(f"  단계: {step}", flush=True)
            if error_code:
                print(f"  에러 코드: {error_code}", flush=True)
            print(f"  에러 타입: {error_type}", flush=True)
            print(f"  에러 메시지: {error_message}", flush=True)
            print(f"{'='*80}\n", flush=True)
            import traceback
            traceback.print_exc()
        
        print(f"\n{'='*80}", flush=True)
        print(f"[Onboarding Step] Django ORM 저장 성공", flush=True)
        print(f"{'='*80}", flush=True)
        print(f"  세션 ID: {session_id}", flush=True)
        print(f"  단계: {step}", flush=True)
        print(f"  현재 단계: {session.current_step}", flush=True)
        print(f"  상태: {session.status}", flush=True)
        print(f"  priority: {session.priority}", flush=True)
        print(f"  recommendation_result['priority']: {session.recommendation_result.get('priority') if session.recommendation_result else None}", flush=True)
        print(f"{'='*80}\n", flush=True)
        
        return JsonResponse({
            'success': True,
            'session_id': session_id,
            'current_step': step,
            'next_step': min(step + 1, 6),
            'saved_data': step_data,  # 저장된 데이터 확인용
        }, json_dumps_params={'ensure_ascii': False})
    
    except DatabaseDisabledError as e:
        return JsonResponse({
            'success': False,
            'error': '데이터베이스 연결이 비활성화되었습니다. (DISABLE_DB=true)',
            'message': 'DB 없이 서버가 실행 중입니다. 온보딩 데이터는 Django DB에만 저장됩니다.',
        }, json_dumps_params={'ensure_ascii': False}, status=503)
    except Exception as e:
        print(f"\n{'='*80}", flush=True)
        print(f"[Onboarding Step] ❌ 전체 프로세스 중 예외 발생!", flush=True)
        print(f"{'='*80}", flush=True)
        print(f"  예외 타입: {type(e).__name__}", flush=True)
        print(f"  예외 메시지: {str(e)}", flush=True)
        import traceback
        print(f"  전체 트레이스백:", flush=True)
        traceback.print_exc()
        print(f"{'='*80}\n", flush=True)
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, json_dumps_params={'ensure_ascii': False}, status=400)


@csrf_exempt
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
    print(f"[Onboarding Complete] 요청 시작...", flush=True)
    try:
        # 요청 데이터 파싱
        try:
            print(f"[Onboarding Complete] 요청 데이터 파싱 시작...", flush=True)
            if hasattr(request, 'data'):
                data = request.data
            else:
                body = request.body.decode("utf-8")
                print(f"[Onboarding Complete] 요청 본문: {body[:500]}")
                data = json.loads(body)
        except json.JSONDecodeError as e:
            print(f"[Onboarding Complete] JSON 파싱 오류: {e}")
            return JsonResponse({
                'success': False,
                'error': f'잘못된 JSON 형식: {str(e)}'
            }, json_dumps_params={'ensure_ascii': False}, status=400)
        except Exception as e:
            print(f"[Onboarding Complete] 요청 파싱 오류: {e}")
            return JsonResponse({
                'success': False,
                'error': f'요청 처리 실패: {str(e)}'
            }, json_dumps_params={'ensure_ascii': False}, status=400)
        
        session_id = data.get('session_id')
        
        if not session_id:
            print("[Onboarding Complete] session_id 누락")
            return JsonResponse({
                'success': False,
                'error': 'session_id 필수'
            }, json_dumps_params={'ensure_ascii': False}, status=400)
        
        # 1. OnboardingSession 저장
        try:
            # household_size 변환 (문자열 "2" -> 정수 2)
            household_size = data.get('household_size', 2)
            if isinstance(household_size, str):
                household_size = int(household_size.replace('인', '').replace(' 이상', '').strip()) if household_size.strip() else 2
            
            # pyung 변환
            pyung = data.get('pyung', 25)
            if isinstance(pyung, str):
                pyung = int(pyung.replace('평', '').strip()) if pyung.strip() else 25
            
            # Step 2: has_pet 처리
            has_pet = data.get('has_pet')
            if has_pet is None:
                # 기존 호환성: pet 필드 확인
                pet_value = data.get('pet', 'no')
                has_pet = pet_value in ['yes', 'Y', True, 'true', 'True']
            
            # Step 3: main_space 처리
            main_space = data.get('main_space', [])
            if isinstance(main_space, str):
                try:
                    import json
                    main_space = json.loads(main_space)
                except:
                    main_space = [main_space] if main_space else ['living']
            if not isinstance(main_space, list):
                main_space = ['living']
            
            # Step 5: priority_list 처리
            priority_list = data.get('priority_list', [])
            if isinstance(priority_list, str):
                try:
                    import json
                    priority_list = json.loads(priority_list)
                except:
                    priority_list = [priority_list] if priority_list else []
            if not isinstance(priority_list, list):
                priority_list = [data.get('priority', 'value')]
            if len(priority_list) == 0:
                priority_list = [data.get('priority', 'value')]
            
            session, _ = OnboardingSession.objects.update_or_create(
                session_id=session_id,
                defaults={
                    # Step 1
                    'vibe': data.get('vibe', 'modern'),
                    # Step 2
                    'household_size': int(household_size),
                    'has_pet': has_pet,
                    # Step 3
                    'housing_type': data.get('housing_type', 'apartment'),
                    'main_space': main_space,
                    'pyung': int(pyung),
                    # Step 4
                    'cooking': data.get('cooking', 'sometimes'),
                    'laundry': data.get('laundry', 'weekly'),
                    'media': data.get('media', 'balanced'),
                    # Step 5
                    'priority': data.get('priority', 'value'),
                    'priority_list': priority_list,
                    # Step 6
                    'budget_level': data.get('budget_level', 'medium'),
                    # 카테고리
                    'selected_categories': data.get('selected_categories', []),
                    'current_step': 6,
                    'status': 'completed',
                    'completed_at': timezone.now(),
                }
            )
            print(f"[Onboarding Complete] 세션 저장 완료: {session_id}")
            
            # ERD 기반 모델에 데이터 저장
            try:
                _save_onboarding_to_erd_models(session, data)
                print(f"[Onboarding Complete] ERD 모델 저장 완료")
            except Exception as erd_error:
                print(f"[Onboarding Complete] ERD 모델 저장 실패 (계속 진행): {erd_error}")
                import traceback
                traceback.print_exc()
                # ERD 저장 실패해도 계속 진행 (하위 호환성)
            
            # Taste Config 매칭 및 데이터 조회
            taste_config_data = None
            try:
                from api.services.taste_config_matching_service import TasteConfigMatchingService
                print(f"[Onboarding Complete] Taste Config 매칭 시작...", flush=True)
                taste_config_data = TasteConfigMatchingService.get_taste_config_by_onboarding(session)
                
                if taste_config_data:
                    # taste_id를 session에 저장
                    if taste_config_data.get('taste_id'):
                        session.taste_id = taste_config_data['taste_id']
                        print(f"[Onboarding Complete] ✅ taste_id 저장: {session.taste_id}", flush=True)
                    
                    # 조회된 데이터를 session의 recommendation_result에 저장
                    if not session.recommendation_result:
                        session.recommendation_result = {}
                    session.recommendation_result['taste_config'] = taste_config_data
                    session.save()
                    
                    print(f"[Onboarding Complete] ✅ Taste Config 매칭 완료: taste_id={taste_config_data.get('taste_id')}", flush=True)
                    print(f"  - categories: {len(taste_config_data.get('recommended_categories', []))}개", flush=True)
                    print(f"  - products: {len(taste_config_data.get('recommended_products', {}))}개 카테고리", flush=True)
                else:
                    print(f"[Onboarding Complete] ⚠️ Taste Config 매칭 실패 (매칭되는 데이터 없음)", flush=True)
            except Exception as taste_config_error:
                print(f"[Onboarding Complete] ⚠️ Taste Config 매칭 중 오류 발생 (계속 진행): {taste_config_error}", flush=True)
                import traceback
                traceback.print_exc()
                # 실패해도 계속 진행
            
            # Oracle DB에도 저장 (기본 정보)
            try:
                print(f"[Onboarding Complete] Oracle DB 저장 시작 (기본 정보)...", flush=True)
                print(f"[Oracle DB] session_id={session_id}, vibe={session.vibe}, household_size={session.household_size}", flush=True)
                
                # main_space와 priority_list 처리
                main_space_list = session.main_space
                if isinstance(main_space_list, str):
                    try:
                        import json
                        main_space_list = json.loads(main_space_list)
                    except:
                        main_space_list = [main_space_list] if main_space_list else []
                elif not isinstance(main_space_list, list):
                    main_space_list = [main_space_list] if main_space_list else []
                
                priority_list_data = session.priority_list
                if isinstance(priority_list_data, str):
                    try:
                        import json
                        priority_list_data = json.loads(priority_list_data)
                    except:
                        priority_list_data = [priority_list_data] if priority_list_data else []
                elif not isinstance(priority_list_data, list):
                    priority_list_data = [priority_list_data] if priority_list_data else []
                
                # selected_categories는 data에서 직접 가져옴 (모델 필드 없음)
                selected_categories_list = data.get('selected_categories', [])
                if not isinstance(selected_categories_list, list):
                    selected_categories_list = [selected_categories_list] if selected_categories_list else []
                
                print(f"[Oracle DB] main_space={main_space_list}, priority_list={priority_list_data}, categories={selected_categories_list}", flush=True)
                print(f"[Oracle DB] selected_categories 전달값: {selected_categories_list} (타입: {type(selected_categories_list).__name__}, 길이: {len(selected_categories_list)})", flush=True)
                print(f"[Oracle DB] taste_id 전달값: {session.taste_id}", flush=True)
                
                onboarding_db_service.create_or_update_session(
                    session_id=session_id,
                    user_id=data.get('user_id', data.get('member_id')),
                    member_id=data.get('member_id'),
                    current_step=6,
                    status='COMPLETED',
                    vibe=session.vibe,
                    household_size=session.household_size,
                    has_pet=session.has_pet,
                    housing_type=session.housing_type,
                    main_space=main_space_list,
                    pyung=session.pyung,
                    cooking=session.cooking,
                    laundry=session.laundry,
                    media=session.media,
                    priority=session.priority,
                    priority_list=priority_list_data,
                    budget_level=session.budget_level,
                    selected_categories=selected_categories_list,
                    taste_id=session.taste_id,  # Taste Config 매칭 결과 저장
                )
                print(f"\n{'='*80}", flush=True)
                print(f"[Onboarding Complete] ✅ Oracle DB 저장 성공 (기본 정보)", flush=True)
                print(f"{'='*80}", flush=True)
                print(f"  세션 ID: {session_id}", flush=True)
                print(f"{'='*80}\n", flush=True)
            except Exception as oracle_error:
                error_type = type(oracle_error).__name__
                error_message = str(oracle_error)
                # Oracle 에러 코드 추출 (예: ORA-00904)
                error_code = ""
                if "ORA-" in error_message:
                    import re
                    match = re.search(r'ORA-\d+', error_message)
                    if match:
                        error_code = match.group()
                
                print(f"\n{'='*80}", flush=True)
                print(f"[Onboarding Complete] ❌ Oracle DB 저장 실패 (기본 정보)", flush=True)
                print(f"{'='*80}", flush=True)
                print(f"  세션 ID: {session_id}", flush=True)
                if error_code:
                    print(f"  에러 코드: {error_code}", flush=True)
                print(f"  에러 타입: {error_type}", flush=True)
                print(f"  에러 메시지: {error_message}", flush=True)
                print(f"{'='*80}\n", flush=True)
                import traceback
                traceback.print_exc()
                # Oracle 저장 실패해도 계속 진행
            
        except Exception as e:
            print(f"[Onboarding Complete] 세션 저장 실패: {e}")
            import traceback
            traceback.print_exc()
            return JsonResponse({
                'success': False,
                'error': f'세션 저장 실패: {str(e)}'
            }, json_dumps_params={'ensure_ascii': False}, status=500)
        
        # 2. user_profile 생성 (온보딩 데이터 포함)
        # 온보딩 데이터에서 추가 정보 추출
        onboarding_data = {
            'has_pet': session.has_pet if session.has_pet is not None else (data.get('has_pet') or data.get('pet') == 'yes'),
            'cooking': session.cooking or data.get('cooking', 'sometimes'),
            'laundry': session.laundry or data.get('laundry', 'weekly'),
            'media': session.media or data.get('media', 'balanced'),
            'main_space': session.main_space if isinstance(session.main_space, list) else (data.get('main_space', ['living'])),
            'priority_list': session.priority_list if isinstance(session.priority_list, list) else (data.get('priority_list', [])),
            'family_size': data.get('family_size', data.get('household_size')),
        }
        
        user_profile = {
            'vibe': session.vibe or 'modern',
            'household_size': session.household_size or 2,
            'housing_type': session.housing_type or 'apartment',
            'pyung': session.pyung or 25,
            'priority': session.priority or 'value',
            'budget_level': session.budget_level or 'medium',
            'categories': getattr(session, 'selected_categories', []) or [],
            'main_space': 'living',
            'space_size': 'medium',
            'has_pet': onboarding_data.get('pet') == 'yes',
            'cooking': onboarding_data.get('cooking', 'sometimes'),
            'laundry': onboarding_data.get('laundry', 'weekly'),
            'media': onboarding_data.get('media', 'balanced'),
        }
        
        print(f"\n[Onboarding Complete] Session: {session_id}")
        print(f"[Profile] {user_profile}")
        
        # 3. Taste ID 가져오기 (우선순위: TASTE_CONFIG 매칭 > 계산 fallback)
        member_id = data.get('member_id')
        taste_id = session.taste_id  # TasteConfig 매칭으로 이미 가져온 값 사용
        
        # 온보딩 데이터 준비 (Taste 계산용 및 추천 엔진용)
        onboarding_data_for_taste = {
            'vibe': session.vibe,
            'household_size': session.household_size,
            'housing_type': session.housing_type,
            'pyung': session.pyung,
            'budget_level': session.budget_level,
            'priority': session.priority if isinstance(session.priority, list) else [session.priority] if session.priority else ['value'],
            'has_pet': onboarding_data.get('pet') == 'yes',
            'main_space': data.get('main_space', []),
            'cooking': onboarding_data.get('cooking', 'sometimes'),
            'laundry': onboarding_data.get('laundry', 'weekly'),
            'media': onboarding_data.get('media', 'balanced'),
        }
        
        # TasteConfig 매칭이 실패했거나 taste_id가 없는 경우에만 계산 (fallback)
        if not taste_id:
            print(f"[Onboarding Complete] ⚠️ TasteConfig 매칭 실패, 계산 방식으로 fallback...", flush=True)
            
            # Taste 계산 (member_id가 있으면 저장, 없으면 계산만)
            if member_id:
                try:
                    taste_id = taste_calculation_service.calculate_and_save_taste(
                        member_id=member_id,
                        onboarding_data=onboarding_data_for_taste
                    )
                    print(f"[Taste 계산 완료 (fallback)] Member: {member_id}, Taste ID: {taste_id}")
                except Exception as taste_error:
                    print(f"[Taste 계산 실패] {str(taste_error)}")
                    # 계산 실패 시 온보딩 데이터로 직접 계산
                    try:
                        from api.utils.taste_classifier import taste_classifier
                        taste_id = taste_classifier.calculate_taste_from_onboarding(onboarding_data_for_taste)
                        print(f"[Taste 계산 (fallback)] Taste ID: {taste_id}")
                    except:
                        pass
            else:
                # member_id가 없어도 taste 계산 (세션 기반)
                try:
                    from api.utils.taste_classifier import taste_classifier
                    taste_id = taste_classifier.calculate_taste_from_onboarding(onboarding_data_for_taste)
                    print(f"[Taste 계산 (fallback, 세션 기반)] Taste ID: {taste_id}")
                except Exception as taste_error:
                    print(f"[Taste 계산 실패] {str(taste_error)}")
            
            # Fallback으로 계산된 taste_id를 session에 저장
            if taste_id:
                session.taste_id = taste_id
                session.save()
                print(f"[Onboarding Complete] ✅ Fallback 계산 taste_id를 세션에 저장: {taste_id}", flush=True)
        else:
            print(f"[Onboarding Complete] ✅ Taste ID (TASTE_CONFIG 매칭): {taste_id}", flush=True)
        
        # 4. 추천 엔진 호출 (taste_id 기반으로 category 선택 및 제품 추천)
        try:
            print(f"[Onboarding Complete] 추천 엔진 호출 시작...")
            result = recommendation_engine.get_recommendations(
                user_profile=user_profile,
                taste_id=taste_id,
                taste_info=onboarding_data_for_taste  # category 점수 산출에 사용
            )
            print(f"[Onboarding Complete] 추천 엔진 결과: success={result.get('success')}, count={result.get('count', 0)}")
        except Exception as e:
            print(f"[Onboarding Complete] 추천 엔진 오류: {e}")
            import traceback
            traceback.print_exc()
            return JsonResponse({
                'success': False,
                'error': f'추천 엔진 오류: {str(e)}'
            }, json_dumps_params={'ensure_ascii': False}, status=500)
        
        # 5. 추천 결과 저장 (온보딩 데이터 포함)
        if result.get('success'):
            session.recommended_products = [
                r['product_id'] for r in result['recommendations']
            ]
            # 추천 결과에 온보딩 데이터도 함께 저장
            result_with_data = result.copy()
            result_with_data['onboarding_data'] = onboarding_data
            session.recommendation_result = result_with_data
            session.save()
            
            # ERD 기반 추천 제품 저장 (OnboardSessRecProducts)
            try:
                _save_recommended_products_to_erd(session, result['recommendations'])
                print(f"[Onboarding Complete] 추천 제품 ERD 저장 완료")
            except Exception as erd_error:
                print(f"[Onboarding Complete] 추천 제품 ERD 저장 실패 (계속 진행): {erd_error}")
            
            print(f"[Success] {len(result['recommendations'])}개 제품 추천됨")
            
            # Oracle DB에 추천 결과 포함해서 최종 저장
            try:
                print(f"[Onboarding Complete] Oracle DB 최종 저장 시작 (추천 결과 포함)...")
                print(f"[Oracle DB] 추천 제품 수: {len(session.recommended_products) if session.recommended_products else 0}")
                
                # main_space와 priority_list 처리
                main_space_list = session.main_space
                if isinstance(main_space_list, str):
                    try:
                        import json
                        main_space_list = json.loads(main_space_list)
                    except:
                        main_space_list = [main_space_list] if main_space_list else []
                elif not isinstance(main_space_list, list):
                    main_space_list = [main_space_list] if main_space_list else []
                
                priority_list_data = session.priority_list
                if isinstance(priority_list_data, str):
                    try:
                        import json
                        priority_list_data = json.loads(priority_list_data)
                    except:
                        priority_list_data = [priority_list_data] if priority_list_data else []
                elif not isinstance(priority_list_data, list):
                    priority_list_data = [priority_list_data] if priority_list_data else []
                
                # selected_categories는 data에서 직접 가져옴 (모델 필드 없음)
                selected_categories_list = data.get('selected_categories', [])
                if not isinstance(selected_categories_list, list):
                    selected_categories_list = [selected_categories_list] if selected_categories_list else []
                
                # recommended_products는 추천 결과에서 직접 추출 (모델 필드 없음)
                recommended_products_list = []
                if result.get('success') and result.get('recommendations'):
                    recommended_products_list = [
                        r.get('product_id') or r.get('id')
                        for r in result['recommendations']
                        if r.get('product_id') or r.get('id')
                    ]
                
                print(f"[Oracle DB] 추천 제품 ID 목록: {recommended_products_list[:5]}..." if len(recommended_products_list) > 5 else f"[Oracle DB] 추천 제품 ID 목록: {recommended_products_list}")
                print(f"[Oracle DB] recommended_products 전달값: {recommended_products_list[:10]} (타입: {type(recommended_products_list).__name__}, 길이: {len(recommended_products_list)})", flush=True)
                print(f"[Oracle DB] taste_id 전달값: {session.taste_id}", flush=True)
                
                onboarding_db_service.create_or_update_session(
                    session_id=session_id,
                    user_id=data.get('user_id', data.get('member_id')),
                    current_step=6,
                    status='COMPLETED',
                    vibe=session.vibe,
                    household_size=session.household_size,
                    has_pet=session.has_pet,
                    housing_type=session.housing_type,
                    main_space=main_space_list,
                    pyung=session.pyung,
                    cooking=session.cooking,
                    laundry=session.laundry,
                    media=session.media,
                    priority=session.priority,
                    priority_list=priority_list_data,
                    budget_level=session.budget_level,
                    selected_categories=selected_categories_list,
                    recommended_products=recommended_products_list,
                    recommendation_result=session.recommendation_result if session.recommendation_result else {},
                    taste_id=session.taste_id,  # Taste Config 매칭 결과 저장
                )
                print(f"\n{'='*80}", flush=True)
                print(f"[Onboarding Complete] ✅ Oracle DB 저장 성공 (추천 결과 포함)", flush=True)
                print(f"{'='*80}", flush=True)
                print(f"  세션 ID: {session_id}", flush=True)
                print(f"{'='*80}\n", flush=True)
            except Exception as oracle_error:
                error_type = type(oracle_error).__name__
                error_message = str(oracle_error)
                # Oracle 에러 코드 추출 (예: ORA-00904)
                error_code = ""
                if "ORA-" in error_message:
                    import re
                    match = re.search(r'ORA-\d+', error_message)
                    if match:
                        error_code = match.group()
                
                print(f"\n{'='*80}", flush=True)
                print(f"[Onboarding Complete] ❌ Oracle DB 저장 실패 (추천 결과 포함)", flush=True)
                print(f"{'='*80}", flush=True)
                print(f"  세션 ID: {session_id}", flush=True)
                if error_code:
                    print(f"  에러 코드: {error_code}", flush=True)
                print(f"  에러 타입: {error_type}", flush=True)
                print(f"  에러 메시지: {error_message}", flush=True)
                print(f"{'='*80}\n", flush=True)
                import traceback
                traceback.print_exc()
                # Oracle 저장 실패해도 계속 진행
            
            
            
            # Taste 정보를 응답에 포함 (이미 위에서 계산됨)
            if taste_id:
                result_with_data['taste_id'] = taste_id
            
            # 응답에 포트폴리오 정보 포함
            response_data = {
                'success': True,
                'session_id': session_id,
                'recommendations': result['recommendations'],
            }
            
            if portfolio_id:
                response_data['portfolio_id'] = portfolio_id
                response_data['style_analysis'] = portfolio_result.get('style_analysis')
                response_data['total_price'] = portfolio_result.get('total_price')
                response_data['total_discount_price'] = portfolio_result.get('total_discount_price')
            
            return JsonResponse(response_data, json_dumps_params={'ensure_ascii': False})
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
                'selected_categories': getattr(session, 'selected_categories', []),
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
    포트폴리오 저장 API (PRD 기반)
    
    POST /api/portfolio/save/
    {
        "session_id": "abc12345",  # 온보딩 세션 ID (필수)
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
        
        session_id = data.get('session_id')
        user_id = data.get('user_id', f"guest_{timezone.now().strftime('%Y%m%d%H%M%S')}")
        
        # session_id가 있으면 포트폴리오 서비스 사용 (PRD 로직)
        if session_id:
            result = portfolio_service.create_portfolio_from_onboarding(
                session_id=session_id,
                user_id=user_id
            )
            
            if result.get('success'):
                return JsonResponse({
                    'success': True,
                    'portfolio_id': result.get('portfolio_id'),
                    'internal_key': result.get('internal_key'),
                    'style_analysis': result.get('style_analysis'),
                    'recommendations': result.get('recommendations'),
                    'total_price': result.get('total_price'),
                    'total_discount_price': result.get('total_discount_price'),
                    'match_score': result.get('match_score'),
                    'message': '포트폴리오가 생성되었습니다.',
                    'share_url': f'/portfolio/{result.get("portfolio_id")}/'
                }, json_dumps_params={'ensure_ascii': False})
            else:
                return JsonResponse({
                    'success': False,
                    'error': result.get('error', '포트폴리오 생성 실패')
                }, json_dumps_params={'ensure_ascii': False}, status=400)
        
        # 기존 방식 (하위 호환성)
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
            'internal_key': portfolio.internal_key,  # LGDX-3
            'message': '포트폴리오가 저장되었습니다.',
            'share_url': f'/portfolio/{portfolio.portfolio_id}/'
        }, json_dumps_params={'ensure_ascii': False})
    
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, json_dumps_params={'ensure_ascii': False}, status=400)


@csrf_exempt
@require_http_methods(["GET"])
def portfolio_detail_view(request, portfolio_id):
    """
    포트폴리오 상세 조회 API
    
    GET /api/portfolio/<portfolio_id>/
    portfolio_id는 portfolio_id 또는 internal_key 모두 지원 (LGDX-3)
    """
    try:
        print(f"[Portfolio Detail] 조회 요청: {portfolio_id}")
        
        # portfolio_id 또는 internal_key로 조회 시도
        portfolio = None
        try:
            portfolio = Portfolio.objects.get(portfolio_id=portfolio_id)
            print(f"[Portfolio Detail] portfolio_id로 조회 성공: {portfolio_id}")
        except Portfolio.DoesNotExist:
            try:
                # internal_key로 조회 시도
                portfolio = Portfolio.objects.get(internal_key=portfolio_id)
                print(f"[Portfolio Detail] internal_key로 조회 성공: {portfolio_id}")
            except Portfolio.DoesNotExist:
                print(f"[Portfolio Detail] 포트폴리오를 찾을 수 없음: {portfolio_id}")
                return JsonResponse({
                    'success': False,
                    'error': '포트폴리오를 찾을 수 없습니다.'
                }, json_dumps_params={'ensure_ascii': False}, status=404)
        
        # products 데이터 검증 및 포맷팅
        products = portfolio.products
        if not isinstance(products, list):
            print(f"[Portfolio Detail] products가 리스트가 아님: {type(products)}")
            products = []
        
        print(f"[Portfolio Detail] 제품 수: {len(products)}")
        
        # PRD: 구매 리뷰 분석 표시 (모델별 최대 3개)
        products_with_reviews = []
        for product_data in products:
            product_id = product_data.get('product_id') or product_data.get('id')
            if product_id:
                try:
                    # 제품 리뷰 조회 (최대 3개)
                    reviews = ProductReview.objects.filter(product_id=product_id).order_by('-created_at')[:3]
                    review_list = [
                        {
                            'star': review.star or '',
                            'review_text': review.review_text[:200] if review.review_text else '',  # 200자 제한
                            'created_at': review.created_at.isoformat() if review.created_at else None
                        }
                        for review in reviews
                    ]
                    product_data['reviews'] = review_list
                    product_data['review_count'] = len(review_list)
                except Exception as e:
                    print(f"[Portfolio Detail] 제품 {product_id} 리뷰 조회 실패: {e}")
                    product_data['reviews'] = []
                    product_data['review_count'] = 0
            else:
                product_data['reviews'] = []
                product_data['review_count'] = 0
            
            # PRD: 도면 기반 설치 유의사항 자동 출력
            installation_notes = _generate_installation_notes(
                product_data=product_data,
                onboarding_data=portfolio.onboarding_data or {}
            )
            product_data['installation_notes'] = installation_notes
            
            products_with_reviews.append(product_data)
        
        return JsonResponse({
            'success': True,
            'portfolio': {
                'portfolio_id': portfolio.portfolio_id,
                'internal_key': portfolio.internal_key,  # LGDX-3
                'user_id': portfolio.user_id,
                'style_type': portfolio.style_type,
                'style_title': portfolio.style_title,
                'style_subtitle': portfolio.style_subtitle,
                'onboarding_data': portfolio.onboarding_data or {},
                'products': products_with_reviews,  # 리뷰 및 설치 유의사항 포함
                'total_original_price': float(portfolio.total_original_price) if portfolio.total_original_price else 0,
                'total_discount_price': float(portfolio.total_discount_price) if portfolio.total_discount_price else 0,
                'match_score': portfolio.match_score or 0,
                'status': portfolio.status,
                'share_url': portfolio.share_url or '',
                'share_count': portfolio.share_count or 0,
                'created_at': portfolio.created_at.isoformat() if portfolio.created_at else None,
            }
        }, json_dumps_params={'ensure_ascii': False})
    
    except Exception as e:
        print(f"[Portfolio Detail] 오류: {e}")
        import traceback
        traceback.print_exc()
        return JsonResponse({
            'success': False,
            'error': f'포트폴리오 조회 실패: {str(e)}'
        }, json_dumps_params={'ensure_ascii': False}, status=500)


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
        
        # PRD: 카카오톡 공유용 메타데이터 생성
        # 대표 이미지: 첫 번째 제품 이미지 또는 기본 이미지
        representative_image = ''
        if portfolio.products and len(portfolio.products) > 0:
            first_product = portfolio.products[0]
            representative_image = first_product.get('image_url', '')
        
        # 기본 이미지가 없으면 프로젝트 기본 이미지 사용
        if not representative_image:
            base_url = request.build_absolute_uri('/').rstrip('/')
            representative_image = f"{base_url}/static/icon.png"
        
        # 카카오 공유용 메타데이터
        share_title = f"LG 홈스타일링 - {portfolio.style_title}" if portfolio.style_title else "LG 홈스타일링 가전 패키지 추천"
        share_description = (
            portfolio.style_subtitle[:150] if portfolio.style_subtitle 
            else f"나에게 딱 맞는 {len(portfolio.products)}개 가전 제품을 추천받았어요!"
        )
        
        return JsonResponse({
            'success': True,
            'share_url': portfolio.share_url,
            'share_count': portfolio.share_count,
            # 카카오톡 공유용 메타 데이터 (OG 태그용)
            'kakao_share_data': {
                'title': share_title,
                'description': share_description,
                'image_url': representative_image,
                'link': portfolio.share_url,
            }
        }, json_dumps_params={'ensure_ascii': False})
    
    except Portfolio.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': '포트폴리오를 찾을 수 없습니다.'
        }, json_dumps_params={'ensure_ascii': False}, status=404)


@csrf_exempt
@require_http_methods(["POST"])
def portfolio_refresh_view(request, portfolio_id):
    """
    포트폴리오 다시 추천받기 (PRD: 2-4)
    
    POST /api/portfolio/<portfolio_id>/refresh/
    {
        "exclude_product_ids": [1, 2, 3]  # 제외할 제품 ID (선택)
    }
    """
    try:
        data = json.loads(request.body.decode('utf-8')) if request.body else {}
        exclude_product_ids = data.get('exclude_product_ids', [])
        
        result = portfolio_service.refresh_portfolio(
            portfolio_id=portfolio_id,
            exclude_product_ids=exclude_product_ids
        )
        
        if result.get('success'):
            return JsonResponse({
                'success': True,
                'portfolio_id': result.get('portfolio_id'),
                'style_analysis': result.get('style_analysis'),
                'recommendations': result.get('recommendations'),
                'total_price': result.get('total_price'),
                'total_discount_price': result.get('total_discount_price'),
                'message': '새로운 추천 결과를 받았습니다.'
            }, json_dumps_params={'ensure_ascii': False})
        else:
            return JsonResponse({
                'success': False,
                'error': result.get('error', '다시 추천받기 실패')
            }, json_dumps_params={'ensure_ascii': False}, status=400)
    
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, json_dumps_params={'ensure_ascii': False}, status=400)


@require_http_methods(["GET"])
def portfolio_alternatives_view(request, portfolio_id):
    """
    다른 추천 후보 확인 (PRD: 2-6)
    
    GET /api/portfolio/<portfolio_id>/alternatives/?category=TV
    """
    try:
        category = request.GET.get('category', None)
        
        result = portfolio_service.get_alternative_recommendations(
            portfolio_id=portfolio_id,
            category=category
        )
        
        if result.get('success'):
            return JsonResponse({
                'success': True,
                'alternatives': result.get('alternatives', [])
            }, json_dumps_params={'ensure_ascii': False})
        else:
            return JsonResponse({
                'success': False,
                'error': result.get('error', '추천 후보 조회 실패')
            }, json_dumps_params={'ensure_ascii': False}, status=400)
    
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, json_dumps_params={'ensure_ascii': False}, status=400)


@csrf_exempt
@require_http_methods(["POST"])
def portfolio_add_to_cart_view(request, portfolio_id):
    """
    포트폴리오 전체 장바구니 담기 (PRD: 2-3)
    
    POST /api/portfolio/<portfolio_id>/add-to-cart/
    {
        "user_id": "kakao_12345"
    }
    """
    try:
        data = json.loads(request.body.decode('utf-8'))
        user_id = data.get('user_id')
        
        if not user_id:
            return JsonResponse({
                'success': False,
                'error': 'user_id 필수'
            }, json_dumps_params={'ensure_ascii': False}, status=400)
        
        result = portfolio_service.add_products_to_cart(
            portfolio_id=portfolio_id,
            user_id=user_id
        )
        
        if result.get('success'):
            return JsonResponse({
                'success': True,
                'added_count': result.get('added_count', 0),
                'cart_items': result.get('cart_items', []),
                'message': f"{result.get('added_count', 0)}개 제품이 장바구니에 추가되었습니다."
            }, json_dumps_params={'ensure_ascii': False})
        else:
            return JsonResponse({
                'success': False,
                'error': result.get('error', '장바구니 추가 실패')
            }, json_dumps_params={'ensure_ascii': False}, status=400)
    
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, json_dumps_params={'ensure_ascii': False}, status=400)


@csrf_exempt
@require_http_methods(["POST", "PUT"])
def portfolio_edit_view(request, portfolio_id):
    """
    포트폴리오 편집 (제품 추가/삭제/교체/업그레이드)
    
    POST /api/portfolio/<portfolio_id>/edit/
    {
        "action": "add",  # "add", "remove", "replace", "upgrade"
        "product_id": 123,  # remove, replace, upgrade 시 필수
        "new_product_id": 456,  # add, replace 시 필수
        "category": "TV"  # add 시 특정 카테고리에서 선택
    }
    """
    try:
        data = json.loads(request.body.decode('utf-8'))
        action = data.get('action')
        product_id = data.get('product_id')
        new_product_id = data.get('new_product_id')
        category = data.get('category')
        
        if not action:
            return JsonResponse({
                'success': False,
                'error': 'action 필수 (add, remove, replace, upgrade)'
            }, json_dumps_params={'ensure_ascii': False}, status=400)
        
        result = portfolio_service.update_portfolio_products(
            portfolio_id=portfolio_id,
            action=action,
            product_id=product_id,
            new_product_id=new_product_id,
            category=category
        )
        
        if result.get('success'):
            return JsonResponse({
                'success': True,
                'portfolio_id': result.get('portfolio_id'),
                'products': result.get('products', []),
                'total_price': result.get('total_price', 0),
                'total_discount_price': result.get('total_discount_price', 0),
                'message': f'포트폴리오가 업데이트되었습니다.'
            }, json_dumps_params={'ensure_ascii': False})
        else:
            return JsonResponse({
                'success': False,
                'error': result.get('error', '포트폴리오 편집 실패')
            }, json_dumps_params={'ensure_ascii': False}, status=400)
    
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, json_dumps_params={'ensure_ascii': False}, status=400)


@csrf_exempt
@require_http_methods(["POST"])
def portfolio_estimate_view(request, portfolio_id):
    """
    실시간 견적 계산 (옵션별 가격 계산)
    
    POST /api/portfolio/<portfolio_id>/estimate/
    {
        "options": {
            "123": {
                "installation": true,
                "warranty": "extended",
                "accessories": ["stand", "wall_mount"]
            }
        }
    }
    """
    try:
        data = json.loads(request.body.decode('utf-8'))
        options = data.get('options', {})
        
        result = portfolio_service.calculate_estimated_price(
            portfolio_id=portfolio_id,
            options=options
        )
        
        if result.get('success'):
            return JsonResponse({
                'success': True,
                'base_price': result.get('base_price', 0),
                'options_price': result.get('options_price', 0),
                'total_price': result.get('total_price', 0),
                'breakdown': result.get('breakdown', [])
            }, json_dumps_params={'ensure_ascii': False})
        else:
            return JsonResponse({
                'success': False,
                'error': result.get('error', '견적 계산 실패')
            }, json_dumps_params={'ensure_ascii': False}, status=400)
    
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, json_dumps_params={'ensure_ascii': False}, status=400)


@csrf_exempt
@require_http_methods(["POST"])
def bestshop_consultation_view(request):
    """
    베스트샵 상담 예약 (PRD: 2-5)
    
    POST /api/bestshop/consultation/
    {
        "portfolio_id": "PF-XXXXXX",
        "user_id": "kakao_12345",
        "consultation_purpose": "이사",
        "preferred_date": "2025-12-15",
        "preferred_time": "14:00",
        "store_location": "서울 강남점"
    }
    
    Note: 실제 베스트샵 API 연동은 외부 시스템이므로 여기서는 포트폴리오 정보를 준비만 함
    """
    try:
        data = json.loads(request.body.decode('utf-8'))
        
        portfolio_id = data.get('portfolio_id')
        user_id = data.get('user_id')
        consultation_purpose = data.get('consultation_purpose', '이사')
        preferred_date = data.get('preferred_date')
        preferred_time = data.get('preferred_time')
        store_location = data.get('store_location')
        
        if not portfolio_id:
            return JsonResponse({
                'success': False,
                'error': 'portfolio_id 필수'
            }, json_dumps_params={'ensure_ascii': False}, status=400)
        
        # 포트폴리오 정보 조회
        try:
            portfolio = Portfolio.objects.get(portfolio_id=portfolio_id)
        except Portfolio.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': '포트폴리오를 찾을 수 없습니다.'
            }, json_dumps_params={'ensure_ascii': False}, status=404)
        
        # 베스트샵 상담 예약 정보 준비
        consultation_data = {
            'portfolio_id': portfolio.portfolio_id,
            'internal_key': portfolio.internal_key,
            'user_id': user_id,
            'consultation_purpose': consultation_purpose,
            'preferred_date': preferred_date,
            'preferred_time': preferred_time,
            'store_location': store_location,
            'products': portfolio.products,
            'total_price': float(portfolio.total_original_price),
            'total_discount_price': float(portfolio.total_discount_price),
            'style_analysis': {
                'title': portfolio.style_title,
                'subtitle': portfolio.style_subtitle,
                'style_type': portfolio.style_type
            },
            'onboarding_data': portfolio.onboarding_data
        }
        
        # 베스트샵 URL 생성 (포트폴리오 정보 포함)
        from urllib.parse import urlencode
        bestshop_base_url = "https://bestshop.lge.co.kr/counselReserve/main/MC11420001"
        bestshop_params = {
            'inflow': 'lgekor',
            'portfolio_id': portfolio.portfolio_id,
        }
        
        # 제품 정보 추가
        if portfolio.products:
            product_names = [p.get('name', '') for p in portfolio.products[:5] if p.get('name')]
            if product_names:
                bestshop_params['products'] = ','.join(product_names)
        
        # 예약 정보 추가
        if preferred_date:
            bestshop_params['date'] = preferred_date
        if preferred_time:
            bestshop_params['time'] = preferred_time
        if store_location:
            bestshop_params['store'] = store_location
        
        # URL 생성
        bestshop_url = f"{bestshop_base_url}?{urlencode(bestshop_params)}"
        
        # 예약 정보 DB 저장
        reservation = Reservation.objects.create(
            user_id=user_id or f"guest_{timezone.now().strftime('%Y%m%d%H%M%S')}",
            portfolio=portfolio,
            consultation_purpose=consultation_purpose,
            preferred_date=preferred_date if preferred_date else None,
            preferred_time=preferred_time if preferred_time else None,
            store_location=store_location,
            contact_name=data.get('contact_name', ''),
            contact_phone=data.get('contact_phone', ''),
            contact_email=data.get('contact_email', ''),
            memo=data.get('memo', ''),
            external_system_url=bestshop_url,
            status='pending'
        )
        
        # PRD: 베스트샵 상담 예약 시 카카오톡 알림 자동 전송 (선택적)
        # 카카오 로그인 사용자이고 액세스 토큰이 있으면 알림 전송
        if request.user.is_authenticated:
            access_token = request.session.get('kakao_access_token')
            if access_token:
                try:
                    consultation_date_str = f"{preferred_date} {preferred_time}" if preferred_date and preferred_time else (preferred_date or '미정')
                    portfolio_title = portfolio.style_title if portfolio and portfolio.style_title else portfolio_id
                    kakao_message_service.send_consultation_notification(
                        user_access_token=access_token,
                        portfolio_title=portfolio_title,
                        consultation_date=consultation_date_str,
                        store_location=store_location or '매장 미정'
                    )
                except Exception as msg_error:
                    # 메시지 전송 실패는 치명적이지 않으므로 로깅만
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.warning(f"[Bestshop Consultation] 카카오 알림 전송 실패 (무시): {msg_error}")
        
        return JsonResponse({
            'success': True,
            'message': '상담 예약이 생성되었습니다.',
            'reservation_id': reservation.reservation_id,
            'consultation_data': consultation_data,
            'bestshop_url': bestshop_url,
            'reservation': {
                'id': reservation.reservation_id,
                'status': reservation.status,
                'preferred_date': reservation.preferred_date.isoformat() if reservation.preferred_date else None,
                'preferred_time': reservation.preferred_time.isoformat() if reservation.preferred_time else None,
                'store_location': reservation.store_location,
                'created_at': reservation.created_at.isoformat(),
            },
            'note': '베스트샵 예약 페이지로 이동합니다. 실제 예약은 베스트샵 시스템에서 완료됩니다.'
        }, json_dumps_params={'ensure_ascii': False})
    
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, json_dumps_params={'ensure_ascii': False}, status=400)


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


# ============================================================
# 카카오 로그인 API
# ============================================================

@require_http_methods(["GET"])
def kakao_login_view(request):
    """
    카카오 로그인 시작
    
    GET /api/auth/kakao/login/
    """
    from django.shortcuts import redirect
    from django.conf import settings
    
    if not settings.KAKAO_REST_API_KEY:
        return JsonResponse({
            'success': False,
            'error': '카카오 API 키가 설정되지 않았습니다.'
        }, status=500)
    
    redirect_uri = request.build_absolute_uri('/api/auth/kakao/callback/')
    auth_url = kakao_auth_service.get_authorization_url(redirect_uri)
    
    return redirect(auth_url)


@require_http_methods(["GET"])
def kakao_callback_view(request):
    """
    카카오 로그인 콜백
    
    GET /api/auth/kakao/callback/?code=xxx
    """
    from django.shortcuts import redirect
    from django.contrib.auth import login
    from django.conf import settings
    
    code = request.GET.get('code')
    error = request.GET.get('error')
    
    if error:
        return redirect(f'/?error={error}')
    
    if not code:
        return redirect('/?error=no_code')
    
    try:
        redirect_uri = request.build_absolute_uri('/api/auth/kakao/callback/')
        
        # 액세스 토큰 발급
        token_response = kakao_auth_service.get_access_token(code, redirect_uri)
        access_token = token_response.get('access_token')
        refresh_token = token_response.get('refresh_token')  # 리프레시 토큰도 저장
        
        if not access_token:
            return redirect('/?error=no_token')
        
        # 사용자 정보 조회
        user_info = kakao_auth_service.get_user_info(access_token)
        
        # Django User 생성/조회
        user, created = kakao_auth_service.get_or_create_user(user_info)
        
        # 로그인 처리
        login(request, user)
        
        # 세션에 카카오 정보 저장 (리프레시 토큰 포함)
        request.session['kakao_access_token'] = access_token
        if refresh_token:
            request.session['kakao_refresh_token'] = refresh_token
        request.session['kakao_user_id'] = str(user_info.get('id'))
        # 토큰 만료 시간 저장 (기본 6시간)
        request.session['kakao_token_expires_at'] = token_response.get('expires_in', 21600)
        
        # 리다이렉트 (마이페이지 또는 메인)
        return redirect('/my-page/?login=success')
    
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"[Kakao Callback] 오류: {e}")
        # 에러 메시지를 URL 인코딩하여 전달
        error_message = str(e)[:100]  # 너무 긴 메시지 방지
        return redirect(f'/?error={error_message}')


@require_http_methods(["GET"])
def kakao_logout_view(request):
    """
    카카오 로그아웃
    
    GET /api/auth/kakao/logout/
    """
    from django.contrib.auth import logout
    from django.shortcuts import redirect
    
    logout(request)
    request.session.flush()
    
    return redirect('/?logout=success')


@require_http_methods(["GET"])
def kakao_user_info_view(request):
    """
    현재 로그인한 카카오 사용자 정보 조회
    
    GET /api/auth/kakao/user/
    """
    if not request.user.is_authenticated:
        return JsonResponse({
            'success': False,
            'error': '로그인이 필요합니다.'
        }, status=401)
    
    return JsonResponse({
        'success': True,
        'user': {
            'id': request.user.id,
            'username': request.user.username,
            'email': request.user.email,
            'first_name': request.user.first_name,
            'is_kakao_user': request.user.username.startswith('kakao_')
        }
    }, json_dumps_params={'ensure_ascii': False})


# ============================================================
# 고급 AI 추천 API (자연어 대화 기반)
# ============================================================

@csrf_exempt
@require_http_methods(["POST"])
def ai_natural_recommend_view(request):
    """
    자연어 대화 기반 AI 추천
    
    POST /api/ai/natural-recommend/
    {
        "message": "2인 가구, 작은 주방, 예산 200만원",
        "conversation_history": [...]  # 선택
    }
    """
    try:
        data = json.loads(request.body.decode('utf-8'))
        
        user_message = data.get('message', '')
        conversation_history = data.get('conversation_history', [])
        
        if not user_message:
            return JsonResponse({
                'success': False,
                'error': '메시지를 입력해주세요.'
            }, status=400)
        
        result = ai_recommendation_service.recommend_from_conversation(
            user_message=user_message,
            conversation_history=conversation_history
        )
        
        return JsonResponse(result, json_dumps_params={'ensure_ascii': False})
    
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, json_dumps_params={'ensure_ascii': False}, status=400)


@csrf_exempt
@require_http_methods(["POST"])
def ai_chat_recommend_view(request):
    """
    대화형 AI 추천 (일반 대화 + 추천)
    
    POST /api/ai/chat-recommend/
    {
        "message": "냉장고 추천해줘",
        "conversation_history": [...]  # 선택
    }
    """
    try:
        data = json.loads(request.body.decode('utf-8'))
        
        user_message = data.get('message', '')
        conversation_history = data.get('conversation_history', [])
        
        if not user_message:
            return JsonResponse({
                'success': False,
                'type': 'error',
                'message': '메시지를 입력해주세요.',
                'error': '메시지를 입력해주세요.'
            }, status=400, json_dumps_params={'ensure_ascii': False})
        
        print(f"[AI 추천] 사용자 메시지: {user_message}")
        
        result = ai_recommendation_service.chat_recommendation(
            user_message=user_message,
            conversation_history=conversation_history
        )
        
        # 결과에 success 필드가 없으면 추가
        if 'success' not in result:
            result['success'] = result.get('type') != 'error'
        
        print(f"[AI 추천] 결과 타입: {result.get('type')}, 성공: {result.get('success')}")
        
        return JsonResponse(result, json_dumps_params={'ensure_ascii': False})
    
    except json.JSONDecodeError as e:
        print(f"[AI 추천] JSON 파싱 오류: {e}")
        return JsonResponse({
            'success': False,
            'type': 'error',
            'message': '요청 형식이 올바르지 않아요. 다시 시도해주세요.',
            'error': f'JSON 파싱 오류: {str(e)}'
        }, status=400, json_dumps_params={'ensure_ascii': False})
    except Exception as e:
        print(f"[AI 추천] 예외 발생: {e}")
        import traceback
        print(f"[AI 추천] 트레이스백: {traceback.format_exc()}")
        return JsonResponse({
            'success': False,
            'type': 'error',
            'message': '죄송해요, 일시적인 오류가 발생했어요. 다시 시도해주세요.',
            'error': str(e)
        }, status=500, json_dumps_params={'ensure_ascii': False})


# ============================================================
# 제품 비교 AI 분석 API
# ============================================================

@csrf_exempt
@require_http_methods(["POST"])
def ai_product_compare_view(request):
    """
    제품 비교 AI 분석
    
    POST /api/ai/product-compare/
    {
        "product_ids": [1, 2, 3],
        "user_context": {  # 선택
            "household_size": 2,
            "budget": 300,
            "priority": "value"
        }
    }
    """
    try:
        data = json.loads(request.body.decode('utf-8'))
        
        product_ids = data.get('product_ids', [])
        user_context = data.get('user_context', {})
        
        if not product_ids or len(product_ids) < 2:
            return JsonResponse({
                'success': False,
                'error': '최소 2개 이상의 제품을 선택해주세요.'
            }, status=400)
        
        result = product_comparison_service.compare_products(
            product_ids=product_ids,
            user_context=user_context
        )
        
        return JsonResponse(result, json_dumps_params={'ensure_ascii': False})
    
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, json_dumps_params={'ensure_ascii': False}, status=400)


# ============================================================
# 카카오톡 메시지 전송 API
# ============================================================

@csrf_exempt
@require_http_methods(["POST"])
def kakao_send_message_view(request):
    """
    카카오톡 메시지 전송 (상담 예약 알림 등)
    
    POST /api/kakao/send-message/
    {
        "portfolio_title": "나의 홈스타일링",
        "consultation_date": "2025-12-15 14:00",
        "store_location": "서울 강남점"
    }
    """
    if not request.user.is_authenticated:
        return JsonResponse({
            'success': False,
            'error': '로그인이 필요합니다.'
        }, status=401)
    
    try:
        data = json.loads(request.body.decode('utf-8'))
        
        # 액세스 토큰 가져오기 (만료 시 리프레시 토큰으로 갱신 시도)
        access_token = request.session.get('kakao_access_token')
        refresh_token = request.session.get('kakao_refresh_token')
        
        if not access_token:
            return JsonResponse({
                'success': False,
                'error': '카카오 로그인이 필요합니다.'
            }, status=401)
        
        # 토큰 만료 시 리프레시 토큰으로 갱신 시도
        if refresh_token:
            try:
                # 토큰 유효성 간단 체크 (실제로는 API 호출로 확인)
                # 여기서는 세션의 만료 시간 확인
                token_expires_at = request.session.get('kakao_token_expires_at', 0)
                import time
                if token_expires_at and time.time() > token_expires_at:
                    # 토큰 갱신 시도
                    try:
                        new_token_data = kakao_auth_service.refresh_access_token(refresh_token)
                        access_token = new_token_data.get('access_token')
                        if access_token:
                            request.session['kakao_access_token'] = access_token
                            if new_token_data.get('refresh_token'):
                                request.session['kakao_refresh_token'] = new_token_data.get('refresh_token')
                            request.session['kakao_token_expires_at'] = time.time() + new_token_data.get('expires_in', 21600)
                    except Exception as refresh_error:
                        # 리프레시 실패 시 재로그인 필요
                        import logging
                        logger = logging.getLogger(__name__)
                        logger.warning(f"[Kakao Message] 토큰 갱신 실패: {refresh_error}")
                        return JsonResponse({
                            'success': False,
                            'error': '카카오 로그인이 만료되었습니다. 다시 로그인해주세요.'
                        }, status=401)
            except Exception as e:
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(f"[Kakao Message] 토큰 확인 중 오류: {e}")
        
        # 포트폴리오 정보 가져오기
        portfolio_id = data.get('portfolio_id')
        portfolio_title = data.get('portfolio_title', '포트폴리오')
        consultation_date = data.get('consultation_date', '')
        store_location = data.get('store_location', '')
        
        # 포트폴리오 ID가 있으면 포트폴리오에서 정보 가져오기
        if portfolio_id:
            try:
                portfolio = Portfolio.objects.get(portfolio_id=portfolio_id)
                if not portfolio_title or portfolio_title == '포트폴리오':
                    portfolio_title = portfolio.style_title or '나의 가전 패키지'
            except Portfolio.DoesNotExist:
                pass
        
        try:
            result = kakao_message_service.send_consultation_notification(
                user_access_token=access_token,
                portfolio_title=portfolio_title,
                consultation_date=consultation_date,
                store_location=store_location
            )
            
            if result:
                return JsonResponse({
                    'success': True,
                    'message': '메시지가 전송되었습니다.'
                }, json_dumps_params={'ensure_ascii': False})
            else:
                # 메시지 전송 실패해도 사용자에게는 성공으로 표시 (비동기 처리 고려)
                return JsonResponse({
                    'success': True,
                    'message': '메시지 전송이 요청되었습니다.',
                    'note': '메시지 전송에 일시적인 문제가 있을 수 있습니다.'
                }, json_dumps_params={'ensure_ascii': False})
        except Exception as msg_error:
            # 메시지 전송 실패는 치명적이지 않으므로 경고만
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"[Kakao Message] 전송 실패 (무시): {msg_error}")
            return JsonResponse({
                'success': True,
                'message': '상담 예약이 완료되었습니다.',
                'note': '카카오톡 알림 전송에 실패했지만 예약은 정상적으로 처리되었습니다.'
            }, json_dumps_params={'ensure_ascii': False})
    
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, json_dumps_params={'ensure_ascii': False}, status=400)


# ============================================================
# 장바구니 API - LGDX-12
# ============================================================

@csrf_exempt
@require_http_methods(["POST"])
def cart_add_view(request):
    """
    장바구니 추가 API
    
    POST /api/cart/add/
    {
        "user_id": "kakao_12345" 또는 "session_xxx",
        "product_id": 123,
        "quantity": 1,
        "extra_data": {"price": 1000000, "discount_price": 900000}
    }
    """
    try:
        data = json.loads(request.body.decode('utf-8'))
        
        user_id = data.get('user_id', f"guest_{timezone.now().strftime('%Y%m%d%H%M%S')}")
        product_id = data.get('product_id')
        quantity = int(data.get('quantity', 1))
        extra_data = data.get('extra_data', {})
        
        if not product_id:
            return JsonResponse({
                'success': False,
                'error': 'product_id 필수'
            }, json_dumps_params={'ensure_ascii': False}, status=400)
        
        try:
            product = Product.objects.get(id=product_id)
        except Product.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': '제품을 찾을 수 없습니다.'
            }, json_dumps_params={'ensure_ascii': False}, status=404)
        
        # 기존 장바구니 항목이 있으면 수량 증가, 없으면 생성
        cart_item, created = Cart.objects.get_or_create(
            user_id=user_id,
            product=product,
            defaults={
                'quantity': quantity,
                'extra_data': extra_data
            }
        )
        
        if not created:
            # 기존 항목이 있으면 수량 증가
            cart_item.quantity += quantity
            if extra_data:
                cart_item.extra_data.update(extra_data)
            cart_item.save()
        
        return JsonResponse({
            'success': True,
            'message': '장바구니에 추가되었습니다.',
            'cart_item': {
                'id': cart_item.id,
                'product_id': cart_item.product.id,
                'product_name': cart_item.product.name,
                'quantity': cart_item.quantity,
            }
        }, json_dumps_params={'ensure_ascii': False})
    
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, json_dumps_params={'ensure_ascii': False}, status=400)


@csrf_exempt
@require_http_methods(["POST"])
def cart_remove_view(request):
    """
    장바구니 삭제 API
    
    POST /api/cart/remove/
    {
        "user_id": "kakao_12345",
        "product_id": 123  # 또는 "cart_item_id": 456
    }
    """
    try:
        data = json.loads(request.body.decode('utf-8'))
        
        user_id = data.get('user_id')
        product_id = data.get('product_id')
        cart_item_id = data.get('cart_item_id')
        
        if not user_id:
            return JsonResponse({
                'success': False,
                'error': 'user_id 필수'
            }, json_dumps_params={'ensure_ascii': False}, status=400)
        
        if cart_item_id:
            # cart_item_id로 삭제
            try:
                cart_item = Cart.objects.get(id=cart_item_id, user_id=user_id)
                cart_item.delete()
            except Cart.DoesNotExist:
                return JsonResponse({
                    'success': False,
                    'error': '장바구니 항목을 찾을 수 없습니다.'
                }, json_dumps_params={'ensure_ascii': False}, status=404)
        elif product_id:
            # product_id로 삭제
            try:
                cart_item = Cart.objects.get(user_id=user_id, product_id=product_id)
                cart_item.delete()
            except Cart.DoesNotExist:
                return JsonResponse({
                    'success': False,
                    'error': '장바구니 항목을 찾을 수 없습니다.'
                }, json_dumps_params={'ensure_ascii': False}, status=404)
        else:
            return JsonResponse({
                'success': False,
                'error': 'product_id 또는 cart_item_id 필수'
            }, json_dumps_params={'ensure_ascii': False}, status=400)
        
        return JsonResponse({
            'success': True,
            'message': '장바구니에서 삭제되었습니다.'
        }, json_dumps_params={'ensure_ascii': False})
    
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, json_dumps_params={'ensure_ascii': False}, status=400)


@require_http_methods(["GET"])
def cart_list_view(request):
    """
    장바구니 목록 조회 API
    
    GET /api/cart/list/?user_id=xxx
    """
    user_id = request.GET.get('user_id')
    
    if not user_id:
        return JsonResponse({
            'success': False,
            'error': 'user_id 필수'
        }, status=400)
    
    cart_items = Cart.objects.filter(user_id=user_id).select_related('product')
    
    cart_list = []
    total_price = 0
    for item in cart_items:
        product_price = item.extra_data.get('discount_price') or item.extra_data.get('price') or float(item.product.price)
        item_total = product_price * item.quantity
        total_price += item_total
        
        cart_list.append({
            'id': item.id,
            'product_id': item.product.id,
            'product_name': item.product.name,
            'product_image_url': item.product.image_url,
            'quantity': item.quantity,
            'price': float(item.product.price),
            'discount_price': item.extra_data.get('discount_price'),
            'item_total': item_total,
            'extra_data': item.extra_data,
            'created_at': item.created_at.isoformat(),
        })
    
    return JsonResponse({
        'success': True,
        'count': len(cart_list),
        'total_price': total_price,
        'items': cart_list
    }, json_dumps_params={'ensure_ascii': False})


# ============================================================
# 제품 상세 페이지
# ============================================================

@require_http_methods(["GET"])
def product_detail_page(request, product_id):
    """
    제품 상세 페이지 렌더링
    
    GET /products/<product_id>/
    """
    try:
        product = Product.objects.get(id=product_id, is_active=True)
        
        # 제품 스펙 가져오기
        spec_data = {}
        if hasattr(product, 'spec') and product.spec.spec_json:
            try:
                spec_data = json.loads(product.spec.spec_json)
            except:
                spec_data = {}
        
        # 제품 리뷰 가져오기 (최대 10개)
        reviews = ProductReview.objects.filter(product=product).order_by('-created_at')[:10]
        
        # 관련 제품 추천 (같은 카테고리에서 최대 4개)
        related_products = Product.objects.filter(
            category=product.category,
            is_active=True
        ).exclude(id=product_id)[:4]
        
        return render(request, "product_detail.html", {
            'product': product,
            'spec_data': spec_data,
            'reviews': reviews,
            'related_products': related_products,
        })
    
    except Product.DoesNotExist:
        from django.http import Http404
        raise Http404("제품을 찾을 수 없습니다.")


# ============================================================
# 검색 기능
# ============================================================

@require_http_methods(["GET"])
def search_view(request):
    """
    제품 검색 API
    
    GET /api/search/?q=검색어&category=TV&page=1&page_size=20
    """
    from django.db.models import Q
    
    query = request.GET.get('q', '').strip()
    category = request.GET.get('category', None)
    page = int(request.GET.get('page', 1))
    page_size = int(request.GET.get('page_size', 20))
    
    if not query:
        return JsonResponse({
            'success': False,
            'error': '검색어가 필요합니다.'
        }, json_dumps_params={'ensure_ascii': False}, status=400)
    
    # 기본 쿼리셋
    queryset = Product.objects.filter(is_active=True)
    
    # 검색 필터 (제품명, 모델명, 설명에서 검색)
    queryset = queryset.filter(
        Q(name__icontains=query) |
        Q(model_number__icontains=query) |
        Q(description__icontains=query)
    )
    
    # 카테고리 필터
    if category:
        queryset = queryset.filter(category=category)
    
    # 총 개수
    total_count = queryset.count()
    
    # 페이지네이션
    start = (page - 1) * page_size
    end = start + page_size
    queryset = queryset.order_by('-created_at')[start:end]
    
    results = []
    for product in queryset:
        results.append({
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
        'success': True,
        'query': query,
        'count': len(results),
        'total_count': total_count,
        'page': page,
        'page_size': page_size,
        'total_pages': (total_count + page_size - 1) // page_size,
        'results': results
    }, json_dumps_params={'ensure_ascii': False})


# ============================================================
# 제품 비교 기능
# ============================================================

@require_http_methods(["GET", "POST"])
def product_compare_view(request):
    """
    제품 비교 API
    
    GET /api/products/compare/?ids=1,2,3 - 비교할 제품 목록 조회
    POST /api/products/compare/ - 제품 비교 (body: {"product_ids": [1, 2, 3]})
    """
    if request.method == 'GET':
        product_ids_str = request.GET.get('ids', '')
        if not product_ids_str:
            return JsonResponse({
                'success': False,
                'error': '제품 ID가 필요합니다.'
            }, json_dumps_params={'ensure_ascii': False}, status=400)
        
        try:
            product_ids = [int(id.strip()) for id in product_ids_str.split(',')]
        except ValueError:
            return JsonResponse({
                'success': False,
                'error': '잘못된 제품 ID 형식입니다.'
            }, json_dumps_params={'ensure_ascii': False}, status=400)
    else:  # POST
        try:
            data = json.loads(request.body.decode('utf-8'))
            product_ids = data.get('product_ids', [])
        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'error': 'Invalid JSON'
            }, json_dumps_params={'ensure_ascii': False}, status=400)
    
    # 최대 4개까지만 비교 가능
    if len(product_ids) > 4:
        return JsonResponse({
            'success': False,
            'error': '최대 4개까지만 비교할 수 있습니다.'
        }, json_dumps_params={'ensure_ascii': False}, status=400)
    
    if len(product_ids) < 2:
        return JsonResponse({
            'success': False,
            'error': '최소 2개 이상의 제품을 선택해야 합니다.'
        }, json_dumps_params={'ensure_ascii': False}, status=400)
    
    # 제품 조회
    products = Product.objects.filter(id__in=product_ids, is_active=True)
    
    if products.count() != len(product_ids):
        return JsonResponse({
            'success': False,
            'error': '일부 제품을 찾을 수 없습니다.'
        }, json_dumps_params={'ensure_ascii': False}, status=404)
    
    # 제품 정보 및 스펙 수집
    compare_data = []
    all_spec_keys = set()
    
    for product in products:
        product_data = {
            'id': product.id,
            'name': product.name,
            'model_number': product.model_number,
            'category': product.category,
            'category_display': product.get_category_display(),
            'description': product.description,
            'price': float(product.price),
            'discount_price': float(product.discount_price) if product.discount_price else None,
            'image_url': product.image_url,
            'specs': {}
        }
        
        # 스펙 정보 가져오기
        if hasattr(product, 'spec') and product.spec.spec_json:
            try:
                spec_data = json.loads(product.spec.spec_json)
                product_data['specs'] = spec_data
                all_spec_keys.update(spec_data.keys())
            except:
                pass
        
        compare_data.append(product_data)
    
    return JsonResponse({
        'success': True,
        'count': len(compare_data),
        'products': compare_data,
        'all_spec_keys': sorted(list(all_spec_keys))
    }, json_dumps_params={'ensure_ascii': False})


# ============================================================
# 찜하기/위시리스트 기능
# ============================================================

@csrf_exempt
@require_http_methods(["POST"])
def wishlist_add_view(request):
    """
    찜하기 추가 API
    
    POST /api/wishlist/add/
    {
        "user_id": "kakao_12345",
        "product_id": 123
    }
    """
    try:
        data = json.loads(request.body.decode('utf-8'))
        user_id = data.get('user_id')
        product_id = data.get('product_id')
        
        if not user_id or not product_id:
            return JsonResponse({
                'success': False,
                'error': 'user_id와 product_id가 필요합니다.'
            }, json_dumps_params={'ensure_ascii': False}, status=400)
        
        try:
            product = Product.objects.get(id=product_id, is_active=True)
        except Product.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': '제품을 찾을 수 없습니다.'
            }, json_dumps_params={'ensure_ascii': False}, status=404)
        
        # 찜하기 추가 (이미 있으면 무시)
        wishlist_item, created = Wishlist.objects.get_or_create(
            user_id=user_id,
            product=product
        )
        
        return JsonResponse({
            'success': True,
            'message': '찜하기에 추가되었습니다.' if created else '이미 찜하기에 있습니다.',
            'wishlist_item': {
                'id': wishlist_item.id,
                'product_id': wishlist_item.product.id,
                'product_name': wishlist_item.product.name,
            }
        }, json_dumps_params={'ensure_ascii': False})
    
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, json_dumps_params={'ensure_ascii': False}, status=400)


@csrf_exempt
@require_http_methods(["POST"])
def wishlist_remove_view(request):
    """
    찜하기 삭제 API
    
    POST /api/wishlist/remove/
    {
        "user_id": "kakao_12345",
        "product_id": 123
    }
    """
    try:
        data = json.loads(request.body.decode('utf-8'))
        user_id = data.get('user_id')
        product_id = data.get('product_id')
        
        if not user_id or not product_id:
            return JsonResponse({
                'success': False,
                'error': 'user_id와 product_id가 필요합니다.'
            }, json_dumps_params={'ensure_ascii': False}, status=400)
        
        try:
            wishlist_item = Wishlist.objects.get(user_id=user_id, product_id=product_id)
            wishlist_item.delete()
            
            return JsonResponse({
                'success': True,
                'message': '찜하기에서 삭제되었습니다.'
            }, json_dumps_params={'ensure_ascii': False})
        except Wishlist.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': '찜하기 항목을 찾을 수 없습니다.'
            }, json_dumps_params={'ensure_ascii': False}, status=404)
    
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, json_dumps_params={'ensure_ascii': False}, status=400)


@require_http_methods(["GET"])
def wishlist_list_view(request):
    """
    찜하기 목록 조회 API
    
    GET /api/wishlist/list/?user_id=xxx
    """
    user_id = request.GET.get('user_id')
    
    if not user_id:
        return JsonResponse({
            'success': False,
            'error': 'user_id 필수'
        }, status=400)
    
    wishlist_items = Wishlist.objects.filter(user_id=user_id).select_related('product')
    
    wishlist_list = []
    for item in wishlist_items:
        wishlist_list.append({
            'id': item.id,
            'product_id': item.product.id,
            'product_name': item.product.name,
            'product_image_url': item.product.image_url,
            'product_price': float(item.product.price),
            'product_discount_price': float(item.product.discount_price) if item.product.discount_price else None,
            'product_category': item.product.category,
            'product_category_display': item.product.get_category_display(),
            'created_at': item.created_at.isoformat(),
        })
    
    return JsonResponse({
        'success': True,
        'count': len(wishlist_list),
        'items': wishlist_list
    }, json_dumps_params={'ensure_ascii': False})


# ============================================================
# 예약 조회/변경 API - PRD 요구사항
# ============================================================

@require_http_methods(["GET"])
def reservation_list_view(request):
    """
    예약 목록 조회 API
    
    GET /api/reservation/list/?user_id=xxx&status=pending
    """
    user_id = request.GET.get('user_id')
    status_filter = request.GET.get('status', None)
    
    if not user_id:
        return JsonResponse({
            'success': False,
            'error': 'user_id 필수'
        }, json_dumps_params={'ensure_ascii': False}, status=400)
    
    reservations = Reservation.objects.filter(user_id=user_id)
    
    # 상태 필터
    if status_filter:
        reservations = reservations.filter(status=status_filter)
    
    reservations = reservations.select_related('portfolio').order_by('-created_at')
    
    reservation_list = []
    for reservation in reservations:
        reservation_data = {
            'reservation_id': reservation.reservation_id,
            'status': reservation.status,
            'status_display': reservation.get_status_display(),
            'consultation_purpose': reservation.consultation_purpose,
            'preferred_date': reservation.preferred_date.isoformat() if reservation.preferred_date else None,
            'preferred_time': reservation.preferred_time.isoformat() if reservation.preferred_time else None,
            'store_location': reservation.store_location,
            'contact_name': reservation.contact_name,
            'contact_phone': reservation.contact_phone,
            'portfolio_id': reservation.portfolio.portfolio_id if reservation.portfolio else None,
            'external_system_url': reservation.external_system_url,
            'created_at': reservation.created_at.isoformat(),
            'confirmed_at': reservation.confirmed_at.isoformat() if reservation.confirmed_at else None,
        }
        reservation_list.append(reservation_data)
    
    return JsonResponse({
        'success': True,
        'count': len(reservation_list),
        'reservations': reservation_list
    }, json_dumps_params={'ensure_ascii': False})


@require_http_methods(["GET"])
def reservation_detail_view(request, reservation_id):
    """
    예약 상세 조회 API
    
    GET /api/reservation/<reservation_id>/
    """
    try:
        reservation = Reservation.objects.select_related('portfolio').get(reservation_id=reservation_id)
        
        # 포트폴리오 정보
        portfolio_data = None
        if reservation.portfolio:
            portfolio_data = {
                'portfolio_id': reservation.portfolio.portfolio_id,
                'style_type': reservation.portfolio.style_type,
                'style_title': reservation.portfolio.style_title,
                'total_price': float(reservation.portfolio.total_discount_price),
                'product_count': len(reservation.portfolio.products),
            }
        
        return JsonResponse({
            'success': True,
            'reservation': {
                'reservation_id': reservation.reservation_id,
                'status': reservation.status,
                'status_display': reservation.get_status_display(),
                'user_id': reservation.user_id,
                'consultation_purpose': reservation.consultation_purpose,
                'preferred_date': reservation.preferred_date.isoformat() if reservation.preferred_date else None,
                'preferred_time': reservation.preferred_time.isoformat() if reservation.preferred_time else None,
                'store_location': reservation.store_location,
                'contact_name': reservation.contact_name,
                'contact_phone': reservation.contact_phone,
                'contact_email': reservation.contact_email,
                'memo': reservation.memo,
                'external_reservation_id': reservation.external_reservation_id,
                'external_system_url': reservation.external_system_url,
                'portfolio': portfolio_data,
                'created_at': reservation.created_at.isoformat(),
                'updated_at': reservation.updated_at.isoformat(),
                'confirmed_at': reservation.confirmed_at.isoformat() if reservation.confirmed_at else None,
                'cancelled_at': reservation.cancelled_at.isoformat() if reservation.cancelled_at else None,
            }
        }, json_dumps_params={'ensure_ascii': False})
    
    except Reservation.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': '예약을 찾을 수 없습니다.'
        }, json_dumps_params={'ensure_ascii': False}, status=404)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, json_dumps_params={'ensure_ascii': False}, status=400)


@csrf_exempt
@require_http_methods(["PUT", "POST"])
def reservation_update_view(request, reservation_id):
    """
    예약 변경 API
    
    PUT /api/reservation/<reservation_id>/update/
    POST /api/reservation/<reservation_id>/update/
    {
        "preferred_date": "2025-12-20",
        "preferred_time": "15:00",
        "store_location": "서울 강남점",
        "contact_name": "홍길동",
        "contact_phone": "010-1234-5678",
        "contact_email": "test@example.com",
        "memo": "변경 사유..."
    }
    """
    try:
        reservation = Reservation.objects.get(reservation_id=reservation_id)
        
        # 취소된 예약은 변경 불가
        if reservation.status == 'cancelled':
            return JsonResponse({
                'success': False,
                'error': '취소된 예약은 변경할 수 없습니다.'
            }, json_dumps_params={'ensure_ascii': False}, status=400)
        
        # 완료된 예약은 변경 불가
        if reservation.status == 'completed':
            return JsonResponse({
                'success': False,
                'error': '완료된 예약은 변경할 수 없습니다.'
            }, json_dumps_params={'ensure_ascii': False}, status=400)
        
        # 요청 데이터 파싱
        if hasattr(request, 'data'):
            data = request.data
        else:
            data = json.loads(request.body.decode('utf-8'))
        
        # 예약 정보 업데이트
        if 'preferred_date' in data:
            from datetime import datetime
            try:
                reservation.preferred_date = datetime.strptime(data['preferred_date'], '%Y-%m-%d').date()
            except ValueError:
                return JsonResponse({
                    'success': False,
                    'error': '날짜 형식이 올바르지 않습니다. (YYYY-MM-DD 형식)'
                }, json_dumps_params={'ensure_ascii': False}, status=400)
        
        if 'preferred_time' in data:
            from datetime import datetime
            try:
                reservation.preferred_time = datetime.strptime(data['preferred_time'], '%H:%M').time()
            except ValueError:
                return JsonResponse({
                    'success': False,
                    'error': '시간 형식이 올바르지 않습니다. (HH:MM 형식)'
                }, json_dumps_params={'ensure_ascii': False}, status=400)
        
        if 'store_location' in data:
            reservation.store_location = data['store_location']
        
        if 'contact_name' in data:
            reservation.contact_name = data['contact_name']
        
        if 'contact_phone' in data:
            reservation.contact_phone = data['contact_phone']
        
        if 'contact_email' in data:
            reservation.contact_email = data['contact_email']
        
        if 'memo' in data:
            reservation.memo = data['memo']
        
        if 'consultation_purpose' in data:
            reservation.consultation_purpose = data['consultation_purpose']
        
        # 상태 변경 시 확인 시간 업데이트
        if 'status' in data and data['status'] == 'confirmed' and reservation.status != 'confirmed':
            reservation.confirmed_at = timezone.now()
        
        reservation.save()
        
        return JsonResponse({
            'success': True,
            'message': '예약이 변경되었습니다.',
            'reservation': {
                'reservation_id': reservation.reservation_id,
                'status': reservation.status,
                'preferred_date': reservation.preferred_date.isoformat() if reservation.preferred_date else None,
                'preferred_time': reservation.preferred_time.isoformat() if reservation.preferred_time else None,
                'store_location': reservation.store_location,
                'updated_at': reservation.updated_at.isoformat(),
            }
        }, json_dumps_params={'ensure_ascii': False})
    
    except Reservation.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': '예약을 찾을 수 없습니다.'
        }, json_dumps_params={'ensure_ascii': False}, status=404)
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON'
        }, json_dumps_params={'ensure_ascii': False}, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, json_dumps_params={'ensure_ascii': False}, status=400)


@csrf_exempt
@require_http_methods(["POST"])
def reservation_cancel_view(request, reservation_id):
    """
    예약 취소 API
    
    POST /api/reservation/<reservation_id>/cancel/
    {
        "cancel_reason": "일정 변경으로 인한 취소"  # 선택
    }
    """
    try:
        reservation = Reservation.objects.get(reservation_id=reservation_id)
        
        # 이미 취소된 예약
        if reservation.status == 'cancelled':
            return JsonResponse({
                'success': False,
                'error': '이미 취소된 예약입니다.'
            }, json_dumps_params={'ensure_ascii': False}, status=400)
        
        # 완료된 예약은 취소 불가
        if reservation.status == 'completed':
            return JsonResponse({
                'success': False,
                'error': '완료된 예약은 취소할 수 없습니다.'
            }, json_dumps_params={'ensure_ascii': False}, status=400)
        
        # 취소 사유
        cancel_reason = ''
        if request.body:
            try:
                data = json.loads(request.body.decode('utf-8'))
                cancel_reason = data.get('cancel_reason', '')
            except:
                pass
        
        # 예약 취소
        reservation.status = 'cancelled'
        reservation.cancelled_at = timezone.now()
        if cancel_reason:
            reservation.memo = f"[취소 사유] {cancel_reason}\n\n{reservation.memo}".strip()
        reservation.save()
        
        return JsonResponse({
            'success': True,
            'message': '예약이 취소되었습니다.',
            'reservation': {
                'reservation_id': reservation.reservation_id,
                'status': reservation.status,
                'cancelled_at': reservation.cancelled_at.isoformat(),
            }
        }, json_dumps_params={'ensure_ascii': False})
    
    except Reservation.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': '예약을 찾을 수 없습니다.'
        }, json_dumps_params={'ensure_ascii': False}, status=404)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, json_dumps_params={'ensure_ascii': False}, status=400)
