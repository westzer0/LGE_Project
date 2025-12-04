# TASTE 분류 및 추천 로직 정리

## 1. Taste 분류 로직 (`api/utils/taste_classifier.py`)

### 개요
- 온보딩 데이터를 기반으로 사용자를 **120개의 taste**로 분류
- 약 10,000개의 온보딩 조합을 120개 taste로 그룹화 (평균 83개 조합/taste)

### 분류 방법
```python
# 주요 속성 조합으로 taste_id 계산
taste_key_parts = [
    vibe,              # 4가지 (modern, cozy, pop, luxury)
    household_range,   # 4가지 범위 (1인, 2인, 3-4인, 5인이상)
    housing_type,      # 4가지 (apartment, detached, villa, officetel, studio)
    pyung_range,       # 7가지 범위 (10이하, 11-15, 16-20, 21-30, 31-40, 41-50, 51이상)
    budget_level,      # 3가지 (low, medium, high)
    priority_str,      # 우선순위 조합 (design, tech, eco, value 등)
    main_space_str,    # 주요 공간 조합
    has_pet,           # 반려동물 여부
    cooking,           # 요리 빈도
    laundry,           # 세탁 빈도
    media,             # 미디어 사용 패턴
]

# MD5 해시로 taste_id 생성 (1 ~ 120)
taste_hash = int(hashlib.md5(taste_key.encode('utf-8')).hexdigest(), 16)
taste_id = (taste_hash % 120) + 1
```

### 주요 메서드
- `calculate_taste_from_onboarding(onboarding_data)`: 온보딩 데이터로부터 taste_id 계산
- `calculate_taste_from_session(session_data)`: DB 세션 데이터로부터 taste_id 계산

---

## 2. Taste별 카테고리 선택 로직 (`api/utils/taste_category_selector.py`)

### 개요
- 각 taste에 따라 **MAIN CATEGORY를 N개 선택**
- 필수 카테고리: TV, KITCHEN, LIVING (항상 포함)
- 추가 카테고리: AIR, AI, OBJET, SIGNATURE (온보딩 데이터 기반 선택)

### 카테고리 개수 결정
```python
# 기본: 3개 (필수 카테고리)
num = 3

# 대가족이면 +1
if household_size >= 4:
    num += 1

# 높은 예산이면 +1
if budget_level in ['high', 'premium', 'luxury']:
    num += 1

# 큰 평수면 +1
if pyung >= 40:
    num += 1

# 최대 7개로 제한
return min(num, 7)
```

### 추가 카테고리 우선순위
1. **미디어 사용이 높으면**: AIR 우선
2. **디자인 우선순위면**: OBJET, SIGNATURE 우선
3. **기술 우선순위면**: AI 우선

---

## 3. Taste별 동적 Scoring 로직 (`api/utils/dynamic_taste_scoring.py`)

### 개요
- 온보딩 데이터를 기반으로 **동적으로 scoring logic 생성**
- 각 taste별로 다른 가중치, 보너스, 페널티 적용

### 기본 가중치 템플릿
```python
BASE_WEIGHTS = {
    "TV": {
        "resolution": 0.15,
        "brightness": 0.10,
        "refresh_rate": 0.10,
        "panel_type": 0.10,
        "power_consumption": 0.10,
        "size": 0.10,
        "price_match": 0.15,
        "features": 0.10,
        "design": 0.10,
    },
    "KITCHEN": {
        "capacity": 0.20,
        "energy_efficiency": 0.15,
        "features": 0.15,
        "size": 0.10,
        "price_match": 0.15,
        "design": 0.15,
        ...
    },
    "LIVING": {
        "audio_quality": 0.20,
        "connectivity": 0.15,
        "power_consumption": 0.10,
        ...
    }
}
```

### 가중치 조정 방법

#### 1. Vibe 기반 조정
- **modern**: 디자인 가중치 증가
- **cozy**: 기능성 가중치 증가
- **luxury**: 프리미엄 기능 가중치 증가

