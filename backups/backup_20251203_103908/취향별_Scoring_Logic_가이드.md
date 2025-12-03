# 취향별 독립적인 Scoring Logic 가이드

## 개요

768개의 취향 조합을 약 400개 정도의 독립적인 Scoring Logic 그룹으로 묶어, 각 취향에 맞게 제품 추천 논리가 독립적으로 적용되도록 구현했습니다.

## 시스템 구조

### 1. 취향 조합 분석 및 클러스터링

```
768개 취향 조합
    ↓ (유사도 분석)
약 400개 그룹
    ↓ (대표 취향 추출)
독립적인 Scoring Logic 생성
```

### 2. Scoring Logic 구성 요소

각 Scoring Logic은 다음 요소로 구성됩니다:

1. **weights**: 카테고리별 속성 가중치
   - TV: 해상도, 밝기, 주사율, 패널 타입, 전력소비, 크기, 가격 적합도
   - KITCHEN: 용량, 에너지 효율, 기능, 크기, 가격 적합도, 디자인
   - LIVING: 오디오 품질, 연결성, 전력소비, 크기, 가격 적합도, 기능

2. **filters**: 필터링 규칙
   - must_have: 필수 조건
   - should_have: 권장 조건
   - exclude: 제외 조건

3. **bonuses**: 보너스 점수 규칙
   - 조건에 맞는 제품에 추가 점수 부여

4. **penalties**: 페널티 점수 규칙
   - 조건에 맞지 않는 제품에 감점 적용

5. **explanation**: Logic 설명
   - 해당 Logic이 어떤 취향을 대표하는지 설명

6. **rationale**: 도출 근거
   - 각 취향 요소(인테리어, 메이트, 우선순위, 예산)가 Logic에 미치는 영향 설명

## 사용 방법

### 1. Scoring Logic 생성

```bash
# 기본 400개 그룹으로 생성
python manage.py generate_taste_scoring_logic

# 그룹 수 지정 (예: 200개)
python manage.py generate_taste_scoring_logic --target-groups 200
```

생성된 파일:
- `api/scoring_logic/taste_scoring_logics.json`: Logic 데이터
- `api/scoring_logic/scoring_logic_explanation.md`: 설명 문서

### 2. 추천 엔진에서 사용

```python
from api.services.recommendation_engine import RecommendationEngine

engine = RecommendationEngine()

# taste_id를 포함한 추천 요청
user_profile = {
    'vibe': 'modern',
    'household_size': 2,
    'priority': 'design',
    'budget_level': 'medium',
    'categories': ['TV', 'KITCHEN'],
}

# taste_id는 온보딩 설문에서 결정된 취향 ID
recommendations = engine.get_recommendations(
    user_profile=user_profile,
    limit=5,
    taste_id=123  # 취향 ID
)
```

### 3. 직접 Scoring Logic 사용

```python
from api.utils.taste_scoring import calculate_product_score_with_taste_logic
from api.models import Product
from api.rule_engine import UserProfile

product = Product.objects.get(id=1)
profile = UserProfile(...)

# taste_id에 맞는 Logic으로 점수 계산
score = calculate_product_score_with_taste_logic(
    product=product,
    profile=profile,
    taste_id=123
)
```

## Logic 도출 근거

각 Scoring Logic은 다음 기준으로 도출됩니다:

### 1. 인테리어 스타일 (Vibe)

- **모던 & 미니멀**: OBJET 라인업에 가중치 부여
- **코지 & 네이처**: OBJET 라인업에 가중치 부여
- **럭셔리 & 아티스틱**: SIGNATURE 라인업에 가중치 부여
- **유니크 & 팝**: OBJET 라인업에 가중치 부여

### 2. 메이트 구성 (Mate)

- **1인 가구**: 소형 제품에 보너스, 대용량 제품에 페널티
- **2인/신혼**: 표준형 제품에 가중치 부여
- **3~4인 가족**: 대용량 제품에 보너스, 소형 제품에 페널티

### 3. 우선순위 (Priority)

- **디자인**: 디자인 관련 속성(패널 타입, 디자인 라인업)에 높은 가중치
- **AI/스마트**: 기술 관련 속성(해상도, 주사율, AI 기능)에 높은 가중치
- **에너지 효율**: 에너지 관련 속성(전력소비, 에너지 등급)에 높은 가중치
- **가성비**: 가격 적합도에 높은 가중치

### 4. 예산 범위 (Budget)

- **실속형**: 가격 필터링과 가격 적합도에 높은 가중치
- **표준형**: 모든 속성에 균등한 가중치
- **고급형**: 기능성과 디자인에 높은 가중치
- **하이엔드**: 프리미엄 라인업과 최고 사양에 높은 가중치

## Logic 예시

### Scoring_Logic_001

**대표 취향**:
- 인테리어: 유니크 & 팝
- 메이트: 3~4인 가족
- 우선순위: AI/스마트 기능
- 예산: 고급형

**가중치 (TV 카테고리)**:
- resolution: 0.275 (기술 우선순위 반영)
- refresh_rate: 0.154 (기술 우선순위 반영)
- features: 0.132 (AI 기능 강조)
- price_match: 0.110

**보너스**:
- AI 또는 스마트 기능 포함: +0.12
- 대용량 제품 (800L 이상): +0.10

**페널티**:
- 소형 제품 (300L 이하): -0.20

**도출 근거**:
- vibe_impact: 유니크 & 팝 스타일은 개성 있는 디자인을 선호하므로, OBJET 라인업에 가중치를 부여합니다.
- mate_impact: 가족 구성은 큰 용량의 제품이 적합하므로, 대용량 제품에 보너스를 부여하고 소형 제품에 페널티를 적용합니다.
- priority_impact: AI/스마트 기능 우선순위는 첨단 기술을 중시하므로, 기술 관련 속성에 높은 가중치를 부여합니다.
- budget_impact: 고급형 예산은 품질을 중시하므로, 기능성과 디자인에 높은 가중치를 부여합니다.

## 파일 구조

```
api/
├── scoring_logic/
│   ├── taste_scoring_logics.json      # Logic 데이터
│   └── scoring_logic_explanation.md   # 설명 문서
├── utils/
│   ├── scoring.py                     # 기본 scoring 함수
│   └── taste_scoring.py               # 취향별 scoring 함수
└── services/
    └── recommendation_engine.py       # 추천 엔진 (taste_id 지원)
```

## 주의사항

1. **taste_id 매핑**: 온보딩 설문에서 결정된 취향 ID가 `taste_recommendations_768.csv`의 `taste_id`와 일치해야 합니다.

2. **Logic 캐싱**: Scoring Logic은 메모리에 캐싱되므로, Logic 파일을 수정한 후에는 서버를 재시작해야 합니다.

3. **기본 Scoring**: taste_id가 없거나 해당 Logic이 없는 경우, 기본 scoring 함수가 사용됩니다.

## 향후 개선 사항

1. **동적 Logic 조정**: 사용자 피드백을 기반으로 Logic 가중치 조정
2. **A/B 테스트**: 여러 Logic을 비교하여 최적의 Logic 선택
3. **실시간 학습**: 추천 결과를 기반으로 Logic 개선

