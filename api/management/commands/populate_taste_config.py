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
from api.utils.ill_suited_category_detector import IllSuitedCategoryDetector
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
                
                # 1. 먼저 ill-suited 카테고리 식별
                from api.utils.taste_category_selector import TasteCategorySelector
                all_categories = TasteCategorySelector.get_available_categories()
                
                # Ill-suited 카테고리 검출
                ill_suited_categories = IllSuitedCategoryDetector.detect_ill_suited_categories(
                    onboarding_data, all_categories
                )
                
                # Ill-suited가 아닌 카테고리만 점수 계산 대상으로
                valid_categories = [cat for cat in all_categories if cat not in ill_suited_categories]
                
                # 2. 각 카테고리의 점수 계산 (ill-suited 제외)
                category_scores = {}
                for category in valid_categories:
                    score = TasteCategorySelector._calculate_category_score(category, onboarding_data)
                    category_scores[category] = score
                
                # Ill-suited 카테고리는 점수 0으로 설정 (참고용)
                for category in ill_suited_categories:
                    category_scores[category] = 0.0
                
                # 점수 기준으로 정렬 (ill-suited 제외, 점수 > 0인 것만)
                valid_category_scores = {cat: score for cat, score in category_scores.items() 
                                        if cat not in ill_suited_categories and score > 0}
                sorted_categories = sorted(
                    valid_category_scores.items(),
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

                # 3. 모든 카테고리 점수 계산 (ill-suited 포함, 참고용)
                # Oracle DB에 없는 카테고리도 포함하여 점수 계산
                all_category_scores = {}
                
                # Oracle DB에 실제 존재하는 카테고리
                for category in all_categories:
                    if category in ill_suited_categories:
                        all_category_scores[category] = 0.0
                    elif category in valid_category_scores:
                        all_category_scores[category] = valid_category_scores[category]
                    else:
                        # 점수가 없는 카테고리는 0점
                        all_category_scores[category] = 0.0
                
                # Oracle DB에 없지만 컬럼이 존재하는 카테고리도 점수 계산
                # (건조기, 워시타워, 로봇청소기, 사운드바, 오븐, 전자레인지 등)
                additional_categories = [
                    '건조기', '워시타워', '로봇청소기', '사운드바', 
                    '오븐', '전자레인지', 'OBJET', 'SIGNATURE'
                ]
                for category in additional_categories:
                    if category not in all_category_scores:
                        # 직접 점수 계산
                        score = TasteCategorySelector._calculate_category_score(category, onboarding_data)
                        all_category_scores[category] = score
                
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
                    'recommended_categories_with_scores': all_category_scores,  # 모든 카테고리별 점수 {"TV": 85.0, "냉장고": 70.0, "반려동물전용": 0.0}
                    'ill_suited_categories': sorted(ill_suited_categories),  # Ill-suited 카테고리 리스트
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
                    self._save_to_oracle(taste_id, config_data, oracle_exists, onboarding_data)
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
    
    def _save_to_normalized_tables(self, cur, taste_id: int, config_data: dict):
        """정규화된 테이블(TASTE_CATEGORY_SCORES, TASTE_RECOMMENDED_PRODUCTS)에 데이터 저장"""
        try:
            # 1. TASTE_CATEGORY_SCORES 테이블 저장
            # 기존 데이터 삭제
            cur.execute("""
                DELETE FROM TASTE_CATEGORY_SCORES WHERE TASTE_ID = :p_taste_id
            """, {'p_taste_id': taste_id})
            
            # 카테고리별 점수 저장
            recommended_categories = config_data.get('recommended_categories', [])
            category_scores = config_data.get('recommended_categories_with_scores', {})
            ill_suited_categories = config_data.get('ill_suited_categories', [])
            
            for category, score in category_scores.items():
                is_recommended = 'Y' if category in recommended_categories else 'N'
                is_ill_suited = 'Y' if category in ill_suited_categories else 'N'
                
                cur.execute("""
                    INSERT INTO TASTE_CATEGORY_SCORES 
                    (TASTE_ID, CATEGORY_NAME, SCORE, IS_RECOMMENDED, IS_ILL_SUITED)
                    VALUES (:p_taste_id, :p_category, :p_score, :p_recommended, :p_ill_suited)
                """, {
                    'p_taste_id': taste_id,
                    'p_category': category,
                    'p_score': float(score) if score is not None else 0.0,
                    'p_recommended': is_recommended,
                    'p_ill_suited': is_ill_suited
                })
            
            # 2. TASTE_RECOMMENDED_PRODUCTS 테이블 저장
            # 기존 데이터 삭제
            cur.execute("""
                DELETE FROM TASTE_RECOMMENDED_PRODUCTS WHERE TASTE_ID = :p_taste_id
            """, {'p_taste_id': taste_id})
            
            # 추천 제품 저장
            recommended_products = config_data.get('recommended_products', {})
            recommended_product_scores = config_data.get('recommended_product_scores', {})
            
            for category, product_ids in recommended_products.items():
                if not isinstance(product_ids, list):
                    continue
                
                scores = recommended_product_scores.get(category, [])
                
                for rank, product_id in enumerate(product_ids, start=1):
                    score = scores[rank - 1] if rank <= len(scores) and scores else None
                    
                    cur.execute("""
                        INSERT INTO TASTE_RECOMMENDED_PRODUCTS
                        (TASTE_ID, CATEGORY_NAME, PRODUCT_ID, SCORE, RANK_ORDER)
                        VALUES (:p_taste_id, :p_category, :p_product_id, :p_score, :p_rank)
                    """, {
                        'p_taste_id': taste_id,
                        'p_category': category,
                        'p_product_id': int(product_id),
                        'p_score': float(score) if score is not None else None,
                        'p_rank': rank
                    })
        except Exception as e:
            # 정규화된 테이블이 없을 수 있으므로 에러를 무시하지 않고 로그만 남김
            self.stdout.write(
                self.style.WARNING(f'정규화된 테이블 저장 실패 (무시됨): {str(e)}')
            )
    
    def _save_to_oracle(self, taste_id: int, config_data: dict, is_update: bool, onboarding_data: dict = None):
        """Oracle DB의 TASTE_CONFIG 테이블에 저장"""
        import json
        from datetime import datetime
        
        recommended_categories_json = json.dumps(config_data['recommended_categories'], ensure_ascii=False)
        recommended_categories_with_scores_json = json.dumps(config_data.get('recommended_categories_with_scores', {}), ensure_ascii=False)
        ill_suited_categories_json = json.dumps(config_data.get('ill_suited_categories', []), ensure_ascii=False)
        recommended_products_json = json.dumps(config_data['recommended_products'], ensure_ascii=False)
        
        has_pet_char = 'Y' if config_data.get('representative_has_pet') else 'N'
        is_active_char = 'Y' if config_data.get('is_active', True) else 'N'
        auto_generated_char = 'Y' if config_data.get('auto_generated', False) else 'N'
        
        # 온보딩 데이터가 없으면 config_data에서 재구성
        if onboarding_data is None:
            onboarding_data = {
                'vibe': config_data.get('representative_vibe', 'modern'),
                'household_size': config_data.get('representative_household_size', 2),
                'main_space': config_data.get('representative_main_space', 'living'),
                'has_pet': config_data.get('representative_has_pet', False),
                'priority': config_data.get('representative_priority', 'value'),
                'budget_level': config_data.get('representative_budget_level', 'medium'),
                'cooking': 'sometimes',
                'laundry': 'weekly',
                'media': 'balanced',
                'pyung': 25
            }
        
        # 카테고리명을 Oracle 컬럼명으로 변환 (Oracle DB 실제 카테고리명 → 컬럼명)
        # Oracle DB 실제 카테고리명을 그대로 사용하되, 점수 계산은 정규화된 이름으로 수행
        from api.utils.taste_category_selector import TasteCategorySelector
        
        # Oracle DB 실제 카테고리명 → Oracle 컬럼명 매핑
        # 같은 컬럼에 여러 카테고리가 매핑될 수 있으므로, 역방향으로 처리
        category_column_mapping = {
            # Oracle DB 실제 카테고리명 → Oracle 컬럼명
            'TV': 'TV_SCORE',
            '프로젝터': '프로젝터_SCORE',
            '스탠바이미': '스탠바이미_SCORE',
            '오디오': '사운드바_SCORE',  # 오디오 → 사운드바_SCORE (통합)
            '사운드바': '사운드바_SCORE',
            '냉장고': '냉장고_SCORE',
            '김치냉장고': '김치냉장고_SCORE',
            '세탁': '세탁기_SCORE',  # Oracle DB '세탁' → '세탁기_SCORE'
            '세탁기': '세탁기_SCORE',
            '의류건조기': '건조기_SCORE',  # Oracle DB 실제명 → 건조기_SCORE
            '건조기': '건조기_SCORE',
            '워시콤보': '워시타워_SCORE',  # Oracle DB 실제명 → 워시타워_SCORE
            '워시타워': '워시타워_SCORE',
            '식기세척기': '식기세척기_SCORE',
            '광파오븐전자레인지': '전자레인지_SCORE',  # Oracle DB 실제명 → 전자레인지_SCORE
            '전자레인지': '전자레인지_SCORE',
            '광파오븐': '오븐_SCORE',  # Oracle DB 실제명 → 오븐_SCORE
            '오븐': '오븐_SCORE',
            '에어컨': '에어컨_SCORE',
            '공기청정기': '공기청정기_SCORE',
            '가습기': '가습기_SCORE',
            '제습기': '제습기_SCORE',
            '청소기': '청소기_SCORE',
            '로봇청소기': '청소기_SCORE',  # 로봇청소기 → 청소기_SCORE (통합)
            '정수기': '정수기_SCORE',
            '와인셀러': '와인셀러_SCORE',
            'AIHome': 'AIHOME_SCORE',
            'OBJET': 'OBJET_SCORE',
            'SIGNATURE': 'SIGNATURE_SCORE',
            '의류관리기': '의류관리기_SCORE',
        }
        
        # 모든 카테고리 점수를 준비 (category_column_mapping의 모든 카테고리 포함)
        all_category_scores = config_data.get('recommended_categories_with_scores', {})
        ill_suited_categories = config_data.get('ill_suited_categories', [])
        
        # category_column_mapping의 모든 카테고리에 대해 점수 설정
        category_score_params = {}
        
        # 카테고리별 점수 계산 (Oracle DB에 없는 카테고리도 점수 계산)
        for category, column_name in category_column_mapping.items():
            score = 0.0
            
            # 1. all_category_scores에 해당 카테고리가 있으면 그 점수 사용
            if category in all_category_scores:
                score = all_category_scores[category]
            # 2. 정규화된 카테고리명으로도 체크 (Oracle DB '세탁' → 로직 '세탁기')
            elif TasteCategorySelector._normalize_category_name(category) != category:
                normalized = TasteCategorySelector._normalize_category_name(category)
                if normalized in all_category_scores:
                    score = all_category_scores[normalized]
                # 역방향 체크: all_category_scores의 카테고리를 정규화해서 매칭
                else:
                    found_score = None
                    for db_category, db_score in all_category_scores.items():
                        normalized_db = TasteCategorySelector._normalize_category_name(db_category)
                        if normalized_db == category or normalized_db == normalized:
                            found_score = db_score
                            break
                    score = found_score if found_score is not None else 0.0
            # 3. Oracle DB에 없는 카테고리 (건조기, 워시타워, 로봇청소기, 사운드바 등)
            #    점수 계산 로직을 직접 호출하여 점수 계산
            else:
                # 온보딩 데이터로 직접 점수 계산
                score = TasteCategorySelector._calculate_category_score(category, onboarding_data)
            
            # 4. ill-suited 체크 (실제 Oracle DB 카테고리명 기준)
            if category in ill_suited_categories:
                score = 0.0
            
            # 5. OBJET, SIGNATURE는 브랜드 라인이므로 예산 기반 점수 부여
            if category in ['OBJET', 'SIGNATURE']:
                budget_level = onboarding_data.get('budget_level', 'medium')
                if budget_level in ['high', 'premium', 'luxury']:
                    score = 20.0
                elif budget_level == 'medium':
                    score = 15.0
                else:
                    score = 10.0
            
            # 파라미터명은 언더스코어와 따옴표 제거 (한글 컬럼명 처리)
            clean_name = column_name.lower().replace('_', '').replace('"', '')
            param_name = f"p_{clean_name}"
            category_score_params[param_name] = float(score) if score is not None else 0.0
        
        with get_connection() as conn:
            with conn.cursor() as cur:
                # 동적 UPDATE 쿼리 생성 (카테고리별 점수 컬럼 포함)
                if is_update:
                    update_fields = [
                        "DESCRIPTION = :p_desc",
                        "REPRESENTATIVE_VIBE = :p_vibe",
                        "REPRESENTATIVE_HOUSEHOLD_SIZE = :p_household_size",
                        "REPRESENTATIVE_MAIN_SPACE = :p_main_space",
                        "REPRESENTATIVE_HAS_PET = :p_has_pet",
                        "REPRESENTATIVE_PRIORITY = :p_priority",
                        "REPRESENTATIVE_BUDGET_LEVEL = :p_budget_level",
                        "RECOMMENDED_CATEGORIES = :p_categories",
                        "CATEGORY_SCORES = :p_categories_scores",
                        "ILL_SUITED_CATEGORIES = :p_ill_suited",
                        "RECOMMENDED_PRODUCTS = :p_products",
                        "IS_ACTIVE = :p_is_active",
                        "AUTO_GENERATED = :p_auto_generated",
                        "LAST_SIMULATION_DATE = :p_sim_date",
                        "UPDATED_AT = SYSDATE"
                    ]
                    
                    # 카테고리별 점수 컬럼 추가 (중복 제거: 컬럼명 기준)
                    # 같은 컬럼에 여러 카테고리가 매핑될 수 있으므로 컬럼명을 키로 사용
                    unique_columns = {}
                    for category, column_name in category_column_mapping.items():
                        if column_name not in unique_columns:
                            unique_columns[column_name] = category
                    
                    for column_name in unique_columns.keys():
                        # 한글이 포함된 컬럼명은 큰따옴표로 감싸기
                        quoted_column = f'"{column_name}"' if any(ord(c) > 127 for c in column_name) else column_name
                        clean_name = column_name.lower().replace('_', '').replace('"', '')
                        param_name = f"p_{clean_name}"
                        update_fields.append(f"{quoted_column} = :{param_name}")
                    
                    update_sql = f"""
                        UPDATE TASTE_CONFIG SET
                            {', '.join(update_fields)}
                        WHERE TASTE_ID = :p_taste_id
                    """
                    
                    params = {
                        'p_desc': config_data.get('description', ''),
                        'p_vibe': config_data.get('representative_vibe', ''),
                        'p_household_size': config_data.get('representative_household_size'),
                        'p_main_space': config_data.get('representative_main_space', ''),
                        'p_has_pet': has_pet_char,
                        'p_priority': config_data.get('representative_priority', ''),
                        'p_budget_level': config_data.get('representative_budget_level', ''),
                        'p_categories': recommended_categories_json,
                        'p_categories_scores': recommended_categories_with_scores_json,
                        'p_ill_suited': ill_suited_categories_json,
                        'p_products': recommended_products_json,
                        'p_is_active': is_active_char,
                        'p_auto_generated': auto_generated_char,
                        'p_sim_date': datetime.now(),
                        'p_taste_id': taste_id
                    }
                    params.update(category_score_params)
                    
                    cur.execute(update_sql, params)
                    
                    # 정규화된 테이블에도 데이터 저장
                    self._save_to_normalized_tables(cur, taste_id, config_data)
                else:
                    # INSERT
                    # 동적 INSERT 쿼리 생성 (카테고리별 점수 컬럼 포함)
                    # 컬럼명 중복 제거
                    unique_columns_insert = {}
                    for category, column_name in category_column_mapping.items():
                        if column_name not in unique_columns_insert:
                            unique_columns_insert[column_name] = category
                    
                    insert_columns = [
                        "TASTE_ID", "DESCRIPTION", "REPRESENTATIVE_VIBE",
                        "REPRESENTATIVE_HOUSEHOLD_SIZE", "REPRESENTATIVE_MAIN_SPACE",
                        "REPRESENTATIVE_HAS_PET", "REPRESENTATIVE_PRIORITY",
                        "REPRESENTATIVE_BUDGET_LEVEL", "RECOMMENDED_CATEGORIES",
                        "CATEGORY_SCORES", "ILL_SUITED_CATEGORIES", "RECOMMENDED_PRODUCTS",
                        "IS_ACTIVE", "AUTO_GENERATED", "LAST_SIMULATION_DATE",
                        "CREATED_AT", "UPDATED_AT"
                    ]
                    
                    insert_values = [
                        ":p_taste_id", ":p_desc", ":p_vibe", ":p_household_size", ":p_main_space",
                        ":p_has_pet", ":p_priority", ":p_budget_level", ":p_categories",
                        ":p_categories_scores", ":p_ill_suited", ":p_products",
                        ":p_is_active", ":p_auto_generated", ":p_sim_date",
                        "SYSDATE", "SYSDATE"
                    ]
                    
                    # 카테고리별 점수 컬럼 추가 (모든 카테고리에 대해)
                    for category, column_name in category_column_mapping.items():
                        # 한글이 포함된 컬럼명은 큰따옴표로 감싸기
                        quoted_column = f'"{column_name}"' if any(ord(c) > 127 for c in column_name) else column_name
                        clean_name = column_name.lower().replace('_', '').replace('"', '')
                        param_name = f"p_{clean_name}"
                        insert_columns.append(quoted_column)
                        insert_values.append(f":{param_name}")
                    
                    insert_sql = f"""
                        INSERT INTO TASTE_CONFIG (
                            {', '.join(insert_columns)}
                        ) VALUES (
                            {', '.join(insert_values)}
                        )
                    """
                    
                    params = {
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
                        'p_ill_suited': ill_suited_categories_json,
                        'p_products': recommended_products_json,
                        'p_is_active': is_active_char,
                        'p_auto_generated': auto_generated_char,
                        'p_sim_date': datetime.now()
                    }
                    params.update(category_score_params)
                    
                    cur.execute(insert_sql, params)
                    
                    # 정규화된 테이블에도 데이터 저장
                    self._save_to_normalized_tables(cur, taste_id, config_data)
                
                conn.commit()

