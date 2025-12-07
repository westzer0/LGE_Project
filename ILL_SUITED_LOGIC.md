# Ill-suited Category Detection Logic 문서

## 개요

이 문서는 `taste_config` 테이블에서 **ill-suited 카테고리**를 판별하는 로직을 설명합니다.

Ill-suited 카테고리는 **온보딩 세션 답변에 완전히 반대되는 제품 카테고리**를 의미하며, 이들은 점수 계산에서 제외되고 `ILL_SUITED_CATEGORIES` 컬럼에 별도로 저장됩니다.

## 목적

1. **정확한 추천**: 온보딩 답변과 완전히 부적합한 카테고리를 사전에 필터링
2. **투명한 점수 관리**: 0점 카테고리를 별도 컬럼으로 관리하여 점수 계산 로직 명확화
3. **카테고리별 점수 추적**: 각 카테고리별 점수를 별도 컬럼으로 저장하여 추적 가능

## 데이터 구조

### Oracle TASTE_CONFIG 테이블

| 컬럼명 | 타입 | 설명 |
|--------|------|------|
| `ILL_SUITED_CATEGORIES` | CLOB (JSON) | Ill-suited 카테고리 리스트 (JSON 배열) |
| `{CATEGORY_NAME}_SCORE` | NUMBER(5,2) | 카테고리별 점수 (0~100점) |
| `CATEGORY_SCORES` | CLOB (JSON) | 모든 카테고리별 점수 매핑 (JSON 객체) |

### 예시

```json
{
  "ILL_SUITED_CATEGORIES": ["미니냉장고", "건조기", "식기세척기"],
  "CATEGORY_SCORES": {
    "TV": 85.0,
    "냉장고": 70.0,
    "에어컨": 65.0,
    "미니냉장고": 0.0,
    "건조기": 0.0,
    "식기세척기": 0.0
  },
  "TV_SCORE": 85.0,
  "냉장고_SCORE": 70.0,
  "에어컨_SCORE": 65.0
}
```

## Ill-suited 판별 로직

### 1. 반려동물 관련 (Pet-related)

**로직**: 반려동물을 키우지 않는다면, 반려동물 전용 제품은 ill-suited

| 조건 | Ill-suited 카테고리 |
|------|---------------------|
| `has_pet = False` | 반려동물 관련 키워드 포함 카테고리 |

**판별 기준**:
- 카테고리명에 "반려동물", "펫", "pet" 포함

**예시**:
- `onboarding_data.has_pet = False` → "반려동물전용" 카테고리는 ill-suited

---

### 2. 가구 수 관련 (Household Size)

**로직**: 가구 수에 비해 과도하게 크거나 작은 제품은 ill-suited

| 가구 수 | Ill-suited 카테고리 |
|---------|---------------------|
| 1인 가구 | 대형 가전 (김치냉장고, 워시타워, 대형냉장고, 대형세탁기) |
| 5인 이상 가구 | 미니 가전 (미니냉장고, 미니세탁기) |

**판별 기준**:
- **1인 가구**: "대형", "김치냉장고", "워시타워" 포함 카테고리
- **5인 이상 가구**: "미니" 포함 카테고리

**예시**:
- `household_size = 1` → "김치냉장고", "워시타워"는 ill-suited
- `household_size = 6` → "미니냉장고", "미니세탁기"는 ill-suited

---

### 3. 주거 형태 및 평수 관련 (Housing Type & Pyung)

**로직**: 작은 평수에 설치하기 어려운 대형 가전은 ill-suited

| 조건 | Ill-suited 카테고리 |
|------|---------------------|
| `housing_type in ['studio', 'officetel']` AND `pyung <= 20` | 대형 가전 (김치냉장고, 워시타워, 건조기, 식기세척기, 대형TV, 프로젝터) |

**판별 기준**:
- 원룸/오피스텔 + 20평 이하: "대형", "김치냉장고", "워시타워", "건조기", "식기세척기", "프로젝터" 포함 카테고리

**예시**:
- `housing_type = 'studio'` + `pyung = 18` → "김치냉장고", "워시타워", "건조기"는 ill-suited

---

### 4. 주요 공간 관련 (Main Space)

