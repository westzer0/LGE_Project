# 현재 구현 vs Playbook 비교 분석

## 📊 전체 구조 비교

| 항목 | Playbook 설계 | 현재 구현 | 상태 |
|------|---------------|-----------|------|
| **3단계 파이프라인** | Hard Filter → Scoring → GPT Explanation | ✅ 구현됨 | ✅ |
| **Hard Filter** | 정책 테이블 기반 | ✅ 하드코딩된 룰 | ⚠️ 개선 필요 |
| **Scoring 구조** | TotalScore = 5개 컴포넌트 합산 | ✅ 가중치 기반 (0~1.0) | ⚠️ 구조 차이 |
| **GPT Explanation** | 점수 breakdown 활용 | ✅ 부분 구현 | ⚠️ 개선 필요 |
| **정책 테이블** | JSON/CSV로 분리 | ❌ 하드코딩 | ❌ 미구현 |

---

## 🔍 상세 비교 분석

### Step 1 — Hard Filter

#### Playbook 설계
```python
# 정책 테이블 (Hard Filter Table)
{
  ("원룸", "냉장고"): {
    "max_depth_mm": 750,
    "ignore_category": false
  },
  ("1인", "세탁기"): {
    "max_capacity_kg": 24
  }
}
```

#### 현재 구현
```python
# api/utils/product_filters.py
def filter_by_housing_type(product, housing_type, pyung):
    if housing_type in ['studio', 'officetel']:
        if category == "KITCHEN" or "냉장고" in product_name:
            capacity = extract_capacity(spec, product)
            if capacity and capacity > 500:
                return False
```

**차이점:**
- ✅ 로직 자체는 잘 구현됨
- ❌ 정책 테이블로 분리되지 않음 (하드코딩)
- ❌ 수정 시 코드 변경 필요

**개선 방향:**
1. Hard Filter 룰을 JSON 파일로 분리
2. 정책 테이블 기반 필터링으로 변경

---

### Step 2 — Scoring Model

#### Playbook 설계
```
TotalScore
= SpecScore           (정수/실수, 예: +32)
+ PreferenceScore     (정수/실수, 예: +18)
+ LifestyleScore      (정수/실수, 예: +20)
+ ReviewScore         (정수/실수, 예: +9)
+ PriceScore          (정수/실수, 예: +8)
= 87.2
```

#### 현재 구현
```python
# api/utils/scoring.py
# 가중치 기반 (0.0 ~ 1.0)
weights = {
    "resolution": 0.35,
    "refresh_rate": 0.25,
    ...
}
final_score = weighted_average  # 0.0 ~ 1.0
```

**차이점:**
- ✅ 취향별 다른 가중치 구조 (최근 개선됨)
- ⚠️ 점수 범위가 다름 (0~1.0 vs 합산 점수)
- ⚠️ 5개 컴포넌트로 명확히 분리되지 않음
- ❌ ReviewScore가 별도로 계산되지 않음
- ⚠️ LifestyleScore가 PreferenceScore와 혼재

**개선 방향:**
1. TotalScore를 5개 컴포넌트 합산 구조로 변경
2. 각 Score를 독립 함수로 분리
3. 점수 범위를 합산 가능한 정수/실수로 변경 (예: 0~100)
4. ReviewScore를 별도로 계산 (배치 전처리 또는 실시간)

---

### Step 2-1) SpecScore 비교

#### Playbook 설계
```python
# Weight Table 기반
if family_size == 4 and fridge_capacity ≈ 800L:
    score += 10
```

#### 현재 구현
```python
# api/utils/scoring.py
def score_capacity(spec, profile, product):
    # 적정 용량 계산 후 점수 (0.0 ~ 1.0)
    if min_reasonable <= capacity <= max_reasonable:
        return 0.8
```

**차이점:**
- ✅ 로직 자체는 유사
- ⚠️ 점수 범위가 다름 (0~1.0 vs +10)
- ⚠️ Weight Table로 분리되지 않음

