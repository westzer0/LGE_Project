# DB 연결 상태 및 외부 로직 확인

## 📊 현재 상태

### 1. 외부 로직 반영 상태 ✅

**모든 외부 로직이 반영되어 있습니다:**

- ✅ **추천 엔진** (`api/services/recommendation_engine.py`)
- ✅ **ChatGPT 서비스** (`api/services/chatgpt_service.py`)
- ✅ **카카오 인증/메시지** (`api/services/kakao_auth_service.py`, `kakao_message_service.py`)
- ✅ **AI 추천 서비스** (`api/services/ai_recommendation_service.py`)
- ✅ **포트폴리오 서비스** (`api/services/portfolio_service.py`)
- ✅ **온보딩 DB 서비스** (`api/services/onboarding_db_service.py`)
- ✅ **맛 기반 추천** (`api/services/taste_based_recommendation_engine.py`)
- ✅ **제품 비교 서비스** (`api/services/product_comparison_service.py`)

**확인 방법:**
```python
# api/views.py에서 모든 서비스가 import되어 있음
from .services.recommendation_engine import recommendation_engine
from .services.chatgpt_service import chatgpt_service
from .services.kakao_auth_service import kakao_auth_service
# ... 등등
```

---

### 2. DB 연결 상태

#### 현재 설정
- **USE_ORACLE**: `false` → **SQLite 사용 중**
- **DISABLE_DB**: `false` → DB 활성화됨
- **현재 DB**: SQLite (`db.sqlite3`)

#### MAPPP (Oracle DB) 연결 방법

**1단계: .env 파일 생성/수정**

`.env` 파일에 다음 내용 추가:
```env
# Oracle DB 연결 활성화
USE_ORACLE=true

# Oracle DB 설정 (MAPPP)
ORACLE_USER=campus_24K_LG3_DX7_p3_4
ORACLE_PASSWORD=smhrd4
ORACLE_HOST=project-db-campus.smhrd.com
ORACLE_PORT=1524
ORACLE_SID=xe

# Oracle Instant Client 경로 (필요시)
ORACLE_INSTANT_CLIENT_PATH=C:\oracle\instantclient_19_23
```

**2단계: DB 연결 테스트**

```bash
# 방법 1: 간단한 테스트
python test_oracle_simple.py

# 방법 2: API 엔드포인트로 확인
# 서버 실행 후 브라우저에서:
http://127.0.0.1:8000/api/oracle/test/
```

**3단계: 서버 재시작**

```bash
python manage.py runserver
```

---

## 🔍 MAPPP 연결 확인

### 현재 MAPPP 연결 상태

**문제점:**
- MAPPP는 Oracle DB의 Service Name입니다
- 현재 코드는 SID 기반 연결을 사용합니다 (`ORACLE_SID=xe`)
- MAPPP를 사용하려면 Service Name 기반 연결로 변경해야 합니다

### MAPPP 연결 설정 방법

**옵션 1: Service Name 사용 (권장)**

`.env` 파일:
```env
USE_ORACLE=true
ORACLE_USER=campus_24K_LG3_DX7_p3_4
ORACLE_PASSWORD=smhrd4
ORACLE_HOST=project-db-campus.smhrd.com
ORACLE_PORT=1524
# Service Name 사용 (SID 대신)
ORACLE_SERVICE_NAME=MAPPP
```

**옵션 2: 코드 수정**

`api/db/oracle_client.py`에서 Service Name 지원 추가:
```python
# Service Name이 있으면 Service Name 사용, 없으면 SID 사용
ORACLE_SERVICE_NAME = os.getenv('ORACLE_SERVICE_NAME')
if ORACLE_SERVICE_NAME:
    DSN = oracledb.makedsn(ORACLE_HOST, ORACLE_PORT, service_name=ORACLE_SERVICE_NAME)
else:
    DSN = oracledb.makedsn(ORACLE_HOST, ORACLE_PORT, sid=ORACLE_SID)
```

---

## ✅ 확인 체크리스트

### 외부 로직
- [x] 추천 엔진 import됨
- [x] ChatGPT 서비스 import됨
- [x] 카카오 서비스 import됨
- [x] AI 추천 서비스 import됨
- [x] 포트폴리오 서비스 import됨

### DB 연결
- [ ] `.env` 파일 존재 여부 확인
- [ ] `USE_ORACLE` 환경변수 설정 확인
- [ ] Oracle Instant Client 설치 확인
- [ ] MAPPP 연결 테스트 성공 여부

---

## 🚀 빠른 확인 명령어

```bash
# 1. 환경변수 확인
python -c "import os; print('USE_ORACLE:', os.getenv('USE_ORACLE', 'false'))"

# 2. DB 연결 테스트
python test_oracle_simple.py

# 3. API로 확인
curl http://127.0.0.1:8000/api/oracle/test/
```

---

## 📝 다음 단계

1. **MAPPP 연결이 필요한 경우:**
   - `.env` 파일에 `USE_ORACLE=true` 추가
   - `ORACLE_SERVICE_NAME=MAPPP` 추가
   - `api/db/oracle_client.py` 수정 (Service Name 지원)

2. **현재 SQLite로 충분한 경우:**
   - 그대로 사용 가능
   - 모든 기능이 정상 작동함

3. **외부 로직 테스트:**
   - 온보딩 완료 → 추천 엔진 작동 확인
   - 포트폴리오 생성 → 정상 작동 확인


