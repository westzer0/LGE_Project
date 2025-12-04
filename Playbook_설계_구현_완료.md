# Playbook 설계 기반 추천 엔진 구현 완료

## ✅ 구현 완료 항목

### 1. 정책 테이블 분리 ✅

#### Hard Filter Table
- **파일**: `api/scoring_logic/hard_filter_rules.json`
- **내용**: 주거 형태, 가족 구성, 예산, 라이프스타일 기반 필터링 규칙
- **형식**: JSON 기반 정책 테이블

#### Weight Table
- **파일**: `api/scoring_logic/weight_rules.json`
- **내용**:
  - SpecScore 규칙
  - PreferenceScore 규칙
  - LifestyleScore 규칙
  - PriceScore 규칙
  - ReviewScore 규칙

#### 정책 로더
- **파일**: `api/utils/policy_loader.py`
- **기능**: JSON 정책 테이블 로드 및 조회
- **Singleton 패턴**으로 메모리 효율성 확보

### 2. Hard Filter 구현 ✅

- **파일**: `api/utils/playbook_filters.py`
- **기능**: 정책 테이블 기반 필터링
- **특징**:
  - 코드 수정 없이 JSON 파일만 수정하여 필터 규칙 변경 가능
  - Sparse Matrix 형태로 필요한 규칙만 정의

### 3. Scoring Model 구현 ✅

- **파일**: `api/utils/playbook_scoring.py`
- **구조**: **5개 컴포넌트 합산 방식**

```
TotalScore = SpecScore + PreferenceScore + LifestyleScore + ReviewScore + PriceScore
```

#### ScoreBreakdown 클래스
- 각 컴포넌트 점수를 명시적으로 분리
- `to_dict()` 메서드로 JSON 직렬화 지원

#### 각 컴포넌트 구현

**SpecScore**: 스펙 적합도 점수
- 가족 구성 기반 용량 매칭
- TV 패널 타입 매칭
- 게임 관련 스펙 매칭

**PreferenceScore**: 우선순위 반영 점수
- 우선순위 배열 지원 (1순위, 2순위, 3순위)
- 배율 방식 적용
- 취향별 차등 반영

**LifestyleScore**: 라이프스타일 점수
- 요리 빈도 기반 가산점
- 세탁 패턴 기반 가산점
- 미디어/게임 취향 기반 가산점

**ReviewScore**: 리뷰 기반 점수
- 평균 별점 기반 점수
- 리뷰 개수 기반 점수
- 부정 키워드 기반 감점

**PriceScore**: 예산 적합도 점수
- 예산 범위 내 가산점
- 예산 초과 시 감점
- budget_level 기반 패널티 조정

### 4. GPT Explanation Layer 구현 ✅

- **파일**: `api/services/playbook_explanation_generator.py`
- **기능**: 점수 breakdown을 활용한 설명 생성

#### 생성되는 설명
1. **why_summary**: 왜 이 제품을 추천하는지
2. **lifestyle_message**: 라이프스타일 연계 메시지
3. **design_message**: 디자인 관련 메시지
4. **review_highlight**: 리뷰 요약

#### 특징
- 점수 breakdown을 분석하여 주요 컴포넌트 기반 설명
- 사용자 온보딩 응답과 제품 스펙을 연결
- GPT 없이도 기본 설명 생성 가능

### 5. Playbook 추천 엔진 구현 ✅

- **파일**: `api/services/playbook_recommendation_engine.py`
- **3단계 파이프라인**:

```
Step 1: Hard Filter → Step 2: Scoring → Step 3: GPT Explanation
```

#### 주요 메서드
- `get_recommendations()`: 전체 파이프라인 실행
- `_apply_hard_filter()`: 정책 테이블 기반 필터링
- `_score_products()`: 5개 컴포넌트 합산 점수 계산
- `_format_recommendation_with_explanation()`: 최종 추천 결과 포맷팅

