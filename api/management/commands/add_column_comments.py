"""
컬럼별 COMMENT 추가 명령어

모든 주요 테이블의 컬럼에 의미를 설명하는 COMMENT를 추가합니다.

사용법:
    python manage.py add_column_comments
    python manage.py add_column_comments --dry-run  # 테스트만 실행
"""
from django.core.management.base import BaseCommand
from api.db.oracle_client import get_connection


class Command(BaseCommand):
    help = '모든 주요 테이블의 컬럼에 COMMENT 추가'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='실제 변경 없이 테스트만 실행',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        if dry_run:
            self.stdout.write(self.style.WARNING('=== DRY RUN 모드 (실제 변경 없음) ===\n'))
        
        self.stdout.write(self.style.SUCCESS('\n=== 컬럼 COMMENT 추가 ===\n'))
        
        # SQL 파일 읽기
        import os
        from pathlib import Path
        
        base_dir = Path(__file__).resolve().parent.parent.parent.parent
        sql_file = base_dir / 'api' / 'db' / 'add_column_comments.sql'
        
        if not sql_file.exists():
            self.stdout.write(
                self.style.ERROR(f'SQL 파일을 찾을 수 없습니다: {sql_file}')
            )
            return
        
        with open(sql_file, 'r', encoding='utf-8') as f:
            sql_content = f.read()
        
        # SQL 문장 분리 (세미콜론 기준)
        sql_statements = [s.strip() for s in sql_content.split(';') if s.strip() and not s.strip().startswith('--')]
        
        success_count = 0
        error_count = 0
        
        try:
            with get_connection() as conn:
                with conn.cursor() as cur:
                    for sql in sql_statements:
                        if not sql or sql.startswith('--'):
                            continue
                        
                        try:
                            if not dry_run:
                                cur.execute(sql)
                            success_count += 1
                            
                            # COMMENT ON 문장에서 테이블/컬럼명 추출
                            if 'COMMENT ON' in sql.upper():
                                if 'COMMENT ON TABLE' in sql.upper():
                                    table_name = sql.split('COMMENT ON TABLE')[1].split('IS')[0].strip()
                                    self.stdout.write(f'  ✓ TABLE: {table_name}')
                                elif 'COMMENT ON COLUMN' in sql.upper():
                                    parts = sql.split('COMMENT ON COLUMN')[1].split('IS')[0].strip()
                                    if '.' in parts:
                                        table_col = parts.split('.')
                                        if len(table_col) == 2:
                                            self.stdout.write(f'    ✓ COLUMN: {table_col[0]}.{table_col[1]}')
                        
                        except Exception as e:
                            error_count += 1
                            self.stdout.write(
                                self.style.ERROR(f'  ✗ 오류: {str(e)[:100]}')
                            )
                            if 'COMMENT ON' in sql.upper():
                                self.stdout.write(f'    SQL: {sql[:100]}...')
                    
                    if not dry_run:
                        conn.commit()
        
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'전체 실행 오류: {str(e)}')
            )
            return
        
        # 결과 출력
        self.stdout.write(self.style.SUCCESS(f'\n=== COMMENT 추가 완료 ==='))
        self.stdout.write(f'성공: {success_count}개')
        self.stdout.write(f'실패: {error_count}개')
        
        if dry_run:
            self.stdout.write(self.style.WARNING('\nDRY RUN 모드였으므로 실제 변경은 없습니다.'))
        else:
            self.stdout.write(self.style.SUCCESS('\n모든 COMMENT가 추가되었습니다.'))
            self.stdout.write('\nCOMMENT 확인 방법:')
            self.stdout.write('  SELECT * FROM USER_COL_COMMENTS WHERE TABLE_NAME = ''테이블명'';')


