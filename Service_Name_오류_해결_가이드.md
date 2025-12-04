# Service Name 오류 해결 가이드

## 🔍 현재 오류

```
DPY-6001: Service "MAPPP" is not registered with the listener at host "49.171.84.3" port 1524. (Similar to ORA-12514)
```

**의미**: Service Name "MAPPP"가 Oracle 리스너에 등록되어 있지 않습니다.

---

## ✅ 해결 방법

### 1단계: 다양한 연결 형식 시도

다음 스크립트를 실행하여 여러 연결 형식을 자동으로 테스트하세요:

```powershell
python test_oracle_connection_variants.py
```

이 스크립트는 다음을 시도합니다:
- Service Name 형식 (현재 설정)
- Service Name 파라미터 방식
- SID 형식
- SID Easy Connect 형식

---

### 2단계: 정확한 Service Name 또는 SID 확인

다음 방법으로 정확한 정보를 확인하세요:

#### 방법 1: 학원 제공 자료 확인
- 학원에서 제공한 데이터베이스 연결 가이드 확인
- 연결 문자열 예제 확인
- 정확한 Service Name 또는 SID 값 확인

#### 방법 2: SQL Developer나 다른 클라이언트 확인
- 이미 연결된 다른 클라이언트가 있다면:
  - 연결 설정에서 Service Name 또는 SID 확인
  - 연결 문자열 확인

#### 방법 3: 네트워크에서 리스너 확인 (가능한 경우)
다음 Python 스크립트로 리스너 상태 확인 시도:

```python
import oracledb

host = "project-db-campus.smhrd.com"
port = 1524

try:
    # 리스너 연결 시도 (서비스 목록 확인)
    # 주의: 이것은 일반적으로 불가능하지만, 일부 경우에는 작동할 수 있음
    print(f"리스너 {host}:{port}에 접속 시도...")
    # 실제로는 직접 확인이 어려움
except Exception as e:
    print(f"리스너 확인 실패: {e}")
```

---

### 3단계: 다른 형식 시도

Service Name 대신 SID를 시도해보세요:

**SID 형식 (콜론 구분)**:
```python
dsn = f"{host}:{port}:{service_name}"  # 콜론 2개 사용
```

**또는 직접 파라미터 지정**:
```python
conn = oracledb.connect(
    user=user,
    password=password,
    host=host,
    port=int(port),
    sid="MAPPP"  # service_name 대신 sid 사용
)
```

---

### 4단계: 학원에 확인 요청

다음 정보를 학원에 확인 요청하세요:
1. **정확한 Service Name**이 무엇인지
2. **SID**를 사용해야 하는지
3. **연결 문자열 형식**이 무엇인지
4. **예제 연결 문자열**이 있는지

---

## 🔧 일반적인 해결 방법

### Service Name vs SID

- **Service Name**: `host:port/service_name` 형식 (슬래시 사용)
- **SID**: `host:port:sid` 형식 (콜론 사용) 또는 별도 파라미터

### 가능한 연결 형식들

1. **Service Name (Easy Connect)**:
   ```
   project-db-campus.smhrd.com:1524/MAPPP
   ```

2. **SID (Easy Connect)**:
   ```
   project-db-campus.smhrd.com:1524:MAPPP
   ```

3. **Service Name (파라미터)**:
   ```python
   conn = oracledb.connect(
       user=user,
       password=password,
       host=host,
       port=port,
       service_name="MAPPP"
   )
   ```

4. **SID (파라미터)**:
   ```python
   conn = oracledb.connect(
       user=user,
       password=password,
       host=host,
       port=port,
       sid="MAPPP"
   )
   ```

---

## 📝 체크리스트

- [ ] `test_oracle_connection_variants.py` 실행하여 다양한 형식 시도
- [ ] 학원 제공 자료에서 정확한 Service Name/SID 확인
- [ ] 다른 클라이언트(SQL Developer 등)의 연결 설정 확인
- [ ] 학원에 정확한 연결 정보 요청
- [ ] SID 형식 시도

---

## 💡 다음 단계

1. **`test_oracle_connection_variants.py` 실행** - 자동으로 다양한 형식 시도
2. **학원에 확인 요청** - 정확한 Service Name 또는 SID 값
3. **성공한 형식을 Django 설정에 적용** - 연결이 성공하면 동일 형식 사용

---

## ⚠️ 중요

현재 오류는 **연결 설정 문제**가 아니라 **Service Name/SID 값이 잘못되었을 가능성**이 높습니다. 

학원에서 제공한 정확한 연결 정보를 확인하는 것이 가장 빠른 해결 방법입니다!



