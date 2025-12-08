#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
CSV 파일들을 Oracle DB에 로드하는 스크립트

사용법:
    python load_csv_to_oracle.py
"""

import sys
import os
import csv
import re
import ast
from pathlib import Path
from typing import List, Dict, Any

# 프로젝트 루트를 sys.path에 추가
BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from api.db.oracle_client import get_connection

# CSV 디렉토리
CSV_DIR = BASE_DIR / "data" / "csv"


def extract_category_from_filename(filename: str) -> str:
    """파일명에서 제품 카테고리 추출"""
    # 예: "냉장고_모델별_평균벡터.csv" -> "냉장고"
    # 예: "TV_모델별_리뷰_인구통계정보.csv" -> "TV"
    # 예: "LG전자_리뷰_김치냉장고_전자레인지_모델별_리뷰_인구통계정보.csv" -> "김치냉장고_전자레인지"
    
    # 파일명에서 확장자 제거
    name = filename.replace('.csv', '')
    
    # 특수 케이스 처리
    if 'LG전자_리뷰' in name:
        # "LG전자_리뷰_김치냉장고_전자레인지_모델별_리뷰_인구통계정보" -> "김치냉장고_전자레인지"
        parts = name.split('_')
        if len(parts) >= 4:
            return '_'.join(parts[2:-2])  # 중간 부분만 추출
    
    # 일반적인 경우: 첫 번째 언더스코어까지가 카테고리
    if '_' in name:
        return name.split('_')[0]
    
    return name


def parse_list_string(list_str: str) -> str:
    """Python 리스트 문자열을 JSON 형태로 변환"""
    if not list_str or list_str.strip() == '[]' or list_str.strip() == '':
        return '[]'
    
    try:
        # Python 리스트 문자열을 파싱
        parsed = ast.literal_eval(list_str)
        if isinstance(parsed, list):
            # JSON 형태로 변환 (단순히 문자열로 저장)
            return str(parsed)
        return '[]'
    except:
        # 파싱 실패 시 원본 반환
        return list_str


def load_recommend_reasons_csv(file_path: Path, category: str):
    """평균벡터 CSV 파일 로드 (model_name, recommend_reason)"""
    print(f"\n[로딩 중] {file_path.name} (카테고리: {category})")
    
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        inserted_count = 0
        updated_count = 0
        error_count = 0
        
        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            
            for row in reader:
                model_name = row.get('model_name', '').strip()
                recommend_reason = row.get('recommend_reason', '').strip()
                
                if not model_name:
                    continue
                
                try:
                    # MERGE 문 사용 (중복 시 업데이트)
                    sql = """
                    MERGE INTO product_recommend_reasons pr
                    USING (
                        SELECT :category AS product_category, :model_name AS model_name, :recommend_reason AS recommend_reason
                        FROM dual
                    ) src
                    ON (pr.product_category = src.product_category AND pr.model_name = src.model_name)
                    WHEN MATCHED THEN
                        UPDATE SET recommend_reason = src.recommend_reason, created_at = SYSDATE
                    WHEN NOT MATCHED THEN
                        INSERT (product_category, model_name, recommend_reason, created_at)
                        VALUES (src.product_category, src.model_name, src.recommend_reason, SYSDATE)
                    """
                    
                    cursor.execute(sql, {
                        'category': category,
                        'model_name': model_name,
                        'recommend_reason': recommend_reason
                    })
                    
                    if cursor.rowcount > 0:
                        # MERGE는 업데이트/삽입 여부를 구분하기 어려우므로 간단히 카운트
                        inserted_count += 1
                    
                except Exception as e:
                    error_count += 1
                    print(f"  [오류] 모델 {model_name}: {str(e)}")
        
        conn.commit()
        print(f"  [완료] 삽입/업데이트: {inserted_count}건, 오류: {error_count}건")
        
    except Exception as e:
        conn.rollback()
        print(f"  [실패] {str(e)}")
        raise
    finally:
        cursor.close()
        conn.close()


def load_demographics_csv(file_path: Path, category: str):
    """인구통계 정보 CSV 파일 로드 (Product_code, family_list, size_list, house_list)"""
    print(f"\n[로딩 중] {file_path.name} (카테고리: {category})")
    
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        inserted_count = 0
        updated_count = 0
        error_count = 0
        
        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            
            for row in reader:
                product_code = row.get('Product_code', '').strip()
                family_list = parse_list_string(row.get('family_list', '').strip())
                size_list = parse_list_string(row.get('size_list', '').strip())
                house_list = parse_list_string(row.get('house_list', '').strip())
                
                if not product_code:
                    continue
                
                try:
                    # MERGE 문 사용
                    sql = """
                    MERGE INTO product_review_demographics pd
                    USING (
                        SELECT :category AS product_category, :product_code AS product_code,
                               :family_list AS family_list, :size_list AS size_list, :house_list AS house_list
                        FROM dual
                    ) src
                    ON (pd.product_category = src.product_category AND pd.product_code = src.product_code)
                    WHEN MATCHED THEN
                        UPDATE SET 
                            family_list = src.family_list,
                            size_list = src.size_list,
                            house_list = src.house_list,
                            created_at = SYSDATE
                    WHEN NOT MATCHED THEN
                        INSERT (product_category, product_code, family_list, size_list, house_list, created_at)
                        VALUES (src.product_category, src.product_code, src.family_list, src.size_list, src.house_list, SYSDATE)
                    """
                    
                    cursor.execute(sql, {
                        'category': category,
                        'product_code': product_code,
                        'family_list': family_list,
                        'size_list': size_list,
                        'house_list': house_list
                    })
                    
                    if cursor.rowcount > 0:
                        inserted_count += 1
                    
                except Exception as e:
                    error_count += 1
                    print(f"  [오류] 제품코드 {product_code}: {str(e)}")
        
        conn.commit()
        print(f"  [완료] 삽입/업데이트: {inserted_count}건, 오류: {error_count}건")
        
    except Exception as e:
        conn.rollback()
        print(f"  [실패] {str(e)}")
        raise
    finally:
        cursor.close()
        conn.close()


def detect_csv_type(file_path: Path) -> str:
    """CSV 파일의 타입 감지 (평균벡터 또는 인구통계)"""
    with open(file_path, 'r', encoding='utf-8') as f:
        first_line = f.readline().strip()
        headers = [h.strip() for h in first_line.split(',')]
        
        if 'model_name' in headers and 'recommend_reason' in headers:
            return 'recommend_reasons'
        elif 'Product_code' in headers and 'family_list' in headers:
            return 'demographics'
        else:
            return 'unknown'


def main():
    """메인 함수"""
    print("=" * 60)
    print("CSV 데이터를 Oracle DB에 로드하는 스크립트")
    print("=" * 60)
    
    if not CSV_DIR.exists():
        print(f"[오류] CSV 디렉토리를 찾을 수 없습니다: {CSV_DIR}")
        return
    
    # CSV 파일 목록 가져오기
    csv_files = list(CSV_DIR.glob("*.csv"))
    
    if not csv_files:
        print(f"[오류] CSV 파일을 찾을 수 없습니다: {CSV_DIR}")
        return
    
    print(f"\n[발견] 총 {len(csv_files)}개의 CSV 파일")
    
    # 테이블 생성 확인
    print("\n[확인] 테이블 존재 여부 확인 중...")
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        # 테이블 존재 확인
        cursor.execute("""
            SELECT table_name FROM user_tables 
            WHERE table_name IN ('PRODUCT_RECOMMEND_REASONS', 'PRODUCT_REVIEW_DEMOGRAPHICS')
        """)
        existing_tables = [row[0] for row in cursor.fetchall()]
        
        if 'PRODUCT_RECOMMEND_REASONS' not in existing_tables:
            print("[경고] PRODUCT_RECOMMEND_REASONS 테이블이 없습니다.")
            print("       먼저 api/db/csv_data_tables_ddl.sql을 실행하여 테이블을 생성하세요.")
            return
        
        if 'PRODUCT_REVIEW_DEMOGRAPHICS' not in existing_tables:
            print("[경고] PRODUCT_REVIEW_DEMOGRAPHICS 테이블이 없습니다.")
            print("       먼저 api/db/csv_data_tables_ddl.sql을 실행하여 테이블을 생성하세요.")
            return
        
        print("[확인] 테이블이 존재합니다.")
        
    except Exception as e:
        print(f"[오류] 테이블 확인 중 오류 발생: {str(e)}")
        return
    finally:
        cursor.close()
        conn.close()
    
    # CSV 파일 처리
    recommend_reasons_files = []
    demographics_files = []
    unknown_files = []
    
    for csv_file in csv_files:
        csv_type = detect_csv_type(csv_file)
        category = extract_category_from_filename(csv_file.name)
        
        if csv_type == 'recommend_reasons':
            recommend_reasons_files.append((csv_file, category))
        elif csv_type == 'demographics':
            demographics_files.append((csv_file, category))
        else:
            unknown_files.append((csv_file, category))
    
    print(f"\n[분류] 평균벡터 파일: {len(recommend_reasons_files)}개")
    print(f"       인구통계 파일: {len(demographics_files)}개")
    if unknown_files:
        print(f"       알 수 없는 형식: {len(unknown_files)}개")
    
    # 평균벡터 파일 로드
    if recommend_reasons_files:
        print("\n" + "=" * 60)
        print("평균벡터 데이터 로드 시작")
        print("=" * 60)
        for csv_file, category in recommend_reasons_files:
            try:
                load_recommend_reasons_csv(csv_file, category)
            except Exception as e:
                print(f"[중단] {csv_file.name} 처리 중 오류: {str(e)}")
                continue
    
    # 인구통계 파일 로드
    if demographics_files:
        print("\n" + "=" * 60)
        print("인구통계 데이터 로드 시작")
        print("=" * 60)
        for csv_file, category in demographics_files:
            try:
                load_demographics_csv(csv_file, category)
            except Exception as e:
                print(f"[중단] {csv_file.name} 처리 중 오류: {str(e)}")
                continue
    
    # 알 수 없는 파일 리포트
    if unknown_files:
        print("\n" + "=" * 60)
        print("알 수 없는 형식의 파일")
        print("=" * 60)
        for csv_file, category in unknown_files:
            print(f"  - {csv_file.name} (카테고리: {category})")
    
    print("\n" + "=" * 60)
    print("모든 작업 완료!")
    print("=" * 60)


if __name__ == "__main__":
    main()

