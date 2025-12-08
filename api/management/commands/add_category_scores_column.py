"""
Django management command: Oracle DB의 TASTE_CONFIG 테이블에 
RECOMMENDED_CATEGORIES_WITH_SCORES 컬럼 추가
"""
from django.core.management.base import BaseCommand
from api.db.oracle_client import get_connection
import os


class Command(BaseCommand):
    help = 'Oracle DB의 TASTE_CONFIG 테이블에 RECOMMENDED_CATEGORIES_WITH_SCORES 컬럼 추가'

    def add_arguments(self, parser):
        parser.add_argument(
            '--check-only',
            action='store_true',
            help='컬럼 존재 여부만 확인 (실제 추가하지 않음)',
        )

    def handle(self, *args, **options):
        check_only = options.get('check_only', False)
        
        # SQL 파일 경로
        sql_file = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            'db',
            'add_category_scores_column.sql'
        )
        
        if not os.path.exists(sql_file):
            self.stdout.write(self.style.ERROR(f'SQL 파일을 찾을 수 없습니다: {sql_file}'))
            return
        
        # SQL 파일 읽기
        with open(sql_file, 'r', encoding='utf-8') as f:
            sql_content = f.read()
        
        # SQL 문 분리 (세미콜론 기준)
        sql_statements = [s.strip() for s in sql_content.split(';') if s.strip() and not s.strip().startswith('--')]
        
        try:
            with get_connection() as conn:
                with conn.cursor() as cur:
                    # 컬럼 존재 여부 확인 (Oracle 11g는 컬럼명 30자 제한으로 CATEGORY_SCORES 사용)
                    cur.execute("""
                        SELECT COUNT(*) 
                        FROM USER_TAB_COLUMNS 
                        WHERE TABLE_NAME = 'TASTE_CONFIG' 
                        AND COLUMN_NAME = 'CATEGORY_SCORES'
                    """)
                    column_exists = cur.fetchone()[0] > 0
                    
                    if column_exists:
                        self.stdout.write(self.style.SUCCESS('✓ CATEGORY_SCORES 컬럼이 이미 존재합니다.'))
                        return
                    
                    if check_only:
                        self.stdout.write(self.style.WARNING('컬럼이 존재하지 않습니다. (--check-only 모드)'))
                        return
                    
                    # ALTER TABLE 실행
                    self.stdout.write('CATEGORY_SCORES 컬럼 추가 중...')
                    
                    for sql in sql_statements:
                        if sql:
                            try:
                                cur.execute(sql)
                                self.stdout.write(self.style.SUCCESS(f'✓ 실행 완료: {sql[:50]}...'))
                            except Exception as e:
                                # 이미 존재하는 경우 무시
                                if 'ORA-01430' in str(e) or 'already exists' in str(e).lower():
                                    self.stdout.write(self.style.WARNING(f'컬럼이 이미 존재합니다: {sql[:50]}...'))
                                else:
                                    raise
                    
                    conn.commit()
                    self.stdout.write(self.style.SUCCESS('\n✓ 컬럼 추가 완료!'))
                    
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'\n✗ 오류 발생: {str(e)}'))
            import traceback
            self.stdout.write(self.style.ERROR(traceback.format_exc()))
            raise

