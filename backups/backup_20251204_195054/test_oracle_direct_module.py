#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Oracle 직접 연결 모듈 테스트
api/db/oracle_client.py 모듈이 정상 작동하는지 확인
"""
import sys
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

print("="*60)
print("Oracle 직접 연결 모듈 테스트")
print("="*60)

try:
    from api.db import fetch_one, fetch_all_dict, fetch_one_dict
    print("✅ 모듈 임포트 성공!")
except ImportError as e:
    print(f"❌ 모듈 임포트 실패: {e}")
    sys.exit(1)

print("\n연결 테스트 중...")

try:
    # 간단한 쿼리로 연결 확인
    result = fetch_one("SELECT USER, SYSDATE, '연결 성공!' FROM DUAL")
    
    if result:
        print("\n" + "="*60)
        print("✅ 연결 성공!")
        print("="*60)
        print(f"사용자: {result[0]}")
        print(f"서버 시간: {result[1]}")
        print(f"상태: {result[2]}")
        print("="*60)
        
        # 딕셔너리 형태로도 테스트
        print("\n딕셔너리 형태 테스트:")
        result_dict = fetch_one_dict("SELECT USER as username, SYSDATE as server_time FROM DUAL")
        if result_dict:
            print(f"  사용자: {result_dict['USERNAME']}")
            print(f"  서버 시간: {result_dict['SERVER_TIME']}")
        
        print("\n✅ 모든 테스트 성공!")
        print("\n이제 Django View나 Service에서 다음과 같이 사용할 수 있습니다:")
        print("  from api.db import fetch_all_dict, fetch_one_dict")
        print("  products = fetch_all_dict('SELECT * FROM products')")
        sys.exit(0)
    else:
        print("❌ 쿼리 결과가 없습니다.")
        sys.exit(1)
        
except Exception as e:
    print("\n" + "="*60)
    print("❌ 테스트 실패!")
    print("="*60)
    print(f"오류: {type(e).__name__}: {str(e)}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