### 6. API 엔드포인트 추가 ✅

- **URL**: `/api/recommend/playbook/`
- **메서드**: `POST`
- **파일**: `api/views.py` → `recommend_playbook_view()`

#### 요청 예시
```json
{
  "vibe": "modern",
  "household_size": 4,
  "housing_type": "apartment",
  "pyung": 30,
  "priority": ["tech", "design"],
  "budget_level": "medium",
  "budget_amount": 2000000,
  "categories": ["TV", "KITCHEN"],
  "onboarding_data": {
    "cooking": "high",
    "laundry": "weekly",
    "media": "gaming"
  },
  "options": {
    "top_n": 3
  }
}
```

#### 응답 예시
```json
{
  "success": true,
  "count": 3,
  "user_profile_summary": "4인 가족이 아파트 30평에 살며 모던한 인테리어 스타일을 선호합니다.",
  "recommendations": [
    {
      "product_id": 1,
      "name": "LG OLED55C5",
      "category": "TV",
      "total_score": 87.2,
      "score_breakdown": {
        "SpecScore": 32.0,
        "PreferenceScore": 18.0,
        "LifestyleScore": 20.0,
        "ReviewScore": 9.0,
        "PriceScore": 8.0,
        "TotalScore": 87.2
      },
      "explanation": {
        "why_summary": "...",
        "lifestyle_message": "...",
        "design_message": "...",
        "review_highlight": "..."
      }
    }
  ]
}
```

---

## 📂 생성된 파일 목록

### 정책 테이블
1. `api/scoring_logic/hard_filter_rules.json` - Hard Filter 규칙
2. `api/scoring_logic/weight_rules.json` - Weight 규칙

### 유틸리티
3. `api/utils/policy_loader.py` - 정책 테이블 로더
4. `api/utils/playbook_filters.py` - Playbook Hard Filter
5. `api/utils/playbook_scoring.py` - Playbook Scoring Model

### 서비스
6. `api/services/playbook_recommendation_engine.py` - Playbook 추천 엔진
7. `api/services/playbook_explanation_generator.py` - Playbook 설명 생성기

### API
8. `api/views.py` - `recommend_playbook_view()` 추가
9. `config/urls.py` - `/api/recommend/playbook/` 엔드포인트 추가

### 문서
10. `추천_엔진_시스템_프롬프트_Playbook.md` - 시스템 프롬프트 문서
11. `현재_구현_vs_Playbook_비교_분석.md` - 비교 분석 문서
12. `Playbook_설계_구현_완료.md` - 이 문서

---

## 🔄 기존 구현과의 관계

### 병행 운영 가능
- **기존 추천 엔진**: `/api/recommend/` (유지)
- **Playbook 추천 엔진**: `/api/recommend/playbook/` (신규)

두 엔진은 독립적으로 동작하며, 필요에 따라 선택적으로 사용 가능합니다.

### 점진적 전환 가능
1. 테스트 기간: 두 엔진 병행 운영
2. 비교 검증: 결과 비교 및 성능 평가
3. 점진적 전환: 검증 후 Playbook 엔진으로 전환
4. 기존 엔진 유지 또는 제거 결정

---

## 🎯 핵심 차이점

| 항목 | 기존 구현 | Playbook 구현 |
|------|-----------|---------------|
| **점수 구조** | 가중치 평균 (0~1.0) | 5개 컴포넌트 합산 (정수/실수) |
| **정책 관리** | 하드코딩 | JSON 테이블 분리 |
| **ReviewScore** | 미구현 | ✅ 별도 컴포넌트 |
| **점수 Breakdown** | 없음 | ✅ 명시적 분리 |
| **GPT Explanation** | 기본 문구 | ✅ Breakdown 활용 |
| **필터링** | 하드코딩 | ✅ 정책 테이블 기반 |

---

## 📊 점수 계산 예시

### 예시: Modern + Tech 사용자의 TV 추천

