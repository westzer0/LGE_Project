# LLM을 사용한 ERD 생성 프롬프트

Python 스크립트를 실행할 수 없는 경우, 다음 프롬프트를 LLM에게 제공하여 ERD를 생성할 수 있습니다.

---

## 프롬프트 템플릿

```
다음 Oracle DB 스키마 정보를 기반으로 Mermaid ERD 다이어그램을 생성해주세요.

## 데이터베이스 스키마 정보

### 테이블 목록 및 Comments

[여기에 각 테이블의 정보를 아래 형식으로 제공하세요]

**테이블명: PRODUCT**
- 테이블 Comment: "LG 가전 제품 정보 테이블"
- 컬럼:
  - PRODUCT_ID (NUMBER) PK - "제품 고유 ID"
  - PRODUCT_NAME (VARCHAR2(200)) - "제품명"
  - MAIN_CATEGORY (VARCHAR2(50)) - "메인 카테고리"
  - PRICE (NUMBER) - "가격"
  - ...

**테이블명: MEMBER**
- 테이블 Comment: "회원 정보 테이블"
- 컬럼:
  - MEMBER_ID (NUMBER) PK - "회원 고유 ID"
  - EMAIL (VARCHAR2(100)) - "이메일"
  - ...

### Foreign Key 관계

[여기에 Foreign Key 관계를 아래 형식으로 제공하세요]

- WISHLIST.PRODUCT_ID -> PRODUCT.PRODUCT_ID
- WISHLIST.MEMBER_ID -> MEMBER.MEMBER_ID
- ONBOARDING_SESSION.USER_ID -> MEMBER.MEMBER_ID
- ...

## 요구사항

1. **Mermaid ERD 형식**으로 작성
2. 모든 테이블 Comments와 컬럼 Comments를 포함
3. Primary Key는 `PK`로 표시
4. Foreign Key는 `FK`로 표시
5. Foreign Key 관계는 `||--o{` 또는 `||--||` 형식으로 표시
6. 코드 블록은 \`\`\`mermaid로 시작하고 \`\`\`로 끝남
7. 테이블 Comment는 테이블 정의 내부 첫 줄에 따옴표로 표시
8. 컬럼 Comment는 각 컬럼 뒤에 따옴표로 표시

## 출력 형식 예시

\`\`\`mermaid
erDiagram
    PRODUCT {
        "LG 가전 제품 정보 테이블"
        NUMBER PRODUCT_ID PK "제품 고유 ID"
        VARCHAR2 PRODUCT_NAME "제품명"
        VARCHAR2 MAIN_CATEGORY "메인 카테고리"
        NUMBER PRICE "가격"
    }
    
    MEMBER {
        "회원 정보 테이블"
        NUMBER MEMBER_ID PK "회원 고유 ID"
        VARCHAR2 EMAIL "이메일"
    }
    
    WISHLIST {
        "위시리스트 테이블"
        NUMBER WISHLIST_ID PK "위시리스트 ID"
        NUMBER PRODUCT_ID FK "제품 ID"
        NUMBER MEMBER_ID FK "회원 ID"
    }
    
    WISHLIST ||--o{ PRODUCT : "PRODUCT_ID"
    WISHLIST ||--o{ MEMBER : "MEMBER_ID"
\`\`\`

위 형식으로 모든 테이블에 대해 ERD를 생성해주세요.
```

---

## Oracle DB에서 정보 추출 방법

### 1. 테이블 목록과 Comments 조회

```sql
SELECT 
    t.TABLE_NAME,
    tc.COMMENTS AS TABLE_COMMENT
FROM USER_TABLES t
LEFT JOIN USER_TAB_COMMENTS tc ON t.TABLE_NAME = tc.TABLE_NAME
ORDER BY t.TABLE_NAME;
```

### 2. 컬럼 정보와 Comments 조회

```sql
SELECT 
    t.TABLE_NAME,
    t.COLUMN_NAME,
    t.DATA_TYPE,
    t.DATA_LENGTH,
    t.DATA_PRECISION,
    t.DATA_SCALE,
    t.NULLABLE,
    c.COMMENTS AS COLUMN_COMMENT
FROM USER_TAB_COLUMNS t
LEFT JOIN USER_COL_COMMENTS c 
    ON t.TABLE_NAME = c.TABLE_NAME 
    AND t.COLUMN_NAME = c.COLUMN_NAME
ORDER BY t.TABLE_NAME, t.COLUMN_ID;
```

### 3. Primary Key 조회

```sql
SELECT 
    c.TABLE_NAME,
    c.COLUMN_NAME
FROM USER_CONS_COLUMNS c
JOIN USER_CONSTRAINTS k 
    ON c.CONSTRAINT_NAME = k.CONSTRAINT_NAME
    AND c.TABLE_NAME = k.TABLE_NAME
WHERE k.CONSTRAINT_TYPE = 'P'
ORDER BY c.TABLE_NAME, c.POSITION;
```

### 4. Foreign Key 관계 조회

```sql
SELECT 
    a.TABLE_NAME AS CHILD_TABLE,
    a.COLUMN_NAME AS CHILD_COLUMN,
    c_pk.TABLE_NAME AS PARENT_TABLE,
    b.COLUMN_NAME AS PARENT_COLUMN
FROM USER_CONS_COLUMNS a
JOIN USER_CONSTRAINTS c 
    ON a.CONSTRAINT_NAME = c.CONSTRAINT_NAME
    AND a.TABLE_NAME = c.TABLE_NAME
JOIN USER_CONSTRAINTS c_pk 
    ON c.R_OWNER = c_pk.OWNER
    AND c.R_CONSTRAINT_NAME = c_pk.CONSTRAINT_NAME
JOIN USER_CONS_COLUMNS b 
    ON c_pk.CONSTRAINT_NAME = b.CONSTRAINT_NAME
    AND c_pk.TABLE_NAME = b.TABLE_NAME
    AND b.POSITION = a.POSITION
WHERE c.CONSTRAINT_TYPE = 'R'
ORDER BY a.TABLE_NAME, a.POSITION;
```

---

## 사용 방법

1. 위 SQL 쿼리들을 Oracle DB에서 실행
2. 결과를 복사하여 프롬프트 템플릿에 붙여넣기
3. LLM에게 프롬프트 제공
4. 생성된 Mermaid ERD 코드를 `ERD.mmd` 파일로 저장
5. GitHub에 업로드하여 자동 렌더링

---

## GitHub 업로드 방법

### 방법 1: Git 명령어 사용

```powershell
# 1. 파일 추가
git add ERD.mmd

# 2. 커밋
git commit -m "Add ERD diagram"

# 3. GitHub에 푸시
git push
```

### 방법 2: GitHub 웹 인터페이스 사용

1. GitHub 저장소로 이동
2. "Add file" → "Upload files" 클릭
3. `ERD.mmd` 파일을 드래그 앤 드롭
4. "Commit changes" 클릭

### GitHub에서 확인

- GitHub는 `.mmd` 파일과 마크다운 파일 내의 Mermaid 코드 블록을 자동으로 렌더링합니다
- 파일을 클릭하면 자동으로 다이어그램이 표시됩니다

---

## 참고 자료

- Mermaid ERD 문법: https://mermaid.js.org/syntax/entityRelationshipDiagram.html
- GitHub Mermaid 지원: https://github.blog/2022-02-14-include-diagrams-markdown-files-mermaid/