#### 2. Priority 기반 조정
- **design**: 디자인 가중치 +0.1
- **tech**: 기술/기능 가중치 +0.1
- **eco**: 에너지 효율 가중치 +0.1
- **value**: 가격 매칭 가중치 +0.1

#### 3. Budget 기반 조정
- **low**: 가격 매칭 가중치 +0.15
- **high**: 기능/디자인 가중치 +0.1

#### 4. Household Size 기반 조정
- **대가족**: 용량 가중치 증가
- **1인 가구**: 크기/효율 가중치 증가

#### 5. 생활 패턴 기반 조정
- **요리 빈도 높음**: 주방가전 기능 가중치 증가
- **세탁 빈도 높음**: 세탁기 용량 가중치 증가
- **미디어 사용 높음**: TV/오디오 기능 가중치 증가

### 보너스/페널티 적용
```python
# OBJET 라인 제품
if "OBJET" in product_name:
    if vibe == "modern" or "design" in priority:
        bonus += 0.1  # 디자인 선호 시 보너스
    else:
        penalty += 0.05  # 디자인 비선호 시 페널티

# 대용량 제품
if capacity > threshold:
    if household_size >= 4:
        bonus += 0.1  # 대가족에게 보너스
    elif household_size == 1:
        penalty += 0.1  # 1인 가구에게 페널티

# 펫 기능
if "펫" in product_name or "PET" in product_name:
    if has_pet:
        bonus += 0.1  # 반려동물 있으면 보너스
    else:
        penalty += 0.1  # 반려동물 없으면 페널티
```

---

## 4. Taste 기반 추천 엔진 (`api/services/taste_based_recommendation_engine.py`)

### 추천 프로세스
1. **Taste별 MAIN CATEGORY 선택**
   - `get_categories_for_taste()` 호출
   - 필수 카테고리 + 추가 카테고리 선택

2. **각 카테고리별 제품 필터링**
   - 가격 필터 (0원 제외, null 제외, 예산 범위)
   - 활성화된 제품만

3. **각 카테고리별 제품 스코어링**
   - `calculate_product_score_with_taste_logic()` 호출
   - 동적 scoring logic 적용

4. **각 카테고리에서 상위 3개씩 선택**
   - 총 3N개 제품 반환 (N = 선택된 카테고리 개수)

---

## 5. 전체 흐름도

```
온보딩 데이터 입력
    ↓
Taste 분류 (taste_classifier)
    ↓
taste_id 계산 (1 ~ 120)
    ↓
Taste별 카테고리 선택 (taste_category_selector)
    ↓
MAIN CATEGORY N개 선택 (TV, KITCHEN, LIVING, AIR, ...)
    ↓
각 카테고리별 제품 필터링
    ↓
동적 Scoring Logic 생성 (dynamic_taste_scoring)
    ↓
각 카테고리별 제품 스코어링
    ↓
각 카테고리에서 상위 3개씩 선택
    ↓
최종 추천 결과 (3N개 제품)
```

---

## 6. 주요 파일 위치

- **Taste 분류**: `api/utils/taste_classifier.py`
- **카테고리 선택**: `api/utils/taste_category_selector.py`
- **동적 Scoring**: `api/utils/dynamic_taste_scoring.py`
- **Scoring 적용**: `api/utils/taste_scoring.py`
- **추천 엔진**: `api/services/taste_based_recommendation_engine.py`
- **Taste 계산 서비스**: `api/services/taste_calculation_service.py`

---

## 7. 데이터베이스 연동

### MEMBER 테이블
- `TASTE` 컬럼: taste_id 저장 (1 ~ 120)

### ONBOARDING_SESSION 테이블
- 온보딩 데이터 저장
- `taste_calculation_service`를 통해 taste_id 계산 및 MEMBER 테이블에 저장

