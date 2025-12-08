"""WISHLIST 테이블 생성 명령"""
from django.core.management.base import BaseCommand
from api.db.oracle_client import get_connection
import os

class Command(BaseCommand):
    help = 'WISHLIST 테이블 생성'

    def handle(self, *args, **options):
        sql_file = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            'db',
            'create_wishlist_table.sql'
        )
        
        with open(sql_file, 'r', encoding='utf-8') as f:
            sql = f.read()
        
        try:
            with get_connection() as conn:
                with conn.cursor() as cur:
                    # SQL 문장들을 세미콜론으로 분리하여 실행
                    statements = [s.strip() for s in sql.split(';') if s.strip() and not s.strip().startswith('--')]
                    
                    for statement in statements:
                        if statement:
                            try:
                                cur.execute(statement)
                                self.stdout.write(self.style.SUCCESS(f'✓ 실행: {statement[:50]}...'))
                            except Exception as e:
                                # 테이블이 이미 존재하는 경우 무시
                                if 'ORA-00955' in str(e) or 'ORA-00942' in str(e):
                                    self.stdout.write(self.style.WARNING(f'⚠ 건너뜀 (이미 존재): {statement[:50]}...'))
                                else:
                                    self.stdout.write(self.style.ERROR(f'✗ 오류: {str(e)}'))
                    
                    conn.commit()
                    self.stdout.write(self.style.SUCCESS('\n✅ WISHLIST 테이블 생성 완료'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ 오류 발생: {str(e)}'))

