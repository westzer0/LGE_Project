# Oracle DB 정규화 필요성 분석

## 현재 TASTE_CONFIG 테이블의 문제점

### 1. 비정규화된 구조 (1NF 위반)

현재 `TASTE_CONFIG` 테이블은 다음과 같은 비정규화된 구조를 가지고 있습니다:

#### 문제점 1: 개별 카테고리 컬럼들
```sql
-- 20개 이상의 개별 점수 컬럼
TV_SCORE NUMBER(5,2)
냉장고_SCORE NUMBER(5,2)
세탁기_SCORE NUMBER(5,2)
에어컨_SCORE NUMBER(5,2)
청소기_SCORE NUMBER(5,2)
-- ... 등등
```

**문제:**
- 카테고리 추가 시마다 `ALTER TABLE` 필요
- Oracle 11g 컬럼명 30자 제한으로 인한 제약
- 테이블 구조가 무거워짐 (120개 taste × 20개 컬럼 = 2,400개 이상의 값)

#### 문제점 2: JSON 컬럼과 개별 컬럼의 중복
```sql
-- JSON 컬럼
CATEGORY_SCORES CLOB  -- {"TV": 85.0, "냉장고": 70.0, ...}
RECOMMENDED_PRODUCTS CLOB  -- {"TV": [1,2,3], ...}
RECOMMENDED_PRODUCT_SCORES CLOB  -- {"TV": [90,85,80], ...}

-- 개별 컬럼 (중복!)
TV_SCORE NUMBER(5,2)
냉장고_SCORE NUMBER(5,2)
```

**문제:**
- 동일한 데이터가 두 곳에 저장됨 (중복)
- 데이터 일관성 문제 가능성
- 업데이트 시 두 곳 모두 수정 필요

#### 문제점 3: CLOB 파싱 오버헤드
현재 코드 (`taste_based_product_scorer.py:160-177`)에서:
```python
# CLOB를 문자열로 읽기
rec_cats = row[7]
if rec_cats:
    if hasattr(rec_cats, 'read'):
        rec_cats = rec_cats.read()
    recommended_categories = json.loads(rec_cats) if isinstance(rec_cats, str) else []
```

**문제:**
- 매번 JSON 파싱 필요 (성능 오버헤드)
- 전체 레코드를 읽어야 함 (필요한 카테고리만 조회 불가)
- CLOB 타입은 인덱싱이 어려움

### 2. 확장성 문제

#### 문제점 4: 카테고리 추가 시 스키마 변경 필요
새로운 카테고리가 추가될 때마다:
1. `ALTER TABLE TASTE_CONFIG ADD 새로운카테고리_SCORE NUMBER(5,2);` 실행
2. 기존 데이터 마이그레이션
3. 코드 수정 필요

**예시:**
```sql
-- 새로운 카테고리 "로봇청소기" 추가 시
ALTER TABLE TASTE_CONFIG ADD "로봇청소기_SCORE" NUMBER(5,2);
-- Oracle 11g 컬럼명 30자 제한으로 "로봇청소기_SCORE"는 가능하지만
-- 더 긴 이름은 불가능
```

### 3. 쿼리 성능 문제

#### 문제점 5: 불필요한 데이터 로딩
```sql
-- 현재: 전체 레코드 로드 (모든 컬럼 + CLOB)
SELECT * FROM TASTE_CONFIG WHERE TASTE_ID = 1;

-- 필요한 것: 특정 카테고리만
-- 하지만 현재 구조에서는 불가능
```

**문제:**
- 특정 카테고리 점수만 필요한데 전체 레코드를 읽어야 함
- CLOB 전체를 메모리에 로드해야 함
- 인덱스 활용 불가

## 정규화 제안

### 정규화된 구조 (3NF)

#### 1. TASTE_CONFIG (기본 테이블 - 유지)
```sql
CREATE TABLE TASTE_CONFIG (
    TASTE_ID NUMBER PRIMARY KEY,
    REPRESENTATIVE_VIBE VARCHAR2(20),
    REPRESENTATIVE_HOUSEHOLD_SIZE NUMBER,
    REPRESENTATIVE_MAIN_SPACE VARCHAR2(50),
    REPRESENTATIVE_HAS_PET CHAR(1),
    REPRESENTATIVE_PRIORITY VARCHAR2(20),
    REPRESENTATIVE_BUDGET_LEVEL VARCHAR2(20),
    IS_ACTIVE CHAR(1) DEFAULT 'Y',
    AUTO_GENERATED CHAR(1) DEFAULT 'N',
    CREATED_AT DATE DEFAULT SYSDATE,
    UPDATED_AT DATE DEFAULT SYSDATE
);
```

**변경사항:**
- ❌ 제거: 개별 점수 컬럼들 (TV_SCORE, 냉장고_SCORE 등)
- ❌ 제거: JSON 컬럼들 (CATEGORY_SCORES, RECOMMENDED_PRODUCTS 등)
- ✅ 유지: 대표 온보딩 특성만 유지

