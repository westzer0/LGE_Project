#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Oracle Instant Client 경로 확인 스크립트
설치된 경로를 자동으로 찾아서 알려줍니다
"""
from pathlib import Path
import os

print("="*60)
print("Oracle Instant Client 경로 확인")
print("="*60)

# 확인할 경로들
candidate_paths = [
    Path(r"C:\oraclexe\instantclient-basic-windows.x64-23.26.0.0.0"),
    Path(r"C:\oraclexe\instantclient_23_26"),
    Path(r"C:\oracle\instantclient_23_26"),
    Path(r"C:\oracle\instantclient_21_8"),
    Path(r"C:\oracle\instantclient_19_23"),
    Path(r"C:\instantclient_23_26"),
    Path(r"C:\instantclient"),
]

print("\n1. 사용자가 제공한 경로 확인:")
user_path = Path(r"C:\oraclexe\instantclient-basic-windows.x64-23.26.0.0.0")
print(f"   경로: {user_path}")
print(f"   존재: {user_path.exists()}")

if user_path.exists():
    print(f"   디렉토리: {user_path.is_dir()}")
    
    # oci.dll 파일 찾기
    oci_dll = user_path / "oci.dll"
    print(f"   oci.dll 존재: {oci_dll.exists()}")
    
    if oci_dll.exists():
        print(f"\n   ✅ 올바른 경로입니다!")
        print(f"   .env 파일에 다음을 추가하세요:")
        print(f"   ORACLE_INSTANT_CLIENT_PATH={user_path}")
    else:
        # 하위 폴더 확인
        print(f"\n   ⚠️  oci.dll을 찾을 수 없습니다.")
        print(f"   하위 폴더 확인 중...")
        
        subdirs = [d for d in user_path.iterdir() if d.is_dir()]
        found_oci = False
        
        for subdir in subdirs[:5]:  # 처음 5개만 확인
            oci_in_sub = subdir / "oci.dll"
            if oci_in_sub.exists():
                print(f"\n   ✅ 하위 폴더에서 발견: {subdir}")
                print(f"   .env 파일에 다음을 추가하세요:")
                print(f"   ORACLE_INSTANT_CLIENT_PATH={subdir}")
                found_oci = True
                break
        
        if not found_oci:
            print(f"   ❌ 하위 폴더에도 oci.dll을 찾을 수 없습니다.")
            print(f"   Instant Client가 제대로 압축 해제되지 않았을 수 있습니다.")

print("\n" + "="*60)
print("2. 일반적인 경로 확인:")
print("="*60)

found_paths = []
for path in candidate_paths:
    if path.exists():
        oci_dll = path / "oci.dll"
        if oci_dll.exists():
            found_paths.append(path)
            print(f"   ✅ {path}")
            print(f"      oci.dll 존재: {oci_dll.exists()}")

if not found_paths:
    print("   ❌ 일반적인 경로에서 Instant Client를 찾을 수 없습니다.")

print("\n" + "="*60)
print("3. 시스템 PATH에서 확인:")
print("="*60)

path_dirs = os.environ.get("PATH", "").split(os.pathsep)
found_in_path = []

for path_dir in path_dirs:
    if not path_dir:
        continue
    oci_dll = Path(path_dir) / "oci.dll"
    if oci_dll.exists():
        found_in_path.append(path_dir)
        print(f"   ✅ {path_dir}")

if not found_in_path:
    print("   ❌ PATH에서 Instant Client를 찾을 수 없습니다.")

print("\n" + "="*60)
print("4. 권장 사항:")
print("="*60)

# 최종 경로 결정
final_path = None

if user_path.exists():
    oci_dll = user_path / "oci.dll"
    if oci_dll.exists():
        final_path = user_path
    else:
        # 하위 폴더 확인
        for subdir in user_path.iterdir():
            if subdir.is_dir():
                oci_in_sub = subdir / "oci.dll"
                if oci_in_sub.exists():
                    final_path = subdir
                    break

if not final_path and found_paths:
    final_path = found_paths[0]

if final_path:
    print(f"\n✅ 사용할 경로: {final_path}")
    print(f"\n.env 파일에 다음을 추가하세요:")
    print(f"ORACLE_INSTANT_CLIENT_PATH={final_path}")
    print("\n또는 시스템 PATH에 추가:")
    print(f"{final_path}")
else:
    print("\n⚠️  올바른 Instant Client 경로를 찾을 수 없습니다.")
    print("\n확인 사항:")
    print("  1. Instant Client가 다운로드되었는지 확인")
    print("  2. 압축 파일을 올바르게 해제했는지 확인")
    print("  3. oci.dll 파일이 있는 폴더 경로 확인")
    print("\n일반적인 구조:")
    print("  C:\\oracle\\instantclient_23_26\\oci.dll")
    print("  C:\\oracle\\instantclient_21_8\\oci.dll")
    print("  C:\\oracle\\instantclient_19_23\\oci.dll")

print("="*60)


