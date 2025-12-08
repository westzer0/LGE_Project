# Django REST Framework (DRF)가 백엔드 로직에 주는 도움

## 🎯 현재 상황 vs DRF 사용

### 현재 방식 (일반 Django Views)
```python
@csrf_exempt
@require_http_methods(["POST"])
def recommend_view(request):
    data = json.loads(request.body.decode("utf-8"))
    
    # 수동으로 데이터 검증
    if not data.get('household_size'):
        return JsonResponse({'error': 'household_size 필수'}, status=400)
    
    # 수동으로 JSON 응답
    return JsonResponse(result, json_dumps_params={'ensure_ascii': False})
```

### DRF 사용 시
```python
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import RecommendRequestSerializer

class RecommendAPIView(APIView):
    def post(self, request):
        serializer = RecommendRequestSerializer(data=request.data)
        if serializer.is_valid():
            # 자동 검증 완료
            result = recommendation_engine.get_recommendations(
                serializer.validated_data
            )
            return Response(result, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
```

## 💡 DRF의 주요 이점

### 1. **자동 데이터 검증 및 변환 (Serializer)**

**현재 방식:**
```python
# 수동으로 하나씩 확인
if not data.get('household_size'):
    return JsonResponse({'error': '필수'}, status=400)
if not isinstance(data.get('household_size'), int):
    return JsonResponse({'error': '숫자여야 함'}, status=400)
```

**DRF 사용:**
```python
class RecommendRequestSerializer(serializers.Serializer):
    household_size = serializers.IntegerField(
        min_value=1, 
        max_value=10,
        required=True,
        error_messages={
            'required': '가족 인원수는 필수입니다.',
            'min_value': '최소 1명 이상이어야 합니다.',
            'max_value': '최대 10명까지 가능합니다.'
        }
    )
    has_pet = serializers.BooleanField(default=False)
    categories = serializers.ListField(
        child=serializers.CharField(),
        allow_empty=False
    )
    
    def validate_household_size(self, value):
        if value < 1:
            raise serializers.ValidationError("가족 인원수는 1명 이상이어야 합니다.")
        return value
```

✅ **장점**: 
- 자동 검증
- 에러 메시지 일관성
- 타입 변환 자동 처리
- 커스텀 검증 로직 추가 쉬움

### 2. **ViewSet으로 CRUD 자동 생성**

**현재 방식:**
```python
# 각 엔드포인트마다 수동으로 작성
@require_http_methods(["GET"])
def portfolio_list_view(request):
    # 리스트 로직
    pass

@require_http_methods(["GET"])
def portfolio_detail_view(request, portfolio_id):
    # 상세 로직
    pass

@require_http_methods(["POST"])
def portfolio_save_view(request):
    # 저장 로직
    pass
```

**DRF 사용:**
```python
from rest_framework import viewsets
from rest_framework.decorators import action

class PortfolioViewSet(viewsets.ModelViewSet):
    queryset = Portfolio.objects.all()
    serializer_class = PortfolioSerializer
    
    # 자동으로 생성되는 엔드포인트:
    # GET    /api/portfolios/          - 리스트
    # POST   /api/portfolios/          - 생성
    # GET    /api/portfolios/{id}/     - 상세
    # PUT    /api/portfolios/{id}/     - 전체 수정
    # PATCH  /api/portfolios/{id}/     - 부분 수정
    # DELETE /api/portfolios/{id}/     - 삭제
    
    @action(detail=True, methods=['post'])
    def share(self, request, pk=None):
        # 커스텀 엔드포인트: /api/portfolios/{id}/share/
        portfolio = self.get_object()
        # 공유 로직
        return Response({'share_url': f'/portfolio/{portfolio.portfolio_id}/'})
```

✅ **장점**:
- 코드 중복 제거
- 표준 REST API 구조
- 자동 URL 라우팅

### 3. **인증/권한 관리**

