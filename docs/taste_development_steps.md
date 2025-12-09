# Taste 계산 및 할당 개발 단계별 계획

## 📋 개발 단계 개요

총 **6단계**로 나누어 각 단계마다 검증하면서 진행합니다.

---

## 🔍 Step 1: 기본 인프라 검증

### 목표
- Oracle DB 연결 확인
- 필요한 테이블 존재 여부 확인
- MEMBER.TASTE 컬럼 확인

### 검증 항목
- [ ] Oracle DB 연결 성공
- [ ] `ONBOARDING_SESSION` 테이블 존재
- [ ] `ONBOARD_SESS_MAIN_SPACES` 테이블 존재
- [ ] `ONBOARD_SESS_PRIORITIES` 테이블 존재
- [ ] `MEMBER` 테이블 존재
- [ ] `MEMBER.TASTE` 컬럼 존재 (NUMBER(3))
- [ ] `MEMBER.TASTE` 제약조건 확인 (1~120 범위)

### 개발 작업
- 테스트 스크립트 작성: `test_taste_infrastructure.py`
- 각 테이블/컬럼 존재 여부 확인
- 제약조건 확인

### 검증 방법
```bash
python test_taste_infrastructure.py
```

### 완료 기준
- 모든 테이블/컬럼 존재 확인
- 제약조건 정상 작동 확인
- 에러 없이 통과

---

## 🔍 Step 2: 온보딩 데이터 조회 로직 검증

### 목표
- `TasteCalculationService._get_onboarding_data_from_session()` 검증
- 실제 온보딩 세션 데이터로 테스트

### 검증 항목
- [ ] `ONBOARDING_SESSION` 테이블에서 기본 데이터 읽기 성공
- [ ] `ONBOARD_SESS_MAIN_SPACES` 테이블에서 MAIN_SPACE 배열 읽기 성공
- [ ] `ONBOARD_SESS_PRIORITIES` 테이블에서 PRIORITY 배열 읽기 성공
- [ ] 데이터 형식 변환 정확성 확인
- [ ] NULL 값 처리 확인
- [ ] 빈 배열 처리 확인

### 개발 작업
- 테스트 스크립트 작성: `test_taste_data_retrieval.py`
- 샘플 온보딩 세션 데이터 생성 (또는 기존 데이터 사용)
- 각 정규화 테이블 데이터 확인

### 검증 방법
```bash
python test_taste_data_retrieval.py
```

### 완료 기준
- 모든 테이블에서 데이터 정상 조회
- 데이터 형식 변환 정확
- 예외 케이스 처리 확인

---

## 🔍 Step 3: Taste 계산 로직 검증

### 목표
- `TasteClassifier.calculate_taste_from_onboarding()` 검증
- 다양한 온보딩 데이터 조합으로 테스트

### 검증 항목
- [ ] Taste ID가 1~120 범위 내에 있는지 확인
- [ ] 동일한 온보딩 데이터는 동일한 Taste ID 반환하는지 확인
- [ ] 다른 온보딩 데이터는 다른 Taste ID 반환하는지 확인
- [ ] NULL 값 처리 확인
- [ ] 기본값 처리 확인

### 개발 작업
- 테스트 스크립트 작성: `test_taste_calculation.py`
- 다양한 온보딩 데이터 조합 테스트 케이스 작성
- Taste ID 분포 확인

### 검증 방법
```bash
python test_taste_calculation.py
```

### 완료 기준
- 모든 테스트 케이스 통과
- Taste ID 범위 검증 통과
- 일관성 확인 (동일 입력 → 동일 출력)

---

## 🔍 Step 4: MEMBER 테이블 저장 로직 검증

### 목표
- `TasteCalculationService.calculate_and_save_taste()` 검증
- MEMBER 테이블에 실제 저장 확인

### 검증 항목
- [ ] MEMBER 테이블에 TASTE 값 저장 성공
- [ ] 저장된 값이 1~120 범위인지 확인
- [ ] 기존 TASTE 값 덮어쓰기 확인
- [ ] 존재하지 않는 MEMBER_ID 처리 확인
- [ ] 트랜잭션 롤백 확인 (에러 발생 시)

### 개발 작업
- 테스트 스크립트 작성: `test_taste_save.py`
- 테스트용 MEMBER 생성
- 저장 전/후 값 비교
- 롤백 테스트

### 검증 방법
```bash
python test_taste_save.py
```

### 완료 기준
- MEMBER 테이블에 정상 저장
- 값 범위 검증 통과
- 에러 처리 확인

---

## 🔍 Step 5: 통합 테스트

### 목표
- 전체 플로우 테스트: 온보딩 완료 → Taste 계산 → 저장
- 실제 API 호출 시뮬레이션

### 검증 항목
- [ ] 온보딩 세션 생성 (Step 1~6)
- [ ] 온보딩 완료 (status='COMPLETED')
- [ ] 조건 체크 (member_id != 'GUEST')
- [ ] Taste 계산 트리거 확인
- [ ] MEMBER.TASTE 저장 확인
- [ ] 로그 확인

### 개발 작업
- 통합 테스트 스크립트 작성: `test_taste_integration.py`
- 전체 온보딩 플로우 시뮬레이션
- 로그 분석

### 검증 방법
```bash
python test_taste_integration.py
```

### 완료 기준
- 전체 플로우 정상 작동
- 모든 조건 체크 통과
- MEMBER.TASTE 정상 저장

---

## 🔍 Step 6: 엣지 케이스 검증

### 목표
- 예외 상황 처리 확인
- 에러 핸들링 검증

### 검증 항목
- [ ] GUEST 회원인 경우 Taste 계산 건너뛰기 확인
- [ ] status != 'COMPLETED' 인 경우 Taste 계산 안 함 확인
- [ ] 온보딩 데이터가 불완전한 경우 처리 확인
- [ ] MEMBER 테이블에 회원이 없는 경우 처리 확인
- [ ] Taste 계산 실패 시 온보딩 저장은 성공하는지 확인
- [ ] 에러 로그 정확성 확인

### 개발 작업
- 엣지 케이스 테스트 스크립트 작성: `test_taste_edge_cases.py`
- 각 예외 상황 테스트 케이스 작성

### 검증 방법
```bash
python test_taste_edge_cases.py
```

### 완료 기준
- 모든 엣지 케이스 처리 확인
- 에러 핸들링 정상 작동
- 로그 정확성 확인

---

## 📊 진행 상황 추적

각 단계 완료 후 체크리스트 업데이트:

- [ ] Step 1 완료
- [ ] Step 2 완료
- [ ] Step 3 완료
- [ ] Step 4 완료
- [ ] Step 5 완료
- [ ] Step 6 완료

---

## 🚀 다음 단계

**Step 1부터 시작합니다.**

Step 1: 기본 인프라 검증
- 테스트 스크립트 작성
- 테이블/컬럼 존재 여부 확인
- 제약조건 확인

준비되면 알려주세요!

