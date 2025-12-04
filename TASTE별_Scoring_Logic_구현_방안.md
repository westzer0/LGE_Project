# TASTE별 제품 점수 평가 Logic 구현 방안

## 문제점

현재 온보딩 데이터를 기반으로 동적으로 taste를 계산했지만, 각 taste별로 제품 점수 평가 로직이 완전히 달라져야 합니다.

## 해결 방안

### 1. 동적 Scoring Logic 생성

온보딩 데이터의 속성을 기반으로 **실시간으로** scoring logic을 생성합니다.

**구현 파일**: `api/utils/dynamic_taste_scoring.py`

### 2. 주요 조정 요소

#### 2.1 Vibe 기반 조정
- **Modern**: 디자인과 기술 중시 (design +30%, features +20%, price -20%)
- **Classic**: 전통적이고 실용적 (price +20%, energy +10%, design -10%)
- **Cozy**: 편안함과 실용성 (price +30%, power +20%, design -10%)
- **Luxury**: 프리미엄과 고급 기능 (design +50%, features +30%, price -40%)

#### 2.2 Priority 기반 조정
- **Design**: design +50%, panel_type +20%
- **Tech/AI**: features +50%, resolution +30%, refresh_rate +30%
- **Value**: price +50%, energy +20%, design -20%
- **Eco**: energy +50%, power +50%, price +10%

#### 2.3 Budget 기반 조정
- **Low**: price +50%, design -30%, features -20%
- **High**: design +30%, features +30%, price -30%

#### 2.4 Household Size 기반 조정
- **4인 이상**: capacity +50%, features +20%
- **1인**: capacity -30%, size +30%

#### 2.5 평수 기반 조정
- **20평 이하**: size +30%, capacity -20%
- **40평 이상**: size +30%, capacity +30%

#### 2.6 생활 패턴 기반 조정
- **요리 매일**: features +30%, capacity +20%
- **미디어 높음**: resolution +40%, brightness +30%, refresh_rate +30%

### 3. 보너스/페널티 시스템

#### 3.1 보너스
- 디자인 우선순위 → OBJET/SIGNATURE +15%
- 기술 우선순위 → AI/스마트 기능 +15%
- 대가족 → 대용량 제품 +12%
- 고급 예산 → 프리미엄 기능 +10%

#### 3.2 페널티
- 대가족 → 소형 제품 -20%
- 소형 주택 → 대형 제품 -15%
- 낮은 예산 → 고가 제품 -15%

### 4. 사용 방법

#### 4.1 추천 엔진에서 사용
```python
from api.utils.taste_scoring import calculate_product_score_with_taste_logic

# 온보딩 데이터와 함께 taste_id 전달
score = calculate_product_score_with_taste_logic(
    product=product,
    profile=user_profile,
    taste_id=taste_id,
    onboarding_data=onboarding_data  # 동적 logic 생성에 사용
)
```

#### 4.2 동적 Logic 직접 생성
```python
from api.utils.dynamic_taste_scoring import DynamicTasteScoring

logic = DynamicTasteScoring.generate_scoring_logic({
    'vibe': 'modern',
    'priority': ['design', 'tech'],
    'budget_level': 'high',
    'household_size': 4,
    'pyung': 30,
    'has_pet': False,
    'cooking': 'daily',
    'laundry': 'weekly',
    'media': 'high',
})
```

### 5. 장점

1. **완전 동적**: 온보딩 데이터만으로 자동 생성
2. **유연성**: 새로운 속성 추가 시 쉽게 확장 가능
3. **정확성**: 사용자의 실제 선호도를 반영
4. **유지보수**: JSON 파일 수동 관리 불필요

### 6. 기존 시스템과의 통합

- 기존 `taste_scoring_logics.json` 파일은 유지 (수동 정의된 logic)
- `onboarding_data`가 제공되면 동적 logic 우선 사용
- `onboarding_data`가 없으면 기존 JSON 파일 기반 logic 사용

### 7. 예시

#### 예시 1: 1인 가구, 모던, 디자인 우선순위
```python
onboarding_data = {
    'vibe': 'modern',
    'priority': ['design'],
    'budget_level': 'medium',
    'household_size': 1,
    'pyung': 20,
}

# 결과:
# - design 가중치: +50% (priority) + 30% (vibe) = 매우 높음
# - size 가중치: +30% (1인 가구)
# - capacity 가중치: -30% (1인 가구)
# - OBJET/SIGNATURE 보너스: +15%
```

#### 예시 2: 4인 가족, 코지, 가성비 우선순위
```python
onboarding_data = {
    'vibe': 'cozy',
    'priority': ['value'],
    'budget_level': 'low',
    'household_size': 4,
    'pyung': 35,
}

# 결과:
# - price 가중치: +50% (priority) + 30% (vibe) + 50% (budget) = 매우 높음
# - capacity 가중치: +50% (4인 가족)
# - 대용량 보너스: +12%
# - 소형 제품 페널티: -20%
```

## 구현 완료

- ✅ `api/utils/dynamic_taste_scoring.py`: 동적 scoring logic 생성 모듈
- ✅ `api/utils/taste_scoring.py`: onboarding_data 파라미터 추가
- ✅ 온보딩 데이터 기반 실시간 가중치 계산
- ✅ 보너스/페널티 자동 생성

## 다음 단계

1. 추천 엔진에서 `onboarding_data` 전달하도록 수정
2. 테스트 및 가중치 조정
3. 실제 사용자 데이터로 검증

