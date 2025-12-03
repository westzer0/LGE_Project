#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys

# Oracle Instant Client 초기화 (Thick 모드, DB 버전이 낮은 경우 필요)
# Django settings 로드 전에 실행되어야 함
try:
    from oracle_init import init_oracle_client
    init_oracle_client()
except ImportError:
    # oracle_init.py가 없으면 스킵 (Thin 모드 사용)
    pass
except Exception as e:
    # 초기화 실패해도 계속 진행 (Thin 모드로 시도)
    print(f"[Warning] Oracle Instant Client 초기화 실패: {e}")
    print("Thin 모드로 시도합니다. (DB 버전이 낮으면 연결 실패할 수 있음)")


def main():
    """Run administrative tasks."""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()
