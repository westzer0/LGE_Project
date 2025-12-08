# DB 구조와 백엔드 로직 비교 분석

## 개요
Oracle DB의 테이블 Comments를 기반으로 DB 구조를 확인하고, 백엔드 로직에 반영 여부를 점검한 결과입니다.

---

## 1. 주요 테이블 목록 및 백엔드 반영 현황

### ✅ 완전히 반영된 테이블

#### 1.1 PRODUCT (제품 정보)
- **DB Comment**: "LG 가전 제품 정보 테이블"
- **주요 컬럼**: PRODUCT_ID, MODEL_CODE, PRODUCT_NAME, MAIN_CATEGORY, CATEGORY, PRICE, DISCOUNT_PRICE, IMAGE_URL, STATUS
- **백엔드 반영**: ✅ `api/models.py`의 `Product` 모델로 반영
- **사용 위치**: 
  - `api/views.py`: 제품 조회, 검색, 상세 정보
  - `api/services/recommendation_engine.py`: 추천 엔진에서 제품 조회
  - `api/services/product_comparison_service.py`: 제품 비교

#### 1.2 PRODUCT_SPEC (제품 스펙)
- **DB Comment**: "제품 스펙 정보 테이블 (EAV 패턴)"
- **주요 컬럼**: PRODUCT_ID, SPEC_KEY, SPEC_VALUE, SPEC_TYPE
- **백엔드 반영**: ✅ `api/models.py`의 `ProductSpec` 모델로 반영
- **사용 위치**: 
  - `api/views.py`: 제품 상세 정보 조회 시 스펙 표시

#### 1.3 ONBOARDING_SESSION (온보딩 세션)
- **DB Comment**: "온보딩 세션 정보 테이블 (사용자 설문 응답 저장)"
- **주요 컬럼**: SESSION_ID, USER_ID, CURRENT_STEP, STATUS, VIBE, HOUSEHOLD_SIZE, HAS_PET, HOUSING_TYPE, PYUNG, MAIN_SPACE, COOKING, LAUNDRY, MEDIA, PRIORITY, PRIORITY_LIST, BUDGET_LEVEL, SELECTED_CATEGORIES, RECOMMENDED_PRODUCTS, RECOMMENDATION_RESULT
- **백엔드 반영**: ✅ `api/models.py`의 `OnboardingSession` 모델로 반영
- **사용 위치**: 
  - `api/views.py`: 온보딩 세션 생성/조회/업데이트
  - `api/services/onboarding_db_service.py`: Oracle DB 직접 조작

#### 1.4 TASTE_CONFIG (Taste 설정)
- **DB Comment**: "Taste별 추천 설정 관리 테이블 (1-120개의 Taste ID별 설정)"
- **주요 컬럼**: TASTE_ID, DESCRIPTION, REPRESENTATIVE_VIBE, REPRESENTATIVE_HOUSEHOLD_SIZE, REPRESENTATIVE_MAIN_SPACE, REPRESENTATIVE_HAS_PET, REPRESENTATIVE_PRIORITY, REPRESENTATIVE_BUDGET_LEVEL, RECOMMENDED_CATEGORIES, CATEGORY_SCORES, RECOMMENDED_PRODUCTS, RECOMMENDED_PRODUCT_SCORES, ILL_SUITED_CATEGORIES, IS_ACTIVE, AUTO_GENERATED, LAST_SIMULATION_DATE
- **백엔드 반영**: ✅ `api/models.py`의 `TasteConfig` 모델로 반영
- **사용 위치**: 
  - `api/utils/taste_category_selector.py`: Taste별 카테고리 선택
  - `api/services/taste_based_product_scorer.py`: Taste 기반 제품 점수 계산

#### 1.5 MEMBER (회원 정보)
- **DB Comment**: "회원 정보 테이블"
- **주요 컬럼**: MEMBER_ID, USER_ID, TASTE, CREATED_AT, UPDATED_AT
- **백엔드 반영**: ✅ Oracle DB 직접 조회
- **사용 위치**: 
  - `api/views.py`: 회원 수 조회 (line 185)
  - `api/services/taste_calculation_service.py`: Taste 계산 및 저장 (line 46-51, 154-155)
  - `api/utils/answer_category_mapper.py`: Member 테이블 조인 (line 95, 99)

#### 1.6 WISHLIST (위시리스트)
- **DB Comment**: "위시리스트 테이블 (찜하기 기능)"
- **주요 컬럼**: WISHLIST_ID, USER_ID, PRODUCT_ID, CREATED_AT
- **백엔드 반영**: ✅ `api/models.py`의 `Wishlist` 모델로 반영
- **사용 위치**: 
  - `api/views.py`: 찜하기 추가/제거/목록 조회 (line 3069-3199)

