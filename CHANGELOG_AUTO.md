# Auto 작업 변경 사항 로그

## 2024-12-XX: PRD 6단계 온보딩 구조 구현 및 개선

### 주요 변경 사항

#### 1. 온보딩 모델 확장 (api/models.py)

**추가된 필드:**
- `has_pet` (BooleanField): Step 2 - 반려동물 여부
- `main_space` (JSONField): Step 3 - 주요 공간 (JSON 배열)
- `cooking` (CharField): Step 4 - 요리 빈도
- `laundry` (CharField): Step 4 - 세탁 빈도
- `media` (CharField): Step 4 - 미디어 사용 패턴
- `priority_list` (JSONField): Step 5 - 우선순위 목록 (JSON 배열, 순서 중요)

**수정된 필드:**
- `current_step`: 최대값을 6으로 확장
- `mark_completed()`: current_step을 6으로 설정
- `to_user_profile()`: 새로운 필드들을 포함하도록 업데이트

#### 2. React 온보딩 컴포넌트 6단계 확장 (src/pages/Onboarding.jsx)

**구조 변경:**
- 기존 4단계 → PRD 기준 6단계로 재구성

**Step 1: Vibe Check**
- 분위기 선택 (modern, cozy, pop, luxury)
- PRD에 맞게 선택지 업데이트

**Step 2: Household DNA**
- 가구 구성 선택 (1인, 2인, 3~4인, 5인 이상)
- 반려동물 여부 질문 추가 (조건부)

**Step 3: Reality Check**
- 주거 형태 선택 (아파트, 오피스텔, 주택, 원룸)
- 주요 공간 다중 선택 추가 (거실, 방, 주방, 드레스룸, 서재, 전체)
- 평수 슬라이더 (기존 유지)

**Step 4: Lifestyle Info**
- 조건부 질문 로직 구현:
  - 주방/전체 선택 시: 요리 빈도 질문
  - 드레스룸/전체 선택 시: 세탁 빈도 질문
  - 거실/방/서재/전체 선택 시: 미디어 사용 패턴 질문

**Step 5: Priorities**
- 우선순위 다중 선택 및 순서 표시
- priority_list 배열 관리
- 첫 번째 우선순위를 priority 필드에도 저장

**Step 6: Budget**
- 예산 범위 선택 (budget, standard, premium)
- PRD에 맞게 선택지 업데이트

#### 3. 온보딩 API 엔드포인트 업데이트 (api/views.py)

**onboarding_complete_view 수정:**
- 새로운 필드들 저장 로직 추가:
  - `has_pet`: Boolean 변환 처리
  - `main_space`: JSON 배열 처리
  - `priority_list`: JSON 배열 처리 및 검증
- `current_step`: 6으로 업데이트
- `onboarding_data`: 새로운 필드들 포함하도록 업데이트

#### 4. 포트폴리오 결과 페이지 개선 (src/pages/PortfolioResult.jsx)

**추가된 기능:**
- `handleKakaoShare()`: 카카오톡 공유 기능 구현
  - 포트폴리오 공유 API 호출
  - 카카오 JavaScript SDK 연동 (TODO: SDK 로드 확인 필요)
  - 링크 복사 fallback
- `handleConsultation()`: 베스트샵 상담예약 기능 구현
  - 상담예약 API 호출
  - 예약 완료 후 페이지 이동

**UI 개선:**
- 카카오톡 공유 버튼 클릭 핸들러 연결
- 링크 복사 버튼 추가

### 테스트 시나리오

#### 온보딩 플로우 테스트

1. **Step 1: Vibe Check**
   - URL: `http://localhost:5173/onboarding`
   - 선택: "모던 & 미니멀"
   - 예상: 다음 버튼 활성화, Step 2로 이동

2. **Step 2: Household DNA**
   - 선택: "우리 둘이 알콩달콩" (2인)
   - 반려동물: "네, 사랑스러운 댕냥이가 있어요"
   - 예상: Step 3로 이동

