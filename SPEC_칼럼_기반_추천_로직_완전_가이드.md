# SPEC 칼럼 기반 추천 로직 완전 가이드

## 📋 요구사항

Oracle DB PRODUCT SPEC 테이블 구조를 기반으로:

1. **SPEC_TYPE**: `COMMON` 또는 `VARIANT`
   - **COMMON**: 모든 제품 종류에 100% 공통 칼럼 → **반드시** 점수 산출 로직에 포함
   - **VARIANT**: 특정 제품 종류에만 있는 칼럼 → 등장 빈도와 온보딩 정보에 따라 포함/제외

2. **SPEC_KEY**: 점수 산정에 사용할 수 있는 스펙 칼럼

3. **추천 프로세스**:
   - **#1**: 칼럼 점수 산출 결과에 따라 패키지에 포함될 가전 종류 확인 (기준 선정 필요)
   - **#2**: 가전 종류가 정해지면, 각 종류별 상위 3개 모델 추천

---

## 🏗️ 전체 아키텍처

```
┌─────────────────────────────────────────────────────────────┐
│                    칼럼 점수 기반 추천 엔진                    │
└─────────────────────────────────────────────────────────────┘
                           │
        ┌──────────────────┼──────────────────┐
        │                  │                  │
        ▼                  ▼                  ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│ SPEC 구조    │  │ 제품 종류별   │  │ 칼럼 점수에   │
│ 분석         │  │ 칼럼 점수     │  │ 따른 제품     │
│              │  │ 산출          │  │ 종류 선정     │
└──────────────┘  └──────────────┘  └──────────────┘
        │                  │                  │
        └──────────────────┼──────────────────┘
                           │
                           ▼
        ┌──────────────────────────────────┐
        │   각 제품 종류별 상위 3개 모델     │
        │   추천                            │
        └──────────────────────────────────┘
```

---

## 🔧 구현 파일 구조

### 1. `api/utils/spec_column_scorer.py`

**역할**: SPEC 칼럼 기반 점수 산출

**주요 클래스**: `SpecColumnScorer`

#### 핵심 메서드

1. **`analyze_spec_structure(products)`**
   ```python
   # SPEC 구조 분석
   - COMMON 칼럼 식별: 모든 제품 종류에 100% 존재
   - VARIANT 칼럼 식별: 제품 종류별로 다름
   - SPEC_KEY별 등장 빈도 계산
   ```

2. **`get_scoring_spec_keys(product_type, user_profile, onboarding_data)`**
   ```python
   # 점수 산출에 사용할 SPEC_KEY 목록 반환
   - COMMON 칼럼: 반드시 포함
   - VARIANT 칼럼: 조건부 포함
     * 등장 빈도 >= 50% AND 중요도 >= 0.8
     * 또는 등장 빈도 >= 80%
   ```

3. **`calculate_product_type_column_score(...)`**
   ```python
   # 제품 종류별 칼럼 점수 산출
   column_score = common_score * 0.7 + variant_score * 0.3
   ```

---

### 2. `api/services/column_based_recommendation_engine.py`

**역할**: 칼럼 점수 기반 추천 엔진 오케스트레이션

**주요 클래스**: `ColumnBasedRecommendationEngine`

#### 추천 프로세스

```python
def get_recommendations(...):
    # 1. 전체 제품 필터링
    filtered_products = _filter_products(user_profile)
    
    # 2. 제품 종류별 그룹화
    products_by_type = group_products_by_type(products_list)
    
    # 3. SPEC 구조 분석 (최초 1회)
    spec_column_scorer.analyze_spec_structure(products_list)
    
    # 4. 제품 종류별 칼럼 점수 산출
    column_scores = _calculate_product_type_column_scores(...)
    
    # 5. 칼럼 점수에 따라 패키지에 포함될 가전 종류 선정
    selected_types = _select_product_types_for_package(...)
    
    # 6. 각 가전 종류별 상위 3개 모델 추천
    recommendations = _recommend_top_products_by_type(...)
    
    return recommendations
```

---

## 📊 단계별 상세 설명

### Step 1: SPEC 구조 분석

#### COMMON 칼럼 식별

