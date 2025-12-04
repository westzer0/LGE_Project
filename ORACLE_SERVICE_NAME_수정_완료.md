# Oracle Service Name 연결 수정 완료

## 🔧 수정 내용

### 1. `config/settings.py` - Service Name 형식으로 변경
- **이전 문제**: 
  - MAPPP를 SID로 인식하여 `ORA-12505` 오류 발생
  - HOST/PORT가 비어있어 bequeath 모드 시도 오류 발생

- **수정 후**:
  - NAME 필드에 `HOST:PORT/SERVICE_NAME` 형식 사용 (예: `project-db-campus.smhrd.com:1524/MAPPP`)
  - Service Name으로 정확하게 연결됩니다
  - ORACLE_* 형식과 기존 DB_* 형식 모두 지원

### 2. `env.example` - 환경 변수 형식 업데이트
- `ORACLE_USER`, `ORACLE_PASSWORD`, `ORACLE_HOST`, `ORACLE_PORT`, `ORACLE_SERVICE_NAME` 형식 추가
- 기존 `DB_*` 형식도 호환성을 위해 유지

### 3. `check_connection.py` - 출력 개선
- Service Name 정보도 함께 출력하도록 개선

---

## ✅ 확인 사항

### `.env` 파일 설정 확인

프로젝트 루트 디렉토리에 `.env` 파일이 있고, 다음 형식으로 설정되어 있는지 확인하세요:

```env
# Oracle 데이터베이스 설정 (ORACLE_* 형식 - 권장)
ORACLE_USER=campus_24K_LG3_DX7_p3_4
ORACLE_PASSWORD=your_password_here
ORACLE_HOST=project-db-campus.smhrd.com
ORACLE_PORT=1524
ORACLE_SERVICE_NAME=MAPPP

# 또는 기존 형식 (호환성 유지)
DB_USER=campus_24K_LG3_DX7_p3_4
DB_PASSWORD=your_password_here
DB_HOST=project-db-campus.smhrd.com
DB_PORT=1524
DB_SERVICE_NAME=MAPPP
```

**중요**: 
- ✅ `ORACLE_SERVICE_NAME` 또는 `DB_SERVICE_NAME`이 **반드시** 설정되어 있어야 합니다
- ✅ `USER`, `PASSWORD`, `HOST`, `PORT`, `SERVICE_NAME` 모두 채워져 있어야 합니다

---

## 🧪 테스트 방법

### 연결 테스트 실행

```powershell
# 가상환경 활성화 (필요한 경우)
.\venv\Scripts\activate

# 연결 테스트
python check_connection.py
```

### 예상 출력 (성공 시)

```
============================================================
Oracle 데이터베이스 연결 확인
============================================================

연결 설정:
  NAME (DSN): project-db-campus.smhrd.com:1524/MAPPP
  USER: campus_24K_LG3_DX7_p3_4
  HOST: (NAME에 포함됨)
  PORT: (NAME에 포함됨)
  Service Name: MAPPP (NAME에서 추출)

연결 테스트 중...

============================================================
✅ 연결 성공!
============================================================
사용자: CAMPUS_24K_LG3_DX7_P3_4
서버 시간: 2024-12-XX XX:XX:XX
상태: 연결 성공!
============================================================
```

---

## 🔍 문제 해결

### 오류가 계속 발생하는 경우

1. **`.env` 파일 확인**
   - 프로젝트 루트 디렉토리에 `.env` 파일이 있는지 확인
   - 모든 필수 항목이 올바르게 설정되어 있는지 확인
   - 비밀번호에 특수문자가 있다면 따옴표로 감싸지 마세요

2. **환경 변수 확인**
   ```powershell
   python -c "import os; from dotenv import load_dotenv; load_dotenv(); print('USER:', os.environ.get('ORACLE_USER') or os.environ.get('DB_USER')); print('SERVICE_NAME:', os.environ.get('ORACLE_SERVICE_NAME') or os.environ.get('DB_SERVICE_NAME'))"
   ```

3. **Service Name 확인**
   - 학원에서 공지한 정확한 Service Name 값이 `MAPPP`가 맞는지 확인
   - 만약 다른 값이라면 `.env` 파일의 `ORACLE_SERVICE_NAME` 값을 수정하세요

4. **네트워크 연결 확인**
   - 방화벽이나 VPN 설정 확인
   - `project-db-campus.smhrd.com:1524`에 접근 가능한지 확인

---

## 📝 기술적 세부사항

### Django Oracle 백엔드 연결 방식

**Service Name 형식**:
```python
'NAME': 'HOST:PORT/SERVICE_NAME'  # 예: 'project-db-campus.smhrd.com:1524/MAPPP'
```

**이 방식의 장점**:
- ✅ SID 대신 Service Name 사용 가능
- ✅ bequeath 모드 오류 방지
- ✅ 원격 연결 안정성 향상

**주의사항**:
- NAME에 전체 DSN을 포함하면 HOST/PORT는 빈 문자열로 설정
- Service Name은 반드시 `/` 앞에 호스트/포트 정보와 함께 지정

---

## ✅ 다음 단계

1. `.env` 파일이 올바르게 설정되어 있는지 확인
2. `python check_connection.py` 실행하여 연결 테스트
3. 연결 성공 시 Django 앱이 정상 작동하는지 확인

문제가 계속되면 학원에서 제공한 정확한 Service Name 값을 확인하여 알려주세요!
