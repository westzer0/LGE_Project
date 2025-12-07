# 전체 데이터베이스 테이블 정규화 분석

## 1. 정규화 필요성 분석

### ✅ 이미 정규화된 테이블

#### 1. PRODUCT 테이블
- **상태**: 정규화 완료
- **구조**: 기본 정보만 저장 (제품명, 가격, 카테고리 등)
- **관계**: ProductSpec과 1:1 관계로 분리

#### 2. PRODUCT_SPEC 테이블
- **상태**: 정규화 완료
- **구조**: `(PRODUCT_ID, SPEC_KEY, SPEC_VALUE, SPEC_TYPE)` 형태로 EAV 패턴 사용
- **장점**: 동적 스펙 추가 가능, 확장성 우수

#### 3. TASTE_CATEGORY_SCORES, TASTE_RECOMMENDED_PRODUCTS
- **상태**: 정규화 완료 (방금 마이그레이션 완료)
- **구조**: TASTE_CONFIG에서 분리된 정규화된 테이블

---

### ⚠️ 정규화 고려 대상 테이블

#### 1. ONBOARDING_SESSION 테이블

**현재 구조:**
```sql
CREATE TABLE ONBOARDING_SESSION (
    SESSION_ID VARCHAR2(100) PRIMARY KEY,
    USER_ID VARCHAR2(100),
    CURRENT_STEP NUMBER DEFAULT 1,
    STATUS VARCHAR2(20) DEFAULT 'IN_PROGRESS',
    VIBE VARCHAR2(20),
    HOUSEHOLD_SIZE NUMBER,
    HAS_PET CHAR(1),
    HOUSING_TYPE VARCHAR2(20),
    PYUNG NUMBER,
    MAIN_SPACE CLOB,  -- ❌ JSON 배열 문자열
    COOKING VARCHAR2(20),
    LAUNDRY VARCHAR2(20),
    MEDIA VARCHAR2(20),
    PRIORITY VARCHAR2(20),
    PRIORITY_LIST CLOB,  -- ❌ JSON 배열 문자열
    BUDGET_LEVEL VARCHAR2(20),
    SELECTED_CATEGORIES CLOB,  -- ❌ JSON 배열 문자열
    RECOMMENDED_PRODUCTS CLOB,  -- ❌ JSON 배열 문자열
    RECOMMENDATION_RESULT CLOB,  -- ❌ JSON 객체 문자열
    CREATED_AT DATE DEFAULT SYSDATE,
    UPDATED_AT DATE DEFAULT SYSDATE,
    COMPLETED_AT DATE
);
```

**문제점:**
1. **CLOB 컬럼 다수**: `MAIN_SPACE`, `PRIORITY_LIST`, `SELECTED_CATEGORIES`, `RECOMMENDED_PRODUCTS`, `RECOMMENDATION_RESULT`
2. **JSON 파싱 오버헤드**: 매번 JSON 파싱 필요
3. **쿼리 제약**: 특정 카테고리나 제품만 조회하기 어려움
4. **인덱싱 불가**: CLOB는 인덱싱이 어려움

**정규화 제안:**