```python
# 모든 제품 종류에서 100% 존재하는 칼럼만 COMMON으로 식별
common_spec_keys = set(all_spec_keys)

for product_type in product_types:
    type_products = products_by_type[product_type]
    
    for product in type_products:
        spec_json = json.loads(product.spec.spec_json)
        spec_keys = set(spec_json.keys())
        
        # 해당 제품 종류에서 100% 존재하는 칼럼만
        for key in spec_keys:
            frequency = count_occurrence(key, type_products)
            if frequency == len(type_products):  # 100% 존재
                type_common_keys.add(key)
    
    # 모든 제품 종류에서 공통인 칼럼만 남김
    common_spec_keys = common_spec_keys.intersection(type_common_keys)
```

**예시**:
- 모든 제품에 공통: `가격`, `브랜드`, `카테고리` → COMMON
- 일부 제품만: `용량`, `해상도`, `에너지등급` → VARIANT

---

#### VARIANT 칼럼 식별

```python
# COMMON이 아닌 칼럼은 모두 VARIANT
variant_keys_by_type = {}

for product_type in product_types:
    all_keys = get_all_spec_keys(product_type)
    variant_keys = all_keys - common_spec_keys
    variant_keys_by_type[product_type] = variant_keys
```

**예시**:
- 세탁기 VARIANT: `용량(kg)`, `세탁모드`, `에너지등급`
- TV VARIANT: `해상도`, `주사율`, `패널타입`
- 냉장고 VARIANT: `총용량(L)`, `냉장실용량`, `냉동실용량`

---

### Step 2: VARIANT 칼럼 포함/제외 결정

#### 등장 빈도 확인

```python
frequency_ratio = occurrence_count / total_products_in_type

# 최소 등장 빈도 기준
if frequency_ratio >= 0.5:  # 50% 이상
    # 온보딩 정보에 따른 중요도 조정
    importance = calculate_importance(spec_key, user_profile, onboarding_data)
    
    if importance >= 0.8:
        include_variant_key = True
```

#### 온보딩 정보 기반 중요도 계산

```python
def _calculate_variant_key_importance(spec_key, product_type, user_profile, onboarding_data):
    importance = 1.0
    
    # 용량 관련 칼럼
    if '용량' in spec_key and product_type == '세탁기':
        if laundry == 'daily' and household_size >= 3:
            importance = 1.2  # 높은 중요도
    
    # 에너지 효율 관련
    if '에너지' in spec_key:
        if priority == 'eco':
            importance = 1.3  # 매우 높은 중요도
    
    # 해상도 관련 (TV)
    if '해상도' in spec_key and product_type == 'TV':
        if media == 'gaming':
            importance = 1.3  # 게이머에게 중요
    
    return importance
```

---

### Step 3: 제품 종류별 칼럼 점수 산출

```python
def calculate_product_type_column_score(product_type, products, user_profile, onboarding_data):
    # 1. 점수 산출에 사용할 SPEC_KEY 목록
    scoring_keys = get_scoring_spec_keys(product_type, user_profile, onboarding_data)
    
    # 2. 각 제품별 칼럼 점수 계산
    product_scores = []
    
    for product in products:
        spec_json = json.loads(product.spec.spec_json)
        
        # COMMON 칼럼 점수 (70% 가중치)
        common_score = calculate_common_score(spec_json, common_keys)
        
        # VARIANT 칼럼 점수 (30% 가중치)
        variant_score = calculate_variant_score(spec_json, variant_keys)
        
        # 최종 칼럼 점수
        column_score = common_score * 0.7 + variant_score * 0.3
        product_scores.append(column_score)
    
    # 3. 제품 종류별 평균 칼럼 점수
    avg_score = sum(product_scores) / len(product_scores)
    return avg_score
```

---

### Step 4: 칼럼 점수에 따른 제품 종류 선정

```python
def _select_product_types_for_package(column_scores, user_profile, onboarding_data):
    # 1. 최소 점수 기준 이상인 제품 종류만
    min_score_threshold = 0.3
    qualified_types = [
        product_type
        for product_type, score in column_scores.items()
        if score >= min_score_threshold
    ]
    
    # 2. 칼럼 점수 순으로 정렬
    sorted_types = sorted(qualified_types, key=lambda t: column_scores[t], reverse=True)
    
    # 3. 시나리오별 필수 제품 종류 포함
    scenario_essential_types = get_product_types_for_scenario(user_profile, onboarding_data)
    
    selected_types = set(sorted_types) | set(scenario_essential_types)
    
    # 4. 최대 개수 제한 (7개)
    final_types = list(selected_types)[:7]
    
    return final_types
```

**선정 기준 예시**:

