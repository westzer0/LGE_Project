"""
콘텐츠 기반 필터링 (Content-Based Filtering) 서비스

MEMBER.TASTE와 PRODUCT/PRODUCT_SPEC을 벡터화하여 유사도를 계산하는 추천 시스템
"""
import json
import logging
import re
from typing import Dict, List, Optional, Tuple
from collections import Counter
import math

from django.db.models import QuerySet
from api.models import Product, ProductSpec
from api.db.oracle_client import fetch_all_dict

logger = logging.getLogger(__name__)


class ContentBasedFiltering:
    """
    콘텐츠 기반 필터링 엔진
    
    프로세스:
    1. MEMBER.TASTE를 태그 리스트로 파싱하여 벡터화
    2. PRODUCT/PRODUCT_SPEC의 스펙을 태그/피처로 변환하여 벡터화
    3. 코사인 유사도 계산
    4. 점수 구간별 등급 부여 (S, A, B, C)
    5. 상위 N개 추천
    """
    
    def __init__(self):
        # 모든 가능한 태그 목록 (TASTE_TAGS + 제품 스펙 태그)
        self.all_tags = self._load_all_tags()
        self.tag_to_index = {tag: idx for idx, tag in enumerate(self.all_tags)}
        self.index_to_tag = {idx: tag for tag, idx in self.tag_to_index.items()}
        
    def _load_all_tags(self) -> List[str]:
        """모든 가능한 태그 목록 로드"""
        # TASTE 태그 (generate_member_dummy_data.py에서 가져옴)
        taste_tags = [
            '미니멀', '모던', '빈티지', '내추럴', '인더스트리얼', '스칸디나비아', '로맨틱', '클래식',
            '럭셔리', '컨템포러리', '프로방스', '아시아틱', '보헤미안', '아르데코', '팝아트', '레트로',
            '심플', '엘레강트', '캐주얼', '세련', '따뜻한', '시원한', '컬러풀', '모노톤',
            '우드톤', '화이트톤', '그레이톤', '파스텔', '비비드', '어스톤', '네이비', '블랙',
            '가구중심', '액세서리중심', '조명중심', '커튼중심', '벽지중심', '바닥중심', '수납중심', '장식중심'
        ]
        
        # 제품 스펙 관련 태그
        spec_tags = [
            '대용량', '소형', '컴팩트', '스마트', 'AI', '에너지효율', '프리미엄', '기본형',
            'OLED', 'QLED', 'LED', 'LCD', '울트라HD', '4K', '8K', 'HDR',
            '무풍', '인버터', '듀얼', '트리플', '스탠드형', '벽걸이형', '빌트인',
            '스테인리스', '블랙', '화이트', '실버', '골드', '베이지',
            '냉장', '냉동', '김치냉장고', '양문형', '4도어', '프렌치도어',
            '드럼세탁기', '일반세탁기', '건조기', '세탁건조기', '미니세탁기',
            '무선', '유선', '청소기', '로봇청소기', '스틱청소기',
            '오븐', '전자레인지', '에어프라이어', '인덕션', '가스레인지',
            '에어컨', '공기청정기', '가습기', '제습기', '선풍기',
        ]
        
        # 카테고리 태그
        category_tags = ['TV', 'KITCHEN', 'LIVING', 'AIR', 'AI', 'OBJET', 'SIGNATURE']
        
        # 모든 태그 합치기 (중복 제거)
        all_tags = list(set(taste_tags + spec_tags + category_tags))
        all_tags.sort()  # 정렬하여 일관성 유지
        
        return all_tags
    
    def parse_taste_string(self, taste_str) -> List[str]:
        """
        MEMBER.TASTE 문자열을 태그 리스트로 파싱
        
        Args:
            taste_str: "미니멀,모던,빈티지" 형식의 문자열 또는 정수형
        
        Returns:
            태그 리스트
        """
        # None인 경우 처리
        if taste_str is None:
            return []
        
        # 정수형이면 문자열로 변환 (Oracle DB에서 NUMBER 타입으로 저장된 경우)
        if isinstance(taste_str, (int, float)):
            # 정수형 TASTE는 태그 ID일 수 있으므로, 일단 문자열로 변환하되
            # 실제로는 태그 문자열이어야 하므로 경고 로그 출력
            logger.warning(
                f"TASTE가 정수형입니다: {taste_str} (타입: {type(taste_str)}). "
                f"문자열 형식(예: '미니멀,모던,빈티지')이어야 합니다."
            )
            # 정수형을 문자열로 변환 (예: 1 -> "1")
            taste_str = str(taste_str)
        
        # 문자열이 아니면 문자열로 변환 시도
        if not isinstance(taste_str, str):
            logger.warning(f"TASTE가 예상하지 못한 타입입니다: {type(taste_str)}, 값: {taste_str}")
            try:
                taste_str = str(taste_str)
            except Exception as e:
                logger.error(f"TASTE를 문자열로 변환 실패: {e}")
                return []
        
        # 빈 문자열 처리
        if not taste_str or not taste_str.strip():
            return []
        
        # 쉼표로 분리하고 공백 제거
        # 사용자 요청대로 명확하게 처리
        taste_str = str(taste_str).strip()
        tags = [tag.strip() for tag in taste_str.split(',') if tag.strip()]
        
        return tags
    
    def extract_product_features(self, product: Product, spec: Optional[ProductSpec] = None) -> List[str]:
        """
        PRODUCT/PRODUCT_SPEC에서 피처(태그) 추출
        
        Args:
            product: Product 모델 인스턴스
            spec: ProductSpec 모델 인스턴스 (선택사항)
        
        Returns:
            피처 태그 리스트
        """
        features = []
        
        # 1. 카테고리 태그
        if product.category:
            features.append(product.category)
        
        # 2. 제품명에서 키워드 추출 (강화된 키워드 매핑)
        if product.name:
            name_upper = product.name.upper()
            name_lower = product.name.lower()
            name_original = product.name
            
            # 기술/브랜드 키워드
            tech_keywords = {
                'OBJET': ['OBJET', '오브제'],
                'SIGNATURE': ['SIGNATURE', '시그니처'],
                'AI': ['AI', '에이아이'],
                '스마트': ['스마트', 'SMART'],
                'OLED': ['OLED', '올레드'],
                'QLED': ['QLED', '큐엘드'],
                '4K': ['4K', 'UHD', '울트라HD'],
                '8K': ['8K'],
                'HDR': ['HDR'],
                '무풍': ['무풍', '무풍에어컨'],
                '인버터': ['인버터', 'INVERTER'],
            }
            
            # 디자인/스타일 키워드
            design_keywords = {
                '프리미엄': ['프리미엄', 'PREMIUM'],
                '럭셔리': ['럭셔리', 'LUXURY'],
                '미니멀': ['미니멀', 'MINIMAL'],
                '모던': ['모던', 'MODERN'],
                '심플': ['심플', 'SIMPLE'],
                '대용량': ['대용량', '큰용량'],
                '소형': ['소형', '미니', 'MINI'],
                '컴팩트': ['컴팩트', 'COMPACT'],
                '빌트인': ['빌트인', 'BUILT-IN', '내장형'],
                '스테인리스': ['스테인리스', 'STAINLESS'],
            }
            
            # 제품 타입 키워드 (명확히 분리, 패턴 매칭 강화)
            product_type_keywords = {
                '냉장고': ['냉장고', '냉장전용고', '냉동전용고', '냉장', 'REFRIGERATOR'],
                '김치냉장고': ['김치냉장고', '김치냉장', 'KIMCHI'],
                '양문형': ['양문형', 'FRENCH DOOR'],
                '4도어': ['4도어', '4DOOR'],
                '프렌치도어': ['프렌치도어', 'FRENCH'],
                '드럼세탁기': ['드럼세탁기', '드럼', 'DRUM'],
                '일반세탁기': ['일반세탁기', '일반세탁'],
                '건조기': ['건조기', 'DRYER'],
                '세탁건조기': ['세탁건조기', '세탁건조'],
                '미니세탁기': ['미니세탁기', '미니세탁'],
                '로봇청소기': ['로봇청소기', '로봇', 'ROBOT'],
                '스틱청소기': ['스틱청소기', '스틱', 'STICK'],
                '청소기': ['청소기', 'VACUUM'],
                '에어컨': ['에어컨', 'AIR CONDITIONER', 'AC'],
                '공기청정기': ['공기청정기', '공기청정', 'AIR PURIFIER'],
                '가습기': ['가습기', 'HUMIDIFIER'],
                '제습기': ['제습기', 'DEHUMIDIFIER'],
                '선풍기': ['선풍기', 'FAN'],
                '오븐': ['오븐', 'OVEN'],
                '전자레인지': ['전자레인지', '전자레인', 'MICROWAVE'],
                '에어프라이어': ['에어프라이어', '에어프라이', 'AIR FRYER'],
                '인덕션': ['인덕션', 'INDUCTION'],
                '가스레인지': ['가스레인지', '가스레인', 'GAS'],
            }
            
            # 색상 키워드
            color_keywords = {
                '블랙': ['블랙', 'BLACK', '검정'],
                '화이트': ['화이트', 'WHITE', '흰색'],
                '실버': ['실버', 'SILVER', '은색'],
                '골드': ['골드', 'GOLD', '금색'],
                '베이지': ['베이지', 'BEIGE'],
            }
            
            # 모든 키워드 그룹 통합
            all_keyword_groups = {
                **tech_keywords,
                **design_keywords,
                **product_type_keywords,
                **color_keywords
            }
            
            # 키워드 매칭
            for feature_tag, keyword_list in all_keyword_groups.items():
                for keyword in keyword_list:
                    if keyword in name_upper or keyword in name_lower or keyword in name_original:
                        features.append(feature_tag)
                        break  # 중복 방지
        
        # 3. 스펙 JSON에서 피처 추출
        if spec and spec.spec_json:
            try:
                spec_data = json.loads(spec.spec_json)
                
                # MAIN_CATEGORY, SUB_CATEGORY
                if spec_data.get('MAIN_CATEGORY'):
                    features.append(spec_data['MAIN_CATEGORY'])
                if spec_data.get('SUB_CATEGORY'):
                    features.append(spec_data['SUB_CATEGORY'])
                
                # 주요 스펙 키 추출
                spec_keys_to_check = [
                    'PRODUCT_TYPE', 'COLOR', 'CAPACITY', 'SIZE', 'PANEL_TYPE',
                    'RESOLUTION', 'ENERGY_EFFICIENCY', 'DESIGN_TYPE'
                ]
                
                for key in spec_keys_to_check:
                    value = spec_data.get(key, '')
                    if value:
                        # 값이 숫자나 단순 문자열이면 그대로 추가
                        if isinstance(value, (int, float)):
                            # 용량, 크기 등은 범주화
                            if key == 'CAPACITY':
                                if value >= 800:
                                    features.append('대용량')
                                elif value <= 300:
                                    features.append('소형')
                            elif key == 'SIZE':
                                if value >= 65:
                                    features.append('대형')
                                elif value <= 32:
                                    features.append('소형')
                            else:
                                features.append(str(value))
                        else:
                            # 문자열 값 처리
                            value_str = str(value).upper()
                            # 주요 키워드 매칭
                            if 'OLED' in value_str:
                                features.append('OLED')
                            elif 'QLED' in value_str:
                                features.append('QLED')
                            elif '4K' in value_str or 'UHD' in value_str:
                                features.append('4K')
                            elif '8K' in value_str:
                                features.append('8K')
                            elif 'HDR' in value_str:
                                features.append('HDR')
                            elif '스마트' in value_str or 'AI' in value_str:
                                features.append('스마트')
                            elif '무풍' in value_str:
                                features.append('무풍')
                            elif '인버터' in value_str:
                                features.append('인버터')
                            elif '스테인리스' in value_str:
                                features.append('스테인리스')
                            elif '블랙' in value_str or 'BLACK' in value_str:
                                features.append('블랙')
                            elif '화이트' in value_str or 'WHITE' in value_str:
                                features.append('화이트')
                            elif '실버' in value_str or 'SILVER' in value_str:
                                features.append('실버')
                            else:
                                features.append(value_str)
                
                # 모든 스펙 값에서 키워드 추출 (강화)
                for key, value in spec_data.items():
                    if isinstance(value, str) and value:
                        value_lower = value.lower()
                        value_upper = value.upper()
                        value_original = str(value)
                        
                        # 디자인/스타일 키워드
                        design_words = ['미니멀', '모던', '심플', '럭셔리', '프리미엄', '엘레강트', '세련']
                        for word in design_words:
                            if word in value_lower or word in value_original:
                                features.append(word)
                        
                        # 제품 타입 키워드 (스펙에서도 추출)
                        product_type_mapping = {
                            '냉장고': ['냉장고', 'REFRIGERATOR', '냉장'],
                            '김치냉장고': ['김치냉장고', '김치냉장', 'KIMCHI'],
                            '양문형': ['양문형', 'FRENCH DOOR'],
                            '4도어': ['4도어', '4DOOR'],
                            '프렌치도어': ['프렌치도어', 'FRENCH'],
                            '드럼세탁기': ['드럼세탁기', '드럼', 'DRUM'],
                            '일반세탁기': ['일반세탁기', '일반세탁'],
                            '건조기': ['건조기', 'DRYER'],
                            '세탁건조기': ['세탁건조기', '세탁건조'],
                            '로봇청소기': ['로봇청소기', '로봇', 'ROBOT'],
                            '스틱청소기': ['스틱청소기', '스틱', 'STICK'],
                            '청소기': ['청소기', 'VACUUM'],
                            '에어컨': ['에어컨', 'AIR CONDITIONER', 'AC'],
                            '공기청정기': ['공기청정기', '공기청정', 'AIR PURIFIER'],
                            '가습기': ['가습기', 'HUMIDIFIER'],
                            '제습기': ['제습기', 'DEHUMIDIFIER'],
                            '선풍기': ['선풍기', 'FAN'],
                            '오븐': ['오븐', 'OVEN'],
                            '전자레인지': ['전자레인지', '전자레인', 'MICROWAVE'],
                            '에어프라이어': ['에어프라이어', '에어프라이', 'AIR FRYER'],
                            '인덕션': ['인덕션', 'INDUCTION'],
                            '가스레인지': ['가스레인지', '가스레인', 'GAS'],
                        }
                        
                        for feature_tag, keyword_list in product_type_mapping.items():
                            for keyword in keyword_list:
                                if keyword in value_lower or keyword in value_upper or keyword in value_original:
                                    features.append(feature_tag)
                                    break
                        
                        # 색상 키워드
                        color_mapping = {
                            '블랙': ['블랙', 'BLACK', '검정'],
                            '화이트': ['화이트', 'WHITE', '흰색'],
                            '실버': ['실버', 'SILVER', '은색'],
                            '골드': ['골드', 'GOLD', '금색'],
                            '베이지': ['베이지', 'BEIGE'],
                        }
                        
                        for color_tag, color_keywords in color_mapping.items():
                            for color_keyword in color_keywords:
                                if color_keyword in value_lower or color_keyword in value_upper or color_keyword in value_original:
                                    features.append(color_tag)
                                    break
                
            except (json.JSONDecodeError, Exception) as e:
                logger.warning(f"스펙 JSON 파싱 실패 (product_id={product.id}): {e}")
        
        # 중복 제거
        return list(set(features))
    
    def text_to_vector(self, tags: List[str]) -> List[float]:
        """
        태그 리스트를 벡터로 변환 (one-hot 인코딩 기반)
        
        Args:
            tags: 태그 리스트
        
        Returns:
            벡터 (리스트)
        """
        vector = [0.0] * len(self.all_tags)
        
        for tag in tags:
            if tag in self.tag_to_index:
                idx = self.tag_to_index[tag]
                vector[idx] = 1.0
        
        return vector
    
    def cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """
        코사인 유사도 계산
        
        Args:
            vec1: 첫 번째 벡터
            vec2: 두 번째 벡터
        
        Returns:
            코사인 유사도 (0.0 ~ 1.0)
        """
        if len(vec1) != len(vec2):
            raise ValueError(f"벡터 길이가 다릅니다: {len(vec1)} vs {len(vec2)}")
        
        # 내적 계산
        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        
        # 벡터의 크기 계산
        magnitude1 = math.sqrt(sum(a * a for a in vec1))
        magnitude2 = math.sqrt(sum(b * b for b in vec2))
        
        # 코사인 유사도
        if magnitude1 == 0 or magnitude2 == 0:
            return 0.0
        
        similarity = dot_product / (magnitude1 * magnitude2)
        
        # 범위 보정 (0.0 ~ 1.0)
        return max(0.0, min(1.0, similarity))
    
    def get_similarity_score(self, member_taste, product: Product, spec: Optional[ProductSpec] = None) -> float:
        """
        MEMBER.TASTE와 PRODUCT 간 유사도 점수 계산
        
        Args:
            member_taste: MEMBER.TASTE 문자열 (예: "미니멀,모던,빈티지") 또는 정수형
            product: Product 모델 인스턴스
            spec: ProductSpec 모델 인스턴스 (선택사항)
        
        Returns:
            유사도 점수 (0.0 ~ 1.0)
        """
        # 1. TASTE를 태그 리스트로 파싱 (정수형 처리 포함)
        taste_tags = self.parse_taste_string(member_taste)
        
        # 2. PRODUCT에서 피처 추출
        product_features = self.extract_product_features(product, spec)
        
        # 3. 벡터화
        taste_vector = self.text_to_vector(taste_tags)
        product_vector = self.text_to_vector(product_features)
        
        # 4. 코사인 유사도 계산
        similarity = self.cosine_similarity(taste_vector, product_vector)
        
        return similarity
    
    def get_score_label(self, score: float) -> str:
        """
        점수 구간별 등급 부여
        
        Args:
            score: 유사도 점수 (0.0 ~ 1.0)
        
        Returns:
            등급 (S, A, B, C)
        """
        if score >= 0.8:
            return 'S'
        elif score >= 0.6:
            return 'A'
        elif score >= 0.4:
            return 'B'
        else:
            return 'C'
    
    def get_recommendations_by_taste(
        self,
        member_id: str,
        limit: int = 10,
        min_score: float = 0.3,
        category_filter: Optional[List[str]] = None
    ) -> Dict:
        """
        MEMBER_ID의 TASTE를 기반으로 제품 추천
        
        Args:
            member_id: MEMBER_ID
            limit: 추천 개수
            min_score: 최소 유사도 점수
            category_filter: 카테고리 필터 (선택사항)
        
        Returns:
            {
                'success': True/False,
                'count': 추천 개수,
                'member_id': member_id,
                'taste': TASTE 문자열,
                'recommendations': [
                    {
                        'product_id': ...,
                        'name': ...,
                        'score': ...,
                        'label': 'S'/'A'/'B'/'C',
                        ...
                    },
                    ...
                ],
                'score_distribution': {
                    'S': 개수,
                    'A': 개수,
                    'B': 개수,
                    'C': 개수
                }
            }
        """
        try:
            # 1. Oracle DB에서 MEMBER.TASTE 조회
            member_query = """
                SELECT MEMBER_ID, TASTE
                FROM MEMBER
                WHERE MEMBER_ID = :member_id
            """
            members = fetch_all_dict(member_query, {'member_id': member_id})
            
            if not members:
                return {
                    'success': False,
                    'message': f'MEMBER_ID {member_id}를 찾을 수 없습니다.',
                    'recommendations': []
                }
            
            member = members[0]
            taste_value = member.get('TASTE', '')
            
            # TASTE 값을 문자열로 변환 (정수형일 수 있음)
            # Oracle DB에서 TASTE가 NUMBER 타입으로 저장되어 있을 수 있음
            if taste_value is None:
                taste_str = ''
            elif isinstance(taste_value, (int, float)):
                # 정수형이면 문자열로 변환
                # 단, 정수형 TASTE는 태그 ID일 수 있으므로 경고 로그 출력
                taste_str = str(taste_value)
                logger.warning(
                    f"MEMBER_ID {member_id}의 TASTE가 정수형입니다: {taste_value} (타입: {type(taste_value)}). "
                    f"문자열 형식(예: '미니멀,모던,빈티지')이어야 합니다."
                )
            else:
                # 문자열이거나 다른 타입인 경우 문자열로 변환
                taste_str = str(taste_value) if taste_value else ''
            
            # 최종 검증: taste_str이 비어있지 않은지 확인
            if taste_str and not isinstance(taste_str, str):
                logger.warning(f"MEMBER_ID {member_id}의 TASTE 변환 후 타입이 예상과 다릅니다: {type(taste_str)}")
                taste_str = str(taste_str) if taste_str else ''
            
            if not taste_str or not taste_str.strip():
                return {
                    'success': False,
                    'message': f'MEMBER_ID {member_id}의 TASTE가 없습니다.',
                    'recommendations': []
                }
            
            # 2. Django DB에서 제품 조회 (Oracle 호환)
            products_query = Product.objects.filter(is_active=True)
            
            if category_filter:
                products_query = products_query.filter(category__in=category_filter)
            
            # Oracle DB 호환: select_related 대신 prefetch_related 사용
            # select_related는 Oracle에서 JOIN 쿼리 생성 시 SQL 문법 오류를 일으킬 수 있음
            # SQL 쿼리 로깅 추가 (디버깅용)
            try:
                # 쿼리 문자열 로깅 (디버깅용)
                query_sql = str(products_query.query)
                logger.debug(f"[Content-Based Filtering] SQL 쿼리: {query_sql[:500]}...")  # 처음 500자만
                
                # Oracle DB 호환: 슬라이싱을 안전하게 처리
                # 먼저 ID만 조회 (더 가벼운 쿼리, Oracle에서 안전)
                try:
                    product_ids = list(products_query.values_list('id', flat=True)[:200])
                except Exception as slice_error:
                    # 슬라이싱 실패 시 전체 ID 조회 후 Python에서 제한
                    logger.warning(f"Oracle 슬라이싱 실패, 전체 조회 후 제한: {slice_error}")
                    all_ids = list(products_query.values_list('id', flat=True))
                    product_ids = all_ids[:200]
                
                if not product_ids:
                    products = []
                else:
                    # ID로 제품과 spec을 함께 조회 (prefetch_related 사용)
                    # prefetch_related는 별도 쿼리로 조회하여 Oracle 호환성 향상
                    products = list(
                        Product.objects.filter(id__in=product_ids)
                        .prefetch_related('spec')
                        .order_by('id')  # 일관된 순서 보장
                    )
                
            except Exception as e:
                # 조회 실패 시 빈 리스트 반환
                logger.error(f"제품 조회 실패: {e}", exc_info=True)
                # SQL 쿼리 정보도 로깅
                try:
                    query_sql = str(products_query.query)
                    logger.error(f"실패한 SQL 쿼리: {query_sql[:1000]}")  # 처음 1000자만
                except:
                    pass
                products = []
            
            # 3. 각 제품에 대해 유사도 계산
            scored_products = []
            
            for product in products:
                try:
                    spec = product.spec if hasattr(product, 'spec') else None
                    score = self.get_similarity_score(taste_str, product, spec)
                    
                    # 점수가 0이면 카테고리 매칭만으로도 기본 점수 부여
                    if score == 0.0:
                        # 카테고리만 매칭되어도 최소 점수 부여 (0.1)
                        product_features = self.extract_product_features(product, spec)
                        if product_features:  # 피처가 하나라도 있으면
                            score = 0.1  # 최소 점수
                    
                    if score >= min_score:
                        label = self.get_score_label(score)
                        scored_products.append({
                            'product': product,
                            'score': score,
                            'label': label
                        })
                except Exception as e:
                    logger.warning(f"제품 {product.id} 유사도 계산 실패: {e}")
                    continue
            
            # 4. 점수 순으로 정렬
            scored_products.sort(key=lambda x: x['score'], reverse=True)
            
            # 5. 상위 N개 선택
            top_products = scored_products[:limit]
            
            # 6. 점수 분포 계산
            score_distribution = {'S': 0, 'A': 0, 'B': 0, 'C': 0}
            for item in top_products:
                label = item['label']
                score_distribution[label] = score_distribution.get(label, 0) + 1
            
            # 7. 결과 포맷팅
            recommendations = []
            for item in top_products:
                product = item['product']
                recommendations.append({
                    'product_id': product.id,
                    'name': product.name,
                    'model_number': product.model_number or '',
                    'category': product.category,
                    'category_display': product.get_category_display(),
                    'price': float(product.price) if product.price else 0,
                    'discount_price': float(product.discount_price) if product.discount_price else None,
                    'image_url': product.image_url or '',
                    'score': round(item['score'], 3),
                    'label': item['label'],
                })
            
            return {
                'success': True,
                'count': len(recommendations),
                'member_id': member_id,
                'taste': taste_str,
                'recommendations': recommendations,
                'score_distribution': score_distribution
            }
            
        except Exception as e:
            logger.error(f"콘텐츠 기반 추천 오류: {e}", exc_info=True)
            return {
                'success': False,
                'message': f'추천 실패: {str(e)}',
                'recommendations': []
            }
    
    def get_recommendations_by_taste_string(
        self,
        taste_str: str,
        limit: int = 10,
        min_score: float = 0.3,
        category_filter: Optional[List[str]] = None
    ) -> Dict:
        """
        TASTE 문자열을 직접 받아서 제품 추천 (MEMBER 테이블 조회 없이)
        
        Args:
            taste_str: TASTE 문자열 (예: "미니멀,모던,빈티지")
            limit: 추천 개수
            min_score: 최소 유사도 점수
            category_filter: 카테고리 필터 (선택사항)
        
        Returns:
            추천 결과 딕셔너리
        """
        try:
            if not taste_str:
                return {
                    'success': False,
                    'message': 'TASTE 문자열이 없습니다.',
                    'recommendations': []
                }
            
            # Django DB에서 제품 조회 (Oracle 호환)
            products_query = Product.objects.filter(is_active=True)
            
            if category_filter:
                products_query = products_query.filter(category__in=category_filter)
            
            # Oracle DB 호환: select_related 대신 prefetch_related 사용
            # select_related는 Oracle에서 JOIN 쿼리 생성 시 SQL 문법 오류를 일으킬 수 있음
            # SQL 쿼리 로깅 추가 (디버깅용)
            try:
                # 쿼리 문자열 로깅 (디버깅용)
                query_sql = str(products_query.query)
                logger.debug(f"[Content-Based Filtering] SQL 쿼리: {query_sql[:500]}...")  # 처음 500자만
                
                # Oracle DB 호환: 슬라이싱을 안전하게 처리
                # 먼저 ID만 조회 (더 가벼운 쿼리, Oracle에서 안전)
                try:
                    product_ids = list(products_query.values_list('id', flat=True)[:200])
                except Exception as slice_error:
                    # 슬라이싱 실패 시 전체 ID 조회 후 Python에서 제한
                    logger.warning(f"Oracle 슬라이싱 실패, 전체 조회 후 제한: {slice_error}")
                    all_ids = list(products_query.values_list('id', flat=True))
                    product_ids = all_ids[:200]
                
                if not product_ids:
                    products = []
                else:
                    # ID로 제품과 spec을 함께 조회 (prefetch_related 사용)
                    # prefetch_related는 별도 쿼리로 조회하여 Oracle 호환성 향상
                    products = list(
                        Product.objects.filter(id__in=product_ids)
                        .prefetch_related('spec')
                        .order_by('id')  # 일관된 순서 보장
                    )
                
            except Exception as e:
                # 조회 실패 시 빈 리스트 반환
                logger.error(f"제품 조회 실패: {e}", exc_info=True)
                # SQL 쿼리 정보도 로깅
                try:
                    query_sql = str(products_query.query)
                    logger.error(f"실패한 SQL 쿼리: {query_sql[:1000]}")  # 처음 1000자만
                except:
                    pass
                products = []
            
            # 각 제품에 대해 유사도 계산
            scored_products = []
            
            for product in products:
                try:
                    spec = product.spec if hasattr(product, 'spec') else None
                    score = self.get_similarity_score(taste_str, product, spec)
                    
                    # 점수가 0이면 카테고리 매칭만으로도 기본 점수 부여
                    if score == 0.0:
                        # 카테고리만 매칭되어도 최소 점수 부여 (0.1)
                        product_features = self.extract_product_features(product, spec)
                        if product_features:  # 피처가 하나라도 있으면
                            score = 0.1  # 최소 점수
                    
                    if score >= min_score:
                        label = self.get_score_label(score)
                        scored_products.append({
                            'product': product,
                            'score': score,
                            'label': label
                        })
                except Exception as e:
                    logger.warning(f"제품 {product.id} 유사도 계산 실패: {e}")
                    continue
            
            # 점수 순으로 정렬
            scored_products.sort(key=lambda x: x['score'], reverse=True)
            
            # 상위 N개 선택
            top_products = scored_products[:limit]
            
            # 점수 분포 계산
            score_distribution = {'S': 0, 'A': 0, 'B': 0, 'C': 0}
            for item in top_products:
                label = item['label']
                score_distribution[label] = score_distribution.get(label, 0) + 1
            
            # 결과 포맷팅
            recommendations = []
            for item in top_products:
                product = item['product']
                recommendations.append({
                    'product_id': product.id,
                    'name': product.name,
                    'model_number': product.model_number or '',
                    'category': product.category,
                    'category_display': product.get_category_display(),
                    'price': float(product.price) if product.price else 0,
                    'discount_price': float(product.discount_price) if product.discount_price else None,
                    'image_url': product.image_url or '',
                    'score': round(item['score'], 3),
                    'label': item['label'],
                })
            
            return {
                'success': True,
                'count': len(recommendations),
                'taste': taste_str,
                'recommendations': recommendations,
                'score_distribution': score_distribution
            }
            
        except Exception as e:
            logger.error(f"콘텐츠 기반 추천 오류: {e}", exc_info=True)
            return {
                'success': False,
                'message': f'추천 실패: {str(e)}',
                'recommendations': []
            }


# 싱글톤 인스턴스
content_based_filtering = ContentBasedFiltering()

