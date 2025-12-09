#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
ONBOARDING_SESSION 테이블의 날짜 관련 컬럼 확인
"""

import os
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

import django
django.setup()

from api.db.oracle_client import get_connection


def check_columns():
    """ONBOARDING_SESSION 테이블의 날짜 관련 컬럼 확인"""
    print("=" * 80)
    print("ONBOARDING_SESSION 테이블 날짜 컬럼 확인")
    print("=" * 80)
    
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                # 모든 컬럼 조회
                print("\n[1] 전체 컬럼 목록 조회...")
                cur.execute("""
                    SELECT COLUMN_NAME, DATA_TYPE, NULLABLE, DATA_DEFAULT
                    FROM USER_TAB_COLUMNS
                    WHERE TABLE_NAME = 'ONBOARDING_SESSION'
                    ORDER BY COLUMN_ID
                """)
                all_columns = cur.fetchall()
                print(f"  총 {len(all_columns)}개 컬럼 발견")
                
                # 날짜 관련 컬럼만 필터링
                date_columns = [col for col in all_columns if 'DATE' in col[0].upper() or 'AT' in col[0].upper()]
                
                print("\n[2] 날짜 관련 컬럼:")
                print("  " + "-" * 70)
                for col in date_columns:
                    print(f"    {col[0]:20s} | {col[1]:15s} | NULLABLE={col[2]:3s} | DEFAULT={str(col[3])[:30]}")
                print("  " + "-" * 70)
                
                # 문제 확인
                print("\n[3] 문제 확인:")
                has_created_date = any(col[0] == 'CREATED_DATE' for col in all_columns)
                has_created_at = any(col[0] == 'CREATED_AT' for col in all_columns)
                has_updated_date = any(col[0] == 'UPDATED_DATE' for col in all_columns)
                has_updated_at = any(col[0] == 'UPDATED_AT' for col in all_columns)
                
                issues = []
                
                if has_created_date and has_created_at:
                    issues.append("⚠️ CREATED_DATE와 CREATED_AT이 모두 존재합니다 (중복)")
                elif has_created_date and not has_created_at:
                    issues.append("⚠️ CREATED_DATE만 존재합니다 (CREATED_AT으로 변경 필요)")
                
                if has_updated_date and has_updated_at:
                    issues.append("⚠️ UPDATED_DATE와 UPDATED_AT이 모두 존재합니다 (중복)")
                elif has_updated_date and not has_updated_at:
                    issues.append("⚠️ UPDATED_DATE만 존재합니다 (UPDATED_AT으로 변경 필요)")
                
                if not issues:
                    print("  ✓ 문제 없음: 모든 날짜 컬럼이 올바르게 설정되어 있습니다.")
                else:
                    for issue in issues:
                        print(f"  {issue}")
                
                # 백엔드 코드와의 일치 여부 확인
                print("\n[4] 백엔드 코드와의 일치 여부:")
                backend_uses = {
                    'CREATED_AT': True,  # onboarding_db_service.py에서 사용
                    'UPDATED_AT': True,  # onboarding_db_service.py에서 사용
                    'COMPLETED_AT': True  # onboarding_db_service.py에서 사용
                }
                
                for col_name, used in backend_uses.items():
                    exists = any(col[0] == col_name for col in all_columns)
                    if exists and used:
                        print(f"  ✓ {col_name}: 백엔드에서 사용 중, 테이블에 존재함")
                    elif not exists and used:
                        print(f"  ✗ {col_name}: 백엔드에서 사용 중이지만 테이블에 없음!")
                    elif exists and not used:
                        print(f"  ⚠️ {col_name}: 테이블에 존재하지만 백엔드에서 사용 안함")
                
                print("\n" + "=" * 80)
                print("확인 완료!")
                print("=" * 80)
                
    except Exception as e:
        print(f"\n오류 발생: {str(e)}")
        import traceback
        print(traceback.format_exc())
        sys.exit(1)


if __name__ == '__main__':
    check_columns()

