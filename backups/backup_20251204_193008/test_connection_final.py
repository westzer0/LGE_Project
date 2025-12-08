#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import sys

# 환경 변수 설정
os.environ['DB_NAME'] = 'MAPPP'
os.environ['DB_USER'] = 'campus_24K_LG3_DX7_p3_4'
os.environ['DB_PASSWORD'] = 'smhrd4'
os.environ['DB_HOST'] = 'project-db-campus.smhrd.com'
os.environ['DB_PORT'] = '1524'
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

try:
    import django
    django.setup()
    
    from django.db import connection
    
    # 연결 정보 출력
    db_config = connection.settings_dict
    print("="*60, file=sys.stderr)
    print("Oracle DB 연결 테스트", file=sys.stderr)
    print("="*60, file=sys.stderr)
    print(f"HOST: {db_config.get('HOST')}", file=sys.stderr)
    print(f"PORT: {db_config.get('PORT')}", file=sys.stderr)
    print(f"NAME: {db_config.get('NAME')}", file=sys.stderr)
    print(f"USER: {db_config.get('USER')}", file=sys.stderr)
    print(f"PASSWORD: {'설정됨' if db_config.get('PASSWORD') else '없음'}", file=sys.stderr)
    
    # 연결 테스트
    print("\n연결 시도 중...", file=sys.stderr)
    with connection.cursor() as cursor:
        cursor.execute("SELECT USER, SYSDATE FROM DUAL")
        result = cursor.fetchone()
        print(f"\n✅ 연결 성공!", file=sys.stderr)
        print(f"사용자: {result[0]}", file=sys.stderr)
        print(f"서버 시간: {result[1]}", file=sys.stderr)
        print("\n✅ 데이터베이스 연결이 정상적으로 작동합니다!", file=sys.stderr)
        print("SUCCESS")
        sys.exit(0)
        
except Exception as e:
    print(f"\n❌ 연결 실패!", file=sys.stderr)
    print(f"오류: {type(e).__name__}: {str(e)}", file=sys.stderr)
    import traceback
    traceback.print_exc(file=sys.stderr)
    print("FAILED")
    sys.exit(1)

