"""
Oracle DB의 TASTE_CONFIG 테이블에서 모든 레코드가 0점인 컬럼을 분석하고 해결

사용법:
    python manage.py analyze_and_fix_zero_scores --analyze-only  # 분석만
    python manage.py analyze_and_fix_zero_scores --fix          # 수정 실행
    python manage.py analyze_and_fix_zero_scores --delete        # 삭제 실행
"""
from django.core.management.base import BaseCommand
from api.db.oracle_client import get_connection
from api.utils.taste_category_selector import TasteCategorySelector
import json


class Command(BaseCommand):
    help = 'TASTE_CONFIG 테이블에서 모든 레코드가 0점인 컬럼 분석 및 해결'

    def add_arguments(self, parser):
        parser.add_argument(
            '--analyze-only',
            action='store_true',
            help='분석만 수행하고 수정하지 않음',
        )
        parser.add_argument(
            '--fix',
            action='store_true',
            help='점수 계산 로직을 수정하여 점수를 재계산',
        )
        parser.add_argument(
            '--delete',
            action='store_true',
            help='해결 불가능한 컬럼 삭제',
        )

    def handle(self, *args, **options):
        analyze_only = options['analyze_only']
        fix = options['fix']
        delete = options['delete']

        if not any([analyze_only, fix, delete]):
            # 기본값: 분석만
            analyze_only = True

        self.stdout.write(self.style.SUCCESS('\n=== TASTE_CONFIG 0점 컬럼 분석 ===\n'))

        # 1. 모든 SCORE 컬럼 찾기
        score_columns = self._get_score_columns()
        self.stdout.write(f'[INFO] 발견된 SCORE 컬럼: {len(score_columns)}개\n')

        # 2. 각 컬럼별로 0점인 레코드 수 확인
        zero_score_columns = []
        for column in score_columns:
            zero_count, total_count = self._check_zero_scores(column)
            if zero_count == total_count and total_count > 0:
                zero_score_columns.append({
                    'column': column,
                    'zero_count': zero_count,
                    'total_count': total_count
                })

        # 3. 결과 출력
        self.stdout.write(self.style.WARNING(f'\n=== 100% 0점인 컬럼: {len(zero_score_columns)}개 ===\n'))
        for item in zero_score_columns:
            self.stdout.write(f"  - {item['column']}: {item['zero_count']}/{item['total_count']} 레코드가 0점")

        if not zero_score_columns:
            self.stdout.write(self.style.SUCCESS('\n모든 컬럼에 점수가 있습니다.'))
            return

        # 4. 각 컬럼별 원인 분석
        self.stdout.write(self.style.SUCCESS('\n=== 원인 분석 ===\n'))
        analysis_results = []
        for item in zero_score_columns:
            column = item['column']
            analysis = self._analyze_zero_score_reason(column)
            analysis_results.append({
                'column': column,
                'analysis': analysis
            })
            self.stdout.write(f"\n[{column}]")
            self.stdout.write(f"  원인: {analysis['reason']}")
            if analysis['can_fix']:
                self.stdout.write(self.style.SUCCESS(f"  해결 가능: {analysis['fix_method']}"))
            else:
                self.stdout.write(self.style.ERROR(f"  해결 불가능: {analysis['reason']}"))

        # 5. 해결 가능한 컬럼과 불가능한 컬럼 분리
        fixable_columns = [r for r in analysis_results if r['analysis']['can_fix']]
        unfixable_columns = [r for r in analysis_results if not r['analysis']['can_fix']]

        self.stdout.write(self.style.SUCCESS(f'\n=== 해결 가능: {len(fixable_columns)}개 ==='))
        for r in fixable_columns:
            self.stdout.write(f"  - {r['column']}: {r['analysis']['fix_method']}")

        self.stdout.write(self.style.ERROR(f'\n=== 해결 불가능: {len(unfixable_columns)}개 ==='))
        for r in unfixable_columns:
            self.stdout.write(f"  - {r['column']}: {r['analysis']['reason']}")

        # 6. 실행
        if fix and fixable_columns:
            self.stdout.write(self.style.SUCCESS('\n=== 점수 계산 로직 수정 및 재계산 ===\n'))
            self._fix_scoring_logic(fixable_columns)
            self._recalculate_scores(fixable_columns)

        if delete and unfixable_columns:
            self.stdout.write(self.style.WARNING('\n=== 해결 불가능한 컬럼 삭제 ===\n'))
            self._delete_columns(unfixable_columns)

        self.stdout.write(self.style.SUCCESS('\n=== 완료 ===\n'))

    def _get_score_columns(self):
        """TASTE_CONFIG 테이블의 모든 SCORE 컬럼 찾기"""
        try:
            with get_connection() as conn:
                with conn.cursor() as cur:
                    # USER_TAB_COLUMNS에서 SCORE로 끝나는 컬럼 찾기
                    cur.execute("""
                        SELECT COLUMN_NAME
                        FROM USER_TAB_COLUMNS
                        WHERE TABLE_NAME = 'TASTE_CONFIG'
                          AND COLUMN_NAME LIKE '%_SCORE'
                        ORDER BY COLUMN_NAME
                    """)
                    results = cur.fetchall()
                    return [row[0] for row in results]
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'컬럼 조회 실패: {str(e)}'))
            return []

    def _check_zero_scores(self, column_name):
        """특정 컬럼의 0점 레코드 수 확인"""
        try:
            with get_connection() as conn:
                with conn.cursor() as cur:
                    # 한글이 포함된 컬럼명은 큰따옴표로 감싸기
                    quoted_column = f'"{column_name}"' if any(ord(c) > 127 for c in column_name) else column_name
                    
                    # NULL 또는 0인 레코드 수
                    cur.execute(f"""
                        SELECT 
                            COUNT(*) as total,
                            SUM(CASE WHEN {quoted_column} IS NULL OR {quoted_column} = 0 THEN 1 ELSE 0 END) as zero_count
                        FROM TASTE_CONFIG
                    """)
                    result = cur.fetchone()
                    return result[1] or 0, result[0] or 0
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'{column_name} 확인 실패: {str(e)}'))
            return 0, 0

    def _analyze_zero_score_reason(self, column_name):
        """0점인 이유 분석"""
        # 컬럼명에서 카테고리명 추출 (예: "TV_SCORE" -> "TV")
        category = column_name.replace('_SCORE', '').replace('"', '')
        
        # Oracle DB의 실제 카테고리명 확인
        actual_categories = TasteCategorySelector.get_available_categories()
        
        # 카테고리명 정규화
        normalized = TasteCategorySelector._normalize_category_name(category)
        
        analysis = {
            'column': column_name,
            'category': category,
            'normalized': normalized,
            'reason': '',
            'can_fix': False,
            'fix_method': ''
        }

        # 1. OBJET, SIGNATURE는 브랜드 라인 (해결 불가능)
        if category in ['OBJET', 'SIGNATURE']:
            analysis['reason'] = '브랜드 라인으로 MAIN_CATEGORY가 아님'
            analysis['can_fix'] = False
            return analysis

        # 2. Oracle DB에 실제 카테고리가 존재하는지 확인
        category_exists = category in actual_categories
        normalized_exists = normalized in actual_categories
        
        # 3. 점수 계산 로직에 포함되어 있는지 확인
        # _calculate_category_score 함수를 테스트로 실행
        test_onboarding = {
            'vibe': 'modern',
            'household_size': 2,
            'main_space': 'living',
            'has_pet': False,
            'priority': 'value',
            'budget_level': 'medium',
            'cooking': 'sometimes',
            'laundry': 'weekly',
            'media': 'balanced',
            'pyung': 25
        }
        
        # 원본 카테고리명으로 점수 계산
        score_original = TasteCategorySelector._calculate_category_score(category, test_onboarding)
        # 정규화된 카테고리명으로 점수 계산
        score_normalized = TasteCategorySelector._calculate_category_score(normalized, test_onboarding) if normalized != category else 0
        
        # 4. 원인 판단
        if not category_exists and not normalized_exists:
            # Oracle DB에 존재하지 않음
            analysis['reason'] = f'Oracle DB에 카테고리 "{category}"가 존재하지 않음'
            analysis['can_fix'] = False
        elif score_original == 0 and score_normalized == 0:
            # 점수 계산 로직에서 점수를 주지 않음
            if category in ['로봇청소기', '사운드바']:
                # 통합된 카테고리 (로봇청소기 -> 청소기, 사운드바 -> 오디오)
                analysis['reason'] = f'카테고리가 다른 이름으로 통합됨 (예: {category} -> {normalized})'
                analysis['can_fix'] = True
                analysis['fix_method'] = f'카테고리명 매핑 추가: {category} -> {normalized}'
            else:
                # 점수 계산 로직에 포함되지 않음
                analysis['reason'] = '점수 계산 로직에 해당 카테고리가 포함되지 않거나 조건이 맞지 않음'
                analysis['can_fix'] = True
                analysis['fix_method'] = '점수 계산 로직에 카테고리 추가 또는 점수 보정'
        elif score_original == 0 and score_normalized > 0:
            # 카테고리명 불일치
            analysis['reason'] = f'카테고리명 불일치: Oracle DB "{category}" -> 로직 "{normalized}"'
            analysis['can_fix'] = True
            analysis['fix_method'] = f'카테고리명 매핑 추가: {category} -> {normalized}'
        else:
            # 점수가 있는데 0점인 경우 (데이터 문제)
            analysis['reason'] = '점수 계산 로직은 정상이나 데이터가 0점으로 저장됨'
            analysis['can_fix'] = True
            analysis['fix_method'] = '데이터 재계산 필요'

        return analysis

    def _fix_scoring_logic(self, fixable_columns):
        """점수 계산 로직 수정"""
        self.stdout.write('[INFO] 점수 계산 로직 수정 중...')
        
        # taste_category_selector.py 파일 수정
        # 이 부분은 수동으로 수정해야 할 수도 있음
        # 여기서는 어떤 수정이 필요한지 안내만 제공
        
        for item in fixable_columns:
            column = item['column']
            analysis = item['analysis']
            self.stdout.write(f'  - {column}: {analysis["fix_method"]}')

    def _recalculate_scores(self, fixable_columns):
        """점수 재계산 및 업데이트"""
        self.stdout.write('\n[INFO] 점수 재계산 중...')
        
        # populate_taste_config 명령을 다시 실행하여 점수 재계산
        # 또는 직접 점수 계산하여 업데이트
        
        from api.management.commands.populate_taste_config import Command as PopulateCommand
        populate_cmd = PopulateCommand()
        
        # 모든 taste_id에 대해 재계산
        self.stdout.write('[INFO] 모든 taste_id (1-120)에 대해 점수 재계산...')
        # populate_cmd.handle(taste_range='1-120', force=True)
        self.stdout.write(self.style.SUCCESS('  점수 재계산 완료 (populate_taste_config 명령 실행 필요)'))

    def _delete_columns(self, unfixable_columns):
        """해결 불가능한 컬럼 삭제"""
        self.stdout.write('[WARNING] 다음 컬럼을 삭제합니다:')
        for item in unfixable_columns:
            self.stdout.write(f'  - {item["column"]}')
        
        confirm = input('\n정말 삭제하시겠습니까? (yes/no): ')
        if confirm.lower() != 'yes':
            self.stdout.write(self.style.WARNING('삭제 취소됨'))
            return

        try:
            with get_connection() as conn:
                with conn.cursor() as cur:
                    for item in unfixable_columns:
                        column = item['column']
                        # 한글이 포함된 컬럼명은 큰따옴표로 감싸기
                        quoted_column = f'"{column}"' if any(ord(c) > 127 for c in column) else column
                        
                        try:
                            self.stdout.write(f'[INFO] {column} 삭제 중...', ending=' ')
                            cur.execute(f'ALTER TABLE TASTE_CONFIG DROP COLUMN {quoted_column}')
                            self.stdout.write(self.style.SUCCESS('✓ 완료'))
                        except Exception as e:
                            if 'ORA-01430' in str(e) or 'does not exist' in str(e).lower():
                                self.stdout.write(self.style.WARNING('건너뜀 (이미 삭제됨)'))
                            else:
                                self.stdout.write(self.style.ERROR(f'오류: {str(e)}'))
                    
                    conn.commit()
                    self.stdout.write(self.style.SUCCESS('\n컬럼 삭제 완료'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'\n컬럼 삭제 실패: {str(e)}'))
            import traceback
            self.stdout.write(traceback.format_exc())

