"""
모든 컬럼에 COMMENT 추가
models.py와 기존 코드를 참고하여 작성
"""
from django.core.management.base import BaseCommand
from api.db.oracle_client import get_connection


class Command(BaseCommand):
    help = '모든 컬럼에 COMMENT 추가 (PRD 및 models.py 참고)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='실제 실행하지 않고 SQL만 출력',
        )

    def handle(self, *args, **options):
        dry_run = options.get('dry_run', False)
        
        sql_file = 'api/db/add_all_column_comments.sql'
        
        try:
            with open(sql_file, 'r', encoding='utf-8') as f:
                sql_content = f.read()
            
            if dry_run:
                self.stdout.write(self.style.WARNING('=== DRY RUN 모드 ==='))
                self.stdout.write(sql_content)
                return
            
            self.stdout.write('컬럼 COMMENT 추가 중...')
            
            with get_connection() as conn:
                with conn.cursor() as cur:
                    # SQL 파일을 세미콜론으로 분리하여 실행
                    statements = [s.strip() for s in sql_content.split(';') if s.strip() and not s.strip().startswith('--')]
                    
                    success_count = 0
                    error_count = 0
                    
                    for statement in statements:
                        if not statement:
                            continue
                        
                        try:
                            cur.execute(statement)
                            success_count += 1
                        except Exception as e:
                            error_count += 1
                            # 오류가 발생해도 계속 진행
                            self.stdout.write(self.style.WARNING(f'  오류: {str(e)[:100]}'))
                            self.stdout.write(self.style.WARNING(f'  SQL: {statement[:100]}...'))
                    
                    conn.commit()
                    
                    self.stdout.write(self.style.SUCCESS(f'\n완료: {success_count}개 COMMENT 추가'))
                    if error_count > 0:
                        self.stdout.write(self.style.WARNING(f'  오류: {error_count}개 (일부 컬럼이 존재하지 않거나 이미 COMMENT가 있을 수 있음)'))
        
        except FileNotFoundError:
            self.stdout.write(self.style.ERROR(f'SQL 파일을 찾을 수 없습니다: {sql_file}'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'오류 발생: {str(e)}'))

