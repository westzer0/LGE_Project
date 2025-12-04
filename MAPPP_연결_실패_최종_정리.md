# MAPPP 연결 실패 최종 정리 및 해결 방법

## 🔍 현재 상황

### 테스트 결과
- ✅ 환경 변수 로드: 성공 (모든 ORACLE_* 변수 정상)
- ✅ 네트워크 연결: 성공 (리스너에 도달 가능)
- ❌ Service Name "MAPPP": 리스너에 등록되지 않음 (ORA-12514)
- ❌ SID "MAPPP": 리스너에 등록되지 않음 (ORA-12505)

### 결론
**"MAPPP"는 실제 Service Name도 SID도 아닙니다.**

---

## ✅ 즉시 확인할 사항

### 1. SQL Developer에서 연결 확인
SQL Developer를 사용하여 실제로 연결이 되는지 확인하세요:

1. SQL Developer 실행
2. 새 연결 생성:
   - **Username**: `campus_24K_LG3_DX7_p3_4`
   - **Password**: `smhrd4`
   - **Hostname**: `project-db-campus.smhrd.com`
   - **Port**: `1524`
   - **Service name** 또는 **SID** 필드 확인

3. **중요**: SQL Developer에서 성공하는 설정을 확인하세요
   - Service name 필드에 무엇이 입력되어 있는지
   - SID 필드에 무엇이 입력되어 있는지
   - 또는 다른 형식의 연결 문자열이 있는지

### 2. 학원에 확인 요청
다음 정보를 학원에 확인 요청하세요:

```
안녕하세요. Oracle 데이터베이스 연결 설정 중 문제가 발생하여 문의드립니다.

현재 연결 정보:
- Host: project-db-campus.smhrd.com
- Port: 1524
- User: campus_24K_LG3_DX7_p3_4
- Password: smhrd4

문제:
"MAPPP"를 Service Name으로 사용했을 때 "Service MAPPP is not registered with the listener" 오류 발생
"MAPPP"를 SID로 사용했을 때 "SID MAPPP is not registered with the listener" 오류 발생

확인이 필요한 사항:
1. 정확한 Service Name이 무엇인지?
2. SID를 사용해야 하는지? (사용한다면 정확한 SID 값은?)
3. 연결 문자열 예제나 SQL Developer 설정 예제가 있는지?
4. 다른 포트나 다른 연결 형식을 사용해야 하는지?

감사합니다.
```

### 3. 다른 가능성 확인

#### 가능성 1: 다른 Service Name
- `MAPPP` 대신 다른 이름일 수 있습니다
- 예: `MAPPP.smhrd.com`, `MAPPP_DB`, `ORCL` 등

#### 가능성 2: 다른 포트
- 포트 1524 대신 다른 포트일 수 있습니다
- 예: 1521 (기본 Oracle 포트)

#### 가능성 3: TNS 연결 형식
- Easy Connect 대신 TNS 연결이 필요할 수 있습니다
- `tnsnames.ora` 파일이 필요할 수 있습니다

#### 가능성 4: 대소문자 구분
- Service Name이 대소문자를 구분할 수 있습니다
- 예: `MAPPP` vs `mappp` vs `MapPP`

---

## 🔧 추가 테스트 스크립트

다음 스크립트로 다른 가능성을 시도해볼 수 있습니다:

### 다른 Service Name 후보 시도
```python
# test_common_service_names.py
possible_names = [
    "MAPPP",
    "MAPPP.smhrd.com",
    "MAPPP_DB",
    "ORCL",
    "XEPDB1",
    "XE",
    "ORCLPDB1",
]

for name in possible_names:
    # Service Name 형식 시도
    # SID 형식 시도
```

### 다른 포트 시도
```python
possible_ports = [1524, 1521, 1522, 1523, 1525]
```

---

## 📝 다음 단계

1. **SQL Developer 연결 확인** (가장 중요!)
   - SQL Developer에서 실제로 연결되는지 확인
   - 성공하는 설정을 정확히 기록

2. **학원에 확인 요청**
   - 정확한 Service Name/SID 값 확인
   - 연결 예제 요청

3. **성공한 설정을 코드에 적용**
   - SQL Developer에서 성공한 설정을 Python 코드에 동일하게 적용

---

## ⚠️ 중요 참고사항

- 현재 **네트워크 연결 자체는 정상**입니다 (리스너에 도달 가능)
- 문제는 **Service Name/SID 값이 잘못되었을 가능성**이 높습니다
- SQL Developer나 다른 클라이언트에서 연결이 성공한다면, 그 설정을 그대로 사용하면 됩니다

---

## 💡 빠른 체크리스트

- [ ] SQL Developer에서 연결 시도
- [ ] SQL Developer 연결 성공 시, 사용한 Service Name/SID 값 확인
- [ ] 학원에 정확한 연결 정보 확인 요청
- [ ] 다른 학생이나 팀원에게 연결 정보 확인 요청
- [ ] 학원 제공 자료에서 연결 예제 확인

