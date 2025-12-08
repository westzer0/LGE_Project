#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""데이터베이스 연결 검증 스크립트"""
import os
import sys

# 환경 변수 설정 (테스트용)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

# .env 파일이 없으면 환경 변수 직접 설정
if not os.path.exists('.env'):
    print("⚠️ .env 파일이 없습니다. 환경 변수를 직접 설정합니다.")
    os.environ['DB_NAME'] = 'MAPPP'
    os.environ['DB_USER'] = 'campus_24K_LG3_DX7_p3_4'
    os.environ['DB_PASSWORD'] = 'smhrd4'
    os.environ['DB_HOST'] = 'project-db-campus.smhrd.com'
    os.environ['DB_PORT'] = '1524'

try:
    import django
    django.setup()
    print("✅ Django 설정 완료")
except Exception as e:
    print(f"❌ Django 설정 실패: {e}")
    sys.exit(1)

from django.db import connection

print("\n" + "="*70)
print("Oracle 데이터베이스 연결 테스트")
print("="*70)

# 설정 정보 출력
db_config = connection.settings_dict
print(f"\n📋 연결 설정:")
print(f"   호스트: {db_config.get('HOST', 'N/A')}")
print(f"   포트: {db_config.get('PORT', 'N/A')}")
print(f"   서비스명: {db_config.get('NAME', 'N/A')}")
print(f"   사용자: {db_config.get('USER', 'N/A')}")
print(f"   비밀번호: {'***설정됨***' if db_config.get('PASSWORD') else '❌ 없음'}")

# 빈 값 확인
if not db_config.get('USER'):
    print("\n❌ 오류: DB_USER가 설정되지 않았습니다!")
    print("   .env 파일에 DB_USER를 설정하거나 환경 변수를 설정하세요.")
    sys.exit(1)

if not db_config.get('PASSWORD'):
    print("\n❌ 오류: DB_PASSWORD가 설정되지 않았습니다!")
    print("   .env 파일에 DB_PASSWORD를 설정하거나 환경 변수를 설정하세요.")
    sys.exit(1)

print("\n" + "-"*70)
print("🔌 데이터베이스 연결 시도 중...")

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
            cursor.execute("SELECT banner FROM v$version WHERE banner LIKE 'Oracle%'")
            version = cursor.fetchone()
            if version:
                print(f"   Oracle 버전: {version[0]}")
        except Exception as e:
            print(f"   버전 확인 실패 (무시): {e}")
        
        # 현재 사용자 확인
        try:
            cursor.execute("SELECT USER FROM DUAL")
            current_user = cursor.fetchone()
            if current_user:
                print(f"   현재 사용자: {current_user[0]}")
        except Exception as e:
            print(f"   사용자 확인 실패 (무시): {e}")
        
        print("\n" + "="*70)
        print("✅ 데이터베이스 연결이 정상적으로 작동합니다!")
        print("="*70)
        sys.exit(0)
        
except Exception as e:
    print(f"\n❌ 연결 실패!")
    print(f"   오류 타입: {type(e).__name__}")
    print(f"   오류 메시지: {str(e)}")
    print("\n" + "="*70)
    print("❌ 데이터베이스 연결에 실패했습니다.")
    print("="*70)
    print("\n가능한 원인:")
    print("1. 네트워크 연결 문제 (방화벽, VPN 등)")
    print("2. 데이터베이스 서버가 실행 중이 아님")
    print("3. 잘못된 연결 정보 (호스트, 포트, 서비스명)")
    print("4. 인증 실패 (사용자명 또는 비밀번호 오류)")
    print("5. Oracle Instant Client 또는 oracledb 패키지 문제")
    import traceback
    print("\n상세 오류:")
    traceback.print_exc()
    sys.exit(1)

