# 최근 3일간 워크플로우 및 현황 보고서

## 📋 개요

이 문서는 최근 3일간 진행된 작업 내용과 현재 taste별 제품 scoring 로직까지의 전체 워크플로우를 정리한 보고서입니다.

---

## 🎯 주요 완료 작업

### 1. Taste별 독립적인 Scoring Logic 아키텍처 구축

#### 1.1 아키텍처 구조
```
api/
├── services/
│   └── taste_scoring_logic_service.py    # Taste별 Logic 관리 서비스
├── utils/
│   ├── taste_scoring.py                  # Scoring Logic 적용 (기존 로직 유지)
│   ├── scoring.py                         # 기본 scoring 함수들
│   └── category_mapping.py                # MAIN_CATEGORY 매핑
└── scoring_logic/
    ├── taste_scoring_logics.json          # 기존 공유 로직 (하위 호환성)
    └── tastes/                            # Taste별 독립 파일
        ├── taste_001.json
        ├── taste_002.json
        ...
        └── taste_120.json
```

#### 1.2 핵심 컴포넌트

**A. TasteScoringLogicService** (`api/services/taste_scoring_logic_service.py`)
- **역할**: Taste별 독립적인 scoring logic 관리
- **주요 기능**:
  - Logic 조회, 생성, 저장
  - 캐싱 지원
  - 모든 MAIN_CATEGORY 지원
- **Logic 우선순위**:
  1. Taste별 독립 파일 (`tastes/taste_{id}.json`) - 최우선
  2. 기존 공유 로직 파일 (`taste_scoring_logics.json`)
  3. 동적 생성 (온보딩 데이터 기반)
  4. 기본 로직 (기본 가중치)

**B. Taste Scoring** (`api/utils/taste_scoring.py`)
- **역할**: Product scoring에 taste logic 적용
- **주요 함수**:
  ```python
  calculate_product_score_with_taste_logic(
      product, profile, taste_id, onboarding_data
  ) -> float
  ```
- **점수 산출 프로세스**:
  1. Taste ID 조회: 사용자의 `member.taste` 값 (1~120)
  2. Logic 조회: TasteScoringLogicService에서 logic 가져오기
  3. MAIN_CATEGORY 결정: `product.spec.spec_json`의 `MAIN_CATEGORY` 사용
  4. 가중치 선택: Logic의 weights에서 MAIN_CATEGORY에 해당하는 가중치
  5. 속성 점수 계산: 각 속성별 점수 계산 (resolution, brightness, capacity 등)
  6. 가중 평균: 속성 점수와 가중치를 곱하여 가중 평균 계산
  7. 보너스/페널티 적용: Logic의 bonuses/penalties 적용
  8. 최종 점수: 0.0 ~ 1.0 범위로 제한

#### 1.3 Logic 파일 구조

각 `tastes/taste_{id}.json` 파일 구조:
```json
{
  "logic_id": "taste_001",
  "logic_name": "Scoring_Logic_Taste_001",
  "taste_id": 1,
  "weights": {
    "TV": {
      "resolution": 0.50,
      "brightness": 0.30,
      "price_match": 0.20
    },
    "냉장고": {
      "capacity": 0.60,
      "energy_efficiency": 0.40
    }
    // 모든 MAIN_CATEGORY 지원
  },
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
  ],
  "filters": {
    "must_have": [],
    "should_have": [],
    "exclude": []
  }
}
```

---

### 2. Recommendation Engine 통합

#### 2.1 RecommendationEngine (`api/services/recommendation_engine.py`)

**주요 흐름**:
1. **Taste 기반 MAIN CATEGORY 선택**
   - `taste_id`가 있으면 `get_categories_for_taste()` 호출
   - 선택된 카테고리를 `user_profile['categories']`에 설정

2. **Hard Filtering**
   - 가격 범위 필터
   - MAIN_CATEGORY 기반 필터링
   - 반려동물 필터
   - 가족 구성 기반 용량 필터
   - 주거 형태/평수 기반 크기 필터
   - 생활 패턴 기반 필터

3. **Soft Scoring**
   - `taste_id`가 있으면 `calculate_product_score_with_taste_logic()` 사용
   - 없으면 기본 `calculate_product_score()` 사용

4. **카테고리별 상위 3개 추천**
   - 각 MAIN_CATEGORY별로 상위 3개 제품 선택
   - 추천 이유 생성 (`recommendation_reason_generator`)

