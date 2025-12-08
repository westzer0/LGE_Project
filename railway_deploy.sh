#!/bin/bash
# Railway 배포 자동화 스크립트

echo "🚀 Railway 배포 준비 중..."

# 1. Node.js 및 npm 확인
if ! command -v node &> /dev/null; then
    echo "⚠️ Node.js가 설치되지 않았습니다. React 빌드를 건너뜁니다."
else
    echo "📦 React 앱 빌드 중..."
    npm install
    npm run build
fi

# 2. Python 의존성 설치
echo "📦 Python 의존성 설치 중..."
pip install -r requirements.txt

# 3. 환경 변수 확인
echo "📋 필수 환경 변수 확인:"
echo "   - DJANGO_SECRET_KEY"
echo "   - DJANGO_DEBUG=False"
echo "   - ALLOWED_HOSTS"
echo "   - KAKAO_REST_API_KEY"
echo "   - KAKAO_JS_KEY"
echo "   - OPENAI_API_KEY"
echo "   - USE_ORACLE=true"
echo "   - ORACLE_HOST, ORACLE_USER, ORACLE_PASSWORD 등"

# 4. 데이터베이스 마이그레이션
echo "🗄️ 데이터베이스 마이그레이션 실행..."
python manage.py migrate --noinput

# 5. 정적 파일 수집
echo "📦 정적 파일 수집 중..."
python manage.py collectstatic --noinput

echo "✅ 배포 준비 완료!"
echo ""
echo "다음 단계:"
echo "1. Railway 대시보드에서 환경 변수 설정"
echo "2. GitHub 저장소 연결"
echo "3. 배포 시작"

