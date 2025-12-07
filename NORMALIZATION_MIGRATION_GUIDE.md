# TASTE_CONFIG 정규화 마이그레이션 가이드

## 개요

이 가이드는 `TASTE_CONFIG` 테이블을 정규화된 구조로 마이그레이션하는 방법을 설명합니다.

## 정규화 목표

1. **데이터 중복 제거**: 개별 컬럼과 JSON 컬럼의 중복 제거
2. **확장성 향상**: 카테고리 추가 시 테이블 구조 변경 불필요
3. **성능 최적화**: 필요한 카테고리만 조회 가능, 인덱스 활용
4. **유지보수성 향상**: 스키마 변경 최소화

## 정규화된 테이블 구조

### 1. TASTE_CONFIG (기본 테이블)
- 대표 온보딩 특성만 저장
- JSON 컬럼 및 개별 점수 컬럼 제거

### 2. TASTE_CATEGORY_SCORES (새 테이블)
- 카테고리별 점수를 개별 레코드로 관리
- `(TASTE_ID, CATEGORY_NAME)` 기본키
- `IS_RECOMMENDED`, `IS_ILL_SUITED` 플래그 포함

### 3. TASTE_RECOMMENDED_PRODUCTS (새 테이블)
- 카테고리별 추천 제품을 개별 레코드로 관리
- `(TASTE_ID, CATEGORY_NAME, PRODUCT_ID)` 기본키
- `SCORE`, `RANK_ORDER` 포함

## 마이그레이션 단계

### Step 1: 정규화된 테이블 생성

정규화된 테이블이 자동으로 생성됩니다. 수동으로 생성하려면:

```bash
# SQL 스크립트 실행
# api/db/normalize_taste_config.sql 참고
```

또는 마이그레이션 명령어 실행 시 자동 생성됩니다.

### Step 2: 데이터 마이그레이션

기존 `TASTE_CONFIG` 테이블의 데이터를 정규화된 테이블로 마이그레이션:

```bash
# 전체 마이그레이션 (1-120)
python manage.py migrate_taste_config_to_normalized

# 특정 범위만 마이그레이션
python manage.py migrate_taste_config_to_normalized --taste-range 1-10

# 테스트 실행 (실제 변경 없음)
python manage.py migrate_taste_config_to_normalized --dry-run
```

**마이그레이션 내용:**
- 개별 점수 컬럼 (`TV_SCORE`, `냉장고_SCORE` 등) → `TASTE_CATEGORY_SCORES`
- JSON 컬럼 (`CATEGORY_SCORES`, `RECOMMENDED_PRODUCTS` 등) → 정규화된 테이블

### Step 3: 코드 업데이트 확인

다음 파일들이 정규화된 구조를 사용하도록 업데이트되었습니다:

1. ✅ `api/services/taste_based_product_scorer.py`
   - `_get_taste_config()` 메서드가 정규화된 테이블에서 조회

2. ✅ `api/management/commands/populate_taste_config.py`
   - `_save_to_normalized_tables()` 메서드 추가
   - 정규화된 테이블에도 데이터 저장

3. ✅ `api/management/commands/migrate_taste_config_to_normalized.py`
   - 동적 카테고리 컬럼 감지
   - 모든 카테고리 자동 마이그레이션

### Step 4: 데이터 검증

마이그레이션 후 데이터 검증:

```sql
-- 마이그레이션된 데이터 개수 확인
SELECT 
    'TASTE_CATEGORY_SCORES' AS TABLE_NAME,
    COUNT(*) AS RECORD_COUNT
FROM TASTE_CATEGORY_SCORES
UNION ALL
SELECT 
    'TASTE_RECOMMENDED_PRODUCTS' AS TABLE_NAME,
    COUNT(*) AS RECORD_COUNT
FROM TASTE_RECOMMENDED_PRODUCTS;

-- Taste별 카테고리 점수 개수 확인
SELECT 
    TASTE_ID,
    COUNT(*) AS CATEGORY_COUNT
FROM TASTE_CATEGORY_SCORES
GROUP BY TASTE_ID
ORDER BY TASTE_ID;

-- 추천 카테고리 확인
SELECT 
    TASTE_ID,
    COUNT(*) AS RECOMMENDED_COUNT
FROM TASTE_CATEGORY_SCORES
WHERE IS_RECOMMENDED = 'Y'
GROUP BY TASTE_ID
ORDER BY TASTE_ID;
```

### Step 5: 기존 컬럼 제거 (선택사항)

모든 코드가 정규화된 구조를 사용하는지 확인 후, 기존 컬럼을 제거할 수 있습니다:

```sql
-- 주의: 모든 코드가 새 구조를 사용하는지 확인 후 실행
-- ALTER TABLE TASTE_CONFIG DROP COLUMN TV_SCORE;
-- ALTER TABLE TASTE_CONFIG DROP COLUMN "냉장고_SCORE";
-- ... (다른 카테고리 컬럼들)

-- JSON 컬럼 제거
-- ALTER TABLE TASTE_CONFIG DROP COLUMN RECOMMENDED_CATEGORIES;
-- ALTER TABLE TASTE_CONFIG DROP COLUMN CATEGORY_SCORES;
-- ALTER TABLE TASTE_CONFIG DROP COLUMN RECOMMENDED_PRODUCTS;
-- ALTER TABLE TASTE_CONFIG DROP COLUMN RECOMMENDED_PRODUCT_SCORES;
-- ALTER TABLE TASTE_CONFIG DROP COLUMN ILL_SUITED_CATEGORIES;
```

## 롤백 방법

문제 발생 시 롤백:

```sql
-- 정규화된 테이블 삭제
DROP TABLE TASTE_RECOMMENDED_PRODUCTS;
DROP TABLE TASTE_CATEGORY_SCORES;
```

기존 코드는 여전히 JSON 컬럼을 사용하므로 정상 동작합니다.

## 주의사항

1. **하위 호환성**: 기존 코드와의 호환성을 위해 단계적 마이그레이션 필요
2. **데이터 검증**: 마이그레이션 후 데이터 일관성 검증 필수
3. **성능 테스트**: 새 구조에서의 쿼리 성능 테스트 필요
4. **백업**: 마이그레이션 전 데이터 백업 권장

## 예상 효과

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

## 문제 해결

### 문제: 정규화된 테이블이 없음
**해결**: 마이그레이션 명령어 실행 시 자동 생성됩니다.

### 문제: 마이그레이션 중 에러 발생
**해결**: `--dry-run` 옵션으로 테스트 후, 특정 범위만 마이그레이션

### 문제: 기존 코드가 JSON 컬럼을 사용
**해결**: `taste_based_product_scorer.py`는 이미 업데이트되었습니다. 다른 파일도 확인 필요

## 참고 문서

- `TASTE_CONFIG_NORMALIZATION_PROPOSAL.md`: 상세 정규화 제안서
- `DB_NORMALIZATION_ANALYSIS.md`: 정규화 필요성 분석
- `api/db/normalize_taste_config.sql`: 정규화 SQL 스크립트


