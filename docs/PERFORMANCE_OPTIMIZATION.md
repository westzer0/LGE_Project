# 성능 최적화 가이드

프로젝트의 성능 최적화 포인트와 개선 사항을 정리한 문서입니다.

## 프론트엔드 최적화

### 1. React 최적화

#### useMemo 사용
- `PortfolioResult.jsx`의 `benefitInfo` 계산을 `useMemo`로 최적화
- 의존성 배열: `[purchaseType, products]`
- 불필요한 재계산 방지

#### useCallback 사용
- 이벤트 핸들러를 `useCallback`으로 메모이제이션
- `handleRefresh`, `handlePurchase`, `handleConsultation` 함수 최적화

#### 컴포넌트 최적화
- `ProductCard` 컴포넌트에 `React.memo` 적용 고려
- 불필요한 리렌더링 방지

### 2. API 호출 최적화

#### 요청 캐싱
- 동일한 포트폴리오 ID로 반복 요청 시 캐싱 고려
- React Query 또는 SWR 사용 검토

#### 배치 요청
- 여러 제품 정보를 한 번에 요청하는 API 고려
- `/api/products/?ids=1,2,3` 형식

### 3. 이미지 최적화

#### Lazy Loading
- 제품 이미지에 lazy loading 적용
- `loading="lazy"` 속성 추가

#### 이미지 포맷
- WebP 또는 AVIF 포맷 사용 고려
- 반응형 이미지 (srcset) 사용

## 백엔드 최적화

### 1. 데이터베이스 쿼리 최적화

#### select_related 사용
```python
# 개선 전
products = Product.objects.filter(is_active=True)

# 개선 후
products = Product.objects.select_related('spec').filter(is_active=True)
```

#### prefetch_related 사용
- 관련 객체가 많은 경우 `prefetch_related` 사용
- 예: `Product.objects.prefetch_related('reviews', 'demographics')`

#### 쿼리 최적화
- `only()` 또는 `defer()` 사용하여 필요한 필드만 로드
- 불필요한 필드 제외

### 2. 추천 엔진 최적화

#### 캐싱 전략
- 사용자 프로필 기반 추천 결과 캐싱
- Redis 또는 메모리 캐시 사용

#### 배치 처리
- 여러 제품의 점수 계산을 배치로 처리
- N+1 쿼리 문제 해결

#### 인덱싱
- 데이터베이스 인덱스 확인
- `price`, `category`, `is_active` 필드 인덱싱

### 3. API 응답 최적화

#### 페이징
- 대량 데이터는 페이징 처리
- `page_size` 파라미터 활용

#### 필드 선택
- 필요한 필드만 반환하는 옵션 제공
- `fields` 파라미터로 선택적 필드 반환

#### 압축
- Gzip 압축 활성화
- 대용량 JSON 응답 압축

## 모니터링 및 프로파일링

### 1. 프론트엔드 프로파일링

#### React DevTools Profiler
- 컴포넌트 렌더링 시간 측정
- 불필요한 리렌더링 식별

#### Performance API
- API 호출 시간 측정
- 사용자 경험 메트릭 수집

### 2. 백엔드 프로파일링

#### Django Debug Toolbar
- 개발 환경에서 쿼리 분석
- 쿼리 개수 및 실행 시간 확인

#### 로깅
- 느린 쿼리 로깅
- 성능 병목 지점 식별

#### APM 도구
- Sentry, New Relic 등 사용
- 프로덕션 환경 성능 모니터링

## 최적화 체크리스트

### 프론트엔드
- [ ] React.memo 적용
- [ ] useMemo/useCallback 사용
- [ ] 이미지 lazy loading
- [ ] 코드 스플리팅
- [ ] 번들 크기 최적화

### 백엔드
- [ ] select_related/prefetch_related 사용
- [ ] 데이터베이스 인덱싱
- [ ] 쿼리 최적화
- [ ] 캐싱 전략
- [ ] API 응답 압축

### 인프라
- [ ] CDN 사용
- [ ] 정적 파일 최적화
- [ ] 데이터베이스 연결 풀링
- [ ] 로드 밸런싱

## 성능 메트릭

### 목표 지표
- **First Contentful Paint (FCP)**: < 1.5초
- **Largest Contentful Paint (LCP)**: < 2.5초
- **Time to Interactive (TTI)**: < 3.5초
- **API 응답 시간**: < 500ms (평균)

### 측정 방법
- Lighthouse 사용
- WebPageTest 사용
- Chrome DevTools Performance 탭

---

**마지막 업데이트**: 2024년 12월

