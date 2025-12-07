"""
Oracle DB의 TASTE_CONFIG 테이블에 ill-suited 및 category별 score 컬럼 추가

사용법:
    python manage.py add_taste_config_columns
"""
from django.core.management.base import BaseCommand
from api.db.oracle_client import get_connection


class Command(BaseCommand):
    help = 'Oracle DB TASTE_CONFIG 테이블에 ill-suited 및 category별 score 컬럼 추가'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='실제로 실행하지 않고 SQL만 출력',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']

        self.stdout.write(self.style.SUCCESS('\n=== TASTE_CONFIG 컬럼 추가 ===\n'))

        # SQL 파일에서 스크립트 읽기
        import os
        from django.conf import settings
        
        sql_file_path = os.path.join(
            settings.BASE_DIR if hasattr(settings, 'BASE_DIR') else '.',
            'api/db/add_taste_config_score_columns.sql'
        )
        
        try:
            with open(sql_file_path, 'r', encoding='utf-8') as f:
                sql_script = f.read()
        except FileNotFoundError:
            self.stdout.write(self.style.ERROR(f'SQL 파일을 찾을 수 없습니다: {sql_file_path}'))
            return

        if dry_run:
            self.stdout.write(self.style.WARNING('[DRY RUN] 실행할 SQL:'))
            self.stdout.write(sql_script)
            return

        try:
            with get_connection() as conn:
                with conn.cursor() as cur:
                    # SQL 스크립트를 세미콜론으로 분리하여 실행
                    # ALTER TABLE 문은 하나씩 실행해야 함
                    statements = [s.strip() for s in sql_script.split(';') if s.strip()]
                    
                    for i, statement in enumerate(statements, 1):
                        # 주석 건너뛰기
                        if statement.startswith('--'):
                            continue
                        
                        # 빈 문장 건너뛰기
                        if not statement:
                            continue
                        
                        try:
                            self.stdout.write(f'[{i}/{len(statements)}] 실행 중...', ending=' ')
                            cur.execute(statement)
                            self.stdout.write(self.style.SUCCESS('✓ 완료'))
                        except Exception as e:
                            # 컬럼이 이미 존재하는 경우 무시
                            if 'ORA-01430' in str(e) or 'already exists' in str(e).lower():
                                self.stdout.write(self.style.WARNING(f'건너뜀 (이미 존재): {str(e)[:50]}'))
                            else:
                                self.stdout.write(self.style.ERROR(f'오류: {str(e)}'))
                                # 계속 진행
                                continue
                    
                    conn.commit()
                    self.stdout.write(self.style.SUCCESS('\n=== 완료 ===\n'))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'\n오류 발생: {str(e)}'))
            import traceback
            self.stdout.write(traceback.format_exc())



