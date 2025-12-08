"""
Taste별 MAIN CATEGORY 선택 로직

각 taste에 따라 Oracle DB의 PRODUCT 테이블 MAIN_CATEGORY 컬럼을 기준으로 N개 선택합니다.
"""
from typing import List, Dict
from api.utils.taste_classifier import taste_classifier
from api.db.oracle_client import get_connection


class TasteCategorySelector:
    """
    Taste별로 MAIN CATEGORY를 선택하는 클래스
    
    Oracle DB의 PRODUCT 테이블 MAIN_CATEGORY 컬럼 값을 기준으로 동적으로 카테고리를 가져옵니다.
    """
    
    # 실제 Oracle DB에서 카테고리 목록을 가져오는 메서드
    @staticmethod
    def get_available_categories() -> List[str]:
        """
        Oracle DB의 PRODUCT 테이블에서 실제 존재하는 MAIN_CATEGORY 목록 가져오기
        Oracle DB 연결 실패 시 Django Product 모델에서 가져오기 (Fallback)
        
        Returns:
            활성 제품이 있는 카테고리 리스트 (제품 수 많은 순서)
        """
        try:
            with get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT MAIN_CATEGORY, COUNT(*) as cnt
                        FROM PRODUCT
                        WHERE MAIN_CATEGORY IS NOT NULL
                          AND STATUS = '판매중'
                          AND PRICE > 0
                          AND PRICE IS NOT NULL
                        GROUP BY MAIN_CATEGORY
                        ORDER BY cnt DESC
                    """)
                    results = cur.fetchall()
                    return [row[0] for row in results]
        except Exception as e:
            # Oracle DB 연결 실패 시 Django Product 모델에서 가져오기
            from api.models import Product
            from api.utils.category_mapping import DJANGO_CATEGORY_TO_MAIN_CATEGORIES
            from django.db.models import Count
            
            # Django Product에서 실제 존재하는 MAIN_CATEGORY 추출
            categories = set()
            products = Product.objects.filter(is_active=True, price__gt=0)
            
            for product in products:
                if hasattr(product, 'spec') and product.spec and product.spec.spec_json:
                    import json
                    try:
                        spec_data = json.loads(product.spec.spec_json)
                        main_cat = spec_data.get('MAIN_CATEGORY', '').strip()
                        if main_cat:
                            categories.add(main_cat)
                    except:
                        pass
                
                # spec이 없으면 Django category를 MAIN_CATEGORY로 매핑
                if not categories:
                    django_cat = product.category
                    main_cats = DJANGO_CATEGORY_TO_MAIN_CATEGORIES.get(django_cat, [])
                    if main_cats:
                        categories.add(main_cats[0])  # 첫 번째 MAIN_CATEGORY 사용
            
            # 기본 카테고리 목록 (fallback)
            if not categories:
                categories = {'TV', '냉장고', '에어컨', '세탁기', '청소기', '공기청정기'}
            
            # 제품 수 기준으로 정렬 (간단하게)
            return sorted(list(categories))
    
    @staticmethod
    def get_essential_categories() -> List[str]:
        """
        필수 카테고리 가져오기 (제품 수가 많은 상위 카테고리)
        
        필수 카테고리: TV, 냉장고, 에어컨, 세탁 (제품 수 기준 상위 3-4개)
        
        Returns:
            필수 카테고리 리스트
        """
        all_categories = TasteCategorySelector.get_available_categories()
        
        # 필수 카테고리 우선순위 (제품 수가 많은 순서)
        essential_priority = ['TV', '냉장고', '에어컨', '세탁']
        
        essential = []
        for cat in essential_priority:
            if cat in all_categories:
                essential.append(cat)
                if len(essential) >= 3:  # 최소 3개
                    break
        
        # 부족하면 제품 수 많은 순서대로 추가
        for cat in all_categories:
            if cat not in essential and len(essential) < 4:
                essential.append(cat)
        
        return essential
    
    @staticmethod
    def select_categories_for_taste(taste_id: int, onboarding_data: Dict, num_categories: int = None) -> List[str]:
        """
        Taste별로 MAIN CATEGORY를 선택
        모든 카테고리에 점수를 매기고 점수 기준으로 선택
        
        Args:
            taste_id: 취향 ID
            onboarding_data: 온보딩 데이터
            num_categories: 선택할 카테고리 개수 (None이면 자동 결정, 최소 3개)
        
        Returns:
            선택된 MAIN CATEGORY 리스트 (점수 내림차순 정렬)
        """
        if not onboarding_data:
            onboarding_data = {}
        
        # 1. 모든 사용 가능한 카테고리 가져오기
        all_categories = TasteCategorySelector.get_available_categories()
        
        # 2. 각 카테고리에 대해 점수 계산 (0~100점)
        category_scores = {}
        for category in all_categories:
            score = TasteCategorySelector._calculate_category_score(category, onboarding_data)
            category_scores[category] = score
        
        # 3. 점수 기준으로 정렬 (내림차순)
        sorted_categories = sorted(
            category_scores.items(),
            key=lambda x: (-x[1], x[0])  # 점수 내림차순, 이름 오름차순
        )
        
        # 4. 점수 분포 분석
        if not sorted_categories:
            return []
        
        scores = [score for _, score in sorted_categories]
        max_score = max(scores) if scores else 0
        min_score = min(scores) if scores else 0
        
        # 5. num_categories가 지정되지 않으면 점수 분포에 따라 동적으로 결정
        if num_categories is None:
            # 점수 분포를 분석하여 자연스러운 구분점 찾기
            if len(sorted_categories) > 0:
                selected = []
                prev_score = None
                
                # 점수 분포 분석: 상위 점수 그룹과 하위 점수 그룹의 경계 찾기
                scores_only = [score for _, score in sorted_categories if score > 0]
                if len(scores_only) > 1:
                    # 점수 차이를 계산하여 급격한 하락 지점 찾기
                    score_diffs = []
                    for i in range(len(scores_only) - 1):
                        diff = scores_only[i] - scores_only[i + 1]
                        score_diffs.append((i, diff))
                    
                    # 가장 큰 점수 차이를 찾기
                    if score_diffs:
                        max_diff_idx, max_diff = max(score_diffs, key=lambda x: x[1])
                        # 평균 점수 차이의 2배 이상 차이가 나면 그 지점을 경계로
                        avg_diff = sum(diff for _, diff in score_diffs) / len(score_diffs) if score_diffs else 0
                        threshold = max(avg_diff * 2, max_score * 0.2)  # 최소 최대 점수의 20%
                        
                        # 급격한 하락 지점 찾기
                        cutoff_idx = None
                        for i, diff in score_diffs:
                            if diff >= threshold and i >= 1:  # 최소 2개는 보장
                                cutoff_idx = i + 1
                                break
                        
                        if cutoff_idx:
                            selected = [cat for cat, score in sorted_categories[:cutoff_idx] if score > 0]
                        else:
                            # 급격한 하락이 없으면 점수 분포에 따라 선택
                            # 점수 분포를 더 세밀하게 분석
                            if len(scores_only) >= 2:
                                # 상위 3개 점수의 평균을 기준으로
                                top_3_avg = sum(scores_only[:min(3, len(scores_only))]) / min(3, len(scores_only))
                                # 평균의 30% 이상인 카테고리 선택 (더 관대하게)
                                threshold_score = top_3_avg * 0.3
                                selected = [cat for cat, score in sorted_categories if score >= threshold_score and score > 0]
                                
                                # 너무 많으면 (10개 초과) 상위 10개만
                                if len(selected) > 10:
                                    selected = selected[:10]
                                # 너무 적으면 (2개 미만) 최소 2개 보장
                                elif len(selected) < 2:
                                    selected = [cat for cat, score in sorted_categories[:2] if score > 0]
                            else:
                                selected = [cat for cat, score in sorted_categories if score > 0]
                    else:
                        # 점수가 1개만 있으면 그 1개만
                        selected = [cat for cat, score in sorted_categories[:1] if score > 0]
                else:
                    # 점수가 있는 카테고리가 1개 이하면 그만큼만
                    selected = [cat for cat, score in sorted_categories if score > 0]
                
                # 최소 2개, 최대 10개 보장
                if len(selected) < 2 and len(sorted_categories) >= 2:
                    selected = [cat for cat, score in sorted_categories[:2] if score > 0]
                elif len(selected) > 10:
                    selected = selected[:10]
            else:
                selected = []
        else:
            # 지정된 개수만큼만 선택 (점수 > 0인 것만)
            selected = [cat for cat, score in sorted_categories[:num_categories] if score > 0]
        
        return selected
    
    @staticmethod
    def _normalize_category_name(category: str) -> str:
        """
        Oracle DB의 실제 카테고리명을 점수 계산 로직에서 사용하는 카테고리명으로 정규화
        
        Args:
            category: Oracle DB의 MAIN_CATEGORY명
        
        Returns:
            정규화된 카테고리명
        """
        if not category:
            return category
        
        # 카테고리명 매핑 (Oracle DB → 로직) - 강화된 매핑
        category_mapping = {
            # 세탁 관련
            '세탁': '세탁기',  # Oracle DB '세탁' → 로직 '세탁기'
            
            # 전자레인지/오븐 관련
            '광파오븐전자레인지': '전자레인지',  # Oracle DB → 로직
            '광파오븐': '오븐',  # Oracle DB → 로직
            '전기레인지': '전자레인지',  # Oracle DB → 로직
            
            # 청소 관련
            '로봇청소기': '청소기',  # Oracle DB → 로직 (통합)
            
            # 오디오/사운드 관련
            '사운드바': '오디오',  # Oracle DB → 로직
            
            # 건조 관련
            '의류건조기': '건조기',  # Oracle DB → 로직
            '건조기': '건조기',  # 명시적 매핑
            
            # 워시타워 관련
            '워시콤보': '워시타워',  # Oracle DB → 로직
            '워시타워': '워시타워',  # 명시적 매핑
        }
        
        # 매핑 적용
        normalized = category_mapping.get(category, category)
        
        # 부분 매칭 (카테고리명에 포함된 경우) - 더 정확한 매칭
        if normalized == category:  # 매핑되지 않은 경우
            category_lower = category.lower()
            
            # 세탁 관련
            if '세탁' in category and '세탁기' not in category:
                normalized = '세탁기'
            # 전자레인지/오븐 관련
            elif '전자레인지' in category or '레인지' in category:
                normalized = '전자레인지'
            elif '오븐' in category and '전자레인지' not in category:
                normalized = '오븐'
            # 청소 관련
            elif '청소' in category:
                normalized = '청소기'
            # 오디오/사운드 관련
            elif '오디오' in category or '사운드' in category:
                normalized = '오디오'
            # 건조 관련
            elif '건조' in category:
                normalized = '건조기'
            # 워시타워 관련
            elif '워시' in category and ('타워' in category or '콤보' in category):
                normalized = '워시타워'
        
        return normalized
    
    def _calculate_category_score(category: str, onboarding_data: Dict) -> float:
        """
        카테고리에 대해 점수 계산 (0~100점)
        
        Args:
            category: MAIN_CATEGORY (Oracle DB 실제 카테고리명)
            onboarding_data: 온보딩 데이터
        
        Returns:
            점수 (0~100점, 조건 미부합은 0점)
        """
        score = 0.0
        max_score = 100.0
        
        # 카테고리명 정규화 (Oracle DB → 로직)
        normalized_category = TasteCategorySelector._normalize_category_name(category)
        
        # OBJET, SIGNATURE는 브랜드 라인이므로 기본 점수만 부여
        # 하지만 Zero Score 문제를 해결하기 위해 점수 범위 확대
        if category in ['OBJET', 'SIGNATURE']:
            # 브랜드 라인은 기본 점수만 부여 (15-30점 범위로 확대)
            budget_level = onboarding_data.get('budget_level', 'medium')
            priority = onboarding_data.get('priority', 'value')
            priority_list = priority if isinstance(priority, list) else [priority]
            priority_lower = [p.lower() for p in priority_list]
            
            # 디자인 우선순위면 더 높은 점수
            if 'design' in priority_lower:
                if budget_level in ['high', 'premium', 'luxury']:
                    return 30.0
                elif budget_level == 'medium':
                    return 25.0
                else:
                    return 20.0
            else:
                if budget_level in ['high', 'premium', 'luxury']:
                    return 25.0
                elif budget_level == 'medium':
                    return 20.0
                else:
                    return 15.0
        
        vibe = onboarding_data.get('vibe', 'modern')
        household_size = onboarding_data.get('household_size', 2)
        main_space = onboarding_data.get('main_space', 'living')
        has_pet = onboarding_data.get('has_pet', False) or onboarding_data.get('pet', False)
        priority = onboarding_data.get('priority', 'value')
        budget_level = onboarding_data.get('budget_level', 'medium')
        cooking = onboarding_data.get('cooking', 'sometimes')
        laundry = onboarding_data.get('laundry', 'weekly')
        media = onboarding_data.get('media', 'balanced')
        pyung = onboarding_data.get('pyung', 25)
        
        # 1. main_space 기반 점수 (최대 30점)
        # Oracle DB 실제 카테고리명과 정규화된 카테고리명 모두 포함
        # main_space='living'일 때 세탁 관련 카테고리 점수 상향 (Zero Score 문제 해결)
        space_scores = {
            'living': {
                'TV': 30, '에어컨': 25, '공기청정기': 20, 
                '청소기': 18, '세탁기': 20, '세탁': 20,  # 세탁기 점수 상향 (18 → 20)
                '냉장고': 10, '식기세척기': 3,
                '의류관리기': 18, '오디오': 8, '사운드바': 8,  # 의류관리기 점수 상향 (15 → 18)
                '건조기': 15, '의류건조기': 15,  # 건조기 추가
                '워시타워': 15, '워시콤보': 15,  # 워시타워 추가
            },
            'kitchen': {
                '냉장고': 30, '식기세척기': 25, 
                '전자레인지': 20, '광파오븐전자레인지': 20,  # Oracle DB 실제명 추가
                '오븐': 15, '광파오븐': 15,  # Oracle DB 실제명 추가
                'TV': 5, '에어컨': 3, '공기청정기': 3,
            },
            'dressing': {
                '세탁기': 30, '세탁': 30,  # Oracle DB '세탁' 추가
                '건조기': 25, '의류건조기': 25,  # Oracle DB 실제명 추가
                '워시타워': 20, '워시콤보': 20,  # Oracle DB 실제명 추가
                '의류관리기': 20,  # 점수 상향
                '에어컨': 5, '공기청정기': 3,
            },
            'bedroom': {
                '에어컨': 30, 'TV': 20, '공기청정기': 15, 
                '청소기': 10, '로봇청소기': 10,  # Oracle DB 실제명 추가
                '냉장고': 3, '오디오': 5, '사운드바': 5,  # 추가
            },
            'study': {
                'TV': 25, '에어컨': 20, '공기청정기': 15, 
                '청소기': 5, '로봇청소기': 5,  # Oracle DB 실제명 추가
                '냉장고': 3, '오디오': 8, '사운드바': 8,  # 추가
            },
        }
        
        # 정규화된 카테고리명과 원본 카테고리명 모두 체크
        score += space_scores.get(main_space, {}).get(category, 0)  # 원본 먼저
        if score == 0:
            score += space_scores.get(main_space, {}).get(normalized_category, 0)  # 정규화된 이름
        
        # main_space='living'일 때 세탁 관련 카테고리 추가 점수 부여 (Zero Score 문제 해결)
        if main_space == 'living' and score == 0:
            # 세탁 관련 카테고리 체크 (원본 및 정규화된 이름 모두)
            laundry_categories = ['세탁기', '세탁', '건조기', '의류건조기', '워시타워', '워시콤보', '의류관리기']
            if category in laundry_categories or normalized_category in laundry_categories:
                score += 12  # living일 때도 세탁 관련 카테고리에 기본 점수 부여
        
        # main_space와 무관한 카테고리도 기본 점수 부여 (다양성 확보)
        if score == 0:
            score += 2  # 기본 점수 2점으로 상향
        
        # 2. household_size 기반 점수 (최대 20점)
        # 정규화된 카테고리명과 원본 모두 체크
        category_check_list = [category, normalized_category]
        
        if household_size == 1:
            if any(c in ['TV', '냉장고', '청소기', '로봇청소기', '에어컨'] for c in category_check_list):
                score += 20
            elif any(c in ['공기청정기', '전자레인지', '광파오븐전자레인지'] for c in category_check_list):
                score += 15
            else:
                score += 2  # 다른 카테고리도 기본 점수
        elif household_size == 2:
            if any(c in ['TV', '냉장고', '세탁기', '세탁', '에어컨'] for c in category_check_list):
                score += 20
            elif any(c in ['공기청정기', '청소기', '로봇청소기', '식기세척기'] for c in category_check_list):
                score += 15
            else:
                score += 2
        elif 3 <= household_size <= 4:
            if any(c in ['냉장고', '세탁기', '세탁', 'TV', '에어컨'] for c in category_check_list):
                score += 20
            elif any(c in ['공기청정기', '청소기', '로봇청소기', '식기세척기', '김치냉장고'] for c in category_check_list):
                score += 15
            else:
                score += 2
        elif household_size >= 5:
            if any(c in ['냉장고', '김치냉장고', '세탁기', '세탁', '워시타워', '워시콤보', '에어컨'] for c in category_check_list):
                score += 20
            elif any(c in ['TV', '공기청정기', '청소기', '로봇청소기', '식기세척기'] for c in category_check_list):
                score += 15
            else:
                score += 2
        
        # 3. has_pet 기반 점수 (최대 15점)
        if has_pet:
            if category in ['공기청정기', '청소기', '에어컨']:
                score += 15
            elif category in ['TV', '냉장고']:
                score += 5
            else:
                score += 1  # 다른 카테고리도 기본 점수
        else:
            # 반려동물 없어도 모든 카테고리에 기본 점수
            score += 1
        
        # 4. budget_level 기반 점수 (최대 15점)
        if budget_level in ['high', 'premium', 'luxury']:
            if any(c in ['TV', '냉장고', '에어컨', '세탁기', '세탁', '공기청정기', '청소기', '로봇청소기'] for c in category_check_list):
                score += 15
            elif any(c in ['와인셀러', '정수기', '제습기', '건조기', '의류건조기', '식기세척기', '의류관리기'] for c in category_check_list):
                score += 12
            elif any(c in ['오디오', '사운드바', '프로젝터'] for c in category_check_list):
                score += 10
            else:
                score += 3  # 다른 카테고리도 기본 점수
        elif budget_level == 'medium':
            if any(c in ['TV', '냉장고', '에어컨', '세탁기', '세탁'] for c in category_check_list):
                score += 15
            elif any(c in ['공기청정기', '청소기', '로봇청소기', '식기세척기'] for c in category_check_list):
                score += 10
            elif any(c in ['오디오', '사운드바', '의류관리기'] for c in category_check_list):
                score += 8
            else:
                score += 2
        else:  # low
            if any(c in ['냉장고', '세탁기', '세탁', 'TV'] for c in category_check_list):
                score += 15
            elif any(c in ['에어컨', '청소기', '로봇청소기'] for c in category_check_list):
                score += 10
            else:
                score += 1
        
        # 5. priority 기반 점수 (최대 10점)
        if priority == 'design':
            if any(c in ['TV', '냉장고', '에어컨'] for c in category_check_list):
                score += 10
            elif any(c in ['의류관리기', '오디오', '사운드바'] for c in category_check_list):
                score += 5
            else:
                score += 1
        elif priority == 'tech':
            if any(c in ['TV', '냉장고', '에어컨', '세탁기', '세탁', '공기청정기', '청소기', '로봇청소기'] for c in category_check_list):
                score += 10
            elif any(c in ['의류관리기', '오디오', '사운드바'] for c in category_check_list):
                score += 5
            else:
                score += 1
        elif priority == 'eco':
            if any(c in ['에어컨', '냉장고', '세탁기', '세탁', '공기청정기'] for c in category_check_list):
                score += 10
            elif any(c in ['청소기', '로봇청소기', '제습기'] for c in category_check_list):
                score += 8
            else:
                score += 1
        else:  # value
            if any(c in ['냉장고', '세탁기', '세탁', 'TV'] for c in category_check_list):
                score += 10
            else:
                score += 1
        
        # 6. cooking 기반 점수 (최대 5점)
        if cooking == 'daily':
            if any(c in ['냉장고', '전자레인지', '광파오븐전자레인지', '식기세척기', '오븐', '광파오븐'] for c in category_check_list):
                score += 5
        elif cooking == 'sometimes':
            if any(c in ['냉장고', '전자레인지', '광파오븐전자레인지'] for c in category_check_list):
                score += 5
        
        # 7. laundry 기반 점수 (최대 10점) - 세탁 빈도에 따라 점수 차등
        # main_space='living'일 때도 세탁 관련 카테고리에 점수 부여 (Zero Score 문제 해결)
        if laundry == 'daily':
            if any(c in ['세탁기', '세탁', '건조기', '의류건조기', '워시타워', '워시콤보'] for c in category_check_list):
                score += 10
            elif any(c in ['의류관리기'] for c in category_check_list):
                score += 8
        elif laundry == 'weekly':
            if any(c in ['세탁기', '세탁'] for c in category_check_list):
                score += 8
            elif any(c in ['건조기', '의류건조기', '워시타워', '워시콤보'] for c in category_check_list):
                score += 5
            elif any(c in ['의류관리기'] for c in category_check_list):
                score += 6  # 의류관리기 점수 상향 (5 → 6)
        elif laundry in ['sometimes', 'monthly']:
            if any(c in ['세탁기', '세탁'] for c in category_check_list):
                score += 5
            elif any(c in ['의류관리기'] for c in category_check_list):
                score += 4  # 의류관리기 점수 상향 (3 → 4)
        
        # main_space='living'이고 laundry가 weekly 이상일 때 세탁 관련 카테고리 추가 점수
        if main_space == 'living' and laundry in ['weekly', 'daily']:
            if any(c in ['세탁기', '세탁', '의류관리기'] for c in category_check_list):
                score += 3  # living일 때 세탁 관련 카테고리 추가 점수
        
        # 8. media 기반 점수 (최대 5점)
        if media in ['high', 'gaming', 'ott']:
            if any(c in ['TV', '프로젝터'] for c in category_check_list):
                score += 5
            elif any(c in ['오디오', '사운드바'] for c in category_check_list):
                score += 3
        
        # 9. pyung 기반 점수 (최대 5점)
        if pyung >= 40:
            if any(c in ['에어컨', '공기청정기', '청소기', '로봇청소기'] for c in category_check_list):
                score += 5
            elif any(c in ['의류관리기'] for c in category_check_list):
                score += 3
        
        # 점수는 최대 100점으로 제한
        return min(score, max_score)
    
    @staticmethod
    def _select_categories_by_onboarding(onboarding_data: Dict) -> List[str]:
        """
        온보딩 질문 기반으로 카테고리 선택
        - 설치 위치(main_space) 기반 카테고리 구분
        - 가구 수, 반려동물, 예산에 따라 카테고리 선택
        
        Args:
            onboarding_data: 온보딩 데이터
        
        Returns:
            선택된 MAIN CATEGORY 리스트
        """
        selected = []
        all_available = TasteCategorySelector.get_available_categories()
        
        # 1. 설치 위치(main_space) 기반 카테고리 선택
        main_space = onboarding_data.get('main_space', 'living')
        space_categories = TasteCategorySelector._get_categories_by_space(main_space, all_available)
        selected.extend(space_categories)
        
        # 2. 가구 수 기반 카테고리 추가
        household_size = onboarding_data.get('household_size', 2)
        household_categories = TasteCategorySelector._get_categories_by_household(household_size, all_available, selected)
        selected.extend(household_categories)
        
        # 3. 반려동물 여부 기반 카테고리 추가
        has_pet = onboarding_data.get('has_pet', False) or onboarding_data.get('pet', False)
        if has_pet:
            pet_categories = TasteCategorySelector._get_categories_by_pet(all_available, selected)
            selected.extend(pet_categories)
        
        # 4. 예산 수준 기반 카테고리 추가 (고예산이면 프리미엄 카테고리)
        budget_level = onboarding_data.get('budget_level', 'medium')
        budget_categories = TasteCategorySelector._get_categories_by_budget(budget_level, all_available, selected)
        selected.extend(budget_categories)
        
        # 5. 생활 패턴 기반 카테고리 추가
        cooking = onboarding_data.get('cooking', 'sometimes')
        laundry = onboarding_data.get('laundry', 'weekly')
        lifestyle_categories = TasteCategorySelector._get_categories_by_lifestyle(
            cooking, laundry, all_available, selected
        )
        selected.extend(lifestyle_categories)
        
        # 6. 추가 카테고리 확보 (다양성 확보를 위해)
        # 선택된 카테고리가 적으면 더 많은 카테고리 추가
        if len(set(selected)) < 8:
            # 우선순위가 낮은 카테고리도 추가
            priority = onboarding_data.get('priority', 'value')
            media = onboarding_data.get('media', 'balanced')
            
            # 미디어 사용 패턴에 따라 추가 카테고리
            if media in ['high', 'gaming', 'ott']:
                if 'TV' not in selected:
                    selected.append('TV')
            
            # 예산 수준에 따라 추가 카테고리
            if budget_level in ['high', 'premium']:
                premium_cats = ['와인셀러', '정수기', '제습기', '건조기']
                for cat in premium_cats:
                    if cat in all_available and cat not in selected:
                        selected.append(cat)
            
            # 가구 수에 따라 추가 카테고리
            if household_size >= 4:
                large_cats = ['김치냉장고', '대형TV', '워시타워']
                for cat in large_cats:
                    if cat in all_available and cat not in selected:
                        selected.append(cat)
        
        # 중복 제거
        return list(dict.fromkeys(selected))
    
    @staticmethod
    def _get_categories_by_space(main_space: str, available: List[str]) -> List[str]:
        """
        설치 위치 기반 카테고리 선택
        
        Args:
            main_space: 주요 공간 (living, kitchen, bedroom 등)
            available: 사용 가능한 카테고리 목록
        
        Returns:
            선택된 카테고리 리스트
        """
        selected = []
        space_lower = main_space.lower()
        
        # 거실/라운지
        if space_lower in ['living', 'lounge', '라운지', '거실']:
            if 'TV' in available:
                selected.append('TV')
            if '냉장고' in available:  # 거실에도 냉장고 필요할 수 있음
                selected.append('냉장고')
            if '에어컨' in available:
                selected.append('에어컨')
            if '공기청정기' in available:
                selected.append('공기청정기')
            if '청소기' in available:
                selected.append('청소기')
            if '세탁기' in available:  # 세탁기도 추가
                selected.append('세탁기')
        
        # 주방
        elif space_lower in ['kitchen', '주방', '키친']:
            if '냉장고' in available:
                selected.append('냉장고')
            if '김치냉장고' in available:
                selected.append('김치냉장고')
            if '전자레인지' in available:
                selected.append('전자레인지')
            if '식기세척기' in available:
                selected.append('식기세척기')
            if '오븐' in available:
                selected.append('오븐')
            if 'TV' in available:  # 주방에도 TV 필요할 수 있음
                selected.append('TV')
            if '에어컨' in available:
                selected.append('에어컨')
        
        # 세탁실/베란다
        elif space_lower in ['laundry', 'balcony', '세탁실', '베란다']:
            if '세탁기' in available:
                selected.append('세탁기')
            if '건조기' in available:
                selected.append('건조기')
            if '워시타워' in available:
                selected.append('워시타워')
            if '냉장고' in available:  # 세탁실 근처에 냉장고 필요할 수 있음
                selected.append('냉장고')
            if 'TV' in available:
                selected.append('TV')
        
        # 기본값: 거실 기준 (최소 3개 이상)
        else:
            if 'TV' in available:
                selected.append('TV')
            if '냉장고' in available:
                selected.append('냉장고')
            if '에어컨' in available:
                selected.append('에어컨')
            if '공기청정기' in available:
                selected.append('공기청정기')
            if '세탁기' in available:
                selected.append('세탁기')
            if '청소기' in available:
                selected.append('청소기')
        
        return selected
    
    @staticmethod
    def _get_categories_by_household(household_size: int, available: List[str], already_selected: List[str]) -> List[str]:
        """
        가구 수 기반 카테고리 선택
        
        Args:
            household_size: 가구 인원수
            available: 사용 가능한 카테고리 목록
            already_selected: 이미 선택된 카테고리
        
        Returns:
            추가 선택된 카테고리 리스트
        """
        selected = []
        available_filtered = [cat for cat in available if cat not in already_selected]
        
        # 대가족(4인 이상)이면 용량이 큰 제품 카테고리 추가
        if household_size >= 4:
            if '김치냉장고' in available_filtered:
                selected.append('김치냉장고')
            if '건조기' in available_filtered:
                selected.append('건조기')
            if '식기세척기' in available_filtered:
                selected.append('식기세척기')
        
        # 소가족(1-2인)이면 컴팩트한 제품 카테고리
        elif household_size <= 2:
            if '미니냉장고' in available_filtered:
                selected.append('미니냉장고')
            if '미니세탁기' in available_filtered:
                selected.append('미니세탁기')
        
        return selected
    
    @staticmethod
    def _get_categories_by_pet(available: List[str], already_selected: List[str]) -> List[str]:
        """
        반려동물 여부 기반 카테고리 선택
        
        Args:
            available: 사용 가능한 카테고리 목록
            already_selected: 이미 선택된 카테고리
        
        Returns:
            추가 선택된 카테고리 리스트
        """
        selected = []
        available_filtered = [cat for cat in available if cat not in already_selected]
        
        # 반려동물이 있으면 공기청정기, 청소기 우선
        if '공기청정기' in available_filtered:
            selected.append('공기청정기')
        if '청소기' in available_filtered:
            selected.append('청소기')
        if '로봇청소기' in available_filtered:
            selected.append('로봇청소기')
        
        return selected
    
    @staticmethod
    def _get_categories_by_budget(budget_level: str, available: List[str], already_selected: List[str]) -> List[str]:
        """
        예산 수준 기반 카테고리 선택 (고예산이면 프리미엄 카테고리)
        
        Args:
            budget_level: 예산 수준 (low, medium, high, premium, luxury)
            available: 사용 가능한 카테고리 목록
            already_selected: 이미 선택된 카테고리
        
        Returns:
            추가 선택된 카테고리 리스트
        """
        selected = []
        available_filtered = [cat for cat in available if cat not in already_selected]
        
        # 고예산이면 프리미엄 카테고리 추가
        if budget_level in ['high', 'premium', 'luxury']:
            if 'OBJET' in available_filtered:
                selected.append('OBJET')
            if 'SIGNATURE' in available_filtered:
                selected.append('SIGNATURE')
            if 'AIHome' in available_filtered:
                selected.append('AIHome')
            if '프로젝터' in available_filtered:
                selected.append('프로젝터')
            if '스탠바이미' in available_filtered:
                selected.append('스탠바이미')
        
        # 저예산이면 필수 카테고리만 (이미 선택된 것들)
        # medium은 기본 카테고리 유지
        
        return selected
    
    @staticmethod
    def _get_categories_by_lifestyle(cooking: str, laundry: str, available: List[str], already_selected: List[str]) -> List[str]:
        """
        생활 패턴 기반 카테고리 선택
        
        Args:
            cooking: 요리 빈도 (often, sometimes, rarely)
            laundry: 세탁 빈도 (daily, weekly, monthly)
            available: 사용 가능한 카테고리 목록
            already_selected: 이미 선택된 카테고리
        
        Returns:
            추가 선택된 카테고리 리스트
        """
        selected = []
        available_filtered = [cat for cat in available if cat not in already_selected]
        
        # 요리를 자주 하면 주방 가전 추가
        if cooking in ['often', 'always', '매일', '자주']:
            if '식기세척기' in available_filtered:
                selected.append('식기세척기')
            if '오븐' in available_filtered:
                selected.append('오븐')
            if '전자레인지' in available_filtered:
                selected.append('전자레인지')
        
        # 세탁을 자주 하면 세탁 관련 가전 추가
        if laundry in ['daily', '매일', '자주']:
            if '건조기' in available_filtered:
                selected.append('건조기')
            if '워시타워' in available_filtered:
                selected.append('워시타워')
        
        return selected
    
    @staticmethod
    def _determine_num_categories(onboarding_data: Dict) -> int:
        """
        온보딩 데이터 기반으로 카테고리 개수 결정
        
        Args:
            onboarding_data: 온보딩 데이터
        
        Returns:
            선택할 카테고리 개수 (최소 3개, 최대 7개)
        """
        household_size = onboarding_data.get('household_size', 2)
        budget_level = onboarding_data.get('budget_level', 'medium')
        pyung = onboarding_data.get('pyung', 25)
        has_pet = onboarding_data.get('has_pet', False) or onboarding_data.get('pet', False)
        
        # 기본값: 3개 (최소 보장)
        num = 3
        
        # 대가족이면 +1
        if household_size >= 4:
            num += 1
        
        # 높은 예산이면 +1
        if budget_level in ['high', 'premium', 'luxury']:
            num += 1
        
        # 큰 평수면 +1
        if pyung >= 40:
            num += 1
        
        # 반려동물이 있으면 +1
        if has_pet:
            num += 1
        
        # 최대 7개로 제한
        return min(num, 7)
    
    @staticmethod
    def _select_additional_categories(
        taste_id: int,
        onboarding_data: Dict,
        already_selected: List[str],
        count: int
    ) -> List[str]:
        """
        추가 카테고리 선택
        
        Args:
            taste_id: 취향 ID
            onboarding_data: 온보딩 데이터
            already_selected: 이미 선택된 카테고리
            count: 추가로 선택할 개수
        
        Returns:
            추가 선택된 카테고리 리스트
        """
        # 실제 DB에 존재하는 카테고리만 사용
        all_available = TasteCategorySelector.get_available_categories()
        available = [cat for cat in all_available if cat not in already_selected]
        
        if not available or count <= 0:
            return []
        
        # 온보딩 데이터 기반 우선순위 결정
        priority_order = TasteCategorySelector._get_category_priority(onboarding_data, available)
        
        # 우선순위대로 선택
        selected = []
        for cat in priority_order:
            if cat in available and len(selected) < count:
                selected.append(cat)
        
        # 부족하면 나머지 랜덤 선택
        remaining = [cat for cat in available if cat not in selected]
        while len(selected) < count and remaining:
            selected.append(remaining.pop(0))
        
        return selected[:count]
    
    @staticmethod
    def _get_category_priority(onboarding_data: Dict, available_categories: List[str]) -> List[str]:
        """
        온보딩 데이터 기반 카테고리 우선순위 결정
        
        Args:
            onboarding_data: 온보딩 데이터
            available_categories: 선택 가능한 카테고리
        
        Returns:
            우선순위가 높은 순서대로 정렬된 카테고리 리스트
        """
        priority = []
        
        # 미디어 사용이 높으면 AIR (에어컨/에어케어) 우선
        media = onboarding_data.get('media', 'balanced')
        if media in ['high', 'gaming'] and 'AIR' in available_categories:
            priority.append('AIR')
        
        # 디자인 우선순위면 OBJET, SIGNATURE 우선
        priority_list = onboarding_data.get('priority', [])
        if isinstance(priority_list, str):
            priority_list = [priority_list]
        priority_lower = [p.lower() for p in priority_list]
        
        if 'design' in priority_lower:
            if 'OBJET' in available_categories:
                priority.append('OBJET')
            if 'SIGNATURE' in available_categories:
                priority.append('SIGNATURE')
        
        # 기술 우선순위면 AI 우선
        if 'tech' in priority_lower or 'ai' in priority_lower:
            if 'AI' in available_categories:
                priority.append('AI')
        
        # 나머지 카테고리 추가 (실제 DB에 존재하는 카테고리만)
        all_available = TasteCategorySelector.get_available_categories()
        for cat in all_available:
            if cat in available_categories and cat not in priority:
                priority.append(cat)
        
        return priority


def get_categories_for_taste(taste_id: int, onboarding_data: Dict = None, num_categories: int = None) -> List[str]:
    """
    Taste별로 MAIN CATEGORY 선택
    
    Args:
        taste_id: 취향 ID
        onboarding_data: 온보딩 데이터
        num_categories: 선택할 카테고리 개수 (None이면 자동 결정)
    
    Returns:
        선택된 MAIN CATEGORY 리스트
    """
    return TasteCategorySelector.select_categories_for_taste(taste_id, onboarding_data, num_categories)

