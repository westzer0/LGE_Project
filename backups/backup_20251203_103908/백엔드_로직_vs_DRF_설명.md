# 백엔드 로직 vs DRF (명확한 구분)

## 🎯 핵심 차이

### **백엔드 로직 = "무엇을" 구현하는가**
- 실제 비즈니스 기능
- 데이터 처리 알고리즘
- 추천 엔진, 계산, 분석 등

### **DRF = "어떻게" 노출하는가**
- API를 만드는 도구
- 데이터 검증, 응답 포맷팅
- 외부와 통신하는 인터페이스

---

## 📊 현재 프로젝트 예시

### 1. 백엔드 로직 (이미 구현됨 ✅)

#### 예시 1: 추천 알고리즘
**파일**: `api/services/recommendation_engine.py`

```python
class RecommendationEngine:
    def get_recommendations(self, user_profile: dict):
        # 1. 제품 필터링 (백엔드 로직)
        filtered_products = self._filter_products(user_profile)
        
        # 2. 점수 계산 (백엔드 로직)
        scored_products = self._score_products(filtered_products, user_profile)
        
        # 3. 정렬 및 반환 (백엔드 로직)
        return sorted(scored_products, key=lambda x: x['score'], reverse=True)
```

**이것이 백엔드 로직입니다!**
- ✅ 어떤 제품을 추천할지 결정
- ✅ 어떻게 점수를 계산할지 구현
- ✅ 어떤 순서로 정렬할지 정의

#### 예시 2: 점수 계산 알고리즘
**파일**: `api/utils/scoring.py`

```python
def calculate_product_score(product, user_profile):
    # 해상도 점수 계산
    resolution_score = score_resolution(product, user_profile)
    
    # 가격 매칭 점수 계산
    price_score = score_price_match(product, user_profile)
    
    # 가족 크기 고려 점수
    household_score = score_household_size(product, user_profile)
    
    # 반려동물 고려 점수
    pet_score = score_pet_friendliness(product, user_profile)
    
    # 최종 점수 합산
    total_score = (resolution_score * 0.25 + 
                   price_score * 0.15 + 
                   household_score * 0.30 + 
                   pet_score * 0.30)
    
    return total_score
```

**이것도 백엔드 로직입니다!**
- ✅ 어떤 점수 체계를 사용할지
- ✅ 어떤 가중치를 적용할지
- ✅ 어떻게 점수를 합산할지

---

### 2. DRF (개선 가능한 부분 🔧)

#### 현재 방식 (일반 Django)
**파일**: `api/views.py`

```python
@csrf_exempt
@require_http_methods(["POST"])
def recommend_view(request):
    # 1. 요청 파싱 (API 도구 역할)
    data = json.loads(request.body.decode("utf-8"))
    
    # 2. 데이터 검증 (API 도구 역할)
    if not data.get('household_size'):
        return JsonResponse({'error': '필수'}, status=400)
    
    # 3. 백엔드 로직 호출
    result = recommendation_engine.get_recommendations(data)
    
    # 4. 응답 생성 (API 도구 역할)
    return JsonResponse(result, json_dumps_params={'ensure_ascii': False})
```

#### DRF로 개선 (API 도구만 바뀜)
```python
class RecommendAPIView(APIView):
    def post(self, request):
        # 1. 자동 요청 파싱 (DRF가 처리)
        serializer = RecommendRequestSerializer(data=request.data)
        
        # 2. 자동 데이터 검증 (DRF가 처리)
        if serializer.is_valid():
            # 3. 백엔드 로직 호출 (변경 없음!)
            result = recommendation_engine.get_recommendations(
                serializer.validated_data
            )
            # 4. 자동 응답 생성 (DRF가 처리)
            return Response(result)
        
        return Response(serializer.errors, status=400)
```

**중요**: 백엔드 로직(`recommendation_engine.get_recommendations()`)은 **그대로 유지**됩니다!

---

## 🔍 더 명확한 비교

### 백엔드 로직 (비즈니스 로직)

