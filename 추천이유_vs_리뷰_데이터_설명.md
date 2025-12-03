# 추천 이유 데이터 vs 리뷰 데이터 상관관계

## 📊 데이터 구조 개요

### 1. **ProductReview (리뷰 데이터)**
- **관계**: Product와 **1:N** (한 제품에 여러 리뷰)
- **의미**: 실제 고객이 작성한 **원본 리뷰 데이터**
- **저장 내용**:
  - `star`: 별점/평가
  - `review_text`: 리뷰 본문 (고객이 직접 작성한 텍스트)
  - `source`: 데이터 출처 (예: "LG전자_리뷰_냉장고.csv")

**예시**:
```
제품: T875MEE111 (냉장고)
리뷰 1: "새로 이사하면서 냉장고 구입한건데 실용성도 좋고 디자인도 이쁘고 색상도 깔끔하니 맘에 들어요"
리뷰 2: "양문형으로 상단이 모두 냉장실이여서 용기의 정리폭이 넓어서 정리도 되고 찾기도 좋고 너무 좋아요"
리뷰 3: "베이지 디자인 모두 맘에 듭니다"
... (수백~수천 개의 리뷰)
```

### 2. **ProductRecommendReason (추천 이유 데이터)**
- **관계**: Product와 **1:1** (한 제품에 하나의 추천 이유)
- **의미**: 리뷰 데이터를 **분석/요약**하여 생성한 **제품 추천 이유**
- **저장 내용**:
  - `reason_text`: 추천 이유 텍스트 (리뷰 요약 또는 LLM 생성)
  - `source`: 데이터 출처 (예: "냉장고_모델별_추천이유.csv")

**예시**:
```
제품: T875MEE111 (냉장고)
추천 이유: "많은 사용자 리뷰에서 '새로이사하면서 냉장고 구입한건데 실용성도 좋고 디자인도이쁘고 색상도깔끔하니 맘에들어요...' 라는 의견이 반복적으로 나타나 이 모델을 추천할 만합니다."
```

---

## 🔗 상관관계

### **추천 이유는 리뷰 데이터의 요약/분석 결과입니다**

```
리뷰 데이터 (원본)
    ↓
[분석/요약 과정]
    ↓
추천 이유 데이터 (요약본)
```

### 구체적인 관계:

1. **데이터 소스**:
   - 리뷰: `data/리뷰/*.csv` (예: "LG전자_리뷰_냉장고.csv")
   - 추천 이유: `data/리뷰_인구통계, 추천이유/*추천이유*.csv` (예: "냉장고_모델별_추천이유.csv")

2. **생성 방식**:
   - **수동 생성**: CSV 파일에 이미 작성된 추천 이유를 import
   - **자동 생성**: ChatGPT API를 사용하여 리뷰를 분석하고 요약 (현재 코드에는 있지만 실제 사용은 제한적)

3. **데이터 특성**:
   - **리뷰**: 개별 고객의 생생한 경험담, 다양한 의견, 긍정/부정 혼재
   - **추천 이유**: 리뷰의 공통점을 추출한 요약, 주로 긍정적 측면 강조

---

## 💡 추천 이유 데이터의 의미

### 현재 시스템에서의 역할:

1. **제품 추천 시 표시**:
   - 사용자에게 "왜 이 제품을 추천하는지" 설명
   - 예: "많은 사용자들이 디자인과 실용성을 칭찬했습니다"

2. **신뢰도 향상**:
   - 실제 고객 리뷰 기반이라는 점을 강조
   - "많은 사용자 리뷰에서..." 같은 표현으로 신뢰성 확보

3. **간결한 정보 제공**:
   - 수백 개의 리뷰를 모두 읽을 수 없으므로 핵심만 요약
   - 사용자가 빠르게 제품의 장점을 파악할 수 있음

---

## 🔄 현재 코드에서의 사용 현황

### 1. **데이터 Import** (`api/management/commands/import_reviews_demographics.py`):
```python
# 추천 이유는 CSV에서 직접 import
ProductRecommendReason.objects.update_or_create(
    product=product,
    defaults={'reason_text': reason_text}
)

# 리뷰는 개별적으로 여러 개 저장
ProductReview.objects.create(
    product=product,
    review_text=review_text
)
```

### 2. **추천 이유 생성** (`api/services/recommendation_engine.py`):
현재는 **DB에 저장된 추천 이유를 사용하지 않고**, 
**실시간으로 ChatGPT를 통해 생성**하고 있습니다:

```python
def _build_recommendation_reason(self, product, user_profile, score):
    # 점수 기반으로 간단한 이유 생성
    # DB의 ProductRecommendReason을 사용하지 않음
    reasons = []
    if score >= 0.8:
        reasons.append("당신의 선호도에 가장 잘 맞는 제품입니다.")
    # ...
    return " ".join(reasons)
```

### 3. **ChatGPT 서비스** (`api/services/chatgpt_service.py`):
리뷰 요약 기능이 있지만, 현재는 **사용되지 않고 있습니다**:

```python
def summarize_reviews(cls, reviews: list, product_name: str = "") -> str:
    """리뷰 요약 - 현재 미사용"""
    # 리뷰들을 ChatGPT에 보내서 요약 생성
    # 하지만 실제 추천 엔진에서는 호출되지 않음
```

---

## 🎯 개선 가능한 부분

### 현재 문제점:
1. **DB에 저장된 추천 이유를 사용하지 않음**
   - CSV에서 import한 추천 이유가 있지만 활용하지 않음
   - 매번 ChatGPT로 생성하거나 간단한 템플릿만 사용

2. **리뷰 데이터와 추천 이유의 연결이 약함**
   - 리뷰를 분석하여 추천 이유를 생성하는 로직이 없음
   - 두 데이터가 별개로 관리됨

### 개선 방안:

#### 옵션 1: DB 추천 이유 활용
```python
def _build_recommendation_reason(self, product, user_profile, score):
    # DB에 저장된 추천 이유가 있으면 사용
    if hasattr(product, 'recommend_reason') and product.recommend_reason.reason_text:
        return product.recommend_reason.reason_text
    
    # 없으면 ChatGPT로 생성
    return self._generate_with_chatgpt(product, user_profile)
```

#### 옵션 2: 리뷰 기반 실시간 생성
```python
def _build_recommendation_reason(self, product, user_profile, score):
    # 제품의 리뷰들을 가져와서 ChatGPT로 요약
    reviews = product.reviews.all()[:20]  # 최근 20개
    review_texts = [r.review_text for r in reviews]
    
    if review_texts:
        from api.services.chatgpt_service import ChatGPTService
        return ChatGPTService.summarize_reviews(review_texts, product.name)
    
    # 리뷰가 없으면 기본 메시지
    return "조건에 맞는 추천 제품입니다."
```

#### 옵션 3: 하이브리드 방식
```python
def _build_recommendation_reason(self, product, user_profile, score):
    # 1순위: DB에 저장된 추천 이유 (CSV에서 import한 것)
    if hasattr(product, 'recommend_reason') and product.recommend_reason.reason_text:
        base_reason = product.recommend_reason.reason_text
    else:
        base_reason = None
    
    # 2순위: 사용자 맞춤 정보 추가
    user_custom = f"{user_profile.get('household_size', 2)}인 가구에 적합"
    
    # 3순위: 최신 리뷰 요약 (선택적)
    if score >= 0.8:  # 높은 점수일 때만 리뷰 요약 추가
        reviews = product.reviews.all()[:10]
        if reviews:
            review_summary = ChatGPTService.summarize_reviews(
                [r.review_text for r in reviews], 
                product.name
            )
            return f"{base_reason or user_custom} {review_summary}"
    
    return base_reason or user_custom
```

---

## 📝 요약

### 질문: "추천 이유 데이터와 리뷰 데이터는 별개의 데이터인가?"

**답변**: 
- **구조적으로는 별개**이지만, **의미적으로는 연결**되어 있습니다.
- **리뷰 데이터** = 원본 (고객이 직접 작성)
- **추천 이유 데이터** = 요약/분석 결과 (리뷰에서 추출)

### 질문: "추천 이유 데이터가 어떤 의미를 갖는지 모르겠어"

**답변**:
- **의미**: "왜 이 제품을 추천하는지"에 대한 **간결한 설명**
- **출처**: 실제 고객 리뷰를 분석하여 생성
- **목적**: 사용자가 수백 개의 리뷰를 읽지 않아도 핵심 장점을 빠르게 파악
- **현재 상태**: DB에 저장되어 있지만 실제로는 **거의 사용되지 않음**

### 개선 제안:
1. DB에 저장된 추천 이유를 실제로 활용하도록 코드 수정
2. 리뷰 데이터를 실시간으로 분석하여 추천 이유 생성
3. 사용자 맞춤 정보와 리뷰 요약을 결합한 하이브리드 방식 도입