| 제품 종류 | 칼럼 점수 | 선정 여부 |
|----------|----------|----------|
| 냉장고   | 0.92     | ✅ 선정 |
| TV       | 0.88     | ✅ 선정 |
| 세탁기   | 0.85     | ✅ 선정 |
| 청소기   | 0.78     | ✅ 선정 |
| 식기세척기 | 0.75   | ✅ 선정 |
| 에어컨   | 0.65     | ✅ 선정 |
| 공기청정기 | 0.58   | ✅ 선정 |
| 제습기   | 0.25     | ❌ 제외 (최소 점수 미달) |

---

### Step 5: 제품 종류별 상위 3개 모델 추천

```python
def _recommend_top_products_by_type(products, product_type, ...):
    # 1. 각 제품 스코어링
    scored_products = []
    for product in products:
        score = calculate_product_score(product, user_profile)
        scored_products.append({'product': product, 'score': score})
    
    # 2. 점수 순으로 정렬 및 상위 3개 선택
    top_products = sorted(scored_products, key=lambda x: x['score'], reverse=True)[:3]
    
    # 3. 포맷팅
    recommendations = format_recommendations(top_products)
    
    return recommendations
```

---

## 📊 실제 예시

### 입력

```json
{
  "household_size": 4,
  "housing_type": "apartment",
  "pyung": 35,
  "priority": "tech",
  "budget_level": "medium",
  "budget_amount": 3000000,
  "categories": ["TV", "KITCHEN", "LIVING"],
  "onboarding_data": {
    "cooking": "high",
    "laundry": "daily",
    "media": "gaming"
  }
}
```

### 처리 과정

#### Step 1: SPEC 구조 분석 결과

```
COMMON 칼럼 (모든 제품 종류에 100% 공통):
- 가격
- 브랜드
- 카테고리
- 모델명

VARIANT 칼럼 (제품 종류별):
- 세탁기: ['용량(kg)', '세탁모드', '에너지등급', '세탁용량']
- 냉장고: ['총용량(L)', '냉장실용량', '냉동실용량', '에너지등급']
- TV: ['해상도', '주사율', '패널타입', '화면크기(인치)']
- 청소기: ['흡입력', '배터리용량', '무게']
```

#### Step 2: VARIANT 칼럼 포함/제외 결정

```
세탁기:
- '용량(kg)': 등장빈도 95%, 중요도 1.2 (세탁 daily + 4인 가족) → ✅ 포함
- '세탁모드': 등장빈도 80% → ✅ 포함
- '에너지등급': 등장빈도 70%, 중요도 0.8 (priority != eco) → ❌ 제외

TV:
- '해상도': 등장빈도 100%, 중요도 1.3 (media == gaming) → ✅ 포함
- '주사율': 등장빈도 85%, 중요도 1.3 (media == gaming) → ✅ 포함
- '패널타입': 등장빈도 90% → ✅ 포함
```

#### Step 3: 제품 종류별 칼럼 점수 산출

```
냉장고:
  COMMON 점수: 0.95 (4/4 칼럼 존재)
  VARIANT 점수: 0.88 (용량, 에너지등급 등)
  최종 칼럼 점수: 0.95 * 0.7 + 0.88 * 0.3 = 0.929

TV:
  COMMON 점수: 0.95
  VARIANT 점수: 0.85 (해상도, 주사율 등)
  최종 칼럼 점수: 0.95 * 0.7 + 0.85 * 0.3 = 0.920

세탁기:
  COMMON 점수: 0.95
  VARIANT 점수: 0.75 (용량 등)
  최종 칼럼 점수: 0.95 * 0.7 + 0.75 * 0.3 = 0.890

청소기:
  COMMON 점수: 0.95
  VARIANT 점수: 0.65
  최종 칼럼 점수: 0.95 * 0.7 + 0.65 * 0.3 = 0.860
```

#### Step 4: 제품 종류 선정

```
칼럼 점수 순 정렬:
1. 냉장고: 0.929
2. TV: 0.920
3. 세탁기: 0.890
4. 청소기: 0.860
5. 식기세척기: 0.780
6. 에어컨: 0.720
7. 공기청정기: 0.680

선정 결과 (최대 7개):
✅ 냉장고, TV, 세탁기, 청소기, 식기세척기, 에어컨, 공기청정기
```

#### Step 5: 각 제품 종류별 상위 3개 추천

