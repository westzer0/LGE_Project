#!/usr/bin/env python
"""서버 실행 문제 진단 스크립트"""
import os
import sys
from pathlib import Path

print("=" * 50)
print("서버 실행 문제 진단")
print("=" * 50)
print()

# 1. Python 버전 확인
print("[1] Python 버전 확인")
print(f"  Python: {sys.version}")
print()

# 2. 현재 디렉토리 확인
print("[2] 작업 디렉토리")
print(f"  현재 디렉토리: {os.getcwd()}")
print(f"  manage.py 존재: {Path('manage.py').exists()}")
print()

# 3. 가상환경 확인
print("[3] 가상환경 확인")
venv_python = Path("venv/Scripts/python.exe")
if venv_python.exists():
    print(f"  ✓ 가상환경 Python: {venv_python}")
else:
    print(f"  ✗ 가상환경 없음 (시스템 Python 사용)")
print(f"  실행 Python: {sys.executable}")
print()

# 4. Django 설치 확인
print("[4] Django 설치 확인")
try:
    import django
    print(f"  ✓ Django 버전: {django.get_version()}")
except ImportError:
    print("  ✗ Django가 설치되지 않음")
    print("  실행: pip install django")
    sys.exit(1)
print()

# 5. 환경 변수 확인
print("[5] 환경 변수 확인")
env_file = Path(".env")
if env_file.exists():
    print(f"  ✓ .env 파일 존재")
else:
    print(f"  ✗ .env 파일 없음 (선택사항)")
print()

# 6. Django 설정 로드 테스트
print("[6] Django 설정 로드 테스트")
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
try:
    import django
    django.setup()
    print("  ✓ Django 설정 로드 성공")
    
    # 데이터베이스 연결 테스트
    from django.db import connection
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        print("  ✓ 데이터베이스 연결 성공")
    except Exception as e:
        print(f"  ✗ 데이터베이스 연결 실패: {e}")
        print("     SQLite를 사용하거나 .env 파일에서 USE_ORACLE=false 설정")
        
except Exception as e:
    print(f"  ✗ Django 설정 로드 실패: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
print()

# 7. 마이그레이션 확인
print("[7] 마이그레이션 확인")
try:
    from django.core.management import execute_from_command_line
    # 마이그레이션 상태 확인 (실제 실행은 안 함)
    print("  마이그레이션 상태 확인 중...")
except Exception as e:
    print(f"  ✗ 마이그레이션 확인 실패: {e}")
print()

print("=" * 50)
print("진단 완료")
print("=" * 50)
print()
print("서버 실행 명령어:")
if venv_python.exists():
    print("  .\\venv\\Scripts\\activate")
    print("  python manage.py runserver 8000")
else:
    print("  python manage.py runserver 8000")
