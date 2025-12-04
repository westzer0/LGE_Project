# Oracle Instant Client 설치 가이드 (Windows)

## 🔍 문제 상황

에러: `DPY-3010: connections to this database server version are not supported by python-oracledb in thin mode`

**의미**: Oracle DB 버전이 낮아서 (11g XE 등) Thin 모드가 지원되지 않습니다.

**해결**: Oracle Instant Client를 설치하고 Thick 모드를 사용해야 합니다.

---

## 📦 Oracle Instant Client 설치

### 1단계: 다운로드

1. **Oracle 공식 사이트 접속**
   - https://www.oracle.com/database/technologies/instant-client/winx64-64-downloads.html

2. **다운로드할 패키지**
   - **Basic Package (ZIP)**: 필수
     - 예: `instantclient-basic-windows.x64-19.23.0.0.0dbru.zip`
     - 또는 21c, 23c 버전도 가능

3. **선택 사항 (필요한 경우)**
   - SQL*Plus Package: SQL*Plus 도구 필요 시
   - Tools Package: 추가 도구 필요 시

### 2단계: 압축 해제 및 설치

1. **압축 해제 위치**
   ```
   C:\oracle\instantclient_19_23
   ```
   또는 원하는 경로 (예: `C:\oracle\instantclient_21_8`)

2. **중요**: 
   - 경로에 한글이나 공백이 없어야 합니다
   - 관리자 권한으로 폴더 생성 권장

### 3단계: PATH 환경 변수 설정 (선택 사항)

**방법 1: 시스템 PATH에 추가 (권장)**
1. Windows 검색에서 "환경 변수" 검색
2. "시스템 환경 변수 편집" 선택
3. "환경 변수" 버튼 클릭
4. "시스템 변수"의 "Path" 선택 → "편집"
5. "새로 만들기" → Instant Client 경로 추가
   ```
   C:\oracle\instantclient_19_23
   ```
6. 모든 창에서 "확인" 클릭

**방법 2: .env 파일에 경로 설정**
`.env` 파일에 추가:
```env
ORACLE_INSTANT_CLIENT_PATH=C:\oracle\instantclient_19_23
```

---

## 🧪 설치 확인

### 방법 1: oci.dll 파일 확인
```
C:\oracle\instantclient_19_23\oci.dll
```
이 파일이 존재하면 설치 완료입니다.

### 방법 2: Python 스크립트로 확인
```powershell
python test_oracle_thick.py
```

---

## 📝 Django 설정 (Thick 모드)

### settings.py에 추가

프로젝트 루트에 `oracle_init.py` 파일 생성:

```python
# oracle_init.py
import os
import oracledb
from pathlib import Path

# Django settings가 로드되기 전에 실행되도록
# manage.py나 wsgi.py에서 import

def init_oracle_client():
    """Oracle Instant Client 초기화 (한 번만 실행)"""
    instant_client_path = os.environ.get('ORACLE_INSTANT_CLIENT_PATH')
    
    if instant_client_path:
        try:
            oracledb.init_oracle_client(lib_dir=instant_client_path)
        except Exception as e:
            # 이미 초기화된 경우 무시
            if "already initialized" not in str(e).lower():
                raise
    else:
        # PATH에서 자동으로 찾기 시도
        import sys
        path_dirs = os.environ.get("PATH", "").split(os.pathsep)
        for path_dir in path_dirs:
            oci_dll = os.path.join(path_dir, "oci.dll")
            if os.path.exists(oci_dll):
                try:
                    oracledb.init_oracle_client(lib_dir=path_dir)
                    break
                except Exception as e:
                    if "already initialized" not in str(e).lower():
                        continue
```

### manage.py 수정

```python
# manage.py 맨 위에 추가
import os
import sys

# Oracle Instant Client 초기화 (가장 먼저)
try:
    from oracle_init import init_oracle_client
    init_oracle_client()
except ImportError:
    pass  # oracle_init.py가 없으면 스킵

# ... 기존 코드 ...
```

### config/wsgi.py 수정

```python
# config/wsgi.py 맨 위에 추가
import os

# Oracle Instant Client 초기화 (가장 먼저)
try:
    from oracle_init import init_oracle_client
    init_oracle_client()
except ImportError:
    pass

# ... 기존 코드 ...
```

---

## ✅ 체크리스트

- [ ] Oracle Instant Client 다운로드
- [ ] 압축 해제 (예: `C:\oracle\instantclient_19_23`)
- [ ] `oci.dll` 파일 존재 확인
- [ ] PATH 환경 변수 설정 또는 `.env` 파일에 경로 추가
- [ ] `python test_oracle_thick.py` 실행하여 연결 테스트
- [ ] Django 설정 업데이트 (선택 사항)

---

## 🔗 참고 링크

- Oracle Instant Client 다운로드: https://www.oracle.com/database/technologies/instant-client/downloads.html
- python-oracledb Thick 모드 문서: https://python-oracledb.readthedocs.io/en/latest/user_guide/initialization.html#enabling-python-oracledb-thick-mode

---

## 💡 주의사항

1. **버전 호환성**: Instant Client 버전이 DB 서버 버전과 같을 필요는 없습니다
   - 19c, 21c, 23c 모두 호환됩니다

2. **초기화는 한 번만**: `init_oracle_client()`는 한 번만 호출해야 합니다

3. **경로에 공백/한글 금지**: 경로에 공백이나 한글이 있으면 오류가 발생할 수 있습니다



