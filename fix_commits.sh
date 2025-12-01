#!/bin/bash
# 깨진 커밋 메시지 수정 스크립트

# 7590408 - 취향별 Scoring Logic 기반 및 추천 문구 생성 기능 추가
git rebase -i 57880e5^
# 커밋 메시지를 다음으로 변경:
# feat: Add taste-based scoring logic and recommendation phrase generation

# 57880e5 - 메인페이지 연동, AI 챗봇, API 키 설정
git rebase -i 339d212^
# 커밋 메시지를 다음으로 변경:
# feat: Add main page integration, AI chatbot, API key configuration

# ca8c15b - merge: 메인페이지 연동 및 배너 이미지 적용
# a122c68 - merge: 메인페이지 연동 및 이미지 추가
# 이 두 개는 merge 커밋이므로 별도 처리 필요

