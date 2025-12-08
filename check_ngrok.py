#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""ngrok 상태 확인 및 문제 진단 스크립트"""

import os
import subprocess
import sys
from pathlib import Path

def run_command(cmd, cwd=None):
    """명령어 실행하고 결과 반환"""
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            cwd=cwd,
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='ignore'
        )
        return result.returncode, result.stdout, result.stderr
    except Exception as e:
        return -1, "", str(e)

def main():
    print("=" * 50)
    print("  ngrok 문제 진단")
    print("=" * 50)
    print()
    
    project_root = Path(__file__).parent
    ngrok_exe = project_root / "ngrok" / "ngrok.exe"
    
    # 1. ngrok.exe 확인
    print("[1/5] ngrok.exe 파일 확인...")
    if ngrok_exe.exists():
        print(f"  [OK] ngrok.exe 발견: {ngrok_exe}")
    else:
        print(f"  [ERROR] ngrok.exe를 찾을 수 없습니다: {ngrok_exe}")
        print("  해결방법: powershell -ExecutionPolicy Bypass -File setup_ngrok_simple.ps1")
        return 1
    
    # 2. ngrok 버전 확인
    print()
    print("[2/5] ngrok 버전 확인...")
    exit_code, stdout, stderr = run_command(f'"{ngrok_exe}" version', cwd=str(project_root))
    if exit_code == 0:
        print(f"  [OK] ngrok 버전 확인 성공")
        if stdout.strip():
            print(f"  출력: {stdout.strip()}")
    else:
        print(f"  [WARNING] ngrok 버전 확인 실패 (Exit code: {exit_code})")
        if stderr:
            print(f"  에러: {stderr.strip()}")
    
    # 3. 인증 토큰 확인
    print()
    print("[3/5] 인증 토큰 확인...")
    exit_code, stdout, stderr = run_command(f'"{ngrok_exe}" config check', cwd=str(project_root))
    if exit_code == 0:
        print("  [OK] 인증 토큰이 설정되어 있습니다")
        if stdout.strip():
            print(f"  출력: {stdout.strip()}")
    else:
        print("  [ERROR] 인증 토큰이 설정되지 않았습니다!")
        print()
        print("  이것이 ngrok이 작동하지 않는 가장 흔한 원인입니다.")
        print()
        print("  해결 방법:")
        print("  1. https://dashboard.ngrok.com/get-started/your-authtoken 접속")
        print("  2. 무료 계정으로 가입 (또는 로그인)")
        print("  3. 인증 토큰 복사")
        print("  4. 다음 명령 실행:")
        print(f'     "{ngrok_exe}" config add-authtoken YOUR_TOKEN')
        if stderr:
            print(f"  에러 메시지: {stderr.strip()}")
    
    # 4. 포트 8000 확인
    print()
    print("[4/5] 포트 8000 사용 확인...")
    exit_code, stdout, stderr = run_command("netstat -ano | findstr :8000", cwd=str(project_root))
    if exit_code == 0 and stdout.strip():
        print("  [WARNING] 포트 8000이 사용 중입니다")
        print(f"  {stdout.strip()}")
    else:
        print("  [OK] 포트 8000이 사용 가능합니다")
    
    # 5. 실행 중인 ngrok 프로세스 확인
    print()
    print("[5/5] 실행 중인 ngrok 프로세스 확인...")
    exit_code, stdout, stderr = run_command("tasklist | findstr ngrok.exe", cwd=str(project_root))
    if exit_code == 0 and stdout.strip():
        print("  [WARNING] 실행 중인 ngrok 프로세스 발견:")
        print(f"  {stdout.strip()}")
    else:
        print("  [OK] 실행 중인 ngrok 프로세스가 없습니다")
    
    print()
    print("=" * 50)
    print("  진단 완료")
    print("=" * 50)
    print()
    print("다음 단계:")
    print("  1. 인증 토큰이 설정되지 않았다면 위의 방법으로 설정")
    print("  2. 서버 시작: .\\start_ngrok.bat")
    print("     또는: .\\start_server_fixed.bat")
    print()
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