#### 2. TASTE_CATEGORY_SCORES (새 테이블)
```sql
CREATE TABLE TASTE_CATEGORY_SCORES (
    TASTE_ID NUMBER NOT NULL,
    CATEGORY_NAME VARCHAR2(50) NOT NULL,
    SCORE NUMBER(5,2) NOT NULL,
    IS_RECOMMENDED CHAR(1) DEFAULT 'N',
    IS_ILL_SUITED CHAR(1) DEFAULT 'N',
    CREATED_AT DATE DEFAULT SYSDATE,
    UPDATED_AT DATE DEFAULT SYSDATE,
    
    PRIMARY KEY (TASTE_ID, CATEGORY_NAME),
    FOREIGN KEY (TASTE_ID) REFERENCES TASTE_CONFIG(TASTE_ID) ON DELETE CASCADE
);

CREATE INDEX IDX_TASTE_CAT_SCORES_TASTE ON TASTE_CATEGORY_SCORES(TASTE_ID);
CREATE INDEX IDX_TASTE_CAT_SCORES_CAT ON TASTE_CATEGORY_SCORES(CATEGORY_NAME);
```

**장점:**
- ✅ 카테고리별 점수를 개별 레코드로 관리
- ✅ 필요한 카테고리만 조회 가능
- ✅ 새로운 카테고리 추가 시 INSERT만 하면 됨
- ✅ 인덱스 활용 가능

#### 3. TASTE_RECOMMENDED_PRODUCTS (새 테이블)
```sql
CREATE TABLE TASTE_RECOMMENDED_PRODUCTS (
    TASTE_ID NUMBER NOT NULL,
    CATEGORY_NAME VARCHAR2(50) NOT NULL,
    PRODUCT_ID NUMBER NOT NULL,
    SCORE NUMBER(5,2),
    RANK_ORDER NUMBER(2),
    CREATED_AT DATE DEFAULT SYSDATE,
    UPDATED_AT DATE DEFAULT SYSDATE,
    
    PRIMARY KEY (TASTE_ID, CATEGORY_NAME, PRODUCT_ID),
    FOREIGN KEY (TASTE_ID) REFERENCES TASTE_CONFIG(TASTE_ID) ON DELETE CASCADE
);

CREATE INDEX IDX_TASTE_REC_PROD_TASTE_CAT ON TASTE_RECOMMENDED_PRODUCTS(TASTE_ID, CATEGORY_NAME);
```

**장점:**
- ✅ 제품별 점수와 순위를 명확히 관리
- ✅ 카테고리별 상위 N개 제품 조회 용이
- ✅ JSON 파싱 불필요

## 정규화 효과

### 1. 저장 공간 절감
- 중복 데이터 제거로 약 30-40% 절감 예상
- JSON 파싱 오버헤드 제거

### 2. 쿼리 성능 향상
```sql
-- 정규화 전: 전체 레코드 + JSON 파싱
SELECT * FROM TASTE_CONFIG WHERE TASTE_ID = 1;
-- → CLOB 전체 로드 + JSON 파싱 필요

-- 정규화 후: 필요한 카테고리만 조회
SELECT SCORE FROM TASTE_CATEGORY_SCORES 
WHERE TASTE_ID = 1 AND CATEGORY_NAME = 'TV';
-- → 인덱스 활용, 빠른 조회
```

### 3. 확장성 향상
- 새로운 카테고리 추가 시 테이블 구조 변경 불필요
- 카테고리 수에 제한 없음
- Oracle 컬럼명 30자 제한 문제 해결

### 4. 유지보수성 향상
- 데이터 일관성 보장 (중복 제거)
- 스키마 변경 최소화
- 코드 가독성 향상

## 마이그레이션 계획

### Phase 1: 새 테이블 생성 및 데이터 이전
1. ✅ `TASTE_CATEGORY_SCORES` 테이블 생성
2. ✅ `TASTE_RECOMMENDED_PRODUCTS` 테이블 생성
3. 기존 데이터 마이그레이션 (Python 스크립트 사용)

### Phase 2: 코드 업데이트
1. `taste_based_product_scorer.py`의 `_get_taste_config()` 메서드 수정
2. 새 테이블에서 데이터 조회하도록 변경
3. JSON 파싱 로직을 JOIN 쿼리로 변경

### Phase 3: 기존 컬럼 제거 (선택사항)
1. 모든 코드가 새 구조를 사용하는지 확인
2. 기존 JSON 컬럼 및 개별 점수 컬럼 제거
3. 테이블 구조 최종 정리

## 결론

**정규화가 반드시 필요합니다!**

현재 구조는:
- ❌ 데이터 중복 (개별 컬럼 + JSON)
- ❌ 확장성 문제 (카테고리 추가 시 ALTER TABLE)
- ❌ 성능 문제 (CLOB 파싱, 전체 레코드 로드)
- ❌ 유지보수 어려움

정규화 후:
- ✅ 데이터 중복 제거
- ✅ 확장성 향상 (카테고리 추가 시 INSERT만)
- ✅ 성능 향상 (인덱스 활용, 필요한 데이터만 조회)
- ✅ 유지보수 용이

## 참고 문서

- `TASTE_CONFIG_NORMALIZATION_PROPOSAL.md`: 상세 정규화 제안서
- `api/db/normalize_taste_config.sql`: 정규화 SQL 스크립트
- `api/management/commands/migrate_taste_config_to_normalized.py`: 마이그레이션 명령어


