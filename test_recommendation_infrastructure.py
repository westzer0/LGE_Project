#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Step 1: 추천 엔진 인프라 확인 - 제품 데이터, 카테고리 구조, Taste-카테고리 매핑 확인

검증 항목:
1. 제품 데이터 테이블 확인
2. 카테고리 테이블 확인
3. Taste-카테고리 매핑 확인
4. 제품-카테고리 관계 확인
5. 예산/조건 필터링 필드 확인
6. 인덱스 및 성능 확인
"""
import sys
import os
from datetime import datetime
import json

# Django 설정 로드
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

import django
django.setup()

from api.db.oracle_client import get_connection, fetch_all_dict, fetch_one
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')  # GUI 없이 사용
from collections import defaultdict


class RecommendationInfrastructureValidator:
    """추천 엔진 인프라 확인 클래스"""
    
    def __init__(self):
        self.results = {
            'product_tables': {},
            'category_structure': {},
            'taste_category_mapping': {},
            'product_category_relationship': {},
            'filtering_fields': {},
            'indexes': {},
            'data_counts': {},
            'errors': []
        }
        self.timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    def validate_all(self):
        """모든 인프라 확인 실행"""
        print("=" * 80)
        print("Step 1: 추천 엔진 인프라 확인")
        print("=" * 80)
        print()
        
        try:
            # 1. 제품 데이터 테이블 확인
            self._validate_product_tables()
            
            # 2. 카테고리 테이블 확인
            self._validate_category_tables()
            
            # 3. Taste-카테고리 매핑 확인
            self._validate_taste_category_mapping()
            
            # 4. 제품-카테고리 관계 확인
            self._validate_product_category_relationship()
            
            # 5. 예산/조건 필터링 필드 확인
            self._validate_filtering_fields()
            
            # 6. 인덱스 확인
            self._check_indexes()
            
            # 7. 데이터 존재 여부 확인
            self._check_data_counts()
            
            # 8. 결과 출력
            self._print_results()
            
            # 9. 시각화 생성
            self._create_visualizations()
            
        except Exception as e:
            print(f"\n❌ 검증 중 예외 발생: {e}")
            import traceback
            traceback.print_exc()
            return False
        
        return self._is_all_passed()
    
    def _validate_product_tables(self):
        """제품 데이터 테이블 확인"""
        print("[1] 제품 데이터 테이블 확인...")
        
        try:
            with get_connection() as conn:
                with conn.cursor() as cur:
                    # PRODUCT 테이블 존재 확인
                    table_exists = self._table_exists(cur, 'PRODUCT')
                    self.results['product_tables']['PRODUCT_EXISTS'] = table_exists
                    
                    if table_exists:
                        print("  ✅ PRODUCT 테이블 존재")
                        
                        # 컬럼 구조 확인
                        columns = self._get_table_columns(cur, 'PRODUCT')
                        self.results['product_tables']['COLUMNS'] = columns
                        
                        required_columns = [
                            'PRODUCT_ID', 'PRODUCT_NAME', 'MAIN_CATEGORY',
                            'PRICE', 'STATUS'
                        ]
                        
                        print("  [필수 컬럼 확인]")
                        for col in required_columns:
                            exists = col in columns
                            status = "✅" if exists else "❌"
                            print(f"    {status} {col}")
                            if not exists:
                                self.results['errors'].append(f"PRODUCT.{col} 컬럼이 없습니다")
                        
                        # 제품 수 확인
                        count = self._get_table_count(cur, 'PRODUCT')
                        self.results['data_counts']['PRODUCT_COUNT'] = count
                        print(f"  📊 제품 수: {count:,}개")
                        
                        if count < 100:
                            print("  ⚠️ 제품 수가 100개 미만입니다 (추천 엔진 실행에 부족할 수 있음)")
                            self.results['errors'].append("제품 수가 100개 미만입니다")
                    else:
                        print("  ❌ PRODUCT 테이블이 존재하지 않습니다")
                        self.results['errors'].append("PRODUCT 테이블이 존재하지 않습니다")
                        
        except Exception as e:
            self.results['errors'].append(f"제품 테이블 확인 중 오류: {str(e)}")
            print(f"  ❌ 오류: {e}")
        print()
    
    def _validate_category_tables(self):
        """카테고리 테이블 확인"""
        print("[2] 카테고리 구조 확인...")
        
        try:
            with get_connection() as conn:
                with conn.cursor() as cur:
                    # PRODUCT 테이블에서 카테고리 정보 추출
                    categories = fetch_all_dict("""
                        SELECT 
                            MAIN_CATEGORY,
                            COUNT(*) as PRODUCT_COUNT
                        FROM PRODUCT
                        WHERE MAIN_CATEGORY IS NOT NULL
                        GROUP BY MAIN_CATEGORY
                        ORDER BY COUNT(*) DESC
                    """)
                    
                    self.results['category_structure']['CATEGORIES'] = categories
                    self.results['category_structure']['CATEGORY_COUNT'] = len(categories)
                    
                    print(f"  📊 카테고리 수: {len(categories)}개")
                    print("  [카테고리별 제품 수]")
                    
                    for cat in categories[:10]:  # 상위 10개만 출력
                        cat_name = cat['MAIN_CATEGORY']
                        count = cat['PRODUCT_COUNT']
                        print(f"    • {cat_name}: {count:,}개")
                    
                    if len(categories) == 0:
                        print("  ⚠️ 카테고리가 없습니다")
                        self.results['errors'].append("카테고리가 없습니다")
                    
        except Exception as e:
            self.results['errors'].append(f"카테고리 확인 중 오류: {str(e)}")
            print(f"  ❌ 오류: {e}")
        print()
    
    def _validate_taste_category_mapping(self):
        """Taste-카테고리 매핑 확인"""
        print("[3] Taste-카테고리 매핑 확인...")
        
        try:
            with get_connection() as conn:
                with conn.cursor() as cur:
                    # TASTE_CONFIG 테이블 확인
                    taste_config_exists = self._table_exists(cur, 'TASTE_CONFIG')
                    self.results['taste_category_mapping']['TASTE_CONFIG_EXISTS'] = taste_config_exists
                    
                    if taste_config_exists:
                        print("  ✅ TASTE_CONFIG 테이블 존재")
                        
                        # TASTE_CATEGORY_SCORES 테이블 확인 (정규화된 매핑)
                        taste_category_scores_exists = self._table_exists(cur, 'TASTE_CATEGORY_SCORES')
                        self.results['taste_category_mapping']['TASTE_CATEGORY_SCORES_EXISTS'] = taste_category_scores_exists
                        
                        if taste_category_scores_exists:
                            print("  ✅ TASTE_CATEGORY_SCORES 테이블 존재 (정규화된 매핑)")
                            
                            # Taste ID별 매핑 수 확인
                            taste_mappings = fetch_all_dict("""
                                SELECT 
                                    TASTE_ID,
                                    COUNT(*) as CATEGORY_COUNT
                                FROM TASTE_CATEGORY_SCORES
                                GROUP BY TASTE_ID
                                ORDER BY TASTE_ID
                            """)
                            
                            self.results['taste_category_mapping']['MAPPINGS'] = taste_mappings
                            
                            # 모든 Taste ID(1-120)에 매핑이 있는지 확인
                            taste_ids_with_mapping = {m['TASTE_ID'] for m in taste_mappings}
                            expected_taste_ids = set(range(1, 121))
                            missing_taste_ids = expected_taste_ids - taste_ids_with_mapping
                            
                            if missing_taste_ids:
                                print(f"  ⚠️ {len(missing_taste_ids)}개 Taste ID에 매핑이 없습니다: {sorted(list(missing_taste_ids))[:10]}...")
                                self.results['errors'].append(f"{len(missing_taste_ids)}개 Taste ID에 매핑이 없습니다")
                            else:
                                print("  ✅ 모든 Taste ID(1-120)에 매핑이 존재합니다")
                            
                            # 매핑 통계
                            if taste_mappings:
                                avg_categories = sum(m['CATEGORY_COUNT'] for m in taste_mappings) / len(taste_mappings)
                                print(f"  📊 Taste당 평균 카테고리 수: {avg_categories:.1f}개")
                        else:
                            # TASTE_CONFIG의 RECOMMENDED_CATEGORIES 필드 확인
                            print("  ⚠️ TASTE_CATEGORY_SCORES 테이블이 없습니다. TASTE_CONFIG.RECOMMENDED_CATEGORIES 확인...")
                            
                            taste_configs = fetch_all_dict("""
                                SELECT 
                                    TASTE_ID,
                                    RECOMMENDED_CATEGORIES
                                FROM TASTE_CONFIG
                                WHERE TASTE_ID BETWEEN 1 AND 120
                                ORDER BY TASTE_ID
                            """)
                            
                            taste_ids_with_data = {t['TASTE_ID'] for t in taste_configs if t.get('RECOMMENDED_CATEGORIES')}
                            expected_taste_ids = set(range(1, 121))
                            missing_taste_ids = expected_taste_ids - taste_ids_with_data
                            
                            if missing_taste_ids:
                                print(f"  ⚠️ {len(missing_taste_ids)}개 Taste ID에 데이터가 없습니다")
                                self.results['errors'].append(f"{len(missing_taste_ids)}개 Taste ID에 데이터가 없습니다")
                            else:
                                print("  ✅ 모든 Taste ID(1-120)에 데이터가 존재합니다")
                    else:
                        print("  ❌ TASTE_CONFIG 테이블이 존재하지 않습니다")
                        self.results['errors'].append("TASTE_CONFIG 테이블이 존재하지 않습니다")
                        
        except Exception as e:
            self.results['errors'].append(f"Taste-카테고리 매핑 확인 중 오류: {str(e)}")
            print(f"  ❌ 오류: {e}")
        print()
    
    def _validate_product_category_relationship(self):
        """제품-카테고리 관계 확인"""
        print("[4] 제품-카테고리 관계 확인...")
        
        try:
            with get_connection() as conn:
                with conn.cursor() as cur:
                    # PRODUCT 테이블에서 MAIN_CATEGORY 필드 확인
                    products_with_category = fetch_one("""
                        SELECT COUNT(*) 
                        FROM PRODUCT 
                        WHERE MAIN_CATEGORY IS NOT NULL
                    """)
                    
                    total_products = fetch_one("""
                        SELECT COUNT(*) 
                        FROM PRODUCT
                    """)
                    
                    if total_products and products_with_category:
                        total = total_products[0]
                        with_cat = products_with_category[0]
                        percentage = (with_cat / total * 100) if total > 0 else 0
                        
                        self.results['product_category_relationship']['TOTAL_PRODUCTS'] = total
                        self.results['product_category_relationship']['PRODUCTS_WITH_CATEGORY'] = with_cat
                        self.results['product_category_relationship']['PERCENTAGE'] = percentage
                        
                        print(f"  📊 총 제품 수: {total:,}개")
                        print(f"  📊 카테고리가 있는 제품: {with_cat:,}개 ({percentage:.1f}%)")
                        
                        if percentage < 90:
                            print("  ⚠️ 카테고리가 없는 제품이 10% 이상입니다")
                            self.results['errors'].append("카테고리가 없는 제품이 많습니다")
                        
                        # 카테고리별 제품 수 분포
                        category_distribution = fetch_all_dict("""
                            SELECT 
                                MAIN_CATEGORY,
                                COUNT(*) as PRODUCT_COUNT
                            FROM PRODUCT
                            WHERE MAIN_CATEGORY IS NOT NULL
                            GROUP BY MAIN_CATEGORY
                            ORDER BY COUNT(*) DESC
                        """)
                        
                        self.results['product_category_relationship']['DISTRIBUTION'] = category_distribution
                        
        except Exception as e:
            self.results['errors'].append(f"제품-카테고리 관계 확인 중 오류: {str(e)}")
            print(f"  ❌ 오류: {e}")
        print()
    
    def _validate_filtering_fields(self):
        """예산/조건 필터링 필드 확인"""
        print("[5] 예산/조건 필터링 필드 확인...")
        
        try:
            with get_connection() as conn:
                with conn.cursor() as cur:
                    # PRODUCT 테이블의 가격 필드 확인
                    price_column_exists = self._column_exists(cur, 'PRODUCT', 'PRICE')
                    discount_price_exists = self._column_exists(cur, 'PRODUCT', 'DISCOUNT_PRICE')
                    
                    self.results['filtering_fields']['PRICE_EXISTS'] = price_column_exists
                    self.results['filtering_fields']['DISCOUNT_PRICE_EXISTS'] = discount_price_exists
                    
                    if price_column_exists:
                        print("  ✅ PRICE 필드 존재")
                        
                        # 가격 데이터 통계
                        price_stats = fetch_one("""
                            SELECT 
                                COUNT(*) as TOTAL,
                                COUNT(PRICE) as WITH_PRICE,
                                MIN(PRICE) as MIN_PRICE,
                                MAX(PRICE) as MAX_PRICE,
                                AVG(PRICE) as AVG_PRICE
                            FROM PRODUCT
                        """)
                        
                        if price_stats:
                            total, with_price, min_price, max_price, avg_price = price_stats
                            self.results['filtering_fields']['PRICE_STATS'] = {
                                'total': total,
                                'with_price': with_price,
                                'min': float(min_price) if min_price else None,
                                'max': float(max_price) if max_price else None,
                                'avg': float(avg_price) if avg_price else None
                            }
                            
                            print(f"    📊 가격이 있는 제품: {with_price:,}개 / {total:,}개")
                            if min_price and max_price:
                                print(f"    📊 가격 범위: {min_price:,}원 ~ {max_price:,}원")
                                print(f"    📊 평균 가격: {avg_price:,.0f}원")
                    else:
                        print("  ❌ PRICE 필드가 없습니다")
                        self.results['errors'].append("PRODUCT.PRICE 필드가 없습니다")
                    
                    if discount_price_exists:
                        print("  ✅ DISCOUNT_PRICE 필드 존재")
                    else:
                        print("  ⚠️ DISCOUNT_PRICE 필드가 없습니다 (선택사항)")
                    
                    # STATUS 필드 확인 (판매 중/품절 필터링)
                    status_exists = self._column_exists(cur, 'PRODUCT', 'STATUS')
                    self.results['filtering_fields']['STATUS_EXISTS'] = status_exists
                    
                    if status_exists:
                        print("  ✅ STATUS 필드 존재")
                        
                        # 상태별 제품 수
                        status_distribution = fetch_all_dict("""
                            SELECT 
                                STATUS,
                                COUNT(*) as COUNT
                            FROM PRODUCT
                            WHERE STATUS IS NOT NULL
                            GROUP BY STATUS
                            ORDER BY COUNT(*) DESC
                        """)
                        
                        self.results['filtering_fields']['STATUS_DISTRIBUTION'] = status_distribution
                        
                        print("    [상태별 제품 수]")
                        for stat in status_distribution:
                            print(f"      • {stat['STATUS']}: {stat['COUNT']:,}개")
                    else:
                        print("  ⚠️ STATUS 필드가 없습니다")
                    
        except Exception as e:
            self.results['errors'].append(f"필터링 필드 확인 중 오류: {str(e)}")
            print(f"  ❌ 오류: {e}")
        print()
    
    def _check_indexes(self):
        """인덱스 확인"""
        print("[6] 인덱스 확인...")
        
        try:
            with get_connection() as conn:
                with conn.cursor() as cur:
                    # PRODUCT 테이블 인덱스 확인
                    product_indexes = self._get_table_indexes(cur, 'PRODUCT')
                    self.results['indexes']['PRODUCT'] = product_indexes
                    
                    print("  [PRODUCT 테이블 인덱스]")
                    important_indexes = ['MAIN_CATEGORY', 'PRICE', 'STATUS', 'PRODUCT_ID']
                    
                    for idx in product_indexes:
                        idx_name = idx.get('INDEX_NAME', '')
                        idx_columns = idx.get('COLUMNS', '')
                        print(f"    • {idx_name}: {idx_columns}")
                    
                    # 중요 인덱스 확인
                    index_columns = [idx.get('COLUMNS', '') for idx in product_indexes]
                    missing_indexes = []
                    
                    for col in important_indexes:
                        has_index = any(col in cols for cols in index_columns)
                        if not has_index:
                            missing_indexes.append(col)
                    
                    if missing_indexes:
                        print(f"  ⚠️ 다음 컬럼에 인덱스가 없습니다: {', '.join(missing_indexes)}")
                        self.results['errors'].append(f"인덱스 부족: {', '.join(missing_indexes)}")
                    else:
                        print("  ✅ 주요 컬럼에 인덱스가 존재합니다")
                    
                    # TASTE_CATEGORY_SCORES 인덱스 확인
                    if self._table_exists(cur, 'TASTE_CATEGORY_SCORES'):
                        taste_indexes = self._get_table_indexes(cur, 'TASTE_CATEGORY_SCORES')
                        self.results['indexes']['TASTE_CATEGORY_SCORES'] = taste_indexes
                        
                        print("  [TASTE_CATEGORY_SCORES 테이블 인덱스]")
                        for idx in taste_indexes:
                            idx_name = idx.get('INDEX_NAME', '')
                            idx_columns = idx.get('COLUMNS', '')
                            print(f"    • {idx_name}: {idx_columns}")
                    
        except Exception as e:
            self.results['errors'].append(f"인덱스 확인 중 오류: {str(e)}")
            print(f"  ❌ 오류: {e}")
        print()
    
    def _check_data_counts(self):
        """데이터 존재 여부 확인"""
        print("[7] 데이터 존재 여부 확인...")
        
        try:
            with get_connection() as conn:
                with conn.cursor() as cur:
                    # 각 테이블의 레코드 수 확인
                    tables_to_check = [
                        'PRODUCT',
                        'TASTE_CONFIG',
                        'TASTE_CATEGORY_SCORES',
                        'TASTE_RECOMMENDED_PRODUCTS',
                        'MEMBER'
                    ]
                    
                    for table_name in tables_to_check:
                        if self._table_exists(cur, table_name):
                            count = self._get_table_count(cur, table_name)
                            self.results['data_counts'][table_name] = count
                            print(f"  • {table_name}: {count:,}개")
                        else:
                            print(f"  • {table_name}: 테이블 없음")
                    
        except Exception as e:
            self.results['errors'].append(f"데이터 수 확인 중 오류: {str(e)}")
            print(f"  ❌ 오류: {e}")
        print()
    
    def _table_exists(self, cur, table_name):
        """테이블 존재 여부 확인"""
        try:
            cur.execute("""
                SELECT COUNT(*) 
                FROM USER_TABLES 
                WHERE TABLE_NAME = :table_name
            """, {'table_name': table_name})
            return cur.fetchone()[0] > 0
        except:
            return False
    
    def _column_exists(self, cur, table_name, column_name):
        """컬럼 존재 여부 확인"""
        try:
            cur.execute("""
                SELECT COUNT(*) 
                FROM USER_TAB_COLUMNS 
                WHERE TABLE_NAME = :table_name 
                  AND COLUMN_NAME = :column_name
            """, {
                'table_name': table_name,
                'column_name': column_name
            })
            return cur.fetchone()[0] > 0
        except:
            return False
    
    def _get_table_columns(self, cur, table_name):
        """테이블의 모든 컬럼 목록 반환"""
        try:
            cur.execute("""
                SELECT COLUMN_NAME
                FROM USER_TAB_COLUMNS
                WHERE TABLE_NAME = :table_name
                ORDER BY COLUMN_ID
            """, {'table_name': table_name})
            return [row[0] for row in cur.fetchall()]
        except:
            return []
    
    def _get_table_count(self, cur, table_name):
        """테이블의 레코드 수 반환"""
        try:
            cur.execute(f"SELECT COUNT(*) FROM {table_name}")
            return cur.fetchone()[0]
        except:
            return 0
    
    def _get_table_indexes(self, cur, table_name):
        """테이블의 인덱스 목록 반환"""
        try:
            cur.execute("""
                SELECT 
                    i.INDEX_NAME,
                    LISTAGG(ic.COLUMN_NAME, ', ') WITHIN GROUP (ORDER BY ic.COLUMN_POSITION) as COLUMNS
                FROM USER_INDEXES i
                JOIN USER_IND_COLUMNS ic ON i.INDEX_NAME = ic.INDEX_NAME
                WHERE i.TABLE_NAME = :table_name
                  AND i.INDEX_TYPE != 'LOB'
                GROUP BY i.INDEX_NAME
                ORDER BY i.INDEX_NAME
            """, {'table_name': table_name})
            
            indexes = []
            for row in cur.fetchall():
                indexes.append({
                    'INDEX_NAME': row[0],
                    'COLUMNS': row[1]
                })
            return indexes
        except:
            return []
    
    def _print_results(self):
        """검증 결과 출력"""
        print("=" * 80)
        print("검증 결과 요약")
        print("=" * 80)
        
        # 제품 테이블
        if self.results['product_tables'].get('PRODUCT_EXISTS'):
            print("✅ 제품 테이블: 존재")
            print(f"   제품 수: {self.results['data_counts'].get('PRODUCT_COUNT', 0):,}개")
        else:
            print("❌ 제품 테이블: 없음")
        
        # 카테고리 구조
        category_count = self.results['category_structure'].get('CATEGORY_COUNT', 0)
        print(f"✅ 카테고리 수: {category_count}개")
        
        # Taste-카테고리 매핑
        if self.results['taste_category_mapping'].get('TASTE_CONFIG_EXISTS'):
            print("✅ TASTE_CONFIG 테이블: 존재")
            if self.results['taste_category_mapping'].get('TASTE_CATEGORY_SCORES_EXISTS'):
                print("✅ TASTE_CATEGORY_SCORES 테이블: 존재 (정규화된 매핑)")
            else:
                print("⚠️ TASTE_CATEGORY_SCORES 테이블: 없음")
        else:
            print("❌ TASTE_CONFIG 테이블: 없음")
        
        # 제품-카테고리 관계
        percentage = self.results['product_category_relationship'].get('PERCENTAGE', 0)
        print(f"✅ 카테고리가 있는 제품: {percentage:.1f}%")
        
        # 필터링 필드
        if self.results['filtering_fields'].get('PRICE_EXISTS'):
            print("✅ PRICE 필드: 존재")
        else:
            print("❌ PRICE 필드: 없음")
        
        # 에러
        if self.results['errors']:
            print(f"\n⚠️ 발견된 문제: {len(self.results['errors'])}개")
            for i, error in enumerate(self.results['errors'][:5], 1):  # 최대 5개만 출력
                print(f"  {i}. {error}")
            if len(self.results['errors']) > 5:
                print(f"  ... 외 {len(self.results['errors']) - 5}개")
        
        print()
    
    def _create_visualizations(self):
        """시각화 생성"""
        print("[8] 시각화 생성...")
        
        try:
            # 1. 카테고리별 제품 수 분포
            if 'DISTRIBUTION' in self.results['product_category_relationship']:
                distribution = self.results['product_category_relationship']['DISTRIBUTION']
                if distribution:
                    self._plot_category_distribution(distribution)
            
            # 2. Taste-카테고리 매핑 분포
            if 'MAPPINGS' in self.results['taste_category_mapping']:
                mappings = self.results['taste_category_mapping']['MAPPINGS']
                if mappings:
                    self._plot_taste_category_mapping(mappings)
            
            # 3. 제품 가격 분포
            if 'PRICE_STATS' in self.results['filtering_fields']:
                price_stats = self.results['filtering_fields']['PRICE_STATS']
                if price_stats and price_stats.get('with_price', 0) > 0:
                    self._plot_price_distribution()
            
            print("  ✅ 시각화 파일 생성 완료")
            
        except Exception as e:
            print(f"  ⚠️ 시각화 생성 중 오류: {e}")
            import traceback
            traceback.print_exc()
        print()
    
    def _plot_category_distribution(self, distribution):
        """카테고리별 제품 수 분포 그래프"""
        try:
            categories = [d['MAIN_CATEGORY'] for d in distribution[:15]]  # 상위 15개
            counts = [d['PRODUCT_COUNT'] for d in distribution[:15]]
            
            plt.figure(figsize=(12, 6))
            plt.barh(categories, counts)
            plt.xlabel('제품 수')
            plt.title('카테고리별 제품 수 분포')
            plt.tight_layout()
            
            filename = f'recommendation_infrastructure_category_distribution_{self.timestamp}.png'
            plt.savefig(filename, dpi=150, bbox_inches='tight')
            plt.close()
            
            print(f"    📊 {filename} 생성 완료")
        except Exception as e:
            print(f"    ⚠️ 카테고리 분포 그래프 생성 실패: {e}")
    
    def _plot_taste_category_mapping(self, mappings):
        """Taste-카테고리 매핑 분포 그래프"""
        try:
            taste_ids = [m['TASTE_ID'] for m in mappings]
            category_counts = [m['CATEGORY_COUNT'] for m in mappings]
            
            plt.figure(figsize=(14, 6))
            plt.plot(taste_ids, category_counts, marker='o', markersize=2, linewidth=0.5)
            plt.xlabel('Taste ID')
            plt.ylabel('카테고리 수')
            plt.title('Taste별 카테고리 매핑 수 분포')
            plt.grid(True, alpha=0.3)
            plt.tight_layout()
            
            filename = f'recommendation_infrastructure_taste_mapping_{self.timestamp}.png'
            plt.savefig(filename, dpi=150, bbox_inches='tight')
            plt.close()
            
            print(f"    📊 {filename} 생성 완료")
        except Exception as e:
            print(f"    ⚠️ Taste 매핑 그래프 생성 실패: {e}")
    
    def _plot_price_distribution(self):
        """제품 가격 분포 그래프"""
        try:
            with get_connection() as conn:
                with conn.cursor() as cur:
                    # 가격 데이터 샘플링 (너무 많으면)
                    # Oracle 11g 호환: ROWNUM 사용
                    prices = fetch_all_dict("""
                        SELECT PRICE
                        FROM (
                            SELECT PRICE
                            FROM PRODUCT
                            WHERE PRICE IS NOT NULL
                              AND PRICE > 0
                            ORDER BY DBMS_RANDOM.VALUE
                        )
                        WHERE ROWNUM <= 1000
                    """)
                    
                    if prices:
                        price_values = [float(p['PRICE']) for p in prices if p.get('PRICE')]
                        
                        plt.figure(figsize=(10, 6))
                        plt.hist(price_values, bins=50, edgecolor='black', alpha=0.7)
                        plt.xlabel('가격 (원)')
                        plt.ylabel('제품 수')
                        plt.title('제품 가격 분포')
                        plt.tight_layout()
                        
                        filename = f'recommendation_infrastructure_price_distribution_{self.timestamp}.png'
                        plt.savefig(filename, dpi=150, bbox_inches='tight')
                        plt.close()
                        
                        print(f"    📊 {filename} 생성 완료")
        except Exception as e:
            print(f"    ⚠️ 가격 분포 그래프 생성 실패: {e}")
    
    def _is_all_passed(self):
        """모든 검증 통과 여부"""
        # 필수 항목 체크
        if not self.results['product_tables'].get('PRODUCT_EXISTS'):
            return False
        
        if not self.results['taste_category_mapping'].get('TASTE_CONFIG_EXISTS'):
            return False
        
        if not self.results['filtering_fields'].get('PRICE_EXISTS'):
            return False
        
        # 제품 수 체크
        product_count = self.results['data_counts'].get('PRODUCT_COUNT', 0)
        if product_count < 10:
            return False
        
        return True


def main():
    """메인 함수"""
    validator = RecommendationInfrastructureValidator()
    success = validator.validate_all()
    
    if success:
        print("=" * 80)
        print("✅ Step 1 검증 완료: 추천 엔진 인프라가 준비되어 있습니다!")
        print("=" * 80)
        return 0
    else:
        print("=" * 80)
        print("❌ Step 1 검증 실패: 일부 인프라가 준비되지 않았습니다.")
        print("=" * 80)
        return 1


if __name__ == '__main__':
    exit(main())

