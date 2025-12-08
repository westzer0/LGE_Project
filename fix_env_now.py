#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
from pathlib import Path

env_path = Path('.env')
if not env_path.exists():
    print("[ERROR] .env 파일을 찾을 수 없습니다.", file=sys.stderr)
    sys.exit(1)

print("[INFO] .env 파일 인코딩 변환 시작...")

# 여러 인코딩 시도
encodings = ['utf-8', 'cp949', 'euc-kr', 'latin-1', 'windows-1252', 'utf-16', 'utf-16-le', 'utf-16-be']
content = None
detected_encoding = None

for encoding in encodings:
    try:
        with open(env_path, 'r', encoding=encoding, errors='replace') as f:
            content = f.read()
        detected_encoding = encoding
        print(f"[INFO] {encoding} 인코딩으로 읽기 성공")
        break
    except (UnicodeDecodeError, UnicodeError):
        continue
    except Exception as e:
        print(f"[WARNING] {encoding} 시도 중 오류: {e}")
        continue

if content is None:
    print("[ERROR] 모든 인코딩 시도 실패. 파일이 손상되었을 수 있습니다.", file=sys.stderr)
    sys.exit(1)

if detected_encoding == 'utf-8':
    print("[INFO] 파일이 이미 UTF-8 인코딩입니다.")
    sys.exit(0)

# 백업 생성
backup = env_path.with_suffix('.env.backup')
if backup.exists():
    backup = env_path.with_suffix(f'.env.backup.{detected_encoding}')
try:
    with open(backup, 'w', encoding=detected_encoding) as f:
        f.write(content)
    print(f"[INFO] 백업 생성: {backup} (인코딩: {detected_encoding})")
except Exception as e:
    print(f"[WARNING] 백업 생성 실패: {e}")

# UTF-8로 저장
try:
    with open(env_path, 'w', encoding='utf-8', newline='') as f:
        f.write(content)
    print("[SUCCESS] UTF-8로 변환 완료!")
    sys.exit(0)
except Exception as e:
    print(f"[ERROR] UTF-8 저장 실패: {e}", file=sys.stderr)
    sys.exit(1)
