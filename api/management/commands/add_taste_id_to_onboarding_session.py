"""
ONBOARDING_SESSION 테이블에 TASTE_ID 컬럼을 추가하는 명령어
"""
from django.core.management.base import BaseCommand
from api.db.oracle_client import get_connection


class Command(BaseCommand):
    help = "ONBOARDING_SESSION 테이블에 TASTE_ID 컬럼 추가"

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='실제로 실행하지 않고 SQL만 출력'
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        if dry_run:
            self.stdout.write(self.style.WARNING("[DRY RUN] 실제로는 실행하지 않습니다."))
        
        self.stdout.write(self.style.SUCCESS("=" * 60))
        self.stdout.write(self.style.SUCCESS("ONBOARDING_SESSION.TASTE_ID 컬럼 추가 시작"))
        self.stdout.write(self.style.SUCCESS("=" * 60))
        
        try:
            with get_connection() as conn:
                with conn.cursor() as cur:
                    # 1. TASTE_ID 컬럼 존재 여부 확인
                    self.stdout.write("\n[1] TASTE_ID 컬럼 확인...")
                    cur.execute("""
                        SELECT COUNT(*) 
                        FROM USER_TAB_COLUMNS 
                        WHERE TABLE_NAME = 'ONBOARDING_SESSION' 
                          AND COLUMN_NAME = 'TASTE_ID'
                    """)
                    exists = cur.fetchone()[0] > 0
                    
                    if exists:
                        self.stdout.write(self.style.SUCCESS("  ✓ TASTE_ID 컬럼이 이미 존재합니다."))
                    else:
                        # 2. TASTE_ID 컬럼 추가
                        self.stdout.write("\n[2] TASTE_ID 컬럼 추가 중...")
                        if not dry_run:
                            cur.execute("ALTER TABLE ONBOARDING_SESSION ADD (TASTE_ID NUMBER(4))")
                            conn.commit()
                        self.stdout.write(self.style.SUCCESS("  ✓ TASTE_ID 컬럼 추가 완료"))
                    
                    # 3. 인덱스 존재 여부 확인
                    self.stdout.write("\n[3] TASTE_ID 인덱스 확인...")
                    cur.execute("""
                        SELECT COUNT(*) 
                        FROM USER_INDEXES 
                        WHERE TABLE_NAME = 'ONBOARDING_SESSION' 
                          AND INDEX_NAME = 'IDX_SESSION_TASTE_ID'
                    """)
                    index_exists = cur.fetchone()[0] > 0
                    
                    if index_exists:
                        self.stdout.write(self.style.SUCCESS("  ✓ TASTE_ID 인덱스가 이미 존재합니다."))
                    else:
                        # 4. 인덱스 생성
                        self.stdout.write("\n[4] TASTE_ID 인덱스 생성 중...")
                        if not dry_run:
                            cur.execute("CREATE INDEX IDX_SESSION_TASTE_ID ON ONBOARDING_SESSION(TASTE_ID)")
                            conn.commit()
                        self.stdout.write(self.style.SUCCESS("  ✓ TASTE_ID 인덱스 생성 완료"))
                    
                    # 5. 주석 추가
                    self.stdout.write("\n[5] TASTE_ID 컬럼 주석 추가 중...")
                    if not dry_run:
                        try:
                            cur.execute("""
                                COMMENT ON COLUMN ONBOARDING_SESSION.TASTE_ID IS 
                                '매칭된 Taste ID (1-1920, TASTE_CONFIG와 비교하여 설정)'
                            """)
                            conn.commit()
                            self.stdout.write(self.style.SUCCESS("  ✓ 주석 추가 완료"))
                        except Exception as e:
                            self.stdout.write(self.style.WARNING(f"  - 주석 추가 중 오류 (무시): {e}"))
                    else:
                        self.stdout.write("  [DRY RUN] 주석 추가 스킵")
                    
                    # 6. 최종 확인
                    self.stdout.write("\n[6] 최종 확인...")
                    if not dry_run:
                        cur.execute("""
                            SELECT 
                                COLUMN_NAME,
                                DATA_TYPE,
                                DATA_LENGTH,
                                NULLABLE
                            FROM USER_TAB_COLUMNS
                            WHERE TABLE_NAME = 'ONBOARDING_SESSION'
                              AND COLUMN_NAME = 'TASTE_ID'
                        """)
                        result = cur.fetchone()
                        
                        if result:
                            col_name, data_type, data_length, nullable = result
                            self.stdout.write(f"  - 컬럼명: {col_name}")
                            self.stdout.write(f"  - 데이터 타입: {data_type}({data_length})")
                            self.stdout.write(f"  - NULL 허용: {nullable}")
                            self.stdout.write(self.style.SUCCESS("  ✓ TASTE_ID 컬럼이 정상적으로 추가되었습니다."))
                        else:
                            self.stdout.write(self.style.ERROR("  ✗ TASTE_ID 컬럼을 찾을 수 없습니다."))
                    else:
                        self.stdout.write("  [DRY RUN] 최종 확인 스킵")
            
            self.stdout.write(self.style.SUCCESS("\n" + "=" * 60))
            self.stdout.write(self.style.SUCCESS("ONBOARDING_SESSION.TASTE_ID 컬럼 추가 완료!"))
            self.stdout.write(self.style.SUCCESS("=" * 60))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"\n오류 발생: {str(e)}"))
            import traceback
            self.stdout.write(self.style.ERROR(traceback.format_exc()))
            raise


