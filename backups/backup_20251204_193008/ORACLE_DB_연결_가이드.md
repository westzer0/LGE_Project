# Oracle 데이터베이스 연결 가이드

## 📋 연결 정보

| 항목 | 값 |
|------|-----|
| DB Type | Oracle |
| Name | MAPPP |
| USER (Schema Name) | campus_24K_LG3_DX7_p3_4 |
| PASSWORD | smhrd4 |
| HOST (URL) | project-db-campus.smhrd.com |
| PORT | 1524 |

---

## 🔧 SQL Developer 연결 방법

### 1. SQL Developer 실행
- 다운로드한 `sqldeveloper-23.1.1.345.2114-x64` 폴더에서 `sqldeveloper.exe` 실행

### 2. 새 연결 생성
1. **Connections** 패널에서 우클릭 → **New Connection** 선택
2. 다음 정보 입력:
   - **Connection Name**: `MAPPP` (원하는 이름)
   - **Username**: `campus_24K_LG3_DX7_p3_4`
   - **Password**: `smhrd4`
   - **Connection Type**: `Basic`
   - **Hostname**: `project-db-campus.smhrd.com`
   - **Port**: `1524`
   - **Service name**: `MAPPP` (또는 SID: `MAPPP`)

### 3. 연결 테스트
- **Test** 버튼 클릭하여 연결 확인
- 성공 시 "Status: Success" 메시지 표시

### 4. 연결 저장 및 접속
- **Save** 버튼 클릭하여 연결 정보 저장
- **Connect** 버튼 클릭하여 데이터베이스에 접속

---

## 🐍 Django 프로젝트 연결 설정

### ✅ 설정 완료 사항

`config/settings.py` 파일에 Oracle 데이터베이스 연결이 설정되어 있습니다:

```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.oracle',
        'NAME': 'MAPPP',  # Service Name
        'USER': 'campus_24K_LG3_DX7_p3_4',
        'PASSWORD': 'smhrd4',
        'HOST': 'project-db-campus.smhrd.com',
        'PORT': '1524',
    }
}
```

### 📦 필요한 패키지

Oracle 연결을 위해 다음 패키지가 설치되어 있습니다:
- `oracledb` (또는 `cx_Oracle`)

### 🔍 연결 테스트 방법

#### 방법 1: Django 관리 명령어 사용
```bash
python manage.py dbshell
```

#### 방법 2: Python 스크립트 사용
```bash
python test_oracle_connection.py
```

#### 방법 3: Django Shell 사용
```bash
python manage.py shell
```
```python
from django.db import connection
cursor = connection.cursor()
cursor.execute("SELECT 1 FROM DUAL")
print(cursor.fetchone())
```

---

## ⚠️ 문제 해결

### 연결 오류가 발생하는 경우

1. **Oracle Instant Client 확인**
   - `oracledb` 패키지는 기본적으로 Thin 모드를 사용하므로 별도의 Oracle Instant Client가 필요 없습니다.
   - 만약 Thick 모드를 사용하려면 Oracle Instant Client를 설치해야 합니다.

2. **방화벽 확인**
   - `project-db-campus.smhrd.com:1524` 포트가 열려있는지 확인

3. **네트워크 연결 확인**
   - 데이터베이스 서버에 접근 가능한지 확인

4. **인증 정보 확인**
   - 사용자명, 비밀번호, 서비스 이름이 정확한지 확인

### Django 마이그레이션 실행

연결이 성공하면 Django 모델을 데이터베이스에 적용할 수 있습니다:

```bash
python manage.py makemigrations
python manage.py migrate
```

---

## 📝 참고 사항

- **Service Name vs SID**: 
  - Service Name: `MAPPP` (현재 설정)
  - SID를 사용해야 하는 경우 `NAME` 필드에 SID 값을 입력

- **Connection String 형식**:
  - Django는 `HOST`, `PORT`, `NAME`을 별도로 지정하거나
  - `NAME`에 `HOST:PORT/SERVICE_NAME` 형식으로 통합할 수 있습니다

---

## ✅ 연결 확인 체크리스트

- [ ] SQL Developer에서 연결 성공
- [ ] Django `python manage.py dbshell` 명령어 실행 성공
- [ ] `test_oracle_connection.py` 스크립트 실행 성공
- [ ] Django 마이그레이션 실행 가능