---

### ⚠️ 부분적으로 반영된 테이블 (정규화 테이블)

#### 2.1 ONBOARDING_SESSION 정규화 테이블들
**DB 테이블**:
- `ONBOARDING_SESSION_MAIN_SPACES` (또는 `ONBOARD_SESS_MAIN_SPACES`)
- `ONBOARDING_SESSION_PRIORITIES` (또는 `ONBOARD_SESS_PRIORITIES`)
- `ONBOARDING_SESSION_CATEGORIES` (또는 `ONBOARD_SESS_CATEGORIES`)
- `ONBOARDING_SESSION_RECOMMENDED_PRODUCTS` (또는 `ONBOARD_SESS_REC_PRODUCTS`)

**DB Comment**: 
- "온보딩 세션별 주요 공간 정보 (정규화)"
- "온보딩 세션별 우선순위 목록 (정규화)"
- "온보딩 세션별 선택한 카테고리 (정규화)"
- "온보딩 세션별 추천 제품 (정규화)"

**백엔드 반영**: ⚠️ **부분 반영**
- ✅ `api/services/onboarding_db_service.py`에서 Oracle DB 직접 조작 (line 119-146, 211-232, 428-455)
- ❌ Django ORM 모델 없음 (정규화 테이블용 모델이 없음)
- ⚠️ **테이블명 불일치**: 
  - SQL 파일: `ONBOARDING_SESSION_MAIN_SPACES` (30자 초과)
  - 실제 사용: `ONBOARD_SESS_MAIN_SPACES` (23자, Oracle 11g 30자 제한 고려)

**권장사항**: 
- 정규화 테이블용 Django 모델 추가 고려
- 테이블명 일관성 확인 필요

#### 2.2 PRODUCT_DEMOGRAPHICS 정규화 테이블들
**DB 테이블**:
- `PRODUCT_DEMOGRAPHICS_FAMILY_TYPES` (또는 `PROD_DEMO_FAMILY_TYPES`)
- `PRODUCT_DEMOGRAPHICS_HOUSE_SIZES` (또는 `PROD_DEMO_HOUSE_SIZES`)
- `PRODUCT_DEMOGRAPHICS_HOUSE_TYPES` (또는 `PROD_DEMO_HOUSE_TYPES`)

**DB Comment**: 
- "제품별 가족 구성 정보 (정규화)"
- "제품별 집 크기 정보 (정규화)"
- "제품별 주거 형태 정보 (정규화)"

**백엔드 반영**: ⚠️ **부분 반영**
- ✅ `api/models.py`의 `ProductDemographics` 모델에서 정규화 테이블 읽기 메서드 제공 (line 98-142)
- ✅ `api/models.py`의 `save_to_normalized()` 메서드로 정규화 테이블 저장 (line 144-181)
- ❌ Django ORM 모델 없음 (정규화 테이블용 모델이 없음)
- ⚠️ **테이블명 불일치**: 
  - SQL 파일: `PRODUCT_DEMOGRAPHICS_FAMILY_TYPES` (30자 초과)
  - 실제 사용: `PROD_DEMO_FAMILY_TYPES` (23자)

**권장사항**: 
- 정규화 테이블용 Django 모델 추가 고려
- 테이블명 일관성 확인 필요

#### 2.3 TASTE_CONFIG 정규화 테이블들
**DB 테이블**:
- `TASTE_CATEGORY_SCORES`
- `TASTE_RECOMMENDED_PRODUCTS`

**DB Comment**: 
- "Taste별 카테고리 점수 관리 테이블 (정규화)"
- "Taste별 추천 제품 관리 테이블 (정규화)"

**백엔드 반영**: ⚠️ **부분 반영**
- ✅ `api/services/taste_based_product_scorer.py`에서 Oracle DB 직접 조회 (line 181-188)
- ✅ `api/management/commands/migrate_taste_config_to_normalized.py`: 마이그레이션 스크립트
- ✅ `api/management/commands/populate_taste_config.py`: 데이터 저장 스크립트
- ❌ Django ORM 모델 없음

**권장사항**: 
- 정규화 테이블용 Django 모델 추가 고려

---

### ❌ 백엔드에서 사용되지 않는 테이블 (확인 필요)

#### 3.1 ONBOARDING_QUESTION (온보딩 질문)
- **DB Comment**: "온보딩 질문 항목 테이블"
- **주요 컬럼**: QUESTION_ID, STEP_NUMBER, QUESTION_TYPE, QUESTION_TEXT, QUESTION_ORDER, IS_REQUIRED, CONDITION_TYPE, CONDITION_VALUE
- **백엔드 반영**: ❌ **사용 안 함**
- **사용 위치**: 
  - `api/services/onboarding_db_service.py`에서 조회만 함 (line 258-274, 351-365)
  - 실제 온보딩 질문은 프론트엔드에서 하드코딩되어 있음

