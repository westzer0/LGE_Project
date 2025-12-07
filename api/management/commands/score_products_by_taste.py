"""
Taste ID별로 선정된 category별로 product를 scoring하여 상위 3개 선정

사용법:
    python manage.py score_products_by_taste --taste-range 1-120
    python manage.py score_products_by_taste --taste-id 1
"""
from django.core.management.base import BaseCommand
from api.services.taste_based_product_scorer import taste_based_product_scorer
from api.db.oracle_client import get_connection
import json


class Command(BaseCommand):
    help = 'Taste ID별로 선정된 category별로 product를 scoring하여 상위 3개 선정'

    def add_arguments(self, parser):
        parser.add_argument(
            '--taste-range',
            type=str,
            default='1-120',
            help='처리할 taste 범위 (예: 1-120, 1-10)',
        )
        parser.add_argument(
            '--taste-id',
            type=int,
            help='단일 taste_id 처리',
        )
        parser.add_argument(
            '--update-only',
            action='store_true',
            help='기존 데이터만 업데이트',
        )

    def handle(self, *args, **options):
        taste_range = options['taste_range']
        taste_id = options['taste_id']
        update_only = options['update_only']

        self.stdout.write(self.style.SUCCESS('\n=== Taste별 제품 Scoring ===\n'))

        # Taste ID 목록 결정
        if taste_id:
            taste_ids = [taste_id]
        else:
            taste_ids = self._parse_taste_range(taste_range)

        self.stdout.write(f'[범위] Taste {taste_ids[0]} ~ {taste_ids[-1]} (총 {len(taste_ids)}개)\n')

        from datetime import datetime
        start_time = datetime.now()
        
        # 예상 시간 계산 (테스트: Taste 1개 처리 시간 측정)
        import time
        test_start = time.time()
        # 간단한 테스트로 예상 시간 계산 (실제로는 첫 번째 taste 처리 시간으로 추정)
        estimated_time_per_taste = 90  # 초 (기본값, 실제 처리 후 업데이트)
        estimated_total_seconds = estimated_time_per_taste * len(taste_ids)
        estimated_minutes = estimated_total_seconds / 60
        estimated_hours = estimated_minutes / 60
        
        self.stdout.write(
            self.style.WARNING(
                f'\n[예상 소요 시간] '
                f'Taste당 약 {estimated_time_per_taste}초 × {len(taste_ids)}개 = '
                f'약 {estimated_minutes:.1f}분 ({estimated_hours:.1f}시간)\n'
            )
        )
        
        success_count = 0
        error_count = 0

        # 진행 상황 로그 파일 생성
        import os
        from datetime import datetime
        log_dir = os.path.join(os.getcwd(), 'logs')
        os.makedirs(log_dir, exist_ok=True)
        log_file = os.path.join(log_dir, f'score_products_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')
        
        with open(log_file, 'w', encoding='utf-8') as f:
            f.write(f'=== Taste별 제품 Scoring 시작 ===\n')
            f.write(f'시작 시간: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}\n')
            f.write(f'총 처리 대상: {len(taste_ids)}개\n\n')
            f.flush()
        
        self.stdout.write(self.style.SUCCESS(f'\n진행 상황 로그: {log_file}\n'))

        for idx, tid in enumerate(taste_ids, 1):
            try:
                start_time = datetime.now()
                status_msg = f'[{idx}/{len(taste_ids)}] Taste {tid} 처리 중...'
                self.stdout.write(status_msg, ending=' ')
                
                with open(log_file, 'a', encoding='utf-8') as f:
                    f.write(f'{status_msg}\n')
                    f.flush()

                # 1. TasteConfig에서 선정된 category 조회
                taste_config = self._get_taste_config(tid)
                if not taste_config:
                    msg = '건너뜀 (TasteConfig 없음)'
                    self.stdout.write(self.style.WARNING(msg))
                    with open(log_file, 'a', encoding='utf-8') as f:
                        f.write(f'  {msg}\n')
                        f.flush()
                    error_count += 1
                    continue

                recommended_categories = taste_config.get('recommended_categories', [])
                if not recommended_categories:
                    msg = '건너뜀 (선정된 category 없음)'
                    self.stdout.write(self.style.WARNING(msg))
                    with open(log_file, 'a', encoding='utf-8') as f:
                        f.write(f'  {msg}\n')
                        f.flush()
                    error_count += 1
                    continue

                # 2. 각 category별로 제품 scoring 및 상위 3개 선정
                # recommended_categories의 모든 카테고리를 포함 (제품이 없어도 빈 배열로 저장)
                recommended_products_by_category = {}
                recommended_product_scores_by_category = {}
                total_scored = 0

                for category in recommended_categories:
                    # 제품 scoring (상위 3개)
                    scored_products = taste_based_product_scorer.score_products_for_taste(
                        taste_id=tid,
                        category=category,
                        limit=3
                    )

                    if scored_products:
                        # product_id 리스트와 score 리스트로 변환 (0~100 정수)
                        product_ids = [item['product_id'] for item in scored_products]
                        product_scores = [int(item['score']) for item in scored_products]  # 0~100 정수
                        recommended_products_by_category[category] = product_ids
                        recommended_product_scores_by_category[category] = product_scores
                        total_scored += len(scored_products)
                    else:
                        # 제품이 없어도 빈 배열로 저장 (모든 카테고리 포함)
                        recommended_products_by_category[category] = []
                        recommended_product_scores_by_category[category] = []

                # 3. Oracle DB에 업데이트 (모든 카테고리 포함)
                self._update_taste_config_products(
                    tid, 
                    recommended_products_by_category,
                    recommended_product_scores_by_category
                )
                
                elapsed = (datetime.now() - start_time).total_seconds()
                
                # 첫 번째 taste 처리 시간으로 예상 시간 업데이트
                if idx == 1:
                    estimated_time_per_taste = elapsed
                    estimated_total_seconds = estimated_time_per_taste * len(taste_ids)
                    estimated_minutes = estimated_total_seconds / 60
                    estimated_hours = estimated_minutes / 60
                    self.stdout.write(
                        self.style.WARNING(
                            f'\n[예상 소요 시간 업데이트] '
                            f'Taste당 약 {estimated_time_per_taste:.1f}초 × {len(taste_ids)}개 = '
                            f'약 {estimated_minutes:.1f}분 ({estimated_hours:.1f}시간)\n'
                        )
                    )
                
                success_msg = f'완료: {len(recommended_categories)}개 category, {total_scored}개 제품 선정 ({elapsed:.1f}초)'
                self.stdout.write(self.style.SUCCESS(success_msg))
                
                # 평균 처리 시간 계산
                avg_time_per_taste = elapsed / idx if idx > 0 else elapsed
                remaining_tastes = len(taste_ids) - idx
                estimated_remaining_minutes = (remaining_tastes * avg_time_per_taste) / 60
                
                with open(log_file, 'a', encoding='utf-8') as f:
                    f.write(f'  {success_msg}\n')
                    f.write(f'  진행률: {idx}/{len(taste_ids)} ({idx*100//len(taste_ids)}%)\n')
                    f.write(f'  예상 남은 시간: 약 {estimated_remaining_minutes:.1f}분\n\n')
                    f.flush()
                
                success_count += 1

            except Exception as e:
                self.stdout.write(self.style.ERROR(f'오류: {str(e)}'))
                error_count += 1
                import traceback
                self.stdout.write(traceback.format_exc())

        # 결과 요약
        end_time = datetime.now()
        total_time = (end_time - start_time).total_seconds() if 'start_time' in locals() else 0
        
        summary = f'''
=== 완료 ===
성공: {success_count}개
오류: {error_count}개
총 처리: {success_count + error_count}개
총 소요 시간: {total_time/60:.1f}분
완료 시간: {end_time.strftime("%Y-%m-%d %H:%M:%S")}
'''
        self.stdout.write(self.style.SUCCESS(summary))
        
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(summary)
            f.write(f'\n로그 파일: {log_file}\n')
            f.flush()
        
        self.stdout.write(self.style.SUCCESS(f'\n진행 상황 로그: {log_file}\n'))

    def _parse_taste_range(self, taste_range: str) -> list:
        """Taste 범위 파싱"""
        try:
            start, end = map(int, taste_range.split('-'))
            return list(range(start, end + 1))
        except ValueError:
            raise ValueError(f"잘못된 범위 형식: {taste_range}. 예: '1-120'")

    def _get_taste_config(self, taste_id: int) -> dict:
        """Oracle DB에서 TasteConfig 조회"""
        try:
            with get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT 
                            RECOMMENDED_CATEGORIES
                        FROM TASTE_CONFIG
                        WHERE TASTE_ID = :p_taste_id
                    """, {'p_taste_id': taste_id})

                    row = cur.fetchone()
                    if not row:
                        return None

                    # CLOB를 문자열로 읽기
                    rec_cats = row[0]
                    if rec_cats:
                        if hasattr(rec_cats, 'read'):
                            rec_cats = rec_cats.read()
                        recommended_categories = json.loads(rec_cats) if isinstance(rec_cats, str) else []
                    else:
                        recommended_categories = []

                    return {
                        'taste_id': taste_id,
                        'recommended_categories': recommended_categories
                    }
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'TasteConfig 조회 실패: {str(e)}'))
            return None

    def _update_taste_config_products(
        self,
        taste_id: int,
        recommended_products_by_category: dict,
        recommended_product_scores_by_category: dict
    ):
        """Oracle DB의 TASTE_CONFIG 테이블에 추천 제품 및 점수 업데이트"""
        try:
            recommended_products_json = json.dumps(recommended_products_by_category, ensure_ascii=False)
            recommended_product_scores_json = json.dumps(recommended_product_scores_by_category, ensure_ascii=False)

            with get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        UPDATE TASTE_CONFIG
                        SET RECOMMENDED_PRODUCTS = :p_products,
                            RECOMMENDED_PRODUCT_SCORES = :p_scores,
                            UPDATED_AT = SYSDATE
                        WHERE TASTE_ID = :p_taste_id
                    """, {
                        'p_products': recommended_products_json,
                        'p_scores': recommended_product_scores_json,
                        'p_taste_id': taste_id
                    })
                    conn.commit()
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'제품 업데이트 실패: {str(e)}'))
            raise