---

### Step 2-2) PreferenceScore 비교

#### Playbook 설계
```python
# 배율 적용
if priority == "design":
    total_score *= 1.5  # 또는 관련 스펙 점수에만 적용
```

#### 현재 구현
```python
# api/utils/scoring.py
# 취향별 가중치 구조로 이미 반영됨
TASTE_COMBINATION_WEIGHTS = {
    ("modern", "tech"): {
        "TV": {
            "resolution": 0.35,  # 높은 가중치
            "price_match": 0.05,  # 낮은 가중치
        }
    }
}
```

**차이점:**
- ✅ 취향별 가중치 구조로 잘 구현됨
- ⚠️ Playbook의 배율 방식과는 다르지만, 결과적으로 유사한 효과
- ✅ 우선순위 순서 반영 가능 (현재는 1순위만 반영)

**개선 방향:**
- 우선순위 배열([1순위, 2순위, ...])에 따른 차등 배율 적용

---

### Step 2-3) LifestyleScore 비교

#### Playbook 설계
```python
# 라이프스타일별 가산점
if cooking_frequency == "high":
    score += 5  # 냉장고 고용량, 인덕션 3구 등
```

#### 현재 구현
```python
# api/utils/scoring.py
# 필터링 단계에서 제외하거나, 스코어링에서 가중치로 반영
# LifestyleScore가 명시적으로 분리되지 않음
```

**차이점:**
- ⚠️ LifestyleScore가 별도 컴포넌트로 분리되지 않음
- ✅ 필터링 단계에서 라이프스타일 기반 제외는 구현됨
- ⚠️ 가산점 방식이 아닌 가중치 방식

**개선 방향:**
1. LifestyleScore를 별도 함수로 분리
2. 라이프스타일별 가산점/감점 방식 추가

---

### Step 2-4) ReviewScore 비교

#### Playbook 설계
```python
# 배치 전처리로 미리 계산
review_score = {
    "avg_rating": 4.7,
    "review_count": 210,
    "negative_keyword_index": 0.1
}
# 점수 변환: 0~10 또는 -10~+10
if avg_rating >= 4.7 and review_count >= 200:
    review_score_value = +8
```

#### 현재 구현
```python
# 현재 ReviewScore가 별도로 계산되지 않음
# 추천 문구 생성 시에만 리뷰 활용
```

**차이점:**
- ❌ ReviewScore가 점수 계산에 포함되지 않음
- ✅ 리뷰 데이터는 있음 (ProductReview 모델)
- ❌ 배치 전처리로 미리 계산하지 않음

**개선 방향:**
1. ReviewScore를 별도 컴포넌트로 추가
2. 배치 전처리로 미리 계산 (또는 실시간 계산)
3. 점수 breakdown에 포함

---

### Step 2-5) PriceScore 비교

#### Playbook 설계
```python
if price <= budget_amount:
    price_score = +10
elif price > budget_amount * 1.1:
    price_score = -5
elif price > budget_amount * 1.3:
    price_score = -15
```

#### 현재 구현
```python
# api/utils/scoring.py
def score_price_match(product, profile):
    # 0.0 ~ 1.0 범위로 반환
    if min_budget <= discount_price <= max_budget:
        return 0.7 ~ 1.0
    elif discount_price > max_budget:
        return 0.1 ~ 0.5  # 감점
```

**차이점:**
- ✅ 로직 자체는 유사
- ⚠️ 점수 범위가 다름 (0~1.0 vs +10/-15)
- ✅ 예산 범위 기반 점수 계산 구현됨

---

### Step 3 — GPT Explanation Layer

#### Playbook 설계
```json
{
  "score_breakdown": {
    "SpecScore": 32,
    "PreferenceScore": 18,
    "LifestyleScore": 20,
    "ReviewScore": 9,
    "PriceScore": 8
  },
  "explanation": {
    "why_summary": "...",
    "lifestyle_message": "...",
    "design_message": "...",
    "review_highlight": "..."
  }
}
```

