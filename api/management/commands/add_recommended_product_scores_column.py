"""
Oracle DB의 TASTE_CONFIG 테이블에 RECOMMENDED_PRODUCT_SCORES 컬럼 추가

사용법:
    python manage.py add_recommended_product_scores_column
"""
from django.core.management.base import BaseCommand
from api.db.oracle_client import get_connection


class Command(BaseCommand):
    help = 'Oracle DB TASTE_CONFIG 테이블에 RECOMMENDED_PRODUCT_SCORES 컬럼 추가'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='실제로 실행하지 않고 SQL만 출력',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']

        self.stdout.write(self.style.SUCCESS('\n=== RECOMMENDED_PRODUCT_SCORES 컬럼 추가 ===\n'))

        sql_statements = [
            'ALTER TABLE TASTE_CONFIG ADD RECOMMENDED_PRODUCT_SCORES CLOB',
            "COMMENT ON COLUMN TASTE_CONFIG.RECOMMENDED_PRODUCT_SCORES IS '카테고리별 추천 제품 점수 매핑 (JSON 객체, RECOMMENDED_PRODUCTS와 1:1 매핑)'"
        ]

        if dry_run:
            self.stdout.write(self.style.WARNING('[DRY RUN] 실행할 SQL:'))
            for sql in sql_statements:
                self.stdout.write(f'  {sql};')
            return

        try:
            with get_connection() as conn:
                with conn.cursor() as cur:
                    for i, statement in enumerate(sql_statements, 1):
                        try:
                            self.stdout.write(f'[{i}/{len(sql_statements)}] 실행 중...', ending=' ')
                            cur.execute(statement)
                            self.stdout.write(self.style.SUCCESS('✓ 완료'))
                        except Exception as e:
                            error_str = str(e).upper()
                            if 'ORA-01430' in error_str or 'ALREADY EXISTS' in error_str:
                                self.stdout.write(self.style.WARNING('건너뜀 (이미 존재)'))
                            else:
                                self.stdout.write(self.style.ERROR(f'오류: {str(e)}'))
                    
                    conn.commit()
                    self.stdout.write(self.style.SUCCESS('\n=== 완료 ===\n'))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'\n오류 발생: {str(e)}'))
            import traceback
            self.stdout.write(traceback.format_exc())

