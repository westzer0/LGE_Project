# Taste별 독립적인 Scoring Logic

각 taste_id마다 완전히 독립적인 scoring logic을 관리하는 디렉토리입니다.

## 구조

```
api/scoring_logic/tastes/
├── taste_001.json  # taste_id 1번의 독립적인 로직
├── taste_002.json  # taste_id 2번의 독립적인 로직
├── taste_003.json  # taste_id 3번의 독립적인 로직
...
└── taste_120.json  # taste_id 120번의 독립적인 로직
```

## 파일 형식

각 `taste_{id}.json` 파일은 다음 형식을 따릅니다:

```json
{
  "logic_id": "taste_001",
  "logic_name": "Scoring_Logic_Taste_001",
  "taste_id": 1,
  "weights": {
    "TV": {
      "resolution": 0.30,
      "brightness": 0.15,
      "refresh_rate": 0.15,
      "panel_type": 0.10,
      "power_consumption": 0.10,
      "size": 0.10,
      "price_match": 0.10
    },
    "냉장고": {
      "capacity": 0.30,
      "energy_efficiency": 0.20,
      "features": 0.20,
      "size": 0.10,
      "price_match": 0.20
    },
    "에어컨": {
      "energy_efficiency": 0.35,
      "power_consumption": 0.25,
      "features": 0.20,
      "price_match": 0.20
    },
    "AIHome": {
      "features": 0.40,
      "connectivity": 0.30,
      "design": 0.20,
      "price_match": 0.10
    },
    "환기 시스템": {
      "energy_efficiency": 0.40,
      "power_consumption": 0.30,
      "features": 0.20,
      "price_match": 0.10
    }
    // 모든 MAIN_CATEGORY에 대해 정의 가능
  },
  "bonuses": [
    {
      "condition": "AI 또는 스마트 기능 포함",
      "bonus": 0.15,
      "reason": "기술 우선순위에 부합"
    }
  ],
  "penalties": [
    {
      "condition": "소형 제품 (300L 이하)",
      "penalty": -0.2,
      "reason": "가족 구성에 부적합한 용량"
    }
  ],
  "filters": {
    "must_have": [],
    "should_have": ["OBJET 또는 오브제 라인업"],
    "exclude": ["소형 제품 (300L 이하)"]
  }
}
```

## 주요 특징

1. **MAIN_CATEGORY 기반**: 모든 MAIN_CATEGORY를 직접 지원
   - TV, 냉장고, 세탁기, 에어컨, AIHome, 환기시스템 등
   
2. **독립적인 가중치**: 각 taste별로 완전히 다른 가중치 구조

3. **보너스/페널티**: taste별 특화된 보너스 및 페널티 규칙

4. **필터링**: taste별 제품 필터링 규칙

## Logic 우선순위

1. **Taste별 독립 파일** (`tastes/taste_{id}.json`) - 최우선
2. 기존 공유 로직 파일 (`taste_scoring_logics.json`)
3. 동적 생성 (온보딩 데이터 기반)
4. 기본 로직 (기본 가중치 사용)

## 사용 방법

각 taste별로 독립적인 logic 파일을 생성하면, 해당 taste_id에 자동으로 적용됩니다.

```python
from api.services.taste_scoring_logic_service import taste_scoring_logic_service

# taste_id 1번의 logic 조회
logic = taste_scoring_logic_service.get_logic_for_taste(1)

# taste_id 1번의 logic 저장
logic_data = {
    "logic_id": "taste_001",
    "logic_name": "Custom Logic for Taste 1",
    "taste_id": 1,
    "weights": { ... },
    "bonuses": [ ... ],
    "penalties": [ ... ]
}
taste_scoring_logic_service.save_taste_logic(1, logic_data)
```

