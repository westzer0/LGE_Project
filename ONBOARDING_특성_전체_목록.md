# 온보딩 특성 전체 목록

DX Project의 온보딩 세션에서 수집하는 모든 특성(Characteristics) 목록입니다.

---

## 📋 목차

1. [Step 1: 분위기 (Vibe)](#step-1-분위기-vibe)
2. [Step 2: 메이트 (Mate)](#step-2-메이트-mate)
3. [Step 3: 주거 형태 (Housing)](#step-3-주거-형태-housing)
4. [Step 4: 라이프스타일 (Lifestyle)](#step-4-라이프스타일-lifestyle)
5. [Step 5: 우선순위 (Priority)](#step-5-우선순위-priority)
6. [Step 6: 예산 (Budget)](#step-6-예산-budget)
7. [데이터베이스 스키마](#데이터베이스-스키마)

---

## Step 1: 분위기 (Vibe)

**질문**: "새로운 가전과 함께할 공간, 어떤 분위기를 꿈꾸시나요?"

| 값 (ANSWER_VALUE) | 표시 텍스트 (ANSWER_TEXT) | 설명 |
|------------------|------------------------|------|
| `modern` | 모던 & 미니멀 | 깔끔하고 심플한 스타일 |
| `cozy` | 코지 & 네이처 | 따뜻하고 자연스러운 톤 |
| `pop` | 유니크 & 팝 | 생기있고 개성있는 스타일 |
| `luxury` | 럭셔리 & 아티스틱 | 고급스럽고 예술적인 분위기 |

**데이터베이스 필드**: `ONBOARDING_SESSION.VIBE` (VARCHAR2(20))

---

## Step 2: 메이트 (Mate)

### 2.1 가구 구성

**질문**: "이 공간에서 함께 생활하는 메이트는 누구인가요?"

| 값 (ANSWER_VALUE) | 표시 텍스트 (ANSWER_TEXT) | 설명 |
|------------------|------------------------|------|
| `alone` | 나 혼자 산다 | 1인 가구 |
| `couple` | 우리 둘이 알콩달콩 | 2인 가구 (부부/연인) |
| `family_3_4` | 아이가 있는 3~4인 가족 | 자녀 있는 가족 |
| `family_5plus` | 5인 이상 대가족 | 대가족 |

**데이터베이스 필드**: `ONBOARDING_SESSION.HOUSEHOLD_SIZE` (NUMBER)
- `1` = alone
- `2` = couple
- `3-4` = family_3_4
- `5+` = family_5plus

### 2.2 반려동물 여부

**질문**: "혹시 반려동물과 함께하시나요?" (조건부 질문)

| 값 (ANSWER_VALUE) | 표시 텍스트 (ANSWER_TEXT) | 설명 |
|------------------|------------------------|------|
| `yes` | 네, 사랑스러운 댕냥이가 있어요 | 반려동물 있음 |
| `no` | 아니요, 없어요 | 반려동물 없음 |

**데이터베이스 필드**: `ONBOARDING_SESSION.HAS_PET` (CHAR(1))
- `'Y'` = yes
- `'N'` = no

---

## Step 3: 주거 형태 (Housing)

### 3.1 주거 형태

**질문**: "가전을 설치할 곳의 주거 형태는 무엇인가요?"

| 값 (ANSWER_VALUE) | 표시 텍스트 (ANSWER_TEXT) | 설명 |
|------------------|------------------------|------|
| `apartment` | 아파트 | 아파트 |
| `officetel` | 오피스텔 | 오피스텔 |
| `detached` | 주택(단독/다가구) | 단독주택, 다가구주택 |
| `studio` | 원룸 | 원룸 |

**데이터베이스 필드**: `ONBOARDING_SESSION.HOUSING_TYPE` (VARCHAR2(20))

### 3.2 주요 공간 (다중 선택 가능)

**질문**: "가전을 배치할 주요 공간은 어디인가요?" (조건부 질문)

| 값 (ANSWER_VALUE) | 표시 텍스트 (ANSWER_TEXT) | 설명 |
|------------------|------------------------|------|
| `living` | 거실 | 거실 공간 |
| `bedroom` | 방 | 침실 |
| `kitchen` | 주방 | 주방 |
| `dressing` | 드레스룸 | 드레스룸 |
| `study` | 서재 | 서재/공부방 |
| `all` | 전체 | 모든 공간 |

**데이터베이스 필드**: `ONBOARDING_SESSION.MAIN_SPACE` (CLOB - JSON 배열)
- 예: `["living", "kitchen", "bedroom"]`
- 단일 선택 시: `["living"]`

### 3.3 평수 (크기)

**질문**: "해당 공간의 크기는 대략 어느 정도인가요?" (조건부 질문)

**입력 형식**: 숫자 입력 (평수 단위)

**데이터베이스 필드**: `ONBOARDING_SESSION.PYUNG` (NUMBER)
- 예: `25`, `30`, `45` 등

---

## Step 4: 라이프스타일 (Lifestyle)

### 4.1 요리 빈도 (조건부 - 주방/전체 선택 시)

**질문**: "평소 집에서 요리는 얼마나 자주 하시나요?"

| 값 (ANSWER_VALUE) | 표시 텍스트 (ANSWER_TEXT) | 설명 |
|------------------|------------------------|------|
| `rarely` | 거의 하지 않아요(배달, 간편식 위주) | 요리를 거의 하지 않음 |
| `sometimes` | 가끔 해요(주말 위주) | 주말에만 요리 |
| `often` | 요리하는 걸 좋아하고 자주 해요 | 자주 요리 |

**데이터베이스 필드**: `ONBOARDING_SESSION.COOKING` (VARCHAR2(20))

### 4.2 세탁 빈도 (조건부 - 드레스룸/전체 선택 시)

**질문**: "세탁은 주로 어떻게 하시나요?"

| 값 (ANSWER_VALUE) | 표시 텍스트 (ANSWER_TEXT) | 설명 |
|------------------|------------------------|------|
| `weekly` | 일주일 1번 정도 | 주 1회 세탁 |
| `few_times` | 일주일 2번~3번 정도 | 주 2-3회 세탁 |
| `daily` | 매일 조금씩 | 매일 세탁 |

**데이터베이스 필드**: `ONBOARDING_SESSION.LAUNDRY` (VARCHAR2(20))

### 4.3 미디어 사용 패턴 (조건부 - 거실/방/서재/전체 선택 시)

**질문**: "집에서 TV나 영상을 주로 어떻게 즐기시나요?"

| 값 (ANSWER_VALUE) | 표시 텍스트 (ANSWER_TEXT) | 설명 |
|------------------|------------------------|------|
| `ott` | 넷플릭스, 영화, 드라마 등 OTT를 즐기는 편 | OTT 서비스 주 사용 |
| `gaming` | 게임이 취미라 주로 게임을 즐기는 편 | 게임 중심 |
| `tv` | 뉴스나 예능 등 일반 프로그램 시청하는 편 | 일반 TV 시청 |
| `none` | TV나 영상을 즐기는 편은 아니에요 | 미디어 사용 적음 |

**데이터베이스 필드**: `ONBOARDING_SESSION.MEDIA` (VARCHAR2(20))

---

## Step 5: 우선순위 (Priority)

### 5.1 첫 번째 우선순위

**질문**: "구매 시 가장 중요하게 생각하는 것은 무엇인가요?"

| 값 (ANSWER_VALUE) | 표시 텍스트 (ANSWER_TEXT) | 설명 |
|------------------|------------------------|------|
| `design` | 디자인/무드 | 디자인과 스타일 중요 |
| `tech` | 기술/성능 | 기술력과 성능 중요 |
| `eco` | 에너지효율 | 에너지 효율성 중요 |
| `value` | 가성비 | 가격 대비 성능 중요 |

**데이터베이스 필드**: `ONBOARDING_SESSION.PRIORITY` (VARCHAR2(20))

### 5.2 우선순위 목록 (다중 선택, 순서 중요)

**다중 선택 가능하며, 선택 순서가 중요합니다.**

| 값 (ANSWER_VALUE) | 표시 텍스트 (ANSWER_TEXT) |
|------------------|------------------------|
| `design` | 디자인/무드 |
| `tech` | 기술/성능 |
| `eco` | 에너지효율 |
| `value` | 가성비 |

**데이터베이스 필드**: `ONBOARDING_SESSION.PRIORITY_LIST` (CLOB - JSON 배열)
- 예: `["design", "tech", "eco"]` (순서 중요)
- 첫 번째 값이 `PRIORITY` 필드와 동일해야 함

---

## Step 6: 예산 (Budget)

**질문**: "예산 범위를 선택해주세요."

| 값 (ANSWER_VALUE) | 표시 텍스트 (ANSWER_TEXT) | 설명 |
|------------------|------------------------|------|
| `budget` | 500만원 이하 | 저예산 |
| `standard` | 500~2000만원 | 중간 예산 |
| `premium` | 2000만원 이상 | 고예산 |

**데이터베이스 필드**: `ONBOARDING_SESSION.BUDGET_LEVEL` (VARCHAR2(20))

**호환성 참고**: Django 모델에서는 다음 값도 지원:
- `low` = budget (500만원 이하)
- `medium` = standard (500~2000만원)
- `high` = premium (2000만원 이상)

---

## 데이터베이스 스키마

### ONBOARDING_SESSION 테이블 전체 필드

| 필드명 | 타입 | 설명 | 필수 여부 |
|--------|------|------|----------|
| `SESSION_ID` | VARCHAR2(100) | 세션 ID (PK) | ✅ 필수 |
| `USER_ID` | VARCHAR2(100) | 사용자 ID (카카오 로그인 시) | 선택 |
| `CURRENT_STEP` | NUMBER | 현재 진행 단계 (1~6) | 기본값: 1 |
| `STATUS` | VARCHAR2(20) | 상태 (IN_PROGRESS, COMPLETED, ABANDONED) | 기본값: IN_PROGRESS |
| | | | |
| **Step 1** | | | |
| `VIBE` | VARCHAR2(20) | 분위기 (modern, cozy, pop, luxury) | 선택 |
| | | | |
| **Step 2** | | | |
| `HOUSEHOLD_SIZE` | NUMBER | 가구 인원수 | 선택 |
| `HAS_PET` | CHAR(1) | 반려동물 여부 (Y/N) | 선택 |
| | | | |
| **Step 3** | | | |
| `HOUSING_TYPE` | VARCHAR2(20) | 주거 형태 (apartment, officetel, detached, studio) | 선택 |
| `PYUNG` | NUMBER | 평수 | 선택 |
| `MAIN_SPACE` | CLOB | 주요 공간 (JSON 배열) | 선택 |
| | | | |
| **Step 4** | | | |
| `COOKING` | VARCHAR2(20) | 요리 빈도 (rarely, sometimes, often) | 선택 |
| `LAUNDRY` | VARCHAR2(20) | 세탁 빈도 (weekly, few_times, daily) | 선택 |
| `MEDIA` | VARCHAR2(20) | 미디어 사용 (ott, gaming, tv, none) | 선택 |
| | | | |
| **Step 5** | | | |
| `PRIORITY` | VARCHAR2(20) | 첫 번째 우선순위 | 선택 |
| `PRIORITY_LIST` | CLOB | 우선순위 목록 (JSON 배열) | 선택 |
| | | | |
| **Step 6** | | | |
| `BUDGET_LEVEL` | VARCHAR2(20) | 예산 범위 (budget, standard, premium) | 선택 |
| | | | |
| **추천 결과** | | | |
| `SELECTED_CATEGORIES` | CLOB | 선택한 카테고리 (JSON 배열) | 선택 |
| `RECOMMENDED_PRODUCTS` | CLOB | 추천 제품 ID 목록 (JSON 배열) | 선택 |
| `RECOMMENDATION_RESULT` | CLOB | 최종 추천 결과 (JSON 객체) | 선택 |
| | | | |
| **타임스탬프** | | | |
| `CREATED_AT` | DATE | 세션 생성 시간 | 기본값: SYSDATE |
| `UPDATED_AT` | DATE | 마지막 업데이트 시간 | 기본값: SYSDATE |
| `COMPLETED_AT` | DATE | 온보딩 완료 시간 | 선택 |

---

## 조건부 질문 로직

### 조건부 질문이 나타나는 조건

| 질문 | 조건 |
|------|------|
| 반려동물 여부 (Step 2) | Step 2의 가구 구성 질문 완료 후 |
| 주요 공간 (Step 3) | Step 3의 주거 형태 질문 완료 후 |
| 평수 (Step 3) | Step 3의 주요 공간 선택 후 |
| 요리 빈도 (Step 4) | Step 3에서 `kitchen` 또는 `all` 선택 시 |
| 세탁 빈도 (Step 4) | Step 3에서 `dressing` 또는 `all` 선택 시 |
| 미디어 사용 (Step 4) | Step 3에서 `living`, `bedroom`, `study`, 또는 `all` 선택 시 |

---

## JSON 필드 구조

### MAIN_SPACE (JSON 배열)
```json
["living", "kitchen", "bedroom"]
```

### PRIORITY_LIST (JSON 배열)
```json
["design", "tech", "eco"]
```

### SELECTED_CATEGORIES (JSON 배열)
```json
["TV", "KITCHEN", "LIVING"]
```

### RECOMMENDED_PRODUCTS (JSON 배열)
```json
[1, 2, 3, 4, 5]
```

### RECOMMENDATION_RESULT (JSON 객체)
```json
{
  "onboarding_data": {
    "vibe": "modern",
    "household_size": 2,
    "has_pet": "no",
    "housing_type": "apartment",
    "pyung": 25,
    "main_space": ["living", "kitchen"],
    "cooking": "sometimes",
    "laundry": "weekly",
    "media": "ott",
    "priority": ["design", "tech"],
    "budget_level": "standard"
  },
  "recommended_products": [...],
  "matching_scores": {...}
}
```

---

## Django 모델 매핑

### OnboardingSession 모델 필드

| Django 필드 | DB 필드 | 타입 |
|------------|---------|------|
| `session_id` | `SESSION_ID` | CharField |
| `vibe` | `VIBE` | CharField (choices) |
| `household_size` | `HOUSEHOLD_SIZE` | IntegerField |
| `housing_type` | `HOUSING_TYPE` | CharField (choices) |
| `pyung` | `PYUNG` | IntegerField |
| `priority` | `PRIORITY` | CharField (choices) |
| `budget_level` | `BUDGET_LEVEL` | CharField (choices) |
| `selected_categories` | `SELECTED_CATEGORIES` | JSONField |
| `recommended_products` | `RECOMMENDED_PRODUCTS` | JSONField |
| `recommendation_result` | `RECOMMENDATION_RESULT` | JSONField |
| `current_step` | `CURRENT_STEP` | IntegerField |
| `status` | `STATUS` | CharField (choices) |

**참고**: Django 모델에는 `has_pet`, `main_space`, `cooking`, `laundry`, `media`, `priority_list` 필드가 없지만, 이들은 `recommendation_result` JSON 필드 내에 저장되거나 Oracle DB에 직접 저장됩니다.

---

## 관련 테이블

### 1. ONBOARDING_QUESTION
온보딩 질문 항목 저장

| 필드 | 타입 | 설명 |
|------|------|------|
| `QUESTION_ID` | NUMBER | 질문 ID (PK) |
| `STEP_NUMBER` | NUMBER | 단계 번호 (1~6) |
| `QUESTION_TYPE` | VARCHAR2(50) | 질문 유형 |
| `QUESTION_TEXT` | VARCHAR2(500) | 질문 텍스트 |
| `QUESTION_ORDER` | NUMBER | 질문 순서 |
| `IS_REQUIRED` | CHAR(1) | 필수 여부 (Y/N) |
| `CONDITION_TYPE` | VARCHAR2(100) | 조건부 질문 타입 |
| `CONDITION_VALUE` | VARCHAR2(200) | 조건 값 |

### 2. ONBOARDING_ANSWER
온보딩 선택지 항목 저장

| 필드 | 타입 | 설명 |
|------|------|------|
| `ANSWER_ID` | NUMBER | 선택지 ID (PK) |
| `QUESTION_ID` | NUMBER | 질문 ID (FK) |
| `ANSWER_VALUE` | VARCHAR2(100) | 선택지 값 |
| `ANSWER_TEXT` | VARCHAR2(500) | 선택지 텍스트 |
| `ANSWER_ORDER` | NUMBER | 선택지 순서 |
| `IMAGE_URL` | VARCHAR2(500) | 이미지 URL |
| `IS_ACTIVE` | CHAR(1) | 활성화 여부 (Y/N) |

### 3. ONBOARDING_USER_RESPONSE
사용자 선택지 결과 저장 (상세 로그)

| 필드 | 타입 | 설명 |
|------|------|------|
| `RESPONSE_ID` | NUMBER | 응답 ID (PK) |
| `SESSION_ID` | VARCHAR2(100) | 세션 ID (FK) |
| `QUESTION_ID` | NUMBER | 질문 ID (FK) |
| `ANSWER_ID` | NUMBER | 선택지 ID (FK) |
| `ANSWER_VALUE` | VARCHAR2(200) | 선택한 값 |
| `RESPONSE_TEXT` | CLOB | 텍스트 입력 값 |
| `STEP_NUMBER` | NUMBER | 단계 번호 |

---

## 통계 및 분석 용도

온보딩 특성을 활용한 분석 예시:

1. **가구 구성별 선호 분위기**
   - 1인 가구는 주로 어떤 분위기를 선호하는가?
   
2. **주거 형태별 주요 공간**
   - 아파트 vs 원룸의 주요 공간 분포

3. **라이프스타일별 우선순위**
   - 요리를 자주 하는 사용자의 구매 우선순위

4. **예산별 카테고리 선택**
   - 예산 범위에 따른 제품 카테고리 선호도

---

**마지막 업데이트**: 2024년 12월


