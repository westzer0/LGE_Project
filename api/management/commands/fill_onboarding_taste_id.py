"""
온보딩 세션의 taste_id를 채우는 명령어
- TASTE_CONFIG 테이블과 매칭 시도
- 매칭 실패 시 계산 방식으로 fallback
- null 값이 나오는 이유를 상세히 분석
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db.models import Q
from api.models import OnboardingSession
from api.services.taste_config_matching_service import TasteConfigMatchingService
from api.services.taste_calculation_service import TasteCalculationService
from api.utils.taste_classifier import taste_classifier
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "온보딩 세션의 taste_id를 채우고 null 값 원인을 분석"

    def add_arguments(self, parser):
        parser.add_argument(
            '--session-id',
            type=str,
            help='특정 세션 ID만 처리'
        )
        parser.add_argument(
            '--status',
            type=str,
            choices=['completed', 'in_progress', 'all'],
            default='completed',
            help='처리할 세션 상태 (기본값: completed)'
        )
        parser.add_argument(
            '--limit',
            type=int,
            default=None,
            help='처리할 최대 세션 수'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='실제로 업데이트하지 않고 확인만 수행'
        )
        parser.add_argument(
            '--analyze-only',
            action='store_true',
            help='분석만 수행하고 업데이트하지 않음'
        )

    def handle(self, *args, **options):
        session_id = options.get('session_id')
        status = options.get('status')
        limit = options.get('limit')
        dry_run = options.get('dry_run')
        analyze_only = options.get('analyze_only')
        
        if dry_run:
            self.stdout.write(self.style.WARNING("[DRY RUN] 실제로는 업데이트하지 않습니다."))
        if analyze_only:
            self.stdout.write(self.style.WARNING("[ANALYZE ONLY] 분석만 수행합니다."))
        
        self.stdout.write(self.style.SUCCESS("=" * 80))
        self.stdout.write(self.style.SUCCESS("온보딩 세션 taste_id 채우기 시작"))
        self.stdout.write(self.style.SUCCESS("=" * 80))
        
        # 세션 조회
        sessions_query = OnboardingSession.objects.all()
        
        if session_id:
            sessions_query = sessions_query.filter(session_id=session_id)
            if not sessions_query.exists():
                self.stdout.write(self.style.ERROR(f"세션을 찾을 수 없습니다: {session_id}"))
                return
        else:
            if status == 'completed':
                sessions_query = sessions_query.filter(status='completed')
            elif status == 'in_progress':
                sessions_query = sessions_query.filter(status='in_progress')
            # status == 'all'이면 필터링하지 않음
        
        # taste_id가 없는 세션만 처리
        sessions_query = sessions_query.filter(
            Q(taste_id__isnull=True) | Q(taste_id=0)
        )
        
        if limit:
            sessions_query = sessions_query[:limit]
        
        sessions = list(sessions_query)
        total_count = len(sessions)
        
        self.stdout.write(f"\n[INFO] 처리할 세션 수: {total_count}")
        if total_count == 0:
            self.stdout.write(self.style.WARNING("처리할 세션이 없습니다."))
            return
        
        # 통계
        stats = {
            'total': total_count,
            'matched_from_taste_config': 0,
            'calculated_fallback': 0,
            'failed': 0,
            'skipped': 0,
            'null_reasons': {}
        }
        
        # 각 세션 처리
        for idx, session in enumerate(sessions, 1):
            self.stdout.write(f"\n[{idx}/{total_count}] 세션 ID: {session.session_id}")
            self.stdout.write(f"  상태: {session.status}, 단계: {session.current_step}")
            
            # 필수 필드 확인
            missing_fields = self._check_required_fields(session)
            if missing_fields:
                reason = f"필수 필드 누락: {', '.join(missing_fields)}"
                self.stdout.write(self.style.WARNING(f"  ⚠️ {reason}"))
                stats['failed'] += 1
                stats['null_reasons'][reason] = stats['null_reasons'].get(reason, 0) + 1
                continue
            
            # 1. TASTE_CONFIG 매칭 시도
            taste_id = None
            match_method = None
            
            try:
                taste_config_data = TasteConfigMatchingService.get_taste_config_by_onboarding(session)
                if taste_config_data and taste_config_data.get('taste_id'):
                    taste_id = taste_config_data['taste_id']
                    match_method = 'TASTE_CONFIG 매칭'
                    self.stdout.write(self.style.SUCCESS(f"  ✅ TASTE_CONFIG 매칭 성공: taste_id={taste_id}"))
                    stats['matched_from_taste_config'] += 1
            except Exception as e:
                self.stdout.write(self.style.WARNING(f"  ⚠️ TASTE_CONFIG 매칭 중 오류: {e}"))
                logger.error(f"TasteConfig 매칭 오류 (session_id={session.session_id}): {e}", exc_info=True)
            
            # 2. 매칭 실패 시 계산 방식으로 fallback
            if not taste_id:
                try:
                    # 온보딩 데이터 준비
                    onboarding_data = self._prepare_onboarding_data(session)
                    taste_id = taste_classifier.calculate_taste_from_onboarding(onboarding_data)
                    
                    # taste_id 검증 (1-1920 범위)
                    taste_id = int(taste_id)
                    if taste_id < 1:
                        taste_id = 1
                    elif taste_id > 1920:
                        taste_id = 1920
                    
                    match_method = '계산 방식 (fallback)'
                    self.stdout.write(self.style.SUCCESS(f"  ✅ 계산 방식으로 taste_id 생성: {taste_id}"))
                    stats['calculated_fallback'] += 1
                except Exception as e:
                    reason = f"계산 방식 오류: {str(e)}"
                    self.stdout.write(self.style.ERROR(f"  ❌ {reason}"))
                    stats['failed'] += 1
                    stats['null_reasons'][reason] = stats['null_reasons'].get(reason, 0) + 1
                    continue
            
            # 3. taste_id 저장
            if taste_id and not analyze_only and not dry_run:
                session.taste_id = taste_id
                session.save()
                self.stdout.write(f"  💾 taste_id 저장 완료: {taste_id} (방법: {match_method})")
                
                # Oracle DB에도 업데이트
                try:
                    from api.services.onboarding_db_service import OnboardingDBService
                    OnboardingDBService.create_or_update_session(
                        session_id=str(session.session_id),
                        current_step=session.current_step,
                        status=session.status,
                        vibe=session.vibe,
                        household_size=session.household_size,
                        housing_type=session.housing_type,
                        pyung=session.pyung,
                        priority=session.priority,
                        budget_level=session.budget_level,
                        has_pet=session.has_pet,
                        taste_id=taste_id,
                    )
                    self.stdout.write(f"  💾 Oracle DB 업데이트 완료")
                except Exception as e:
                    self.stdout.write(self.style.WARNING(f"  ⚠️ Oracle DB 업데이트 실패: {e}"))
            elif analyze_only:
                self.stdout.write(f"  📊 분석 결과: taste_id={taste_id} (방법: {match_method})")
        
        # 최종 통계 출력
        self.stdout.write("\n" + "=" * 80)
        self.stdout.write(self.style.SUCCESS("처리 완료 - 통계"))
        self.stdout.write("=" * 80)
        self.stdout.write(f"  전체 처리: {stats['total']}")
        self.stdout.write(self.style.SUCCESS(f"  ✅ TASTE_CONFIG 매칭 성공: {stats['matched_from_taste_config']}"))
        self.stdout.write(self.style.SUCCESS(f"  ✅ 계산 방식 성공: {stats['calculated_fallback']}"))
        self.stdout.write(self.style.ERROR(f"  ❌ 실패: {stats['failed']}"))
        
        if stats['null_reasons']:
            self.stdout.write(f"\n[NULL 값 원인 분석]")
            for reason, count in sorted(stats['null_reasons'].items(), key=lambda x: x[1], reverse=True):
                self.stdout.write(f"  - {reason}: {count}건")
        
        # TASTE_CONFIG 매칭 실패 원인 분석
        if stats['matched_from_taste_config'] < stats['total']:
            self._analyze_matching_failures(sessions)
    
    def _check_required_fields(self, session):
        """필수 필드 확인 및 복원"""
        missing = []
        
        if not session.vibe:
            missing.append('vibe')
        if session.household_size is None:
            missing.append('household_size')
        
        # has_pet이 None이면 recommendation_result에서 복원 시도
        if session.has_pet is None:
            if session.recommendation_result and isinstance(session.recommendation_result, dict):
                if 'has_pet' in session.recommendation_result:
                    session.has_pet = session.recommendation_result['has_pet']
                    session.save(update_fields=['has_pet'])
                elif 'pet' in session.recommendation_result:
                    pet_value = session.recommendation_result['pet']
                    session.has_pet = (pet_value == 'yes')
                    session.save(update_fields=['has_pet'])
                else:
                    missing.append('has_pet')
            else:
                missing.append('has_pet')
        
        if not session.priority:
            missing.append('priority')
        if not session.budget_level:
            missing.append('budget_level')
        
        return missing
    
    def _prepare_onboarding_data(self, session):
        """세션 데이터를 온보딩 데이터 형식으로 변환"""
        onboarding_data = {
            'vibe': session.vibe,
            'household_size': session.household_size,
            'housing_type': session.housing_type or 'apartment',
            'pyung': session.pyung or 25,
            'budget_level': session.budget_level,
            'has_pet': session.has_pet or False,
        }
        
        # priority 처리
        if isinstance(session.priority, list):
            onboarding_data['priority'] = session.priority
        elif session.priority:
            onboarding_data['priority'] = [session.priority]
        else:
            onboarding_data['priority'] = ['value']
        
        # main_space 처리
        if session.recommendation_result and isinstance(session.recommendation_result, dict):
            main_space = session.recommendation_result.get('main_space', [])
            if isinstance(main_space, list):
                onboarding_data['main_space'] = main_space
            elif main_space:
                onboarding_data['main_space'] = [main_space]
            else:
                onboarding_data['main_space'] = []
        
        # 생활 패턴
        if session.cooking:
            onboarding_data['cooking'] = session.cooking
        if session.laundry:
            onboarding_data['laundry'] = session.laundry
        if session.media:
            onboarding_data['media'] = session.media
        
        return onboarding_data
    
    def _analyze_matching_failures(self, sessions):
        """TASTE_CONFIG 매칭 실패 원인 분석"""
        self.stdout.write(f"\n[TASTE_CONFIG 매칭 실패 원인 분석]")
        
        from api.db.oracle_client import get_connection
        
        failure_reasons = {
            'vibe_mismatch': 0,
            'household_size_mismatch': 0,
            'has_pet_mismatch': 0,
            'priority_mismatch': 0,
            'budget_level_mismatch': 0,
            'no_matching_combinations': 0,
        }
        
        try:
            with get_connection() as conn:
                with conn.cursor() as cur:
                    for session in sessions:
                        if session.taste_id:
                            continue  # 이미 taste_id가 있는 세션은 건너뜀
                        
                        # TASTE_CONFIG에서 각 조건별로 몇 개나 있는지 확인
                        conditions = {
                            'vibe': session.vibe,
                            'household_size': session.household_size,
                            'has_pet': 'Y' if session.has_pet else 'N',
                            'priority': session.priority,
                            'budget_level': session.budget_level,
                        }
                        
                        # priority 매핑
                        priority_mapping = {
                            'design': 'design',
                            'ai_smart': 'tech',
                            'energy': 'eco',
                            'cost_effective': 'value',
                            'tech': 'tech',
                            'eco': 'eco',
                            'value': 'value',
                        }
                        if isinstance(conditions['priority'], list) and len(conditions['priority']) > 0:
                            priority_first = conditions['priority'][0]
                        else:
                            priority_first = conditions['priority'] if conditions['priority'] else 'value'
                        mapped_priority = priority_mapping.get(priority_first, priority_first)
                        
                        # budget_level 매핑
                        budget_level_mapping = {
                            'budget': 'low',
                            'standard': 'medium',
                            'premium': 'high',
                            'luxury': 'luxury',
                            'low': 'low',
                            'medium': 'medium',
                            'high': 'high',
                        }
                        mapped_budget_level = budget_level_mapping.get(conditions['budget_level'], conditions['budget_level'])
                        
                        # 전체 조건 매칭 확인
                        cur.execute("""
                            SELECT COUNT(*) 
                            FROM TASTE_CONFIG
                            WHERE REPRESENTATIVE_VIBE = :vibe
                              AND REPRESENTATIVE_HOUSEHOLD_SIZE = :household_size
                              AND REPRESENTATIVE_HAS_PET = :has_pet
                              AND REPRESENTATIVE_PRIORITY = :priority
                              AND REPRESENTATIVE_BUDGET_LEVEL = :budget_level
                              AND IS_ACTIVE = 'Y'
                        """, {
                            'vibe': conditions['vibe'],
                            'household_size': int(conditions['household_size']),
                            'has_pet': conditions['has_pet'],
                            'priority': mapped_priority,
                            'budget_level': mapped_budget_level,  # 매핑된 budget_level 사용
                        })
                        full_match = cur.fetchone()[0]
                        
                        if full_match == 0:
                            # 부분 매칭 확인
                            cur.execute("""
                                SELECT 
                                    COUNT(CASE WHEN REPRESENTATIVE_VIBE = :vibe THEN 1 END) as vibe_count,
                                    COUNT(CASE WHEN REPRESENTATIVE_HOUSEHOLD_SIZE = :household_size THEN 1 END) as household_count,
                                    COUNT(CASE WHEN REPRESENTATIVE_HAS_PET = :has_pet THEN 1 END) as pet_count,
                                    COUNT(CASE WHEN REPRESENTATIVE_PRIORITY = :priority THEN 1 END) as priority_count,
                                    COUNT(CASE WHEN REPRESENTATIVE_BUDGET_LEVEL = :budget_level THEN 1 END) as budget_count
                                FROM TASTE_CONFIG
                                WHERE IS_ACTIVE = 'Y'
                            """, {
                                'vibe': conditions['vibe'],
                                'household_size': int(conditions['household_size']),
                                'has_pet': conditions['has_pet'],
                                'priority': mapped_priority,
                                'budget_level': mapped_budget_level,  # 매핑된 budget_level 사용
                            })
                            row = cur.fetchone()
                            vibe_count, household_count, pet_count, priority_count, budget_count = row
                            
                            if vibe_count == 0:
                                failure_reasons['vibe_mismatch'] += 1
                            elif household_count == 0:
                                failure_reasons['household_size_mismatch'] += 1
                            elif pet_count == 0:
                                failure_reasons['has_pet_mismatch'] += 1
                            elif priority_count == 0:
                                failure_reasons['priority_mismatch'] += 1
                            elif budget_count == 0:
                                failure_reasons['budget_level_mismatch'] += 1
                            else:
                                failure_reasons['no_matching_combinations'] += 1
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"  분석 중 오류: {e}"))
            logger.error(f"매칭 실패 분석 오류: {e}", exc_info=True)
            return
        
        for reason, count in sorted(failure_reasons.items(), key=lambda x: x[1], reverse=True):
            if count > 0:
                reason_kr = {
                    'vibe_mismatch': 'VIBE 값 불일치',
                    'household_size_mismatch': 'HOUSEHOLD_SIZE 값 불일치',
                    'has_pet_mismatch': 'HAS_PET 값 불일치',
                    'priority_mismatch': 'PRIORITY 값 불일치',
                    'budget_level_mismatch': 'BUDGET_LEVEL 값 불일치',
                    'no_matching_combinations': '조합이 TASTE_CONFIG에 없음',
                }.get(reason, reason)
                self.stdout.write(f"  - {reason_kr}: {count}건")