**로직**: 주요 공간과 무관한 카테고리는 ill-suited

| 주요 공간 | Ill-suited 카테고리 |
|-----------|---------------------|
| 주방이 주요 공간이 아님 | 주방 가전 (식기세척기, 전자레인지, 오븐, 김치냉장고) |
| 세탁실/베란다가 주요 공간이 아님 | 세탁 가전 (건조기, 워시타워, 의류관리기) |

**판별 기준**:
- `main_space`에 "kitchen", "주방" 없음 → 주방 가전
- `main_space`에 "laundry", "세탁", "베란다" 없음 → 세탁 가전

**예시**:
- `main_space = 'living'` → "식기세척기", "전자레인지"는 ill-suited
- `main_space = 'kitchen'` → "건조기", "워시타워"는 ill-suited

---

### 5. 생활 패턴 관련 (Lifestyle)

**로직**: 생활 패턴과 맞지 않는 카테고리는 ill-suited

| 생활 패턴 | Ill-suited 카테고리 |
|-----------|---------------------|
| 요리 빈도: `rarely`, `never` | 주방 가전 (식기세척기, 오븐, 전자레인지) |
| 세탁 빈도: `rarely`, `never` | 세탁 가전 (건조기, 워시타워, 의류관리기) |
| 미디어 사용: `none`, `minimal` | 미디어 가전 (TV, 프로젝터, 스탠바이미, 오디오, 사운드바) |

**판별 기준**:
- `cooking in ['rarely', 'never', '전혀', '안함']` → 주방 가전
- `laundry in ['rarely', 'never', '거의안함', '전혀']` → 세탁 가전
- `media in ['none', 'minimal', '없음', '안봄']` → 미디어 가전

**예시**:
- `cooking = 'rarely'` → "식기세척기", "오븐"은 ill-suited
- `laundry = 'never'` → "건조기", "워시타워"는 ill-suited
- `media = 'none'` → "TV", "프로젝터"는 ill-suited

---

### 6. 인테리어 무드 관련 (Vibe)

**로직**: 인테리어 무드와 맞지 않는 제품 스타일은 ill-suited

| 무드 | Ill-suited 카테고리 |
|------|---------------------|
| `luxury`, `럭셔리`, `고급` | 저가형 제품 (미니냉장고, 미니세탁기) |

**판별 기준**:
- `vibe in ['luxury', '럭셔리', '고급']` → "미니" 포함 카테고리

**예시**:
- `vibe = 'luxury'` → "미니냉장고", "미니세탁기"는 ill-suited

---

## 점수 계산 방식

### Ill-suited 카테고리
- **점수: 0점 고정**
- `ILL_SUITED_CATEGORIES` 컬럼에 저장
- 점수 계산에서 제외

### 일반 카테고리
- **점수 범위: 0~100점**
- `TasteCategorySelector._calculate_category_score()` 함수로 계산
- 계산 요소:
  - `main_space` 기반 점수 (최대 30점)
  - `household_size` 기반 점수 (최대 20점)
  - `has_pet` 기반 점수 (최대 15점)
  - `budget_level` 기반 점수 (최대 15점)
  - `priority` 기반 점수 (최대 10점)
  - `cooking` 기반 점수 (최대 5점)
  - `laundry` 기반 점수 (최대 5점)
  - `media` 기반 점수 (최대 5점)
  - `pyung` 기반 점수 (최대 5점)

### 점수 저장 위치

1. **JSON 컬럼**: `CATEGORY_SCORES` (모든 카테고리 점수 포함)
2. **개별 컬럼**: `{CATEGORY_NAME}_SCORE` (주요 카테고리만)
   - 예: `TV_SCORE`, `냉장고_SCORE`, `에어컨_SCORE` 등

---

## 사용 예시

### Python 코드

