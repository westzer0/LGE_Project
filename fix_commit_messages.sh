#!/bin/bash
# 커밋 메시지 수정 스크립트

# 최근 4개 커밋의 메시지를 수정
git rebase -i HEAD~4 <<EOF
edit ca8c15b
edit a122c68
edit 7590408
pick 026775c
EOF

# 각 커밋 메시지 수정
# ca8c15b: merge 메시지
git commit --amend -m "merge: 원격 변경사항 병합 완료 (로컬 버전 유지)"

# a122c68: merge 메시지  
git commit --amend -m "merge: 원격 변경사항 병합 및 충돌 해결"

# 7590408: feat 메시지
git commit --amend -m "feat: 취향별 독립적인 Scoring Logic 시스템 및 추천 문구 생성 기능 추가

- 취향별 독립적인 Scoring Logic 생성 시스템 구현
  - 768개 취향 조합을 약 400개 그룹으로 클러스터링
  - 각 그룹별 독립적인 scoring logic 생성 및 적용
  - Logic 도출 근거 자동 문서화

- 취향별 추천 문구 생성 기능 추가
  - 리뷰 기반 및 AI 기반 추천 문구 생성
  - 중복 방지 로직 강화
  - 768개 취향 조합별 고유 문구 생성

- 분석 및 검증 도구 추가
  - 추천 정확도 검증 도구
  - 취향 조합 분석 도구
  - 추천 문구 분석 도구

- 데이터 import 개선
  - 리뷰 및 인구통계 데이터 import 개선
  - 데이터 상태 확인 도구 개선

- 문서화
  - 취향별 Scoring Logic 가이드 추가
  - 백엔드 로직 정확도 검증 가이드 추가
  - 데이터 import 가이드 추가"

git rebase --continue

