"""
Taste ID별 제품 Scoring 서비스

각 taste_id별로 선정된 category별로 product.model_code를 3개씩 scoring합니다.

사용하는 테이블/컬럼:
1. PRODUCT 테이블:
   - PRODUCT_ID: 제품 ID
   - MODEL_CODE: 모델 코드
   - PRODUCT_NAME: 제품명
   - PRICE: 제품 가격 (budget_level과 비교)
   - MAIN_CATEGORY: 카테고리 필터링
   - STATUS: '판매중' 필터링

2. PRODUCT_SPEC 테이블:
   - PRODUCT_ID: 제품 ID (PRODUCT 테이블과 조인)
   - SPEC_KEY: 스펙 키 (예: '용량', '화면크기', '해상도', '에너지효율' 등)
   - SPEC_VALUE: 스펙 값
   - SPEC_TYPE: 'common' 타입만 사용 (공통 스펙, 모든 variant에 공통으로 적용되는 스펙)

3. TASTE_CONFIG 테이블:
   - TASTE_ID: Taste ID (1-1920)
   - REPRESENTATIVE_VIBE: 대표 무드 (modern/cozy/pop/luxury)
   - REPRESENTATIVE_HOUSEHOLD_SIZE: 대표 가구 수
   - REPRESENTATIVE_PRIORITY: 대표 우선순위 (design/tech/eco/value)
   - REPRESENTATIVE_BUDGET_LEVEL: 대표 예산 수준 (low/medium/high/premium/luxury)
   - REPRESENTATIVE_HAS_PET: 반려동물 여부 (Y/N)
   - RECOMMENDED_CATEGORIES: 선정된 카테고리 리스트

Scoring 로직:
- PRODUCT_SPEC 테이블에서 SPEC_TYPE='common'인 항목들을 조회
- 각 SPEC_KEY와 SPEC_VALUE를 taste_config의 특성들과 비교
- taste_id별로 다른 scoring 기준 적용 (vibe, household_size, priority, budget_level 등)
- feature 점수 80% + 가격 점수 20%
- 최종 점수: 0~100 정수

결과 저장:
- RECOMMENDED_PRODUCTS: {"TV": [product_id1, product_id2, product_id3], ...}
- RECOMMENDED_PRODUCT_SCORES: {"TV": [score1, score2, score3], ...} (0~100 정수)
"""
import json
import logging
from typing import Dict, List, Optional, Tuple
from collections import defaultdict
from django.db.models import Q
from api.models import Product, ProductSpec, TasteConfig
from api.db.oracle_client import get_connection

logger = logging.getLogger(__name__)


