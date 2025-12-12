"""
TASTE_CONFIG와 ONBOARDING_SESSION 매칭 디버깅용 명령어
"""
from django.core.management.base import BaseCommand
from api.db.oracle_client import get_connection


class Command(BaseCommand):
    help = "TASTE_CONFIG와 ONBOARDING_SESSION 매칭 디버깅"

    def add_arguments(self, parser):
        parser.add_argument(
            '--session-id',
            type=str,
            help='디버깅할 세션 ID'
        )

    def handle(self, *args, **options):
        session_id = options.get('session_id')
        
        if not session_id:
            # 완료된 세션 중 하나 선택
            with get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT SESSION_ID
                        FROM ONBOARDING_SESSION
                        WHERE STATUS = 'COMPLETED'
                          AND (TASTE_ID IS NULL OR TASTE_ID = 0)
                        AND ROWNUM <= 1
                    """)
                    result = cur.fetchone()
                    if result:
                        session_id = result[0]
                        self.stdout.write(f"[INFO] 세션 {session_id}를 선택했습니다.")
                    else:
                        self.stdout.write(self.style.ERROR("완료된 세션을 찾을 수 없습니다."))
                        return
        
        with get_connection() as conn:
            with conn.cursor() as cur:
                # 1. 세션 데이터 조회
                self.stdout.write(f"\n[1] 세션 {session_id} 데이터:")
                cur.execute("""
                    SELECT 
                        VIBE,
                        HOUSEHOLD_SIZE,
                        HAS_PET,
                        PRIORITY,
                        BUDGET_LEVEL
                    FROM ONBOARDING_SESSION
                    WHERE SESSION_ID = :session_id
                """, {'session_id': session_id})
                
                cols = [c[0] for c in cur.description]
                row = cur.fetchone()
                
                if not row:
                    self.stdout.write(self.style.ERROR("세션을 찾을 수 없습니다."))
                    return
                
                session_data = dict(zip(cols, row))
                for key, value in session_data.items():
                    self.stdout.write(f"  {key}: {value}")
                
                # 2. MAIN_SPACE 조회
                cur.execute("""
                    SELECT MAIN_SPACE 
                    FROM ONBOARD_SESS_MAIN_SPACES
                    WHERE SESSION_ID = :session_id
                    ORDER BY MAIN_SPACE
                """, {'session_id': session_id})
                main_spaces = [row[0] for row in cur.fetchall()]
                main_space_str = ','.join(sorted(main_spaces)) if main_spaces else ''
                self.stdout.write(f"  MAIN_SPACE: {main_space_str}")
                
                # 3. TASTE_CONFIG에서 매칭 시도
                self.stdout.write(f"\n[2] TASTE_CONFIG 매칭 시도:")
                has_pet_char = session_data.get('HAS_PET') or 'N'
                
                self.stdout.write(f"  검색 조건:")
                self.stdout.write(f"    VIBE: {session_data.get('VIBE')}")
                self.stdout.write(f"    HOUSEHOLD_SIZE: {session_data.get('HOUSEHOLD_SIZE')}")
                self.stdout.write(f"    MAIN_SPACE: {main_space_str}")
                self.stdout.write(f"    HAS_PET: {has_pet_char}")
                self.stdout.write(f"    PRIORITY: {session_data.get('PRIORITY')}")
                self.stdout.write(f"    BUDGET_LEVEL: {session_data.get('BUDGET_LEVEL')}")
                
                cur.execute("""
                    SELECT 
                        TASTE_ID,
                        REPRESENTATIVE_VIBE,
                        REPRESENTATIVE_HOUSEHOLD_SIZE,
                        REPRESENTATIVE_MAIN_SPACE,
                        REPRESENTATIVE_HAS_PET,
                        REPRESENTATIVE_PRIORITY,
                        REPRESENTATIVE_BUDGET_LEVEL
                    FROM (
                        SELECT TASTE_ID,
                            REPRESENTATIVE_VIBE,
                            REPRESENTATIVE_HOUSEHOLD_SIZE,
                            REPRESENTATIVE_MAIN_SPACE,
                            REPRESENTATIVE_HAS_PET,
                            REPRESENTATIVE_PRIORITY,
                            REPRESENTATIVE_BUDGET_LEVEL
                        FROM TASTE_CONFIG
                        WHERE REPRESENTATIVE_VIBE = :vibe
                          AND REPRESENTATIVE_HOUSEHOLD_SIZE = :household_size
                          AND REPRESENTATIVE_MAIN_SPACE = :main_space
                          AND REPRESENTATIVE_HAS_PET = :has_pet
                          AND REPRESENTATIVE_PRIORITY = :priority
                          AND REPRESENTATIVE_BUDGET_LEVEL = :budget_level
                          AND IS_ACTIVE = 'Y'
                        ORDER BY TASTE_ID
                    )
                    WHERE ROWNUM <= 5
                """, {
                    'vibe': session_data.get('VIBE'),
                    'household_size': session_data.get('HOUSEHOLD_SIZE'),
                    'main_space': main_space_str,
                    'has_pet': has_pet_char,
                    'priority': session_data.get('PRIORITY'),
                    'budget_level': session_data.get('BUDGET_LEVEL')
                })
                
                results = cur.fetchall()
                if results:
                    self.stdout.write(f"\n  ✓ 매칭되는 TASTE_CONFIG {len(results)}개 발견:")
                    for row in results:
                        self.stdout.write(f"    TASTE_ID: {row[0]}")
                else:
                    self.stdout.write(f"\n  ⚠️ 정확히 매칭되는 TASTE_CONFIG가 없습니다.")
                    
                    # 4. 부분 매칭 확인
                    self.stdout.write(f"\n[3] 부분 매칭 확인:")
                    
                    # VIBE만 매칭
                    cur.execute("""
                        SELECT COUNT(*) 
                        FROM TASTE_CONFIG
                        WHERE REPRESENTATIVE_VIBE = :vibe
                          AND IS_ACTIVE = 'Y'
                    """, {'vibe': session_data.get('VIBE')})
                    vibe_count = cur.fetchone()[0]
                    self.stdout.write(f"  VIBE만 매칭: {vibe_count}개")
                    
                    # VIBE + HOUSEHOLD_SIZE
                    cur.execute("""
                        SELECT COUNT(*) 
                        FROM TASTE_CONFIG
                        WHERE REPRESENTATIVE_VIBE = :vibe
                          AND REPRESENTATIVE_HOUSEHOLD_SIZE = :household_size
                          AND IS_ACTIVE = 'Y'
                    """, {
                        'vibe': session_data.get('VIBE'),
                        'household_size': session_data.get('HOUSEHOLD_SIZE')
                    })
                    vibe_household_count = cur.fetchone()[0]
                    self.stdout.write(f"  VIBE + HOUSEHOLD_SIZE 매칭: {vibe_household_count}개")
                    
                    # 전체 조건 중 NULL이 아닌 것들로 매칭
                    conditions = []
                    params = {}
                    
                    if session_data.get('VIBE'):
                        conditions.append("REPRESENTATIVE_VIBE = :vibe")
                        params['vibe'] = session_data.get('VIBE')
                    if session_data.get('HOUSEHOLD_SIZE'):
                        conditions.append("REPRESENTATIVE_HOUSEHOLD_SIZE = :household_size")
                        params['household_size'] = session_data.get('HOUSEHOLD_SIZE')
                    if main_space_str:
                        conditions.append("REPRESENTATIVE_MAIN_SPACE = :main_space")
                        params['main_space'] = main_space_str
                    if has_pet_char:
                        conditions.append("REPRESENTATIVE_HAS_PET = :has_pet")
                        params['has_pet'] = has_pet_char
                    if session_data.get('PRIORITY'):
                        conditions.append("REPRESENTATIVE_PRIORITY = :priority")
                        params['priority'] = session_data.get('PRIORITY')
                    if session_data.get('BUDGET_LEVEL'):
                        conditions.append("REPRESENTATIVE_BUDGET_LEVEL = :budget_level")
                        params['budget_level'] = session_data.get('BUDGET_LEVEL')
                    
                    if conditions:
                        where_clause = " AND ".join(conditions)
                        cur.execute(f"""
                            SELECT COUNT(*) 
                            FROM TASTE_CONFIG
                            WHERE {where_clause}
                              AND IS_ACTIVE = 'Y'
                        """, params)
                        partial_count = cur.fetchone()[0]
                        self.stdout.write(f"  NULL이 아닌 모든 조건 매칭: {partial_count}개")




