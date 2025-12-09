# Taste 계산 및 할당 통합 계획

## 📋 개요

온보딩 데이터를 기반으로 사용자의 Taste ID(1~120)를 계산하고, 회원인 경우 MEMBER 테이블에 저장하는 기능을 구현합니다.

---

## 🗄️ 관련 테이블

### 1. **읽기 테이블 (Input) - 온보딩 데이터 조회**

#### 1.1 `ONBOARDING_SESSION` (메인 테이블)
```sql
-- 온보딩 세션 기본 정보
SELECT 
    SESSION_ID,
    MEMBER_ID,           -- 회원 ID (GUEST 또는 실제 회원 ID)
    VIBE,                -- Step 1: 분위기
    HOUSEHOLD_SIZE,       -- Step 2: 가구 인원수
    HOUSING_TYPE,         -- Step 3: 주거 형태
    PYUNG,                -- Step 3: 평수
    BUDGET_LEVEL,         -- Step 6: 예산 범위
    PRIORITY,             -- Step 5: 우선순위 (첫 번째)
    HAS_PET,              -- Step 2: 반려동물 여부 (Y/N)
    COOKING,              -- Step 4: 요리 빈도
    LAUNDRY,              -- Step 4: 세탁 빈도
    MEDIA,                -- Step 4: 미디어 사용 패턴
    STATUS                -- 상태 (IN_PROGRESS, COMPLETED, ABANDONED)
FROM ONBOARDING_SESSION
WHERE SESSION_ID = :session_id
```

#### 1.2 `ONBOARD_SESS_MAIN_SPACES` (정규화 테이블)
```sql
-- Step 3: 주요 공간 (다중 선택)
SELECT MAIN_SPACE 
FROM ONBOARD_SESS_MAIN_SPACES
WHERE SESSION_ID = :session_id
ORDER BY MAIN_SPACE
-- 예: ['living', 'kitchen', 'bedroom']
```

#### 1.3 `ONBOARD_SESS_PRIORITIES` (정규화 테이블)
```sql
-- Step 5: 우선순위 목록 (순서 중요)
SELECT PRIORITY 
FROM ONBOARD_SESS_PRIORITIES
WHERE SESSION_ID = :session_id
ORDER BY PRIORITY_ORDER
-- 예: ['tech', 'design', 'value']
```

### 2. **쓰기 테이블 (Output) - Taste 저장**

#### 2.1 `MEMBER` (회원 테이블)
```sql
-- 회원의 Taste ID 저장
UPDATE MEMBER
SET TASTE = :taste_id  -- 1~120 범위의 정수
WHERE MEMBER_ID = :member_id
```

**조건:**
- `MEMBER_ID != 'GUEST'` 인 경우만 저장
- `TASTE` 컬럼 타입: `NUMBER(3)`
- 범위: 1 ~ 120

---

## 🔄 백엔드 로직 흐름

### **Phase 1: 온보딩 데이터 저장**
```
[API Request]
POST /api/onboarding/step/
{
    "session_id": "abc123",
    "step": 6,
    "member_id": "user123",  // 또는 null (GUEST)
    "budget_level": "medium",
    ...
}
    ↓
[OnboardingDBService.create_or_update_session()]
    ↓
1. ONBOARDING_SESSION 테이블에 저장/업데이트
2. 정규화 테이블에 저장:
   - ONBOARD_SESS_MAIN_SPACES
   - ONBOARD_SESS_PRIORITIES
   - ONBOARD_SESS_CATEGORIES
   - ONBOARD_SESS_REC_PRODUCTS
    ↓
3. 커밋 완료
    ↓
4. 조건 확인:
   - status == 'COMPLETED' ✅
   - member_id != 'GUEST' ✅
    ↓
[Phase 2로 이동]
```

### **Phase 2: Taste 계산 및 할당**
```
[TasteCalculationService.calculate_and_save_taste()]
    ↓
1. 온보딩 데이터 조회
   - ONBOARDING_SESSION 테이블에서 읽기
   - ONBOARD_SESS_MAIN_SPACES 테이블에서 읽기
   - ONBOARD_SESS_PRIORITIES 테이블에서 읽기
    ↓
2. 데이터 변환
   {
       'vibe': 'modern',
       'household_size': 4,
       'housing_type': 'apartment',
       'pyung': 30,
       'main_space': ['living', 'kitchen'],
       'priority': ['tech', 'design'],
       'budget_level': 'medium',
       'has_pet': False,
       'cooking': 'frequently',
       'laundry': 'weekly',
       'media': 'balanced'
   }
    ↓
3. Taste ID 계산
   [TasteClassifier.calculate_taste_from_onboarding()]
   - 해시 기반 분류 알고리즘
   - 1~120 범위의 정수 반환
    ↓
4. MEMBER 테이블에 저장
   UPDATE MEMBER SET TASTE = :taste_id WHERE MEMBER_ID = :member_id
    ↓
✅ 완료
```

---

## 🔧 백엔드 로직 상세

### **1. OnboardingDBService.create_or_update_session()**
**위치:** `api/services/onboarding_db_service.py`

**역할:**
- 온보딩 데이터를 Oracle DB에 저장
- 온보딩 완료 시 Taste 계산 트리거

**핵심 코드:**
```python
# 온보딩 데이터 저장 후
if status == 'COMPLETED' and final_member_id and final_member_id != 'GUEST':
    taste_id = taste_calculation_service.calculate_and_save_taste(
        member_id=final_member_id,
        onboarding_session_id=session_id
    )
```

**실행 시점:**
- `status='COMPLETED'` 일 때
- `member_id != 'GUEST'` 일 때

---

### **2. TasteCalculationService.calculate_and_save_taste()**
**위치:** `api/services/taste_calculation_service.py`

