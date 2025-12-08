#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Oracle DB의 테이블 Comments와 제약조건을 기반으로 Mermaid ERD 생성
"""
import sys
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

# Django 설정 로드
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

def get_table_comment(table_name):
    """테이블 Comment 조회"""
    sql = """
        SELECT COMMENTS
        FROM USER_TAB_COMMENTS
        WHERE TABLE_NAME = :table_name
    """
    result = fetch_all_dict(sql, {'table_name': table_name})
    return result[0]['COMMENTS'] if result and result[0]['COMMENTS'] else None

def get_columns_with_comments(table_name):
    """테이블의 모든 컬럼 정보와 Comments 조회"""
    sql = """
        SELECT 
            t.COLUMN_NAME,
            t.DATA_TYPE,
            t.DATA_LENGTH,
            t.DATA_PRECISION,
            t.DATA_SCALE,
            t.NULLABLE,
            t.COLUMN_ID,
            c.COMMENTS
        FROM USER_TAB_COLUMNS t
        LEFT JOIN USER_COL_COMMENTS c 
            ON t.TABLE_NAME = c.TABLE_NAME 
            AND t.COLUMN_NAME = c.COLUMN_NAME
        WHERE t.TABLE_NAME = :table_name
        ORDER BY t.COLUMN_ID
    """
    return fetch_all_dict(sql, {'table_name': table_name})

def get_primary_keys():
    """모든 테이블의 Primary Key 조회"""
    sql = """
        SELECT 
            c.TABLE_NAME,
            c.COLUMN_NAME,
            c.POSITION
        FROM USER_CONS_COLUMNS c
        JOIN USER_CONSTRAINTS k 
            ON c.CONSTRAINT_NAME = k.CONSTRAINT_NAME
            AND c.TABLE_NAME = k.TABLE_NAME
        WHERE k.CONSTRAINT_TYPE = 'P'
        ORDER BY c.TABLE_NAME, c.POSITION
    """
    return fetch_all_dict(sql)

def get_foreign_keys():
    """모든 Foreign Key 관계 조회"""
    sql = """
        SELECT 
            a.TABLE_NAME AS CHILD_TABLE,
            a.COLUMN_NAME AS CHILD_COLUMN,
            c_pk.TABLE_NAME AS PARENT_TABLE,
            b.COLUMN_NAME AS PARENT_COLUMN,
            a.CONSTRAINT_NAME
        FROM USER_CONS_COLUMNS a
        JOIN USER_CONSTRAINTS c 
            ON a.CONSTRAINT_NAME = c.CONSTRAINT_NAME
            AND a.TABLE_NAME = c.TABLE_NAME
        JOIN USER_CONSTRAINTS c_pk 
            ON c.R_OWNER = c_pk.OWNER
            AND c.R_CONSTRAINT_NAME = c_pk.CONSTRAINT_NAME
        JOIN USER_CONS_COLUMNS b 
            ON c_pk.CONSTRAINT_NAME = b.CONSTRAINT_NAME
            AND c_pk.TABLE_NAME = b.TABLE_NAME
            AND b.POSITION = a.POSITION
        WHERE c.CONSTRAINT_TYPE = 'R'
        ORDER BY a.TABLE_NAME, a.POSITION
    """
    return fetch_all_dict(sql)

def format_data_type(col):
    """데이터 타입 포맷팅"""
    dtype = col['DATA_TYPE']
    
    if col['DATA_PRECISION']:
        dtype += f"({col['DATA_PRECISION']}"
        if col['DATA_SCALE']:
            dtype += f",{col['DATA_SCALE']}"
        dtype += ")"
    elif col['DATA_LENGTH'] and col['DATA_TYPE'] in ('VARCHAR2', 'CHAR', 'NVARCHAR2', 'NCHAR'):
        dtype += f"({col['DATA_LENGTH']})"
    
    return dtype

def generate_mermaid_erd():
    """Mermaid ERD 생성"""
    import sys
    sys.stdout.reconfigure(encoding='utf-8')
    
    print("=" * 70, flush=True)
    print("Oracle DB ERD 생성 시작", flush=True)
    print("=" * 70, flush=True)
    
    # 1. 테이블 목록 조회
    print("\n[1] 테이블 목록 조회 중...")
    tables = get_all_tables()
    print(f"   총 {len(tables)}개 테이블 발견")
    
    # 2. Primary Key 조회
    print("\n[2] Primary Key 조회 중...")
    pk_dict = {}
    pks = get_primary_keys()
    for pk in pks:
        table = pk['TABLE_NAME']
        if table not in pk_dict:
            pk_dict[table] = []
        pk_dict[table].append(pk['COLUMN_NAME'])
    print(f"   {len(pk_dict)}개 테이블에 Primary Key 존재")
    
    # 3. Foreign Key 조회
    print("\n[3] Foreign Key 관계 조회 중...")
    fks = get_foreign_keys()
    fk_relations = {}
    for fk in fks:
        child = fk['CHILD_TABLE']
        parent = fk['PARENT_TABLE']
        key = (child, parent)
        if key not in fk_relations:
            fk_relations[key] = []
        fk_relations[key].append({
            'child_col': fk['CHILD_COLUMN'],
            'parent_col': fk['PARENT_COLUMN']
        })
    print(f"   {len(fk_relations)}개 Foreign Key 관계 발견")
    
    # 4. Mermaid ERD 생성
    print("\n[4] Mermaid ERD 생성 중...")
    erd_lines = []
    erd_lines.append("```mermaid")
    erd_lines.append("erDiagram")
    erd_lines.append("")
    
    # 각 테이블에 대해 ERD 엔티티 생성
    for table in tables:
        table_name = table['TABLE_NAME']
        
        # 테이블 Comment 조회
        table_comment = get_table_comment(table_name)
        
        # 컬럼 정보 조회
        columns = get_columns_with_comments(table_name)
        
        # 테이블 정의 시작
        erd_lines.append(f"    {table_name} {{")
        
        # 테이블 Comment가 있으면 주석으로 추가
        if table_comment:
            erd_lines.append(f"        \"{table_comment}\"")
        
        # 각 컬럼 추가
        for col in columns:
            col_name = col['COLUMN_NAME']
            dtype = format_data_type(col)
            nullable = "" if col['NULLABLE'] == 'N' else " nullable"
            
            # PK 표시
            is_pk = table_name in pk_dict and col_name in pk_dict[table_name]
            pk_marker = " PK" if is_pk else ""
            
            # FK 표시 (간단히만 표시)
            is_fk = any(
                fk['CHILD_TABLE'] == table_name and fk['CHILD_COLUMN'] == col_name
                for fk in fks
            )
            fk_marker = " FK" if is_fk else ""
            
            # Comment가 있으면 추가
            comment = col['COMMENTS']
            if comment:
                # Comment가 너무 길면 자르기
                if len(comment) > 50:
                    comment = comment[:47] + "..."
                erd_lines.append(f"        {dtype} {col_name}{pk_marker}{fk_marker} \"{comment}\"{nullable}")
            else:
                erd_lines.append(f"        {dtype} {col_name}{pk_marker}{fk_marker}{nullable}")
        
        erd_lines.append("    }")
        erd_lines.append("")
    
    # Foreign Key 관계 추가
    if fk_relations:
        erd_lines.append("    %% Foreign Key Relationships")
        for (child_table, parent_table), relations in sorted(fk_relations.items()):
            # 관계 설명 생성
            rel_desc = f"{relations[0]['child_col']} -> {relations[0]['parent_col']}"
            if len(relations) > 1:
                rel_desc = f"{len(relations)} columns"
            erd_lines.append(f"    {child_table} ||--o{{ {parent_table} : \"{rel_desc}\"")
    
    erd_lines.append("```")
    
    erd_content = "\n".join(erd_lines)
    
    # 파일로 저장
    output_file = "ERD.mmd"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(erd_content)
    
    print(f"\n✅ ERD 생성 완료: {output_file}")
    print(f"   - 테이블 수: {len(tables)}")
    print(f"   - Foreign Key 관계: {len(fk_relations)}")
    print("\n📝 GitHub에 업로드하면 자동으로 렌더링됩니다!")
    print(f"   git add {output_file}")
    print(f"   git commit -m 'Add ERD diagram'")
    print(f"   git push")
    
    return erd_content

if __name__ == '__main__':
    import sys
    import traceback
    
    # 출력을 파일로도 저장
    log_file = open('generate_erd.log', 'w', encoding='utf-8')
    
    def log_print(*args, **kwargs):
        print(*args, **kwargs, flush=True)
        print(*args, **kwargs, file=log_file, flush=True)
    
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        
        # DB 연결 테스트
        log_print("\n[0] DB 연결 테스트...")
        try:
            conn = get_connection()
            log_print("   ✅ DB 연결 성공")
            conn.close()
        except Exception as db_err:
            log_print(f"   ❌ DB 연결 실패: {db_err}")
            log_print("\n   가능한 원인:")
            log_print("   1. DISABLE_DB=true로 설정되어 있을 수 있습니다")
            log_print("   2. Oracle DB 서버에 연결할 수 없습니다")
            log_print("   3. 환경 변수가 설정되지 않았습니다")
            raise
        
        # ERD 생성
        log_print("\n[1] ERD 생성 시작...")
        erd_content = generate_erd()
        
        log_print("\n" + "=" * 70)
        log_print("✅ 완료!")
        log_print("=" * 70)
        log_print(f"\nERD.mmd 파일이 생성되었습니다!")
        
    except Exception as e:
        log_print(f"\n❌ 오류 발생: {e}")
        traceback.print_exc(file=log_file)
        traceback.print_exc()
        sys.exit(1)
    finally:
        log_file.close()