**권장사항**: 
- 온보딩 질문을 DB에서 관리하도록 백엔드 로직 추가 고려

#### 3.2 ONBOARDING_ANSWER (온보딩 선택지)
- **DB Comment**: "온보딩 선택지 항목 테이블"
- **주요 컬럼**: ANSWER_ID, QUESTION_ID, ANSWER_VALUE, ANSWER_TEXT, ANSWER_ORDER, IMAGE_URL, IS_ACTIVE
- **백엔드 반영**: ❌ **사용 안 함**
- **사용 위치**: 
  - `api/services/onboarding_db_service.py`에서 조회만 함 (line 274-286, 376-387)

**권장사항**: 
- 온보딩 선택지를 DB에서 관리하도록 백엔드 로직 추가 고려

#### 3.3 ONBOARDING_USER_RESPONSE (온보딩 사용자 응답)
- **DB Comment**: "온보딩 사용자 선택지 결과 항목 테이블"
- **주요 컬럼**: RESPONSE_ID, SESSION_ID, QUESTION_ID, ANSWER_ID, ANSWER_VALUE, RESPONSE_TEXT, STEP_NUMBER
- **백엔드 반영**: ⚠️ **부분 사용**
- **사용 위치**: 
  - `api/services/onboarding_db_service.py`에서 저장/조회 (line 287-315, 481-494)
  - 하지만 실제 온보딩 플로우에서는 `ONBOARDING_SESSION` 테이블만 사용

**권장사항**: 
- `ONBOARDING_USER_RESPONSE` 테이블 활용도 향상 또는 제거 고려

#### 3.4 USER_SAMPLE (사용자 샘플)
- **DB Comment**: 확인 필요 (SQL 파일에 없음)
- **백엔드 반영**: ✅ `api/models.py`의 `UserSample` 모델로 반영 (line 227-257)
- **사용 위치**: 
  - 모델만 정의되어 있고 실제 사용되는 곳이 없음

**권장사항**: 
- `USER_SAMPLE` 테이블의 실제 용도 확인 필요

#### 3.5 USER_SAMPLE 정규화 테이블들
**DB 테이블** (normalize_user_sample.sql 참고):
- `USER_SAMPLE_RECOMMENDATIONS`
- `USER_SAMPLE_PURCHASED_ITEMS`

**DB Comment**: 
- "사용자 샘플별 추천 제품 정보 (정규화)"
- "사용자 샘플별 구매한 제품 (정규화)"

**백엔드 반영**: ❌ **사용 안 함**

**권장사항**: 
- 사용 목적 확인 후 제거 또는 활용 방안 수립

#### 3.6 PRODUCT_REVIEW_DEMOGRAPHICS (CSV 데이터)
- **DB Comment**: "제품별 리뷰 인구통계 정보"
- **주요 컬럼**: ID, PRODUCT_CATEGORY, PRODUCT_CODE, FAMILY_LIST, SIZE_LIST, HOUSE_LIST
- **백엔드 반영**: ❌ **사용 안 함**

**권장사항**: 
- CSV 데이터 임포트용 테이블로 보이므로, 실제 사용 여부 확인 필요

#### 3.7 PRODUCT_RECOMMEND_REASONS (CSV 데이터)
- **DB Comment**: "제품별 추천 이유 (평균벡터 데이터)"
- **주요 컬럼**: ID, PRODUCT_CATEGORY, MODEL_NAME, RECOMMEND_REASON
- **백엔드 반영**: ❌ **사용 안 함**

**권장사항**: 
- CSV 데이터 임포트용 테이블로 보이므로, 실제 사용 여부 확인 필요

---

## 2. 누락된 기능 및 개선 사항

### 2.1 정규화 테이블용 Django 모델 부재
**문제**: 정규화된 테이블들(`ONBOARD_SESS_*`, `PROD_DEMO_*`, `TASTE_CATEGORY_SCORES`, `TASTE_RECOMMENDED_PRODUCTS`)에 대한 Django ORM 모델이 없어서 Oracle DB 직접 조회만 사용 중

**영향**: 
- 코드 중복 (SQL 쿼리 반복)
- 타입 안정성 부족
- 테스트 어려움

**권장사항**: 
- 정규화 테이블용 Django 모델 추가
- 또는 Django ORM의 `Meta.db_table` 옵션으로 기존 테이블 매핑

