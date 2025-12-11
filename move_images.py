#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
이미지 파일 이동 스크립트
images/다운로드 이미지 하위 폴더의 모든 이미지를 images/Download Images로 이동
"""

import os
import shutil
from pathlib import Path

# 이미지 파일 확장자
IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.avif', '.svg', '.ico'}

def get_unique_filename(dest_dir, filename):
    """
    파일명이 겹치면 숫자를 붙여서 고유한 파일명 생성
    
    Args:
        dest_dir: 대상 디렉토리 경로
        filename: 원본 파일명
    
    Returns:
        고유한 파일명 (경로 포함)
    """
    dest_path = dest_dir / filename
    
    # 파일이 존재하지 않으면 그대로 반환
    if not dest_path.exists():
        return dest_path
    
    # 파일명과 확장자 분리
    stem = dest_path.stem
    suffix = dest_path.suffix
    
    # 숫자를 붙여서 고유한 파일명 찾기
    counter = 1
    while True:
        new_filename = f"{stem}_{counter}{suffix}"
        new_path = dest_dir / new_filename
        if not new_path.exists():
            return new_path
        counter += 1

def is_image_file(filepath):
    """
    파일이 이미지 파일인지 확인
    
    Args:
        filepath: 파일 경로
    
    Returns:
        이미지 파일이면 True, 아니면 False
    """
    return filepath.suffix.lower() in IMAGE_EXTENSIONS

def move_images_from_subfolders(source_dir, dest_dir):
    """
    소스 디렉토리의 모든 하위 폴더에서 이미지를 찾아 대상 디렉토리로 이동
    
    Args:
        source_dir: 소스 디렉토리 (images/다운로드 이미지)
        dest_dir: 대상 디렉토리 (images/Download Images)
    """
    source_path = Path(source_dir)
    dest_path = Path(dest_dir)
    
    # 대상 디렉토리가 없으면 생성
    dest_path.mkdir(parents=True, exist_ok=True)
    
    print(f"[시작] 소스 디렉토리: {source_path}")
    print(f"[시작] 대상 디렉토리: {dest_path}")
    print("-" * 80)
    
    moved_count = 0
    skipped_count = 0
    folders_to_remove = []
    
    # 모든 하위 폴더를 재귀적으로 탐색
    for root, dirs, files in os.walk(source_path):
        root_path = Path(root)
        
        # 소스 디렉토리 자체는 건너뛰기
        if root_path == source_path:
            continue
        
        # 각 파일 확인
        for file in files:
            file_path = root_path / file
            
            # 이미지 파일인지 확인
            if not is_image_file(file_path):
                continue
            
            try:
                # 고유한 파일명 생성
                dest_file_path = get_unique_filename(dest_path, file)
                
                # 파일 이동
                shutil.move(str(file_path), str(dest_file_path))
                
                if dest_file_path.name != file:
                    print(f"[이동] {file_path.relative_to(source_path)} -> {dest_file_path.name} (이름 변경)")
                else:
                    print(f"[이동] {file_path.relative_to(source_path)} -> {dest_file_path.name}")
                
                moved_count += 1
                
            except Exception as e:
                print(f"[오류] {file_path.relative_to(source_path)} 이동 실패: {e}")
                skipped_count += 1
        
        # 빈 폴더인지 확인 (나중에 삭제하기 위해)
        try:
            if root_path != source_path:
                # 폴더 내에 파일이나 하위 폴더가 있는지 확인
                has_content = any(root_path.iterdir())
                if not has_content:
                    folders_to_remove.append(root_path)
        except Exception as e:
            print(f"[오류] {root_path} 확인 실패: {e}")
    
    # 빈 폴더 삭제 (깊은 폴더부터 삭제하기 위해 정렬)
    folders_to_remove.sort(key=lambda p: len(p.parts), reverse=True)
    
    removed_folders = 0
    for folder_path in folders_to_remove:
        try:
            # 폴더가 정말 비어있는지 다시 확인
            if not any(folder_path.iterdir()):
                folder_path.rmdir()
                print(f"[삭제] 빈 폴더: {folder_path.relative_to(source_path)}")
                removed_folders += 1
        except Exception as e:
            print(f"[오류] {folder_path.relative_to(source_path)} 삭제 실패: {e}")
    
    print("-" * 80)
    print(f"[완료] 이동된 파일: {moved_count}개")
    print(f"[완료] 건너뛴 파일: {skipped_count}개")
    print(f"[완료] 삭제된 폴더: {removed_folders}개")

def main():
    """메인 함수"""
    # 프로젝트 루트 디렉토리
    project_root = Path(__file__).resolve().parent
    
    # 소스 디렉토리: api/static/images/다운로드 이미지
    source_dir = project_root / 'api' / 'static' / 'images' / '다운로드 이미지'
    
    # 대상 디렉토리: api/static/images/Download Images
    dest_dir = project_root / 'api' / 'static' / 'images' / 'Download Images'
    
    # 소스 디렉토리 존재 확인
    if not source_dir.exists():
        print(f"[오류] 소스 디렉토리를 찾을 수 없습니다: {source_dir}")
        return
    
    # 이미지 이동 실행
    move_images_from_subfolders(source_dir, dest_dir)

if __name__ == '__main__':
    main()

