# taste_recommendations_768.csv 파일 설명

## 📋 파일 개요

이 파일은 **768개의 서로 다른 취향 조합**을 담고 있는 데이터 파일입니다.

각 행은 하나의 **취향 조합(taste_id)**을 나타내며, 이 조합에 따라 제품 추천 로직이 달라집니다.

## 📊 파일 구조

### 컬럼 설명

| 컬럼명 | 설명 | 예시 |
|--------|------|------|
| `taste_id` | 취향 조합의 고유 ID (1~768) | `1`, `2`, `3`, ... `768` |
| `인테리어_스타일` | 선호하는 인테리어 스타일 | `모던 & 미니멀`, `따뜻한 코지`, `럭셔리 & 프리미엄` 등 |
| `메이트_구성` | 가구 구성 | `나 혼자 산다 (1인 가구)`, `신혼부부 (2인 가구)`, `함께 사는 3~4인 가족` 등 |
| `우선순위` | 구매 시 우선 고려사항 | `인테리어를 완성하는 디자인`, `삶을 편하게 해주는 AI/스마트 기능`, `에너지 효율` 등 |
| `예산_범위` | 예산 범위 | `500만원 미만 (실속형)`, `500~1,500만원 (표준형)`, `1,500~3,000만원 (고급형)` 등 |
| `선호_라인업` | 선호하는 제품 라인업 | `OBJET`, `SIGNATURE`, `기본형` 등 |
| `리뷰_기반_추천문구` | 실제 구매 리뷰를 분석한 추천 문구 | 긴 문구 (여러 줄) |
| `AI_기반_추천문구` | AI가 생성한 추천 문구 | 긴 문구 (여러 줄) |

### 데이터 예시

```csv
taste_id,인테리어_스타일,메이트_구성,우선순위,예산_범위,선호_라인업,리뷰_기반_추천문구,AI_기반_추천문구
1,모던 & 미니멀 (Modern & Minimal),나 혼자 산다 (1인 가구),인테리어를 완성하는 디자인,500만원 미만 (실속형),500만원 미만 (실속형),"혼자만의 모던 & 미니멀 무드...","모던 & 미니멀 감성으로 채우는 혼자만의 공간..."
2,따뜻한 코지 (Cozy & Warm),신혼부부 (2인 가구),삶을 편하게 해주는 AI/스마트 기능,500~1,500만원 (표준형),OBJET,"신혼부부를 위한 따뜻한 코지 무드...","따뜻한 코지 감성으로 채우는 신혼부부의 공간..."
```

## 🎯 이 파일의 용도

### 1. **취향별 추천 로직 적용**

768개의 취향 조합을 **50개의 Scoring Logic**으로 그룹화하여 사용합니다.

```
768개 취향 조합 (taste_recommendations_768.csv)
    ↓
50개 Scoring Logic (taste_scoring_logics.json)
    ↓
제품 추천 점수 계산
```

### 2. **사용자 프로필 매칭**

사용자가 온보딩 설문을 완료하면:
1. 사용자의 답변을 기반으로 **취향 조합**을 찾습니다
2. 해당 `taste_id`를 찾습니다
3. `taste_id`에 해당하는 **Scoring Logic**을 적용합니다
4. 제품 추천 점수를 계산합니다

### 3. **추천 문구 생성**

각 취향 조합에 대해:
- **리뷰_기반_추천문구**: 실제 구매자 리뷰를 분석한 문구
- **AI_기반_추천문구**: AI가 생성한 문구

이 문구들을 사용하여 사용자에게 제품을 추천하는 이유를 설명합니다.

## 🔄 데이터 흐름

### 시나리오: 사용자가 온보딩 설문 완료

