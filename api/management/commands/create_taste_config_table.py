"""
Oracle DB에 TASTE_CONFIG 테이블 생성

사용법:
    python manage.py create_taste_config_table
"""
from django.core.management.base import BaseCommand
from api.db.oracle_client import get_connection


class Command(BaseCommand):
    help = 'Oracle DB에 TASTE_CONFIG 테이블 생성'

    def add_arguments(self, parser):
        parser.add_argument(
            '--drop-if-exists',
            action='store_true',
            help='기존 테이블이 있으면 삭제 후 재생성',
        )

    def handle(self, *args, **options):
        drop_if_exists = options['drop_if_exists']

        self.stdout.write(self.style.SUCCESS('\n=== TASTE_CONFIG 테이블 생성 ===\n'))

        try:
            with get_connection() as conn:
                with conn.cursor() as cur:
                    # 기존 테이블 확인
                    cur.execute("""
                        SELECT COUNT(*) 
                        FROM USER_TABLES 
                        WHERE TABLE_NAME = 'TASTE_CONFIG'
                    """)
                    table_exists = cur.fetchone()[0] > 0

                    if table_exists:
                        if drop_if_exists:
                            self.stdout.write('[INFO] 기존 TASTE_CONFIG 테이블 삭제 중...')
                            cur.execute("DROP TABLE TASTE_CONFIG CASCADE CONSTRAINTS")
                            self.stdout.write(self.style.SUCCESS('✓ 삭제 완료'))
                        else:
                            self.stdout.write(self.style.WARNING('TASTE_CONFIG 테이블이 이미 존재합니다.'))
                            self.stdout.write('기존 테이블을 삭제하고 재생성하려면 --drop-if-exists 옵션을 사용하세요.')
                            return

                    # 테이블 생성
                    self.stdout.write('[INFO] TASTE_CONFIG 테이블 생성 중...')
                    cur.execute("""
                        CREATE TABLE TASTE_CONFIG (
                            TASTE_ID NUMBER PRIMARY KEY,
                            DESCRIPTION VARCHAR2(500),
                            REPRESENTATIVE_VIBE VARCHAR2(20),
                            REPRESENTATIVE_HOUSEHOLD_SIZE NUMBER,
                            REPRESENTATIVE_MAIN_SPACE VARCHAR2(50),
                            REPRESENTATIVE_HAS_PET CHAR(1),
                            REPRESENTATIVE_PRIORITY VARCHAR2(20),
                            REPRESENTATIVE_BUDGET_LEVEL VARCHAR2(20),
                            RECOMMENDED_CATEGORIES CLOB,
                            RECOMMENDED_PRODUCTS CLOB,
                            IS_ACTIVE CHAR(1) DEFAULT 'Y',
                            AUTO_GENERATED CHAR(1) DEFAULT 'N',
                            LAST_SIMULATION_DATE DATE,
                            CREATED_AT DATE DEFAULT SYSDATE,
                            UPDATED_AT DATE DEFAULT SYSDATE
                        )
                    """)
                    self.stdout.write(self.style.SUCCESS('✓ 테이블 생성 완료'))

                    # 인덱스 생성
                    self.stdout.write('[INFO] 인덱스 생성 중...')
                    cur.execute("CREATE INDEX IDX_TASTE_CONFIG_ACTIVE ON TASTE_CONFIG(IS_ACTIVE)")
                    cur.execute("CREATE INDEX IDX_TASTE_CONFIG_UPDATED ON TASTE_CONFIG(UPDATED_AT)")
                    self.stdout.write(self.style.SUCCESS('✓ 인덱스 생성 완료'))

                    # 주석 추가
                    self.stdout.write('[INFO] 주석 추가 중...')
                    cur.execute("COMMENT ON TABLE TASTE_CONFIG IS 'Taste별 추천 설정 관리 테이블'")
                    cur.execute("COMMENT ON COLUMN TASTE_CONFIG.TASTE_ID IS 'Taste ID (1-120)'")
                    cur.execute("COMMENT ON COLUMN TASTE_CONFIG.RECOMMENDED_CATEGORIES IS '추천 MAIN_CATEGORY 리스트 (JSON 배열)'")
                    cur.execute("COMMENT ON COLUMN TASTE_CONFIG.RECOMMENDED_PRODUCTS IS '카테고리별 추천 제품 ID 매핑 (JSON 객체)'")
                    self.stdout.write(self.style.SUCCESS('✓ 주석 추가 완료'))

                    conn.commit()
                    self.stdout.write(self.style.SUCCESS('\n=== 완료 ===\n'))
                    self.stdout.write('Oracle SQL Developer에서 TASTE_CONFIG 테이블을 확인할 수 있습니다.')

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'\n오류 발생: {str(e)}'))
            import traceback
            self.stdout.write(traceback.format_exc())