class TasteBasedProductScorer:
    """Taste ID별 제품 Scoring 서비스"""
    
    def __init__(self):
        # Taste별 scoring 기준 캐시
        self.taste_scoring_criteria_cache = {}
        
    def score_products_for_taste(
        self,
        taste_id: int,
        category: str,
        limit: int = 3
    ) -> List[Dict]:
        """
        특정 taste_id와 category에 대해 제품을 scoring하여 상위 N개 반환
        
        Args:
            taste_id: Taste ID (1-1920)
            category: MAIN_CATEGORY (예: 'TV', '냉장고')
            limit: 반환할 제품 수 (기본 3개)
            
        Returns:
            [{'product_id': int, 'model_code': str, 'score': float, ...}, ...]
        """
        try:
            # 1. TasteConfig에서 taste_id 정보 조회
            taste_config = self._get_taste_config(taste_id)
            if not taste_config:
                logger.warning(f"TasteConfig not found for taste_id={taste_id}")
                return []
            
            # 2. 해당 category가 선정된 category인지 확인
            recommended_categories = taste_config.get('recommended_categories', [])
            if category not in recommended_categories:
                logger.warning(f"Category {category} not in recommended categories for taste_id={taste_id}")
                return []
            
            # 3. Oracle DB에서 직접 제품 조회 (Django ORM 의존 제거)
            products_data = self._get_products_from_oracle(category)
            if not products_data:
                logger.warning(f"No products found for category={category}")
                return []
            
            # 4. Taste별 scoring 기준 가져오기
            scoring_criteria = self._get_scoring_criteria_for_taste(taste_id, taste_config, category)
            
            # 5. 각 제품에 대해 scoring
            scored_products = []
            for product_data in products_data:
                score = self._calculate_product_score_from_oracle(
                    product_data=product_data,
                    category=category,
                    scoring_criteria=scoring_criteria,
                    taste_config=taste_config
                )
                
                # 점수가 0이어도 기본 점수 부여 (가격 기반)
                if score == 0:
                    # 가격이 있으면 기본 점수 부여 (10 ~ 50점)
                    price = product_data.get('price', 0.0)
                    if price > 0:
                        # 가격이 낮을수록 높은 점수 (가성비)
                        price_score = self._calculate_price_score_from_data(
                            price=price,
                            budget_level=taste_config.get('representative_budget_level', 'medium')
                        )
                        score = max(10, int(round(price_score * 30)))  # 최소 10점 (0~100 정수)
                
                scored_products.append({
                    'product_id': product_data['product_id'],
                    'model_code': product_data['model_code'],
                    'name': product_data['product_name'],
                    'category': category,
                    'score': score
                })
            
            # 6. 점수 순으로 정렬하여 상위 N개 반환
            scored_products.sort(key=lambda x: x['score'], reverse=True)
            return scored_products[:limit]
            
        except Exception as e:
            logger.error(f"Error scoring products for taste_id={taste_id}, category={category}: {str(e)}", exc_info=True)
            return []
    
    def _get_taste_config(self, taste_id: int) -> Optional[Dict]:
        """Oracle DB에서 TasteConfig 조회 (정규화된 구조 사용)"""
        try:
            with get_connection() as conn:
                with conn.cursor() as cur:
                    # 1. 기본 TASTE_CONFIG 정보 조회 (RECOMMENDED_PRODUCTS, RECOMMENDED_PRODUCT_SCORES 포함)
                    cur.execute("""
                        SELECT 
                            TASTE_ID,
                            REPRESENTATIVE_VIBE,
                            REPRESENTATIVE_HOUSEHOLD_SIZE,
                            REPRESENTATIVE_MAIN_SPACE,
                            REPRESENTATIVE_HAS_PET,
                            REPRESENTATIVE_PRIORITY,
                            REPRESENTATIVE_BUDGET_LEVEL,
                            RECOMMENDED_CATEGORIES,
                            RECOMMENDED_PRODUCTS,
                            RECOMMENDED_PRODUCT_SCORES
                        FROM TASTE_CONFIG
                        WHERE TASTE_ID = :p_taste_id
                    """, {'p_taste_id': taste_id})
                    
                    row = cur.fetchone()
                    if not row:
                        return None
                    
                    # 2. RECOMMENDED_CATEGORIES 파싱 (CLOB에서 먼저 읽기)
                    recommended_categories_from_clob = []
                    if row[7]:  # RECOMMENDED_CATEGORIES CLOB
                        try:
                            cats_json = row[7].read() if hasattr(row[7], 'read') else str(row[7])
                            if cats_json:
                                recommended_categories_from_clob = json.loads(cats_json)
                        except (json.JSONDecodeError, AttributeError) as e:
                            logger.warning(f"Failed to parse RECOMMENDED_CATEGORIES for taste_id={taste_id}: {e}")
                    
                    # 3. RECOMMENDED_PRODUCTS 파싱
                    recommended_products = {}
                    if row[8]:  # RECOMMENDED_PRODUCTS CLOB
                        try:
                            products_json = row[8].read() if hasattr(row[8], 'read') else str(row[8])
                            if products_json:
                                recommended_products = json.loads(products_json)
                        except (json.JSONDecodeError, AttributeError) as e:
                            logger.warning(f"Failed to parse RECOMMENDED_PRODUCTS for taste_id={taste_id}: {e}")
                    
                    # 4. RECOMMENDED_PRODUCT_SCORES 파싱
                    recommended_product_scores = {}
                    if row[9]:  # RECOMMENDED_PRODUCT_SCORES CLOB
                        try:
                            scores_json = row[9].read() if hasattr(row[9], 'read') else str(row[9])
                            if scores_json:
                                recommended_product_scores = json.loads(scores_json)
                        except (json.JSONDecodeError, AttributeError) as e:
                            logger.warning(f"Failed to parse RECOMMENDED_PRODUCT_SCORES for taste_id={taste_id}: {e}")
                    
                    # 5. 정규화된 TASTE_CATEGORY_SCORES 테이블에서 카테고리 점수 조회
                    cur.execute("""
                        SELECT 
                            CATEGORY_NAME,
                            SCORE,
                            IS_RECOMMENDED,
                            IS_ILL_SUITED
                        FROM TASTE_CATEGORY_SCORES
                        WHERE TASTE_ID = :p_taste_id
                        ORDER BY CATEGORY_NAME
                    """, {'p_taste_id': taste_id})
                    
                    category_rows = cur.fetchall()
                    
                    # 6. 카테고리 데이터 구성
                    recommended_categories = recommended_categories_from_clob.copy() if recommended_categories_from_clob else []
                    category_scores = {}
                    ill_suited_categories = []
                    
                    for cat_row in category_rows:
                        category_name = cat_row[0]
                        score = float(cat_row[1]) if cat_row[1] is not None else None
                        is_recommended = cat_row[2] == 'Y' if cat_row[2] else False
                        is_ill_suited = cat_row[3] == 'Y' if cat_row[3] else False
                        
                        if score is not None:
                            category_scores[category_name] = score
                        
                        if is_recommended and category_name not in recommended_categories:
                            recommended_categories.append(category_name)
                        
                        if is_ill_suited:
                            ill_suited_categories.append(category_name)
                    
                    return {
                        'taste_id': row[0],
                        'representative_vibe': row[1],
                        'representative_household_size': row[2],
                        'representative_main_space': row[3],
                        'representative_has_pet': row[4] == 'Y' if row[4] else False,
                        'representative_priority': row[5],
                        'representative_budget_level': row[6],
                        'recommended_categories': recommended_categories,
                        'category_scores': category_scores,
                        'ill_suited_categories': ill_suited_categories,
                        'recommended_products': recommended_products,  # 추가
                        'recommended_product_scores': recommended_product_scores  # 추가
                    }
        except Exception as e:
            logger.error(f"Error fetching TasteConfig for taste_id={taste_id}: {str(e)}", exc_info=True)
            return None
    
    def get_recommended_product_scores(self, taste_id: int) -> Optional[Dict]:
        """
        taste_id에 대한 RECOMMENDED_PRODUCT_SCORES 조회
        
        Returns:
            {"TV": [85, 78, 72], "냉장고": [90, 85, 80], ...} 형태의 딕셔너리
            또는 None (데이터가 없는 경우)
        """
        taste_config = self._get_taste_config(taste_id)
        if taste_config:
            return taste_config.get('recommended_product_scores', {})
        return None
    
    def _get_products_from_oracle(self, category: str) -> List[Dict]:
        """Oracle DB에서 직접 제품 정보 조회 (JOIN으로 최적화, N+1 문제 해결)"""
        products_data = []
        
        try:
            with get_connection() as conn:
                with conn.cursor() as cur:
                    # JOIN을 사용하여 한 번의 쿼리로 제품과 스펙 정보 모두 조회
                    cur.execute("""
                        SELECT 
                            P.PRODUCT_ID,
                            P.MODEL_CODE,
                            P.PRODUCT_NAME,
                            P.PRICE,
                            PS.SPEC_KEY,
                            PS.SPEC_VALUE
                        FROM PRODUCT P
                        LEFT JOIN PRODUCT_SPEC PS ON P.PRODUCT_ID = PS.PRODUCT_ID
                            AND PS.SPEC_TYPE = 'COMMON'
                            AND PS.SPEC_VALUE IS NOT NULL
                            AND PS.SPEC_VALUE != 'nan'
                        WHERE P.STATUS = '판매중'
                          AND P.PRICE > 0
                          AND P.PRICE IS NOT NULL
                          AND P.MAIN_CATEGORY = :p_category
                        ORDER BY P.PRICE ASC, P.PRODUCT_ID, PS.SPEC_KEY
                    """, {'p_category': category})
                    
                    rows = cur.fetchall()
                    
                    # 결과를 제품별로 그룹화
                    current_product_id = None
                    current_product_data = None
                    
                    for row in rows:
                        product_id = row[0]
                        model_code = row[1] or ''
                        product_name = row[2] or ''
                        price = float(row[3]) if row[3] else 0.0
                        spec_key = row[4]
                        spec_value = row[5]
                        
                        # 새로운 제품인 경우
                        if current_product_id != product_id:
                            # 이전 제품 저장
                            if current_product_data:
                                products_data.append(current_product_data)
                            
                            # 새 제품 데이터 초기화
                            current_product_id = product_id
                            current_product_data = {
                                'product_id': product_id,
                                'model_code': model_code,
                                'product_name': product_name,
                                'price': price,
                                'common_features': {}
                            }
                        
                        # 스펙 정보 추가
                        if spec_key and spec_value:
                            current_product_data['common_features'][spec_key] = spec_value
                    
                    # 마지막 제품 저장
                    if current_product_data:
                        products_data.append(current_product_data)
                    
                    logger.info(f"Oracle DB에서 {category} 카테고리 제품 {len(products_data)}개 조회 완료 (최적화된 쿼리)")
                    
        except Exception as e:
            logger.error(f"Oracle DB 제품 조회 실패 (category={category}): {str(e)}", exc_info=True)
        
        return products_data
    
    def _get_scoring_criteria_for_taste(
        self,
        taste_id: int,
        taste_config: Dict,
        category: str
    ) -> Dict:
        """
        Taste별 scoring 기준 생성
        
        taste_config의 특성들을 기반으로:
        - 어떤 feature를 중시할지
        - 각 feature의 가중치는 얼마인지
        - feature 값의 이상적인 범위는 무엇인지
        
        Returns:
            {
                'feature_weights': {'feature_name': weight, ...},
                'feature_ideal_ranges': {'feature_name': (min, max), ...},
                'feature_priorities': ['feature1', 'feature2', ...]
            }
        """
        # 캐시 확인
        cache_key = f"{taste_id}_{category}"
        if cache_key in self.taste_scoring_criteria_cache:
            return self.taste_scoring_criteria_cache[cache_key]
        
        vibe = taste_config.get('representative_vibe', 'modern')
        household_size = taste_config.get('representative_household_size', 2)
        priority = taste_config.get('representative_priority', 'value')
        budget_level = taste_config.get('representative_budget_level', 'medium')
        has_pet = taste_config.get('representative_has_pet', False)
        
        # 실제 제품의 SPEC_KEY 리스트 가져오기 (동적 매칭용)
        # 이건 제품별로 다르므로, 여기서는 기본 가중치만 생성
        # 실제 제품 scoring 시에는 제품의 SPEC_KEY를 사용
        base_weights = self._get_base_feature_weights(category, available_spec_keys=None)
        
        # Taste 특성에 따른 가중치 조정
        adjusted_weights = self._adjust_weights_by_taste(
            base_weights=base_weights,
            vibe=vibe,
            household_size=household_size,
            priority=priority,
            budget_level=budget_level,
            has_pet=has_pet,
            category=category
        )
        
        # 이상적인 feature 값 범위 계산
        ideal_ranges = self._calculate_ideal_ranges(
            category=category,
            household_size=household_size,
            budget_level=budget_level,
            priority=priority
        )
        
        criteria = {
            'feature_weights': adjusted_weights,
            'feature_ideal_ranges': ideal_ranges,
            'feature_priorities': sorted(adjusted_weights.items(), key=lambda x: x[1], reverse=True)[:5]
        }
        
        # 캐시 저장
        self.taste_scoring_criteria_cache[cache_key] = criteria
        
        return criteria
    
    def _get_base_feature_weights(self, category: str, available_spec_keys: List[str] = None) -> Dict[str, float]:
        """
        Category별 기본 feature 가중치
        available_spec_keys: 실제 제품에 있는 SPEC_KEY 리스트 (동적 매칭용)
        """
        # SPEC_KEY 매핑 (실제 SPEC_KEY -> 표준 feature 이름)
        spec_key_mapping = {
            # TV 관련
            '해상도': ['해상도'],
            '화면 사이즈 (베젤 미포함)': ['화면크기', '화면 크기'],
            '주사율': ['주사율'],
            'HDR (High Dynamic Range)': ['HDR', 'HDR 지원'],
            'ThinQ': ['스마트기능', '스마트', 'ThinQ'],
            'Wi-Fi': ['스마트기능', 'Wi-Fi'],
            'Bluetooth 지원': ['스마트기능', 'Bluetooth'],
            
            # 냉장고 관련
            '냉장 용량 (L)': ['용량'],
            '냉동 용량 (L)': ['용량'],
            '전체 용량 (L)': ['용량'],
            '용량 (가용용량)(L)': ['용량'],
            '용량': ['용량'],
            '에너지소비효율등급': ['에너지효율'],
            '에너지 소비효율등급': ['에너지효율'],
            '냉각방식': ['냉각방식'],
            '냉각 방식': ['냉각방식'],
            
            # 세탁기 관련
            '세탁 용량 (kg)': ['용량'],
            '용량': ['용량'],
            '에너지소비효율등급': ['에너지효율'],
            '소음': ['소음'],
            
            # 에어컨 관련
            '냉방능력(정격/최소)(W)': ['냉방능력'],
            '표준사용면적 (㎡)': ['냉방능력'],
            '에너지소비효율등급': ['에너지효율'],
            '공기청정 필터': ['필터기능'],
            '필터': ['필터기능'],
            
            # 공기청정기 관련
            '표준사용면적 (㎡)': ['청정면적'],
            '필터': ['필터타입'],
            '공기청정 필터': ['필터타입'],
        }
        
        # Category별 중요 feature 우선순위
        category_priorities = {
            'TV': ['해상도', '화면크기', '주사율', 'HDR', '스마트기능'],
            '냉장고': ['용량', '에너지효율', '냉각방식', '스마트기능'],
            '세탁': ['용량', '에너지효율', '스마트기능', '소음'],
            '세탁기': ['용량', '에너지효율', '스마트기능', '소음'],
            '에어컨': ['냉방능력', '에너지효율', '필터기능', '스마트기능'],
            '공기청정기': ['청정면적', '필터타입', '스마트기능', '소음'],
            '청소기': ['청정세기', '필터', '스마트기능', '소음'],
        }
        
        # 실제 제품의 SPEC_KEY를 기반으로 가중치 생성
        weights = {}
        priorities = category_priorities.get(category, [])
        
        if available_spec_keys:
            # 실제 SPEC_KEY를 표준 feature로 매핑 (임시로 category를 사용)
            # _map_spec_keys_to_features를 사용할 수 없으므로 여기서 직접 매핑
            matched_features = {}
            for spec_key in available_spec_keys:
                # category별 매핑 확인
                category_map = {
                    'TV': {
                        '해상도': '해상도',
                        '화면 사이즈 (베젤 미포함)': '화면크기',
                        '화면 사이즈': '화면크기',
                        '화면크기': '화면크기',
                        '주사율': '주사율',
                        'HDR': 'HDR',
                        'ThinQ': '스마트기능',
                        'Wi-Fi': '스마트기능',
                    },
                    '냉장고': {
                        '냉장 용량 (L)': '용량',
                        '냉동 용량 (L)': '용량',
                        '전체 용량 (L)': '용량',
                        '용량': '용량',
                        '에너지소비효율등급': '에너지효율',
                        'ThinQ': '스마트기능',
                    },
                }.get(category, {})
                
                # 정확한 매칭
                if spec_key in category_map:
                    std_feature = category_map[spec_key]
                    if std_feature not in matched_features:
                        matched_features[std_feature] = spec_key
                else:
                    # 부분 매칭
                    for std_feature in priorities:
                        if std_feature in spec_key:
                            if std_feature not in matched_features:
                                matched_features[std_feature] = spec_key
                            break
            
            # 매칭된 feature에 가중치 부여
            if matched_features:
                total_priority = sum(range(1, len(priorities) + 1))
                for i, feature in enumerate(priorities):
                    if feature in matched_features:
                        # 우선순위에 따라 가중치 할당 (높은 우선순위일수록 높은 가중치)
                        weight = (len(priorities) - i) / total_priority
                        weights[feature] = weight
                
                # 가중치 정규화
                if weights:
                    scale = sum(weights.values())
                    if scale > 0:
                        weights = {k: v / scale for k, v in weights.items()}
        else:
            # 기본 가중치 (available_spec_keys가 없을 때)
            for i, feature in enumerate(priorities):
                weights[feature] = (len(priorities) - i) / sum(range(1, len(priorities) + 1))
        
        return weights if weights else {
            '기능': 0.30,
            '성능': 0.25,
            '에너지효율': 0.20,
            '디자인': 0.15,
            '가격': 0.10
        }
    
    def _adjust_weights_by_taste(
        self,
        base_weights: Dict[str, float],
        vibe: str,
        household_size: int,
        priority: str,
        budget_level: str,
        has_pet: bool,
        category: str
    ) -> Dict[str, float]:
        """Taste 특성에 따른 가중치 조정"""
        adjusted = base_weights.copy()
        
        # Priority에 따른 조정
        if priority == 'design':
            if '디자인' in adjusted:
                adjusted['디자인'] *= 1.5
            if '스타일' in adjusted:
                adjusted['스타일'] *= 1.3
        elif priority == 'tech':
            if '스마트기능' in adjusted:
                adjusted['스마트기능'] *= 1.5
            if '기능' in adjusted:
                adjusted['기능'] *= 1.3
        elif priority == 'eco':
            if '에너지효율' in adjusted:
                adjusted['에너지효율'] *= 1.5
            if '전력소비' in adjusted:
                adjusted['전력소비'] *= 1.3
        elif priority == 'value':
            if '가격' in adjusted:
                adjusted['가격'] *= 1.5
            if '가성비' in adjusted:
                adjusted['가성비'] *= 1.3
        
        # Household size에 따른 조정
        if household_size >= 4:
            if '용량' in adjusted:
                adjusted['용량'] *= 1.3
            if '크기' in adjusted:
                adjusted['크기'] *= 1.2
        elif household_size == 1:
            if '용량' in adjusted:
                adjusted['용량'] *= 0.8
            if '크기' in adjusted:
                adjusted['크기'] *= 0.8
        
        # Budget level에 따른 조정
        if budget_level in ['high', 'premium', 'luxury']:
            if '가격' in adjusted:
                adjusted['가격'] *= 0.5  # 가격 중요도 감소
            if '프리미엄기능' in adjusted:
                adjusted['프리미엄기능'] *= 1.3
        elif budget_level == 'low':
            if '가격' in adjusted:
                adjusted['가격'] *= 1.5
            if '프리미엄기능' in adjusted:
                adjusted['프리미엄기능'] *= 0.5
        
        # Has pet에 따른 조정
        if has_pet:
            if '필터기능' in adjusted:
                adjusted['필터기능'] *= 1.3
            if '청정기능' in adjusted:
                adjusted['청정기능'] *= 1.2
        
        # 가중치 정규화 (합이 1.0이 되도록)
        total = sum(adjusted.values())
        if total > 0:
            adjusted = {k: v / total for k, v in adjusted.items()}
        
        return adjusted
    
    def _calculate_ideal_ranges(
        self,
        category: str,
        household_size: int,
        budget_level: str,
        priority: str
    ) -> Dict[str, Tuple[float, float]]:
        """이상적인 feature 값 범위 계산"""
        ranges = {}
        
        # Category별 기본 범위
        if category == '냉장고':
            # 용량: 가구 수에 따라
            if household_size >= 4:
                ranges['용량'] = (400, 1000)  # 리터
            elif household_size == 2:
                ranges['용량'] = (200, 400)
            else:
                ranges['용량'] = (100, 300)
        
        elif category == '세탁기':
            if household_size >= 4:
                ranges['용량'] = (15, 25)  # kg
            elif household_size == 2:
                ranges['용량'] = (10, 15)
            else:
                ranges['용량'] = (8, 12)
        
        elif category == 'TV':
            if household_size >= 4:
                ranges['화면크기'] = (65, 85)  # 인치
            elif household_size == 2:
                ranges['화면크기'] = (55, 65)
            else:
                ranges['화면크기'] = (43, 55)
        
        # Budget level에 따른 가격 범위는 별도 처리
        
        return ranges
    
    def _calculate_product_score_from_oracle(
        self,
        product_data: Dict,
        category: str,
        scoring_criteria: Dict,
        taste_config: Dict
    ) -> int:
        """
        Oracle DB에서 가져온 제품 데이터로 점수 계산 (0~100 정수)
        
        사용하는 테이블/컬럼:
        1. PRODUCT 테이블:
           - PRODUCT_ID: 제품 ID
           - PRICE: 제품 가격 (budget_level과 비교)
           - MAIN_CATEGORY: 카테고리 필터링
           - STATUS: '판매중' 필터링
        
        2. PRODUCT_SPEC 테이블:
           - PRODUCT_ID: 제품 ID (PRODUCT 테이블과 조인)
           - SPEC_KEY: 스펙 키 (예: '용량', '화면크기', '해상도' 등)
           - SPEC_VALUE: 스펙 값
           - SPEC_TYPE: 'common' 타입만 사용 (공통 스펙)
        
        3. TASTE_CONFIG 테이블:
           - REPRESENTATIVE_VIBE: 대표 무드 (modern/cozy/pop/luxury)
           - REPRESENTATIVE_HOUSEHOLD_SIZE: 대표 가구 수
           - REPRESENTATIVE_PRIORITY: 대표 우선순위 (design/tech/eco/value)
           - REPRESENTATIVE_BUDGET_LEVEL: 대표 예산 수준 (low/medium/high/premium/luxury)
           - REPRESENTATIVE_HAS_PET: 반려동물 여부
        
        Scoring 로직:
        - PRODUCT_SPEC의 SPEC_TYPE='common'인 항목들을 가져와서
        - taste_config의 특성들과 비교하여 점수 계산
        - feature 점수 80% + 가격 점수 20%
        - 최종 점수: 0~100 정수
        """
        common_features = product_data.get('common_features', {})
        
        if not common_features:
            return 0
        
        try:
            # 실제 제품의 SPEC_KEY를 기반으로 동적 가중치 생성
            available_spec_keys = list(common_features.keys())
            dynamic_weights = self._get_base_feature_weights(
                category=category,
                available_spec_keys=available_spec_keys
            )
            
            # Taste 특성에 따른 가중치 조정
            adjusted_weights = self._adjust_weights_by_taste(
                base_weights=dynamic_weights,
                vibe=taste_config.get('representative_vibe', 'modern'),
                household_size=taste_config.get('representative_household_size', 2),
                priority=taste_config.get('representative_priority', 'value'),
                budget_level=taste_config.get('representative_budget_level', 'medium'),
                has_pet=taste_config.get('representative_has_pet', False),
                category=category
            )
            
            ideal_ranges = scoring_criteria.get('feature_ideal_ranges', {})
            
            total_score = 0.0
            total_weight = 0.0
            
            # SPEC_KEY 매핑 (실제 SPEC_KEY -> 표준 feature 이름)
            spec_key_to_feature = self._map_spec_keys_to_features(available_spec_keys, category)
            
            # 각 SPEC_KEY별 점수 계산
            feature_scores_detail = {}  # 디버깅용
            unmatched_features = []  # 매칭되지 않은 feature들
            
            for spec_key, spec_value in common_features.items():
                # SPEC_KEY를 표준 feature로 매핑
                standard_feature = spec_key_to_feature.get(spec_key)
                
                if standard_feature and standard_feature in adjusted_weights:
                    # 매칭된 feature: 가중치 적용
                    weight = adjusted_weights[standard_feature]
                    feature_score = self._score_spec_value(
                        spec_key=spec_key,
                        spec_value=spec_value,
                        standard_feature=standard_feature,
                        ideal_range=ideal_ranges.get(standard_feature),
                        taste_config=taste_config,
                        category=category
                    )
                    
                    total_score += feature_score * weight
                    total_weight += weight
                    feature_scores_detail[f"{spec_key}({standard_feature})"] = {
                        'value': spec_value,
                        'score': feature_score,
                        'weight': weight
                    }
                else:
                    # 매칭되지 않은 feature도 기본 점수 부여 (제품별 차이 반영)
                    unmatched_features.append((spec_key, spec_value))
                    # 기본 가중치로 점수 계산 (매칭된 feature가 없을 때만)
                    if total_weight == 0:
                        basic_score = self._score_spec_value(
                            spec_key=spec_key,
                            spec_value=spec_value,
                            standard_feature='기본',
                            ideal_range=None,
                            taste_config=taste_config,
                            category=category
                        )
                        # 기본 가중치 (매칭된 feature가 없을 때만)
                        basic_weight = 0.1 / len(common_features) if common_features else 0.1
                        total_score += basic_score * basic_weight
                        total_weight += basic_weight
                        feature_scores_detail[f"{spec_key}(기본)"] = {
                            'value': spec_value,
                            'score': basic_score,
                            'weight': basic_weight
                        }
            
            # 가중 평균 점수
            if total_weight > 0:
                feature_avg_score = total_score / total_weight
            else:
                # 매칭된 feature가 없으면 모든 COMMON feature를 기본 점수로 계산
                feature_avg_score = 0.3  # 기본 점수
                if common_features:
                    # 매칭되지 않은 feature들도 기본 점수 부여
                    unmatched_count = len(common_features) - len(feature_scores_detail)
                    if unmatched_count > 0:
                        feature_avg_score = 0.4  # feature가 있으면 조금 더 높은 점수
            
            # 가격 점수 추가 (budget_level과 비교)
            price = product_data.get('price', 0.0)
            price_score = self._calculate_price_score_from_data(
                price=price,
                budget_level=taste_config.get('representative_budget_level', 'medium')
            )
            
            # 최종 점수: feature 점수 90%, 가격 점수 10% (feature 차이를 더 크게 반영)
            if feature_avg_score == 0.0:
                # feature 점수가 없으면 가격 기반으로만 점수 계산
                final_score = max(0.1, price_score * 0.5)  # 최소 0.1 (10점)
            else:
                final_score = feature_avg_score * 0.9 + price_score * 0.1
            
            # 제품별 차이를 더 크게 반영: 제품 고유 특성 반영
            if len(feature_scores_detail) > 0:
                feature_scores_list = [v['score'] for v in feature_scores_detail.values()]
                
                # 1. 점수 분산 (제품이 특정 feature에서 우수할수록 보너스)
                if len(feature_scores_list) > 1:
                    import statistics
                    try:
                        score_std = statistics.stdev(feature_scores_list)
                        # 표준편차가 클수록 보너스 (최대 0.05)
                        bonus_std = min(0.05, score_std * 0.15)
                        final_score = min(1.0, final_score + bonus_std)
                    except:
                        pass
                
                # 2. 최고 점수 feature 보너스 (제품이 특정 feature에서 매우 우수할 때)
                max_feature_score = max(feature_scores_list) if feature_scores_list else 0
                if max_feature_score >= 0.9:
                    bonus_max = 0.03  # 최고 점수 feature 보너스
                    final_score = min(1.0, final_score + bonus_max)
                
                # 3. 매칭된 feature 개수 보너스 (더 많은 feature가 매칭될수록)
                matched_count = len(feature_scores_detail)
                if matched_count >= 5:
                    bonus_count = 0.02  # feature 개수 보너스
                    final_score = min(1.0, final_score + bonus_count)
                
                # 4. 제품별 고유 값 차이 반영 (같은 카테고리 내에서도 차등)
                # 가격 차이를 feature 점수에 반영 (가격이 비슷하면 feature 차이를 더 크게)
                # 이 부분은 카테고리별로 다르게 처리할 수 있음
            
            # 0.0 ~ 1.0 범위를 0 ~ 100 정수로 변환
            score_0_to_100 = int(round(final_score * 100))
            
            # 로깅 (디버깅용)
            if logger.isEnabledFor(logging.DEBUG):
                logger.debug(
                    f"Product {product_data.get('product_id')} scoring: "
                    f"feature_avg={feature_avg_score:.3f}, price_score={price_score:.3f}, "
                    f"final={final_score:.3f}, score_0_100={score_0_to_100}, "
                    f"matched_features={len(feature_scores_detail)}/{len(common_features)}"
                )
            
            return min(max(score_0_to_100, 0), 100)  # 0 ~ 100 정수 범위로 제한
            
        except (json.JSONDecodeError, AttributeError, TypeError) as e:
            logger.warning(f"Error calculating score for product {product_data.get('product_id')}: {str(e)}")
            return 0
    
    def _calculate_product_score(
        self,
        product: Product,
        category: str,
        scoring_criteria: Dict,
        taste_config: Dict
    ) -> float:
        """
        제품의 점수 계산 (Django Product 모델용 - 호환성 유지)
        
        product_spec.spec_json의 "common" feature와 taste_config 특성들을 비교
        """
        if not hasattr(product, 'spec') or not product.spec or not product.spec.spec_json:
            return 0.0
        
        try:
            spec_json = json.loads(product.spec.spec_json)
            common_features = spec_json.get('common', {})
            
            if not common_features:
                return 0.0
            
            feature_weights = scoring_criteria.get('feature_weights', {})
            ideal_ranges = scoring_criteria.get('feature_ideal_ranges', {})
            
            total_score = 0.0
            total_weight = 0.0
            
            # 각 feature별 점수 계산
            for feature_name, weight in feature_weights.items():
                if feature_name not in common_features:
                    continue
                
                feature_value = common_features[feature_name]
                feature_score = self._score_feature_value(
                    feature_name=feature_name,
                    feature_value=feature_value,
                    ideal_range=ideal_ranges.get(feature_name),
                    taste_config=taste_config
                )
                
                total_score += feature_score * weight
                total_weight += weight
            
            # 가중 평균 점수
            if total_weight > 0:
                final_score = total_score / total_weight
            else:
                final_score = 0.0
            
            # 가격 점수 추가 (budget_level과 비교)
            price_score = self._calculate_price_score(
                product=product,
                budget_level=taste_config.get('representative_budget_level', 'medium')
            )
            
            # 최종 점수: feature 점수 80%, 가격 점수 20%
            final_score = final_score * 0.8 + price_score * 0.2
            
            return min(max(final_score, 0.0), 1.0)  # 0.0 ~ 1.0 범위로 제한
            
        except (json.JSONDecodeError, AttributeError, TypeError) as e:
            logger.warning(f"Error calculating score for product {product.id}: {str(e)}")
            return 0.0
    
    def _map_spec_keys_to_features(self, spec_keys: List[str], category: str) -> Dict[str, str]:
        """
        실제 SPEC_KEY를 표준 feature 이름으로 매핑
        
        Returns:
            {실제_SPEC_KEY: 표준_feature_이름}
        """
        mapping = {}
        
        # Category별 SPEC_KEY -> feature 매핑
        category_mappings = {
            'TV': {
                '해상도': '해상도',
                '화면 사이즈 (베젤 미포함)': '화면크기',
                '화면 사이즈': '화면크기',
                '화면크기': '화면크기',
                '주사율': '주사율',
                'HDR (High Dynamic Range)': 'HDR',
                'HDR': 'HDR',
                'ThinQ': '스마트기능',
                'ThinQ (Wi-Fi)': '스마트기능',
                'ThinQ(Wi-Fi)': '스마트기능',
                'Wi-Fi': '스마트기능',
                'Bluetooth 지원': '스마트기능',
                '블루투스': '스마트기능',
            },
            '냉장고': {
                '냉장 용량 (L)': '용량',
                '냉동 용량 (L)': '용량',
                '전체 용량 (L)': '용량',
                '용량 (가용용량)(L)': '용량',
                '용량': '용량',
                '에너지소비효율등급': '에너지효율',
                '에너지 소비효율등급': '에너지효율',
                '냉각방식': '냉각방식',
                '냉각 방식': '냉각방식',
                'ThinQ': '스마트기능',
                'Wi-Fi': '스마트기능',
            },
            '세탁': {
                '세탁 용량 (kg)': '용량',
                '용량': '용량',
                '에너지소비효율등급': '에너지효율',
                '소음': '소음',
                'ThinQ': '스마트기능',
                'Wi-Fi': '스마트기능',
            },
            '세탁기': {
                '세탁 용량 (kg)': '용량',
                '용량': '용량',
                '에너지소비효율등급': '에너지효율',
                '소음': '소음',
                'ThinQ': '스마트기능',
                'Wi-Fi': '스마트기능',
            },
            '에어컨': {
                '냉방능력(정격/최소)(W)': '냉방능력',
                '표준사용면적 (㎡)': '냉방능력',
                '에너지소비효율등급': '에너지효율',
                '공기청정 필터': '필터기능',
                '필터': '필터기능',
                'ThinQ': '스마트기능',
                'Wi-Fi': '스마트기능',
            },
            '공기청정기': {
                '표준사용면적 (㎡)': '청정면적',
                '필터': '필터타입',
                '공기청정 필터': '필터타입',
                'ThinQ': '스마트기능',
                'Wi-Fi': '스마트기능',
            },
            '청소기': {
                '청정세기': '청정세기',
                '필터': '필터',
                'ThinQ': '스마트기능',
                'Wi-Fi': '스마트기능',
            },
        }
        
        category_map = category_mappings.get(category, {})
        
        for spec_key in spec_keys:
            # 정확한 매칭
            if spec_key in category_map:
                mapping[spec_key] = category_map[spec_key]
            else:
                # 부분 매칭 (SPEC_KEY에 표준 feature 이름이 포함된 경우)
                for std_feature in ['용량', '에너지효율', '스마트기능', '소음', '필터', '해상도', '화면크기', '화면 사이즈', '주사율', 'HDR']:
                    if std_feature in spec_key:
                        mapping[spec_key] = std_feature
                        break
        
        return mapping
    
    def _score_spec_value(
        self,
        spec_key: str,
        spec_value: str,
        standard_feature: str,
        ideal_range: Optional[Tuple[float, float]],
        taste_config: Dict,
        category: str
    ) -> float:
        """
        SPEC_VALUE를 파싱하고 점수 계산 (0.0 ~ 1.0)
        
        복잡한 로직:
        - 숫자 값: ideal_range와 비교
        - 텍스트 값: taste_config의 특성과 비교
        - 등급 값: 등급을 숫자로 변환하여 비교
        """
        if not spec_value or spec_value == 'nan' or spec_value == '':
            return 0.0
        
        try:
            # 숫자 값 추출 (예: "500L", "50kg", "1등급" 등)
            import re
            numbers = re.findall(r'[\d.]+', str(spec_value))
            
            if numbers:
                # 첫 번째 숫자 사용
                num_value = float(numbers[0])
                
                # ideal_range가 있으면 범위 기반 점수
                if ideal_range:
                    min_val, max_val = ideal_range
                    if min_val <= num_value <= max_val:
                        return 1.0
                    elif num_value < min_val:
                        return max(0.3, num_value / min_val)
                    else:
                        return max(0.3, max_val / num_value)
                
                # 등급 값 처리 (1등급, 2등급 등)
                if '등급' in spec_value or 'grade' in spec_value.lower():
                    # 등급이 낮을수록 좋음 (1등급 > 2등급)
                    if num_value == 1:
                        return 1.0
                    elif num_value == 2:
                        return 0.8
                    elif num_value == 3:
                        return 0.6
                    else:
                        return 0.4
                
                # 용량/크기 값 처리
                if '용량' in spec_key or '크기' in spec_key or '사이즈' in spec_key:
                    household_size = taste_config.get('representative_household_size', 2)
                    # 가구 수에 따른 이상적인 용량 계산
                    if category in ['냉장고', '세탁', '세탁기']:
                        ideal_capacity = household_size * 100  # 가구당 100L 또는 10kg
                        if abs(num_value - ideal_capacity) / ideal_capacity < 0.2:
                            return 1.0
                        else:
                            return max(0.5, 1.0 - abs(num_value - ideal_capacity) / ideal_capacity / 2)
                    elif category == 'TV':
                        # TV 화면 크기: 가구 수에 따라 이상적인 크기 계산
                        # 1인: 43-55인치, 2인: 55-65인치, 3-4인: 65-75인치, 5인 이상: 75인치 이상
                        if household_size == 1:
                            ideal_size = 50  # cm (약 20인치)
                        elif household_size == 2:
                            ideal_size = 60  # cm (약 24인치)
                        elif household_size <= 4:
                            ideal_size = 70  # cm (약 28인치)
                        else:
                            ideal_size = 80  # cm (약 32인치)
                        
                        # 화면 크기 차이에 따라 점수 계산 (더 세밀하게)
                        diff_ratio = abs(num_value - ideal_size) / ideal_size
                        if diff_ratio < 0.1:  # 10% 이내 차이
                            return 1.0
                        elif diff_ratio < 0.2:  # 20% 이내 차이
                            return 0.9
                        elif diff_ratio < 0.3:  # 30% 이내 차이
                            return 0.8
                        elif diff_ratio < 0.5:  # 50% 이내 차이
                            return 0.7
                        else:
                            return max(0.5, 0.7 - diff_ratio * 0.3)
                
                # 해상도 값 처리 (TV)
                if '해상도' in spec_key:
                    # 해상도 우선순위: 4K > Full HD > HD
                    text_value = str(spec_value).upper()
                    if '4K' in text_value or 'UHD' in text_value or '3840' in text_value:
                        return 1.0
                    elif 'FULL HD' in text_value or 'FHD' in text_value or '1920' in text_value:
                        return 0.8
                    elif 'HD' in text_value or '1366' in text_value:
                        return 0.6
                    else:
                        return 0.5
                
                # 주사율 값 처리 (TV)
                if '주사율' in spec_key:
                    # 주사율이 높을수록 좋음
                    if num_value >= 120:
                        return 1.0
                    elif num_value >= 60:
                        return 0.8
                    elif num_value >= 30:
                        return 0.6
                    else:
                        return 0.4
                
                # 기본 숫자 점수 (값이 있으면 0.5점)
                return 0.5
            
            # 텍스트 값 처리
            text_value = str(spec_value).lower()
            
            # 스마트 기능 관련
            if '스마트' in standard_feature or 'ThinQ' in spec_key or 'Wi-Fi' in spec_key:
                if any(keyword in text_value for keyword in ['예', '있음', '지원', '가능', 'O', 'Y', 'Yes', 'true', '○']):
                    return 1.0
                elif any(keyword in text_value for keyword in ['부분', '일부', '제한']):
                    return 0.6
                else:
                    return 0.0
            
            # 필터 관련
            if '필터' in standard_feature:
                if '헤파' in text_value or 'HEPA' in text_value.upper():
                    return 1.0
                elif '필터' in text_value:
                    return 0.7
                else:
                    return 0.3
            
            # 기본 텍스트 점수: 제품별 차이를 더 크게 반영
            if any(keyword in text_value for keyword in ['예', '있음', '지원', '가능', 'O', 'Y', 'Yes', '○']):
                # 긍정적인 값도 세밀하게 차등
                if '완전' in text_value or '전체' in text_value or '모든' in text_value:
                    return 1.0
                elif '부분' in text_value or '일부' in text_value:
                    return 0.8
                else:
                    return 0.9  # 기본 긍정 값
            elif any(keyword in text_value for keyword in ['아니오', '없음', '미지원', 'X', 'N', 'No', '불가능']):
                return 0.2
            else:
                # 알 수 없는 값: 제품별로 다르게 처리하여 차등 반영
                # 텍스트 길이나 내용에 따라 차등
                text_len = len(text_value)
                if text_len > 10:
                    return 0.6  # 상세한 설명이 있으면 조금 더 높은 점수
                elif text_len > 5:
                    return 0.5
                else:
                    return 0.4
                
        except (ValueError, TypeError) as e:
            logger.warning(f"Error parsing spec_value: {spec_key}={spec_value}, error={str(e)}")
            return 0.3  # 기본 점수
    
    def _score_feature_value(
        self,
        feature_name: str,
        feature_value: any,
        ideal_range: Optional[Tuple[float, float]],
        taste_config: Dict
    ) -> float:
        """Feature 값의 점수 계산 (0.0 ~ 1.0)"""
        if feature_value is None or feature_value == '':
            return 0.0
        
        # 이상적인 범위가 있으면 범위 기반 점수
        if ideal_range:
            min_val, max_val = ideal_range
            try:
                num_value = float(str(feature_value).replace(',', '').replace(' ', ''))
                if min_val <= num_value <= max_val:
                    # 범위 내: 1.0점
                    return 1.0
                elif num_value < min_val:
                    # 범위보다 작음: 비례 감점
                    return max(0.0, num_value / min_val)
                else:
                    # 범위보다 큼: 비례 감점
                    return max(0.0, max_val / num_value)
            except (ValueError, TypeError):
                pass
        
        # 텍스트 값인 경우 (예: '예', '있음', '지원' 등)
        if isinstance(feature_value, str):
            positive_keywords = ['예', '있음', '지원', '가능', '적용', '포함', 'O', 'Y', 'Yes']
            negative_keywords = ['아니오', '없음', '미지원', '불가능', '미적용', '미포함', 'X', 'N', 'No']
            
            value_lower = feature_value.lower()
            if any(kw in value_lower for kw in positive_keywords):
                return 1.0
            elif any(kw in value_lower for kw in negative_keywords):
                return 0.0
            else:
                # 알 수 없는 값: 중간 점수
                return 0.5
        
        # 기본값: 값이 있으면 0.5점
        return 0.5
    
    def _calculate_price_score_from_data(
        self,
        price: float,
        budget_level: str
    ) -> float:
        """가격 점수 계산 (budget_level과 비교) - Oracle 데이터용"""
        if not price or price <= 0:
            return 0.0
        
        # Budget level별 이상적인 가격 범위
        budget_ranges = {
            'low': (0, 1000000),
            'medium': (1000000, 3000000),
            'high': (3000000, 7000000),
            'premium': (7000000, 15000000),
            'luxury': (15000000, 50000000)
        }
        
        ideal_min, ideal_max = budget_ranges.get(budget_level, (1000000, 3000000))
        
        if ideal_min <= price <= ideal_max:
            return 1.0
        elif price < ideal_min:
            # 예산보다 낮음: 약간 감점
            return max(0.7, price / ideal_min)
        else:
            # 예산보다 높음: 비례 감점
            return max(0.0, ideal_max / price)
    
    def _calculate_price_score(
        self,
        product: Product,
        budget_level: str
    ) -> float:
        """가격 점수 계산 (budget_level과 비교) - Django Product 모델용"""
        if not product.price or product.price <= 0:
            return 0.0
        
        return self._calculate_price_score_from_data(float(product.price), budget_level)


# Singleton 인스턴스
taste_based_product_scorer = TasteBasedProductScorer()

