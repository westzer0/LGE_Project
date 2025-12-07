# Taste별 독립적인 Scoring Logic 백엔드 구조

## 개요

각 `taste_id` (1~120)마다 완전히 독립적인 scoring logic을 적용할 수 있는 백엔드 구조입니다.
기본 로직을 유지하면서 taste별로 override 가능한 확장 가능한 구조입니다.

## 아키텍처 구조

```
api/
├── services/
│   └── taste_scoring_logic_service.py    # Taste별 Logic 관리 서비스
├── utils/
│   ├── taste_scoring.py                  # Scoring Logic 적용 (기존 로직 유지)
│   ├── scoring.py                        # 기본 scoring 함수들
│   └── category_mapping.py               # MAIN_CATEGORY 매핑
└── scoring_logic/
    ├── taste_scoring_logics.json         # 기존 공유 로직 (하위 호환성)
    └── tastes/                           # Taste별 독립 파일
        ├── taste_001.json
        ├── taste_002.json
        ...
        └── taste_120.json
```

## 주요 컴포넌트
### 1. TasteScoringLogicService

**위치**: `api/services/taste_scoring_logic_service.py`

**역할**:
- Taste별 독립적인 scoring logic 관리
- Logic 조회, 생성, 저장
- 캐싱 지원
- 모든 MAIN_CATEGORY 지원

**주요 메서드**:
```python
# Logic 조회
get_logic_for_taste(taste_id, onboarding_data=None) -> Dict

# 기본 Logic 생성
create_base_logic_for_taste(taste_id, onboarding_data=None) -> Dict

# Logic 저장
save_taste_logic(taste_id, logic) -> bool
```

**Logic 우선순위**:
1. Taste별 독립 파일 (`tastes/taste_{id}.json`) - 최우선
2. 기존 공유 로직 파일 (`taste_scoring_logics.json`)
3. 동적 생성 (온보딩 데이터 기반)
4. 기본 로직 (기본 가중치)

### 2. Taste Scoring

**위치**: `api/utils/taste_scoring.py`

**역할**:
- Product scoring에 taste logic 적용
- MAIN_CATEGORY 기반 가중치 조회
- 보너스/페널티 적용

**주요 함수**:
```python
# Taste logic을 적용한 제품 점수 계산
calculate_product_score_with_taste_logic(
    product, profile, taste_id, onboarding_data
) -> float

# Taste ID에 해당하는 Logic 조회
get_logic_for_taste_id(taste_id, onboarding_data) -> Dict
```

## Logic 파일 구조

### Taste별 독립 파일

각 `tastes/taste_{id}.json` 파일은 다음 구조를 따릅니다:

```json
{
  "logic_id": "taste_001",
  "logic_name": "Scoring_Logic_Taste_001",
  "taste_id": 1,
  "weights": {
    "TV": { ... },
    "냉장고": { ... },
    "에어컨": { ... },
    "AIHome": { ... },
    "환기 시스템": { ... }
    // 모든 MAIN_CATEGORY 지원
  },
  "bonuses": [ ... ],
  "penalties": [ ... ],
  "filters": { ... }
}
```

### MAIN_CATEGORY 지원

모든 MAIN_CATEGORY를 직접 지원합니다:
- TV, 오디오, 사운드바, 프로젝터, 스탠바이미
- 냉장고, 김치냉장고, 식기세척기, 전자레인지, 오븐 등
- 세탁기, 건조기, 청소기, 공기청정기, 가습기 등
- 에어컨, 시스템 에어컨, 환기 시스템
- AIHome
- OBJET, SIGNATURE

## 사용 예시

### 1. 기본 사용 (기존 코드 호환)

```python
from api.utils.taste_scoring import calculate_product_score_with_taste_logic

# Taste ID를 사용한 점수 계산
score = calculate_product_score_with_taste_logic(
    product=product,
    profile=user_profile,
    taste_id=1,
    onboarding_data=onboarding_data  # 선택사항
)
```

### 2. Taste별 Logic 조회

