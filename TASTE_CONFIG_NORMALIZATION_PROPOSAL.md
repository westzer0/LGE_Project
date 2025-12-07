# TASTE_CONFIG 정규화 제안서

## 현재 문제점

### 1. 데이터 중복 (Redundancy)
- **개별 컬럼과 JSON 컬럼의 중복**: `TV_SCORE`, `냉장고_SCORE` 등의 개별 컬럼과 `CATEGORY_SCORES` JSON 컬럼이 동일한 데이터를 저장
- **확장성 문제**: 새로운 카테고리가 추가될 때마다 새로운 컬럼을 추가해야 함 (Oracle 11g 컬럼명 30자 제한)
- **데이터 일관성**: 개별 컬럼과 JSON 컬럼 간 동기화 문제 가능성

### 2. 테이블 구조의 무거움
- **많은 컬럼**: 20개 이상의 카테고리별 점수 컬럼
- **큰 JSON 컬럼**: `RECOMMENDED_PRODUCTS`, `RECOMMENDED_PRODUCT_SCORES` 등이 CLOB로 저장되어 전체 레코드 크기가 큼
- **쿼리 성능**: 필요한 카테고리만 조회하기 어려움 (전체 레코드를 읽어야 함)

### 3. 유지보수 어려움
- **스키마 변경**: 카테고리 추가 시 ALTER TABLE 필요
- **데이터 마이그레이션**: 기존 데이터를 새 구조로 이전하는 작업 복잡

## 정규화 제안

### 목표
1. **데이터 중복 제거**: 개별 컬럼 제거, JSON을 정규화된 테이블로 분리
2. **확장성 향상**: 새로운 카테고리 추가 시 테이블 구조 변경 불필요
3. **성능 최적화**: 필요한 카테고리만 조회 가능
4. **유지보수성 향상**: 스키마 변경 최소화

### 정규화된 테이블 구조

#### 1. TASTE_CONFIG (기본 테이블 - 유지)
```sql
CREATE TABLE TASTE_CONFIG (
    TASTE_ID NUMBER PRIMARY KEY,
    
    -- 대표 온보딩 특성
    REPRESENTATIVE_VIBE VARCHAR2(20),
    REPRESENTATIVE_HOUSEHOLD_SIZE NUMBER,
    REPRESENTATIVE_MAIN_SPACE VARCHAR2(50),
    REPRESENTATIVE_HAS_PET CHAR(1),
    REPRESENTATIVE_PRIORITY VARCHAR2(20),
    REPRESENTATIVE_BUDGET_LEVEL VARCHAR2(20),
    
    -- 메타 정보
    IS_ACTIVE CHAR(1) DEFAULT 'Y',
    AUTO_GENERATED CHAR(1) DEFAULT 'N',
    LAST_SIMULATION_DATE DATE,
    CREATED_AT DATE DEFAULT SYSDATE,
    UPDATED_AT DATE DEFAULT SYSDATE
);
```

**변경사항**:
- JSON 컬럼 제거: `RECOMMENDED_CATEGORIES`, `CATEGORY_SCORES`, `RECOMMENDED_PRODUCTS`, `RECOMMENDED_PRODUCT_SCORES`, `ILL_SUITED_CATEGORIES`
- 개별 점수 컬럼 제거: `TV_SCORE`, `냉장고_SCORE` 등 모든 카테고리별 점수 컬럼

#### 2. TASTE_CATEGORY_SCORES (새 테이블)
```sql
CREATE TABLE TASTE_CATEGORY_SCORES (
    TASTE_ID NUMBER NOT NULL,
    CATEGORY_NAME VARCHAR2(50) NOT NULL,
    SCORE NUMBER(5,2) NOT NULL,  -- 0~100점
    IS_RECOMMENDED CHAR(1) DEFAULT 'N',  -- 'Y'/'N' - 추천 카테고리 여부
    IS_ILL_SUITED CHAR(1) DEFAULT 'N',  -- 'Y'/'N' - 부적합 카테고리 여부
    CREATED_AT DATE DEFAULT SYSDATE,
    UPDATED_AT DATE DEFAULT SYSDATE,
    
    PRIMARY KEY (TASTE_ID, CATEGORY_NAME),
    FOREIGN KEY (TASTE_ID) REFERENCES TASTE_CONFIG(TASTE_ID) ON DELETE CASCADE
);

CREATE INDEX IDX_TASTE_CAT_SCORES_TASTE ON TASTE_CATEGORY_SCORES(TASTE_ID);
CREATE INDEX IDX_TASTE_CAT_SCORES_CAT ON TASTE_CATEGORY_SCORES(CATEGORY_NAME);
CREATE INDEX IDX_TASTE_CAT_SCORES_REC ON TASTE_CATEGORY_SCORES(TASTE_ID, IS_RECOMMENDED);
```

**장점**:
- 카테고리별 점수를 개별 레코드로 관리
- 필요한 카테고리만 조회 가능
- 새로운 카테고리 추가 시 INSERT만 하면 됨

