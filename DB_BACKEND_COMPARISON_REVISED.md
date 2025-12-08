# DB 구조와 백엔드 로직 비교 분석 (수정본)

## 개요
Oracle DB의 테이블 Comments를 기반으로 DB 구조를 확인하고, 백엔드 로직에 반영 여부를 재점검한 결과입니다.

---

## 1. 주요 테이블 목록 및 백엔드 반영 현황

### ✅ 완전히 반영된 테이블

#### 1.1 PRODUCT (제품 정보)
- **DB Comment**: "LG 가전 제품 정보 테이블"
- **백엔드 반영**: ✅ `api/models.py`의 `Product` 모델로 반영
- **사용 위치**: `api/views.py`, `api/services/recommendation_engine.py`

#### 1.2 PRODUCT_SPEC (제품 스펙)
- **DB Comment**: "제품 스펙 정보 테이블 (EAV 패턴)"
- **백엔드 반영**: ✅ `api/models.py`의 `ProductSpec` 모델로 반영
- **사용 위치**: `api/views.py` (제품 상세 정보 조회)

#### 1.3 ONBOARDING_SESSION (온보딩 세션)
- **DB Comment**: "온보딩 세션 정보 테이블 (사용자 설문 응답 저장)"
- **백엔드 반영**: ✅ `api/models.py`의 `OnboardingSession` 모델로 반영
- **사용 위치**: `api/views.py`, `api/services/onboarding_db_service.py`

#### 1.4 TASTE_CONFIG (Taste 설정)
- **DB Comment**: "Taste별 추천 설정 관리 테이블 (1-120개의 Taste ID별 설정)"
- **백엔드 반영**: ✅ `api/models.py`의 `TasteConfig` 모델로 반영
- **사용 위치**: `api/utils/taste_category_selector.py`, `api/services/taste_based_product_scorer.py`

#### 1.5 MEMBER (회원 정보)
- **DB Comment**: "회원 정보 테이블"
- **백엔드 반영**: ✅ Oracle DB 직접 조회
- **사용 위치**: `api/views.py`, `api/services/taste_calculation_service.py`

#### 1.6 WISHLIST (위시리스트)
- **DB Comment**: "위시리스트 테이블 (찜하기 기능)"
- **백엔드 반영**: ✅ `api/models.py`의 `Wishlist` 모델로 반영
- **사용 위치**: `api/views.py` (line 3069-3199)

---

### ✅ 실제로 사용 중인 테이블 (이전 분석 오류 수정)

#### 2.1 ONBOARDING_QUESTION (온보딩 질문)
- **DB Comment**: "온보딩 질문 항목 테이블"
- **백엔드 반영**: ✅ **실제로 사용 중**
- **사용 위치**: 
  - `api/services/onboarding_db_service.py`: `save_user_response()`, `save_multiple_responses()` 메서드에서 QUESTION_ID 조회 (line 258-269, 351-361)
  - `api/views.py`: 온보딩 단계별 응답 저장 시 호출 (line 954-1063)
- **사용 방식**: 
  - 각 온보딩 단계에서 사용자 응답을 저장할 때 `question_type`과 `step_number`로 QUESTION_ID를 조회
  - QUESTION_ID를 `ONBOARDING_USER_RESPONSE` 테이블에 저장

**이전 분석 오류**: "DB에 있지만 실제로는 프론트엔드 하드코딩 사용"이라고 했지만, 실제로는 백엔드에서 질문 ID를 조회하는 데 사용되고 있음.

#### 2.2 ONBOARDING_ANSWER (온보딩 선택지)
- **DB Comment**: "온보딩 선택지 항목 테이블"
- **백엔드 반영**: ✅ **실제로 사용 중**
- **사용 위치**: 
  - `api/services/onboarding_db_service.py`: `save_user_response()`, `save_multiple_responses()` 메서드에서 ANSWER_ID 조회 (line 273-283, 375-384)
  - `api/views.py`: 온보딩 단계별 응답 저장 시 호출 (line 954-1063)
- **사용 방식**: 
  - 사용자가 선택한 `answer_value`로 ANSWER_ID를 조회
  - ANSWER_ID를 `ONBOARDING_USER_RESPONSE` 테이블에 저장

**이전 분석 오류**: "DB에 있지만 실제로는 프론트엔드 하드코딩 사용"이라고 했지만, 실제로는 백엔드에서 선택지 ID를 조회하는 데 사용되고 있음.