```sql
-- 1. ONBOARDING_SESSION_MAIN_SPACES (주요 공간)
CREATE TABLE ONBOARDING_SESSION_MAIN_SPACES (
    SESSION_ID VARCHAR2(100) NOT NULL,
    MAIN_SPACE VARCHAR2(50) NOT NULL,
    CREATED_AT DATE DEFAULT SYSDATE,
    PRIMARY KEY (SESSION_ID, MAIN_SPACE),
    FOREIGN KEY (SESSION_ID) REFERENCES ONBOARDING_SESSION(SESSION_ID) ON DELETE CASCADE
);

-- 2. ONBOARDING_SESSION_PRIORITIES (우선순위 목록)
CREATE TABLE ONBOARDING_SESSION_PRIORITIES (
    SESSION_ID VARCHAR2(100) NOT NULL,
    PRIORITY VARCHAR2(20) NOT NULL,
    PRIORITY_ORDER NUMBER NOT NULL,  -- 순서 정보
    CREATED_AT DATE DEFAULT SYSDATE,
    PRIMARY KEY (SESSION_ID, PRIORITY_ORDER),
    FOREIGN KEY (SESSION_ID) REFERENCES ONBOARDING_SESSION(SESSION_ID) ON DELETE CASCADE
);

-- 3. ONBOARDING_SESSION_CATEGORIES (선택한 카테고리)
CREATE TABLE ONBOARDING_SESSION_CATEGORIES (
    SESSION_ID VARCHAR2(100) NOT NULL,
    CATEGORY_NAME VARCHAR2(50) NOT NULL,
    CREATED_AT DATE DEFAULT SYSDATE,
    PRIMARY KEY (SESSION_ID, CATEGORY_NAME),
    FOREIGN KEY (SESSION_ID) REFERENCES ONBOARDING_SESSION(SESSION_ID) ON DELETE CASCADE
);

-- 4. ONBOARDING_SESSION_RECOMMENDED_PRODUCTS (추천 제품)
CREATE TABLE ONBOARDING_SESSION_RECOMMENDED_PRODUCTS (
    SESSION_ID VARCHAR2(100) NOT NULL,
    PRODUCT_ID NUMBER NOT NULL,
    CATEGORY_NAME VARCHAR2(50),
    RANK_ORDER NUMBER,
    SCORE NUMBER(5,2),
    CREATED_AT DATE DEFAULT SYSDATE,
    PRIMARY KEY (SESSION_ID, PRODUCT_ID),
    FOREIGN KEY (SESSION_ID) REFERENCES ONBOARDING_SESSION(SESSION_ID) ON DELETE CASCADE
);
```

**정규화 효과:**
- ✅ JSON 파싱 오버헤드 제거
- ✅ 특정 카테고리/제품만 조회 가능
- ✅ 인덱스 활용 가능
- ✅ 통계 쿼리 용이

**우선순위**: 중간 (TASTE_CONFIG보다는 덜 급함)

---

#### 2. USER_SAMPLE 테이블

**현재 구조:**
```python
class UserSample(models.Model):
    user_id = models.CharField(max_length=50, unique=True)
    household_size = models.CharField(max_length=20, blank=True)
    space_type = models.CharField(max_length=20, blank=True)
    space_purpose = models.CharField(max_length=50, blank=True)
    space_sqm = models.FloatField(null=True, blank=True)
    space_size_cat = models.CharField(max_length=20, blank=True)
    style_pref = models.CharField(max_length=50, blank=True)
    cooking_freq = models.CharField(max_length=20, blank=True)
    laundry_pattern = models.CharField(max_length=50, blank=True)
    media_pref = models.CharField(max_length=50, blank=True)
    pet = models.CharField(max_length=10, blank=True)
    budget_range = models.CharField(max_length=50, blank=True)
    payment_pref = models.CharField(max_length=20, blank=True)
    
    recommended_fridge_l = models.IntegerField(null=True, blank=True)
    recommended_washer_kg = models.IntegerField(null=True, blank=True)
    recommended_tv_inch = models.IntegerField(null=True, blank=True)
    recommended_vacuum = models.CharField(max_length=50, blank=True)
    recommended_oven = models.CharField(max_length=50, blank=True)
    purchased_items = models.TextField(blank=True)  -- ❌ JSON 또는 텍스트
```

**문제점:**
1. **추천 제품 정보가 개별 컬럼**: `recommended_fridge_l`, `recommended_washer_kg` 등
2. **purchased_items가 TEXT**: JSON 파싱 필요할 수 있음

**정규화 제안:**

```sql
-- USER_SAMPLE_RECOMMENDATIONS (추천 제품 정보)
CREATE TABLE USER_SAMPLE_RECOMMENDATIONS (
    USER_ID VARCHAR2(50) NOT NULL,
    CATEGORY_NAME VARCHAR2(50) NOT NULL,
    RECOMMENDED_VALUE VARCHAR2(100),
    RECOMMENDED_UNIT VARCHAR2(20),  -- 'L', 'KG', 'INCH' 등
    CREATED_AT DATE DEFAULT SYSDATE,
    PRIMARY KEY (USER_ID, CATEGORY_NAME),
    FOREIGN KEY (USER_ID) REFERENCES USER_SAMPLE(USER_ID) ON DELETE CASCADE
);

-- USER_SAMPLE_PURCHASED_ITEMS (구매한 제품)
CREATE TABLE USER_SAMPLE_PURCHASED_ITEMS (
    USER_ID VARCHAR2(50) NOT NULL,
    PRODUCT_ID NUMBER NOT NULL,
    PURCHASED_AT DATE,
    CREATED_AT DATE DEFAULT SYSDATE,
    PRIMARY KEY (USER_ID, PRODUCT_ID),
    FOREIGN KEY (USER_ID) REFERENCES USER_SAMPLE(USER_ID) ON DELETE CASCADE
);
```

