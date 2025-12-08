#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""강화된 .env 파일 인코딩 변환 스크립트"""

import sys
from pathlib import Path

def detect_and_convert():
    env_path = Path('.env')
    
    if not env_path.exists():
        print("[ERROR] .env 파일을 찾을 수 없습니다.", file=sys.stderr)
        return False
    
    print("[INFO] .env 파일 인코딩 변환 시작...")
    
    # 바이너리로 읽기
    try:
        with open(env_path, 'rb') as f:
            raw_bytes = f.read()
    except Exception as e:
        print(f"[ERROR] 파일 읽기 실패: {e}", file=sys.stderr)
        return False
    
    # 여러 인코딩 시도
    encodings = [
        ('utf-8', 'strict'),
        ('utf-8-sig', 'strict'),  # BOM이 있는 UTF-8
        ('cp949', 'replace'),      # 손상된 바이트는 대체
        ('euc-kr', 'replace'),
        ('latin-1', 'strict'),      # 모든 바이트를 문자로 변환
        ('windows-1252', 'replace'),
    ]
    
    content = None
    detected_encoding = None
    
    for encoding, error_handling in encodings:
        try:
            content = raw_bytes.decode(encoding, errors=error_handling)
            detected_encoding = encoding
            print(f"[INFO] {encoding} 인코딩으로 읽기 성공 (오류 처리: {error_handling})")
            break
        except (UnicodeDecodeError, UnicodeError) as e:
            continue
        except Exception as e:
            print(f"[WARNING] {encoding} 시도 중 오류: {e}")
            continue
    
    if content is None:
        print("[ERROR] 모든 인코딩 시도 실패.", file=sys.stderr)
        return False
    
    if detected_encoding in ('utf-8', 'utf-8-sig'):
        print("[INFO] 파일이 이미 UTF-8 인코딩입니다.")
        return True
    
    # 백업 생성
    backup = env_path.with_suffix('.env.backup')
    counter = 1
    while backup.exists():
        backup = env_path.with_suffix(f'.env.backup.{counter}')
        counter += 1
    
    try:
        with open(backup, 'wb') as f:
            f.write(raw_bytes)
        print(f"[INFO] 원본 백업 생성: {backup}")
    except Exception as e:
        print(f"[WARNING] 백업 생성 실패: {e}")
    
    # UTF-8로 저장
    try:
        with open(env_path, 'w', encoding='utf-8', newline='') as f:
            f.write(content)
        print("[SUCCESS] .env 파일을 UTF-8로 변환했습니다!")
        print(f"  원본 인코딩: {detected_encoding}")
        return True
    except Exception as e:
        print(f"[ERROR] UTF-8 저장 실패: {e}", file=sys.stderr)
        return False

if __name__ == '__main__':
    success = detect_and_convert()
    sys.exit(0 if success else 1)
