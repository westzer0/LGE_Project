"""
ONBOARDING_SESSION에서 taste_id가 NULL인 레코드들을 분석하는 명령어
"""
from django.core.management.base import BaseCommand
from api.db.oracle_client import get_connection


class Command(BaseCommand):
    help = "taste_id가 NULL인 레코드 분석"

    def add_arguments(self, parser):
        parser.add_argument(
            '--session-id',
            type=str,
            help='분석할 특정 세션 ID'
        )

    def handle(self, *args, **options):
        session_id = options.get('session_id')
        
        with get_connection() as conn:
            with conn.cursor() as cur:
                if session_id:
                    # 특정 세션 분석
                    self.stdout.write(f"\n[분석] 세션 {session_id}:")
                    cur.execute("""
                        SELECT 
                            SESSION_ID,
                            STATUS,
                            CURRENT_STEP,
                            VIBE,
                            HOUSEHOLD_SIZE,
                            HAS_PET,
                            HOUSING_TYPE,
                            PYUNG,
                            PRIORITY,
                            BUDGET_LEVEL,
                            TASTE_ID
                        FROM ONBOARDING_SESSION
                        WHERE SESSION_ID = :session_id
                    """, {'session_id': session_id})
                else:
                    # COMPLETED 상태인데 taste_id가 NULL인 세션들
                    self.stdout.write("\n[분석] COMPLETED 상태인데 TASTE_ID가 NULL인 세션들:")
                    cur.execute("""
                        SELECT 
                            SESSION_ID,
                            STATUS,
                            CURRENT_STEP,
                            VIBE,
                            HOUSEHOLD_SIZE,
                            HAS_PET,
                            HOUSING_TYPE,
                            PYUNG,
                            PRIORITY,
                            BUDGET_LEVEL,
                            TASTE_ID
                        FROM (
                            SELECT 
                                SESSION_ID,
                                STATUS,
                                CURRENT_STEP,
                                VIBE,
                                HOUSEHOLD_SIZE,
                                HAS_PET,
                                HOUSING_TYPE,
                                PYUNG,
                                PRIORITY,
                                BUDGET_LEVEL,
                                TASTE_ID
                            FROM ONBOARDING_SESSION
                            WHERE STATUS = 'COMPLETED'
                              AND (TASTE_ID IS NULL OR TASTE_ID = 0)
                            ORDER BY CREATED_AT DESC
                        )
                        WHERE ROWNUM <= 10
                    """)
                
                cols = [c[0] for c in cur.description]
                rows = cur.fetchall()
                
                if not rows:
                    self.stdout.write(self.style.WARNING("  해당하는 레코드가 없습니다."))
                    return
                
                for row in rows:
                    data = dict(zip(cols, row))
                    self.stdout.write(f"\n  세션 ID: {data['SESSION_ID']}")
                    self.stdout.write(f"    STATUS: {data['STATUS']}")
                    self.stdout.write(f"    CURRENT_STEP: {data['CURRENT_STEP']}")
                    self.stdout.write(f"    VIBE: {data['VIBE']}")
                    self.stdout.write(f"    HOUSEHOLD_SIZE: {data['HOUSEHOLD_SIZE']}")
                    self.stdout.write(f"    HAS_PET: {data['HAS_PET']}")
                    self.stdout.write(f"    HOUSING_TYPE: {data['HOUSING_TYPE']}")
                    self.stdout.write(f"    PYUNG: {data['PYUNG']}")
                    self.stdout.write(f"    PRIORITY: {data['PRIORITY']}")
                    self.stdout.write(f"    BUDGET_LEVEL: {data['BUDGET_LEVEL']}")
                    self.stdout.write(f"    TASTE_ID: {data['TASTE_ID']}")
                    
                    # MAIN_SPACE 조회
                    cur.execute("""
                        SELECT MAIN_SPACE 
                        FROM ONBOARD_SESS_MAIN_SPACES
                        WHERE SESSION_ID = :session_id
                        ORDER BY MAIN_SPACE
                    """, {'session_id': data['SESSION_ID']})
                    main_spaces = [r[0] for r in cur.fetchall()]
                    self.stdout.write(f"    MAIN_SPACE: {main_spaces if main_spaces else '(없음)'}")
                    
                    # 매칭 시도
                    if data['STATUS'] == 'COMPLETED':
                        self.stdout.write(f"\n    [매칭 시도]")
                        from api.services.onboarding_taste_matching_service import onboarding_taste_matching_service
                        taste_id = onboarding_taste_matching_service.update_taste_id_for_session(data['SESSION_ID'])
                        if taste_id:
                            self.stdout.write(self.style.SUCCESS(f"      ✓ TASTE_ID 업데이트 성공: {taste_id}"))
                        else:
                            self.stdout.write(self.style.ERROR(f"      ✗ 매칭 실패"))
                            
                            # 부분 매칭 확인
                            cur.execute("""
                                SELECT COUNT(*) 
                                FROM TASTE_CONFIG
                                WHERE REPRESENTATIVE_VIBE = :vibe
                                  AND IS_ACTIVE = 'Y'
                            """, {'vibe': data['VIBE']})
                            vibe_count = cur.fetchone()[0]
                            self.stdout.write(f"      - VIBE만 매칭: {vibe_count}개")
                            
                            if data['HOUSEHOLD_SIZE']:
                                cur.execute("""
                                    SELECT COUNT(*) 
                                    FROM TASTE_CONFIG
                                    WHERE REPRESENTATIVE_VIBE = :vibe
                                      AND REPRESENTATIVE_HOUSEHOLD_SIZE = :household_size
                                      AND IS_ACTIVE = 'Y'
                                """, {
                                    'vibe': data['VIBE'],
                                    'household_size': data['HOUSEHOLD_SIZE']
                                })
                                count = cur.fetchone()[0]
                                self.stdout.write(f"      - VIBE + HOUSEHOLD_SIZE 매칭: {count}개")
                
                # 통계
                self.stdout.write(f"\n[통계]")
                cur.execute("""
                    SELECT 
                        COUNT(*) as total,
                        SUM(CASE WHEN STATUS = 'COMPLETED' AND (TASTE_ID IS NULL OR TASTE_ID = 0) THEN 1 ELSE 0 END) as completed_null,
                        SUM(CASE WHEN STATUS = 'IN_PROGRESS' AND (TASTE_ID IS NULL OR TASTE_ID = 0) THEN 1 ELSE 0 END) as in_progress_null,
                        SUM(CASE WHEN STATUS = 'COMPLETED' AND TASTE_ID IS NOT NULL AND TASTE_ID > 0 THEN 1 ELSE 0 END) as completed_with_taste
                    FROM ONBOARDING_SESSION
                """)
                stats = cur.fetchone()
                total, completed_null, in_progress_null, completed_with_taste = stats
                
                self.stdout.write(f"  전체 세션: {total}")
                self.stdout.write(f"  COMPLETED + TASTE_ID NULL: {completed_null}")
                self.stdout.write(f"  IN_PROGRESS + TASTE_ID NULL: {in_progress_null}")
                self.stdout.write(f"  COMPLETED + TASTE_ID 있음: {completed_with_taste}")