```python
from api.services.taste_scoring_logic_service import taste_scoring_logic_service

# Logic 조회
logic = taste_scoring_logic_service.get_logic_for_taste(
    taste_id=1,
    onboarding_data=onboarding_data  # 선택사항
)

# Logic 저장 (새로운 logic 생성)
taste_scoring_logic_service.save_taste_logic(taste_id=1, logic=logic_data)
```

### 3. 기본 Logic 생성

```python
from api.services.taste_scoring_logic_service import taste_scoring_logic_service

# 모든 MAIN_CATEGORY를 지원하는 기본 logic 생성
base_logic = taste_scoring_logic_service.create_base_logic_for_taste(
    taste_id=1,
    onboarding_data=onboarding_data  # 선택사항
)
```

## 특징

### 1. 확장 가능한 구조
- Taste별 독립 파일로 관리
- 필요할 때만 생성 (기본 로직 사용 가능)
- 파일 기반이므로 버전 관리 용이

### 2. 하위 호환성
- 기존 `taste_scoring_logics.json` 지원
- 기존 코드 수정 없이 동작
- 점진적 마이그레이션 가능

### 3. 모든 MAIN_CATEGORY 지원
- TV, KITCHEN, LIVING 하드코딩 제거
- 모든 MAIN_CATEGORY 직접 지원
- 동적 카테고리 확장 가능

### 4. 캐싱
- Logic 캐싱으로 성능 최적화
- Cache 무효화 메서드 제공

## 점수 산출 프로세스

1. **Taste ID 조회**: 사용자의 `member.taste` 값 (1~120)
2. **Logic 조회**: TasteScoringLogicService에서 logic 가져오기
3. **MAIN_CATEGORY 결정**: `product.spec.spec_json`의 `MAIN_CATEGORY` 사용
4. **가중치 선택**: Logic의 weights에서 MAIN_CATEGORY에 해당하는 가중치
5. **속성 점수 계산**: 각 속성별 점수 계산 (resolution, brightness, capacity 등)
6. **가중 평균**: 속성 점수와 가중치를 곱하여 가중 평균 계산
7. **보너스/페널티 적용**: Logic의 bonuses/penalties 적용
8. **최종 점수**: 0.0 ~ 1.0 범위로 제한

## 확장 방법

### 1. 새로운 Taste Logic 생성

```bash
# 파일 생성
api/scoring_logic/tastes/taste_001.json
```

### 2. Logic 구조 커스터마이징

각 taste별로 완전히 다른 가중치 구조를 정의할 수 있습니다:

```json
{
  "weights": {
    "TV": {
      "resolution": 0.50,  // 이 taste는 해상도를 매우 중시
      "brightness": 0.30,
      "price_match": 0.20
    },
    "냉장고": {
      "capacity": 0.60,    // 이 taste는 용량을 매우 중시
      "energy_efficiency": 0.40
    }
  }
}
```

### 3. 보너스/페널티 추가

```json
{
  "bonuses": [
    {
      "condition": "AI 또는 스마트 기능 포함",
      "bonus": 0.2,
      "reason": "이 taste는 AI 기능을 선호"
    }
  ],
  "penalties": [
    {
      "condition": "고가 제품",
      "penalty": -0.1,
      "reason": "가성비 중시"
    }
  ]
}
```

## 주의사항

1. **가중치 합**: 각 카테고리의 가중치 합이 1.0이 되도록 권장
2. **MAIN_CATEGORY 명확성**: MAIN_CATEGORY 값을 정확히 사용 (대소문자 주의)
3. **캐시**: Logic 파일을 수정한 후에는 캐시를 무효화하거나 서버 재시작 필요

## 마이그레이션 가이드

기존 구조에서 새 구조로 마이그레이션:

1. 기존 로직 유지: `taste_scoring_logics.json`은 그대로 유지
2. 점진적 이동: 필요한 taste부터 독립 파일로 이동
3. 테스트: 각 taste별로 점수 계산 테스트
4. 완전 전환: 모든 taste를 독립 파일로 이동 후 공유 파일 제거 가능

## 참고

- `api/scoring_logic/tastes/README.md`: Taste 파일 구조 상세 설명
- `api/utils/category_mapping.py`: MAIN_CATEGORY 매핑 정보
- `api/utils/scoring.py`: 기본 scoring 함수들

