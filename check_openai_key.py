"""
OpenAI API 키 연결 상태 확인 스크립트
"""
import os
import sys
import django

# Django 설정 로드
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.conf import settings
from api.services.chatgpt_service import ChatGPTService, OPENAI_AVAILABLE, client

def check_openai_connection():
    """OpenAI API 키 연결 상태 확인"""
    print("=" * 60)
    print("OpenAI API 키 연결 상태 확인")
    print("=" * 60)
    print()
    
    # 1. 환경변수 확인
    env_key = os.environ.get('OPENAI_API_KEY', '')
    print("1. 환경변수 확인:")
    if env_key:
        masked_key = env_key[:8] + "..." + env_key[-4:] if len(env_key) > 12 else "***"
        print(f"   ✓ OPENAI_API_KEY 환경변수 존재: {masked_key}")
    else:
        print("   ✗ OPENAI_API_KEY 환경변수가 설정되지 않았습니다.")
    print()
    
    # 2. Django 설정 확인
    django_key = getattr(settings, 'OPENAI_API_KEY', '')
    print("2. Django 설정 확인:")
    if django_key:
        masked_key = django_key[:8] + "..." + django_key[-4:] if len(django_key) > 12 else "***"
        print(f"   ✓ settings.OPENAI_API_KEY 존재: {masked_key}")
    else:
        print("   ✗ settings.OPENAI_API_KEY가 설정되지 않았습니다.")
    print()
    
    # 3. 서비스 초기화 상태 확인
    print("3. ChatGPT 서비스 초기화 상태:")
    print(f"   OPENAI_AVAILABLE: {OPENAI_AVAILABLE}")
    print(f"   client 객체: {'존재' if client is not None else 'None'}")
    print()
    
    # 4. is_available() 메서드 확인
    print("4. ChatGPTService.is_available() 확인:")
    is_avail = ChatGPTService.is_available()
    print(f"   결과: {is_avail}")
    print()
    
    # 5. 실제 API 호출 테스트
    if is_avail:
        print("5. 실제 API 호출 테스트:")
        try:
            test_response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "user", "content": "안녕하세요. 연결 테스트입니다. '연결 성공'이라고만 답변해주세요."}
                ],
                max_tokens=10,
                temperature=0
            )
            response_text = test_response.choices[0].message.content.strip()
            print(f"   ✓ API 호출 성공!")
            print(f"   응답: {response_text}")
            print()
            print("=" * 60)
            print("✅ OpenAI API 키가 정상적으로 연결되어 있습니다!")
            print("=" * 60)
            return True
        except Exception as e:
            print(f"   ✗ API 호출 실패: {e}")
            print()
            print("=" * 60)
            print("❌ OpenAI API 키는 설정되어 있지만 연결에 실패했습니다.")
            print("   API 키가 유효한지 확인해주세요.")
            print("=" * 60)
            return False
    else:
        print("5. 실제 API 호출 테스트:")
        print("   ⚠️ 서비스가 사용 불가능한 상태입니다. API 호출 테스트를 건너뜁니다.")
        print()
        print("=" * 60)
        print("❌ OpenAI API 키가 설정되지 않았거나 초기화에 실패했습니다.")
        print("=" * 60)
        print()
        print("해결 방법:")
        print("1. 환경변수에 OPENAI_API_KEY를 설정하세요:")
        print("   Windows PowerShell: $env:OPENAI_API_KEY='your-api-key'")
        print("   Windows CMD: set OPENAI_API_KEY=your-api-key")
        print("   Linux/Mac: export OPENAI_API_KEY='your-api-key'")
        print()
        print("2. 또는 .env 파일을 생성하고 다음을 추가하세요:")
        print("   OPENAI_API_KEY=your-api-key")
        return False

if __name__ == "__main__":
    check_openai_connection()

