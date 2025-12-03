"""
WSGI config for config project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/wsgi/
"""

import os

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

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

application = get_wsgi_application()
