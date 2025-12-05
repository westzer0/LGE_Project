#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Oracle DB 연결 간단 테스트
"""

import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

output_file = "oracle_connection_test_result.txt"
output_lines = []

def log(msg):
    """콘솔 출력과 파일 저장"""
    print(msg)
    output_lines.append(msg)

log("="*60)
log("Oracle DB 연결 테스트")
log("="*60)

try:
    log("\n[1] 연결 모듈 import 중...")
    from api.db.oracle_client import get_connection, fetch_one, fetch_all_dict
    log("✅ 연결 모듈 import 성공")
    
    log("\n[2] 연결 테스트 중...")
    result = fetch_one("SELECT USER, SYSDATE, '연결 성공!' FROM DUAL")
    
    if result:
        log("✅ 연결 성공!")
        log(f"   사용자: {result[0]}")
        log(f"   서버 시간: {result[1]}")
        log(f"   상태: {result[2]}")
    else:
        log("⚠️ 연결은 되었지만 결과가 없습니다.")
    
    log("\n[3] 테이블 목록 조회 중...")
    tables = fetch_all_dict("""
        SELECT table_name 
        FROM user_tables 
        ORDER BY table_name
    """)
    
    if tables:
        log(f"✅ 발견된 테이블: {len(tables)}개")
        for i, t in enumerate(tables, 1):
            log(f"   {i}. {t['TABLE_NAME']}")
    else:
        log("⚠️ 테이블이 없습니다.")
    
    log("\n" + "="*60)
    log("연결 테스트 완료!")
    log("="*60)
    
    # 파일 저장
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(output_lines))
    log(f"\n✅ 결과가 '{output_file}' 파일에 저장되었습니다.")
    
except ImportError as e:
    error_msg = f"❌ 모듈 import 실패: {e}"
    log(error_msg)
    import traceback
    traceback.print_exc()
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(output_lines))
except Exception as e:
    error_msg = f"❌ 오류 발생: {type(e).__name__}: {e}"
    log(error_msg)
    import traceback
    traceback.print_exc()
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(output_lines))

