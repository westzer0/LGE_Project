"""
모든 테이블 정규화 마이그레이션 명령어

ONBOARDING_SESSION, PRODUCT_DEMOGRAPHICS, USER_SAMPLE 테이블을
정규화된 구조로 마이그레이션합니다.

사용법:
    python manage.py migrate_all_to_normalized
    python manage.py migrate_all_to_normalized --dry-run  # 테스트만 실행
    python manage.py migrate_all_to_normalized --table onboarding  # 특정 테이블만
"""
import json
from django.core.management.base import BaseCommand
from api.db.oracle_client import get_connection
from api.models import ProductDemographics, UserSample


class Command(BaseCommand):
    help = '모든 테이블을 정규화된 구조로 마이그레이션'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='실제 마이그레이션 없이 테스트만 실행',
        )
        parser.add_argument(
            '--table',
            type=str,
            choices=['onboarding', 'demographics', 'user_sample', 'all'],
            default='all',
            help='마이그레이션할 테이블 선택',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        table = options['table']
        
        if dry_run:
            self.stdout.write(self.style.WARNING('=== DRY RUN 모드 (실제 변경 없음) ===\n'))
        
        self.stdout.write(self.style.SUCCESS(f'\n=== 전체 테이블 정규화 마이그레이션 ===\n'))
        
        # 1. 테이블 생성
        if not dry_run:
            self._ensure_normalized_tables(table)
        
        # 2. 데이터 마이그레이션
        if table in ['onboarding', 'all']:
            self._migrate_onboarding_session(dry_run)
        
        if table in ['demographics', 'all']:
            self._migrate_product_demographics(dry_run)
        
        if table in ['user_sample', 'all']:
            self._migrate_user_sample(dry_run)
        
        self.stdout.write(self.style.SUCCESS('\n=== 마이그레이션 완료 ==='))

    def _ensure_normalized_tables(self, table):
        """정규화된 테이블이 존재하는지 확인하고 없으면 생성"""
        try:
            with get_connection() as conn:
                with conn.cursor() as cur:
                    if table in ['onboarding', 'all']:
                        self._create_onboarding_tables(cur)
                    
                    if table in ['demographics', 'all']:
                        self._create_demographics_tables(cur)
                    
                    if table in ['user_sample', 'all']:
                        self._create_user_sample_tables(cur)
                    
                    conn.commit()
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'테이블 생성 실패: {str(e)}')
            )
            raise

    def _create_onboarding_tables(self, cur):
        """ONBOARDING_SESSION 정규화 테이블 생성"""
        # Oracle 11g 30자 제한으로 테이블 이름 단축
        tables = [
            'ONBOARD_SESS_MAIN_SPACES',      # 23자
            'ONBOARD_SESS_PRIORITIES',       # 22자
            'ONBOARD_SESS_CATEGORIES',       # 22자
            'ONBOARD_SESS_REC_PRODUCTS'      # 23자
        ]
        
        for table_name in tables:
            cur.execute(f"""
                SELECT COUNT(*) 
                FROM USER_TABLES 
                WHERE TABLE_NAME = '{table_name}'
            """)
            if cur.fetchone()[0] == 0:
                self.stdout.write(f'{table_name} 테이블 생성 중...')
                self._create_onboarding_table(cur, table_name)

    def _get_session_id_type(self, cur):
        """ONBOARDING_SESSION의 SESSION_ID 타입 확인"""
        try:
            cur.execute("""
                SELECT DATA_TYPE, DATA_LENGTH, DATA_PRECISION, DATA_SCALE
                FROM USER_TAB_COLUMNS 
                WHERE TABLE_NAME = 'ONBOARDING_SESSION' 
                AND COLUMN_NAME = 'SESSION_ID'
            """)
            result = cur.fetchone()
            if result:
                data_type, data_length, data_precision, data_scale = result
                if data_type == 'NUMBER':
                    if data_scale and data_scale > 0:
                        return f"NUMBER({data_precision},{data_scale})"
                    elif data_precision:
                        return f"NUMBER({data_precision})"
                    return "NUMBER"
                elif data_type == 'VARCHAR2':
                    return f"VARCHAR2({data_length})"
                return f"{data_type}({data_length})"
        except Exception as e:
            self.stdout.write(self.style.WARNING(f'  타입 확인 오류: {str(e)}'))
        return "NUMBER(22)"  # 기본값을 NUMBER로 변경

    def _create_onboarding_table(self, cur, table_name):
        """ONBOARDING_SESSION 정규화 테이블 생성"""
        session_id_type = self._get_session_id_type(cur)
        
        if table_name == 'ONBOARD_SESS_MAIN_SPACES':
            # 외래키 없이 먼저 생성 (타입 호환성 문제 해결)
            cur.execute(f"""
                CREATE TABLE ONBOARD_SESS_MAIN_SPACES (
                    SESSION_ID {session_id_type} NOT NULL,
                    MAIN_SPACE VARCHAR2(50) NOT NULL,
                    CREATED_AT DATE DEFAULT SYSDATE,
                    PRIMARY KEY (SESSION_ID, MAIN_SPACE)
                )
            """)
            # 외래키는 나중에 추가
            try:
                cur.execute(f"""
                    ALTER TABLE ONBOARD_SESS_MAIN_SPACES
                    ADD CONSTRAINT FK_SESS_MAIN_SPACES
                    FOREIGN KEY (SESSION_ID) REFERENCES ONBOARDING_SESSION(SESSION_ID) ON DELETE CASCADE
                """)
            except:
                pass  # 외래키 추가 실패해도 계속 진행
            cur.execute("CREATE INDEX IDX_SESS_MAIN_SP ON ONBOARD_SESS_MAIN_SPACES(SESSION_ID)")
        
        elif table_name == 'ONBOARD_SESS_PRIORITIES':
            cur.execute(f"""
                CREATE TABLE ONBOARD_SESS_PRIORITIES (
                    SESSION_ID {session_id_type} NOT NULL,
                    PRIORITY VARCHAR2(20) NOT NULL,
                    PRIORITY_ORDER NUMBER NOT NULL,
                    CREATED_AT DATE DEFAULT SYSDATE,
                    PRIMARY KEY (SESSION_ID, PRIORITY_ORDER)
                )
            """)
            try:
                cur.execute(f"""
                    ALTER TABLE ONBOARD_SESS_PRIORITIES
                    ADD CONSTRAINT FK_SESS_PRIORITIES
                    FOREIGN KEY (SESSION_ID) REFERENCES ONBOARDING_SESSION(SESSION_ID) ON DELETE CASCADE
                """)
            except:
                pass
            cur.execute("CREATE INDEX IDX_SESS_PRIOR ON ONBOARD_SESS_PRIORITIES(SESSION_ID)")
        
        elif table_name == 'ONBOARD_SESS_CATEGORIES':
            cur.execute(f"""
                CREATE TABLE ONBOARD_SESS_CATEGORIES (
                    SESSION_ID {session_id_type} NOT NULL,
                    CATEGORY_NAME VARCHAR2(50) NOT NULL,
                    CREATED_AT DATE DEFAULT SYSDATE,
                    PRIMARY KEY (SESSION_ID, CATEGORY_NAME)
                )
            """)
            try:
                cur.execute(f"""
                    ALTER TABLE ONBOARD_SESS_CATEGORIES
                    ADD CONSTRAINT FK_SESS_CATEGORIES
                    FOREIGN KEY (SESSION_ID) REFERENCES ONBOARDING_SESSION(SESSION_ID) ON DELETE CASCADE
                """)
            except:
                pass
            cur.execute("CREATE INDEX IDX_SESS_CAT ON ONBOARD_SESS_CATEGORIES(SESSION_ID)")
        
        elif table_name == 'ONBOARD_SESS_REC_PRODUCTS':
            cur.execute(f"""
                CREATE TABLE ONBOARD_SESS_REC_PRODUCTS (
                    SESSION_ID {session_id_type} NOT NULL,
                    PRODUCT_ID NUMBER NOT NULL,
                    CATEGORY_NAME VARCHAR2(50),
                    RANK_ORDER NUMBER,
                    SCORE NUMBER(5,2),
                    CREATED_AT DATE DEFAULT SYSDATE,
                    PRIMARY KEY (SESSION_ID, PRODUCT_ID)
                )
            """)
            try:
                cur.execute(f"""
                    ALTER TABLE ONBOARD_SESS_REC_PRODUCTS
                    ADD CONSTRAINT FK_SESS_REC_PROD
                    FOREIGN KEY (SESSION_ID) REFERENCES ONBOARDING_SESSION(SESSION_ID) ON DELETE CASCADE
                """)
            except:
                pass
            cur.execute("CREATE INDEX IDX_SESS_REC_PROD ON ONBOARD_SESS_REC_PRODUCTS(SESSION_ID)")

    def _create_demographics_tables(self, cur):
        """PRODUCT_DEMOGRAPHICS 정규화 테이블 생성"""
        # Oracle 11g 30자 제한으로 테이블 이름 단축
        tables = [
            'PROD_DEMO_FAMILY_TYPES',      # 23자
            'PROD_DEMO_HOUSE_SIZES',       # 22자
            'PROD_DEMO_HOUSE_TYPES'         # 22자
        ]
        
        for table_name in tables:
            cur.execute(f"""
                SELECT COUNT(*) 
                FROM USER_TABLES 
                WHERE TABLE_NAME = '{table_name}'
            """)
            if cur.fetchone()[0] == 0:
                self.stdout.write(f'{table_name} 테이블 생성 중...')
                self._create_demographics_table(cur, table_name)

    def _create_demographics_table(self, cur, table_name):
        """PRODUCT_DEMOGRAPHICS 정규화 테이블 생성"""
        if table_name == 'PROD_DEMO_FAMILY_TYPES':
            cur.execute("""
                CREATE TABLE PROD_DEMO_FAMILY_TYPES (
                    PRODUCT_ID NUMBER NOT NULL,
                    FAMILY_TYPE VARCHAR2(50) NOT NULL,
                    CREATED_AT DATE DEFAULT SYSDATE,
                    PRIMARY KEY (PRODUCT_ID, FAMILY_TYPE),
                    FOREIGN KEY (PRODUCT_ID) REFERENCES PRODUCT(PRODUCT_ID) ON DELETE CASCADE
                )
            """)
            cur.execute("CREATE INDEX IDX_PROD_DEMO_FAM ON PROD_DEMO_FAMILY_TYPES(PRODUCT_ID)")
        
        elif table_name == 'PROD_DEMO_HOUSE_SIZES':
            cur.execute("""
                CREATE TABLE PROD_DEMO_HOUSE_SIZES (
                    PRODUCT_ID NUMBER NOT NULL,
                    HOUSE_SIZE VARCHAR2(50) NOT NULL,
                    CREATED_AT DATE DEFAULT SYSDATE,
                    PRIMARY KEY (PRODUCT_ID, HOUSE_SIZE),
                    FOREIGN KEY (PRODUCT_ID) REFERENCES PRODUCT(PRODUCT_ID) ON DELETE CASCADE
                )
            """)
            cur.execute("CREATE INDEX IDX_PROD_DEMO_SIZE ON PROD_DEMO_HOUSE_SIZES(PRODUCT_ID)")
        
        elif table_name == 'PROD_DEMO_HOUSE_TYPES':
            cur.execute("""
                CREATE TABLE PROD_DEMO_HOUSE_TYPES (
                    PRODUCT_ID NUMBER NOT NULL,
                    HOUSE_TYPE VARCHAR2(50) NOT NULL,
                    CREATED_AT DATE DEFAULT SYSDATE,
                    PRIMARY KEY (PRODUCT_ID, HOUSE_TYPE),
                    FOREIGN KEY (PRODUCT_ID) REFERENCES PRODUCT(PRODUCT_ID) ON DELETE CASCADE
                )
            """)
            cur.execute("CREATE INDEX IDX_PROD_DEMO_TYPE ON PROD_DEMO_HOUSE_TYPES(PRODUCT_ID)")

    def _create_user_sample_tables(self, cur):
        """USER_SAMPLE 정규화 테이블 생성"""
        tables = [
            'USER_SAMPLE_RECOMMENDATIONS',
            'USER_SAMPLE_PURCHASED_ITEMS'
        ]
        
        for table_name in tables:
            cur.execute(f"""
                SELECT COUNT(*) 
                FROM USER_TABLES 
                WHERE TABLE_NAME = '{table_name}'
            """)
            if cur.fetchone()[0] == 0:
                self.stdout.write(f'{table_name} 테이블 생성 중...')
                self._create_user_sample_table(cur, table_name)

    def _create_user_sample_table(self, cur, table_name):
        """USER_SAMPLE 정규화 테이블 생성"""
        # USER_SAMPLE 테이블 존재 여부 확인
        cur.execute("""
            SELECT COUNT(*) 
            FROM USER_TABLES 
            WHERE TABLE_NAME = 'USER_SAMPLE'
        """)
        user_sample_exists = cur.fetchone()[0] > 0
        
        if table_name == 'USER_SAMPLE_RECOMMENDATIONS':
            if user_sample_exists:
                cur.execute("""
                    CREATE TABLE USER_SAMPLE_RECOMMENDATIONS (
                        USER_ID VARCHAR2(50) NOT NULL,
                        CATEGORY_NAME VARCHAR2(50) NOT NULL,
                        RECOMMENDED_VALUE VARCHAR2(100),
                        RECOMMENDED_UNIT VARCHAR2(20),
                        CREATED_AT DATE DEFAULT SYSDATE,
                        PRIMARY KEY (USER_ID, CATEGORY_NAME),
                        FOREIGN KEY (USER_ID) REFERENCES USER_SAMPLE(USER_ID) ON DELETE CASCADE
                    )
                """)
            else:
                # 외래키 없이 생성 (Django ORM 전용 테이블일 수 있음)
                cur.execute("""
                    CREATE TABLE USER_SAMPLE_RECOMMENDATIONS (
                        USER_ID VARCHAR2(50) NOT NULL,
                        CATEGORY_NAME VARCHAR2(50) NOT NULL,
                        RECOMMENDED_VALUE VARCHAR2(100),
                        RECOMMENDED_UNIT VARCHAR2(20),
                        CREATED_AT DATE DEFAULT SYSDATE,
                        PRIMARY KEY (USER_ID, CATEGORY_NAME)
                    )
                """)
            cur.execute("CREATE INDEX IDX_USR_SMP_REC ON USER_SAMPLE_RECOMMENDATIONS(USER_ID)")
        
        elif table_name == 'USER_SAMPLE_PURCHASED_ITEMS':
            if user_sample_exists:
                cur.execute("""
                    CREATE TABLE USER_SAMPLE_PURCHASED_ITEMS (
                        USER_ID VARCHAR2(50) NOT NULL,
                        PRODUCT_ID NUMBER NOT NULL,
                        PURCHASED_AT DATE,
                        CREATED_AT DATE DEFAULT SYSDATE,
                        PRIMARY KEY (USER_ID, PRODUCT_ID),
                        FOREIGN KEY (USER_ID) REFERENCES USER_SAMPLE(USER_ID) ON DELETE CASCADE
                    )
                """)
            else:
                # 외래키 없이 생성
                cur.execute("""
                    CREATE TABLE USER_SAMPLE_PURCHASED_ITEMS (
                        USER_ID VARCHAR2(50) NOT NULL,
                        PRODUCT_ID NUMBER NOT NULL,
                        PURCHASED_AT DATE,
                        CREATED_AT DATE DEFAULT SYSDATE,
                        PRIMARY KEY (USER_ID, PRODUCT_ID)
                    )
                """)
            cur.execute("CREATE INDEX IDX_USR_SMP_PURCH ON USER_SAMPLE_PURCHASED_ITEMS(USER_ID)")

    def _migrate_onboarding_session(self, dry_run):
        """ONBOARDING_SESSION 데이터 마이그레이션 (Oracle DB 직접 접근)"""
        self.stdout.write('\n[ONBOARDING_SESSION] 마이그레이션 시작...')
        
        try:
            with get_connection() as conn:
                with conn.cursor() as cur:
                    # 모든 세션 조회 (MEMBER_ID 오름차순 정렬)
                    cur.execute("""
                        SELECT 
                            SESSION_ID,
                            MAIN_SPACE,
                            PRIORITY_LIST,
                            SELECTED_CATEGORIES,
                            RECOMMENDED_PRODUCTS
                        FROM ONBOARDING_SESSION
                        ORDER BY MEMBER_ID ASC
                    """)
                    
                    rows = cur.fetchall()
                    count = 0
                    
                    for row in rows:
                        session_id = row[0]
                        main_space_clob = row[1]
                        priority_list_clob = row[2]
                        selected_categories_clob = row[3]
                        recommended_products_clob = row[4]
                        
                        if not dry_run:
                            # MAIN_SPACE 마이그레이션
                            if main_space_clob:
                                main_spaces = self._parse_json_clob(main_space_clob)
                                if main_spaces and isinstance(main_spaces, list):
                                    for space in main_spaces:
                                        cur.execute("""
                                            INSERT INTO ONBOARD_SESS_MAIN_SPACES 
                                            (SESSION_ID, MAIN_SPACE)
                                            VALUES (:p_session_id, :p_space)
                                        """, {
                                            'p_session_id': session_id,
                                            'p_space': str(space)
                                        })
                            
                            # PRIORITY_LIST 마이그레이션
                            if priority_list_clob:
                                priorities = self._parse_json_clob(priority_list_clob)
                                if priorities and isinstance(priorities, list):
                                    for idx, priority in enumerate(priorities, start=1):
                                        cur.execute("""
                                            INSERT INTO ONBOARD_SESS_PRIORITIES 
                                            (SESSION_ID, PRIORITY, PRIORITY_ORDER)
                                            VALUES (:p_session_id, :p_priority, :p_order)
                                        """, {
                                            'p_session_id': session_id,
                                            'p_priority': str(priority),
                                            'p_order': idx
                                        })
                            
                            # SELECTED_CATEGORIES 마이그레이션
                            if selected_categories_clob:
                                categories = self._parse_json_clob(selected_categories_clob)
                                if categories and isinstance(categories, list):
                                    for category in categories:
                                        cur.execute("""
                                            INSERT INTO ONBOARD_SESS_CATEGORIES 
                                            (SESSION_ID, CATEGORY_NAME)
                                            VALUES (:p_session_id, :p_category)
                                        """, {
                                            'p_session_id': session_id,
                                            'p_category': str(category)
                                        })
                            
                            # RECOMMENDED_PRODUCTS 마이그레이션
                            if recommended_products_clob:
                                products = self._parse_json_clob(recommended_products_clob)
                                if products and isinstance(products, list):
                                    for idx, product_id in enumerate(products, start=1):
                                        cur.execute("""
                                            INSERT INTO ONBOARD_SESS_REC_PRODUCTS 
                                            (SESSION_ID, PRODUCT_ID, RANK_ORDER)
                                            VALUES (:p_session_id, :p_product_id, :p_rank)
                                        """, {
                                            'p_session_id': session_id,
                                            'p_product_id': int(product_id),
                                            'p_rank': idx
                                        })
                        
                        count += 1
                        if count % 10 == 0:
                            self.stdout.write(f'  진행: {count}/{len(rows)}...')
                    
                    if not dry_run:
                        conn.commit()
            
            self.stdout.write(self.style.SUCCESS(f'  완료: {count}개 세션'))
        
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'  오류: {str(e)}')
            )

    def _migrate_product_demographics(self, dry_run):
        """PRODUCT_DEMOGRAPHICS 데이터 마이그레이션 (Django ORM 사용)"""
        self.stdout.write('\n[PRODUCT_DEMOGRAPHICS] 마이그레이션 시작...')
        
        try:
            demographics = ProductDemographics.objects.all()
            count = 0
            
            for demo in demographics:
                if not dry_run:
                    # PRODUCT_ID가 Oracle DB에 존재하는지 확인
                    with get_connection() as conn:
                        with conn.cursor() as cur:
                            cur.execute("""
                                SELECT COUNT(*) FROM PRODUCT WHERE PRODUCT_ID = :p_product_id
                            """, {'p_product_id': demo.product_id})
                            product_exists = cur.fetchone()[0] > 0
                            
                            if not product_exists:
                                continue  # Oracle DB에 없는 제품은 건너뛰기
                            
                            # FAMILY_TYPES 마이그레이션
                            if demo.family_types:
                                family_types = demo.family_types if isinstance(demo.family_types, list) else json.loads(demo.family_types) if isinstance(demo.family_types, str) else []
                                for family_type in family_types:
                                    try:
                                        cur.execute("""
                                            INSERT INTO PROD_DEMO_FAMILY_TYPES 
                                            (PRODUCT_ID, FAMILY_TYPE)
                                            VALUES (:p_product_id, :p_family_type)
                                        """, {
                                            'p_product_id': demo.product_id,
                                            'p_family_type': str(family_type)
                                        })
                                    except:
                                        pass  # 중복 등 오류 무시
                            
                            # HOUSE_SIZES 마이그레이션
                            if demo.house_sizes:
                                house_sizes = demo.house_sizes if isinstance(demo.house_sizes, list) else json.loads(demo.house_sizes) if isinstance(demo.house_sizes, str) else []
                                for house_size in house_sizes:
                                    try:
                                        cur.execute("""
                                            INSERT INTO PROD_DEMO_HOUSE_SIZES 
                                            (PRODUCT_ID, HOUSE_SIZE)
                                            VALUES (:p_product_id, :p_house_size)
                                        """, {
                                            'p_product_id': demo.product_id,
                                            'p_house_size': str(house_size)
                                        })
                                    except:
                                        pass
                            
                            # HOUSE_TYPES 마이그레이션
                            if demo.house_types:
                                house_types = demo.house_types if isinstance(demo.house_types, list) else json.loads(demo.house_types) if isinstance(demo.house_types, str) else []
                                for house_type in house_types:
                                    try:
                                        cur.execute("""
                                            INSERT INTO PROD_DEMO_HOUSE_TYPES 
                                            (PRODUCT_ID, HOUSE_TYPE)
                                            VALUES (:p_product_id, :p_house_type)
                                        """, {
                                            'p_product_id': demo.product_id,
                                            'p_house_type': str(house_type)
                                        })
                                    except:
                                        pass
                            
                            conn.commit()
                
                count += 1
                if count % 10 == 0:
                    self.stdout.write(f'  진행: {count}/{demographics.count()}...')
            
            self.stdout.write(self.style.SUCCESS(f'  완료: {count}개 제품'))
        
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'  오류: {str(e)}')
            )

    def _migrate_user_sample(self, dry_run):
        """USER_SAMPLE 데이터 마이그레이션 (Django ORM 사용)"""
        self.stdout.write('\n[USER_SAMPLE] 마이그레이션 시작...')
        
        try:
            users = UserSample.objects.all()
            count = 0
            
            for user in users:
                if not dry_run:
                    # 추천 제품 정보 마이그레이션
                    category_mapping = {
                        '냉장고': ('recommended_fridge_l', 'L'),
                        '세탁기': ('recommended_washer_kg', 'KG'),
                        'TV': ('recommended_tv_inch', 'INCH'),
                        '청소기': ('recommended_vacuum', None),
                        '오븐': ('recommended_oven', None),
                    }
                    
                    for category, (field_name, unit) in category_mapping.items():
                        value = getattr(user, field_name, None)
                        if value:
                            with get_connection() as conn:
                                with conn.cursor() as cur:
                                    cur.execute("""
                                        INSERT INTO USER_SAMPLE_RECOMMENDATIONS 
                                        (USER_ID, CATEGORY_NAME, RECOMMENDED_VALUE, RECOMMENDED_UNIT)
                                        VALUES (:p_user_id, :p_category, :p_value, :p_unit)
                                    """, {
                                        'p_user_id': user.user_id,
                                        'p_category': category,
                                        'p_value': str(value),
                                        'p_unit': unit
                                    })
                                    conn.commit()
                    
                    # PURCHASED_ITEMS 마이그레이션
                    if user.purchased_items:
                        try:
                            items = json.loads(user.purchased_items) if isinstance(user.purchased_items, str) else user.purchased_items
                            if isinstance(items, list):
                                for product_id in items:
                                    with get_connection() as conn:
                                        with conn.cursor() as cur:
                                            cur.execute("""
                                                INSERT INTO USER_SAMPLE_PURCHASED_ITEMS 
                                                (USER_ID, PRODUCT_ID)
                                                VALUES (:p_user_id, :p_product_id)
                                            """, {
                                                'p_user_id': user.user_id,
                                                'p_product_id': int(product_id)
                                            })
                                            conn.commit()
                        except:
                            pass
                
                count += 1
                if count % 10 == 0:
                    self.stdout.write(f'  진행: {count}/{users.count()}...')
            
            self.stdout.write(self.style.SUCCESS(f'  완료: {count}개 사용자'))
        
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'  오류: {str(e)}')
            )
    
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