```python
# 추천 알고리즘 - "어떤 제품을 추천할까?"
def filter_products_by_size(products, user_space_size):
    # 공간 크기에 맞는 제품만 필터링
    return [p for p in products if p.size <= user_space_size]

# 가격 계산 - "얼마인가?"
def calculate_discount_price(original_price, discount_rate):
    return original_price * (1 - discount_rate)

# 점수 계산 - "얼마나 적합한가?"
def score_product(product, user_profile):
    score = 0
    if product.category == user_profile['preferred_category']:
        score += 10
    if product.price <= user_profile['budget']:
        score += 20
    return score
```

**이런 것들이 백엔드 로직입니다!**

### DRF (API 도구)

```python
# Serializer - "데이터 검증"
class ProductSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=100)
    price = serializers.IntegerField(min_value=0)
    
# View - "API 엔드포인트"
class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
```

**이런 것들이 DRF입니다!**

---

## 📋 현재 프로젝트 구조

### 이미 구현된 백엔드 로직 ✅

1. **추천 엔진** (`api/services/recommendation_engine.py`)
   - 제품 필터링
   - 점수 계산
   - 정렬 로직

2. **점수 계산** (`api/utils/scoring.py`)
   - 해상도 점수
   - 가격 매칭 점수
   - 가족 크기 점수
   - 반려동물 점수

3. **데이터 처리** (`api/models.py`)
   - 데이터베이스 모델
   - 데이터 관계 정의

4. **비즈니스 규칙** (`api/rule_engine.py`)
   - 사용자 프로필 구축
   - 규칙 기반 추천

### DRF로 개선 가능한 부분 🔧

1. **API 엔드포인트** (`api/views.py`)
   - 현재: 수동 JSON 파싱
   - DRF: 자동 처리

2. **데이터 검증**
   - 현재: 수동 검증
   - DRF: Serializer로 자동 검증

3. **에러 처리**
   - 현재: 각각 다름
   - DRF: 표준화

---

## 🎯 결론

### 백엔드 로직 구현
- ✅ **이미 완료됨!**
- 추천 알고리즘, 점수 계산, 필터링 등 모두 구현되어 있음

### DRF 도입
- 🔧 **API를 더 잘 만들기 위한 도구**
- 백엔드 로직은 그대로 두고, API 부분만 개선
- 코드가 더 깔끔해지고, 유지보수가 쉬워짐

### 비유로 이해하기

```
백엔드 로직 = 요리사 (실제 요리를 만드는 사람)
DRF = 접시/식탁 (요리를 어떻게 서빙할지)
```

- 요리사(백엔드 로직)는 이미 요리를 만들 수 있음 ✅
- DRF는 더 예쁜 접시로, 더 체계적으로 서빙하는 것 🔧

---

## 💡 실제 예시

### 시나리오: "4인 가족을 위한 TV 추천"

#### 백엔드 로직 (변경 없음)
```python
# 1. 가족 크기 확인
if household_size == 4:
    recommended_size = "55인치 이상"

# 2. 제품 필터링
tvs = Product.objects.filter(
    category='TV',
    size__gte=55
)

# 3. 점수 계산
for tv in tvs:
    tv.score = calculate_score(tv, user_profile)

# 4. 정렬
recommended_tvs = sorted(tvs, key=lambda x: x.score, reverse=True)
```

#### DRF (API만 개선)
```python
# Serializer: 데이터 검증만
class RecommendRequestSerializer(serializers.Serializer):
    household_size = serializers.IntegerField(min_value=1, max_value=10)

# View: 백엔드 로직 호출만
class RecommendAPIView(APIView):
    def post(self, request):
        serializer = RecommendRequestSerializer(data=request.data)
        if serializer.is_valid():
            # 위의 백엔드 로직 그대로 사용!
            result = recommendation_engine.get_recommendations(
                serializer.validated_data
            )
            return Response(result)
```

---

## ✅ 요약

| 구분 | 백엔드 로직 | DRF |
|------|-----------|-----|
| **목적** | 비즈니스 기능 구현 | API 도구 |
| **현재 상태** | ✅ 이미 구현됨 | 🔧 개선 가능 |
| **변경 필요** | ❌ 변경 불필요 | ✅ API 부분만 |
| **예시** | 추천 알고리즘, 점수 계산 | 데이터 검증, 응답 포맷 |

**결론**: 
- 백엔드 로직은 이미 잘 구현되어 있습니다! ✅
- DRF는 이 로직을 더 깔끔하게 외부에 노출하는 도구입니다! 🔧

