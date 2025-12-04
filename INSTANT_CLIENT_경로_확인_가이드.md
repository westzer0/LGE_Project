# Oracle Instant Client 경로 확인 가이드

## 🔍 경로 확인 방법

### 상황: `C:\oraclexe\instantclient-basic-windows.x64-23.26.0.0.0`

이 경로는 압축 파일을 해제한 폴더 이름인 것 같습니다. 

**중요**: 실제 Instant Client 파일들(`oci.dll` 등)은 이 폴더 안에 바로 있거나, 하위 폴더에 있을 수 있습니다.

---

## ✅ 올바른 경로 찾기

### 방법 1: 파일 탐색기에서 확인

1. **파일 탐색기 열기**
   - `C:\oraclexe\instantclient-basic-windows.x64-23.26.0.0.0` 폴더 열기

2. **`oci.dll` 파일 찾기**
   - 이 폴더에 바로 `oci.dll` 파일이 있나요?
   - 또는 하위 폴더에 있나요?

3. **올바른 경로 확인**
   - `oci.dll` 파일이 있는 폴더 경로를 복사하세요
   - 예: `C:\oraclexe\instantclient-basic-windows.x64-23.26.0.0.0` (바로 여기)
   - 또는: `C:\oraclexe\instantclient-basic-windows.x64-23.26.0.0.0\instantclient_23_26` (하위 폴더)

### 방법 2: Python 스크립트로 확인

```powershell
python check_instant_client_path.py
```

이 스크립트가 자동으로 올바른 경로를 찾아줍니다.

### 방법 3: 수동 확인

PowerShell에서:

```powershell
# 경로 존재 확인
Test-Path "C:\oraclexe\instantclient-basic-windows.x64-23.26.0.0.0"

# oci.dll 파일 확인
Test-Path "C:\oraclexe\instantclient-basic-windows.x64-23.26.0.0.0\oci.dll"

# 폴더 내용 확인
Get-ChildItem "C:\oraclexe\instantclient-basic-windows.x64-23.26.0.0.0" | Select-Object Name
```

---

## 📁 일반적인 폴더 구조

### 올바른 구조 (바로 있음)
```
C:\oraclexe\instantclient-basic-windows.x64-23.26.0.0.0\
  ├── oci.dll          ← 이 파일이 여기 있어야 함!
  ├── oraociei23.dll
  ├── oraocci23.dll
  └── ... (기타 dll 파일들)
```

**이 경우 사용할 경로**:
```
C:\oraclexe\instantclient-basic-windows.x64-23.26.0.0.0
```

### 하위 폴더에 있는 경우
```
C:\oraclexe\instantclient-basic-windows.x64-23.26.0.0.0\
  └── instantclient_23_26\
      ├── oci.dll          ← 실제 파일들이 여기 있음
      ├── oraociei23.dll
      └── ...
```

**이 경우 사용할 경로**:
```
C:\oraclexe\instantclient-basic-windows.x64-23.26.0.0.0\instantclient_23_26
```

---

## 🔧 .env 파일 설정

올바른 경로를 찾았으면 `.env` 파일에 추가하세요:

```env
ORACLE_INSTANT_CLIENT_PATH=C:\oraclexe\instantclient-basic-windows.x64-23.26.0.0.0
```

또는 하위 폴더에 있다면:

```env
ORACLE_INSTANT_CLIENT_PATH=C:\oraclexe\instantclient-basic-windows.x64-23.26.0.0.0\instantclient_23_26
```

---

## 🧪 경로 확인 테스트

`.env` 파일에 경로를 추가한 후:

```powershell
python test_oracle_thick.py
```

**성공 메시지 예시**:
```
Oracle Instant Client 경로: C:\oraclexe\instantclient-basic-windows.x64-23.26.0.0.0
✅ Thick 모드 활성화 성공!
✅ Thick 모드로 연결 성공!
```

**실패 메시지 예시**:
```
❌ Thick 모드 활성화 실패: ...
확인 사항:
  1. Oracle Instant Client가 설치되어 있는지 확인
  2. ORACLE_INSTANT_CLIENT_PATH 환경 변수나 .env 파일에 경로가 올바른지 확인
  3. 경로에 oci.dll 파일이 있는지 확인
```

---

## 💡 권장 사항

### 경로 이름 변경 (선택 사항)

현재 폴더 이름이 너무 길고 복잡합니다. 더 간단하게 변경하는 것을 권장합니다:

1. **파일 탐색기에서**
   - `C:\oraclexe\instantclient-basic-windows.x64-23.26.0.0.0` 폴더 선택
   - 폴더 이름 변경: `instantclient_23_26` 또는 `instantclient`

2. **또는 새 위치로 복사**
   ```
   C:\oracle\instantclient_23_26
   ```

3. **.env 파일 업데이트**
   ```env
   ORACLE_INSTANT_CLIENT_PATH=C:\oracle\instantclient_23_26
   ```

---

## ✅ 체크리스트

- [ ] `C:\oraclexe\instantclient-basic-windows.x64-23.26.0.0.0` 폴더 확인
- [ ] `oci.dll` 파일 위치 확인 (바로 있는지, 하위 폴더인지)
- [ ] 올바른 경로를 `.env` 파일에 추가
- [ ] `python test_oracle_thick.py` 실행하여 테스트

---

## 🔍 빠른 확인

다음 명령으로 바로 확인할 수 있습니다:

```powershell
# oci.dll 파일 찾기
Get-ChildItem -Path C:\oraclexe -Recurse -Filter "oci.dll" -ErrorAction SilentlyContinue | Select-Object FullName
```

이 명령이 `oci.dll` 파일의 전체 경로를 보여줍니다.


