#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
실제 Oracle DB 구조 확인 스크립트
ONBOARDING_SESSION 테이블의 실제 구조를 확인하고 보고서 생성
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

def check_onboarding_session_structure():
    """ONBOARDING_SESSION 테이블 구조 확인"""
    print("=" * 80)
    print("ONBOARDING_SESSION 테이블 구조 확인")
    print("=" * 80)
    
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                # 1. 테이블 존재 여부 확인
                cur.execute("""
                    SELECT COUNT(*) 
                    FROM USER_TABLES 
                    WHERE TABLE_NAME = 'ONBOARDING_SESSION'
                """)
                table_exists = cur.fetchone()[0] > 0
                
                if not table_exists:
                    print("\n[오류] ONBOARDING_SESSION 테이블이 존재하지 않습니다.")
                    return False
                
                print("\n[확인] ONBOARDING_SESSION 테이블이 존재합니다.")
                
                # 2. 컬럼 구조 확인
                cur.execute("""
                    SELECT 
                        COLUMN_NAME,
                        DATA_TYPE,
                        DATA_LENGTH,
                        DATA_PRECISION,
                        DATA_SCALE,
                        NULLABLE,
                        DATA_DEFAULT
                    FROM USER_TAB_COLUMNS
                    WHERE TABLE_NAME = 'ONBOARDING_SESSION'
                    ORDER BY COLUMN_ID
                """)
                
                columns = cur.fetchall()
                print("\n[컬럼 구조]")
                print("-" * 80)
                print(f"{'컬럼명':<30} {'타입':<20} {'NULL':<10} {'기본값':<20}")
                print("-" * 80)
                
                session_id_type = None
                member_id_nullable = None
                clob_columns = []
                
                for col_name, data_type, data_length, data_precision, data_scale, nullable, data_default in columns:
                    # 타입 문자열 생성
                    if data_type == 'NUMBER':
                        if data_scale and data_scale > 0:
                            type_str = f"NUMBER({data_precision},{data_scale})"
                        elif data_precision:
                            type_str = f"NUMBER({data_precision})"
                        else:
                            type_str = "NUMBER"
                    elif data_type == 'VARCHAR2':
                        type_str = f"VARCHAR2({data_length})"
                    elif data_type == 'CLOB':
                        type_str = "CLOB"
                        clob_columns.append(col_name)
                    elif data_type == 'CHAR':
                        type_str = f"CHAR({data_length})"
                    elif data_type == 'DATE':
                        type_str = "DATE"
                    else:
                        type_str = f"{data_type}({data_length})"
                    
                    nullable_str = "NULL" if nullable == 'Y' else "NOT NULL"
                    default_str = str(data_default) if data_default else ""
                    
                    print(f"{col_name:<30} {type_str:<20} {nullable_str:<10} {default_str:<20}")
                    
                    # 특정 컬럼 정보 저장
                    if col_name == 'SESSION_ID':
                        session_id_type = type_str
                    if col_name == 'MEMBER_ID':
                        member_id_nullable = nullable == 'Y'
                
                # 3. 외래키 제약조건 확인
                print("\n[외래키 제약조건]")
                print("-" * 80)
                cur.execute("""
                    SELECT 
                        CONSTRAINT_NAME,
                        R_CONSTRAINT_NAME,
                        DELETE_RULE
                    FROM USER_CONSTRAINTS
                    WHERE TABLE_NAME = 'ONBOARDING_SESSION'
                    AND CONSTRAINT_TYPE = 'R'
                """)
                
                fk_constraints = cur.fetchall()
                if fk_constraints:
                    for constraint_name, r_constraint_name, delete_rule in fk_constraints:
                        print(f"제약조건명: {constraint_name}")
                        print(f"  참조 테이블: {r_constraint_name}")
                        print(f"  삭제 규칙: {delete_rule}")
                else:
                    print("외래키 제약조건이 없습니다.")
                
                # 4. 정규화 테이블 존재 여부 확인
                print("\n[정규화 테이블 존재 여부]")
                print("-" * 80)
                normalized_tables = [
                    'ONBOARD_SESS_MAIN_SPACES',
                    'ONBOARD_SESS_PRIORITIES',
                    'ONBOARD_SESS_CATEGORIES',
                    'ONBOARD_SESS_REC_PRODUCTS'
                ]
                
                for table_name in normalized_tables:
                    cur.execute("""
                        SELECT COUNT(*) 
                        FROM USER_TABLES 
                        WHERE TABLE_NAME = :table_name
                    """, {'table_name': table_name})
                    exists = cur.fetchone()[0] > 0
                    status = "✓ 존재" if exists else "✗ 없음"
                    print(f"{table_name:<35} {status}")
                
                # 5. 요약 보고서
                print("\n" + "=" * 80)
                print("[요약]")
                print("=" * 80)
                
                print(f"\n1. SESSION_ID 타입: {session_id_type}")
                if 'VARCHAR2' in session_id_type:
                    print("   ✓ VARCHAR2 타입으로 올바르게 설정됨")
                else:
                    print("   ✗ VARCHAR2 타입이 아님 - 수정 필요")
                
                print(f"\n2. MEMBER_ID NULL 허용: {member_id_nullable}")
                if member_id_nullable:
                    print("   ✓ NULL 허용으로 설정됨")
                else:
                    print("   ✗ NULL 허용이 아님 - 수정 필요")
                
                print(f"\n3. CLOB 컬럼 개수: {len(clob_columns)}")
                if clob_columns:
                    print(f"   ✗ 다음 CLOB 컬럼들이 존재함: {', '.join(clob_columns)}")
                    print("   → 제거 또는 사용 중단 필요")
                else:
                    print("   ✓ CLOB 컬럼이 없음")
                
                print(f"\n4. 외래키 제약조건: {len(fk_constraints)}개")
                if len(fk_constraints) == 0:
                    print("   ⚠ MEMBER_ID 외래키 제약조건이 없음 - 추가 고려 필요")
                
                print(f"\n5. 정규화 테이블: {sum(1 for t in normalized_tables if cur.execute('SELECT COUNT(*) FROM USER_TABLES WHERE TABLE_NAME = :t', {'t': t}) or cur.fetchone()[0] > 0)}/{len(normalized_tables)}개 존재")
                
                # 6. 권장 사항
                print("\n" + "=" * 80)
                print("[권장 사항]")
                print("=" * 80)
                
                recommendations = []
                
                if 'VARCHAR2' not in session_id_type:
                    recommendations.append("SESSION_ID를 VARCHAR2(100)로 변경")
                
                if not member_id_nullable:
                    recommendations.append("MEMBER_ID를 NULL 허용으로 변경")
                
                if clob_columns:
                    recommendations.append(f"CLOB 컬럼 제거: {', '.join(clob_columns)}")
                
                if len(fk_constraints) == 0:
                    recommendations.append("MEMBER_ID 외래키 제약조건 추가 고려")
                
                if recommendations:
                    for i, rec in enumerate(recommendations, 1):
                        print(f"{i}. {rec}")
                else:
                    print("모든 항목이 올바르게 설정되어 있습니다.")
                
                return True
                
    except Exception as e:
        print(f"\n[오류] 데이터베이스 연결 또는 쿼리 실행 실패: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = check_onboarding_session_structure()
    if success:
        print("\n" + "=" * 80)
        print("완료")
        print("=" * 80)
    else:
        print("\n" + "=" * 80)
        print("실패 - 수동으로 확인이 필요합니다")
        print("=" * 80)
        sys.exit(1)

