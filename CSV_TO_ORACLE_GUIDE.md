# CSV 데이터를 Oracle DB에 로드하는 가이드

이 가이드는 `data/csv` 디렉토리에 있는 CSV 파일들을 Oracle DB에 로드하는 방법을 설명합니다.

## 📋 개요

CSV 파일은 두 가지 유형으로 구분됩니다:

1. **평균벡터 파일** (`*_모델별_평균벡터.csv`)
   - 컬럼: `model_name`, `recommend_reason`
   - 예: `냉장고_모델별_평균벡터.csv`, `공기청정기_모델별_평균벡터.csv`

2. **인구통계 정보 파일** (`*_모델별_리뷰_인구통계정보.csv` 또는 `*_모델별_리뷰_정보추출결과.csv`)
   - 컬럼: `Product_code`, `family_list`, `size_list`, `house_list`
   - 예: `TV_모델별_리뷰_인구통계정보.csv`, `세탁기_모델별_리뷰_인구통계정보.csv`

## 🗄️ 생성되는 테이블

### 1. `PRODUCT_RECOMMEND_REASONS`
평균벡터 데이터를 저장하는 테이블

| 컬럼명 | 타입 | 설명 |
|--------|------|------|
| id | NUMBER | 기본키 (자동 증가) |
| product_category | VARCHAR2(100) | 제품 카테고리 |
| model_name | VARCHAR2(200) | 모델명 |
| recommend_reason | CLOB | 추천 이유 |
| created_at | DATE | 생성일시 |

### 2. `PRODUCT_REVIEW_DEMOGRAPHICS`
인구통계 정보를 저장하는 테이블

| 컬럼명 | 타입 | 설명 |
|--------|------|------|
| id | NUMBER | 기본키 (자동 증가) |
| product_category | VARCHAR2(100) | 제품 카테고리 |
| product_code | VARCHAR2(200) | 제품 코드 |
| family_list | CLOB | 가족 구성 리스트 (JSON 배열 형태) |
| size_list | CLOB | 주거 크기 리스트 (JSON 배열 형태) |
| house_list | CLOB | 주거 형태 리스트 (JSON 배열 형태) |
| created_at | DATE | 생성일시 |

## 🚀 사용 방법

### 1단계: 테이블 생성 (DDL 실행)

#### 방법 A: Python 스크립트 사용 (권장)
```powershell
python api/db/execute_ddl.py
```

#### 방법 B: SQL 파일 직접 실행
SQL Developer나 다른 Oracle 클라이언트에서 다음 파일을 실행:
```
api/db/csv_data_tables_ddl.sql
```

#### 방법 C: Python에서 직접 실행
```python
from api.db.oracle_client import get_connection

conn = get_connection()
cursor = conn.cursor()

# DDL 파일 내용을 읽어서 실행
with open('api/db/csv_data_tables_ddl.sql', 'r', encoding='utf-8') as f:
    ddl = f.read()
    cursor.execute(ddl)

conn.commit()
cursor.close()
conn.close()
```

### 2단계: CSV 데이터 로드

```powershell
python load_csv_to_oracle.py
```

이 스크립트는:
- `data/csv` 디렉토리의 모든 CSV 파일을 자동으로 감지
- 파일 형식을 자동으로 판별
- 적절한 테이블에 데이터 삽입
- 중복 데이터는 자동으로 업데이트 (MERGE 사용)

## 📊 실행 결과 확인

### 데이터 개수 확인
```sql
-- 평균벡터 데이터 개수
SELECT product_category, COUNT(*) as cnt
FROM product_recommend_reasons
GROUP BY product_category
ORDER BY product_category;

-- 인구통계 데이터 개수
SELECT product_category, COUNT(*) as cnt
FROM product_review_demographics
GROUP BY product_category
ORDER BY product_category;
```

### 샘플 데이터 조회
```sql
-- 평균벡터 샘플
SELECT * FROM product_recommend_reasons
WHERE ROWNUM <= 5;

-- 인구통계 샘플
SELECT * FROM product_review_demographics
WHERE ROWNUM <= 5;
```

## 🔧 문제 해결

### 문제 1: 테이블이 이미 존재함
```
ORA-00955: name is already used by an existing object
```
**해결**: 테이블이 이미 존재하는 경우입니다. 기존 테이블을 사용하거나 삭제 후 재생성하세요.

```sql
-- 테이블 삭제 (주의: 데이터가 모두 삭제됩니다)
DROP TABLE product_review_demographics;
DROP TABLE product_recommend_reasons;
```

### 문제 2: 인코딩 오류
CSV 파일이 UTF-8이 아닌 경우, 파일을 UTF-8로 변환하세요.

### 문제 3: 연결 오류
`.env` 파일의 Oracle 연결 정보를 확인하세요:
- `ORACLE_USER`
- `ORACLE_PASSWORD`
- `ORACLE_HOST`
- `ORACLE_PORT`

## 📝 주의사항

1. **중복 데이터 처리**: MERGE 문을 사용하여 동일한 제품 카테고리와 모델명/제품코드가 있으면 업데이트됩니다.

2. **대용량 데이터**: CLOB 타입을 사용하므로 긴 텍스트도 저장 가능합니다.

3. **카테고리 추출**: 파일명에서 자동으로 제품 카테고리를 추출합니다. 예:
   - `냉장고_모델별_평균벡터.csv` → 카테고리: `냉장고`
   - `TV_모델별_리뷰_인구통계정보.csv` → 카테고리: `TV`

4. **리스트 데이터**: `family_list`, `size_list`, `house_list`는 Python 리스트 문자열 형태로 저장됩니다.
   - 예: `['부모님', '신혼']` → 그대로 문자열로 저장

## 🔄 데이터 재로드

데이터를 다시 로드하려면:
1. 기존 데이터를 유지하면서 업데이트: 그냥 `load_csv_to_oracle.py` 실행 (MERGE로 처리)
2. 기존 데이터를 삭제하고 새로 로드:
   ```sql
   DELETE FROM product_review_demographics;
   DELETE FROM product_recommend_reasons;
   ```
   그 다음 `load_csv_to_oracle.py` 실행

## 📞 추가 정보

- Oracle 연결 설정: `ORACLE_DB_SETUP_GUIDE_WINDOWS10.md` 참조
- Oracle 클라이언트: `api/db/oracle_client.py` 참조