#### 2.2 사용 예시

```python
from api.services.recommendation_engine import recommendation_engine

result = recommendation_engine.get_recommendations(
    user_profile={
        'vibe': 'modern',
        'household_size': 4,
        'budget_level': 'medium',
        'categories': ['TV', '냉장고'],  # 또는 taste_id로 자동 선택
        'onboarding_data': {...}
    },
    taste_id=1,  # taste별 scoring logic 사용
    limit=3
)
```

---

### 3. Ill-suited Category Detection Logic

#### 3.1 Ill-suited 판별 로직 (`ILL_SUITED_LOGIC.md`)

**판별 기준**:

1. **반려동물 관련**
   - `has_pet = False` → 반려동물 전용 제품 제외

2. **가구 수 관련**
   - 1인 가구 → 대형 가전 (김치냉장고, 워시타워) 제외
   - 5인 이상 가구 → 미니 가전 제외

3. **주거 형태 및 평수**
   - 원룸/오피스텔 + 20평 이하 → 대형 가전 제외

4. **주요 공간 관련**
   - 주방이 주요 공간 아님 → 주방 가전 제외
   - 세탁실/베란다가 주요 공간 아님 → 세탁 가전 제외

5. **생활 패턴**
   - 요리 빈도 낮음 → 주방 가전 제외
   - 세탁 빈도 낮음 → 세탁 가전 제외
   - 미디어 사용 없음 → 미디어 가전 제외

6. **인테리어 무드**
   - luxury → 저가형 제품 제외

#### 3.2 점수 계산 방식

- **Ill-suited 카테고리**: 0점 고정, `ILL_SUITED_CATEGORIES`에 저장
- **일반 카테고리**: 0~100점, `TasteCategorySelector._calculate_category_score()`로 계산

---

### 4. TASTE_CONFIG 정규화 제안

#### 4.1 현재 문제점 (`TASTE_CONFIG_NORMALIZATION_PROPOSAL.md`)

1. **데이터 중복**
   - 개별 컬럼 (`TV_SCORE`, `냉장고_SCORE`)과 JSON 컬럼 (`CATEGORY_SCORES`) 중복
   - 확장성 문제 (새 카테고리 추가 시 컬럼 추가 필요)

2. **테이블 구조의 무거움**
   - 20개 이상의 카테고리별 점수 컬럼
   - 큰 JSON 컬럼 (CLOB)

3. **유지보수 어려움**
   - 카테고리 추가 시 ALTER TABLE 필요

#### 4.2 정규화 제안

**새 테이블 구조**:
1. **TASTE_CONFIG** (기본 테이블 - 유지)
   - JSON 컬럼 제거
   - 개별 점수 컬럼 제거

2. **TASTE_CATEGORY_SCORES** (새 테이블)
   ```sql
   CREATE TABLE TASTE_CATEGORY_SCORES (
       TASTE_ID NUMBER NOT NULL,
       CATEGORY_NAME VARCHAR2(50) NOT NULL,
       SCORE NUMBER(5,2) NOT NULL,
       IS_RECOMMENDED CHAR(1) DEFAULT 'N',
       IS_ILL_SUITED CHAR(1) DEFAULT 'N',
       PRIMARY KEY (TASTE_ID, CATEGORY_NAME)
   );
   ```

3. **TASTE_RECOMMENDED_PRODUCTS** (새 테이블)
   ```sql
   CREATE TABLE TASTE_RECOMMENDED_PRODUCTS (
       TASTE_ID NUMBER NOT NULL,
       CATEGORY_NAME VARCHAR2(50) NOT NULL,
       PRODUCT_ID NUMBER NOT NULL,
       SCORE NUMBER(5,2),
       RANK_ORDER NUMBER(2),
       PRIMARY KEY (TASTE_ID, CATEGORY_NAME, PRODUCT_ID)
   );
   ```

**마이그레이션 전략**:
- Phase 1: 새 테이블 생성 및 데이터 이전
- Phase 2: 코드 업데이트
- Phase 3: 기존 컬럼 제거 (선택사항)

---

### 5. Zero Score 분석 및 해결 방안

#### 5.1 문제점 (`ZERO_SCORE_ANALYSIS_REPORT.md`)