3. **Step 3: Reality Check**
   - 주거 형태: "아파트"
   - 주요 공간: "거실", "주방" 선택
   - 평수: 30평
   - 예상: Step 4로 이동

4. **Step 4: Lifestyle Info**
   - 요리 빈도: "가끔 해요" (주방 선택 시 표시)
   - 세탁 빈도: 표시 안 됨 (드레스룸 미선택)
   - 미디어 사용: "OTT를 즐기는 편" (거실 선택 시 표시)
   - 예상: Step 5로 이동

5. **Step 5: Priorities**
   - 우선순위 선택: "디자인", "기술", "에너지효율" (순서대로)
   - 예상: 선택 순서가 표시됨, Step 6로 이동

6. **Step 6: Budget**
   - 예산: "500~2000만원"
   - 예상: "완료하고 추천받기" 버튼 활성화

7. **완료 및 추천**
   - 클릭: "완료하고 추천받기"
   - 예상: 
     - `/api/onboarding/complete/` API 호출
     - 추천 결과 수신
     - `/result?portfolio_id=XXX`로 이동

#### 포트폴리오 결과 페이지 테스트

1. **카카오 공유**
   - URL: `http://localhost:5173/result?portfolio_id=PF-XXXXXX`
   - 클릭: 카카오톡 공유 버튼
   - 예상:
     - `/api/portfolio/{portfolio_id}/share/` API 호출
     - 카카오톡 공유 모달 표시 (SDK 로드 시)
     - 또는 링크 복사 알림

2. **베스트샵 상담예약**
   - 클릭: "베스트샵 상담예약" 버튼
   - 예상:
     - `/api/bestshop/consultation/` API 호출
     - 예약 완료 후 `/reservation-status`로 이동

3. **다시 추천받기**
   - 클릭: "다시 추천받기" 버튼
   - 예상: `/onboarding`로 이동

### 데이터베이스 마이그레이션 필요

새로운 필드 추가로 인해 마이그레이션 필요:

```bash
python manage.py makemigrations
python manage.py migrate
```

### 알려진 이슈 및 TODO

1. **카카오 JavaScript SDK 로드**
   - 현재: SDK 로드 확인 로직만 구현
   - TODO: `index.html`에 카카오 SDK 스크립트 태그 추가 필요
   - 예: `<script src="https://developers.kakao.com/sdk/js/kakao.js"></script>`

2. **조건부 질문 로직**
   - Step 4에서 선택된 공간에 따라 질문이 동적으로 표시됨
   - 모든 조건부 질문이 없을 경우에도 진행 가능하도록 처리됨

3. **우선순위 순서**
   - `priority_list`는 선택 순서를 유지
   - 첫 번째 우선순위는 `priority` 필드에도 저장

4. **하위 호환성**
   - 기존 4단계 온보딩 데이터와의 호환성 유지
   - `pet` 필드 → `has_pet` 변환 로직 포함

### 다음 단계 권장 사항

1. **추천 엔진 개선**
   - 새로운 필드들(`main_space`, `priority_list` 등)을 추천 로직에 반영
   - 라이프스타일 정보 기반 추천 강화

2. **포트폴리오 결과 페이지**
   - 스타일 분석 결과 표시 개선
   - 제품 카드에 추천 이유 표시
   - 가격 계산 로직 검증

3. **카카오 공유 완성**
   - 카카오 SDK 초기화 코드 추가
   - 공유 이미지 최적화
   - 공유 통계 추적

4. **베스트샵 상담 연동**
   - 외부 시스템 연동 (실제 베스트샵 API)
   - 예약 조회/변경 기능 완성

---

**작업 완료 시간**: 약 2시간  
**주요 파일 변경**: 4개 파일  
**추가된 필드**: 6개  
**새로운 기능**: 카카오 공유, 베스트샵 상담예약
