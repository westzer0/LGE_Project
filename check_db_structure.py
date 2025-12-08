#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Oracle DB의 테이블 Comments를 조회하여 DB 구조를 확인하고
백엔드 로직과 비교하는 스크립트
"""

import sys
import json
from pathlib import Path

# Django 설정 로드
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

import django
django.setup()

from api.db.oracle_client import get_connection, fetch_all_dict

def get_all_tables():
    """모든 테이블 목록 조회"""
    sql = """
        SELECT TABLE_NAME
        FROM USER_TABLES
        ORDER BY TABLE_NAME
    """
    return fetch_all_dict(sql)

def get_table_comments():
    """모든 테이블의 Comments 조회"""
    sql = """
        SELECT TABLE_NAME, COMMENTS
        FROM USER_TAB_COMMENTS
        WHERE COMMENTS IS NOT NULL
        ORDER BY TABLE_NAME
    """
    return fetch_all_dict(sql)

def get_column_comments(table_name):
    """특정 테이블의 모든 컬럼 Comments 조회"""
    sql = """
        SELECT 
            COLUMN_NAME,
            DATA_TYPE,
            DATA_LENGTH,
            DATA_PRECISION,
            DATA_SCALE,
            NULLABLE,
            COMMENTS
        FROM USER_TAB_COLUMNS t
        LEFT JOIN USER_COL_COMMENTS c 
            ON t.TABLE_NAME = c.TABLE_NAME 
            AND t.COLUMN_NAME = c.COLUMN_NAME
        WHERE t.TABLE_NAME = :table_name
        ORDER BY t.COLUMN_ID
    """
    return fetch_all_dict(sql, {'table_name': table_name})

def get_table_structure():
    """모든 테이블의 구조와 Comments를 조회"""
    tables = get_all_tables()
    structure = {}
    
    for table in tables:
        table_name = table['TABLE_NAME']
        print(f"\n[테이블] {table_name}")
        
        # 테이블 Comment 조회
        table_comments = get_table_comments()
        table_comment = None
        for tc in table_comments:
            if tc['TABLE_NAME'] == table_name:
                table_comment = tc['COMMENTS']
                break
        
        # 컬럼 정보 조회
        columns = get_column_comments(table_name)
        
        structure[table_name] = {
            'table_comment': table_comment,
            'columns': columns
        }
        
        if table_comment:
            print(f"  [Comment] {table_comment}")
        
        print(f"  [컬럼 수] {len(columns)}")
        for col in columns[:5]:  # 처음 5개만 미리보기
            nullable = 'NULL' if col['NULLABLE'] == 'Y' else 'NOT NULL'
            dtype = col['DATA_TYPE']
            if col['DATA_PRECISION']:
                dtype += f"({col['DATA_PRECISION']}"
                if col['DATA_SCALE']:
                    dtype += f",{col['DATA_SCALE']}"
                dtype += ")"
            elif col['DATA_LENGTH']:
                dtype += f"({col['DATA_LENGTH']})"
            
            comment = col['COMMENTS'] or '(Comment 없음)'
            print(f"    - {col['COLUMN_NAME']}: {dtype} {nullable} | {comment}")
        
        if len(columns) > 5:
            print(f"    ... 외 {len(columns) - 5}개 컬럼")
    
    return structure

def save_structure_to_file(structure, filename='db_structure.json'):
    """구조를 JSON 파일로 저장"""
    # Oracle CLOB 타입을 문자열로 변환
    def convert_to_serializable(obj):
        if isinstance(obj, dict):
            return {k: convert_to_serializable(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [convert_to_serializable(item) for item in obj]
        elif hasattr(obj, '__str__'):
            return str(obj)
        else:
            return obj
    
    serializable_structure = convert_to_serializable(structure)
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(serializable_structure, f, ensure_ascii=False, indent=2)
    
    print(f"\n[저장 완료] {filename}")

def main():
    try:
        print("=" * 80)
        print("Oracle DB 구조 조회 시작")
        print("=" * 80)
        
        # DB 연결 테스트
        print("\n[1단계] DB 연결 테스트...")
        try:
            conn = get_connection()
            print("✓ DB 연결 성공")
            conn.close()
        except Exception as e:
            print(f"✗ DB 연결 실패: {e}")
            return None
        
        print("\n[2단계] 테이블 구조 조회...")
        structure = get_table_structure()
        
        print("\n" + "=" * 80)
        print(f"총 {len(structure)}개 테이블 조회 완료")
        print("=" * 80)
        
        # JSON 파일로 저장
        print("\n[3단계] 결과 저장...")
        save_structure_to_file(structure)
        
        # 요약 정보 출력
        print("\n[테이블 목록]")
        for table_name in sorted(structure.keys()):
            table_info = structure[table_name]
            col_count = len(table_info['columns'])
            comment = table_info['table_comment'] or '(Comment 없음)'
            print(f"  - {table_name}: {col_count}개 컬럼 | {comment}")
        
        return structure
        
    except Exception as e:
        print(f"\n[오류 발생] {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == '__main__':
    main()