#### 3. TASTE_RECOMMENDED_PRODUCTS (새 테이블)
```sql
CREATE TABLE TASTE_RECOMMENDED_PRODUCTS (
    TASTE_ID NUMBER NOT NULL,
    CATEGORY_NAME VARCHAR2(50) NOT NULL,
    PRODUCT_ID NUMBER NOT NULL,
    SCORE NUMBER(5,2),  -- 해당 제품의 점수 (0~100점)
    RANK_ORDER NUMBER(2),  -- 카테고리 내 순위 (1, 2, 3...)
    CREATED_AT DATE DEFAULT SYSDATE,
    UPDATED_AT DATE DEFAULT SYSDATE,
    
    PRIMARY KEY (TASTE_ID, CATEGORY_NAME, PRODUCT_ID),
    FOREIGN KEY (TASTE_ID) REFERENCES TASTE_CONFIG(TASTE_ID) ON DELETE CASCADE
);

CREATE INDEX IDX_TASTE_REC_PROD_TASTE ON TASTE_RECOMMENDED_PRODUCTS(TASTE_ID);
CREATE INDEX IDX_TASTE_REC_PROD_CAT ON TASTE_RECOMMENDED_PRODUCTS(CATEGORY_NAME);
CREATE INDEX IDX_TASTE_REC_PROD_TASTE_CAT ON TASTE_RECOMMENDED_PRODUCTS(TASTE_ID, CATEGORY_NAME);
```

**장점**:
- 제품별 점수와 순위를 명확히 관리
- 카테고리별 상위 N개 제품 조회 용이
- JSON 파싱 불필요

## 마이그레이션 전략

### Phase 1: 새 테이블 생성 및 데이터 이전
1. 새 테이블 생성 (`TASTE_CATEGORY_SCORES`, `TASTE_RECOMMENDED_PRODUCTS`)
2. 기존 `TASTE_CONFIG`의 JSON 데이터를 새 테이블로 마이그레이션
3. 기존 개별 컬럼 데이터도 새 테이블로 통합

### Phase 2: 코드 업데이트
1. `taste_based_product_scorer.py`의 `_get_taste_config()` 메서드 수정
2. 새 테이블에서 데이터 조회하도록 변경
3. 기존 JSON 파싱 로직을 JOIN 쿼리로 변경

### Phase 3: 기존 컬럼 제거 (선택사항)
1. 모든 코드가 새 구조를 사용하는지 확인
2. 기존 JSON 컬럼 및 개별 점수 컬럼 제거
3. 테이블 구조 최종 정리

## 예상 효과

### 1. 저장 공간 절감
- 중복 데이터 제거로 약 30-40% 절감 예상
- JSON 파싱 오버헤드 제거

### 2. 쿼리 성능 향상
- 필요한 카테고리만 조회 가능 (전체 레코드 읽기 불필요)
- 인덱스 활용으로 조회 속도 향상
- JOIN을 통한 효율적인 데이터 조회

### 3. 확장성 향상
- 새로운 카테고리 추가 시 테이블 구조 변경 불필요
- 카테고리 수에 제한 없음

### 4. 유지보수성 향상
- 데이터 일관성 보장 (중복 제거)
- 스키마 변경 최소화
- 코드 가독성 향상

## 마이그레이션 스크립트 예시

### 데이터 마이그레이션
```sql
-- 1. TASTE_CATEGORY_SCORES 데이터 이전
INSERT INTO TASTE_CATEGORY_SCORES (TASTE_ID, CATEGORY_NAME, SCORE, IS_RECOMMENDED, IS_ILL_SUITED)
SELECT 
    tc.TASTE_ID,
    cat.category_name,
    CASE 
        WHEN cat.category_name = 'TV' THEN tc.TV_SCORE
        WHEN cat.category_name = '냉장고' THEN tc."냉장고_SCORE"
        -- ... 다른 카테고리들
    END AS SCORE,
    CASE 
        WHEN cat.category_name IN (
            SELECT JSON_VALUE(tc.RECOMMENDED_CATEGORIES, '$[' || LEVEL - 1 || ']')
            FROM DUAL
            CONNECT BY LEVEL <= JSON_ARRAY_LENGTH(tc.RECOMMENDED_CATEGORIES)
        ) THEN 'Y'
        ELSE 'N'
    END AS IS_RECOMMENDED,
    CASE 
        WHEN cat.category_name IN (
            SELECT JSON_VALUE(tc.ILL_SUITED_CATEGORIES, '$[' || LEVEL - 1 || ']')
            FROM DUAL
            CONNECT BY LEVEL <= JSON_ARRAY_LENGTH(tc.ILL_SUITED_CATEGORIES)
        ) THEN 'Y'
        ELSE 'N'
    END AS IS_ILL_SUITED
FROM TASTE_CONFIG tc
CROSS JOIN (
    SELECT 'TV' AS category_name FROM DUAL
    UNION ALL SELECT '냉장고' FROM DUAL
    UNION ALL SELECT '세탁기' FROM DUAL
    -- ... 모든 카테고리
) cat;

-- 2. TASTE_RECOMMENDED_PRODUCTS 데이터 이전
-- (JSON 파싱하여 INSERT)
```

## 주의사항

1. **하위 호환성**: 기존 코드와의 호환성을 위해 단계적 마이그레이션 필요
2. **데이터 검증**: 마이그레이션 후 데이터 일관성 검증 필수
3. **성능 테스트**: 새 구조에서의 쿼리 성능 테스트 필요
4. **롤백 계획**: 문제 발생 시 롤백 가능한 구조 유지

## 다음 단계

1. 이 제안서 검토 및 승인
2. 마이그레이션 스크립트 작성
3. 테스트 환경에서 검증
4. 프로덕션 마이그레이션 실행



