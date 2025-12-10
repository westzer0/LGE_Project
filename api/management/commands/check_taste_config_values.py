"""
TASTE_CONFIG 테이블의 실제 값들을 확인하는 명령어
"""
from django.core.management.base import BaseCommand
from api.db.oracle_client import get_connection


class Command(BaseCommand):
    help = "TASTE_CONFIG 테이블의 실제 값 확인"

    def handle(self, *args, **options):
        with get_connection() as conn:
            with conn.cursor() as cur:
                # 1. VIBE 값들
                self.stdout.write("\n[1] REPRESENTATIVE_VIBE 값들:")
                cur.execute("""
                    SELECT DISTINCT REPRESENTATIVE_VIBE, COUNT(*) as cnt
                    FROM TASTE_CONFIG
                    WHERE IS_ACTIVE = 'Y'
                    GROUP BY REPRESENTATIVE_VIBE
                    ORDER BY REPRESENTATIVE_VIBE
                """)
                for row in cur.fetchall():
                    self.stdout.write(f"  {row[0]}: {row[1]}개")
                
                # 2. HOUSEHOLD_SIZE 값들
                self.stdout.write("\n[2] REPRESENTATIVE_HOUSEHOLD_SIZE 값들:")
                cur.execute("""
                    SELECT DISTINCT REPRESENTATIVE_HOUSEHOLD_SIZE, COUNT(*) as cnt
                    FROM TASTE_CONFIG
                    WHERE IS_ACTIVE = 'Y'
                    GROUP BY REPRESENTATIVE_HOUSEHOLD_SIZE
                    ORDER BY REPRESENTATIVE_HOUSEHOLD_SIZE
                """)
                for row in cur.fetchall():
                    self.stdout.write(f"  {row[0]}: {row[1]}개")
                
                # 3. HAS_PET 값들
                self.stdout.write("\n[3] REPRESENTATIVE_HAS_PET 값들:")
                cur.execute("""
                    SELECT DISTINCT REPRESENTATIVE_HAS_PET, COUNT(*) as cnt
                    FROM TASTE_CONFIG
                    WHERE IS_ACTIVE = 'Y'
                    GROUP BY REPRESENTATIVE_HAS_PET
                    ORDER BY REPRESENTATIVE_HAS_PET
                """)
                for row in cur.fetchall():
                    self.stdout.write(f"  {row[0]}: {row[1]}개")
                
                # 4. PRIORITY 값들
                self.stdout.write("\n[4] REPRESENTATIVE_PRIORITY 값들:")
                cur.execute("""
                    SELECT DISTINCT REPRESENTATIVE_PRIORITY, COUNT(*) as cnt
                    FROM TASTE_CONFIG
                    WHERE IS_ACTIVE = 'Y'
                    GROUP BY REPRESENTATIVE_PRIORITY
                    ORDER BY REPRESENTATIVE_PRIORITY
                """)
                for row in cur.fetchall():
                    self.stdout.write(f"  {row[0]}: {row[1]}개")
                
                # 5. BUDGET_LEVEL 값들
                self.stdout.write("\n[5] REPRESENTATIVE_BUDGET_LEVEL 값들:")
                cur.execute("""
                    SELECT DISTINCT REPRESENTATIVE_BUDGET_LEVEL, COUNT(*) as cnt
                    FROM TASTE_CONFIG
                    WHERE IS_ACTIVE = 'Y'
                    GROUP BY REPRESENTATIVE_BUDGET_LEVEL
                    ORDER BY REPRESENTATIVE_BUDGET_LEVEL
                """)
                for row in cur.fetchall():
                    self.stdout.write(f"  {row[0]}: {row[1]}개")
                
                # 6. MAIN_SPACE 값들 (샘플)
                self.stdout.write("\n[6] REPRESENTATIVE_MAIN_SPACE 값들 (샘플):")
                cur.execute("""
                    SELECT DISTINCT REPRESENTATIVE_MAIN_SPACE, COUNT(*) as cnt
                    FROM (
                        SELECT REPRESENTATIVE_MAIN_SPACE
                        FROM TASTE_CONFIG
                        WHERE IS_ACTIVE = 'Y'
                          AND REPRESENTATIVE_MAIN_SPACE IS NOT NULL
                    )
                    GROUP BY REPRESENTATIVE_MAIN_SPACE
                    ORDER BY cnt DESC
                """)
                rows = cur.fetchall()[:10]
                for row in rows:
                    self.stdout.write(f"  '{row[0]}': {row[1]}개")
                
                # NULL인 것도 확인
                cur.execute("""
                    SELECT COUNT(*) 
                    FROM TASTE_CONFIG
                    WHERE IS_ACTIVE = 'Y'
                      AND (REPRESENTATIVE_MAIN_SPACE IS NULL OR REPRESENTATIVE_MAIN_SPACE = '')
                """)
                null_count = cur.fetchone()[0]
                self.stdout.write(f"  NULL 또는 빈 문자열: {null_count}개")

