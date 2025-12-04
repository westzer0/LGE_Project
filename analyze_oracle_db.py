#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Oracle DB 테이블 구조 및 데이터 분석 스크립트
"""

import sys
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

from api.db.oracle_client import get_connection, fetch_all_dict, fetch_all
import json
from collections import Counter
from datetime import datetime

def get_all_tables():
    """모든 테이블 목록 조회"""
    sql = """
    SELECT table_name 
    FROM user_tables 
    ORDER BY table_name
    """
    return fetch_all_dict(sql)

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
    return fetch_all_dict(sql, {'table_name': table_name.upper()})

def get_table_row_count(table_name):
    """테이블의 행 개수 조회"""
    sql = f"SELECT COUNT(*) as cnt FROM {table_name}"
    result = fetch_one(sql)
    return result[0] if result else 0

def get_table_sample_data(table_name, limit=5):
    """테이블 샘플 데이터 조회"""
    sql = f"SELECT * FROM {table_name} WHERE ROWNUM <= {limit}"
    try:
        return fetch_all_dict(sql)
    except Exception as e:
        return f"Error: {str(e)}"

def analyze_table_data(table_name):
    """테이블 데이터 상세 분석"""
    # 전역 출력 리스트에 추가하기 위해 함수 수정 필요
    # 일단 print로 유지하고 나중에 파일로 리다이렉트
    print(f"\n{'='*80}")
    print(f"테이블: {table_name}")
    print(f"{'='*80}")
    
    # 컬럼 정보
    columns = get_table_columns(table_name)
    print(f"\n[컬럼 정보] ({len(columns)}개 컬럼)")
    print("-" * 80)
    for col in columns:
        nullable = "NULL" if col['NULLABLE'] == 'Y' else "NOT NULL"
        default = f" DEFAULT {col['DATA_DEFAULT']}" if col['DATA_DEFAULT'] else ""
        print(f"  {col['COLUMN_NAME']:<30} {col['DATA_TYPE']:<20} {nullable}{default}")
    
    # 행 개수
    row_count = get_table_row_count(table_name)
    print(f"\n[데이터 개수] {row_count:,}개")
    
    # 샘플 데이터
    if row_count > 0:
        print(f"\n[샘플 데이터] (최대 5개)")
        print("-" * 80)
        samples = get_table_sample_data(table_name, 5)
        if isinstance(samples, list) and len(samples) > 0:
            for i, row in enumerate(samples, 1):
                print(f"\n  [샘플 {i}]")
                for key, value in row.items():
                    # 긴 텍스트는 잘라서 표시
                    if isinstance(value, str) and len(value) > 100:
                        value = value[:100] + "..."
                    print(f"    {key}: {value}")
        else:
            print(f"  {samples}")
    
    # 통계 정보 (숫자형 컬럼)
    numeric_columns = [col['COLUMN_NAME'] for col in columns 
                      if col['DATA_TYPE'] in ('NUMBER', 'FLOAT', 'BINARY_DOUBLE', 'BINARY_FLOAT')]
    
    if numeric_columns and row_count > 0:
        print(f"\n[숫자형 컬럼 통계]")
        print("-" * 80)
        for col_name in numeric_columns[:5]:  # 최대 5개만
            try:
                stats_sql = f"""
                SELECT 
                    MIN({col_name}) as min_val,
                    MAX({col_name}) as max_val,
                    AVG({col_name}) as avg_val,
                    COUNT(DISTINCT {col_name}) as distinct_count
                FROM {table_name}
                WHERE {col_name} IS NOT NULL
                """
                stats = fetch_one(stats_sql)
                if stats and stats[0] is not None:
                    print(f"  {col_name}:")
                    print(f"    최소값: {stats[0]}, 최대값: {stats[1]}, 평균: {stats[2]:.2f}, 고유값: {stats[3]}")
            except Exception as e:
                pass
    
    # 문자열 컬럼 분포 (최대 3개)
    varchar_columns = [col['COLUMN_NAME'] for col in columns 
                      if col['DATA_TYPE'] in ('VARCHAR2', 'CHAR', 'NVARCHAR2', 'NCHAR')]
    
    if varchar_columns and row_count > 0:
        print(f"\n[문자열 컬럼 분포] (상위 5개 값)")
        print("-" * 80)
        for col_name in varchar_columns[:3]:  # 최대 3개만
            try:
                dist_sql = f"""
                SELECT {col_name}, COUNT(*) as cnt
                FROM {table_name}
                WHERE {col_name} IS NOT NULL
                GROUP BY {col_name}
                ORDER BY cnt DESC
                FETCH FIRST 5 ROWS ONLY
                """
                dists = fetch_all_dict(dist_sql)
                if dists:
                    print(f"  {col_name}:")
                    for dist in dists:
                        value = str(dist[col_name])[:50]  # 최대 50자
                        print(f"    '{value}': {dist['CNT']}개")
            except Exception as e:
                pass

def main():
    output_file = "oracle_db_analysis_result.txt"
    output_lines = []
    
    def log(msg):
        """콘솔 출력과 파일 저장 동시에"""
        print(msg)
        output_lines.append(msg)
    
    log("="*80)
    log("Oracle DB 테이블 분석 시작")
    log("="*80)
    log(f"분석 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        # 연결 테스트
        log("\n[0단계] Oracle DB 연결 테스트 중...")
        try:
            test_result = fetch_one("SELECT '연결 성공' FROM DUAL")
            if test_result:
                log("✅ Oracle DB 연결 성공!")
            else:
                log("⚠️ 연결은 되었지만 쿼리 결과가 없습니다.")
        except Exception as e:
            log(f"❌ Oracle DB 연결 실패: {str(e)}")
            log("연결 정보를 확인해주세요.")
            return
        
        # 1. 모든 테이블 목록 조회
        log("\n[1단계] 테이블 목록 조회 중...")
        tables = get_all_tables()
        
        if not tables:
            log("❌ 테이블이 없습니다.")
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write('\n'.join(output_lines))
            log(f"\n분석 결과가 '{output_file}' 파일에 저장되었습니다.")
            return
        
        log(f"\n✅ 발견된 테이블: {len(tables)}개")
        table_names = [t['TABLE_NAME'] for t in tables]
        for i, table_name in enumerate(table_names, 1):
            row_count = get_table_row_count(table_name)
            log(f"  {i}. {table_name} ({row_count:,}개 행)")
        
        # 2. 각 테이블 상세 분석
        log(f"\n[2단계] 각 테이블 상세 분석 중...")
        for table_name in table_names:
            try:
                analyze_table_data(table_name)
            except Exception as e:
                log(f"\n❌ {table_name} 분석 중 오류: {str(e)}")
                import traceback
                error_trace = traceback.format_exc()
                log(error_trace)
        
        # 3. 요약 정보
        log(f"\n{'='*80}")
        log("분석 완료 요약")
        log(f"{'='*80}")
        log(f"총 테이블 수: {len(tables)}개")
        total_rows = sum(get_table_row_count(t['TABLE_NAME']) for t in tables)
        log(f"총 데이터 행 수: {total_rows:,}개")
        
        # 파일 저장
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(output_lines))
        
        log(f"\n✅ 분석 결과가 '{output_file}' 파일에 저장되었습니다.")
        
    except Exception as e:
        error_msg = f"\n❌ 오류 발생: {str(e)}"
        log(error_msg)
        import traceback
        error_trace = traceback.format_exc()
        log(error_trace)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(output_lines))
        
        log(f"\n오류 정보가 '{output_file}' 파일에 저장되었습니다.")

if __name__ == "__main__":
    main()

