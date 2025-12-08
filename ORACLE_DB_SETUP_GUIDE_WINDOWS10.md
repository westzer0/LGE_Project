# Windows 10 Oracle DB 환경 설정 가이드

집에서 Windows 10에서 현재와 동일한 Oracle DB 환경을 구성하기 위한 완전한 가이드입니다.

## 📋 프로젝트 개요

- **프로젝트명**: DX Project (LG 홈스타일링 프로젝트)
- **프레임워크**: Django 4.2.17
- **데이터베이스**: Oracle 11g XE (SID: xe)
- **Python 버전**: Python 3.x (가상환경 사용)

---

## 🔧 1. 필수 소프트웨어 설치

### 1.1 Python 설치
- Python 3.x 버전 설치 (권장: 3.8 이상)
- 설치 시 "Add Python to PATH" 옵션 체크

### 1.2 Oracle Instant Client 설치 (Windows 10)

**중요**: Oracle 11g XE는 Thin 모드를 지원하지 않으므로 **Thick 모드**를 사용해야 합니다.

#### 설치 방법:

1. **Oracle Instant Client 다운로드**
   - Oracle 공식 사이트에서 다운로드: https://www.oracle.com/database/technologies/instant-client/downloads.html
   - 버전: **Instant Client 19.x 또는 21.x** (Windows 64-bit)
   - 필요한 패키지: **Basic Package** 또는 **Basic Light Package**

2. **설치 경로**
   - 예: `C:\oracle\instantclient_19_23`
   - 또는 `C:\oracle\instantclient_21_3` (버전에 따라 다름)

3. **PATH 환경 변수 설정**
   - Windows 검색: "환경 변수" → "시스템 환경 변수 편집"
   - "환경 변수" 버튼 클릭
   - "시스템 변수"에서 `Path` 선택 → "편집"
   - Oracle Instant Client 경로 추가 (예: `C:\oracle\instantclient_19_23`)
   - 확인 후 **재시작 권장**

4. **검증**
   ```powershell
   # PowerShell에서 확인
   Test-Path C:\oracle\instantclient_19_23\oci.dll
   # True가 나와야 함
   ```

---

## 📦 2. 프로젝트 설정

### 2.1 프로젝트 클론/복사
```powershell
# 프로젝트 디렉토리로 이동
cd "C:\Users\134\Desktop\DX Project"
```

### 2.2 가상환경 생성 및 활성화
```powershell
# 가상환경 생성
python -m venv venv

# 가상환경 활성화 (PowerShell)
.\venv\Scripts\Activate.ps1

# 만약 실행 정책 오류가 나면:
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### 2.3 필수 패키지 설치
```powershell
# requirements.txt 설치
pip install -r requirements.txt
```

**requirements.txt 내용:**
```
asgiref==3.8.1
Django==4.2.17
sqlparse==0.5.3
tzdata==2025.2
openai>=1.0.0
python-dotenv>=1.0.0
djangorestframework>=3.14.0
oracledb>=1.4.0
```

---

## 🔐 3. 환경 변수 설정 (.env 파일)

프로젝트 루트 디렉토리에 `.env` 파일을 생성하고 다음 내용을 입력:

```env
# Django Secret Key (필수)
DJANGO_SECRET_KEY=django-insecure-8zb-1$0d6^f=&c@v8-l2-9b*9ydnp7k3m0-s_y8gljjkvtiyt8

# 카카오 API 키 (선택사항)
KAKAO_REST_API_KEY=your_kakao_rest_api_key_here
KAKAO_JS_KEY=your_kakao_js_key_here

# OpenAI API 키 (선택사항)
OPENAI_API_KEY=your_openai_api_key_here

# ============================================
# Oracle 데이터베이스 설정 (필수)
# ============================================
ORACLE_USER=campus_24K_LG3_DX7_p3_4
ORACLE_PASSWORD=smhrd4
ORACLE_HOST=project-db-campus.smhrd.com
ORACLE_PORT=1524
ORACLE_SID=xe

# Oracle Instant Client 경로 (Thick 모드 사용 시 필수)
# Windows 10에서 설치한 경로로 변경
# 예: C:\oracle\instantclient_19_23
# 또는 PATH에 추가한 경우 비워두어도 됨
ORACLE_INSTANT_CLIENT_PATH=C:\oracle\instantclient_19_23

# Oracle 사용 여부 (true로 설정)
USE_ORACLE=true
```

**중요 사항:**
- `ORACLE_PASSWORD`는 실제 비밀번호로 변경 필요
- `ORACLE_INSTANT_CLIENT_PATH`는 실제 설치 경로로 변경
- `.env` 파일은 `.gitignore`에 포함되어 있어 Git에 커밋되지 않음

---

## ⚙️ 4. Django 설정 (config/settings.py)

### 4.1 현재 설정 확인

현재 프로젝트는 **SQLite가 기본값**으로 설정되어 있습니다. Oracle을 사용하려면 `config/settings.py`를 수정해야 합니다.

### 4.2 Oracle DB 활성화 방법

`config/settings.py` 파일에서 다음 부분을 수정:

**현재 (SQLite 사용 중):**
```python
# SQLite 설정 (테스트용)
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}
```

**변경 후 (Oracle 사용):**
```python
# Oracle DB 설정 활성화
USE_ORACLE = os.environ.get('USE_ORACLE', 'False').lower() == 'true'
if USE_ORACLE:
    DATABASES = {
        "default": {
            "ENGINE": "api.db.oracle_backend",  # 커스텀 Oracle 백엔드 (Oracle 11g 지원)
            "NAME": ORACLE_SID,  # SID
            "USER": ORACLE_USER,
            "PASSWORD": ORACLE_PASSWORD,
            "HOST": ORACLE_HOST,
            "PORT": str(ORACLE_PORT),
        }
    }
