#!/usr/bin/env python
"""
온보딩 시스템 리팩토링 SQL 마이그레이션 실행 스크립트

사용법:
    python execute_migration.py

주의:
    - 실행 전 반드시 데이터베이스 백업을 수행하세요
    - Oracle DB 연결 정보가 .env 파일에 설정되어 있어야 합니다
"""

import os
import sys
import django

# Django 설정
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from api.db.oracle_client import get_connection
import re


def read_sql_file(file_path):
    """SQL 파일 읽기"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    return content


def split_sql_statements(sql_content):
    """SQL 문을 세미콜론과 슬래시로 분리 (PL/SQL 블록 처리)"""
    import re
    
    statements = []
    
    # 주석 제거 (-- 로 시작하는 라인, 단 문자열 내부는 보호)
    lines = sql_content.split('\n')
    cleaned_lines = []
    for line in lines:
        # -- 주석 제거 (문자열 내부는 간단히 처리)
        if '--' in line:
            # 따옴표가 없는 라인에서만 주석 제거
            if line.count("'") % 2 == 0:
                line = line[:line.index('--')]
        cleaned_lines.append(line.rstrip())
    
    cleaned_content = '\n'.join(cleaned_lines)
    
    # 빈 내용이면 반환
    if not cleaned_content.strip():
        return statements
    
    # '/' 구분자로 분리 (SQL*Plus 실행 구분자, oracledb에서는 무시)
    # 하지만 PL/SQL 블록을 올바르게 분리하기 위해 사용
    # '/' 앞의 내용만 처리 (뒤는 빈 줄이므로 무시)
    # 줄 단위로 '/'만 있는 경우를 찾아서 분리
    parts = []
    current_part = []
    for line in cleaned_content.split('\n'):
        stripped_line = line.strip()
        if stripped_line == '/':
            # 현재까지의 내용을 하나의 부분으로 저장
            if current_part:
                parts.append('\n'.join(current_part))
                current_part = []
        else:
            current_part.append(line)
    # 마지막 부분 추가
    if current_part:
        parts.append('\n'.join(current_part))
    
    # 각 부분을 처리
    for part in parts:
        part = part.strip()
        if not part:
            continue
        
        # CREATE OR REPLACE로 시작하는 DDL 문장은 전체를 하나로 처리
        # (이미 '/'로 분리되었으므로 완전한 단위임)
        if re.match(r'\bCREATE\s+(OR\s+REPLACE\s+)?(TRIGGER|PROCEDURE|FUNCTION|PACKAGE)', 
                   part, re.IGNORECASE):
            statements.append(part)
            continue
        
        # 이 부분에서 BEGIN/END 블록과 일반 SQL 문장 처리
        i = 0
        while i < len(part):
            # BEGIN 찾기
            begin_match = re.search(r'\bBEGIN\b', part[i:], re.IGNORECASE | re.MULTILINE)
            if not begin_match:
                # 남은 내용을 세미콜론으로 분리
                remaining = part[i:].strip()
                if remaining:
                    statements.extend(_split_by_semicolon_safe(remaining))
                break
            
            begin_pos = i + begin_match.start()
            
            # BEGIN 이전 내용 처리
            before_begin = part[i:begin_pos].strip()
            if before_begin:
                statements.extend(_split_by_semicolon_safe(before_begin))
            
            # END 찾기 (중첩된 BEGIN/END 고려)
            end_pos = begin_pos + len(begin_match.group())
            depth = 1
            in_string = False
            
            while end_pos < len(part) and depth > 0:
                char = part[end_pos]
                
                # 한 줄 주석 처리
                if not in_string and end_pos + 1 < len(part) and part[end_pos:end_pos+2] == '--':
                    while end_pos < len(part) and part[end_pos] != '\n':
                        end_pos += 1
                    continue
                
                # 문자열 내부 체크
                if char == "'":
                    if end_pos + 1 < len(part) and part[end_pos+1] == "'":
                        end_pos += 2
                        continue
                    in_string = not in_string
                
                if not in_string:
                    # BEGIN 찾기
                    if end_pos + 5 <= len(part):
                        lookahead = part[end_pos:end_pos+5]
                        if re.match(r'\bBEGIN\b', lookahead, re.IGNORECASE):
                            depth += 1
                            end_pos += 5
                            continue
                    
                    # END 찾기
                    if end_pos + 3 <= len(part):
                        lookahead = part[end_pos:end_pos+3]
                        if re.match(r'\bEND\b', lookahead, re.IGNORECASE):
                            next_char_pos = end_pos + 3
                            if (next_char_pos >= len(part) or 
                                part[next_char_pos] in ' \t\n;'):
                                depth -= 1
                                if depth == 0:
                                    end_pos = next_char_pos
                                    if end_pos < len(part) and part[end_pos] == ';':
                                        end_pos += 1
                                    break
                                else:
                                    end_pos = next_char_pos
                                    continue
                
                end_pos += 1
            
            if depth == 0:
                # 블록 추출
                block = part[begin_pos:end_pos].strip()
                if block:
                    statements.append(block)
                i = end_pos
            else:
                # END를 찾지 못함
                remaining = part[begin_pos:].strip()
                if remaining:
                    statements.append(remaining)
                break
    
    # 빈 statement 제거 및 정리
    final_statements = []
    for stmt in statements:
        stmt = stmt.strip()
        if not stmt or stmt.startswith('--') or len(stmt) < 3:
            continue
        final_statements.append(stmt)
    
    return final_statements


def _split_by_semicolon_safe(text):
    """문자열 내부의 세미콜론을 보호하면서 세미콜론으로 분리"""
    statements = []
    in_string = False
    string_char = None
    start = 0
    
    i = 0
    while i < len(text):
        char = text[i]
        
        # 문자열 내부 체크
        if char == "'" and (i == 0 or text[i-1] != '\\'):
            # 연속된 따옴표 체크
            if i + 1 < len(text) and text[i+1] == "'":
                i += 2
                continue
            if not in_string:
                in_string = True
                string_char = "'"
            elif char == string_char:
                in_string = False
                string_char = None
        elif char == '"' and (i == 0 or text[i-1] != '\\'):
            if not in_string:
                in_string = True
                string_char = '"'
            elif char == string_char:
                in_string = False
                string_char = None
        
        # 문자열 외부에서만 세미콜론으로 분리
        if not in_string and char == ';':
            part = text[start:i].strip()
            if part and not part.startswith('--') and not part.startswith('/') and len(part) > 5:
                statements.append(part)
            start = i + 1
        
        i += 1
    
    # 마지막 부분
    if start < len(text):
        part = text[start:].strip()
        if part and not part.startswith('--') and not part.startswith('/') and len(part) > 5:
            statements.append(part)
    
    return statements


def execute_migration():
    """마이그레이션 실행"""
    sql_file_path = 'api/db/migration_onboarding_refactor.sql'
    
    if not os.path.exists(sql_file_path):
        print(f"❌ SQL 파일을 찾을 수 없습니다: {sql_file_path}")
        return False
    
    print("=" * 60)
    print("온보딩 시스템 리팩토링 마이그레이션 실행")
    print("=" * 60)
    print(f"📄 SQL 파일: {sql_file_path}")
    print()
    
    # SQL 파일 읽기
    try:
        sql_content = read_sql_file(sql_file_path)
        statements = split_sql_statements(sql_content)
        print(f"✅ SQL 파일 읽기 완료 ({len(statements)}개 문장)")
    except Exception as e:
        print(f"❌ SQL 파일 읽기 실패: {e}")
        return False
    
    # 사용자 확인
    print()
    print("⚠️  경고: 이 작업은 데이터베이스 스키마를 변경합니다.")
    print("⚠️  실행 전 반드시 데이터베이스 백업을 수행했는지 확인하세요.")
    print()
    response = input("계속하시겠습니까? (yes/no): ")
    if response.lower() != 'yes':
        print("❌ 사용자가 취소했습니다.")
        return False
    
    # Oracle DB 연결 및 실행
    success_count = 0
    error_count = 0
    
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                print()
                print("=" * 60)
                print("마이그레이션 실행 시작")
                print("=" * 60)
                
                for i, statement in enumerate(statements, 1):
                    # 문장 요약 (처음 50자)
                    preview = statement[:50].replace('\n', ' ').strip()
                    if len(statement) > 50:
                        preview += "..."
                    
                    try:
                        cur.execute(statement)
                        conn.commit()
                        success_count += 1
                        print(f"✅ [{i}/{len(statements)}] 성공: {preview}")
                    except Exception as e:
                        error_count += 1
                        error_msg = str(e)
                        # 일부 오류는 무시 (이미 실행된 경우 등)
                        ignore_errors = [
                            'ORA-00942',  # table or view does not exist
                            'ORA-01430',  # column being added already exists
                            'ORA-00904',  # invalid identifier (컬럼이 이미 없음)
                            'ORA-00957',  # duplicate column name (이미 변경됨)
                            'ORA-00955',  # name is already used (이미 존재)
                            'ORA-01451',  # column to be modified to NULL cannot be modified to NULL (이미 NULL)
                        ]
                        
                        should_ignore = any(err in error_msg for err in ignore_errors)
                        
                        if should_ignore:
                            print(f"⚠️  [{i}/{len(statements)}] 경고 (무시): {preview}")
                            print(f"   메시지: {error_msg[:100]}")
                        else:
                            print(f"❌ [{i}/{len(statements)}] 실패: {preview}")
                            print(f"   오류: {error_msg}")
                            conn.rollback()
                            # 심각한 오류는 중단 여부 확인
                            if 'ORA-02291' in error_msg or 'ORA-02292' in error_msg:
                                response = input("   계속하시겠습니까? (yes/no): ")
                                if response.lower() != 'yes':
                                    break
                
                print()
                print("=" * 60)
                print("마이그레이션 실행 완료")
                print("=" * 60)
                print(f"✅ 성공: {success_count}개")
                print(f"❌ 실패: {error_count}개")
                print()
                
                # 검증 쿼리 실행
                print("검증 쿼리 실행 중...")
                try:
                    # 테이블 존재 확인
                    cur.execute("""
                        SELECT TABLE_NAME 
                        FROM USER_TABLES 
                        WHERE TABLE_NAME IN (
                            'ONBOARDING_SESSION',
                            'ONBOARD_SESS_MAIN_SPACES',
                            'ONBOARD_SESS_PRIORITIES',
                            'ONBOARD_SESS_CATEGORIES',
                            'ONBOARD_SESS_REC_PRODUCTS',
                            'STYLE_MESSAGE',
                            'SHARE_LINK',
                            'PORTFOLIO_VERSION'
                        )
                        ORDER BY TABLE_NAME
                    """)
                    tables = [row[0] for row in cur.fetchall()]
                    print(f"✅ 확인된 테이블: {', '.join(tables)}")
                    
                    # GUEST 회원 확인
                    cur.execute("SELECT * FROM MEMBER WHERE MEMBER_ID = 'GUEST'")
                    guest = cur.fetchone()
                    if guest:
                        print("✅ GUEST 회원 존재 확인")
                    else:
                        print("⚠️  GUEST 회원이 없습니다. 수동으로 생성해주세요.")
                    
                except Exception as e:
                    print(f"⚠️  검증 쿼리 실행 실패: {e}")
    
    except Exception as e:
        print(f"❌ 데이터베이스 연결 실패: {e}")
        return False
    
    print()
    print("=" * 60)
    if error_count == 0:
        print("✅ 마이그레이션이 성공적으로 완료되었습니다!")
    else:
        print("⚠️  일부 오류가 발생했습니다. 로그를 확인하세요.")
    print("=" * 60)
    
    return error_count == 0


if __name__ == '__main__':
    try:
        success = execute_migration()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n❌ 사용자가 중단했습니다.")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ 예상치 못한 오류: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

