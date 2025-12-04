#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Oracle DB 간단 연결 테스트 - 결과를 콘솔과 파일에 출력
"""

import sys
from pathlib import Path
from datetime import datetime

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

result_file = "oracle_connection_test.txt"

def log(msg):
    """콘솔 출력 + 파일 저장"""
    print(msg)
    with open(result_file, 'a', encoding='utf-8') as f:
        f.write(msg + '\n')

# 파일 초기화
with open(result_file, 'w', encoding='utf-8') as f:
    f.write(f"Oracle DB 연결 테스트 결과\n")
    f.write(f"테스트 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    f.write("="*60 + "\n\n")

log("="*60)
log("Oracle DB 연결 테스트 시작")
log("="*60)

try:
    log("\n[1단계] 모듈 import 중...")
    from api.db.oracle_client import get_connection, fetch_one, fetch_all_dict
    log("✅ 모듈 import 성공")
    
    log("\n[2단계] 연결 테스트 중...")
    result = fetch_one("SELECT USER, SYSDATE, '연결 성공!' FROM DUAL")
    
    if result:
        log("✅ 연결 성공!")
        log(f"   사용자: {result[0]}")
        log(f"   서버 시간: {result[1]}")
        log(f"   상태: {result[2]}")
    else:
        log("⚠️ 연결은 되었지만 결과가 없습니다.")
    
    log("\n[3단계] 테이블 목록 조회 중...")
    tables = fetch_all_dict("""
        SELECT table_name 
        FROM user_tables 
        ORDER BY table_name
    """)
    
    if tables:
        log(f"\n✅ 발견된 테이블: {len(tables)}개\n")
        for i, t in enumerate(tables, 1):
            table_name = t['TABLE_NAME']
            # 행 개수 조회
            try:
                count_result = fetch_one(f"SELECT COUNT(*) FROM {table_name}")
                row_count = count_result[0] if count_result else 0
                log(f"  {i}. {table_name} ({row_count:,}개 행)")
            except Exception as e:
                log(f"  {i}. {table_name} (행 개수 조회 실패: {str(e)})")
    else:
        log("⚠️ 테이블이 없습니다.")
    
    log("\n" + "="*60)
    log("✅ 연결 테스트 완료!")
    log("="*60)
    log(f"\n결과가 '{result_file}' 파일에도 저장되었습니다.")
    
except ImportError as e:
    log(f"\n❌ 모듈 import 실패: {e}")
    import traceback
    log(traceback.format_exc())
except Exception as e:
    log(f"\n❌ 오류 발생: {type(e).__name__}: {e}")
    import traceback
    log(traceback.format_exc())


