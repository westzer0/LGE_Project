#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Oracle DB에서 직접 테이블 정보를 읽어서 Django 모델 생성
Django의 inspectdb 대신 직접 oracledb를 사용
"""

import os
import sys
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

# 환경 변수 설정
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

# .env 파일 로드
try:
    from dotenv import dotenv_values
    env_path = BASE_DIR / '.env'
    if env_path.exists():
        env_vars = dotenv_values(env_path)
        for key, value in env_vars.items():
            if value is not None:
                os.environ.setdefault(key, value)
except:
    pass

# Oracle 클라이언트 사용
from api.db.oracle_client import get_connection, fetch_all_dict, DatabaseDisabledError

def get_table_columns(table_name):
    """테이블의 컬럼 정보 조회"""
    sql = """
    SELECT 
        column_name,
        data_type,
        data_length,
        data_precision,
        data_scale,
        nullable,
        data_default
    FROM user_tab_columns
    WHERE table_name = :table_name
    ORDER BY column_id
    """
    try:
        return fetch_all_dict(sql, {'table_name': table_name.upper()})
    except Exception as e:
        print(f"테이블 {table_name} 컬럼 조회 실패: {e}")
        return []

def get_primary_keys(table_name):
    """테이블의 Primary Key 조회"""
    sql = """
    SELECT column_name
    FROM user_cons_columns
    WHERE constraint_name = (
        SELECT constraint_name
        FROM user_constraints
        WHERE table_name = :table_name
        AND constraint_type = 'P'
    )
    """
    try:
        result = fetch_all_dict(sql, {'table_name': table_name.upper()})
        return [r['COLUMN_NAME'] for r in result]
    except:
        return []

def get_foreign_keys(table_name):
    """테이블의 Foreign Key 조회"""
    sql = """
    SELECT 
        acc.column_name,
        acc.constraint_name,
        ccu.table_name AS foreign_table_name,
        ccu.column_name AS foreign_column_name
    FROM user_cons_columns acc
    JOIN user_constraints ac ON acc.constraint_name = ac.constraint_name
    JOIN user_cons_columns ccu ON ac.r_constraint_name = ccu.constraint_name
    WHERE ac.table_name = :table_name
    AND ac.constraint_type = 'R'
    """
    try:
        return fetch_all_dict(sql, {'table_name': table_name.upper()})
    except:
        return []

def python_type_from_oracle(data_type, data_length=None, data_precision=None, data_scale=None):
    """Oracle 데이터 타입을 Python/Django 타입으로 변환"""
    data_type = data_type.upper()
    
    if 'VARCHAR' in data_type or 'CHAR' in data_type:
        max_length = data_length or 255
        return f"models.CharField(max_length={max_length}, blank=True, null=True)"
    elif 'NUMBER' in data_type:
        if data_scale and data_scale > 0:
            return "models.DecimalField(max_digits=19, decimal_places=2, blank=True, null=True)"
        elif data_precision:
            if data_precision <= 9:
                return "models.IntegerField(blank=True, null=True)"
            else:
                return "models.BigIntegerField(blank=True, null=True)"
        else:
            return "models.IntegerField(blank=True, null=True)"
    elif 'DATE' in data_type or 'TIMESTAMP' in data_type:
        return "models.DateTimeField(blank=True, null=True)"
    elif 'CLOB' in data_type or 'BLOB' in data_type:
        return "models.TextField(blank=True, null=True)"
    else:
        return "models.CharField(max_length=255, blank=True, null=True)"

def generate_model(table_name, columns, primary_keys, foreign_keys):
    """Django 모델 코드 생성"""
    model_code = []
    model_code.append(f"class {table_name.capitalize()}(models.Model):")
    model_code.append(f'    """')
    model_code.append(f'    {table_name} 테이블')
    model_code.append(f'    """')
    model_code.append("")
    
    # 컬럼 정의
    for col in columns:
        col_name = col['COLUMN_NAME'].lower()
        field_type = python_type_from_oracle(
            col['DATA_TYPE'],
            col.get('DATA_LENGTH'),
            col.get('DATA_PRECISION'),
            col.get('DATA_SCALE')
        )
        
        # Primary Key 처리
        if col_name.upper() in [pk.upper() for pk in primary_keys]:
            if 'IntegerField' in field_type:
                field_type = field_type.replace('IntegerField', 'AutoField')
            field_type = field_type.replace(', blank=True, null=True', '')
        
        # Nullable 처리
        if col['NULLABLE'] == 'N' and col_name.upper() not in [pk.upper() for pk in primary_keys]:
            field_type = field_type.replace(', blank=True, null=True', '')
        
        model_code.append(f"    {col_name} = {field_type}")
    
    # Meta 클래스
    model_code.append("")
    model_code.append("    class Meta:")
    model_code.append(f"        db_table = '{table_name.upper()}'")
    if primary_keys:
        model_code.append(f"        # primary_key = {primary_keys}")
    model_code.append("")
    model_code.append(f"    def __str__(self):")
    if primary_keys:
        pk_col = primary_keys[0].lower()
        model_code.append(f"        return f\"{table_name}({{self.{pk_col}}})\"")
    else:
        model_code.append(f"        return f\"{table_name}({{self.pk}})\"")
    model_code.append("")
    model_code.append("")
    
    return "\n".join(model_code)

def main():
    print("=" * 60)
    print("Oracle DB 테이블 정보를 Django 모델로 변환")
    print("=" * 60)
    
    try:
        # 연결 테스트
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT SYSDATE FROM DUAL")
                print("✅ Oracle DB 연결 성공!")
    except DatabaseDisabledError:
        print("❌ DB가 비활성화되어 있습니다.")
        return
    except Exception as e:
        print(f"❌ 연결 실패: {e}")
        return
    
    # 테이블 목록 조회
    try:
        sql = "SELECT table_name FROM user_tables ORDER BY table_name"
        tables = fetch_all_dict(sql)
        print(f"\n✅ 총 {len(tables)}개의 테이블 발견")
    except Exception as e:
        print(f"❌ 테이블 목록 조회 실패: {e}")
        return
    
    # 모델 코드 생성
    models_code = []
    models_code.append("# This is an auto-generated Django model module.")
    models_code.append("# You'll have to do the following manually to clean this up:")
    models_code.append("#   * Rearrange models' order")
    models_code.append("#   * Make sure each model has one field with primary_key=True")
    models_code.append("#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table")
    models_code.append("# Feel free to rename the models, but don't rename db_table values or field names.")
    models_code.append("from django.db import models")
    models_code.append("")
    models_code.append("")
    
    # 각 테이블에 대해 모델 생성
    for table_info in tables:
        table_name = table_info['TABLE_NAME']
        print(f"\n처리 중: {table_name}...")
        
        columns = get_table_columns(table_name)
        if not columns:
            print(f"  ⚠️ 컬럼 정보 없음, 건너뜀")
            continue
        
        primary_keys = get_primary_keys(table_name)
        foreign_keys = get_foreign_keys(table_name)
        
        model_code = generate_model(table_name, columns, primary_keys, foreign_keys)
        models_code.append(model_code)
        print(f"  ✅ 모델 생성 완료 ({len(columns)}개 컬럼)")
    
    # 파일 저장
    output_file = BASE_DIR / 'api' / 'models_inspected.py'
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(models_code))
    
    print(f"\n✅ 모델 파일 생성 완료: {output_file}")
    print(f"   총 {len(tables)}개 테이블 처리됨")

if __name__ == '__main__':
    main()


