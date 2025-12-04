# Oracle Bequeath 오류 해결 가이드

## 🔍 문제 진단

터미널 출력에서 다음 오류가 발생했습니다:
```
오류: NotSupportedError: DPY-3001: bequeath is only supported in python-oracledb thick mode
```

**원인**: Python 드라이버가 로컬(Bequeath) 접속으로 연결을 시도하고 있어서 발생하는 문제입니다.

---

## ✅ 해결 방법

### 1. `.env` 파일 확인

프로젝트 루트 디렉토리의 `.env` 파일에 다음 5개 항목이 **정확히** 설정되어 있는지 확인하세요:

```env
ORACLE_USER=campus_24K_LG3_DX7_p3_4
ORACLE_PASSWORD=smhrd4
ORACLE_HOST=project-db-campus.smhrd.com
ORACLE_PORT=1524
ORACLE_SERVICE_NAME=MAPPP
```

**중요**: 
- ✅ 키 이름이 정확해야 합니다 (`ORACLE_USER`, `ORACLE_PASSWORD` 등)
- ✅ 모든 값이 채워져 있어야 합니다
- ✅ USER가 비어있으면 `.env` 파일을 읽지 못하는 것입니다

---

### 2. 직접 연결 테스트 (Django 없이)

먼저 Django 없이 Oracle에 직접 연결하여 Thin 모드가 작동하는지 확인하세요:

```powershell
python test_oracle.py
```

이 스크립트는:
- ✅ `oracledb`를 Thin 모드로 사용 (Thick 모드 사용 안 함)
- ✅ DSN을 명시적으로 지정 (`host:port/service_name` 형식)
- ✅ `init_oracle_client()`를 호출하지 않음

**예상 출력 (성공 시)**:
```
============================================================
Oracle 데이터베이스 연결 확인 (Thin 모드)
============================================================

연결 설정:
  USER: campus_24K_LG3_DX7_p3_4
  DSN:  project-db-campus.smhrd.com:1524/MAPPP
  Host: project-db-campus.smhrd.com
  Port: 1524
  Service Name: MAPPP

연결 테스트 중...

============================================================
✅ 연결 성공!
============================================================
```

---

### 3. Django 연결 테스트

직접 연결 테스트가 성공하면, Django를 통한 연결을 테스트합니다:

```powershell
python check_connection.py
```

---

### 4. oracledb 버전 확인

문제가 계속되면 oracledb 버전을 확인하세요:

```powershell
pip show oracledb
```

버전이 너무 낮으면 (1.x 또는 2.x) 업데이트:

```powershell
pip install --upgrade oracledb
```

---

## 🔧 핵심 원칙

### ✅ 올바른 방법 (Thin 모드)

```python
import oracledb

# DSN을 명시적으로 지정 (필수!)
dsn = f"{host}:{port}/{service_name}"

conn = oracledb.connect(
    user=user,
    password=password,
    dsn=dsn,  # 이게 있어야 Thin 모드로 연결
)
```

### ❌ 잘못된 방법 (Bequeath 모드 시도)

```python
# DSN을 지정하지 않으면 Bequeath 모드로 시도
conn = oracledb.connect(
    user=user,
    password=password,
    # dsn 없음 - 이러면 Bequeath 모드로 시도해서 오류 발생!
)
```

```python
# init_oracle_client()를 호출하면 Thick 모드로 전환
oracledb.init_oracle_client()  # 이건 사용하지 마세요!
```

---

## 📝 Django 설정 확인

`config/settings.py`의 데이터베이스 설정:

```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.oracle',
        'NAME': f'{db_host}:{db_port}/{db_service_name}',  # 전체 DSN 문자열
        'USER': db_user,
        'PASSWORD': db_password,
        'HOST': '',  # NAME에 이미 포함되어 있으므로 빈 문자열
        'PORT': '',  # NAME에 이미 포함되어 있으므로 빈 문자열
    }
}
```

---

## 🐛 문제 해결 체크리스트

- [ ] `.env` 파일이 프로젝트 루트에 있는가?
- [ ] `.env` 파일에 `ORACLE_USER`, `ORACLE_PASSWORD`, `ORACLE_HOST`, `ORACLE_PORT`, `ORACLE_SERVICE_NAME`이 모두 설정되어 있는가?
- [ ] `test_oracle.py`가 성공하는가? (Django 없이 직접 연결)
- [ ] oracledb 버전이 최신인가? (`pip show oracledb`로 확인)
- [ ] 코드에서 `init_oracle_client()`를 호출하지 않는가?
- [ ] DSN이 항상 명시적으로 지정되어 있는가?

---

## 🔗 관련 참고 자료

- Enable python-oracledb thick mode in Windows environment
- Install Oracle Instant Client and set PATH and variables
- Convert SID connection to service name in connect string
- Use EZCONNECT format host:port/service in python-oracledb

---

## 💡 추가 팁

만약 위의 모든 방법을 시도했는데도 여전히 같은 오류가 발생하면:

1. `check_connection.py` 전체 코드를 확인하여 Bequeath 모드를 요청하는 부분이 있는지 확인
2. Django Oracle 백엔드의 내부 설정 확인
3. 학원에서 제공한 정확한 Service Name 값 확인