else:
    # SQLite 설정 (테스트용)
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }
```

---

## 🗄️ 5. Oracle DB 연결 정보

### 5.1 연결 정보 요약

| 항목 | 값 |
|------|-----|
| **호스트** | `project-db-campus.smhrd.com` |
| **포트** | `1524` |
| **SID** | `xe` |
| **사용자명** | `campus_24K_LG3_DX7_p3_4` |
| **비밀번호** | `smhrd4` (실제 비밀번호로 변경 필요) |
| **DB 버전** | Oracle 11g XE |

### 5.2 연결 문자열 (DSN)

```
project-db-campus.smhrd.com:1524/xe
```

### 5.3 커스텀 Oracle 백엔드

프로젝트는 Oracle 11g 호환성을 위해 커스텀 백엔드를 사용합니다:
- 경로: `api/db/oracle_backend/base.py`
- Django 5.2의 버전 체크를 우회하여 Oracle 11g 지원

---

## 🚀 6. 실행 및 테스트

### 6.1 Oracle 연결 테스트

```powershell
# 가상환경 활성화 상태에서
python -c "from api.db.oracle_client import get_connection; conn = get_connection(); print('연결 성공!'); conn.close()"
```

### 6.2 Django 서버 실행

```powershell
# 마이그레이션 실행 (필요시)
python manage.py migrate

# 서버 실행
python manage.py runserver
```

### 6.3 문제 해결

#### 문제 1: `ORA-12154: TNS:could not resolve the connect identifier`
- **원인**: Oracle Instant Client가 제대로 설치되지 않음
- **해결**: PATH 환경 변수 확인, 재시작

#### 문제 2: `DPI-1047: Cannot locate a 64-bit Oracle Client library`
- **원인**: 32-bit/64-bit 불일치 또는 Instant Client 미설치
- **해결**: 64-bit Instant Client 설치 확인

#### 문제 3: `ORA-00942: table or view does not exist`
- **원인**: 테이블이 Oracle DB에 없음
- **해결**: `python manage.py migrate` 실행

---

## 📁 7. 프로젝트 구조 (중요 파일)

```
DX Project/
├── config/
│   └── settings.py          # Django 설정 (Oracle DB 설정 포함)
├── api/
│   ├── db/
│   │   ├── oracle_client.py  # Oracle 직접 연결 클라이언트
│   │   └── oracle_backend/   # Django 커스텀 Oracle 백엔드
│   │       ├── __init__.py
│   │       └── base.py
│   └── models.py            # Django 모델
├── oracle_init.py            # Oracle Instant Client 초기화
├── manage.py                 # Django 관리 스크립트
├── requirements.txt          # Python 패키지 목록
├── .env                      # 환경 변수 (생성 필요)
└── env.example               # 환경 변수 예시
```

---

## 🔄 8. SQLite ↔ Oracle 전환 방법

### Oracle 사용 시:
```powershell
# .env 파일에서
USE_ORACLE=true
```

### SQLite 사용 시 (테스트용):
```powershell
# .env 파일에서
USE_ORACLE=false
```

또는 `config/settings.py`에서 직접 SQLite 설정 사용

---

## 📝 9. LLM에게 전달할 핵심 정보 요약

다른 LLM에게 이 프로젝트의 Oracle DB 환경을 설명할 때 다음 정보를 전달하세요:

```
프로젝트: Django 4.2.17 기반, Oracle 11g XE 사용

Oracle DB 연결 정보:
- 호스트: project-db-campus.smhrd.com
- 포트: 1524
- SID: xe
- 사용자: campus_24K_LG3_DX7_p3_4
- 비밀번호: smhrd4 (또는 실제 비밀번호)

Windows 10 설정:
- Oracle Instant Client 19.x 또는 21.x 설치 필요 (Thick 모드)
- PATH 환경 변수에 Instant Client 경로 추가
- .env 파일에 ORACLE_INSTANT_CLIENT_PATH 설정

Django 설정:
- 커스텀 Oracle 백엔드 사용: api.db.oracle_backend
- Oracle 11g 호환성을 위해 버전 체크 우회
- USE_ORACLE=true 환경 변수로 Oracle 활성화

필수 패키지:
- oracledb>=1.4.0
- python-dotenv>=1.0.0
- Django==4.2.17
```

---

## ✅ 10. 체크리스트

집에서 환경 설정 시 다음을 확인하세요:

- [ ] Python 3.x 설치 완료
- [ ] Oracle Instant Client 설치 완료 (64-bit)
- [ ] PATH 환경 변수에 Instant Client 경로 추가
- [ ] 가상환경 생성 및 활성화
- [ ] `pip install -r requirements.txt` 실행 완료
- [ ] `.env` 파일 생성 및 Oracle 연결 정보 입력
- [ ] `ORACLE_INSTANT_CLIENT_PATH` 경로 확인
- [ ] `USE_ORACLE=true` 설정
- [ ] `config/settings.py`에서 Oracle DB 설정 활성화
- [ ] 연결 테스트 성공
- [ ] Django 서버 실행 성공

---

## 📞 추가 참고 자료

- `ORACLE_DB_TROUBLESHOOTING.md`: Oracle DB 문제 해결 가이드
- `env.example`: 환경 변수 예시 파일
- `README_ENV_SETUP.md`: 환경 설정 README (있는 경우)

---

**마지막 업데이트**: 2024년 12월