```
1. 사용자 온보딩 설문
   ├─ 인테리어 스타일: "모던 & 미니멀"
   ├─ 가구 구성: "1인 가구"
   ├─ 우선순위: "디자인"
   └─ 예산: "500만원 미만"

2. taste_recommendations_768.csv에서 매칭
   └─ taste_id: 1 (예시)

3. taste_id → Scoring Logic 매핑
   └─ Scoring_Logic_001 (예시)

4. Scoring Logic 적용
   ├─ 가중치: 디자인 30%, 가격 25%, 용량 20% 등
   ├─ 보너스: OBJET 라인업 +0.1점
   └─ 페널티: 대용량 제품 -0.2점 (1인 가구)

5. 제품 추천 점수 계산
   └─ 각 제품에 대해 0.0~1.0 점수 부여

6. 추천 문구 생성
   └─ "리뷰_기반_추천문구" 또는 "AI_기반_추천문구" 사용
```

## 📈 768개 취향 조합의 의미

### 왜 768개인가?

이는 다양한 취향 요소의 **조합(Combination)**입니다:

```
인테리어_스타일: 4가지 (모던, 코지, 럭셔리, 유니크)
메이트_구성: 4가지 (1인, 2인, 3~4인, 5인 이상)
우선순위: 4가지 (디자인, 기술, 에너지, 가성비)
예산_범위: 4가지 (실속형, 표준형, 고급형, 프리미엄)
선호_라인업: 3가지 (OBJET, SIGNATURE, 기본형)

이론적 조합: 4 × 4 × 4 × 4 × 3 = 768개
```

실제로는 모든 조합이 의미 있는 것은 아니므로, 실제 데이터에서 의미 있는 조합만 선별하여 768개를 구성했습니다.

## 🔧 코드에서의 사용

### 1. 추천 엔진에서 사용

```python
# api/services/recommendation_engine.py
def get_recommendations(self, user_profile: dict, taste_id: int = None):
    # taste_id가 있으면 취향별 로직 사용
    if taste_id is not None:
        score = calculate_product_score_with_taste_logic(
            product=product,
            profile=profile,
            taste_id=taste_id  # ← 여기서 사용
        )
```

### 2. 추천 문구 생성에서 사용

```python
# api/services/recommendation_reason_generator.py
def generate_reason(self, product, user_profile, taste_info=None):
    # taste_info는 CSV 행 전체를 dict로 변환한 것
    if taste_info and taste_info.get('리뷰_기반_추천문구'):
        base_reason = taste_info['리뷰_기반_추천문구']
        # 개인화 처리 후 반환
```

### 3. 시뮬레이션에서 사용

```python
# api/management/commands/simulate_taste_recommendations.py
# 768개 취향 조합 모두에 대해 추천 시뮬레이션 실행
for row in csv_data:
    taste_id = int(row['taste_id'])
    # 각 taste_id에 대해 추천 실행
```

## 💡 핵심 정리

1. **768개 취향 조합**: 다양한 사용자 취향을 표현
2. **50개 Scoring Logic**: 유사한 취향을 그룹화하여 효율성 확보
3. **개인화된 추천**: 각 취향 조합에 맞는 제품 추천
4. **추천 문구**: 리뷰 기반 또는 AI 기반 문구로 추천 이유 설명

## ❓ 자주 묻는 질문

### Q1. 왜 768개나 되는가?
A: 다양한 취향 조합을 모두 커버하기 위해서입니다. 실제로는 50개의 Scoring Logic으로 그룹화하여 사용합니다.

### Q2. taste_id는 어떻게 결정되는가?
A: 사용자의 온보딩 설문 답변을 기반으로 가장 유사한 취향 조합을 찾습니다.

### Q3. 새로운 취향 조합을 추가할 수 있는가?
A: 네, CSV 파일에 새로운 행을 추가하고, 해당 taste_id에 대한 Scoring Logic을 생성하면 됩니다.

### Q4. 리뷰_기반_추천문구와 AI_기반_추천문구의 차이는?
A: 
- **리뷰_기반**: 실제 구매자 리뷰를 분석하여 생성 (더 신뢰도 높음)
- **AI_기반**: AI가 생성한 문구 (더 다양하고 창의적)

## 📚 관련 파일

- `api/scoring_logic/taste_scoring_logics.json`: 50개 Scoring Logic 정의
- `api/utils/taste_scoring.py`: 취향별 점수 계산 로직
- `api/services/recommendation_reason_generator.py`: 추천 문구 생성
- `api/management/commands/simulate_taste_recommendations.py`: 시뮬레이션 스크립트

