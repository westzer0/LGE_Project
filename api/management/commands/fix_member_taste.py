"""
MEMBER 테이블의 TASTE 칼럼을 1~1920 범위의 정수로 수정하는 명령어
"""
from django.core.management.base import BaseCommand
from api.db.oracle_client import get_connection


class Command(BaseCommand):
    help = "MEMBER 테이블의 TASTE 칼럼을 NUMBER(4) 타입으로 수정하고 1~1920 범위 제약조건 추가"

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
        self.stdout.write(self.style.SUCCESS("MEMBER.TASTE 칼럼 수정 시작"))
        self.stdout.write(self.style.SUCCESS("=" * 60))
        
        try:
            with get_connection() as conn:
                with conn.cursor() as cur:
                    # 1. 기존 TASTE 칼럼 삭제 시도
                    self.stdout.write("\n[1] 기존 TASTE 칼럼 확인 및 삭제...")
                    try:
                        if not dry_run:
                            cur.execute("ALTER TABLE MEMBER DROP COLUMN TASTE")
                            conn.commit()
                        self.stdout.write(self.style.SUCCESS("  ✓ 기존 TASTE 칼럼 삭제 완료"))
                    except Exception as e:
                        error_code = str(e)
                        if 'ORA-00904' in error_code or '904' in error_code:
                            self.stdout.write(self.style.WARNING("  - TASTE 칼럼이 존재하지 않습니다 (정상)"))
                        else:
                            self.stdout.write(self.style.WARNING(f"  - TASTE 칼럼 삭제 중 오류 (무시): {e}"))
                    
                    # 2. TASTE 칼럼 추가 (NUMBER(4))
                    self.stdout.write("\n[2] TASTE 칼럼 추가 (NUMBER(4))...")
                    try:
                        if not dry_run:
                            cur.execute("ALTER TABLE MEMBER ADD (TASTE NUMBER(4))")
                            conn.commit()
                        self.stdout.write(self.style.SUCCESS("  ✓ TASTE 칼럼 추가 완료"))
                    except Exception as e:
                        error_code = str(e)
                        if 'ORA-01430' in error_code or '1430' in error_code:
                            self.stdout.write(self.style.WARNING("  - TASTE 칼럼이 이미 존재합니다"))
                        else:
                            raise
                    
                    # 3. 기존 제약조건 삭제 시도
                    self.stdout.write("\n[3] 기존 TASTE 제약조건 확인 및 삭제...")
                    try:
                        if not dry_run:
                            cur.execute("ALTER TABLE MEMBER DROP CONSTRAINT CHK_TASTE_RANGE")
                            conn.commit()
                        self.stdout.write(self.style.SUCCESS("  ✓ 기존 제약조건 삭제 완료"))
                    except Exception as e:
                        error_code = str(e)
                        if 'ORA-02443' in error_code or '2443' in error_code:
                            self.stdout.write(self.style.WARNING("  - 제약조건이 존재하지 않습니다 (정상)"))
                        else:
                            self.stdout.write(self.style.WARNING(f"  - 제약조건 삭제 중 오류 (무시): {e}"))
                    
                    # 4. CHECK 제약조건 추가 (1~1920 범위)
                    self.stdout.write("\n[4] TASTE 범위 제약조건 추가 (1~1920)...")
                    try:
                        if not dry_run:
                            cur.execute("""
                                ALTER TABLE MEMBER 
                                ADD CONSTRAINT CHK_TASTE_RANGE 
                                CHECK (TASTE IS NULL OR (TASTE >= 1 AND TASTE <= 1920))
                            """)
                            conn.commit()
                        self.stdout.write(self.style.SUCCESS("  ✓ TASTE 범위 제약조건 추가 완료 (1~1920)"))
                    except Exception as e:
                        error_code = str(e)
                        if 'ORA-02264' in error_code or '2264' in error_code:
                            self.stdout.write(self.style.WARNING("  - 제약조건이 이미 존재합니다"))
                        else:
                            raise
                    
                    # 5. 기존 잘못된 데이터 정리
                    self.stdout.write("\n[5] 기존 잘못된 TASTE 값 정리...")
                    try:
                        if not dry_run:
                            # 범위를 벗어난 값 확인
                            cur.execute("""
                                SELECT COUNT(*) 
                                FROM MEMBER 
                                WHERE TASTE IS NOT NULL AND (TASTE < 1 OR TASTE > 1920)
                            """)
                            invalid_count = cur.fetchone()[0]
                            
                            if invalid_count > 0:
                                self.stdout.write(self.style.WARNING(f"  - 잘못된 TASTE 값 {invalid_count}개 발견"))
                                # 범위를 벗어난 값을 NULL로 설정
                                cur.execute("""
                                    UPDATE MEMBER 
                                    SET TASTE = NULL 
                                    WHERE TASTE IS NOT NULL AND (TASTE < 1 OR TASTE > 1920)
                                """)
                                conn.commit()
                                self.stdout.write(self.style.SUCCESS(f"  ✓ {invalid_count}개 값 정리 완료 (NULL로 설정)"))
                            else:
                                self.stdout.write(self.style.SUCCESS("  ✓ 잘못된 값 없음"))
                        else:
                            self.stdout.write("  [DRY RUN] 잘못된 값 확인 및 정리 스킵")
                    
                    # 6. 최종 확인
                    self.stdout.write("\n[6] 최종 확인...")
                    if not dry_run:
                        cur.execute("""
                            SELECT 
                                COUNT(*) as total,
                                COUNT(TASTE) as with_taste,
                                MIN(TASTE) as min_taste,
                                MAX(TASTE) as max_taste
                            FROM MEMBER
                        """)
                        result = cur.fetchone()
                        total, with_taste, min_taste, max_taste = result
                        
                        self.stdout.write(f"  - 전체 회원 수: {total}")
                        self.stdout.write(f"  - TASTE가 있는 회원: {with_taste}")
                        if min_taste is not None:
                            self.stdout.write(f"  - 최소 TASTE: {min_taste}")
                            self.stdout.write(f"  - 최대 TASTE: {max_taste}")
                            if min_taste >= 1 and max_taste <= 1920:
                                self.stdout.write(self.style.SUCCESS("  ✓ 모든 TASTE 값이 1~1920 범위 내입니다"))
                            else:
                                self.stdout.write(self.style.ERROR(f"  ✗ TASTE 값이 범위를 벗어남: {min_taste}~{max_taste}"))
                        else:
                            self.stdout.write("  - TASTE 값이 없습니다")
            
            self.stdout.write(self.style.SUCCESS("\n" + "=" * 60))
            self.stdout.write(self.style.SUCCESS("MEMBER.TASTE 칼럼 수정 완료!"))
            self.stdout.write(self.style.SUCCESS("=" * 60))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"\n오류 발생: {str(e)}"))
            import traceback
            self.stdout.write(self.style.ERROR(traceback.format_exc()))
            raise

