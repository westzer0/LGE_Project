"""
TASTE_CONFIG 테이블의 0점 컬럼 문제 해결

1. 점수 계산 로직 수정으로 해결 가능한 컬럼: 점수 재계산
2. 해결 불가능한 컬럼: 삭제

사용법:
    python manage.py fix_zero_score_columns --recalculate  # 점수 재계산
    python manage.py fix_zero_score_columns --delete      # 해결 불가능한 컬럼 삭제
    python manage.py fix_zero_score_columns --all          # 재계산 + 삭제
"""
from django.core.management.base import BaseCommand
from api.db.oracle_client import get_connection


class Command(BaseCommand):
    help = 'TASTE_CONFIG 테이블의 0점 컬럼 문제 해결'

    def add_arguments(self, parser):
        parser.add_argument(
            '--recalculate',
            action='store_true',
            help='점수 재계산 (populate_taste_config 실행)',
        )
        parser.add_argument(
            '--delete',
            action='store_true',
            help='해결 불가능한 컬럼 삭제',
        )
        parser.add_argument(
            '--all',
            action='store_true',
            help='재계산 + 삭제 모두 실행',
        )

    def handle(self, *args, **options):
        recalculate = options['recalculate'] or options['all']
        delete = options['delete'] or options['all']

        self.stdout.write(self.style.SUCCESS('\n=== TASTE_CONFIG 0점 컬럼 해결 ===\n'))

        if recalculate:
            self.stdout.write('[INFO] 점수 재계산 중...')
            self._recalculate_all_scores()
        
        if delete:
            self.stdout.write('[INFO] 해결 불가능한 컬럼 삭제 중...')
            self._delete_unfixable_columns()

        self.stdout.write(self.style.SUCCESS('\n=== 완료 ===\n'))

    def _recalculate_all_scores(self):
        """모든 taste_id에 대해 점수 재계산"""
        from api.management.commands.populate_taste_config import Command as PopulateCommand
        from io import StringIO
        import sys
        
        # populate_taste_config 명령 실행
        populate_cmd = PopulateCommand()
        
        # stdout을 캡처하여 출력 숨기기
        old_stdout = sys.stdout
        sys.stdout = StringIO()
        
        try:
            # 모든 taste_id (1-120)에 대해 강제 재계산
            populate_cmd.handle(taste_range='1-120', force=True)
            self.stdout.write(self.style.SUCCESS('  ✓ 점수 재계산 완료'))
        except Exception as e:
            sys.stdout = old_stdout
            self.stdout.write(self.style.ERROR(f'  ✗ 점수 재계산 실패: {str(e)}'))
            import traceback
            self.stdout.write(traceback.format_exc())
        finally:
            sys.stdout = old_stdout

    def _delete_unfixable_columns(self):
        """해결 불가능한 컬럼 삭제
        
        삭제 대상:
        - OBJET_SCORE, SIGNATURE_SCORE: 브랜드 라인으로 MAIN_CATEGORY가 아님
        """
        # 삭제할 컬럼 목록
        columns_to_delete = [
            'OBJET_SCORE',
            'SIGNATURE_SCORE',
        ]
        
        self.stdout.write('[WARNING] 다음 컬럼을 삭제합니다:')
        for col in columns_to_delete:
            self.stdout.write(f'  - {col}')
        
        confirm = input('\n정말 삭제하시겠습니까? (yes/no): ')
        if confirm.lower() != 'yes':
            self.stdout.write(self.style.WARNING('삭제 취소됨'))
            return

        try:
            with get_connection() as conn:
                with conn.cursor() as cur:
                    for column in columns_to_delete:
                        try:
                            self.stdout.write(f'[INFO] {column} 삭제 중...', ending=' ')
                            cur.execute(f'ALTER TABLE TASTE_CONFIG DROP COLUMN {column}')
                            self.stdout.write(self.style.SUCCESS('✓ 완료'))
                        except Exception as e:
                            error_str = str(e).upper()
                            if 'ORA-01430' in error_str or 'DOES NOT EXIST' in error_str or 'NOT FOUND' in error_str:
                                self.stdout.write(self.style.WARNING('건너뜀 (이미 삭제됨)'))
                            else:
                                self.stdout.write(self.style.ERROR(f'오류: {str(e)}'))
                    
                    conn.commit()
                    self.stdout.write(self.style.SUCCESS('\n컬럼 삭제 완료'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'\n컬럼 삭제 실패: {str(e)}'))
            import traceback
            self.stdout.write(traceback.format_exc())

