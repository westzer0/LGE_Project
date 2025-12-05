import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

# .env 파일이 없으면 환경 변수 직접 설정
if not os.path.exists('.env'):
    os.environ['DB_NAME'] = 'MAPPP'
    os.environ['DB_USER'] = 'campus_24K_LG3_DX7_p3_4'
    os.environ['DB_PASSWORD'] = 'smhrd4'
    os.environ['DB_HOST'] = 'project-db-campus.smhrd.com'
    os.environ['DB_PORT'] = '1524'

django.setup()

from django.db import connection

print("="*60)
print("Oracle DB 연결 테스트")
print("="*60)

db_config = connection.settings_dict
print(f"\n설정:")
print(f"  HOST: {db_config.get('HOST')}")
print(f"  PORT: {db_config.get('PORT')}")
print(f"  NAME: {db_config.get('NAME')}")
print(f"  USER: {db_config.get('USER')}")
print(f"  PASSWORD: {'설정됨' if db_config.get('PASSWORD') else '없음'}")

if not db_config.get('USER') or not db_config.get('PASSWORD'):
    print("\n❌ 오류: DB_USER 또는 DB_PASSWORD가 설정되지 않았습니다!")
    sys.exit(1)

print("\n연결 시도 중...")

try:
    with connection.cursor() as cursor:
        cursor.execute("SELECT USER, SYSDATE FROM DUAL")
        result = cursor.fetchone()
        print(f"\n✅ 연결 성공!")
        print(f"   사용자: {result[0]}")
        print(f"   서버 시간: {result[1]}")
        
        cursor.execute("SELECT banner FROM v$version WHERE ROWNUM = 1")
        version = cursor.fetchone()
        if version:
            print(f"   Oracle 버전: {version[0]}")
        
        print("\n" + "="*60)
        print("✅ 데이터베이스 연결이 정상적으로 작동합니다!")
        print("="*60)
        sys.exit(0)
        
except Exception as e:
    print(f"\n❌ 연결 실패!")
    print(f"   오류: {type(e).__name__}: {str(e)}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