**100% 0점인 칼럼 (10개)**:
1. `OBJET_SCORE`
2. `SIGNATURE_SCORE`
3. `건조기_SCORE`
4. `로봇청소기_SCORE`
5. `사운드바_SCORE`
6. `세탁기_SCORE`
7. `오븐_SCORE`
8. `워시타워_SCORE`
9. `의류관리기_SCORE`
10. `전자레인지_SCORE`

#### 5.2 원인 분석

1. **카테고리명 불일치**
   - 점수 계산 로직: `세탁기` → Oracle DB: `세탁`
   - 점수 계산 로직: `전자레인지` → Oracle DB: `광파오븐전자레인지`

2. **OBJET/SIGNATURE**
   - 브랜드 라인이므로 `MAIN_CATEGORY`가 아님
   - 별도 처리 필요

3. **점수 계산 로직 조건 불일치**
   - `main_space='living'`일 때 세탁 관련 카테고리 점수 낮음

#### 5.3 해결 방안

1. **카테고리명 매핑 추가**
   ```python
   CATEGORY_NAME_MAPPING = {
       '세탁': '세탁기',
       '광파오븐전자레인지': '전자레인지',
   }
   ```

2. **점수 계산 로직 보정**
   - `main_space='living'`일 때 세탁 관련 카테고리 점수 상향

3. **데이터 재생성**
   - 수정 후 모든 taste_id 1-120 데이터 재생성

---

## 🔄 전체 워크플로우

### Step 1: 사용자 온보딩
```
사용자 온보딩 데이터 입력
  ↓
taste_id 계산 (1~120)
  ↓
TASTE_CONFIG 테이블에 저장
```

### Step 2: 카테고리 선택
```
taste_id 기반으로 MAIN_CATEGORY 선택
  ↓
Ill-suited 카테고리 제외
  ↓
카테고리별 점수 계산 (0~100점)
  ↓
상위 카테고리 선택
```

### Step 3: 제품 필터링 (Hard Filter)
```
가격 범위 필터
  ↓
MAIN_CATEGORY 필터
  ↓
반려동물 필터
  ↓
가족 구성 기반 용량 필터
  ↓
주거 형태/평수 기반 크기 필터
  ↓
생활 패턴 기반 필터
```

### Step 4: 제품 스코어링 (Soft Score)
```
taste_id 기반 Scoring Logic 조회
  ↓
MAIN_CATEGORY별 가중치 선택
  ↓
속성별 점수 계산
  - resolution, brightness, capacity 등
  ↓
가중 평균 계산
  ↓
보너스/페널티 적용
  ↓
최종 점수 (0.0 ~ 1.0)
```

### Step 5: 추천 생성
```
카테고리별 상위 3개 제품 선택
  ↓
추천 이유 생성
  ↓
최종 추천 반환
```

---

## 📊 현재 구현 상태

### ✅ 완료된 기능

1. **Taste별 독립적인 Scoring Logic 아키텍처**
   - TasteScoringLogicService 구현
   - Taste별 독립 파일 지원
   - 동적 logic 생성 지원
   - 모든 MAIN_CATEGORY 지원

2. **Recommendation Engine 통합**
   - Taste 기반 카테고리 선택
   - Hard Filtering
   - Soft Scoring (taste별 logic 적용)
   - 카테고리별 상위 3개 추천

3. **Ill-suited Category Detection**
   - 6가지 판별 기준 구현
   - 0점 카테고리 관리

4. **문서화**
   - TASTE_SCORING_ARCHITECTURE.md
   - TASTE_CONFIG_NORMALIZATION_PROPOSAL.md
   - ILL_SUITED_LOGIC.md
   - ZERO_SCORE_ANALYSIS_REPORT.md

### ⚠️ 개선 필요 사항

1. **카테고리명 매핑**
   - Oracle DB와 점수 계산 로직 간 카테고리명 불일치 해결
   - `세탁` → `세탁기`, `광파오븐전자레인지` → `전자레인지` 등

2. **Zero Score 문제**
   - 10개 카테고리의 0점 문제 해결
   - OBJET/SIGNATURE 별도 처리

3. **TASTE_CONFIG 정규화**
   - 정규화 제안 검토 및 마이그레이션 계획 수립

4. **점수 계산 로직 보정**
   - `main_space='living'`일 때 세탁 관련 카테고리 점수 상향

---

## 🎯 다음 단계 제안

### 1. 즉시 조치 (High Priority)

