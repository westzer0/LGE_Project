"""빠른 데이터베이스 연결 테스트"""
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

try:
    django.setup()
    print("Django 설정 완료")
except Exception as e:
    print(f"Django 설정 실패: {e}")
    sys.exit(1)

from django.db import connection

print("\n" + "="*60)
print("Oracle 데이터베이스 연결 테스트")
print("="*60)

# 설정 정보 출력
db_config = connection.settings_dict
print(f"\n연결 정보:")
print(f"  호스트: {db_config.get('HOST', 'N/A')}")
print(f"  포트: {db_config.get('PORT', 'N/A')}")
print(f"  서비스명: {db_config.get('NAME', 'N/A')}")
print(f"  사용자: {db_config.get('USER', 'N/A')}")
print(f"  비밀번호: {'***' if db_config.get('PASSWORD') else 'N/A'}")

print("\n" + "-"*60)
print("연결 시도 중...")

try:
    # 연결 테스트
    with connection.cursor() as cursor:
        # 간단한 쿼리 실행
        cursor.execute("SELECT 1 FROM DUAL")
        result = cursor.fetchone()
        
        print("✅ 연결 성공!")
        print(f"   테스트 쿼리 결과: {result}")
        
        # Oracle 버전 확인
        try:
            cursor.execute("SELECT * FROM v$version WHERE banner LIKE 'Oracle%'")
            version = cursor.fetchone()
            if version:
                print(f"   Oracle 버전: {version[0]}")
        except:
            pass
        
        # 현재 사용자 확인
        try:
            cursor.execute("SELECT USER FROM DUAL")
            current_user = cursor.fetchone()
            if current_user:
                print(f"   현재 사용자: {current_user[0]}")
        except:
            pass
        
        print("\n" + "="*60)
        print("✅ 데이터베이스 연결 정상!")
        print("="*60)
        
except Exception as e:
    print(f"\n❌ 연결 실패!")
    print(f"   오류: {e}")
    print("\n" + "="*60)
    import traceback
    traceback.print_exc()
    sys.exit(1)

