#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""간단한 .env 파일 인코딩 변환 스크립트"""

from pathlib import Path
import sys
import os

def main():
    env_path = Path('.env')
    
    if not env_path.exists():
        print(f"[ERROR] .env 파일을 찾을 수 없습니다.", flush=True)
        print(f"  env.example 파일을 복사하여 .env 파일을 만드세요.", flush=True)
        return False
    
    print(f"[INFO] .env 파일 인코딩 변환 시작...", flush=True)
    
    # 먼저 UTF-8로 읽기 시도
    try:
        with open(env_path, 'r', encoding='utf-8') as f:
            content = f.read()
        print(f"[INFO] 파일이 이미 UTF-8 인코딩입니다.", flush=True)
        return True
    except UnicodeDecodeError:
        pass
    except Exception as e:
        print(f"[WARNING] UTF-8 읽기 실패: {e}", flush=True)
    
    # CP949로 읽기 시도
    try:
        with open(env_path, 'r', encoding='cp949') as f:
            content = f.read()
        print(f"[INFO] CP949 인코딩으로 읽기 성공", flush=True)
        
        # 백업 생성
        backup_path = env_path.with_suffix('.env.backup')
        if backup_path.exists():
            backup_path = env_path.with_suffix('.env.backup.old')
        with open(backup_path, 'w', encoding='cp949') as f:
            f.write(content)
        print(f"[INFO] 백업 파일 생성: {backup_path}", flush=True)
        
        # UTF-8로 저장
        with open(env_path, 'w', encoding='utf-8', newline='') as f:
            f.write(content)
        print(f"[SUCCESS] .env 파일을 UTF-8로 변환했습니다!", flush=True)
        return True
        
    except Exception as e:
        print(f"[ERROR] 변환 실패: {e}", flush=True)
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    try:
        success = main()
        sys.stdout.flush()
        sys.stderr.flush()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"[FATAL ERROR] {e}", flush=True)
        import traceback
        traceback.print_exc()
        sys.exit(1)
