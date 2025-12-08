"""
진행 상황 확인 스크립트
"""
import os
import glob
from datetime import datetime

log_dir = os.path.join(os.getcwd(), 'logs')
log_files = glob.glob(os.path.join(log_dir, 'score_products_*.log'))

if not log_files:
    print("진행 상황 로그 파일을 찾을 수 없습니다.")
    exit(1)

# 가장 최근 로그 파일
latest_log = max(log_files, key=os.path.getmtime)

print(f"=== 진행 상황 확인 ===\n")
print(f"로그 파일: {latest_log}\n")

with open(latest_log, 'r', encoding='utf-8') as f:
    lines = f.readlines()
    
    # 마지막 몇 줄 출력
    print("=== 최근 진행 상황 (마지막 10줄) ===")
    for line in lines[-10:]:
        print(line.rstrip())
    
    # 진행률 계산
    progress_lines = [l for l in lines if '진행률' in l]
    if progress_lines:
        last_progress = progress_lines[-1]
        print(f"\n=== 현재 진행률 ===")
        print(last_progress.rstrip())
    
    # 예상 남은 시간
    remaining_lines = [l for l in lines if '예상 남은 시간' in l]
    if remaining_lines:
        last_remaining = remaining_lines[-1]
        print(f"\n=== 예상 남은 시간 ===")
        print(last_remaining.rstrip())
    
    # 통계
    success_count = len([l for l in lines if '완료:' in l])
    error_count = len([l for l in lines if '건너뜀' in l])
    
    print(f"\n=== 통계 ===")
    print(f"완료된 Taste: {success_count}개")
    print(f"건너뛴 Taste: {error_count}개")
    print(f"총 처리: {success_count + error_count}개")

