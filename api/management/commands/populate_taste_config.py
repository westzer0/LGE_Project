"""
모든 Taste에 대해 카테고리와 추천 제품을 생성하여 TASTE_CONFIG 테이블에 저장
- Django ORM (SQLite/PostgreSQL)
- Oracle DB

사용법:
    python manage.py populate_taste_config
    python manage.py populate_taste_config --taste-range 1-10  # 특정 범위만
    python manage.py populate_taste_config --update-only  # 기존 데이터만 업데이트
"""
import json
from django.core.management.base import BaseCommand
from api.models import TasteConfig
from api.services.recommendation_engine import recommendation_engine
from api.utils.answer_category_mapper import AnswerCategoryMapper
from api.db.oracle_client import get_connection


class Command(BaseCommand):
    help = '모든 taste(1-120)에 대해 카테고리와 추천 제품을 생성하여 TASTE_CONFIG에 저장'

    def add_arguments(self, parser):
        parser.add_argument(
            '--taste-range',
            type=str,
            default='1-120',
            help='처리할 taste 범위 (예: 1-120, 1-10)',
        )
        parser.add_argument(
            '--update-only',
            action='store_true',
            help='기존 데이터만 업데이트 (새로 생성하지 않음)',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='기존 데이터를 강제로 덮어쓰기',
        )

    def handle(self, *args, **options):
        taste_range = options['taste_range']
        update_only = options['update_only']
        force = options['force']

        self.stdout.write(self.style.SUCCESS('\n=== Taste Config 생성 ===\n'))

        # Taste 범위 파싱
        taste_ids = self._parse_taste_range(taste_range)
        self.stdout.write(f'[범위] Taste {taste_ids[0]} ~ {taste_ids[-1]} (총 {len(taste_ids)}개)\n')

        # 온보딩 데이터 생성 함수
        def generate_onboarding_data_for_taste(taste_id: int) -> dict:
            """taste_id에 따라 다양한 onboarding_data 생성"""
            vibes = ['modern', 'cozy', 'pop', 'luxury']
            household_sizes = [1, 2, 3, 4, 5]
            housing_types = ['apartment', 'detached', 'villa', 'officetel', 'studio']
            priorities = ['design', 'tech', 'eco', 'value']
            budget_levels = ['low', 'medium', 'high']
            main_spaces = ['living', 'kitchen', 'dressing', 'bedroom']
            cooking_options = ['daily', 'sometimes', 'rarely']
            laundry_options = ['daily', 'weekly', 'biweekly']
            media_options = ['balanced', 'entertainment', 'minimal']
            
            idx = taste_id - 1
            
            return {
                'vibe': vibes[idx % len(vibes)],
                'household_size': household_sizes[idx % len(household_sizes)],
                'housing_type': housing_types[idx % len(housing_types)],
                'pyung': 20 + (idx % 20),
                'priority': priorities[idx % len(priorities)],
                'budget_level': budget_levels[idx % len(budget_levels)],
                'has_pet': (idx % 3 == 0),
                'cooking': cooking_options[idx % len(cooking_options)],
                'laundry': laundry_options[idx % len(laundry_options)],
                'media': media_options[idx % len(media_options)],
                'main_space': main_spaces[idx % len(main_spaces)],
            }

        success_count = 0
        update_count = 0
        skip_count = 0
        error_count = 0

        for idx, taste_id in enumerate(taste_ids, 1):
            try:
                self.stdout.write(f'[{idx}/{len(taste_ids)}] Taste {taste_id} 처리 중...', ending=' ')

                # 기존 데이터 확인
                existing_config = TasteConfig.objects.filter(taste_id=taste_id).first()
                
                if existing_config and not force:
                    if update_only:
                        # 업데이트 모드: 기존 데이터만 업데이트
                        pass
                    else:
                        self.stdout.write(self.style.WARNING('건너뜀 (이미 존재)'))
                        skip_count += 1
                        continue

                # 온보딩 데이터 생성
                onboarding_data = generate_onboarding_data_for_taste(taste_id)
                
                # 1. 먼저 선택된 카테고리와 점수 가져오기
                from api.utils.taste_category_selector import TasteCategorySelector
                all_categories = TasteCategorySelector.get_available_categories()
                
                # 각 카테고리의 점수 계산
                category_scores = {}
                for category in all_categories:
                    score = TasteCategorySelector._calculate_category_score(category, onboarding_data)
                    category_scores[category] = score
                
                # 점수 기준으로 정렬
                sorted_categories = sorted(
                    category_scores.items(),
                    key=lambda x: (-x[1], x[0])
                )
                
                # 점수가 0보다 큰 카테고리만 선택 (점수 분포에 따라 동적 선택)
                scores_only = [score for _, score in sorted_categories if score > 0]
                if len(scores_only) > 1:
                    # 점수 차이를 계산하여 급격한 하락 지점 찾기
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
                
                selected_categories = [cat for cat, _ in selected_categories_with_scores]
                category_scores_dict = {cat: score for cat, score in selected_categories_with_scores}
                
                if not selected_categories:
                    self.stdout.write(self.style.ERROR('카테고리 선택 실패'))
                    error_count += 1
                    continue
                
                # 2. 사용자 프로필 생성 (선택된 카테고리 포함)
                user_profile = {
                    'vibe': onboarding_data['vibe'],
                    'household_size': onboarding_data['household_size'],
                    'housing_type': onboarding_data['housing_type'],
                    'pyung': onboarding_data['pyung'],
                    'priority': onboarding_data['priority'],
                    'budget_level': onboarding_data['budget_level'],
                    'has_pet': onboarding_data['has_pet'],
                    'cooking': onboarding_data['cooking'],
                    'laundry': onboarding_data['laundry'],
                    'media': onboarding_data['media'],
                    'main_space': onboarding_data['main_space'],
                    'categories': selected_categories,  # 선택된 카테고리 사용
                    'onboarding_data': onboarding_data,
                }

                # 3. 각 카테고리별로 제품 추천
                recommended_products_by_category = {}
                all_recommendations = []
                
                for category in selected_categories:
                    # 각 카테고리별로 추천 엔진 호출
                    user_profile_single = user_profile.copy()
                    user_profile_single['categories'] = [category]  # 단일 카테고리로 필터링
                    
                    result = recommendation_engine.get_recommendations(
                        user_profile=user_profile_single,
                        taste_id=taste_id,
                        limit=10  # 각 카테고리당 최대 10개
                    )
                    
                    if result.get('success'):
                        recommendations = result.get('recommendations', [])
                        all_recommendations.extend(recommendations)
                        
                        # 각 카테고리별 상위 3개 제품만 저장
                        category_products = []
                        for rec in recommendations:
                            product_id = rec.get('product_id')
                            if product_id and product_id not in category_products:
                                category_products.append(product_id)
                                if len(category_products) >= 3:
                                    break
                        
                        if category_products:
                            recommended_products_by_category[category] = category_products
                
                # 최종 카테고리 리스트 (제품이 추천된 카테고리만)
                categories = list(recommended_products_by_category.keys())
                
                # 제품이 추천되지 않은 카테고리도 포함 (최소 3개 보장)
                if len(categories) < 3:
                    for cat in selected_categories:
                        if cat not in categories:
                            categories.append(cat)
                        if len(categories) >= 3:
                            break

                # TasteConfig 저장 또는 업데이트
                # recommended_categories_with_scores: {"TV": 85.0, "냉장고": 70.0, ...} (점수 포함)
                config_data = {
                    'description': f"Taste {taste_id}: {onboarding_data['vibe']}, {onboarding_data['household_size']}인 가구",
                    'representative_vibe': onboarding_data['vibe'],
                    'representative_household_size': onboarding_data['household_size'],
                    'representative_main_space': onboarding_data['main_space'],
                    'representative_has_pet': onboarding_data['has_pet'],
                    'representative_priority': onboarding_data['priority'],
                    'representative_budget_level': onboarding_data['budget_level'],
                    'recommended_categories': sorted(list(categories)),  # 호환성을 위해 배열도 유지
                    'recommended_categories_with_scores': selected_category_scores,  # 카테고리별 점수 {"TV": 85.0, "냉장고": 70.0}
                    'recommended_products': recommended_products_by_category,
                    'auto_generated': True,
                }

                # Django ORM 저장
                if existing_config:
                    for key, value in config_data.items():
                        setattr(existing_config, key, value)
                    existing_config.save()
                    update_count += 1
                    self.stdout.write(self.style.SUCCESS(f'업데이트 완료: {len(categories)}개 카테고리'))
                else:
                    TasteConfig.objects.create(taste_id=taste_id, **config_data)
                    success_count += 1
                    self.stdout.write(self.style.SUCCESS(f'생성 완료: {len(categories)}개 카테고리'))
                
                # Oracle DB에도 저장
                try:
                    # Oracle DB에 기존 데이터가 있는지 확인
                    oracle_exists = self._check_oracle_exists(taste_id)
                    self._save_to_oracle(taste_id, config_data, oracle_exists)
                    self.stdout.write(self.style.SUCCESS(' (Oracle DB 저장 완료)'))
                except Exception as e:
                    import traceback
                    self.stdout.write(self.style.ERROR(f' (Oracle DB 저장 실패: {str(e)})'))
                    self.stdout.write(self.style.ERROR(f'상세: {traceback.format_exc()}'))

            except Exception as e:
                self.stdout.write(self.style.ERROR(f'오류: {str(e)}'))
                error_count += 1

        # 결과 요약
        self.stdout.write(self.style.SUCCESS('\n=== 완료 ===\n'))
        self.stdout.write(f'생성: {success_count}개')
        self.stdout.write(f'업데이트: {update_count}개')
        self.stdout.write(f'건너뜀: {skip_count}개')
        self.stdout.write(f'오류: {error_count}개')
        self.stdout.write(f'총 처리: {success_count + update_count}개\n')

    def _parse_taste_range(self, taste_range: str) -> list:
        """Taste 범위 파싱 (예: "1-120" -> [1, 2, ..., 120])"""
        try:
            start, end = map(int, taste_range.split('-'))
            return list(range(start, end + 1))
        except ValueError:
            raise ValueError(f"잘못된 범위 형식: {taste_range}. 예: '1-120'")
    
    def _check_oracle_exists(self, taste_id: int) -> bool:
        """Oracle DB에 해당 taste_id가 존재하는지 확인"""
        try:
            with get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT COUNT(*) FROM TASTE_CONFIG WHERE TASTE_ID = :p_taste_id", {
                        'p_taste_id': taste_id
                    })
                    count = cur.fetchone()[0]
                    return count > 0
        except Exception:
            return False
    
    def _save_to_oracle(self, taste_id: int, config_data: dict, is_update: bool):
        """Oracle DB의 TASTE_CONFIG 테이블에 저장"""
        import json
        from datetime import datetime
        
        recommended_categories_json = json.dumps(config_data['recommended_categories'], ensure_ascii=False)
        recommended_categories_with_scores_json = json.dumps(config_data.get('recommended_categories_with_scores', {}), ensure_ascii=False)
        recommended_products_json = json.dumps(config_data['recommended_products'], ensure_ascii=False)
        
        has_pet_char = 'Y' if config_data.get('representative_has_pet') else 'N'
        is_active_char = 'Y' if config_data.get('is_active', True) else 'N'
        auto_generated_char = 'Y' if config_data.get('auto_generated', False) else 'N'
        
        with get_connection() as conn:
            with conn.cursor() as cur:
                if is_update:
                    # UPDATE
                    cur.execute("""
                        UPDATE TASTE_CONFIG SET
                            DESCRIPTION = :p_desc,
                            REPRESENTATIVE_VIBE = :p_vibe,
                            REPRESENTATIVE_HOUSEHOLD_SIZE = :p_household_size,
                            REPRESENTATIVE_MAIN_SPACE = :p_main_space,
                            REPRESENTATIVE_HAS_PET = :p_has_pet,
                            REPRESENTATIVE_PRIORITY = :p_priority,
                            REPRESENTATIVE_BUDGET_LEVEL = :p_budget_level,
                            RECOMMENDED_CATEGORIES = :p_categories,
                            CATEGORY_SCORES = :p_categories_scores,
                            RECOMMENDED_PRODUCTS = :p_products,
                            IS_ACTIVE = :p_is_active,
                            AUTO_GENERATED = :p_auto_generated,
                            LAST_SIMULATION_DATE = :p_sim_date,
                            UPDATED_AT = SYSDATE
                        WHERE TASTE_ID = :p_taste_id
                    """, {
                        'p_desc': config_data.get('description', ''),
                        'p_vibe': config_data.get('representative_vibe', ''),
                        'p_household_size': config_data.get('representative_household_size'),
                        'p_main_space': config_data.get('representative_main_space', ''),
                        'p_has_pet': has_pet_char,
                        'p_priority': config_data.get('representative_priority', ''),
                        'p_budget_level': config_data.get('representative_budget_level', ''),
                        'p_categories': recommended_categories_json,
                        'p_categories_scores': recommended_categories_with_scores_json,
                        'p_products': recommended_products_json,
                        'p_is_active': is_active_char,
                        'p_auto_generated': auto_generated_char,
                        'p_sim_date': datetime.now(),
                        'p_taste_id': taste_id
                    })
                else:
                    # INSERT
                    cur.execute("""
                        INSERT INTO TASTE_CONFIG (
                            TASTE_ID, DESCRIPTION, REPRESENTATIVE_VIBE,
                            REPRESENTATIVE_HOUSEHOLD_SIZE, REPRESENTATIVE_MAIN_SPACE,
                            REPRESENTATIVE_HAS_PET, REPRESENTATIVE_PRIORITY,
                            REPRESENTATIVE_BUDGET_LEVEL, RECOMMENDED_CATEGORIES,
                            CATEGORY_SCORES, RECOMMENDED_PRODUCTS,
                            IS_ACTIVE, AUTO_GENERATED, LAST_SIMULATION_DATE,
                            CREATED_AT, UPDATED_AT
                        ) VALUES (
                            :p_taste_id, :p_desc, :p_vibe, :p_household_size, :p_main_space,
                            :p_has_pet, :p_priority, :p_budget_level, :p_categories,
                            :p_categories_scores, :p_products, :p_is_active, :p_auto_generated,
                            :p_sim_date, SYSDATE, SYSDATE
                        )
                    """, {
                        'p_taste_id': taste_id,
                        'p_desc': config_data.get('description', ''),
                        'p_vibe': config_data.get('representative_vibe', ''),
                        'p_household_size': config_data.get('representative_household_size'),
                        'p_main_space': config_data.get('representative_main_space', ''),
                        'p_has_pet': has_pet_char,
                        'p_priority': config_data.get('representative_priority', ''),
                        'p_budget_level': config_data.get('representative_budget_level', ''),
                        'p_categories': recommended_categories_json,
                        'p_categories_scores': recommended_categories_with_scores_json,
                        'p_products': recommended_products_json,
                        'p_is_active': is_active_char,
                        'p_auto_generated': auto_generated_char,
                        'p_sim_date': datetime.now()
                    })
                conn.commit()

