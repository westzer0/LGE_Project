# Django REST Framework (DRF) 가이드

## 📚 Django REST Framework란?

Django REST Framework는 Django에서 **RESTful API**를 쉽고 체계적으로 만들 수 있게 해주는 강력한 라이브러리입니다.

## 🎯 현재 프로젝트 vs DRF 사용

### 현재 방식 (일반 Django)
```python
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

@csrf_exempt
@require_http_methods(["POST"])
def recommend_view(request):
    data = json.loads(request.body.decode("utf-8"))
    # 수동으로 JSON 파싱
    # 수동으로 에러 처리
    # 수동으로 응답 생성
    return JsonResponse({'success': True, ...})
```

**단점:**
- JSON 파싱을 직접 해야 함
- 에러 처리를 직접 작성해야 함
- API 문서화가 어려움
- 인증/권한 처리가 복잡
- 코드 중복이 많음

### DRF 사용 시
```python
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import RecommendSerializer

class RecommendAPIView(APIView):
    def post(self, request):
        serializer = RecommendSerializer(data=request.data)
        if serializer.is_valid():
            # 자동으로 데이터 검증 및 변환
            result = recommendation_engine.get_recommendations(...)
            return Response(result, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
```

**장점:**
- ✅ 자동 JSON 파싱 및 검증
- ✅ 자동 에러 처리
- ✅ API 문서 자동 생성 (Swagger/OpenAPI)
- ✅ 강력한 인증/권한 시스템
- ✅ 페이징, 필터링 등 내장 기능
- ✅ 코드가 훨씬 간결하고 유지보수 쉬움

## 🚀 설치 방법

### 1. 패키지 설치
```powershell
pip install djangorestframework
```

### 2. settings.py 설정
```python
INSTALLED_APPS = [
    ...
    'rest_framework',  # 추가
    'api',
]
```

### 3. URL 설정 (선택사항)
```python
# config/urls.py
from rest_framework.documentation import include_docs_urls

urlpatterns = [
    ...
    path('api/docs/', include_docs_urls(title='API 문서')),
]
```

## 💡 DRF의 주요 기능

### 1. **Serializer** - 데이터 검증 및 변환
```python
from rest_framework import serializers

class RecommendRequestSerializer(serializers.Serializer):
    vibe = serializers.CharField(required=True)
    household_size = serializers.IntegerField(min_value=1, max_value=10)
    has_pet = serializers.BooleanField(default=False)
    categories = serializers.ListField(child=serializers.CharField())
```

### 2. **ViewSet** - CRUD 자동 생성
```python
from rest_framework import viewsets
from rest_framework.decorators import action

class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    
    # 자동으로 생성되는 엔드포인트:
    # GET /api/products/ - 리스트
    # POST /api/products/ - 생성
    # GET /api/products/{id}/ - 상세
    # PUT /api/products/{id}/ - 수정
    # DELETE /api/products/{id}/ - 삭제
    
    @action(detail=True, methods=['get'])
    def recommendations(self, request, pk=None):
        # 커스텀 엔드포인트: /api/products/{id}/recommendations/
        ...
```

### 3. **인증/권한**
```python
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import TokenAuthentication

class ProtectedAPIView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    ...
```

### 4. **페이징**
```python
# settings.py
REST_FRAMEWORK = {
    'PAGE_SIZE': 20,
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
}
```

### 5. **필터링/검색**
```python
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter

class ProductViewSet(viewsets.ModelViewSet):
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ['category', 'price']
    search_fields = ['name', 'description']
    # /api/products/?category=TV&search=올레드
```

### 6. **자동 API 문서화**
DRF를 사용하면 Swagger/OpenAPI 문서가 자동으로 생성됩니다!
- `/api/docs/` - 브라우저에서 API 테스트 가능

## 📖 실제 적용 예시

### 예시 1: 현재 추천 API를 DRF로 변환

**변경 전:**
```python
@csrf_exempt
@require_http_methods(["POST"])
def recommend_view(request):
    data = json.loads(request.body.decode("utf-8"))
    # ...
    return JsonResponse(result)
```

**변경 후:**
```python
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import RecommendRequestSerializer

class RecommendAPIView(APIView):
    def post(self, request):
        serializer = RecommendRequestSerializer(data=request.data)
        if serializer.is_valid():
            user_profile = serializer.validated_data
            result = recommendation_engine.get_recommendations(user_profile)
            return Response(result, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
```

### 예시 2: Product 리스트 API

```python
from rest_framework import viewsets
from rest_framework.decorators import action
from .models import Product
from .serializers import ProductSerializer

class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.filter(is_active=True)
    serializer_class = ProductSerializer
    
    @action(detail=False, methods=['get'])
    def by_category(self, request):
        category = request.query_params.get('category')
        products = self.queryset.filter(category=category)
        serializer = self.get_serializer(products, many=True)
        return Response(serializer.data)
```

## 🎁 DRF가 제공하는 추가 기능

1. **브라우저 기반 API 테스트 인터페이스**
   - `/api/products/` 접속하면 브라우저에서 바로 테스트 가능

2. **자동 Swagger 문서**
   - `/api/docs/` - API 문서 자동 생성

3. **Rate Limiting (API 호출 제한)**
   ```python
   REST_FRAMEWORK = {
       'DEFAULT_THROTTLE_CLASSES': [
           'rest_framework.throttling.AnonRateThrottle',
       ],
       'DEFAULT_THROTTLE_RATES': {
           'anon': '100/hour',
       }
   }
   ```

4. **버전 관리**
   ```python
   # /api/v1/products/
   # /api/v2/products/
   ```

## 📦 설치 및 설정

### 설치
```powershell
pip install djangorestframework
```

### settings.py 추가
```python
INSTALLED_APPS = [
    ...
    'rest_framework',
    'api',
]
```

### 기본 설정 (선택사항)
```python
REST_FRAMEWORK = {
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
        'rest_framework.renderers.BrowsableAPIRenderer',  # 브라우저 테스트 UI
    ],
}
```

## 🔄 마이그레이션 계획

현재 프로젝트의 API를 DRF로 점진적으로 전환할 수 있습니다:

1. **1단계**: DRF 설치 및 기본 설정
2. **2단계**: 새 API 엔드포인트부터 DRF로 작성
3. **3단계**: 기존 API를 점진적으로 DRF로 변환

## 🎯 결론

**DRF를 사용하면:**
- ✅ 코드가 훨씬 간결하고 읽기 쉬움
- ✅ API 문서가 자동으로 생성됨
- ✅ 표준화된 REST API 구조
- ✅ 강력한 인증/권한 시스템
- ✅ 유지보수가 훨씬 쉬움
- ✅ 테스트가 용이함

**단점:**
- ❌ 학습 곡선 (하지만 크지 않음)
- ❌ 약간의 추가 의존성

**권장:** 현재 프로젝트처럼 API가 많고 복잡하다면 DRF 도입을 적극 추천합니다!

