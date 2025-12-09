# Step 2: 온보딩 데이터 조회 로직 검증 - 프롬프트

## 📋 현재 상황

Step 1 (기본 인프라 검증)이 완료되었습니다:
- ✅ Oracle DB 연결 확인
- ✅ 모든 필수 테이블 존재 확인 (ONBOARDING_SESSION, ONBOARD_SESS_MAIN_SPACES, ONBOARD_SESS_PRIORITIES, MEMBER)
- ✅ 모든 필수 컬럼 존재 확인
- ✅ MEMBER.TASTE 컬럼 존재 및 제약조건 확인 (1~120 범위)
- ✅ 정규화 테이블 생성 완료

## 🎯 Step 2 목표

**온보딩 데이터 조회 로직 검증**

`TasteCalculationService._get_onboarding_data_from_session()` 메서드가 올바르게 작동하는지 검증합니다.

### 검증해야 할 항목

1. ✅ `ONBOARDING_SESSION` 테이블에서 기본 데이터 읽기 성공
2. ✅ `ONBOARD_SESS_MAIN_SPACES` 테이블에서 MAIN_SPACE 배열 읽기 성공
3. ✅ `ONBOARD_SESS_PRIORITIES` 테이블에서 PRIORITY 배열 읽기 성공
4. ✅ 데이터 형식 변환 정확성 확인
5. ✅ NULL 값 처리 확인
6. ✅ 빈 배열 처리 확인

## 📁 관련 파일 위치

- **서비스 파일**: `api/services/taste_calculation_service.py`
  - 메서드: `TasteCalculationService._get_onboarding_data_from_session()`
  - 라인: 약 58~130

- **DB 클라이언트**: `api/db/oracle_client.py`
  - `get_connection()` 함수 사용

## 🔍 검증 방법

### 1. 테스트 스크립트 작성

`test_taste_data_retrieval.py` 파일을 생성하여 다음을 테스트:

```python
# 테스트 케이스:
# 1. 실제 존재하는 SESSION_ID로 데이터 조회
# 2. ONBOARDING_SESSION의 모든 필수 컬럼 확인
# 3. 정규화 테이블에서 MAIN_SPACE 배열 읽기
# 4. 정규화 테이블에서 PRIORITY 배열 읽기
# 5. 데이터 형식 변환 확인 (예: HAS_PET 'Y' → True)
# 6. NULL 값 처리 확인
# 7. 빈 배열 처리 확인
```

### 2. 실제 데이터 사용

- 실제 DB에 존재하는 `SESSION_ID` 사용 (Step 1에서 확인: 1,056개 세션 존재)
- 또는 테스트용 온보딩 세션 생성 후 테스트

### 3. 검증 항목

각 검증 항목에 대해:
- ✅ 성공 케이스 확인
- ❌ 실패 케이스 확인 (에러 처리)
- 📊 데이터 형식 확인 (타입, 값 변환)

## 📝 예상 출력 형식

```python
# 반환되는 onboarding_data 형식:
{
    'vibe': 'modern',              # 문자열
    'household_size': 4,            # 정수
    'housing_type': 'apartment',    # 문자열
    'pyung': 30,                    # 정수
    'budget_level': 'medium',       # 문자열
    'priority': ['tech', 'design'], # 배열 (정규화 테이블에서)
    'main_space': ['living', 'kitchen'], # 배열 (정규화 테이블에서)
    'has_pet': False,               # 불린 (HAS_PET 'Y' → True)
    'cooking': 'frequently',        # 문자열
    'laundry': 'weekly',            # 문자열
    'media': 'balanced'             # 문자열
}
```

## 🚀 실행 방법

1. 테스트 스크립트 작성
2. 실제 SESSION_ID로 테스트 실행
3. 결과 확인 및 검증
4. 문제 발견 시 수정 후 재테스트

## ✅ 완료 기준

- [ ] 모든 테이블에서 데이터 정상 조회
- [ ] 데이터 형식 변환 정확
- [ ] NULL 값 처리 확인
- [ ] 빈 배열 처리 확인
- [ ] 예외 케이스 처리 확인 (존재하지 않는 SESSION_ID 등)

## 📌 참고사항

- Step 1에서 확인한 실제 데이터:
  - ONBOARDING_SESSION 레코드: 1,056개
  - 샘플 SESSION_ID: `1764840383702`, `1764840384247`, `1764840384743`
- 정규화 테이블이 비어있을 수 있으므로, 테스트용 데이터를 생성해야 할 수도 있습니다.

---

**작업 시작**: `test_taste_data_retrieval.py` 파일을 생성하고 위 검증 항목들을 테스트하는 코드를 작성하세요.

