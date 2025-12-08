#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""간단한 API 키 확인 스크립트"""
import os
import sys
from pathlib import Path

# .env 파일 로드
from dotenv import load_dotenv
env_path = Path('.env')
if env_path.exists():
    load_dotenv(env_path)
else:
    print("❌ .env 파일을 찾을 수 없습니다!")
    sys.exit(1)

# Django 설정 로드
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
import django
django.setup()

from django.conf import settings

print("\n" + "="*70)
print("API 키 확인 결과")
print("="*70 + "\n")

keys = {
    'OPENAI_API_KEY': (settings.OPENAI_API_KEY, 'OpenAI API'),
    'KAKAO_REST_API_KEY': (settings.KAKAO_REST_API_KEY, '카카오 REST API'),
    'KAKAO_JS_KEY': (settings.KAKAO_JS_KEY, '카카오 JavaScript'),
    'KAKAO_NATIVE_APP_KEY': (settings.KAKAO_NATIVE_APP_KEY, '카카오 네이티브 앱'),
    'KAKAO_ADMIN_KEY': (settings.KAKAO_ADMIN_KEY, '카카오 Admin'),
}

all_ok = True
for key, (value, desc) in keys.items():
    if value:
        masked = f"{value[:15]}...{value[-5:]}" if len(value) > 20 else value
        print(f"✅ {desc:20s} ({key})")
        print(f"   값: {masked} ({len(value)}자)")
    else:
        print(f"❌ {desc:20s} ({key}) - 미설정")
        all_ok = False
    print()

print("="*70)
if all_ok:
    print("✅ 모든 API 키가 정상적으로 로드되었습니다!")
else:
    print("⚠️  일부 API 키가 로드되지 않았습니다.")
print("="*70 + "\n")

# Save to file
result_file = Path('api_keys_status.txt')
with open(result_file, 'w', encoding='utf-8') as f:
    f.write("API 키 상태 확인 결과\n")
    f.write("="*70 + "\n\n")
    for key, (value, desc) in keys.items():
        status = "✓" if value else "✗"
        f.write(f"{status} {desc} ({key}): {len(value)}자\n")
    f.write("\n" + "="*70 + "\n")
    if all_ok:
        f.write("✅ 모든 API 키가 정상적으로 로드되었습니다!\n")
    else:
        f.write("⚠️  일부 API 키가 로드되지 않았습니다.\n")

print(f"결과가 {result_file} 파일에 저장되었습니다.")
