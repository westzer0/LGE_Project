#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Oracle DB의 테이블 Comments와 제약조건을 기반으로 Mermaid ERD 생성 (간단 버전)
"""
import sys
import os
from pathlib import Path

# 출력 파일 설정
output_file = Path(__file__).parent / "ERD.mmd"
log_file = Path(__file__).parent / "erd_generation.log"

def log(message):
    """로그 출력"""
    print(message, flush=True)
    with open(log_file, 'a', encoding='utf-8') as f:
        f.write(message + '\n')

try:
    BASE_DIR = Path(__file__).resolve().parent
    sys.path.insert(0, str(BASE_DIR))
    
    log("=" * 70)
    log("Oracle DB ERD 생성 시작")
    log("=" * 70)
    
    # Django 설정 로드
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
    
    import django
    django.setup()
    
    from api.db.oracle_client import get_connection, fetch_all_dict, DatabaseDisabledError
    
    # DB 연결 테스트
    log("\n[1] DB 연결 테스트...")
    try:
        conn = get_connection()
        log("   ✅ DB 연결 성공")
        conn.close()
    except DatabaseDisabledError:
        log("   ⚠️ DB가 비활성화되어 있습니다 (DISABLE_DB=true)")
        log("   ERD 생성을 위해 USE_ORACLE=true로 설정하세요.")
        sys.exit(1)
    except Exception as e:
        log(f"   ❌ DB 연결 실패: {e}")
        sys.exit(1)
    
    # 테이블 목록 조회
    log("\n[2] 테이블 목록 조회...")
    tables = fetch_all_dict("SELECT TABLE_NAME FROM USER_TABLES ORDER BY TABLE_NAME")
    log(f"   총 {len(tables)}개 테이블 발견")
    
    # Primary Key 조회
    log("\n[3] Primary Key 조회...")
    pks = fetch_all_dict("""
        SELECT c.TABLE_NAME, c.COLUMN_NAME
        FROM USER_CONS_COLUMNS c
        JOIN USER_CONSTRAINTS k ON c.CONSTRAINT_NAME = k.CONSTRAINT_NAME
        WHERE k.CONSTRAINT_TYPE = 'P'
        ORDER BY c.TABLE_NAME, c.POSITION
    """)
    pk_dict = {}
    for pk in pks:
        if pk['TABLE_NAME'] not in pk_dict:
            pk_dict[pk['TABLE_NAME']] = []
        pk_dict[pk['TABLE_NAME']].append(pk['COLUMN_NAME'])
    log(f"   {len(pk_dict)}개 테이블에 Primary Key 존재")
    
    # Foreign Key 조회
    log("\n[4] Foreign Key 관계 조회...")
    fks = fetch_all_dict("""
        SELECT 
            a.TABLE_NAME AS CHILD_TABLE,
            a.COLUMN_NAME AS CHILD_COLUMN,
            c_pk.TABLE_NAME AS PARENT_TABLE,
            b.COLUMN_NAME AS PARENT_COLUMN
        FROM USER_CONS_COLUMNS a
        JOIN USER_CONSTRAINTS c ON a.CONSTRAINT_NAME = c.CONSTRAINT_NAME
        JOIN USER_CONSTRAINTS c_pk ON c.R_OWNER = c_pk.OWNER AND c.R_CONSTRAINT_NAME = c_pk.CONSTRAINT_NAME
        JOIN USER_CONS_COLUMNS b ON c_pk.CONSTRAINT_NAME = b.CONSTRAINT_NAME AND b.POSITION = a.POSITION
        WHERE c.CONSTRAINT_TYPE = 'R'
        ORDER BY a.TABLE_NAME, a.POSITION
    """)
    fk_relations = {}
    for fk in fks:
        key = (fk['CHILD_TABLE'], fk['PARENT_TABLE'])
        if key not in fk_relations:
            fk_relations[key] = []
        fk_relations[key].append({
            'child_col': fk['CHILD_COLUMN'],
            'parent_col': fk['PARENT_COLUMN']
        })
    log(f"   {len(fk_relations)}개 Foreign Key 관계 발견")
    
    # ERD 생성
    log("\n[5] Mermaid ERD 생성 중...")
    erd_lines = []
    erd_lines.append("```mermaid")
    erd_lines.append("erDiagram")
    erd_lines.append("")
    
    for table in tables:
        table_name = table['TABLE_NAME']
        
        # 테이블 Comment
        table_comments = fetch_all_dict(
            "SELECT COMMENTS FROM USER_TAB_COMMENTS WHERE TABLE_NAME = :name",
            {'name': table_name}
        )
        table_comment = table_comments[0]['COMMENTS'] if table_comments and table_comments[0]['COMMENTS'] else None
        
        # 컬럼 정보
        columns = fetch_all_dict("""
            SELECT 
                t.COLUMN_NAME, t.DATA_TYPE, t.DATA_LENGTH, t.DATA_PRECISION, t.DATA_SCALE, t.NULLABLE,
                c.COMMENTS
            FROM USER_TAB_COLUMNS t
            LEFT JOIN USER_COL_COMMENTS c ON t.TABLE_NAME = c.TABLE_NAME AND t.COLUMN_NAME = c.COLUMN_NAME
            WHERE t.TABLE_NAME = :name
            ORDER BY t.COLUMN_ID
        """, {'name': table_name})
        
        erd_lines.append(f"    {table_name} {{")
        if table_comment:
            erd_lines.append(f"        \"{table_comment}\"")
        
        for col in columns:
            dtype = col['DATA_TYPE']
            if col['DATA_PRECISION']:
                dtype += f"({col['DATA_PRECISION']}"
                if col['DATA_SCALE']:
                    dtype += f",{col['DATA_SCALE']}"
                dtype += ")"
            elif col['DATA_LENGTH'] and col['DATA_TYPE'] in ('VARCHAR2', 'CHAR', 'NVARCHAR2', 'NCHAR'):
                dtype += f"({col['DATA_LENGTH']})"
            
            is_pk = table_name in pk_dict and col['COLUMN_NAME'] in pk_dict[table_name]
            is_fk = any(fk['CHILD_TABLE'] == table_name and fk['CHILD_COLUMN'] == col['COLUMN_NAME'] for fk in fks)
            
            pk_marker = " PK" if is_pk else ""
            fk_marker = " FK" if is_fk else ""
            nullable = "" if col['NULLABLE'] == 'N' else " nullable"
            
            comment = col['COMMENTS']
            if comment:
                if len(comment) > 50:
                    comment = comment[:47] + "..."
                erd_lines.append(f"        {dtype} {col['COLUMN_NAME']}{pk_marker}{fk_marker} \"{comment}\"{nullable}")
            else:
                erd_lines.append(f"        {dtype} {col['COLUMN_NAME']}{pk_marker}{fk_marker}{nullable}")
        
        erd_lines.append("    }")
        erd_lines.append("")
    
    # Foreign Key 관계
    if fk_relations:
        erd_lines.append("    %% Foreign Key Relationships")
        for (child, parent), relations in sorted(fk_relations.items()):
            rel_desc = f"{relations[0]['child_col']} -> {relations[0]['parent_col']}"
            if len(relations) > 1:
                rel_desc = f"{len(relations)} columns"
            erd_lines.append(f"    {child} ||--o{{ {parent} : \"{rel_desc}\"")
    
    erd_lines.append("```")
    
    # 파일 저장
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(erd_lines))
    
    log(f"\n✅ ERD 생성 완료: {output_file}")
    log(f"   - 테이블 수: {len(tables)}")
    log(f"   - Foreign Key 관계: {len(fk_relations)}")
    log("\n📝 GitHub에 업로드하는 방법:")
    log("   git add ERD.mmd")
    log("   git commit -m 'Add ERD diagram'")
    log("   git push")
    
except Exception as e:
    log(f"\n❌ 오류 발생: {e}")
    import traceback
    traceback.print_exc()
    with open(log_file, 'a', encoding='utf-8') as f:
        traceback.print_exc(file=f)
    sys.exit(1)