**우선순위**: 낮음 (현재 구조로도 충분히 사용 가능)

---

#### 3. PRODUCT_DEMOGRAPHICS 테이블

**현재 구조:**
```python
class ProductDemographics(models.Model):
    product = models.OneToOneField("Product", ...)
    family_types = models.JSONField(default=list, blank=True)  -- ❌ JSON
    house_sizes = models.JSONField(default=list, blank=True)  -- ❌ JSON
    house_types = models.JSONField(default=list, blank=True)  -- ❌ JSON
```

**문제점:**
1. **JSON 컬럼 다수**: `family_types`, `house_sizes`, `house_types`

**정규화 제안:**

```sql
-- PRODUCT_DEMOGRAPHICS_FAMILY_TYPES
CREATE TABLE PRODUCT_DEMOGRAPHICS_FAMILY_TYPES (
    PRODUCT_ID NUMBER NOT NULL,
    FAMILY_TYPE VARCHAR2(50) NOT NULL,
    PRIMARY KEY (PRODUCT_ID, FAMILY_TYPE),
    FOREIGN KEY (PRODUCT_ID) REFERENCES PRODUCT(PRODUCT_ID) ON DELETE CASCADE
);

-- PRODUCT_DEMOGRAPHICS_HOUSE_SIZES
CREATE TABLE PRODUCT_DEMOGRAPHICS_HOUSE_SIZES (
    PRODUCT_ID NUMBER NOT NULL,
    HOUSE_SIZE VARCHAR2(50) NOT NULL,
    PRIMARY KEY (PRODUCT_ID, HOUSE_SIZE),
    FOREIGN KEY (PRODUCT_ID) REFERENCES PRODUCT(PRODUCT_ID) ON DELETE CASCADE
);

-- PRODUCT_DEMOGRAPHICS_HOUSE_TYPES
CREATE TABLE PRODUCT_DEMOGRAPHICS_HOUSE_TYPES (
    PRODUCT_ID NUMBER NOT NULL,
    HOUSE_TYPE VARCHAR2(50) NOT NULL,
    PRIMARY KEY (PRODUCT_ID, HOUSE_TYPE),
    FOREIGN KEY (PRODUCT_ID) REFERENCES PRODUCT(PRODUCT_ID) ON DELETE CASCADE
);
```

**우선순위**: 낮음 (사용 빈도가 낮을 수 있음)

---

## 2. 정규화 우선순위 요약

| 테이블 | 우선순위 | 이유 |
|--------|---------|------|
| **TASTE_CONFIG** | ✅ **완료** | 카테고리 추가 시마다 ALTER TABLE 필요, 데이터 중복 |
| **ONBOARDING_SESSION** | ⚠️ **중간** | CLOB 컬럼 다수, JSON 파싱 오버헤드, 통계 쿼리 필요 |
| **PRODUCT_DEMOGRAPHICS** | ⚠️ **낮음** | JSON 컬럼 있으나 사용 빈도 낮을 수 있음 |
| **USER_SAMPLE** | ⚠️ **낮음** | 현재 구조로도 충분히 사용 가능 |

---

## 3. 결론

**TASTE_CONFIG 외에 정규화가 필요한 테이블:**

1. **ONBOARDING_SESSION** (우선순위: 중간)
   - CLOB 컬럼이 많고, 통계/조회 쿼리가 필요할 수 있음
   - 하지만 현재 사용 패턴에 따라 결정 필요

2. **PRODUCT_DEMOGRAPHICS** (우선순위: 낮음)
   - JSON 컬럼이 있으나, 사용 빈도가 낮을 수 있음
   - 필요 시 정규화 고려

**권장사항:**
- 현재는 **TASTE_CONFIG 정규화 완료**로 충분
- **ONBOARDING_SESSION**은 사용 패턴을 관찰한 후 필요 시 정규화
- 다른 테이블들은 현재 구조로도 충분히 사용 가능