#### 현재 구현
```python
# api/services/recommendation_reason_generator.py
def generate_reason(product, user_profile, taste_info, score):
    # 점수 breakdown 없이 추천 문구만 생성
    return "추천 이유 문구"
```

**차이점:**
- ✅ 추천 문구 생성은 구현됨
- ❌ 점수 breakdown 정보를 활용하지 않음
- ⚠️ 라이프스타일/디자인 메시지가 분리되지 않음
- ✅ 리뷰 분석은 부분적으로 활용

**개선 방향:**
1. 점수 breakdown을 입력으로 받아 설명에 활용
2. 라이프스타일 메시지, 디자인 메시지 분리
3. 리뷰 요약 정보 구조화

---

## 📋 정책 테이블 비교

### Playbook 설계
```
Hard Filter Table (JSON)
Weight Table (JSON)
- Sparse Matrix 형태
- 150~250줄 내외
- 코드 수정 없이 정책 변경 가능
```

### 현재 구현
```python
# api/utils/product_filters.py - 하드코딩
if household_size == 1:
    if capacity >= 200:
        return False

# api/utils/scoring.py - 하드코딩
TASTE_COMBINATION_WEIGHTS = {
    ("modern", "tech"): {...}
}
```

**차이점:**
- ❌ 정책 테이블로 분리되지 않음
- ❌ 수정 시 코드 변경 필요
- ⚠️ 로직은 잘 구현되어 있으나 유연성 부족

**개선 방향:**
1. Hard Filter Table을 JSON 파일로 분리
2. Weight Table을 JSON 파일로 분리
3. 정책 로더 함수 구현

---

## 🎯 개선 우선순위

### 우선순위 1 (필수)
1. ✅ **Hard Filter 로직 구현** - 완료
2. ✅ **Scoring 로직 구현** - 완료 (구조 개선 필요)
3. ⚠️ **GPT Explanation Layer** - 부분 완료 (개선 필요)

### 우선순위 2 (중요)
1. **ReviewScore 추가**
   - 배치 전처리 또는 실시간 계산
   - 점수 breakdown에 포함

2. **Scoring 구조 개선**
   - 5개 컴포넌트로 명확히 분리
   - 점수 범위 통일 (합산 가능한 형태)

3. **점수 Breakdown을 GPT에 전달**
   - 추천 문구 생성 시 활용
   - "왜 이 점수를 받았는지" 설명 가능

### 우선순위 3 (선택)
1. **정책 테이블 분리**
   - JSON 파일로 관리
   - 코드 수정 없이 정책 변경 가능

2. **LifestyleScore 분리**
   - 별도 컴포넌트로 계산
   - 가산점/감점 방식 추가

3. **우선순위 배열 반영**
   - [1순위, 2순위, ...] 순서에 따른 차등 배율

---

## 💡 결론

### 현재 상태
- ✅ **기본 구조는 잘 구현됨**: Hard Filter, Scoring, GPT Explanation 모두 작동
- ⚠️ **구조적 차이**: Playbook과 점수 계산 방식이 다름
- ⚠️ **정책 관리**: 하드코딩되어 있어 유연성 부족

### 개선 방향
1. **점수 구조 통일**: 5개 컴포넌트 합산 방식으로 변경
2. **ReviewScore 추가**: 점수 계산에 포함
3. **정책 테이블 분리**: 코드 수정 없이 정책 변경 가능하도록
4. **GPT Explanation 강화**: 점수 breakdown 활용

### 호환성
현재 구현도 잘 작동하고 있으므로, Playbook 구조로 전환하는 것은 **점진적 개선**으로 진행하는 것이 좋습니다. 기존 동작은 유지하면서 새로운 구조를 병행 개발 후 전환하는 방식을 권장합니다.


