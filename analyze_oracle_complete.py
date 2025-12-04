#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Oracle DB 완전 분석 스크립트 - 결과를 파일로 저장
"""

import sys
from pathlib import Path
from datetime import datetime

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

# 결과 파일
result_file = "ORACLE_DB_ANALYSIS_RESULT.md"

def write_result(msg):
    """결과를 파일에 추가"""
    with open(result_file, 'a', encoding='utf-8') as f:
        f.write(msg + '\n')
    print(msg)  # 콘솔에도 출력

def clear_result():
    """결과 파일 초기화"""
    with open(result_file, 'w', encoding='utf-8') as f:
        f.write(f"# Oracle DB 분석 결과\n\n")
        f.write(f"**분석 시간**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write("---\n\n")

def main():
    clear_result()
    
    write_result("## 1. 연결 테스트\n")
    
    try:
        from api.db.oracle_client import get_connection, fetch_one, fetch_all_dict
        
        write_result("### ✅ 연결 모듈 로드 성공\n")
        
        # 연결 테스트
        write_result("### 연결 확인 중...\n")
        result = fetch_one("SELECT USER, SYSDATE, '연결 성공!' FROM DUAL")
        
        if result:
            write_result(f"- **사용자**: {result[0]}")
            write_result(f"- **서버 시간**: {result[1]}")
            write_result(f"- **상태**: {result[2]}\n")
            write_result("### ✅ Oracle DB 연결 성공!\n")
        else:
            write_result("### ⚠️ 연결은 되었지만 결과가 없습니다.\n")
        
        # 테이블 목록
        write_result("\n## 2. 테이블 목록\n")
        tables = fetch_all_dict("""
            SELECT table_name 
            FROM user_tables 
            ORDER BY table_name
        """)
        
        if not tables:
            write_result("### ❌ 테이블이 없습니다.\n")
            return
        
        write_result(f"### 총 {len(tables)}개 테이블 발견\n\n")
        table_names = [t['TABLE_NAME'] for t in tables]
        
        for i, table_name in enumerate(table_names, 1):
            # 행 개수 조회
            count_sql = f"SELECT COUNT(*) FROM {table_name}"
            count_result = fetch_one(count_sql)
            row_count = count_result[0] if count_result else 0
            write_result(f"{i}. **{table_name}** ({row_count:,}개 행)\n")
        
        # 각 테이블 상세 분석
        write_result("\n## 3. 테이블 상세 분석\n")
        
        for table_name in table_names:
            write_result(f"\n### 테이블: {table_name}\n")
            
            # 컬럼 정보
            columns = fetch_all_dict("""
                SELECT 
                    column_name,
                    data_type,
                    data_length,
                    nullable,
                    data_default
                FROM user_tab_columns
                WHERE table_name = :table_name
                ORDER BY column_id
            """, {'table_name': table_name.upper()})
            
            write_result("#### 컬럼 정보\n")
            write_result("| 컬럼명 | 데이터 타입 | 길이 | NULL 허용 | 기본값 |\n")
            write_result("|--------|------------|------|----------|--------|\n")
            
            for col in columns:
                col_name = col['COLUMN_NAME']
                data_type = col['DATA_TYPE']
                data_length = col['DATA_LENGTH'] or ''
                nullable = 'Y' if col['NULLABLE'] == 'Y' else 'N'
                default = str(col['DATA_DEFAULT']) if col['DATA_DEFAULT'] else ''
                if len(default) > 30:
                    default = default[:30] + '...'
                
                write_result(f"| {col_name} | {data_type} | {data_length} | {nullable} | {default} |\n")
            
            # 행 개수
            count_result = fetch_one(f"SELECT COUNT(*) FROM {table_name}")
            row_count = count_result[0] if count_result else 0
            write_result(f"\n#### 데이터 개수: {row_count:,}개\n")
            
            # 샘플 데이터
            if row_count > 0:
                write_result("\n#### 샘플 데이터 (최대 3개)\n")
                try:
                    samples = fetch_all_dict(f"SELECT * FROM {table_name} WHERE ROWNUM <= 3")
                    if samples:
                        for i, row in enumerate(samples, 1):
                            write_result(f"\n**샘플 {i}:**\n")
                            for key, value in list(row.items())[:10]:  # 최대 10개 컬럼만
                                if isinstance(value, str) and len(value) > 100:
                                    value = value[:100] + "..."
                                if value is None:
                                    value = "NULL"
                                write_result(f"- `{key}`: {value}\n")
                except Exception as e:
                    write_result(f"⚠️ 샘플 데이터 조회 실패: {str(e)}\n")
            
            # 통계 정보 (숫자형 컬럼)
            numeric_cols = [col['COLUMN_NAME'] for col in columns 
                          if col['DATA_TYPE'] in ('NUMBER', 'FLOAT')]
            
            if numeric_cols and row_count > 0:
                write_result("\n#### 숫자형 컬럼 통계\n")
                for col_name in numeric_cols[:3]:  # 최대 3개
                    try:
                        stats = fetch_one(f"""
                            SELECT 
                                MIN({col_name}) as min_val,
                                MAX({col_name}) as max_val,
                                AVG({col_name}) as avg_val,
                                COUNT(DISTINCT {col_name}) as distinct_count
                            FROM {table_name}
                            WHERE {col_name} IS NOT NULL
                        """)
                        if stats and stats[0] is not None:
                            write_result(f"- **{col_name}**: 최소={stats[0]}, 최대={stats[1]}, 평균={stats[2]:.2f}, 고유값={stats[3]}개\n")
                    except:
                        pass
        
        # 요약
        write_result("\n## 4. 분석 요약\n")
        total_rows = sum(
            fetch_one(f"SELECT COUNT(*) FROM {t}")[0] 
            for t in table_names
        )
        write_result(f"- **총 테이블 수**: {len(tables)}개")
        write_result(f"- **총 데이터 행 수**: {total_rows:,}개\n")
        
        write_result("\n---\n")
        write_result(f"**분석 완료 시간**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        
    except ImportError as e:
        write_result(f"### ❌ 모듈 import 실패\n")
        write_result(f"```\n{str(e)}\n```\n")
        import traceback
        write_result(f"```\n{traceback.format_exc()}\n```\n")
    except Exception as e:
        write_result(f"### ❌ 오류 발생\n")
        write_result(f"**오류 타입**: {type(e).__name__}\n")
        write_result(f"**오류 메시지**: {str(e)}\n\n")
        import traceback
        write_result(f"```\n{traceback.format_exc()}\n```\n")

if __name__ == "__main__":
    main()
    print(f"\n✅ 분석 완료! 결과는 '{result_file}' 파일을 확인하세요.")



