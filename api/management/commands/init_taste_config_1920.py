"""
이론적 최대 조합 수(1,920개)로 TASTE_CONFIG 테이블 초기화
representative 필드들만 채우고 나머지는 비워둠

사용법:
    python manage.py init_taste_config_1920
"""
import json
from itertools import product
from django.core.management.base import BaseCommand
from api.db.oracle_client import get_connection


class Command(BaseCommand):
    help = '이론적 최대 조합 수(1,920개)로 TASTE_CONFIG 테이블 초기화 (representative 필드만 채움)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear-existing',
            action='store_true',
            help='기존 데이터를 모두 삭제하고 시작',
        )
        parser.add_argument(
            '--batch-size',
            type=int,
            default=100,
            help='한 번에 처리할 배치 크기 (기본값: 100)',
        )

    def handle(self, *args, **options):
        clear_existing = options['clear_existing']
        batch_size = options['batch_size']

        self.stdout.write(self.style.SUCCESS('\n=== TASTE_CONFIG 초기화 (1,920개 조합) ===\n'))

        # 1. 모든 조합 생성
        self.stdout.write('[1] 모든 조합 생성 중...')
        vibes = ['modern', 'cozy', 'pop', 'luxury']
        household_sizes = [1, 2, 3, 4, 5]
        main_spaces = ['living', 'kitchen', 'dressing', 'bedroom']
        has_pet_values = [False, True]  # False, True
        priorities = ['design', 'tech', 'eco', 'value']
        budget_levels = ['low', 'medium', 'high']

        # 모든 조합 생성
        all_combinations = list(product(
            vibes,
            household_sizes,
            main_spaces,
            has_pet_values,
            priorities,
            budget_levels
        ))

        total_combinations = len(all_combinations)
        self.stdout.write(f'  - 총 조합 수: {total_combinations:,}개')
        self.stdout.write(f'  - 이론적 최대: {4 * 5 * 4 * 2 * 4 * 3}개')
        
        if total_combinations != 1920:
            self.stdout.write(self.style.WARNING(
                f'  ⚠️  조합 수가 예상과 다릅니다: {total_combinations}개 (예상: 1,920개)'
            ))

        # 2. 기존 데이터 삭제 (옵션)
        if clear_existing:
            self.stdout.write('[2] 기존 데이터 삭제 중...')
            try:
                with get_connection() as conn:
                    with conn.cursor() as cur:
                        cur.execute("DELETE FROM TASTE_CONFIG")
                        deleted_count = cur.rowcount
                        conn.commit()
                        self.stdout.write(f'  - 삭제된 레코드 수: {deleted_count:,}개')
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'  삭제 실패: {str(e)}'))
                return
        else:
            self.stdout.write('[2] 기존 데이터 확인 중...')
            try:
                with get_connection() as conn:
                    with conn.cursor() as cur:
                        cur.execute("SELECT COUNT(*) FROM TASTE_CONFIG")
                        existing_count = cur.fetchone()[0]
                        if existing_count > 0:
                            self.stdout.write(self.style.WARNING(
                                f'  - 기존 레코드 수: {existing_count:,}개 (--clear-existing 옵션으로 삭제 가능)'
                            ))
            except Exception as e:
                self.stdout.write(self.style.WARNING(f'  확인 실패: {str(e)}'))

        # 3. 데이터 삽입
        self.stdout.write('[3] 데이터 삽입 중...')
        success_count = 0
        error_count = 0

        # 배치 단위로 처리
        for batch_start in range(0, total_combinations, batch_size):
            batch_end = min(batch_start + batch_size, total_combinations)
            batch_combinations = all_combinations[batch_start:batch_end]
            
            try:
                with get_connection() as conn:
                    with conn.cursor() as cur:
                        for idx, combo in enumerate(batch_combinations):
                            taste_id = batch_start + idx + 1
                            
                            vibe, household_size, main_space, has_pet, priority, budget_level = combo
                            
                            # description 생성
                            has_pet_str = "반려동물 있음" if has_pet else "반려동물 없음"
                            description = (
                                f"Taste {taste_id}: {vibe}, {household_size}인 가구, "
                                f"{main_space}, {has_pet_str}, {priority}, {budget_level}"
                            )
                            
                            # INSERT 쿼리 실행
                            cur.execute("""
                                INSERT INTO TASTE_CONFIG (
                                    TASTE_ID,
                                    DESCRIPTION,
                                    REPRESENTATIVE_VIBE,
                                    REPRESENTATIVE_HOUSEHOLD_SIZE,
                                    REPRESENTATIVE_MAIN_SPACE,
                                    REPRESENTATIVE_HAS_PET,
                                    REPRESENTATIVE_PRIORITY,
                                    REPRESENTATIVE_BUDGET_LEVEL,
                                    RECOMMENDED_CATEGORIES,
                                    RECOMMENDED_PRODUCTS,
                                    IS_ACTIVE,
                                    AUTO_GENERATED,
                                    CREATED_AT,
                                    UPDATED_AT
                                ) VALUES (
                                    :p_taste_id,
                                    :p_desc,
                                    :p_vibe,
                                    :p_household_size,
                                    :p_main_space,
                                    :p_has_pet,
                                    :p_priority,
                                    :p_budget_level,
                                    NULL,
                                    NULL,
                                    'Y',
                                    'Y',
                                    SYSDATE,
                                    SYSDATE
                                )
                            """, {
                                'p_taste_id': taste_id,
                                'p_desc': description,
                                'p_vibe': vibe,
                                'p_household_size': household_size,
                                'p_main_space': main_space,
                                'p_has_pet': 'Y' if has_pet else 'N',
                                'p_priority': priority,
                                'p_budget_level': budget_level
                            })
                        
                        conn.commit()
                        success_count += len(batch_combinations)
                        
                        if (batch_end % 100 == 0) or (batch_end == total_combinations):
                            self.stdout.write(f'  진행: {batch_end:,}/{total_combinations:,} ({batch_end*100//total_combinations}%)')
                            
            except Exception as e:
                error_count += len(batch_combinations)
                self.stdout.write(self.style.ERROR(
                    f'  배치 {batch_start+1}-{batch_end} 삽입 실패: {str(e)}'
                ))
                import traceback
                self.stdout.write(self.style.ERROR(traceback.format_exc()))

        # 4. 결과 요약
        self.stdout.write(self.style.SUCCESS('\n=== 완료 ===\n'))
        self.stdout.write(f'성공: {success_count:,}개')
        self.stdout.write(f'실패: {error_count:,}개')
        self.stdout.write(f'총 처리: {success_count + error_count:,}개')
        
        # 5. 검증
        self.stdout.write('\n[4] 데이터 검증 중...')
        try:
            with get_connection() as conn:
                with conn.cursor() as cur:
                    # 총 개수 확인
                    cur.execute("SELECT COUNT(*) FROM TASTE_CONFIG")
                    total_count = cur.fetchone()[0]
                    self.stdout.write(f'  - TASTE_CONFIG 총 레코드 수: {total_count:,}개')
                    
                    # representative 필드별 고유 값 확인
                    cur.execute("""
                        SELECT 
                            COUNT(DISTINCT REPRESENTATIVE_VIBE) as vibe_count,
                            COUNT(DISTINCT REPRESENTATIVE_HOUSEHOLD_SIZE) as household_count,
                            COUNT(DISTINCT REPRESENTATIVE_MAIN_SPACE) as main_space_count,
                            COUNT(DISTINCT REPRESENTATIVE_HAS_PET) as has_pet_count,
                            COUNT(DISTINCT REPRESENTATIVE_PRIORITY) as priority_count,
                            COUNT(DISTINCT REPRESENTATIVE_BUDGET_LEVEL) as budget_count
                        FROM TASTE_CONFIG
                    """)
                    row = cur.fetchone()
                    self.stdout.write(f'  - 고유 값 개수:')
                    self.stdout.write(f'    REPRESENTATIVE_VIBE: {row[0]}개')
                    self.stdout.write(f'    REPRESENTATIVE_HOUSEHOLD_SIZE: {row[1]}개')
                    self.stdout.write(f'    REPRESENTATIVE_MAIN_SPACE: {row[2]}개')
                    self.stdout.write(f'    REPRESENTATIVE_HAS_PET: {row[3]}개')
                    self.stdout.write(f'    REPRESENTATIVE_PRIORITY: {row[4]}개')
                    self.stdout.write(f'    REPRESENTATIVE_BUDGET_LEVEL: {row[5]}개')
                    
                    # 중복 조합 확인
                    cur.execute("""
                        SELECT 
                            REPRESENTATIVE_VIBE,
                            REPRESENTATIVE_HOUSEHOLD_SIZE,
                            REPRESENTATIVE_MAIN_SPACE,
                            REPRESENTATIVE_HAS_PET,
                            REPRESENTATIVE_PRIORITY,
                            REPRESENTATIVE_BUDGET_LEVEL,
                            COUNT(*) as cnt
                        FROM TASTE_CONFIG
                        GROUP BY 
                            REPRESENTATIVE_VIBE,
                            REPRESENTATIVE_HOUSEHOLD_SIZE,
                            REPRESENTATIVE_MAIN_SPACE,
                            REPRESENTATIVE_HAS_PET,
                            REPRESENTATIVE_PRIORITY,
                            REPRESENTATIVE_BUDGET_LEVEL
                        HAVING COUNT(*) > 1
                        ORDER BY cnt DESC
                    """)
                    duplicates = cur.fetchall()
                    if duplicates:
                        self.stdout.write(self.style.WARNING(
                            f'  ⚠️  중복된 조합 발견: {len(duplicates)}개'
                        ))
                        for dup in duplicates[:5]:  # 상위 5개만 표시
                            self.stdout.write(f'    {dup[:6]} → {dup[6]}번 반복')
                    else:
                        self.stdout.write(self.style.SUCCESS('  ✓ 모든 조합이 고유함'))
                    
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'  검증 실패: {str(e)}'))

        self.stdout.write(self.style.SUCCESS('\n[OK] 초기화 완료!\n'))

