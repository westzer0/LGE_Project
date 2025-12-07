"""
정규화 마이그레이션 상태 확인 및 시각화

마이그레이션 진행 상태를 확인하고 시각화합니다.

사용법:
    python manage.py check_normalization_status
    python manage.py check_normalization_status --detailed  # 상세 정보
"""
from django.core.management.base import BaseCommand
from api.db.oracle_client import get_connection
from api.models import OnboardingSession, ProductDemographics, UserSample


class Command(BaseCommand):
    help = '정규화 마이그레이션 상태 확인 및 시각화'

    def add_arguments(self, parser):
        parser.add_argument(
            '--detailed',
            action='store_true',
            help='상세 정보 출력',
        )
        parser.add_argument(
            '--html',
            type=str,
            help='HTML 리포트 파일 경로 (예: --html report.html)',
        )

    def handle(self, *args, **options):
        detailed = options['detailed']
        html_path = options.get('html')
        
        self.stdout.write(self.style.SUCCESS('\n' + '='*80))
        self.stdout.write(self.style.SUCCESS('정규화 마이그레이션 상태 확인'))
        self.stdout.write(self.style.SUCCESS('='*80 + '\n'))
        
        # 상태 데이터 수집
        status_data = {}
        
        # 1. TASTE_CONFIG 정규화 상태
        status_data['taste_config'] = self._check_taste_config_status(detailed, return_data=True)
        
        # 2. ONBOARDING_SESSION 정규화 상태
        status_data['onboarding_session'] = self._check_onboarding_session_status(detailed, return_data=True)
        
        # 3. PRODUCT_DEMOGRAPHICS 정규화 상태
        status_data['product_demographics'] = self._check_product_demographics_status(detailed, return_data=True)
        
        # 4. USER_SAMPLE 정규화 상태
        status_data['user_sample'] = self._check_user_sample_status(detailed, return_data=True)
        
        self.stdout.write('\n' + '='*80)
        
        # HTML 리포트 생성
        if html_path:
            self._generate_html_report(status_data, html_path)
            self.stdout.write(self.style.SUCCESS(f'\nHTML 리포트 생성 완료: {html_path}'))

    def _print_progress_bar(self, current, total, width=50):
        """프로그레스 바 출력"""
        if total == 0:
            percentage = 0
            filled = 0
        else:
            percentage = (current / total) * 100
            filled = int((current / total) * width)
        
        bar = '█' * filled + '░' * (width - filled)
        return f"[{bar}] {percentage:.1f}% ({current}/{total})"

    def _check_taste_config_status(self, detailed, return_data=False):
        """TASTE_CONFIG 정규화 상태 확인"""
        self.stdout.write(self.style.SUCCESS('\n[1] TASTE_CONFIG 정규화 상태'))
        self.stdout.write('-' * 80)
        
        data = {'status': 'error'}
        
        try:
            with get_connection() as conn:
                with conn.cursor() as cur:
                    # 기본 테이블 데이터 수
                    cur.execute("SELECT COUNT(*) FROM TASTE_CONFIG")
                    taste_config_count = cur.fetchone()[0]
                    
                    # 정규화된 테이블 데이터 수
                    cur.execute("SELECT COUNT(*) FROM TASTE_CATEGORY_SCORES")
                    category_scores_count = cur.fetchone()[0]
                    
                    cur.execute("SELECT COUNT(*) FROM TASTE_RECOMMENDED_PRODUCTS")
                    recommended_products_count = cur.fetchone()[0]
                    
                    # 예상 데이터 수 (120개 taste × 평균 카테고리 수)
                    expected_category_scores = taste_config_count * 15  # 평균 15개 카테고리 가정
                    
                    # 진행률 계산
                    if expected_category_scores > 0:
                        progress = min(100, (category_scores_count / expected_category_scores) * 100)
                    else:
                        progress = 100 if category_scores_count > 0 else 0
                    
                    data = {
                        'status': 'success',
                        'base_count': taste_config_count,
                        'category_scores_count': category_scores_count,
                        'recommended_products_count': recommended_products_count,
                        'expected_count': expected_category_scores,
                        'progress': progress
                    }
                    
                    self.stdout.write(f'  기본 테이블 (TASTE_CONFIG): {taste_config_count}개 레코드')
                    self.stdout.write(f'  정규화 테이블 (TASTE_CATEGORY_SCORES): {category_scores_count}개 레코드')
                    self.stdout.write(f'  정규화 테이블 (TASTE_RECOMMENDED_PRODUCTS): {recommended_products_count}개 레코드')
                    self.stdout.write('')
                    self.stdout.write(f'  진행률: {self._print_progress_bar(category_scores_count, expected_category_scores)}')
                    
                    if detailed:
                        # Taste별 상세 정보
                        cur.execute("""
                            SELECT TASTE_ID, COUNT(*) as CNT
                            FROM TASTE_CATEGORY_SCORES
                            GROUP BY TASTE_ID
                            ORDER BY TASTE_ID
                        """)
                        taste_counts = cur.fetchall()
                        data['taste_counts'] = taste_counts
                        self.stdout.write(f'\n  Taste별 카테고리 점수 개수:')
                        for taste_id, cnt in taste_counts[:10]:  # 처음 10개만
                            self.stdout.write(f'    Taste {taste_id}: {cnt}개')
                        if len(taste_counts) > 10:
                            self.stdout.write(f'    ... 외 {len(taste_counts) - 10}개')
        
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'  오류: {str(e)}'))
            data['error'] = str(e)
        
        return data if return_data else None

    def _table_exists(self, cur, table_name):
        """테이블 존재 여부 확인"""
        try:
            cur.execute(f"""
                SELECT COUNT(*) 
                FROM USER_TABLES 
                WHERE TABLE_NAME = '{table_name}'
            """)
            return cur.fetchone()[0] > 0
        except:
            return False

    def _check_onboarding_session_status(self, detailed, return_data=False):
        """ONBOARDING_SESSION 정규화 상태 확인"""
        self.stdout.write(self.style.SUCCESS('\n[2] ONBOARDING_SESSION 정규화 상태'))
        self.stdout.write('-' * 80)
        
        data = {'status': 'error'}
        
        try:
            # Django ORM으로 기본 데이터 수 확인
            total_sessions = OnboardingSession.objects.count()
            
            with get_connection() as conn:
                with conn.cursor() as cur:
                    # 테이블 존재 여부 확인 (짧은 이름 사용)
                    if not self._table_exists(cur, 'ONBOARD_SESS_MAIN_SPACES'):
                        self.stdout.write(self.style.WARNING('  ⚠ 정규화 테이블이 아직 생성되지 않았습니다.'))
                        self.stdout.write('  마이그레이션을 실행하세요: python manage.py migrate_all_to_normalized')
                        data = {'status': 'not_created', 'base_count': total_sessions}
                        return data if return_data else None
                    
                    # 정규화된 테이블 데이터 수
                    cur.execute("SELECT COUNT(*) FROM ONBOARD_SESS_MAIN_SPACES")
                    main_spaces_count = cur.fetchone()[0]
                    
                    cur.execute("SELECT COUNT(*) FROM ONBOARD_SESS_PRIORITIES")
                    priorities_count = cur.fetchone()[0]
                    
                    cur.execute("SELECT COUNT(*) FROM ONBOARD_SESS_CATEGORIES")
                    categories_count = cur.fetchone()[0]
                    
                    cur.execute("SELECT COUNT(*) FROM ONBOARD_SESS_REC_PRODUCTS")
                    recommended_products_count = cur.fetchone()[0]
                    
                    # MAIN_SPACE가 있는 세션 수
                    cur.execute("""
                        SELECT COUNT(DISTINCT SESSION_ID) 
                        FROM ONBOARD_SESS_MAIN_SPACES
                    """)
                    sessions_with_main_space = cur.fetchone()[0]
                    
                    # PRIORITY_LIST가 있는 세션 수
                    cur.execute("""
                        SELECT COUNT(DISTINCT SESSION_ID) 
                        FROM ONBOARD_SESS_PRIORITIES
                    """)
                    sessions_with_priority = cur.fetchone()[0]
                    
                    # SELECTED_CATEGORIES가 있는 세션 수
                    cur.execute("""
                        SELECT COUNT(DISTINCT SESSION_ID) 
                        FROM ONBOARD_SESS_CATEGORIES
                    """)
                    sessions_with_category = cur.fetchone()[0]
                    
                    self.stdout.write(f'  기본 테이블 (ONBOARDING_SESSION): {total_sessions}개 세션')
                    self.stdout.write('')
                    self.stdout.write('  정규화 테이블:')
                    self.stdout.write(f'    ONBOARD_SESS_MAIN_SPACES: {main_spaces_count}개 레코드 ({sessions_with_main_space}개 세션)')
                    self.stdout.write(f'    ONBOARD_SESS_PRIORITIES: {priorities_count}개 레코드 ({sessions_with_priority}개 세션)')
                    self.stdout.write(f'    ONBOARD_SESS_CATEGORIES: {categories_count}개 레코드 ({sessions_with_category}개 세션)')
                    self.stdout.write(f'    ONBOARD_SESS_REC_PRODUCTS: {recommended_products_count}개 레코드')
                    self.stdout.write('')
                    
                    # 진행률 계산
                    if total_sessions > 0:
                        progress_main_space = (sessions_with_main_space / total_sessions) * 100
                        progress_priority = (sessions_with_priority / total_sessions) * 100
                        progress_category = (sessions_with_category / total_sessions) * 100
                        
                        self.stdout.write('  진행률:')
                        self.stdout.write(f'    MAIN_SPACE: {self._print_progress_bar(sessions_with_main_space, total_sessions)}')
                        self.stdout.write(f'    PRIORITY_LIST: {self._print_progress_bar(sessions_with_priority, total_sessions)}')
                        self.stdout.write(f'    SELECTED_CATEGORIES: {self._print_progress_bar(sessions_with_category, total_sessions)}')
                    
                    data = {
                        'status': 'success',
                        'base_count': total_sessions,
                        'main_spaces_count': main_spaces_count,
                        'priorities_count': priorities_count,
                        'categories_count': categories_count,
                        'recommended_products_count': recommended_products_count,
                        'sessions_with_main_space': sessions_with_main_space,
                        'sessions_with_priority': sessions_with_priority,
                        'sessions_with_category': sessions_with_category,
                        'progress_main_space': (sessions_with_main_space / total_sessions * 100) if total_sessions > 0 else 0,
                        'progress_priority': (sessions_with_priority / total_sessions * 100) if total_sessions > 0 else 0,
                        'progress_category': (sessions_with_category / total_sessions * 100) if total_sessions > 0 else 0,
                    }
                    
                    if detailed:
                        # 세션별 상세 정보
                        cur.execute("""
                            SELECT SESSION_ID, COUNT(*) as CNT
                            FROM ONBOARD_SESS_MAIN_SPACES
                            GROUP BY SESSION_ID
                            ORDER BY CNT DESC
                            FETCH FIRST 10 ROWS ONLY
                        """)
                        top_sessions = cur.fetchall()
                        data['top_sessions'] = top_sessions
                        if top_sessions:
                            self.stdout.write(f'\n  주요 공간이 많은 세션 (상위 10개):')
                            for session_id, cnt in top_sessions:
                                self.stdout.write(f'    {session_id[:20]}...: {cnt}개')
        
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'  오류: {str(e)}'))
            data['error'] = str(e)
        
        return data if return_data else None

    def _check_product_demographics_status(self, detailed, return_data=False):
        """PRODUCT_DEMOGRAPHICS 정규화 상태 확인"""
        self.stdout.write(self.style.SUCCESS('\n[3] PRODUCT_DEMOGRAPHICS 정규화 상태'))
        self.stdout.write('-' * 80)
        
        data = {'status': 'error'}
        
        try:
            # Django ORM으로 기본 데이터 수 확인
            total_demographics = ProductDemographics.objects.count()
            
            with get_connection() as conn:
                with conn.cursor() as cur:
                    # 테이블 존재 여부 확인 (Oracle 11g는 30자 제한)
                    table_name = 'PROD_DEMO_FAMILY_TYPES'
                    if not self._table_exists(cur, table_name):
                        self.stdout.write(self.style.WARNING('  ⚠ 정규화 테이블이 아직 생성되지 않았습니다.'))
                        self.stdout.write('  마이그레이션을 실행하세요: python manage.py migrate_all_to_normalized')
                        data = {'status': 'not_created', 'base_count': total_demographics}
                        return data if return_data else None
                    
                    # 정규화된 테이블 데이터 수
                    cur.execute(f"SELECT COUNT(*) FROM {table_name}")
                    family_types_count = cur.fetchone()[0]
                    
                    cur.execute("SELECT COUNT(*) FROM PROD_DEMO_HOUSE_SIZES")
                    house_sizes_count = cur.fetchone()[0]
                    
                    cur.execute("SELECT COUNT(*) FROM PROD_DEMO_HOUSE_TYPES")
                    house_types_count = cur.fetchone()[0]
                    
                    # 데이터가 있는 제품 수
                    cur.execute(f"""
                        SELECT COUNT(DISTINCT PRODUCT_ID) 
                        FROM {table_name}
                    """)
                    products_with_family = cur.fetchone()[0]
                    
                    cur.execute("""
                        SELECT COUNT(DISTINCT PRODUCT_ID) 
                        FROM PROD_DEMO_HOUSE_SIZES
                    """)
                    products_with_size = cur.fetchone()[0]
                    
                    cur.execute("""
                        SELECT COUNT(DISTINCT PRODUCT_ID) 
                        FROM PROD_DEMO_HOUSE_TYPES
                    """)
                    products_with_type = cur.fetchone()[0]
                    
                    self.stdout.write(f'  기본 테이블 (PRODUCT_DEMOGRAPHICS): {total_demographics}개 제품')
                    self.stdout.write('')
                    self.stdout.write('  정규화 테이블:')
                    self.stdout.write(f'    PROD_DEMO_FAMILY_TYPES: {family_types_count}개 레코드 ({products_with_family}개 제품)')
                    self.stdout.write(f'    PROD_DEMO_HOUSE_SIZES: {house_sizes_count}개 레코드 ({products_with_size}개 제품)')
                    self.stdout.write(f'    PROD_DEMO_HOUSE_TYPES: {house_types_count}개 레코드 ({products_with_type}개 제품)')
                    self.stdout.write('')
                    
                    # 진행률 계산
                    if total_demographics > 0:
                        self.stdout.write('  진행률:')
                        self.stdout.write(f'    FAMILY_TYPES: {self._print_progress_bar(products_with_family, total_demographics)}')
                        self.stdout.write(f'    HOUSE_SIZES: {self._print_progress_bar(products_with_size, total_demographics)}')
                        self.stdout.write(f'    HOUSE_TYPES: {self._print_progress_bar(products_with_type, total_demographics)}')
                    
                    data = {
                        'status': 'success',
                        'base_count': total_demographics,
                        'family_types_count': family_types_count,
                        'house_sizes_count': house_sizes_count,
                        'house_types_count': house_types_count,
                        'products_with_family': products_with_family,
                        'products_with_size': products_with_size,
                        'products_with_type': products_with_type,
                        'progress_family': (products_with_family / total_demographics * 100) if total_demographics > 0 else 0,
                        'progress_size': (products_with_size / total_demographics * 100) if total_demographics > 0 else 0,
                        'progress_type': (products_with_type / total_demographics * 100) if total_demographics > 0 else 0,
                    }
                    
                    if detailed:
                        # 제품별 상세 정보
                        cur.execute(f"""
                            SELECT PRODUCT_ID, COUNT(*) as CNT
                            FROM {table_name}
                            GROUP BY PRODUCT_ID
                            ORDER BY CNT DESC
                            FETCH FIRST 10 ROWS ONLY
                        """)
                        top_products = cur.fetchall()
                        data['top_products'] = top_products
                        if top_products:
                            self.stdout.write(f'\n  가족 구성이 많은 제품 (상위 10개):')
                            for product_id, cnt in top_products:
                                self.stdout.write(f'    제품 {product_id}: {cnt}개')
        
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'  오류: {str(e)}'))
            data['error'] = str(e)
        
        return data if return_data else None

    def _check_user_sample_status(self, detailed, return_data=False):
        """USER_SAMPLE 정규화 상태 확인"""
        self.stdout.write(self.style.SUCCESS('\n[4] USER_SAMPLE 정규화 상태'))
        self.stdout.write('-' * 80)
        
        data = {'status': 'error'}
        
        try:
            # Django ORM으로 기본 데이터 수 확인
            total_users = UserSample.objects.count()
            
            with get_connection() as conn:
                with conn.cursor() as cur:
                    # 테이블 존재 여부 확인
                    if not self._table_exists(cur, 'USER_SAMPLE_RECOMMENDATIONS'):
                        self.stdout.write(self.style.WARNING('  ⚠ 정규화 테이블이 아직 생성되지 않았습니다.'))
                        self.stdout.write('  마이그레이션을 실행하세요: python manage.py migrate_all_to_normalized')
                        data = {'status': 'not_created', 'base_count': total_users}
                        return data if return_data else None
                    
                    # 정규화된 테이블 데이터 수
                    cur.execute("SELECT COUNT(*) FROM USER_SAMPLE_RECOMMENDATIONS")
                    recommendations_count = cur.fetchone()[0]
                    
                    cur.execute("SELECT COUNT(*) FROM USER_SAMPLE_PURCHASED_ITEMS")
                    purchased_items_count = cur.fetchone()[0]
                    
                    # 데이터가 있는 사용자 수
                    cur.execute("""
                        SELECT COUNT(DISTINCT USER_ID) 
                        FROM USER_SAMPLE_RECOMMENDATIONS
                    """)
                    users_with_recommendations = cur.fetchone()[0]
                    
                    cur.execute("""
                        SELECT COUNT(DISTINCT USER_ID) 
                        FROM USER_SAMPLE_PURCHASED_ITEMS
                    """)
                    users_with_purchases = cur.fetchone()[0]
                    
                    self.stdout.write(f'  기본 테이블 (USER_SAMPLE): {total_users}개 사용자')
                    self.stdout.write('')
                    self.stdout.write('  정규화 테이블:')
                    self.stdout.write(f'    USER_SAMPLE_RECOMMENDATIONS: {recommendations_count}개 레코드 ({users_with_recommendations}개 사용자)')
                    self.stdout.write(f'    USER_SAMPLE_PURCHASED_ITEMS: {purchased_items_count}개 레코드 ({users_with_purchases}개 사용자)')
                    self.stdout.write('')
                    
                    # 진행률 계산
                    if total_users > 0:
                        self.stdout.write('  진행률:')
                        self.stdout.write(f'    RECOMMENDATIONS: {self._print_progress_bar(users_with_recommendations, total_users)}')
                        self.stdout.write(f'    PURCHASED_ITEMS: {self._print_progress_bar(users_with_purchases, total_users)}')
                    else:
                        self.stdout.write('  진행률: 데이터 없음')
                    
                    data = {
                        'status': 'success',
                        'base_count': total_users,
                        'recommendations_count': recommendations_count,
                        'purchased_items_count': purchased_items_count,
                        'users_with_recommendations': users_with_recommendations,
                        'users_with_purchases': users_with_purchases,
                        'progress_recommendations': (users_with_recommendations / total_users * 100) if total_users > 0 else 0,
                        'progress_purchases': (users_with_purchases / total_users * 100) if total_users > 0 else 0,
                    }
        
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'  오류: {str(e)}'))
            data['error'] = str(e)
        
        return data if return_data else None
    
    def _generate_html_report(self, status_data, html_path):
        """HTML 리포트 생성"""
        html = f"""<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>정규화 마이그레이션 상태 리포트</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 10px;
            padding: 30px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.3);
        }}
        h1 {{
            color: #333;
            text-align: center;
            margin-bottom: 30px;
        }}
        .section {{
            margin-bottom: 30px;
            padding: 20px;
            background: #f8f9fa;
            border-radius: 8px;
        }}
        .progress-bar {{
            width: 100%;
            height: 30px;
            background: #e0e0e0;
            border-radius: 15px;
            overflow: hidden;
            margin: 10px 0;
        }}
        .progress-fill {{
            height: 100%;
            background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-weight: bold;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>정규화 마이그레이션 상태 리포트</h1>
        <p>생성 시간: <script>document.write(new Date().toLocaleString('ko-KR'));</script></p>
    </div>
</body>
</html>"""
        
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(html)