**현재 방식:**
```python
# 수동으로 인증 체크
def portfolio_save_view(request):
    # 인증 로직 직접 구현
    if not request.user.is_authenticated:
        return JsonResponse({'error': '로그인 필요'}, status=401)
```

**DRF 사용:**
```python
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import TokenAuthentication

class PortfolioViewSet(viewsets.ModelViewSet):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    # 자동으로 인증 체크!
```

✅ **장점**:
- 다양한 인증 방식 지원 (Token, Session, JWT 등)
- 권한 관리 체계화
- 코드 간결화

### 4. **페이징**

**현재 방식:**
```python
# 수동으로 페이지네이션 구현
def portfolio_list_view(request):
    page = int(request.GET.get('page', 1))
    page_size = int(request.GET.get('page_size', 20))
    offset = (page - 1) * page_size
    
    portfolios = Portfolio.objects.all()[offset:offset+page_size]
    # 총 개수, 다음 페이지 등 모두 수동 처리
```

**DRF 사용:**
```python
class PortfolioViewSet(viewsets.ModelViewSet):
    queryset = Portfolio.objects.all()
    serializer_class = PortfolioSerializer
    # 설정만 하면 자동 페이징!
```

**settings.py:**
```python
REST_FRAMEWORK = {
    'PAGE_SIZE': 20,
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
}
```

✅ **장점**:
- 자동 페이징
- 메타데이터 자동 생성 (다음 페이지, 총 개수 등)
- 다양한 페이징 스타일 지원

### 5. **필터링/검색**

**현재 방식:**
```python
# 수동으로 필터링
def portfolio_list_view(request):
    queryset = Portfolio.objects.all()
    
    style_type = request.GET.get('style_type')
    if style_type:
        queryset = queryset.filter(style_type=style_type)
    
    user_id = request.GET.get('user_id')
    if user_id:
        queryset = queryset.filter(user_id=user_id)
    
    # 복잡한 검색 로직...
```

**DRF 사용:**
```python
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter

class PortfolioViewSet(viewsets.ModelViewSet):
    queryset = Portfolio.objects.all()
    serializer_class = PortfolioSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ['style_type', 'user_id', 'status']
    search_fields = ['style_title', 'style_subtitle']
    
    # 자동으로 생성되는 필터:
    # /api/portfolios/?style_type=modern
    # /api/portfolios/?search=미니멀
```

✅ **장점**:
- 간단한 설정으로 강력한 필터링
- URL 쿼리 파라미터로 자동 필터링
- 복잡한 검색 로직 간소화

### 6. **자동 API 문서화**

**DRF 사용 시:**
- Swagger/OpenAPI 문서 자동 생성
- 브라우저에서 직접 API 테스트 가능
- 팀 협업에 유용

```python
# config/urls.py
from rest_framework.documentation import include_docs_urls

urlpatterns = [
    path('api/docs/', include_docs_urls(title='API 문서')),
]
```

접속: `http://localhost:8000/api/docs/`

✅ **장점**:
- API 문서 자동 생성
- 프론트엔드 개발자와 소통 용이
- 문서와 코드 동기화

### 7. **에러 처리 표준화**

**현재 방식:**
```python
# 각 뷰마다 다른 에러 형식
try:
    portfolio = Portfolio.objects.get(portfolio_id=id)
except Portfolio.DoesNotExist:
    return JsonResponse({'error': '찾을 수 없음'}, status=404)
except Exception as e:
    return JsonResponse({'error': str(e)}, status=500)
```

**DRF 사용:**
```python
# 표준화된 에러 응답 자동 생성
# 404: {"detail": "찾을 수 없습니다."}
# 400: {"field_name": ["에러 메시지"]}
# 500: 표준 에러 형식
```

✅ **장점**:
- 일관된 에러 형식
- 클라이언트에서 처리 쉬움
- 디버깅 용이

## 🎯 실제 프로젝트에 적용 예시

