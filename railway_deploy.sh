#!/bin/bash
# Railway 배포 자동화 스크립트

echo "🚀 Railway 배포 준비 중..."

# 1. 환경 변수 확인
echo "📋 필수 환경 변수 확인:"
echo "   - DJANGO_SECRET_KEY"
echo "   - DJANGO_DEBUG=False"
echo "   - ALLOWED_HOSTS"
echo "   - KAKAO_REST_API_KEY"
echo "   - KAKAO_JS_KEY"
echo "   - OPENAI_API_KEY"
echo "   - USE_ORACLE=true"
echo "   - ORACLE_HOST, ORACLE_USER, ORACLE_PASSWORD 등"

# 2. 정적 파일 수집
echo "📦 정적 파일 수집 중..."
python manage.py collectstatic --noinput

# 3. 마이그레이션 확인
echo "🗄️ 데이터베이스 마이그레이션 확인..."
python manage.py migrate --check

echo "✅ 배포 준비 완료!"
echo ""
echo "다음 단계:"
echo "1. Railway 대시보드에서 환경 변수 설정"
echo "2. GitHub 저장소 연결"
echo "3. 배포 시작"

