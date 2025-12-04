#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
oci.dll 파일 찾기 스크립트
"""
from pathlib import Path

print("="*60)
print("oci.dll 파일 찾기")
print("="*60)

# 확인할 경로
check_path = Path(r"C:\oraclexe\instantclient-basic-windows.x64-23.26.0.0.0")

print(f"\n1. 지정된 경로 확인:")
print(f"   {check_path}")

if check_path.exists():
    print(f"   ✅ 경로 존재")
    
    # 바로 여기 있는지 확인
    oci_dll = check_path / "oci.dll"
    print(f"\n   oci.dll 바로 여기: {oci_dll.exists()}")
    
    if oci_dll.exists():
        print(f"   ✅ 찾았습니다! 올바른 경로입니다.")
        print(f"\n   사용할 경로: {check_path}")
    else:
        print(f"   ❌ 여기는 없습니다. 하위 폴더 확인 중...")
        
        # 하위 폴더에서 찾기
        found = False
        for subdir in check_path.iterdir():
            if subdir.is_dir():
                oci_in_sub = subdir / "oci.dll"
                if oci_in_sub.exists():
                    print(f"\n   ✅ 하위 폴더에서 발견!")
                    print(f"   경로: {subdir}")
                    print(f"   oci.dll: {oci_in_sub}")
                    print(f"\n   올바른 경로: {subdir}")
                    print(f"\n   .env 파일에 다음을 사용하세요:")
                    print(f"   ORACLE_INSTANT_CLIENT_PATH={subdir}")
                    found = True
                    break
        
        if not found:
            print(f"\n   ❌ 하위 폴더에도 없습니다.")
            print(f"\n   폴더 내용:")
            for item in list(check_path.iterdir())[:10]:
                if item.is_dir():
                    print(f"   📁 {item.name}/")
                else:
                    print(f"   📄 {item.name}")
else:
    print(f"   ❌ 경로가 존재하지 않습니다!")

# C:\oraclexe 전체에서 찾기
print(f"\n" + "="*60)
print("2. C:\\oraclexe 전체에서 oci.dll 찾기:")
print("="*60)

try:
    import os
    for root, dirs, files in os.walk(r"C:\oraclexe"):
        if "oci.dll" in files:
            oci_path = Path(root) / "oci.dll"
            print(f"   ✅ 발견: {oci_path}")
            print(f"   폴더: {root}")
            print(f"\n   올바른 경로: {root}")
            print(f"\n   .env 파일에 다음을 사용하세요:")
            print(f"   ORACLE_INSTANT_CLIENT_PATH={root}")
            break
    else:
        print("   ❌ C:\\oraclexe에서 찾을 수 없습니다.")
except Exception as e:
    print(f"   오류: {e}")

print("\n" + "="*60)