### 현재 프로젝트의 추천 API를 DRF로 변환

**변경 전:**
```python
@csrf_exempt
@require_http_methods(["POST"])
def recommend_view(request):
    try:
        data = json.loads(request.body.decode("utf-8"))
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)
    
    # 수동 검증
    if not data.get('household_size'):
        return JsonResponse({"error": "household_size 필수"}, status=400)
    
    # 추천 로직
    result = recommendation_engine.get_recommendations(data)
    
    return JsonResponse(result, json_dumps_params={'ensure_ascii': False})
```

**변경 후:**
```python
# serializers.py
class RecommendRequestSerializer(serializers.Serializer):
    vibe = serializers.ChoiceField(
        choices=['modern', 'cozy', 'natural', 'luxury'],
        required=True
    )
    household_size = serializers.IntegerField(min_value=1, max_value=10)
    has_pet = serializers.BooleanField(default=False)
    housing_type = serializers.ChoiceField(
        choices=['apartment', 'house', 'officetel']
    )
    pyung = serializers.IntegerField(min_value=10, max_value=100)
    priority = serializers.ChoiceField(
        choices=['tech', 'design', 'price', 'balance']
    )
    budget_level = serializers.ChoiceField(
        choices=['low', 'medium', 'high']
    )
    categories = serializers.ListField(
        child=serializers.CharField(),
        allow_empty=False
    )

class RecommendResponseSerializer(serializers.Serializer):
    success = serializers.BooleanField()
    products = serializers.ListField()
    match_score = serializers.FloatField()

# views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

class RecommendAPIView(APIView):
    def post(self, request):
        serializer = RecommendRequestSerializer(data=request.data)
        
        if serializer.is_valid():
            user_profile = serializer.validated_data
            result = recommendation_engine.get_recommendations(user_profile)
            
            response_serializer = RecommendResponseSerializer(result)
            return Response(
                response_serializer.data,
                status=status.HTTP_200_OK
            )
        
        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )
```

## 📊 비교표

| 기능 | 현재 방식 | DRF 사용 | 개선도 |
|------|----------|----------|--------|
| 데이터 검증 | 수동 | 자동 | ⭐⭐⭐⭐⭐ |
| 에러 처리 | 각각 다름 | 표준화 | ⭐⭐⭐⭐⭐ |
| API 문서 | 없음 | 자동 생성 | ⭐⭐⭐⭐⭐ |
| CRUD 생성 | 수동 | 자동 | ⭐⭐⭐⭐ |
| 페이징 | 수동 | 자동 | ⭐⭐⭐⭐ |
| 필터링 | 수동 | 자동 | ⭐⭐⭐⭐ |
| 인증/권한 | 수동 | 내장 | ⭐⭐⭐⭐⭐ |
| 코드 길이 | 많음 | 적음 | ⭐⭐⭐⭐⭐ |

## 🎯 결론

**DRF를 사용하면:**
- ✅ 코드가 훨씬 간결하고 읽기 쉬움
- ✅ 유지보수가 쉬움
- ✅ 표준 REST API 구조
- ✅ 자동 문서화
- ✅ 강력한 기능들 (페이징, 필터링, 검색)
- ✅ 팀 협업에 유리

**현재 프로젝트에 추천:**
- 새 API 엔드포인트부터 DRF로 작성
- 기존 API는 점진적으로 DRF로 전환
- 특히 추천 API, 포트폴리오 API는 DRF로 변환하면 큰 이점

## 🚀 시작하기

```bash
# 1. 설치
pip install djangorestframework

# 2. settings.py에 추가
INSTALLED_APPS = [
    ...
    'rest_framework',
]

# 3. 첫 번째 ViewSet 작성
# api/views.py
from rest_framework import viewsets
from .serializers import PortfolioSerializer

class PortfolioViewSet(viewsets.ModelViewSet):
    queryset = Portfolio.objects.all()
    serializer_class = PortfolioSerializer
```

