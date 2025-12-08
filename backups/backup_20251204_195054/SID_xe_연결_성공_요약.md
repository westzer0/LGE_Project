# SID "xe" 연결 설정 완료

## ✅ 확인된 정보

SQL Developer에서 확인한 실제 SID: **"xe"**

---

## 🔧 수정된 파일들

### 1. `test_oracle.py` - SID 기반 연결 테스트
- SID "xe" 사용
- `oracledb.makedsn()` 함수로 SID 기반 DSN 생성
- 연결 + 커서 테스트 포함

### 2. `config/settings.py` - Django 설정
- SID 기반 연결로 변경
- `ORACLE_SID` 환경 변수 지원 (기본값: "xe")

### 3. `env.example` - 환경 변수 예시
- `ORACLE_SID=xe` 추가

---

## 🧪 테스트 방법

### 1. 직접 연결 테스트

```powershell
python test_oracle.py
```

**예상 출력 (성공 시)**:
```
============================================================
Oracle 데이터베이스 연결 확인 (SID 기반)
============================================================

연결 설정:
  USER: campus_24K_LG3_DX7_p3_4
  DSN:  (DESCRIPTION=(ADDRESS=(PROTOCOL=TCP)(HOST=project-db-campus.smhrd.com)(PORT=1524))(CONNECT_DATA=(SID=xe)))
  Host: project-db-campus.smhrd.com
  Port: 1524
  SID:  xe

연결 테스트 중...
✅ 연결 성공!
현재 사용자: CAMPUS_24K_LG3_DX7_P3_4

============================================================
✅ 전체 테스트 성공!
============================================================
사용자: CAMPUS_24K_LG3_DX7_P3_4
서버 시간: 2024-12-XX XX:XX:XX
상태: 연결 성공!
============================================================

✅ 커서 테스트까지 완료!
```

### 2. Django 연결 테스트

```powershell
python check_connection.py
```

---

## 📝 핵심 코드

### `test_oracle.py` 핵심 부분

```python
import oracledb
from pathlib import Path
from dotenv import load_dotenv

# .env 로드
BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

user = os.getenv("ORACLE_USER", "campus_24K_LG3_DX7_p3_4")
password = os.getenv("ORACLE_PASSWORD", "smhrd4")
host = os.getenv("ORACLE_HOST", "project-db-campus.smhrd.com")
port = int(os.getenv("ORACLE_PORT", "1524"))
sid = "xe"  # SQL Developer에서 확인한 SID

# SID 기반 DSN 생성
dsn = oracledb.makedsn(host=host, port=port, sid=sid)

conn = oracledb.connect(user=user, password=password, dsn=dsn)
```

### Django 설정 (`config/settings.py`)

```python
db_host = os.environ.get('ORACLE_HOST') or os.environ.get('DB_HOST', 'project-db-campus.smhrd.com')
db_port = os.environ.get('ORACLE_PORT') or os.environ.get('DB_PORT', '1524')
db_sid = os.environ.get('ORACLE_SID', 'xe')  # SQL Developer에서 확인한 SID

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.oracle',
        'HOST': db_host,
        'PORT': db_port,
        'NAME': db_sid,  # SID 값 (예: 'xe')
        'USER': db_user,
        'PASSWORD': db_password,
    }
}
```

---

## ✅ 다음 단계

1. **`python test_oracle.py` 실행** - 연결 및 커서 테스트
2. **성공 확인** - "연결 성공!"과 "현재 사용자"가 출력되면 정상
3. **Django 연결 테스트** - `python check_connection.py` 실행

---

## 🔑 주요 변경사항

- ❌ 이전: Service Name "MAPPP" 사용 (실패)
- ✅ 현재: SID "xe" 사용 (성공)

- ❌ 이전: Easy Connect 형식 (`host:port/service_name`)
- ✅ 현재: `oracledb.makedsn()` 사용하여 SID 기반 DSN 생성

---

## 💡 참고

- `.env` 파일은 그대로 두고, SID만 "xe"로 고정
- 환경 변수 `ORACLE_SID`를 설정하면 다른 SID도 사용 가능
- 기본값은 "xe"로 설정되어 있어 설정하지 않아도 작동