### 2.2 테이블명 불일치
**문제**: SQL 파일과 실제 사용되는 테이블명이 다름
- SQL: `ONBOARDING_SESSION_MAIN_SPACES` (30자 초과)
- 실제: `ONBOARD_SESS_MAIN_SPACES` (23자)

**권장사항**: 
- SQL 파일 수정 또는 문서화
- 테이블명 일관성 유지

### 2.3 ONBOARDING_QUESTION/ANSWER 미활용
**문제**: DB에 온보딩 질문/선택지가 정의되어 있지만 실제로는 프론트엔드에서 하드코딩

**권장사항**: 
- 온보딩 질문/선택지를 DB에서 관리하도록 API 추가
- 프론트엔드에서 동적으로 질문 로드

### 2.4 USER_SAMPLE 테이블 미사용
**문제**: 모델은 정의되어 있지만 실제 사용되는 곳이 없음

**권장사항**: 
- 사용 목적 확인 후 제거 또는 활용

---

## 3. 체크리스트

### ✅ 완료된 항목
- [x] PRODUCT 테이블 - 완전 반영
- [x] PRODUCT_SPEC 테이블 - 완전 반영
- [x] ONBOARDING_SESSION 테이블 - 완전 반영
- [x] TASTE_CONFIG 테이블 - 완전 반영
- [x] MEMBER 테이블 - 완전 반영
- [x] WISHLIST 테이블 - 완전 반영

### ⚠️ 부분 완료된 항목
- [ ] ONBOARDING_SESSION 정규화 테이블 - Oracle DB 직접 조회만 사용, Django 모델 없음
- [ ] PRODUCT_DEMOGRAPHICS 정규화 테이블 - 메서드로 읽기/쓰기 제공, Django 모델 없음
- [ ] TASTE_CONFIG 정규화 테이블 - Oracle DB 직접 조회만 사용, Django 모델 없음

### ❌ 미완료된 항목
- [ ] ONBOARDING_QUESTION 테이블 - DB에 있지만 백엔드에서 미사용
- [ ] ONBOARDING_ANSWER 테이블 - DB에 있지만 백엔드에서 미사용
- [ ] ONBOARDING_USER_RESPONSE 테이블 - 부분 사용 (저장/조회만, 실제 플로우 미사용)
- [ ] USER_SAMPLE 테이블 - 모델만 있고 실제 사용 안 함
- [ ] USER_SAMPLE 정규화 테이블 - 사용 안 함
- [ ] PRODUCT_REVIEW_DEMOGRAPHICS 테이블 - 사용 안 함
- [ ] PRODUCT_RECOMMEND_REASONS 테이블 - 사용 안 함

---

## 4. 권장 조치 사항

### 우선순위 높음
1. **정규화 테이블용 Django 모델 추가**
   - `ONBOARD_SESS_*` 테이블용 모델
   - `PROD_DEMO_*` 테이블용 모델
   - `TASTE_CATEGORY_SCORES`, `TASTE_RECOMMENDED_PRODUCTS` 테이블용 모델

2. **테이블명 일관성 확인**
   - SQL 파일과 실제 사용 테이블명 일치시키기
   - 또는 문서화

### 우선순위 중간
3. **ONBOARDING_QUESTION/ANSWER 활용**
   - 온보딩 질문/선택지를 DB에서 관리하도록 API 추가
   - 프론트엔드에서 동적 로드

4. **ONBOARDING_USER_RESPONSE 활용도 향상**
   - 실제 온보딩 플로우에서 활용하거나 제거

### 우선순위 낮음
5. **USER_SAMPLE 테이블 정리**
   - 사용 목적 확인 후 제거 또는 활용

6. **CSV 데이터 테이블 정리**
   - `PRODUCT_REVIEW_DEMOGRAPHICS`, `PRODUCT_RECOMMEND_REASONS` 사용 여부 확인

---

## 5. 참고 파일

- `api/db/add_column_comments.sql`: 모든 테이블의 Comments 정의
- `api/db/onboarding_tables_ddl.sql`: 온보딩 관련 테이블 DDL
- `api/db/normalize_onboarding_session.sql`: 온보딩 세션 정규화 테이블
- `api/db/normalize_product_demographics.sql`: 제품 인구통계 정규화 테이블
- `api/db/normalize_taste_config.sql`: Taste 설정 정규화 테이블
- `api/db/create_wishlist_table.sql`: 위시리스트 테이블 DDL
- `api/models.py`: Django ORM 모델 정의
- `api/services/onboarding_db_service.py`: 온보딩 DB 서비스 (Oracle 직접 조회)
- `api/services/taste_calculation_service.py`: Taste 계산 서비스 (MEMBER 테이블 사용)