1. **카테고리명 매핑 추가**
   - `taste_category_selector.py`에 카테고리명 매핑 추가
   - Oracle DB와 점수 계산 로직 간 불일치 해결

2. **Zero Score 문제 해결**
   - 카테고리명 매핑 적용
   - 점수 계산 로직 보정
   - 데이터 재생성

### 2. 단기 계획 (Medium Priority)

1. **TASTE_CONFIG 정규화**
   - 정규화 제안 검토
   - 마이그레이션 스크립트 작성
   - 테스트 환경 검증

2. **점수 계산 로직 개선**
   - `main_space='living'`일 때 세탁 관련 카테고리 점수 상향
   - 의류관리기 점수 보정

### 3. 장기 계획 (Low Priority)

1. **성능 최적화**
   - Logic 캐싱 개선
   - 쿼리 최적화

2. **모니터링 및 로깅**
   - 점수 계산 로그 추가
   - 추천 품질 모니터링

---

## 📝 관련 파일 목록

### 핵심 구현 파일
- `api/services/taste_scoring_logic_service.py`: Taste별 Logic 관리 서비스
- `api/utils/taste_scoring.py`: Taste별 Scoring Logic 적용
- `api/services/recommendation_engine.py`: 추천 엔진
- `api/utils/scoring.py`: 기본 scoring 함수들
- `api/utils/category_mapping.py`: MAIN_CATEGORY 매핑

### 문서 파일
- `TASTE_SCORING_ARCHITECTURE.md`: Taste별 Scoring Logic 아키텍처
- `TASTE_CONFIG_NORMALIZATION_PROPOSAL.md`: TASTE_CONFIG 정규화 제안
- `ILL_SUITED_LOGIC.md`: Ill-suited 카테고리 판별 로직
- `ZERO_SCORE_ANALYSIS_REPORT.md`: Zero Score 분석 보고서

### 설정 파일
- `api/scoring_logic/taste_scoring_logics.json`: 기존 공유 로직
- `api/scoring_logic/tastes/`: Taste별 독립 파일 디렉토리

---

## 🔍 LLM 의견 및 제안

### 1. 아키텍처 평가

**장점**:
- ✅ Taste별 독립적인 logic 관리로 확장성 우수
- ✅ 하위 호환성 유지 (기존 코드 수정 최소화)
- ✅ 동적 logic 생성 지원으로 유연성 확보
- ✅ 모든 MAIN_CATEGORY 지원

**개선 제안**:
- ⚠️ Logic 파일이 많아질 경우 관리 복잡도 증가 → 버전 관리 시스템 도입 고려
- ⚠️ 캐시 무효화 전략 명확화 필요

### 2. 데이터 구조 평가

**현재 구조의 문제점**:
- ❌ TASTE_CONFIG 테이블의 중복 데이터 (개별 컬럼 + JSON)
- ❌ 카테고리 추가 시 ALTER TABLE 필요
- ❌ Oracle 컬럼명 30자 제한

**정규화 제안의 장점**:
- ✅ 확장성 향상 (새 카테고리 추가 시 INSERT만)
- ✅ 데이터 중복 제거
- ✅ 쿼리 성능 향상 (필요한 카테고리만 조회)

### 3. 점수 계산 로직 평가

**현재 로직의 강점**:
- ✅ 가중치 기반 점수 계산으로 유연성 확보
- ✅ 보너스/페널티 시스템으로 세밀한 조정 가능
- ✅ MAIN_CATEGORY별 독립적인 가중치 지원

**개선 필요 사항**:
- ⚠️ 카테고리명 불일치 해결 (즉시 조치 필요)
- ⚠️ Zero Score 문제 해결
- ⚠️ 점수 계산 로직 보정 (main_space='living'일 때)

---

## 📌 결론

최근 3일간 **Taste별 독립적인 Scoring Logic 아키텍처**를 구축하고, **Recommendation Engine에 통합**하는 작업이 완료되었습니다. 

현재 **taste별 제품 scoring logic까지 구현**되어 있으며, 다음 단계로는:
1. 카테고리명 매핑 추가 (즉시 조치)
2. Zero Score 문제 해결
3. TASTE_CONFIG 정규화 검토

를 진행하는 것을 권장합니다.

---

**작성일**: 2025-01-XX  
**작성자**: AI Assistant  
**버전**: 1.0


