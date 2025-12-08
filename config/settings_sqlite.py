"""
SQLite 설정 파일 (테스트용)

Oracle 11g 호환성 문제를 피하기 위해 SQLite 사용
테스트 시 이 파일을 settings.py로 복사하거나 import하여 사용
"""
from pathlib import Path
import os

BASE_DIR = Path(__file__).resolve().parent.parent

# SQLite 설정 (테스트용)
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