#### 2.3 ONBOARDING_USER_RESPONSE (온보딩 사용자 응답)
- **DB Comment**: "온보딩 사용자 선택지 결과 항목 테이블"
- **백엔드 반영**: ✅ **실제로 사용 중**
- **사용 위치**: 
  - `api/services/onboarding_db_service.py`: 
    - `save_user_response()`: 단일 응답 저장 (line 240-333)
    - `save_multiple_responses()`: 다중 선택 응답 저장 (line 336-404)
    - `get_user_responses()`: 응답 조회 (line 475-500)
  - `api/views.py`: 온보딩 단계별 응답 저장 시 호출 (line 954-1063)
- **사용 방식**: 
  - 각 온보딩 단계에서 사용자 응답을 저장
  - QUESTION_ID, ANSWER_ID, ANSWER_VALUE, RESPONSE_TEXT 등을 저장
  - 나중에 조회하여 사용자 응답 이력 확인 가능

**이전 분석 오류**: "저장/조회만 하고 실제 플로우 미사용"이라고 했지만, 실제로는 온보딩 플로우에서 매 단계마다 저장되고 있음.

---

### ⚠️ 부분적으로 반영된 테이블 (정규화 테이블)

#### 3.1 ONBOARDING_SESSION 정규화 테이블들
- `ONBOARD_SESS_MAIN_SPACES`, `ONBOARD_SESS_PRIORITIES`, `ONBOARD_SESS_CATEGORIES`, `ONBOARD_SESS_REC_PRODUCTS`
- **백엔드 반영**: ⚠️ Oracle DB 직접 조회만 사용, Django ORM 모델 없음
- **사용 위치**: `api/services/onboarding_db_service.py`

#### 3.2 PRODUCT_DEMOGRAPHICS 정규화 테이블들
- `PROD_DEMO_FAMILY_TYPES`, `PROD_DEMO_HOUSE_SIZES`, `PROD_DEMO_HOUSE_TYPES`
- **백엔드 반영**: ⚠️ 메서드로 읽기/쓰기 제공, Django ORM 모델 없음
- **사용 위치**: `api/models.py`의 `ProductDemographics` 모델

#### 3.3 TASTE_CONFIG 정규화 테이블들
- `TASTE_CATEGORY_SCORES`, `TASTE_RECOMMENDED_PRODUCTS`
- **백엔드 반영**: ⚠️ Oracle DB 직접 조회만 사용, Django ORM 모델 없음
- **사용 위치**: `api/services/taste_based_product_scorer.py`

---

### ❌ 백엔드에서 실제로 사용되지 않는 테이블 (확인 필요)

#### 4.1 USER_SAMPLE (사용자 샘플)
- **DB Comment**: 확인 필요 (SQL 파일에 없음)
- **백엔드 반영**: ⚠️ **모델만 있고 실제 사용 안 함**
- **현재 상태**: 
  - `api/models.py`에 `UserSample` 모델 정의됨 (line 227-257)
  - `api/management/commands/import_user_samples.py`에서 CSV 임포트 기능 있음
  - `api/admin.py`에 Admin 등록됨
  - 하지만 `api/views.py`나 다른 서비스에서 실제로 조회/사용하는 코드 없음
- **권장사항**: 
  - 추천 엔진이나 사용자 분석에서 활용해야 할 것 같음
  - 사용 목적 확인 후 활용 방안 수립 필요

#### 4.2 USER_SAMPLE 정규화 테이블들
- `USER_SAMPLE_RECOMMENDATIONS`, `USER_SAMPLE_PURCHASED_ITEMS`
- **백엔드 반영**: ❌ **사용 안 함**
- **현재 상태**: 
  - `api/db/normalize_user_sample.sql`에 테이블 정의 있음
  - `api/management/commands/migrate_all_to_normalized.py`에 마이그레이션 스크립트 있음
  - 하지만 실제로 조회/사용하는 코드 없음
- **권장사항**: 
  - USER_SAMPLE 테이블과 함께 활용 방안 수립 필요

#### 4.3 PRODUCT_REVIEW_DEMOGRAPHICS (CSV 데이터)
- **DB Comment**: "제품별 리뷰 인구통계 정보"
- **백엔드 반영**: ❌ **사용 안 함**
- **현재 상태**: 
  - `api/db/csv_data_tables_ddl.sql`에 테이블 정의 있음
  - CSV 임포트용으로 보이지만 실제로 조회하는 코드 없음
- **권장사항**: 
  - 제품 상세 페이지에서 "이 제품을 구매한 사람들의 특성" 표시 시 활용해야 할 것 같음
  - 제품 추천 시 인구통계 정보 활용 고려

