# 프론트엔드 스타일 가이드 (Frontend Style Guide)

## ⚠️ 중요: 이 가이드는 절대 변경하지 마세요!

이 문서는 현재 프론트엔드 디자인의 핵심 요소들을 정의합니다. 
백엔드 개발 시에도 이 스타일 가이드를 준수해야 합니다.

---

## 📐 레이아웃 구조

### 1. Header 구조
- **위치**: `position: fixed; top: 0;`
- **높이**: 120px (상단 60px + 하단 60px)
- **패딩**: `padding: 0 60px;` (데스크톱)
- **배경**: `background: #fff;`
- **테두리**: `border-bottom: 1px solid #e5e5e5;`

### 2. Breadcrumb 구조
- **위치**: `position: fixed; top: 120px;`
- **높이**: 40px
- **패딩**: `padding: 12px 0;`
- **Breadcrumb-nav 패딩**: `padding: 7px 0px 0px;` ⚠️ 필수
- **배경**: `background: #fff;`

### 3. Main Content
- **마진 상단**: `margin-top: 160px;` (Header 120px + Breadcrumb 40px)
- **최소 높이**: `min-height: calc(100vh - 160px);`

---

## 🎨 핵심 스타일 규칙

### Breadcrumb Navigation
```css
.breadcrumb-nav {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 14px;
    color: #666;
    padding: 7px 0px 0px; /* ⚠️ 필수: 절대 변경 금지 */
}
```

### 온보딩 프로그레스 바
- **총 단계**: 7단계 (절대 변경 금지)
- **프로그레스 바 너비 계산**:
  - 1단계: `width: 14.29%;` (1/7)
  - 2단계: `width: 28.57%;` (2/7)
  - 3단계: `width: 42.86%;` (3/7)
  - 4단계: `width: 57.14%;` (4/7)
  - 5단계: `width: 71.43%;` (5/7)
  - 6단계: `width: 85.7%;` (6/7)
  - 7단계: `width: 100%;` (7/7)

### 텍스트 표시
- 모든 단계에서 "X단계 / 7단계" 형식 유지

---

## 🚫 금지 사항

### 절대 변경하면 안 되는 것들:

1. **Breadcrumb padding**: `padding: 7px 0px 0px;` - 변경 금지
2. **온보딩 단계 수**: 7단계 고정 - 변경 금지
3. **Header 높이**: 120px 고정 - 변경 금지
4. **Breadcrumb 위치**: `top: 120px;` 고정 - 변경 금지
5. **Main Content 마진**: `margin-top: 160px;` 고정 - 변경 금지
6. **프로그레스 바 계산식**: (단계 / 7) × 100% - 변경 금지

### other_recommendations.html 특수 규칙
- **Grid padding**: `padding: 0 60px 0 20px;` - 변경 금지

---

## ✅ 변경 전 체크리스트

프론트엔드를 수정하기 전에 반드시 확인:

- [ ] Breadcrumb padding이 `7px 0px 0px`인가?
- [ ] 온보딩 단계가 7단계로 표시되는가?
- [ ] 프로그레스 바 너비가 (단계/7) × 100%로 계산되는가?
- [ ] Header 높이가 120px인가?
- [ ] Main Content 마진이 160px인가?
- [ ] other_recommendations.html의 padding이 `0 60px 0 20px`인가?

---

## 📝 파일별 필수 스타일

### 모든 템플릿 파일에 필수:
```css
.breadcrumb-nav {
    padding: 7px 0px 0px; /* 필수 */
}
```

### 온보딩 페이지들 (onboarding.html ~ onboarding_step7.html):
```css
.progress-fill {
    width: [단계/7 × 100%]; /* 필수 계산식 */
}

.progress-text {
    content: "[X]단계 / 7단계"; /* 필수 형식 */
}
```

---

## 🔧 백엔드 개발 시 주의사항

1. **템플릿 수정 시**: 반드시 위 스타일 규칙을 유지하세요
2. **새 페이지 추가 시**: 기존 스타일 가이드를 따라주세요
3. **레이아웃 변경 시**: 이 문서를 먼저 확인하세요

---

## 📞 문의

프론트엔드 스타일 관련 문의는 이 문서를 참고하거나, 
기존 템플릿 파일들을 참조하세요.

**마지막 업데이트**: 2025-01-27
**버전**: 1.0.0