```
SpecScore: 32점
  - 해상도 4K: +15점
  - 주사율 120Hz: +10점
  - 패널 타입 OLED: +7점

PreferenceScore: 18점
  - Tech 우선순위 1순위: 해상도 점수 ×1.5 = +9점
  - 주사율 점수 ×1.4 = +9점

LifestyleScore: 20점
  - 게임 취향: 120Hz+ 가산점 +8점
  - HDMI2.1 가산점 +5점
  - 미디어 소비 패턴 반영 +7점

ReviewScore: 9점
  - 평균 별점 4.7점, 리뷰 200개+: +8점
  - 부정 키워드 없음: +1점

PriceScore: 8점
  - 예산 범위 내: +10점 (약간 초과로 -2점)

─────────────────────────────
TotalScore: 87.2점
```

---

## 🚀 사용 방법

### 1. Playbook API 호출

```javascript
fetch('/api/recommend/playbook/', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json',
    },
    body: JSON.stringify({
        vibe: 'modern',
        household_size: 4,
        housing_type: 'apartment',
        pyung: 30,
        priority: ['tech', 'design'],
        budget_level: 'medium',
        budget_amount: 2000000,
        categories: ['TV', 'KITCHEN'],
        onboarding_data: {
            cooking: 'high',
            laundry: 'weekly',
            media: 'gaming'
        },
        options: {
            top_n: 3
        }
    })
})
.then(response => response.json())
.then(data => {
    console.log('추천 결과:', data);
    console.log('점수 Breakdown:', data.recommendations[0].score_breakdown);
    console.log('설명:', data.recommendations[0].explanation);
});
```

### 2. 정책 테이블 수정

필터링 규칙이나 가중치를 변경하려면:
1. `api/scoring_logic/hard_filter_rules.json` 또는 `weight_rules.json` 수정
2. 서버 재시작 또는 캐시 클리어
3. 즉시 적용됨 (코드 수정 불필요)

---

## 📝 다음 단계 (선택)

### 추가 개선 사항
1. **배치 전처리**: ReviewScore를 미리 계산하여 DB에 저장
2. **정책 테이블 GUI**: 웹 인터페이스로 정책 수정
3. **A/B 테스트**: 기존 엔진과 Playbook 엔진 비교
4. **성능 최적화**: 정책 테이블 캐싱 강화
5. **GPT 강화**: ChatGPT API를 활용한 더 풍부한 설명 생성

### 테스트
1. 다양한 사용자 프로필로 테스트
2. 점수 breakdown 검증
3. 필터링 정확도 확인
4. 설명 품질 평가

---

## ✅ 구현 완료 체크리스트

- [x] Hard Filter Table JSON 생성
- [x] Weight Table JSON 생성
- [x] 정책 로더 구현
- [x] Playbook Hard Filter 구현
- [x] Playbook Scoring Model 구현 (5개 컴포넌트)
- [x] SpecScore 구현
- [x] PreferenceScore 구현
- [x] LifestyleScore 구현
- [x] ReviewScore 구현
- [x] PriceScore 구현
- [x] 점수 Breakdown 구조 (ScoreBreakdown 클래스)
- [x] Playbook Explanation Generator 구현
- [x] Playbook Recommendation Engine 구현
- [x] API 엔드포인트 추가
- [x] URL 라우팅 설정
- [x] 문서화

---

## 🎉 결론

**Playbook 설계를 기반으로 한 추천 엔진이 완전히 구현되었습니다!**

- ✅ 정책 테이블 분리로 유연한 관리
- ✅ 5개 컴포넌트 합산 방식으로 명확한 점수 구조
- ✅ 점수 Breakdown을 활용한 상세한 설명
- ✅ 기존 구현과 병행 운영 가능

이제 `/api/recommend/playbook/` 엔드포인트를 통해 새로운 추천 엔진을 사용할 수 있습니다!


