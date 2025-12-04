#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
온보딩 테이블을 Oracle DB에 자동으로 생성하는 스크립트
"""
import sys
import os
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

from api.db.oracle_client import get_connection
import oracledb


def execute_sql_file(conn, sql_file_path):
    """SQL 파일을 읽어서 실행"""
    with open(sql_file_path, 'r', encoding='utf-8') as f:
        sql_content = f.read()
    
    # SQL 문을 세미콜론으로 분리 (Oracle은 세미콜론이 필요 없지만, 주석 처리)
    # 각 SQL 문을 개별적으로 실행
    statements = []
    current_statement = []
    
    for line in sql_content.split('\n'):
        line = line.strip()
        if not line or line.startswith('--'):
            continue
        
        # 주석 제거 (-- 이후 부분)
        if '--' in line:
            line = line[:line.index('--')].strip()
        
        if line:
            current_statement.append(line)
            # 세미콜론으로 문장 종료
            if line.endswith(';'):
                statement = ' '.join(current_statement)
                if statement:
                    statements.append(statement.rstrip(';'))
                current_statement = []
    
    # 마지막 문장 처리
    if current_statement:
        statement = ' '.join(current_statement)
        if statement:
            statements.append(statement)
    
    # 각 SQL 문 실행
    with conn.cursor() as cur:
        for i, statement in enumerate(statements, 1):
            try:
                print(f"[{i}/{len(statements)}] 실행 중...")
                # CREATE TABLE, ALTER TABLE 등은 execute로 실행
                if any(keyword in statement.upper() for keyword in ['CREATE', 'ALTER', 'DROP', 'INSERT', 'UPDATE', 'DELETE', 'COMMIT']):
                    cur.execute(statement)
                    print(f"  ✓ 성공: {statement[:50]}...")
                else:
                    # SELECT 등은 fetch 필요
                    cur.execute(statement)
                    print(f"  ✓ 성공: {statement[:50]}...")
            except Exception as e:
                print(f"  ✗ 실패: {statement[:50]}...")
                print(f"    오류: {str(e)}")
                # 일부 오류는 무시 (예: 테이블이 이미 존재하는 경우)
                if 'already exists' in str(e).lower() or 'name is already used' in str(e).lower():
                    print(f"    (이미 존재하는 객체이므로 무시)")
                else:
                    raise
    
    conn.commit()
    print(f"\n총 {len(statements)}개 SQL 문 실행 완료")


def check_table_exists(conn, table_name):
    """테이블이 존재하는지 확인"""
    with conn.cursor() as cur:
        cur.execute("""
            SELECT COUNT(*) FROM USER_TABLES WHERE TABLE_NAME = :table_name
        """, {'table_name': table_name.upper()})
        result = cur.fetchone()
        return result[0] > 0 if result else False


def main():
    """메인 함수"""
    print("=" * 60)
    print("온보딩 테이블 생성 스크립트")
    print("=" * 60)
    
    try:
        # Oracle DB 연결
        print("\n[1] Oracle DB 연결 중...")
        conn = get_connection()
        print("  ✓ 연결 성공!")
        
        # 테이블 존재 여부 확인
        print("\n[2] 기존 테이블 확인 중...")
        tables = [
            'ONBOARDING_QUESTION',
            'ONBOARDING_ANSWER',
            'ONBOARDING_SESSION',
            'ONBOARDING_USER_RESPONSE'
        ]
        
        existing_tables = []
        for table in tables:
            if check_table_exists(conn, table):
                existing_tables.append(table)
                print(f"  ⚠ {table} 테이블이 이미 존재합니다.")
        
        if existing_tables:
            print(f"\n⚠ 경고: {len(existing_tables)}개 테이블이 이미 존재합니다.")
            print("기존 테이블에 ALTER TABLE을 실행하여 누락된 칼럼을 추가합니다...")
            
            # ALTER TABLE 스크립트 실행
            alter_file = BASE_DIR / 'api' / 'db' / 'onboarding_tables_alter.sql'
            if alter_file.exists():
                print(f"\n[3] ALTER TABLE 스크립트 실행 중... ({alter_file})")
                try:
                    execute_sql_file(conn, alter_file)
                    print("  ✓ ALTER TABLE 완료!")
                except Exception as e:
                    print(f"  ✗ ALTER TABLE 실패: {str(e)}")
                    print("    (일부 칼럼이 이미 존재할 수 있습니다)")
                    # 칼럼 존재 여부 확인
                    with conn.cursor() as cur:
                        try:
                            cur.execute("""
                                SELECT COLUMN_NAME FROM USER_TAB_COLUMNS 
                                WHERE TABLE_NAME = 'ONBOARDING_SESSION'
                                AND COLUMN_NAME IN ('HAS_PET', 'MAIN_SPACE', 'COOKING', 'LAUNDRY', 'MEDIA', 'PRIORITY_LIST')
                            """)
                            existing_cols = [row[0] for row in cur.fetchall()]
                            if existing_cols:
                                print(f"    이미 존재하는 칼럼: {', '.join(existing_cols)}")
                        except:
                            pass
        else:
            # DDL 스크립트 실행
            ddl_file = BASE_DIR / 'api' / 'db' / 'onboarding_tables_ddl.sql'
            if not ddl_file.exists():
                print(f"  ✗ DDL 파일을 찾을 수 없습니다: {ddl_file}")
                return
            
            print(f"\n[3] DDL 스크립트 실행 중... ({ddl_file})")
            execute_sql_file(conn, ddl_file)
            print("  ✓ DDL 실행 완료!")
        
        # 최종 확인
        print("\n[4] 테이블 생성 확인 중...")
        all_created = True
        for table in tables:
            if check_table_exists(conn, table):
                print(f"  ✓ {table} 테이블 생성됨")
            else:
                print(f"  ✗ {table} 테이블 생성 실패")
                all_created = False
        
        if all_created:
            print("\n" + "=" * 60)
            print("✅ 모든 테이블이 성공적으로 생성되었습니다!")
            print("=" * 60)
        else:
            print("\n" + "=" * 60)
            print("⚠ 일부 테이블 생성에 실패했습니다. 위의 오류 메시지를 확인하세요.")
            print("=" * 60)
        
        conn.close()
        
    except Exception as e:
        print(f"\n✗ 오류 발생: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()

