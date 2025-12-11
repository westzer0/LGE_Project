"""
ONBOARDING_SESSION 테이블의 taste_id를 TASTE_CONFIG와 비교하여 업데이트하는 명령어
"""
from django.core.management.base import BaseCommand
from api.services.onboarding_taste_matching_service import onboarding_taste_matching_service


class Command(BaseCommand):
    help = "ONBOARDING_SESSION 테이블의 TASTE_ID를 TASTE_CONFIG와 비교하여 업데이트"

    def add_arguments(self, parser):
        parser.add_argument(
            '--session-id',
            type=str,
            help='특정 세션 ID만 업데이트 (지정하지 않으면 모든 완료된 세션 업데이트)'
        )
        parser.add_argument(
            '--limit',
            type=int,
            default=None,
            help='처리할 최대 세션 수 (기본값: 전체)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='실제로 업데이트하지 않고 확인만 수행'
        )

    def handle(self, *args, **options):
        session_id = options.get('session_id')
        limit = options.get('limit')
        dry_run = options.get('dry_run')
        
        if dry_run:
            self.stdout.write(self.style.WARNING("[DRY RUN] 실제로는 업데이트하지 않습니다."))
        
        self.stdout.write(self.style.SUCCESS("=" * 60))
        self.stdout.write(self.style.SUCCESS("ONBOARDING_SESSION.TASTE_ID 업데이트 시작"))
        self.stdout.write(self.style.SUCCESS("=" * 60))
        
        try:
            if session_id:
                # 특정 세션만 업데이트
                self.stdout.write(f"\n[INFO] 세션 {session_id}의 TASTE_ID 업데이트 중...")
                if not dry_run:
                    taste_id = onboarding_taste_matching_service.update_taste_id_for_session(session_id)
                    if taste_id:
                        self.stdout.write(self.style.SUCCESS(f"  ✓ TASTE_ID 업데이트 완료: {taste_id}"))
                    else:
                        self.stdout.write(self.style.WARNING(f"  ⚠️ 매칭되는 TASTE_CONFIG를 찾을 수 없습니다."))
                else:
                    self.stdout.write("  [DRY RUN] 업데이트 스킵")
            else:
                # 모든 완료된 세션 업데이트
                self.stdout.write(f"\n[INFO] 모든 완료된 세션의 TASTE_ID 업데이트 중...")
                if limit:
                    self.stdout.write(f"  - 최대 {limit}개 세션 처리")
                
                if not dry_run:
                    result = onboarding_taste_matching_service.update_taste_id_for_all_sessions(limit=limit)
                    self.stdout.write(f"\n[결과]")
                    self.stdout.write(f"  - 처리된 세션 수: {result['total_processed']}")
                    self.stdout.write(self.style.SUCCESS(f"  - 업데이트 성공: {result['updated']}"))
                    if result['failed'] > 0:
                        self.stdout.write(self.style.WARNING(f"  - 업데이트 실패: {result['failed']}"))
                else:
                    self.stdout.write("  [DRY RUN] 업데이트 스킵")
            
            self.stdout.write(self.style.SUCCESS("\n" + "=" * 60))
            self.stdout.write(self.style.SUCCESS("TASTE_ID 업데이트 완료!"))
            self.stdout.write(self.style.SUCCESS("=" * 60))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"\n오류 발생: {str(e)}"))
            import traceback
            self.stdout.write(self.style.ERROR(traceback.format_exc()))
            raise




