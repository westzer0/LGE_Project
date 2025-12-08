#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Oracle DDL 스크립트를 실행하는 유틸리티

사용법:
    python api/db/execute_ddl.py
"""

import sys
from pathlib import Path

# 프로젝트 루트를 sys.path에 추가
BASE_DIR = Path(__file__).resolve().parent.parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from api.db.oracle_client import get_connection

DDL_FILE = Path(__file__).parent / "csv_data_tables_ddl.sql"


def execute_ddl():
    """DDL 파일을 읽어서 실행"""
    if not DDL_FILE.exists():
        print(f"[오류] DDL 파일을 찾을 수 없습니다: {DDL_FILE}")
        return False
    
    print(f"[읽기] DDL 파일: {DDL_FILE}")
    
    with open(DDL_FILE, 'r', encoding='utf-8') as f:
        ddl_content = f.read()
    
    # SQL 문을 세미콜론으로 분리
    # 주석과 빈 줄 제거
    statements = []
    current_statement = []
    
    for line in ddl_content.split('\n'):
        line = line.strip()
        if not line or line.startswith('--'):
            continue
        
        current_statement.append(line)
        
        if line.endswith(';'):
            statement = ' '.join(current_statement)
            if statement.strip() and statement.strip() != ';':
                statements.append(statement.rstrip(';'))
            current_statement = []
    
    # 마지막 문장 처리
    if current_statement:
        statement = ' '.join(current_statement)
        if statement.strip():
            statements.append(statement)
    
    print(f"[발견] {len(statements)}개의 SQL 문")
    
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        for i, statement in enumerate(statements, 1):
            try:
                print(f"\n[{i}/{len(statements)}] 실행 중...")
                # DDL은 autocommit이므로 각각 실행
                cursor.execute(statement)
                print(f"  [성공] 완료")
            except Exception as e:
                # 테이블이 이미 존재하는 경우 등은 경고만 출력
                error_msg = str(e)
                if 'ORA-00955' in error_msg or 'already exists' in error_msg.lower():
                    print(f"  [경고] 이미 존재함: {error_msg}")
                else:
                    print(f"  [오류] {error_msg}")
                    raise
        
        conn.commit()
        print("\n[완료] 모든 DDL 문 실행 완료!")
        return True
        
    except Exception as e:
        conn.rollback()
        print(f"\n[실패] 오류 발생: {str(e)}")
        return False
    finally:
        cursor.close()
        conn.close()


if __name__ == "__main__":
    print("=" * 60)
    print("Oracle DDL 실행 스크립트")
    print("=" * 60)
    execute_ddl()

