# DPY-3010 오류 해결: Thick 모드 사용

## 🔍 문제 원인

**에러**: `DPY-3010: connections to this database server version are not supported by python-oracledb in thin mode`

**의미**: 
- Oracle DB 버전이 11g XE 등 낮은 버전
- python-oracledb Thin 모드는 DB 12.1 이상만 지원
- 따라서 **Thick 모드**를 사용해야 함

---

## ✅ 해결 방법

### 1단계: Oracle Instant Client 설치

자세한 내용은 `ORACLE_INSTANT_CLIENT_설치_가이드.md` 참조

**요약**:
1. Oracle 공식 사이트에서 Instant Client 다운로드
   - https://www.oracle.com/database/technologies/instant-client/winx64-64-downloads.html
   - Basic Package (ZIP) 다운로드

2. 압축 해제
   ```
   C:\oracle\instantclient_19_23
   ```
   (또는 원하는 경로)

3. .env 파일에 경로 설정
   ```env
   ORACLE_INSTANT_CLIENT_PATH=C:\oracle\instantclient_19_23
   ```

### 2단계: Thick 모드 테스트

```powershell
python test_oracle_thick.py
```

**성공 시 출력**:
```
✅ Thick 모드 활성화 성공!
✅ Thick 모드로 연결 성공!
현재 사용자: CAMPUS_24K_LG3_DX7_P3_4
✅ 커서 테스트까지 완료!
```

### 3단계: Django 설정 (자동 완료)

다음 파일들이 이미 설정되어 있습니다:
- ✅ `oracle_init.py` - Oracle 초기화 모듈
- ✅ `manage.py` - Oracle 초기화 추가
- ✅ `config/wsgi.py` - Oracle 초기화 추가

---

## 📝 생성된 파일들

1. **`test_oracle_thick.py`**
   - Thick 모드 연결 테스트 스크립트
   - PATH나 .env에서 Instant Client 경로 자동 감지

2. **`oracle_init.py`**
   - Oracle Instant Client 초기화 모듈
   - Django에서 자동으로 사용

3. **`ORACLE_INSTANT_CLIENT_설치_가이드.md`**
   - 상세한 설치 가이드

4. **`env.example`**
   - `ORACLE_INSTANT_CLIENT_PATH` 추가

---

## 🔧 설정 방법

### .env 파일 설정

`.env` 파일에 다음 추가:
```env
ORACLE_INSTANT_CLIENT_PATH=C:\oracle\instantclient_19_23
```

### 또는 시스템 PATH 설정

시스템 환경 변수 PATH에 추가:
```
C:\oracle\instantclient_19_23
```

---

## 🧪 테스트 순서

1. **Oracle Instant Client 설치**
   - 다운로드 및 압축 해제
   - 경로 확인 (oci.dll 파일 존재 확인)

2. **.env 파일 설정**
   - `ORACLE_INSTANT_CLIENT_PATH` 추가

3. **Thick 모드 테스트**
   ```powershell
   python test_oracle_thick.py
   ```

4. **Django 연결 테스트**
   ```powershell
   python check_connection.py
   ```

---

## ✅ 체크리스트

- [ ] Oracle Instant Client 다운로드 및 설치
- [ ] `.env` 파일에 `ORACLE_INSTANT_CLIENT_PATH` 설정
- [ ] `python test_oracle_thick.py` 성공
- [ ] `python check_connection.py` 성공 (Django)

---

## 💡 참고사항

1. **초기화는 한 번만**: `init_oracle_client()`는 한 번만 호출되어야 합니다
   - `oracle_init.py`가 자동으로 처리합니다

2. **경로에 공백/한글 금지**: 경로에 공백이나 한글이 있으면 오류 발생 가능

3. **버전 호환성**: Instant Client 19c, 21c, 23c 모두 호환됩니다

---

## 🎯 핵심 요약

- ❌ **이전**: Thin 모드 사용 → DPY-3010 오류 (DB 버전 낮음)
- ✅ **현재**: Thick 모드 사용 → Oracle Instant Client 필요

- **Thin 모드**: DB 12.1 이상만 지원 (11g XE는 지원 안 함)
- **Thick 모드**: 모든 DB 버전 지원 (Instant Client 필요)

---

## 🔗 관련 문서

- `ORACLE_INSTANT_CLIENT_설치_가이드.md` - 상세 설치 가이드
- `test_oracle_thick.py` - Thick 모드 테스트 스크립트
- `oracle_init.py` - Django 초기화 모듈

