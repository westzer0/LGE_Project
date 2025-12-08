"""
콘텐츠 기반 필터링을 기존 추천 엔진에 통합하는 예시

이 모듈은 recommendation_engine.py에 콘텐츠 기반 필터링을 통합하는 방법을 보여줍니다.
"""
from typing import Dict, List, Optional
from api.services.content_based_filtering import content_based_filtering
from api.services.recommendation_engine import RecommendationEngine


class HybridRecommendationEngine(RecommendationEngine):
    """
    하이브리드 추천 엔진
    
    기존 규칙 기반 추천 + 콘텐츠 기반 필터링을 결합
    """
    
    def get_recommendations_with_content_filtering(
        self,
        user_profile: dict,
        member_id: Optional[str] = None,
        taste_str: Optional[str] = None,
        use_content_filtering: bool = True,
        content_weight: float = 0.3,  # 콘텐츠 기반 점수 가중치 (0.0 ~ 1.0)
        limit: int = 3
    ) -> dict:
        """
        콘텐츠 기반 필터링을 포함한 하이브리드 추천
        
        Args:
            user_profile: 사용자 프로필
            member_id: MEMBER_ID (Oracle DB)
            taste_str: TASTE 문자열 (member_id가 없을 때 사용)
            use_content_filtering: 콘텐츠 기반 필터링 사용 여부
            content_weight: 콘텐츠 기반 점수 가중치 (0.0 ~ 1.0)
            limit: 추천 개수
        
        Returns:
            추천 결과 딕셔너리
        """
        # 1. 기존 규칙 기반 추천
        rule_based_result = self.get_recommendations(
            user_profile=user_profile,
            limit=limit * 2  # 더 많이 가져와서 필터링
        )
        
        if not rule_based_result['success']:
            return rule_based_result
        
        # 2. 콘텐츠 기반 필터링 적용
        if use_content_filtering and (member_id or taste_str):
            # 콘텐츠 기반 점수 계산
            content_scores = {}
            
            if member_id:
                # MEMBER_ID로 TASTE 조회
                content_result = content_based_filtering.get_recommendations_by_taste(
                    member_id=member_id,
                    limit=100,  # 충분히 많이 가져오기
                    min_score=0.0  # 최소 점수 없음
                )
            else:
                # TASTE 문자열 직접 사용
                content_result = content_based_filtering.get_recommendations_by_taste_string(
                    taste_str=taste_str,
                    limit=100,
                    min_score=0.0
                )
            
            if content_result['success']:
                # 제품 ID -> 콘텐츠 기반 점수 매핑
                for rec in content_result['recommendations']:
                    product_id = rec['product_id']
                    content_scores[product_id] = rec['score']
            
            # 3. 하이브리드 점수 계산 (규칙 기반 점수 + 콘텐츠 기반 점수)
            rule_weight = 1.0 - content_weight
            
            for rec in rule_based_result['recommendations']:
                product_id = rec['product_id']
                rule_score = rec.get('score', 0.5)
                content_score = content_scores.get(product_id, 0.0)
                
                # 하이브리드 점수 = 규칙 기반 점수 * rule_weight + 콘텐츠 기반 점수 * content_weight
                hybrid_score = (rule_score * rule_weight) + (content_score * content_weight)
                rec['score'] = round(hybrid_score, 3)
                rec['rule_score'] = round(rule_score, 3)
                rec['content_score'] = round(content_score, 3)
            
            # 4. 하이브리드 점수 순으로 재정렬
            rule_based_result['recommendations'].sort(
                key=lambda x: x['score'],
                reverse=True
            )
        
        # 5. 상위 N개만 반환
        rule_based_result['recommendations'] = rule_based_result['recommendations'][:limit]
        rule_based_result['count'] = len(rule_based_result['recommendations'])
        
        return rule_based_result


# 싱글톤 인스턴스
hybrid_recommendation_engine = HybridRecommendationEngine()