#### 4.4 PRODUCT_RECOMMEND_REASONS (CSV 데이터)
- **DB Comment**: "제품별 추천 이유 (평균벡터 데이터)"
- **백엔드 반영**: ❌ **사용 안 함**
- **현재 상태**: 
  - `api/db/csv_data_tables_ddl.sql`에 테이블 정의 있음
  - CSV 임포트용으로 보이지만 실제로 조회하는 코드 없음
- **권장사항**: 
  - 제품 추천 결과에 "추천 이유" 표시 시 활용해야 할 것 같음
  - 현재는 `ProductRecommendReason` 모델을 사용하는 것으로 보이지만, 이 테이블도 활용 고려

---

## 2. 수정된 분석 결과

### 이전 분석의 오류

1. **ONBOARDING_QUESTION/ANSWER**: "미사용"으로 잘못 분석
   - ✅ 실제로는 `onboarding_db_service`에서 QUESTION_ID/ANSWER_ID 조회에 사용 중
   - ✅ `api/views.py`의 온보딩 단계별 응답 저장 시 호출됨

2. **ONBOARDING_USER_RESPONSE**: "부분 사용"으로 분석했지만 실제로는 완전히 사용 중
   - ✅ 온보딩 플로우에서 매 단계마다 저장됨
   - ✅ `save_user_response()`, `save_multiple_responses()`, `get_user_responses()` 메서드로 완전히 활용됨

### 실제 미사용 테이블

1. **USER_SAMPLE**: 모델만 있고 실제 조회/사용 안 함
2. **USER_SAMPLE 정규화 테이블**: 사용 안 함
3. **PRODUCT_REVIEW_DEMOGRAPHICS**: 사용 안 함
4. **PRODUCT_RECOMMEND_REASONS**: 사용 안 함

---

## 3. 개선 권장 사항

### 우선순위 높음

1. **USER_SAMPLE 테이블 활용**
   - 추천 엔진에서 유사 사용자 찾기
   - 사용자 분석 및 통계
   - A/B 테스트 데이터

2. **PRODUCT_REVIEW_DEMOGRAPHICS 활용**
   - 제품 상세 페이지에 "이 제품을 구매한 사람들의 특성" 표시
   - 제품 추천 시 인구통계 정보 활용

3. **PRODUCT_RECOMMEND_REASONS 활용**
   - 제품 추천 결과에 "추천 이유" 표시
   - 현재 `ProductRecommendReason` 모델과 통합 또는 대체

### 우선순위 중간

4. **정규화 테이블용 Django 모델 추가**
   - 코드 중복 감소
   - 타입 안정성 향상
   - 테스트 용이성 향상

---

## 4. 체크리스트 (수정본)

### ✅ 완전히 반영된 항목
- [x] PRODUCT 테이블
- [x] PRODUCT_SPEC 테이블
- [x] ONBOARDING_SESSION 테이블
- [x] TASTE_CONFIG 테이블
- [x] MEMBER 테이블
- [x] WISHLIST 테이블
- [x] ONBOARDING_QUESTION 테이블 (수정: 실제로 사용 중)
- [x] ONBOARDING_ANSWER 테이블 (수정: 실제로 사용 중)
- [x] ONBOARDING_USER_RESPONSE 테이블 (수정: 실제로 사용 중)

### ⚠️ 부분 완료된 항목
- [ ] ONBOARDING_SESSION 정규화 테이블 - Oracle DB 직접 조회만 사용, Django 모델 없음
- [ ] PRODUCT_DEMOGRAPHICS 정규화 테이블 - 메서드로 읽기/쓰기 제공, Django 모델 없음
- [ ] TASTE_CONFIG 정규화 테이블 - Oracle DB 직접 조회만 사용, Django 모델 없음

### ❌ 실제 미사용 항목
- [ ] USER_SAMPLE 테이블 - 모델만 있고 실제 조회/사용 안 함
- [ ] USER_SAMPLE 정규화 테이블 - 사용 안 함
- [ ] PRODUCT_REVIEW_DEMOGRAPHICS 테이블 - 사용 안 함
- [ ] PRODUCT_RECOMMEND_REASONS 테이블 - 사용 안 함

---

## 5. 참고 파일

- `api/services/onboarding_db_service.py`: 온보딩 DB 서비스 (ONBOARDING_QUESTION/ANSWER/USER_RESPONSE 사용)
- `api/views.py` (line 954-1063): 온보딩 단계별 응답 저장 (ONBOARDING_USER_RESPONSE 저장)
- `api/models.py`: Django ORM 모델 정의
- `api/db/csv_data_tables_ddl.sql`: CSV 데이터 테이블 DDL (PRODUCT_REVIEW_DEMOGRAPHICS, PRODUCT_RECOMMEND_REASONS)