```
냉장고:
  1. LG 디오스 냉장고 850L (점수: 0.92)
  2. LG 컨버터블 냉장고 750L (점수: 0.89)
  3. LG 일반 냉장고 650L (점수: 0.85)

TV:
  1. LG OLED TV 65형 (점수: 0.90)
  2. LG QNED TV 55형 (점수: 0.87)
  3. LG 나노셀 TV 50형 (점수: 0.82)

세탁기:
  1. LG 워시타워 24/20kg (점수: 0.88)
  2. LG 트롬 세탁기 20kg (점수: 0.85)
  3. LG 통돌이 세탁기 16kg (점수: 0.80)

... (각 종류별 3개씩)
```

### 최종 출력

```json
{
  "success": true,
  "count": 21,  // 7개 제품 종류 × 3개씩
  "product_types": [
    "냉장고", "TV", "세탁기", "청소기", 
    "식기세척기", "에어컨", "공기청정기"
  ],
  "column_scores": {
    "냉장고": 0.929,
    "TV": 0.920,
    "세탁기": 0.890,
    "청소기": 0.860,
    "식기세척기": 0.780,
    "에어컨": 0.720,
    "공기청정기": 0.680
  },
  "recommendations": [
    {
      "product_type": "냉장고",
      "name": "LG 디오스 냉장고 850L",
      "score": 0.92,
      "price": 2500000,
      ...
    },
    // ... 총 21개 (각 제품 종류별 3개씩)
  ]
}
```

---

## 🔄 COMMON vs VARIANT 로직

### COMMON 칼럼 (반드시 포함)

```
조건: 모든 제품 종류에서 100% 존재
처리: 항상 점수 산출에 포함
가중치: 70%

예시:
- 가격: 모든 제품에 있음 → COMMON
- 브랜드: 모든 제품에 있음 → COMMON
- 카테고리: 모든 제품에 있음 → COMMON
```

### VARIANT 칼럼 (조건부 포함)

```
조건 1: 등장 빈도 >= 50%
조건 2: 온보딩 정보 기반 중요도 >= 0.8
또는
조건 3: 등장 빈도 >= 80% (무조건 포함)

처리: 조건 충족 시만 포함
가중치: 30%

예시:
- 세탁기 '용량(kg)':
  * 등장 빈도: 95%
  * 중요도: 1.2 (세탁 daily + 4인 가족)
  * → ✅ 포함

- TV '주사율':
  * 등장 빈도: 85%
  * 중요도: 1.3 (media == gaming)
  * → ✅ 포함

- 세탁기 '에너지등급':
  * 등장 빈도: 70%
  * 중요도: 0.8 (priority != eco)
  * → ❌ 제외 (조건 미충족)
```

---

## 📝 API 엔드포인트

### `POST /api/recommend/column-based/`

**요청:**
```json
{
  "vibe": "modern",
  "household_size": 4,
  "housing_type": "apartment",
  "pyung": 35,
  "priority": "tech",
  "budget_level": "medium",
  "budget_amount": 3000000,
  "categories": ["TV", "KITCHEN", "LIVING"],
  "onboarding_data": {
    "cooking": "high",
    "laundry": "daily",
    "media": "gaming"
  }
}
```

**응답:**
```json
{
  "success": true,
  "count": 21,
  "product_types": ["냉장고", "TV", "세탁기", ...],
  "column_scores": {
    "냉장고": 0.929,
    "TV": 0.920,
    ...
  },
  "recommendations": [
    {
      "product_type": "냉장고",
      "name": "LG 디오스 냉장고",
      "score": 0.92,
      ...
    },
    // 각 제품 종류별 상위 3개씩
  ]
}
```

---

## ✅ 구현 완료

- [x] SPEC 칼럼 분류 로직 (COMMON/VARIANT)
- [x] VARIANT 칼럼 포함/제외 로직 (등장 빈도 + 온보딩 정보)
- [x] 제품 종류별 칼럼 점수 산출
- [x] 칼럼 점수에 따른 제품 종류 선정
- [x] 제품 종류별 상위 3개 모델 추천
- [x] API 엔드포인트 추가

---

## 🔜 추가 작업

- [ ] Oracle DB 실제 구조 확인 및 연동
- [ ] SPEC_TYPE/SPEC_KEY 실제 데이터 매핑
- [ ] 칼럼 점수 산출 정확도 향상
- [ ] 제품 종류 선정 기준 튜닝