```python
from api.utils.ill_suited_category_detector import IllSuitedCategoryDetector

# 온보딩 데이터
onboarding_data = {
    'has_pet': False,
    'household_size': 1,
    'housing_type': 'studio',
    'pyung': 18,
    'main_space': 'living',
    'cooking': 'rarely',
    'laundry': 'weekly',
    'media': 'none',
    'vibe': 'luxury'
}

# 모든 사용 가능한 카테고리
all_categories = ['TV', '냉장고', '에어컨', '미니냉장고', '김치냉장고', 
                  '식기세척기', '건조기', '프로젝터']

# Ill-suited 카테고리 판별
ill_suited = IllSuitedCategoryDetector.detect_ill_suited_categories(
    onboarding_data, all_categories
)

# 결과
# ill_suited = ['미니냉장고', '김치냉장고', '식기세척기', '프로젝터', 'TV']
```

### 이유 확인

```python
# 특정 카테고리가 ill-suited인 이유 확인
reason = IllSuitedCategoryDetector.get_ill_suited_reason(
    '식기세척기', onboarding_data
)
# reason = "요리를 거의 하지 않으므로 불필요; 주방이 주요 공간이 아니므로 불필요"
```

---

## 데이터 생성 프로세스

### 1. `populate_taste_config` 명령어 실행

```bash
python manage.py populate_taste_config --taste-range 1-120
```

### 2. 프로세스 흐름

1. **Ill-suited 카테고리 식별**
   - `IllSuitedCategoryDetector.detect_ill_suited_categories()` 호출
   - 온보딩 데이터 기반으로 ill-suited 카테고리 리스트 생성

2. **유효 카테고리 점수 계산**
   - Ill-suited가 아닌 카테고리만 점수 계산
   - `TasteCategorySelector._calculate_category_score()` 사용

3. **점수 정렬 및 선택**
   - 점수 기준으로 정렬
   - 점수 분포 분석하여 추천 카테고리 선택

4. **데이터 저장**
   - `ILL_SUITED_CATEGORIES`: Ill-suited 카테고리 리스트
   - `CATEGORY_SCORES`: 모든 카테고리 점수 (JSON)
   - `{CATEGORY_NAME}_SCORE`: 주요 카테고리별 점수 (개별 컬럼)

---

## 주요 카테고리별 Score 컬럼

다음 카테고리들은 Oracle 테이블에 별도 컬럼으로 저장됩니다:

### TV 관련
- `TV_SCORE`
- `프로젝터_SCORE`
- `스탠바이미_SCORE`
- `오디오_SCORE`
- `사운드바_SCORE`

### 냉장고 관련
- `냉장고_SCORE`
- `김치냉장고_SCORE`

### 세탁 관련
- `세탁기_SCORE`
- `건조기_SCORE`
- `워시타워_SCORE`

### 주방 가전
- `식기세척기_SCORE`
- `전자레인지_SCORE`
- `오븐_SCORE`

### 공기 관련
- `에어컨_SCORE`
- `공기청정기_SCORE`
- `가습기_SCORE`
- `제습기_SCORE`

### 청소 관련
- `청소기_SCORE`
- `로봇청소기_SCORE`

### 기타
- `정수기_SCORE`
- `와인셀러_SCORE`
- `AIHOME_SCORE`
- `OBJET_SCORE`
- `SIGNATURE_SCORE`

---

## 주의사항

1. **동적 카테고리**: 새로운 카테고리가 추가되면 SQL 스크립트에 컬럼을 추가해야 할 수 있습니다.
2. **컬럼명 길이**: Oracle은 컬럼명이 30자로 제한되므로 주의가 필요합니다.
3. **JSON vs 개별 컬럼**: 
   - JSON 컬럼 (`CATEGORY_SCORES`): 모든 카테고리 점수 포함
   - 개별 컬럼 (`{CATEGORY}_SCORE`): 주요 카테고리만 (성능 최적화)

---

## 업데이트 내역

- 2025-01-XX: 초기 버전 작성
  - Ill-suited 카테고리 판별 로직 정의
  - Category별 점수 컬럼 구조 추가
  - 문서화 완료

---

## 관련 파일

- `api/utils/ill_suited_category_detector.py`: Ill-suited 판별 로직
- `api/utils/taste_category_selector.py`: 카테고리 점수 계산
- `api/management/commands/populate_taste_config.py`: 데이터 생성 명령어
- `api/db/add_taste_config_score_columns.sql`: Oracle 테이블 스키마 업데이트



