from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import json
from openai import OpenAI
from .models import Product
from .rule_engine import build_profile, recommend_products

client = OpenAI(api_key="환경변수에서_불러오기")  # 코드에 하드코딩 X


def index_view(request):
    """
    루트 페이지: 온보딩 설문 + 추천 결과를 보여주는 기본 화면.
    """
    return render(request, "index.html")


@csrf_exempt
def recommend(request):
    if request.method != "POST":
        return JsonResponse({"detail": "POST only"}, status=405)

    try:
        data = json.loads(request.body.decode("utf-8"))
    except json.JSONDecodeError:
        return JsonResponse({"detail": "Invalid JSON"}, status=400)

    household = data.get("household", 2)
    budget = data.get("budget", 300)

    # 여기서 OpenAI 호출 (예: Responses API) :contentReference[oaicite:1]{index=1}
    response = client.responses.create(
        model="gpt-4.1-mini",
        input=(
            f"{household}인 가구, 예산 {budget}만원, "
            f"이사 가전 포트폴리오 추천 JSON 만들어줘 ..."
        ),
        response_format={"type": "json_object"},
    )

    result = json.loads(response.output[0].content[0].text)

    return JsonResponse(result)


@csrf_exempt
@require_http_methods(["POST"])
def recommend_view(request):
    """POST /api/recommend/ - 룰베이스 추천 API"""
    try:
        payload = json.loads(request.body.decode("utf-8"))
    except json.JSONDecodeError:
        return JsonResponse({"detail": "Invalid JSON"}, status=400)

    # UserProfile 생성
    profile = build_profile(payload)

    # 제품 추천
    recommendations = recommend_products(profile)

    return JsonResponse({
        "user_profile": payload,
        "recommendations": recommendations
    }, json_dumps_params={'ensure_ascii': False})


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