**역할:**
- 온보딩 세션에서 데이터 조회
- Taste ID 계산
- MEMBER 테이블에 저장

**핵심 코드:**
```python
# 1. 온보딩 데이터 조회
onboarding_data = TasteCalculationService._get_onboarding_data_from_session(session_id)

# 2. Taste 계산
taste_id = taste_classifier.calculate_taste_from_onboarding(onboarding_data)

# 3. 범위 검증 (1~120)
taste_id = max(1, min(120, int(taste_id)))

# 4. MEMBER 테이블에 저장
UPDATE MEMBER SET TASTE = :taste_id WHERE MEMBER_ID = :member_id
```

---

### **3. TasteCalculationService._get_onboarding_data_from_session()**
**위치:** `api/services/taste_calculation_service.py`

**역할:**
- ONBOARDING_SESSION 테이블에서 기본 데이터 읽기
- 정규화 테이블에서 배열 데이터 읽기
- 데이터 형식 변환

**읽는 테이블:**
1. `ONBOARDING_SESSION` (기본 정보)
2. `ONBOARD_SESS_MAIN_SPACES` (main_space 배열)
3. `ONBOARD_SESS_PRIORITIES` (priority 배열)

---

### **4. TasteClassifier.calculate_taste_from_onboarding()**
**위치:** `api/utils/taste_classifier.py`

**역할:**
- 온보딩 데이터를 기반으로 Taste ID 계산
- 해시 기반 분류 알고리즘 사용

**계산 로직:**
```python
# 1. 주요 속성 추출
vibe, household_size, housing_type, pyung, budget_level, priority, main_space, has_pet, cooking, laundry, media

# 2. 정규화 (범위화)
pyung_range = _normalize_pyung(pyung)  # 예: '21-30'
household_range = _normalize_household_size(household_size)  # 예: '3-4인'

# 3. Taste 키 생성
taste_key = '|'.join([vibe, household_range, housing_type, pyung_range, budget_level, priority_str, main_space_str, ...])

# 4. 해시 기반 ID 생성
taste_hash = md5(taste_key).hexdigest()
taste_id = (taste_hash % 120) + 1  # 1~120 범위
```

---

## 📊 데이터 흐름 다이어그램

```
┌─────────────────────────────────────────────────────────────┐
│                    온보딩 완료 (Step 6)                        │
│              status='COMPLETED', member_id='user123'         │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│         OnboardingDBService.create_or_update_session()       │
│                                                              │
│  1. ONBOARDING_SESSION 저장/업데이트                         │
│  2. 정규화 테이블 저장                                       │
│  3. 커밋 완료                                                │
│  4. 조건 확인: status='COMPLETED' && member_id!='GUEST'      │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│      TasteCalculationService.calculate_and_save_taste()      │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ 1. 온보딩 데이터 조회                                 │  │
│  │    - ONBOARDING_SESSION (기본 정보)                  │  │
│  │    - ONBOARD_SESS_MAIN_SPACES (main_space 배열)      │  │
│  │    - ONBOARD_SESS_PRIORITIES (priority 배열)         │  │
│  └──────────────────────────────────────────────────────┘  │
│                           │                                  │
│                           ▼                                  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ 2. 데이터 변환                                        │  │
│  │    {                                                  │  │
│  │      'vibe': 'modern',                               │  │
│  │      'household_size': 4,                            │  │
│  │      'main_space': ['living', 'kitchen'],            │  │
│  │      'priority': ['tech', 'design'],                 │  │
│  │      ...                                             │  │
│  │    }                                                  │  │
│  └──────────────────────────────────────────────────────┘  │
│                           │                                  │
│                           ▼                                  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ 3. Taste ID 계산                                      │  │
│  │    TasteClassifier.calculate_taste_from_onboarding()  │  │
│  │    → taste_id = 45 (1~120 범위)                      │  │
│  └──────────────────────────────────────────────────────┘  │
│                           │                                  │
│                           ▼                                  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ 4. MEMBER 테이블에 저장                               │  │
│  │    UPDATE MEMBER SET TASTE = 45                      │  │
│  │    WHERE MEMBER_ID = 'user123'                       │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

---

## ✅ 검증 체크리스트

### **Phase 1: 온보딩 데이터 저장 검증**
- [ ] ONBOARDING_SESSION 테이블에 데이터 저장 확인
- [ ] 정규화 테이블에 데이터 저장 확인
- [ ] status='COMPLETED' 설정 확인
- [ ] member_id 값 확인 (GUEST 또는 실제 회원 ID)

### **Phase 2: Taste 계산 검증**
- [ ] 온보딩 데이터 조회 성공 확인
- [ ] 정규화 테이블에서 데이터 읽기 확인
- [ ] Taste ID 계산 결과 확인 (1~120 범위)
- [ ] MEMBER 테이블에 TASTE 저장 확인

### **Phase 3: 엣지 케이스 검증**
- [ ] GUEST 회원인 경우 Taste 계산 건너뛰기 확인
- [ ] status != 'COMPLETED' 인 경우 Taste 계산 안 함 확인
- [ ] 온보딩 데이터가 불완전한 경우 처리 확인
- [ ] MEMBER 테이블에 회원이 없는 경우 처리 확인

---

## 🚀 다음 단계

1. **단위 테스트 작성**
   - TasteCalculationService 테스트
   - TasteClassifier 테스트
   - 데이터 조회/저장 테스트

2. **통합 테스트**
   - 온보딩 완료 → Taste 계산 전체 플로우 테스트

3. **에러 처리 강화**
   - 각 단계별 에러 처리
   - 로깅 강화

4. **성능 최적화**
   - 데이터 조회 최적화
   - 캐싱 고려

