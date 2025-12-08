"""
TASTE_CONFIG 정규화 마이그레이션 명령어

기존 TASTE_CONFIG 테이블의 JSON 컬럼과 개별 점수 컬럼을
정규화된 테이블(TASTE_CATEGORY_SCORES, TASTE_RECOMMENDED_PRODUCTS)로 마이그레이션합니다.

사용법:
    python manage.py migrate_taste_config_to_normalized
    python manage.py migrate_taste_config_to_normalized --dry-run  # 테스트만 실행
    python manage.py migrate_taste_config_to_normalized --taste-range 1-10  # 특정 범위만
"""
import json
from django.core.management.base import BaseCommand
from api.db.oracle_client import get_connection


class Command(BaseCommand):
    help = 'TASTE_CONFIG 테이블을 정규화된 구조로 마이그레이션'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='실제 마이그레이션 없이 테스트만 실행',
        )
        parser.add_argument(
            '--taste-range',
            type=str,
            help='마이그레이션할 taste 범위 (예: 1-10, 1-120)',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        taste_range = options.get('taste_range', '1-120')
        
        if dry_run:
            self.stdout.write(self.style.WARNING('=== DRY RUN 모드 (실제 변경 없음) ===\n'))
        
        # Taste 범위 파싱
        start_taste, end_taste = map(int, taste_range.split('-'))
        
        self.stdout.write(self.style.SUCCESS(f'\n=== TASTE_CONFIG 정규화 마이그레이션 ===\n'))
        self.stdout.write(f'범위: Taste {start_taste} ~ {end_taste}\n')
        
        # 1. 새 테이블 생성 확인
        if not dry_run:
            self._ensure_normalized_tables()
        
        # 2. 데이터 마이그레이션
        migrated_count = 0
        error_count = 0
        
        for taste_id in range(start_taste, end_taste + 1):
            try:
                if self._migrate_taste_config(taste_id, dry_run):
                    migrated_count += 1
                    if taste_id % 10 == 0:
                        self.stdout.write(f'진행: {taste_id}/{end_taste}...')
                else:
                    error_count += 1
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'Taste {taste_id} 마이그레이션 실패: {str(e)}')
                )
                error_count += 1
        
        # 3. 결과 출력
        self.stdout.write(self.style.SUCCESS(f'\n=== 마이그레이션 완료 ==='))
        self.stdout.write(f'성공: {migrated_count}개')
        self.stdout.write(f'실패: {error_count}개')
        
        if dry_run:
            self.stdout.write(self.style.WARNING('\nDRY RUN 모드였으므로 실제 변경은 없습니다.'))
        else:
            self.stdout.write(self.style.SUCCESS('\n마이그레이션이 완료되었습니다.'))

    def _ensure_normalized_tables(self):
        """정규화된 테이블이 존재하는지 확인하고 없으면 생성"""
        try:
            with get_connection() as conn:
                with conn.cursor() as cur:
                    # TASTE_CATEGORY_SCORES 테이블 확인
                    cur.execute("""
                        SELECT COUNT(*) 
                        FROM USER_TABLES 
                        WHERE TABLE_NAME = 'TASTE_CATEGORY_SCORES'
                    """)
                    if cur.fetchone()[0] == 0:
                        self.stdout.write('TASTE_CATEGORY_SCORES 테이블 생성 중...')
                        self._create_category_scores_table(cur)
                    
                    # TASTE_RECOMMENDED_PRODUCTS 테이블 확인
                    cur.execute("""
                        SELECT COUNT(*) 
                        FROM USER_TABLES 
                        WHERE TABLE_NAME = 'TASTE_RECOMMENDED_PRODUCTS'
                    """)
                    if cur.fetchone()[0] == 0:
                        self.stdout.write('TASTE_RECOMMENDED_PRODUCTS 테이블 생성 중...')
                        self._create_recommended_products_table(cur)
                    
                    conn.commit()
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'테이블 생성 실패: {str(e)}')
            )
            raise

    def _create_category_scores_table(self, cur):
        """TASTE_CATEGORY_SCORES 테이블 생성"""
        cur.execute("""
            CREATE TABLE TASTE_CATEGORY_SCORES (
                TASTE_ID NUMBER NOT NULL,
                CATEGORY_NAME VARCHAR2(50) NOT NULL,
                SCORE NUMBER(5,2) NOT NULL,
                IS_RECOMMENDED CHAR(1) DEFAULT 'N',
                IS_ILL_SUITED CHAR(1) DEFAULT 'N',
                CREATED_AT DATE DEFAULT SYSDATE,
                UPDATED_AT DATE DEFAULT SYSDATE,
                PRIMARY KEY (TASTE_ID, CATEGORY_NAME),
                FOREIGN KEY (TASTE_ID) REFERENCES TASTE_CONFIG(TASTE_ID) ON DELETE CASCADE
            )
        """)
        
        cur.execute("""
            CREATE INDEX IDX_TASTE_CAT_SCORES_TASTE ON TASTE_CATEGORY_SCORES(TASTE_ID)
        """)
        
        cur.execute("""
            CREATE INDEX IDX_TASTE_CAT_SCORES_CAT ON TASTE_CATEGORY_SCORES(CATEGORY_NAME)
        """)

    def _create_recommended_products_table(self, cur):
        """TASTE_RECOMMENDED_PRODUCTS 테이블 생성"""
        cur.execute("""
            CREATE TABLE TASTE_RECOMMENDED_PRODUCTS (
                TASTE_ID NUMBER NOT NULL,
                CATEGORY_NAME VARCHAR2(50) NOT NULL,
                PRODUCT_ID NUMBER NOT NULL,
                SCORE NUMBER(5,2),
                RANK_ORDER NUMBER(2),
                CREATED_AT DATE DEFAULT SYSDATE,
                UPDATED_AT DATE DEFAULT SYSDATE,
                PRIMARY KEY (TASTE_ID, CATEGORY_NAME, PRODUCT_ID),
                FOREIGN KEY (TASTE_ID) REFERENCES TASTE_CONFIG(TASTE_ID) ON DELETE CASCADE
            )
        """)
        
        cur.execute("""
            CREATE INDEX IDX_TASTE_REC_PROD_TASTE ON TASTE_RECOMMENDED_PRODUCTS(TASTE_ID)
        """)
        
        cur.execute("""
            CREATE INDEX IDX_TASTE_REC_PROD_TASTE_CAT 
            ON TASTE_RECOMMENDED_PRODUCTS(TASTE_ID, CATEGORY_NAME)
        """)

    def _get_category_score_columns(self, cur):
        """TASTE_CONFIG 테이블의 모든 _SCORE 컬럼을 동적으로 감지"""
        cur.execute("""
            SELECT COLUMN_NAME 
            FROM USER_TAB_COLUMNS 
            WHERE TABLE_NAME = 'TASTE_CONFIG' 
            AND COLUMN_NAME LIKE '%_SCORE'
            ORDER BY COLUMN_NAME
        """)
        return [row[0] for row in cur.fetchall()]

    def _migrate_taste_config(self, taste_id: int, dry_run: bool) -> bool:
        """특정 taste_id의 데이터를 정규화된 테이블로 마이그레이션"""
        try:
            with get_connection() as conn:
                with conn.cursor() as cur:
                    # 1. 동적으로 _SCORE 컬럼 목록 가져오기
                    score_columns = self._get_category_score_columns(cur)
                    
                    # 2. SELECT 쿼리 동적 생성
                    base_columns = [
                        'TASTE_ID',
                        'RECOMMENDED_CATEGORIES',
                        'CATEGORY_SCORES',
                        'RECOMMENDED_PRODUCTS',
                        'RECOMMENDED_PRODUCT_SCORES',
                        'ILL_SUITED_CATEGORIES'
                    ]
                    
                    # 컬럼명에 따옴표 추가 (한글/특수문자 포함)
                    quoted_score_columns = []
                    for col in score_columns:
                        if any(ord(c) > 127 for c in col) or col[0].isdigit():
                            quoted_score_columns.append(f'"{col}"')
                        else:
                            quoted_score_columns.append(col)
                    
                    select_columns = base_columns + quoted_score_columns
                    select_sql = f"""
                        SELECT {', '.join(select_columns)}
                        FROM TASTE_CONFIG
                        WHERE TASTE_ID = :p_taste_id
                    """
                    
                    cur.execute(select_sql, {'p_taste_id': taste_id})
                    row = cur.fetchone()
                    
                    if not row:
                        return False
                    
                    # 3. JSON 컬럼 파싱
                    recommended_categories = self._parse_json_clob(row[1])
                    category_scores_json = self._parse_json_clob(row[2])
                    recommended_products_json = self._parse_json_clob(row[3])
                    recommended_product_scores_json = self._parse_json_clob(row[4])
                    ill_suited_categories = self._parse_json_clob(row[5])
                    
                    # 4. 카테고리별 점수 컬럼 매핑 생성
                    category_column_mapping = {}
                    for idx, col_name in enumerate(score_columns, start=6):
                        # 컬럼명에서 카테고리명 추출 (예: "TV_SCORE" -> "TV", "냉장고_SCORE" -> "냉장고")
                        category = col_name.replace('_SCORE', '').replace('"', '')
                        category_column_mapping[category] = idx
                    
                    # 5. 카테고리별 점수 마이그레이션
                    if not dry_run:
                        self._migrate_category_scores(
                            cur, taste_id, row, recommended_categories, 
                            category_scores_json, ill_suited_categories,
                            category_column_mapping
                        )
                    
                    # 6. 추천 제품 마이그레이션
                    if not dry_run:
                        self._migrate_recommended_products(
                            cur, taste_id, recommended_products_json,
                            recommended_product_scores_json
                        )
                    
                    if not dry_run:
                        conn.commit()
                    
                    return True
                    
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Taste {taste_id} 마이그레이션 오류: {str(e)}')
            )
            return False

    def _parse_json_clob(self, clob_value):
        """CLOB 값을 JSON으로 파싱"""
        if not clob_value:
            return None
        
        try:
            if hasattr(clob_value, 'read'):
                clob_value = clob_value.read()
            
            if isinstance(clob_value, str):
                return json.loads(clob_value)
            return clob_value
        except (json.JSONDecodeError, AttributeError):
            return None

    def _migrate_category_scores(self, cur, taste_id, row, recommended_categories, 
                                 category_scores_json, ill_suited_categories,
                                 category_column_mapping):
        """카테고리별 점수를 TASTE_CATEGORY_SCORES 테이블로 마이그레이션"""
        # 기존 데이터 삭제
        cur.execute("""
            DELETE FROM TASTE_CATEGORY_SCORES WHERE TASTE_ID = :p_taste_id
        """, {'p_taste_id': taste_id})
        
        # 모든 카테고리 수집 (컬럼 + JSON)
        all_categories = set(category_column_mapping.keys())
        if category_scores_json and isinstance(category_scores_json, dict):
            all_categories.update(category_scores_json.keys())
        
        # 카테고리별 점수 삽입
        for category in all_categories:
            score = None
            
            # 1. JSON에서 점수 확인 (최우선)
            if category_scores_json and isinstance(category_scores_json, dict):
                if category in category_scores_json:
                    score = category_scores_json[category]
            
            # 2. 개별 컬럼에서 점수 확인
            if score is None and category in category_column_mapping:
                col_idx = category_column_mapping[category]
                if col_idx < len(row) and row[col_idx] is not None:
                    score = row[col_idx]
            
            # 점수가 없으면 건너뛰기
            if score is None:
                continue
            
            is_recommended = 'Y' if (recommended_categories and category in recommended_categories) else 'N'
            is_ill_suited = 'Y' if (ill_suited_categories and category in ill_suited_categories) else 'N'
            
            try:
                cur.execute("""
                    INSERT INTO TASTE_CATEGORY_SCORES 
                    (TASTE_ID, CATEGORY_NAME, SCORE, IS_RECOMMENDED, IS_ILL_SUITED)
                    VALUES (:p_taste_id, :p_category, :p_score, :p_recommended, :p_ill_suited)
                """, {
                    'p_taste_id': taste_id,
                    'p_category': category,
                    'p_score': float(score),
                    'p_recommended': is_recommended,
                    'p_ill_suited': is_ill_suited
                })
            except Exception as e:
                self.stdout.write(
                    self.style.WARNING(f'  카테고리 {category} 삽입 실패: {str(e)}')
                )

    def _migrate_recommended_products(self, cur, taste_id, recommended_products_json,
                                     recommended_product_scores_json):
        """추천 제품을 TASTE_RECOMMENDED_PRODUCTS 테이블로 마이그레이션"""
        if not recommended_products_json or not isinstance(recommended_products_json, dict):
            return
        
        # 기존 데이터 삭제
        cur.execute("""
            DELETE FROM TASTE_RECOMMENDED_PRODUCTS WHERE TASTE_ID = :p_taste_id
        """, {'p_taste_id': taste_id})
        
        # 카테고리별 추천 제품 삽입
        for category, product_ids in recommended_products_json.items():
            if not isinstance(product_ids, list):
                continue
            
            scores = []
            if (recommended_product_scores_json and 
                isinstance(recommended_product_scores_json, dict) and
                category in recommended_product_scores_json):
                scores = recommended_product_scores_json[category]
            
            for rank, product_id in enumerate(product_ids, start=1):
                score = scores[rank - 1] if rank <= len(scores) else None
                
                cur.execute("""
                    INSERT INTO TASTE_RECOMMENDED_PRODUCTS
                    (TASTE_ID, CATEGORY_NAME, PRODUCT_ID, SCORE, RANK_ORDER)
                    VALUES (:p_taste_id, :p_category, :p_product_id, :p_score, :p_rank)
                """, {
                    'p_taste_id': taste_id,
                    'p_category': category,
                    'p_product_id': int(product_id),
                    'p_score': float(score) if score is not None else None,
                    'p_rank': rank
                })


