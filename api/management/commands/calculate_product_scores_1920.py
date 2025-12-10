"""
1,920개 taste_id에 대해 recommended_product_scores 계산 및 업데이트

사용법:
    python manage.py calculate_product_scores_1920
    python manage.py calculate_product_scores_1920 --taste-range 1-100
    python manage.py calculate_product_scores_1920 --batch-size 10
"""
import json
from django.core.management.base import BaseCommand
from api.services.recommendation_engine import recommendation_engine
from api.utils.taste_category_selector import TasteCategorySelector
from api.utils.ill_suited_category_detector import IllSuitedCategoryDetector
from api.services.taste_based_product_scorer import taste_based_product_scorer
from api.db.oracle_client import get_connection


class Command(BaseCommand):
    help = '1,920개 taste_id에 대해 recommended_product_scores 계산 및 업데이트'

    def add_arguments(self, parser):
        parser.add_argument(
            '--taste-range',
            type=str,
            default='1-1920',
            help='처리할 taste 범위 (예: 1-1920, 1-100)',
        )
        parser.add_argument(
            '--batch-size',
            type=int,
            default=10,
            help='진행 상황 출력 간격 (기본값: 10)',
        )
        parser.add_argument(
            '--skip-categories',
            action='store_true',
            help='카테고리 선택 단계 건너뛰기 (이미 recommended_categories가 있는 경우)',
        )

    def handle(self, *args, **options):
        taste_range = options['taste_range']
        batch_size = options['batch_size']
        skip_categories = options['skip_categories']

        self.stdout.write(self.style.SUCCESS('\n=== Recommended Product Scores 계산 ===\n'))

        # Taste 범위 파싱
        taste_ids = self._parse_taste_range(taste_range)
        self.stdout.write(f'[범위] Taste {taste_ids[0]} ~ {taste_ids[-1]} (총 {len(taste_ids)}개)\n')

        success_count = 0
        error_count = 0
        skip_count = 0

        # 진행 상황 로그 파일 생성
        import os
        from datetime import datetime
        log_dir = os.path.join(os.getcwd(), 'logs')
        os.makedirs(log_dir, exist_ok=True)
        log_file = os.path.join(log_dir, f'calculate_product_scores_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')
        
        with open(log_file, 'w', encoding='utf-8') as f:
            f.write(f'=== Recommended Product Scores 계산 시작 ===\n')
            f.write(f'시작 시간: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}\n')
            f.write(f'총 처리 대상: {len(taste_ids)}개\n\n')
            f.flush()
        
        self.stdout.write(self.style.SUCCESS(f'\n진행 상황 로그: {log_file}\n'))

        for idx, taste_id in enumerate(taste_ids, 1):
            try:
                start_time = datetime.now()
                status_msg = f'[{idx}/{len(taste_ids)}] Taste {taste_id} 처리 중...'
                self.stdout.write(status_msg, ending=' ')
                
                with open(log_file, 'a', encoding='utf-8') as f:
                    f.write(f'{status_msg}\n')
                    f.flush()

                # 1. TasteConfig에서 representative 필드 조회
                taste_config = self._get_taste_config(taste_id)
                if not taste_config:
                    msg = '건너뜀 (TasteConfig 없음)'
                    self.stdout.write(self.style.WARNING(msg))
                    with open(log_file, 'a', encoding='utf-8') as f:
                        f.write(f'  {msg}\n')
                        f.flush()
                    error_count += 1
                    continue

                # 2. 온보딩 데이터 재구성
                onboarding_data = self._build_onboarding_data(taste_config)
                
                # 3. 카테고리 선택 (skip_categories가 False인 경우)
                recommended_categories = taste_config.get('recommended_categories', [])
                
                if not skip_categories or not recommended_categories:
                    # 카테고리 선택 및 점수 계산
                    all_categories = TasteCategorySelector.get_available_categories()
                    
                    # Ill-suited 카테고리 검출
                    ill_suited_categories = IllSuitedCategoryDetector.detect_ill_suited_categories(
                        onboarding_data, all_categories
                    )
                    
                    # Ill-suited가 아닌 카테고리만 점수 계산
                    valid_categories = [cat for cat in all_categories if cat not in ill_suited_categories]
                    
                    # 각 카테고리의 점수 계산
                    category_scores = {}
                    for category in valid_categories:
                        score = TasteCategorySelector._calculate_category_score(category, onboarding_data)
                        category_scores[category] = score
                    
                    # Ill-suited 카테고리는 점수 0
                    for category in ill_suited_categories:
                        category_scores[category] = 0.0
                    
                    # 점수 기준으로 정렬 및 선택
                    valid_category_scores = {cat: score for cat, score in category_scores.items() 
                                            if cat not in ill_suited_categories and score > 0}
                    sorted_categories = sorted(
                        valid_category_scores.items(),
                        key=lambda x: (-x[1], x[0])
                    )
                    
                    # 동적 카테고리 선택 로직 (populate_taste_config.py와 동일)
                    scores_only = [score for _, score in sorted_categories if score > 0]
                    if len(scores_only) > 1:
                        score_diffs = []
                        for i in range(len(scores_only) - 1):
                            diff = scores_only[i] - scores_only[i + 1]
                            score_diffs.append((i, diff))
                        
                        if score_diffs:
                            max_score = max(scores_only)
                            avg_diff = sum(diff for _, diff in score_diffs) / len(score_diffs) if score_diffs else 0
                            threshold = max(avg_diff * 2, max_score * 0.2)
                            
                            cutoff_idx = None
                            for i, diff in score_diffs:
                                if diff >= threshold and i >= 1:
                                    cutoff_idx = i + 1
                                    break
                            
                            if cutoff_idx:
                                selected_categories_with_scores = sorted_categories[:cutoff_idx]
                            else:
                                top_3_avg = sum(scores_only[:min(3, len(scores_only))]) / min(3, len(scores_only))
                                threshold_score = top_3_avg * 0.3
                                selected_categories_with_scores = [(cat, score) for cat, score in sorted_categories if score >= threshold_score and score > 0]
                                if len(selected_categories_with_scores) > 10:
                                    selected_categories_with_scores = selected_categories_with_scores[:10]
                                elif len(selected_categories_with_scores) < 2:
                                    selected_categories_with_scores = sorted_categories[:2] if len(sorted_categories) >= 2 else sorted_categories
                        else:
                            selected_categories_with_scores = sorted_categories[:1] if sorted_categories else []
                    else:
                        selected_categories_with_scores = [(cat, score) for cat, score in sorted_categories if score > 0]
                    
                    if len(selected_categories_with_scores) < 2 and len(sorted_categories) >= 2:
                        selected_categories_with_scores = sorted_categories[:2]
                    elif len(selected_categories_with_scores) > 10:
                        selected_categories_with_scores = selected_categories_with_scores[:10]
                    
                    recommended_categories = [cat for cat, _ in selected_categories_with_scores]
                    
                    if not recommended_categories:
                        msg = '건너뜀 (카테고리 선택 실패)'
                        self.stdout.write(self.style.WARNING(msg))
                        with open(log_file, 'a', encoding='utf-8') as f:
                            f.write(f'  {msg}\n')
                            f.flush()
                        error_count += 1
                        continue
                
                # 4. 먼저 카테고리를 업데이트 (제품 scoring 전에 필요)
                self._update_taste_config_categories(taste_id, recommended_categories)
                
                # 5. 각 카테고리별로 제품 scoring 및 상위 3개 선정
                recommended_products_by_category = {}
                recommended_product_scores_by_category = {}
                total_scored = 0

                for category in recommended_categories:
                    # 제품 scoring (상위 3개)
                    scored_products = taste_based_product_scorer.score_products_for_taste(
                        taste_id=taste_id,
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
                        # 제품이 없어도 빈 배열로 저장
                        recommended_products_by_category[category] = []
                        recommended_product_scores_by_category[category] = []

                # 6. Oracle DB에 제품 및 점수 업데이트
                self._update_taste_config_products(
                    taste_id,
                    recommended_products_by_category,
                    recommended_product_scores_by_category
                )
                
                elapsed = (datetime.now() - start_time).total_seconds()
                
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

                # 배치 단위로 진행 상황 출력
                if idx % batch_size == 0:
                    self.stdout.write(
                        self.style.WARNING(
                            f'\n[진행 상황] {idx}/{len(taste_ids)} ({idx*100//len(taste_ids)}%) 완료, '
                            f'예상 남은 시간: 약 {estimated_remaining_minutes:.1f}분\n'
                        )
                    )

            except Exception as e:
                msg = f'오류: {str(e)}'
                self.stdout.write(self.style.ERROR(msg))
                error_count += 1
                import traceback
                with open(log_file, 'a', encoding='utf-8') as f:
                    f.write(f'  {msg}\n')
                    f.write(f'{traceback.format_exc()}\n')
                    f.flush()

        # 결과 요약
        end_time = datetime.now()
        total_time = (end_time - start_time).total_seconds() if 'start_time' in locals() else 0
        
        summary = f'''
=== 완료 ===
성공: {success_count}개
오류: {error_count}개
건너뜀: {skip_count}개
총 처리: {success_count + error_count + skip_count}개
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
            raise ValueError(f"잘못된 범위 형식: {taste_range}. 예: '1-1920'")

    def _get_taste_config(self, taste_id: int) -> dict:
        """Oracle DB에서 TasteConfig 조회"""
        try:
            with get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT 
                            TASTE_ID,
                            REPRESENTATIVE_VIBE,
                            REPRESENTATIVE_HOUSEHOLD_SIZE,
                            REPRESENTATIVE_MAIN_SPACE,
                            REPRESENTATIVE_HAS_PET,
                            REPRESENTATIVE_PRIORITY,
                            REPRESENTATIVE_BUDGET_LEVEL,
                            RECOMMENDED_CATEGORIES
                        FROM TASTE_CONFIG
                        WHERE TASTE_ID = :p_taste_id
                    """, {'p_taste_id': taste_id})

                    row = cur.fetchone()
                    if not row:
                        return None

                    # RECOMMENDED_CATEGORIES 파싱
                    recommended_categories = []
                    if row[7]:  # RECOMMENDED_CATEGORIES CLOB
                        try:
                            rec_cats = row[7]
                            if hasattr(rec_cats, 'read'):
                                rec_cats = rec_cats.read()
                            if rec_cats:
                                recommended_categories = json.loads(rec_cats) if isinstance(rec_cats, str) else []
                        except (json.JSONDecodeError, AttributeError):
                            pass

                    return {
                        'taste_id': row[0],
                        'representative_vibe': row[1],
                        'representative_household_size': row[2],
                        'representative_main_space': row[3],
                        'representative_has_pet': row[4] == 'Y' if row[4] else False,
                        'representative_priority': row[5],
                        'representative_budget_level': row[6],
                        'recommended_categories': recommended_categories
                    }
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'TasteConfig 조회 실패: {str(e)}'))
            return None

    def _build_onboarding_data(self, taste_config: dict) -> dict:
        """TasteConfig의 representative 필드로부터 onboarding_data 재구성"""
        # 기본값 설정
        housing_types = ['apartment', 'detached', 'villa', 'officetel', 'studio']
        cooking_options = ['daily', 'sometimes', 'rarely']
        laundry_options = ['daily', 'weekly', 'biweekly']
        media_options = ['balanced', 'entertainment', 'minimal']
        
        # taste_id 기반으로 일관된 기본값 생성
        taste_id = taste_config['taste_id']
        idx = taste_id - 1
        
        return {
            'vibe': taste_config.get('representative_vibe', 'modern'),
            'household_size': taste_config.get('representative_household_size', 2),
            'housing_type': housing_types[idx % len(housing_types)],
            'pyung': 20 + (idx % 20),
            'priority': taste_config.get('representative_priority', 'value'),
            'budget_level': taste_config.get('representative_budget_level', 'medium'),
            'has_pet': taste_config.get('representative_has_pet', False),
            'cooking': cooking_options[idx % len(cooking_options)],
            'laundry': laundry_options[idx % len(laundry_options)],
            'media': media_options[idx % len(media_options)],
            'main_space': taste_config.get('representative_main_space', 'living'),
        }

    def _update_taste_config_categories(self, taste_id: int, recommended_categories: list):
        """Oracle DB의 TASTE_CONFIG 테이블에 추천 카테고리만 먼저 업데이트"""
        try:
            recommended_categories_json = json.dumps(recommended_categories, ensure_ascii=False)

            with get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        UPDATE TASTE_CONFIG
                        SET RECOMMENDED_CATEGORIES = :p_categories,
                            UPDATED_AT = SYSDATE
                        WHERE TASTE_ID = :p_taste_id
                    """, {
                        'p_categories': recommended_categories_json,
                        'p_taste_id': taste_id
                    })
                    conn.commit()
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'카테고리 업데이트 실패: {str(e)}'))
            raise

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
                    # RECOMMENDED_PRODUCT_SCORES 컬럼이 있는지 확인
                    try:
                        cur.execute("""
                            SELECT COLUMN_NAME 
                            FROM USER_TAB_COLUMNS 
                            WHERE TABLE_NAME = 'TASTE_CONFIG' 
                            AND COLUMN_NAME = 'RECOMMENDED_PRODUCT_SCORES'
                        """)
                        has_scores_column = cur.fetchone() is not None
                    except:
                        has_scores_column = False
                    
                    if has_scores_column:
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
                    else:
                        # 컬럼이 없으면 제품만 업데이트
                        cur.execute("""
                            UPDATE TASTE_CONFIG
                            SET RECOMMENDED_PRODUCTS = :p_products,
                                UPDATED_AT = SYSDATE
                            WHERE TASTE_ID = :p_taste_id
                        """, {
                            'p_products': recommended_products_json,
                            'p_taste_id': taste_id
                        })
                        # 컬럼 추가 시도
                        try:
                            cur.execute("ALTER TABLE TASTE_CONFIG ADD RECOMMENDED_PRODUCT_SCORES CLOB")
                            # 다시 업데이트
                            cur.execute("""
                                UPDATE TASTE_CONFIG
                                SET RECOMMENDED_PRODUCT_SCORES = :p_scores,
                                    UPDATED_AT = SYSDATE
                                WHERE TASTE_ID = :p_taste_id
                            """, {
                                'p_scores': recommended_product_scores_json,
                                'p_taste_id': taste_id
                            })
                        except:
                            pass  # 컬럼 추가 실패 시 무시
                    
                    conn.commit()
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'제품 업데이트 실패: {str(e)}'))
            raise

