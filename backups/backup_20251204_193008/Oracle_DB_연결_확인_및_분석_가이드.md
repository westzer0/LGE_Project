# Oracle DB 연결 확인 및 분석 가이드

## 🔍 Oracle DB 연결 확인 방법

### 방법 1: 간단한 연결 테스트

프로젝트 루트에서 다음 명령어를 실행하세요:

```powershell
python -c "from api.db.oracle_client import fetch_one; result = fetch_one('SELECT USER, SYSDATE FROM DUAL'); print(f'✅ 연결 성공! 사용자: {result[0]}, 시간: {result[1]}')"
```

### 방법 2: 상세 연결 테스트 스크립트

다음 파일을 실행하세요:
- `check_connection.py` - Django ORM을 통한 연결 테스트
- `test_oracle_connection_simple.py` - 직접 연결 모듈 테스트

### 방법 3: Python 인터프리터에서 직접 확인

```python
# Python 인터프리터 실행
python

# 다음 코드 입력
from api.db.oracle_client import get_connection, fetch_one, fetch_all_dict

# 연결 테스트
result = fetch_one("SELECT USER, SYSDATE, '연결 성공!' FROM DUAL")
print(f"사용자: {result[0]}")
print(f"서버 시간: {result[1]}")
print(f"상태: {result[2]}")

# 테이블 목록 조회
tables = fetch_all_dict("SELECT table_name FROM user_tables ORDER BY table_name")
print(f"\n발견된 테이블: {len(tables)}개")
for t in tables:
    print(f"  - {t['TABLE_NAME']}")
```

---

## 📊 Oracle DB 데이터 분석 방법

### 분석 스크립트 실행

프로젝트 루트에서 다음 명령어를 실행하세요:

```powershell
python analyze_oracle_complete.py
```

실행 후 `ORACLE_DB_ANALYSIS_RESULT.md` 파일이 생성되며, 다음 정보가 포함됩니다:
- 연결 상태
- 모든 테이블 목록
- 각 테이블의 컬럼 정보
- 데이터 개수
- 샘플 데이터
- 숫자형 컬럼 통계

### 수동 분석 (Python 인터프리터)

```python
from api.db.oracle_client import fetch_all_dict, fetch_one

# 1. 모든 테이블 목록
tables = fetch_all_dict("SELECT table_name FROM user_tables ORDER BY table_name")
for t in tables:
    table_name = t['TABLE_NAME']
    
    # 행 개수
    count = fetch_one(f"SELECT COUNT(*) FROM {table_name}")[0]
    print(f"{table_name}: {count}개 행")
    
    # 컬럼 정보
    columns = fetch_all_dict(f"""
        SELECT column_name, data_type, nullable
        FROM user_tab_columns
        WHERE table_name = '{table_name}'
        ORDER BY column_id
    """)
    print(f"  컬럼: {len(columns)}개")
    for col in columns[:5]:  # 처음 5개만
        print(f"    - {col['COLUMN_NAME']} ({col['DATA_TYPE']})")
    
    # 샘플 데이터
    if count > 0:
        samples = fetch_all_dict(f"SELECT * FROM {table_name} WHERE ROWNUM <= 3")
        print(f"  샘플 데이터: {len(samples)}개")
        if samples:
            print(f"    첫 번째 행: {list(samples[0].keys())[:3]}")  # 처음 3개 컬럼만
    print()
```

---

## 🔧 연결 정보 확인

연결 정보는 `api/db/oracle_client.py` 파일에서 확인할 수 있습니다:

```python
ORACLE_USER = "campus_24K_LG3_DX7_p3_4"
ORACLE_HOST = "project-db-campus.smhrd.com"
ORACLE_PORT = 1524
ORACLE_SID = "xe"
```

또는 `.env` 파일에서 환경 변수로 설정할 수 있습니다:
- `ORACLE_USER`
- `ORACLE_PASSWORD`
- `ORACLE_HOST`
- `ORACLE_PORT`

---

## 📝 분석 결과 확인

분석 스크립트를 실행하면 다음 파일이 생성됩니다:
- `ORACLE_DB_ANALYSIS_RESULT.md` - 마크다운 형식의 상세 분석 결과

이 파일에는 다음이 포함됩니다:
1. 연결 테스트 결과
2. 테이블 목록 및 행 개수
3. 각 테이블의 상세 정보:
   - 컬럼 구조
   - 데이터 개수
   - 샘플 데이터
   - 숫자형 컬럼 통계

---

## ❓ 문제 해결

### 연결이 안 될 때

1. **환경 변수 확인**
   ```powershell
   # .env 파일이 있는지 확인
   Test-Path .env
   ```

2. **Oracle 클라이언트 확인**
   - Oracle Instant Client가 설치되어 있는지 확인
   - PATH에 oci.dll이 있는지 확인

3. **네트워크 확인**
   - `project-db-campus.smhrd.com:1524`에 접근 가능한지 확인
   - 방화벽 설정 확인

### 스크립트 실행 시 오류가 발생할 때

1. **모듈 import 오류**
   ```powershell
   pip install oracledb python-dotenv
   ```

2. **권한 오류**
   - Oracle 사용자 계정 권한 확인
   - 테이블 접근 권한 확인

---

## 🚀 빠른 시작

가장 빠른 확인 방법:

```powershell
# 1. 연결 테스트
python -c "from api.db.oracle_client import fetch_one; print(fetch_one('SELECT SYSDATE FROM DUAL'))"

# 2. 테이블 목록
python -c "from api.db.oracle_client import fetch_all_dict; tables = fetch_all_dict('SELECT table_name FROM user_tables'); print([t['TABLE_NAME'] for t in tables])"
```

성공하면 연결이 정상적으로 작동하는 것입니다!

