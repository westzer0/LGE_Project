# Oracle DB 환경 설정 - 빠른 참조 (LLM용)

다른 LLM에게 전달할 때 사용하는 간단한 요약입니다.

---

## 🎯 프로젝트 개요

- **프레임워크**: Django 4.2.17
- **데이터베이스**: Oracle 11g XE
- **OS**: Windows 10
- **Python**: 3.x

---

## 🔌 Oracle DB 연결 정보

```python
ORACLE_USER = 'campus_24K_LG3_DX7_p3_4'
ORACLE_PASSWORD = 'smhrd4'  # 실제 비밀번호로 변경 필요
ORACLE_HOST = 'project-db-campus.smhrd.com'
ORACLE_PORT = 1524
ORACLE_SID = 'xe'
```

**연결 문자열**: `project-db-campus.smhrd.com:1524/xe`

---

## 📦 필수 패키지

```txt
Django==4.2.17
oracledb>=1.4.0
python-dotenv>=1.0.0
djangorestframework>=3.14.0
```

---

## ⚙️ Django 설정 (config/settings.py)

### Oracle DB 활성화 코드:

```python
# Oracle DB 설정
ORACLE_USER = os.environ.get('ORACLE_USER', 'campus_24K_LG3_DX7_p3_4')
ORACLE_PASSWORD = os.environ.get('ORACLE_PASSWORD', 'smhrd4')
ORACLE_HOST = os.environ.get('ORACLE_HOST', 'project-db-campus.smhrd.com')
ORACLE_PORT = int(os.environ.get('ORACLE_PORT', '1524'))
ORACLE_SID = os.environ.get('ORACLE_SID', 'xe')

# Oracle DB 설정 활성화
USE_ORACLE = os.environ.get('USE_ORACLE', 'False').lower() == 'true'
if USE_ORACLE:
    DATABASES = {
        "default": {
            "ENGINE": "api.db.oracle_backend",  # 커스텀 백엔드 (Oracle 11g 지원)
            "NAME": ORACLE_SID,
            "USER": ORACLE_USER,
            "PASSWORD": ORACLE_PASSWORD,
            "HOST": ORACLE_HOST,
            "PORT": str(ORACLE_PORT),
        }
    }
```

---

## 🔧 Windows 10 필수 설정

### 1. Oracle Instant Client 설치
- **버전**: 19.x 또는 21.x (64-bit)
- **설치 경로 예시**: `C:\oracle\instantclient_19_23`
- **PATH 환경 변수에 추가 필요**

### 2. .env 파일 설정

```env
USE_ORACLE=true
ORACLE_USER=campus_24K_LG3_DX7_p3_4
ORACLE_PASSWORD=smhrd4
ORACLE_HOST=project-db-campus.smhrd.com
ORACLE_PORT=1524
ORACLE_SID=xe
ORACLE_INSTANT_CLIENT_PATH=C:\oracle\instantclient_19_23
```

---

## 🗂️ 커스텀 Oracle 백엔드

- **경로**: `api/db/oracle_backend/base.py`
- **목적**: Oracle 11g 호환성 (Django 5.2 버전 체크 우회)
- **사용 이유**: Oracle 11g XE는 IDENTITY 컬럼 미지원

---

## 🔍 주요 파일 위치

- `config/settings.py` - Django 설정
- `api/db/oracle_client.py` - Oracle 직접 연결 클라이언트
- `api/db/oracle_backend/` - 커스텀 Django Oracle 백엔드
- `oracle_init.py` - Oracle Instant Client 초기화
- `.env` - 환경 변수 (생성 필요)

---

## ⚠️ 중요 사항

1. **Thick 모드 필수**: Oracle 11g XE는 Thin 모드 미지원
2. **PATH 설정**: Oracle Instant Client를 PATH에 추가해야 함
3. **환경 변수**: `USE_ORACLE=true`로 설정해야 Oracle 사용
4. **비밀번호**: 실제 비밀번호로 변경 필요

---

## 🚀 빠른 시작 명령어

```powershell
# 가상환경 활성화
.\venv\Scripts\Activate.ps1

# 패키지 설치
pip install -r requirements.txt

# .env 파일 생성 (위 내용 참고)

# 연결 테스트
python -c "from api.db.oracle_client import get_connection; conn = get_connection(); print('OK'); conn.close()"

# Django 서버 실행
python manage.py runserver
```

---

**상세 가이드**: `ORACLE_DB_SETUP_GUIDE_WINDOWS10.md` 참고




