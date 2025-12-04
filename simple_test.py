import os
import sys

# 환경 변수 설정
os.environ['DB_NAME']='MAPPP'
os.environ['DB_USER']='campus_24K_LG3_DX7_p3_4'
os.environ['DB_PASSWORD']='smhrd4'
os.environ['DB_HOST']='project-db-campus.smhrd.com'
os.environ['DB_PORT']='1524'
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

print("="*60, file=sys.stderr)
print("Oracle 데이터베이스 연결 테스트", file=sys.stderr)
print("="*60, file=sys.stderr)
print("환경 변수 설정 완료", file=sys.stderr)
sys.stderr.flush()

try:
    import django
    print("Django 임포트 중...", file=sys.stderr)
    sys.stderr.flush()
    django.setup()
    print("Django 설정 완료", file=sys.stderr)
    sys.stderr.flush()
    
    from django.db import connection
    print("데이터베이스 연결 시도 중...", file=sys.stderr)
    sys.stderr.flush()
    
    cursor = connection.cursor()
    cursor.execute("SELECT USER, SYSDATE FROM DUAL")
    result = cursor.fetchone()
    
    print("\n" + "="*60, file=sys.stderr)
    print("✅ 연결 성공!", file=sys.stderr)
    print("="*60, file=sys.stderr)
    print(f"사용자: {result[0]}", file=sys.stderr)
    print(f"서버 시간: {result[1]}", file=sys.stderr)
    print("="*60, file=sys.stderr)
    sys.stderr.flush()
    
    # 표준 출력에도 결과 출력
    print("SUCCESS")
    print(f"User: {result[0]}")
    print(f"Time: {result[1]}")
    sys.stdout.flush()
    
except Exception as e:
    print("\n" + "="*60, file=sys.stderr)
    print("❌ 연결 실패!", file=sys.stderr)
    print("="*60, file=sys.stderr)
    print(f"오류 타입: {type(e).__name__}", file=sys.stderr)
    print(f"오류 메시지: {str(e)}", file=sys.stderr)
    print("="*60, file=sys.stderr)
    import traceback
    traceback.print_exc(file=sys.stderr)
    sys.stderr.flush()
    
    print("FAILED")
    print(str(e))
    sys.stdout.flush()

