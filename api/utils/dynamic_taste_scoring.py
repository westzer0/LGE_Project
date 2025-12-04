"""
온보딩 데이터를 기반으로 동적으로 taste별 scoring logic을 생성하는 모듈

온보딩 데이터의 속성(vibe, priority, budget_level, household_size 등)을 기반으로
각 taste별로 다른 가중치와 보너스/페널티를 동적으로 계산합니다.
"""
from typing import Dict, List, Optional
from api.utils.taste_classifier import taste_classifier


class DynamicTasteScoring:
    """
    온보딩 데이터를 기반으로 동적으로 scoring logic을 생성하는 클래스
    """
    
    # 기본 가중치 템플릿 (카테고리별)
    BASE_WEIGHTS = {
        "TV": {
            "resolution": 0.15,
            "brightness": 0.10,
            "refresh_rate": 0.10,
            "panel_type": 0.10,
            "power_consumption": 0.10,
            "size": 0.10,
            "price_match": 0.15,
            "features": 0.10,
            "design": 0.10,
        },
        "KITCHEN": {
            "capacity": 0.20,
            "energy_efficiency": 0.15,
            "features": 0.15,
            "size": 0.10,
            "price_match": 0.15,
            "design": 0.15,
            "resolution": 0.05,
            "refresh_rate": 0.05,
        },
        "LIVING": {
            "audio_quality": 0.20,
            "connectivity": 0.15,
            "power_consumption": 0.10,
            "size": 0.10,
            "price_match": 0.15,
            "features": 0.15,
            "design": 0.10,
            "resolution": 0.05,
        },
        "default": {
            "price_match": 0.25,
            "features": 0.20,
            "energy_efficiency": 0.15,
            "size": 0.15,
            "design": 0.15,
            "capacity": 0.10,
        }
    }
    
    @staticmethod
    def generate_scoring_logic(onboarding_data: Dict) -> Dict:
        """
        온보딩 데이터를 기반으로 scoring logic 생성
        
        Args:
            onboarding_data: 온보딩 데이터 딕셔너리
        
        Returns:
            scoring logic 딕셔너리 (weights, bonuses, penalties 포함)
        """
        vibe = onboarding_data.get('vibe', 'modern')
        priority = onboarding_data.get('priority', [])
        if isinstance(priority, str):
            priority = [priority]
        budget_level = onboarding_data.get('budget_level', 'medium')
        household_size = onboarding_data.get('household_size', 2)
        pyung = onboarding_data.get('pyung', 25)
        has_pet = onboarding_data.get('has_pet', False)
        cooking = onboarding_data.get('cooking', 'sometimes')
        laundry = onboarding_data.get('laundry', 'weekly')
        media = onboarding_data.get('media', 'balanced')
        
        # 1. 기본 가중치 복사
        weights = {
            "TV": DynamicTasteScoring.BASE_WEIGHTS["TV"].copy(),
            "KITCHEN": DynamicTasteScoring.BASE_WEIGHTS["KITCHEN"].copy(),
            "LIVING": DynamicTasteScoring.BASE_WEIGHTS["LIVING"].copy(),
            "default": DynamicTasteScoring.BASE_WEIGHTS["default"].copy(),
        }
        
        # 2. Vibe 기반 가중치 조정
        DynamicTasteScoring._adjust_by_vibe(weights, vibe)
        
        # 3. Priority 기반 가중치 조정
        DynamicTasteScoring._adjust_by_priority(weights, priority)
        
        # 4. Budget 기반 가중치 조정
        DynamicTasteScoring._adjust_by_budget(weights, budget_level)
        
        # 5. Household size 기반 가중치 조정
        DynamicTasteScoring._adjust_by_household_size(weights, household_size)
        
        # 6. 평수 기반 가중치 조정
        DynamicTasteScoring._adjust_by_pyung(weights, pyung)
        
        # 7. 생활 패턴 기반 가중치 조정
        DynamicTasteScoring._adjust_by_lifestyle(weights, cooking, laundry, media)
        
        # 8. 가중치 정규화 (합이 1.0이 되도록)
        for category in weights:
            DynamicTasteScoring._normalize_weights(weights[category])
        
        # 9. 보너스/페널티 생성
        bonuses = DynamicTasteScoring._generate_bonuses(onboarding_data)
        penalties = DynamicTasteScoring._generate_penalties(onboarding_data)
        
        return {
            "weights": weights,
            "bonuses": bonuses,
            "penalties": penalties,
        }
    
    @staticmethod
    def _adjust_by_vibe(weights: Dict, vibe: str):
        """Vibe 기반 가중치 조정"""
        vibe_lower = vibe.lower()
        
        if 'modern' in vibe_lower or '모던' in vibe_lower:
            # 모던: 디자인과 기술 중시
            for category in ["TV", "KITCHEN", "LIVING"]:
                if "design" in weights[category]:
                    weights[category]["design"] *= 1.3
                if "features" in weights[category]:
                    weights[category]["features"] *= 1.2
                if "price_match" in weights[category]:
                    weights[category]["price_match"] *= 0.8
        
        elif 'classic' in vibe_lower or '클래식' in vibe_lower:
            # 클래식: 전통적이고 실용적
            for category in ["TV", "KITCHEN", "LIVING"]:
                if "design" in weights[category]:
                    weights[category]["design"] *= 0.9
                if "price_match" in weights[category]:
                    weights[category]["price_match"] *= 1.2
                if "energy_efficiency" in weights[category]:
                    weights[category]["energy_efficiency"] *= 1.1
        
        elif 'cozy' in vibe_lower or '코지' in vibe_lower:
            # 코지: 편안함과 실용성
            for category in ["TV", "KITCHEN", "LIVING"]:
                if "price_match" in weights[category]:
                    weights[category]["price_match"] *= 1.3
                if "power_consumption" in weights[category]:
                    weights[category]["power_consumption"] *= 1.2
                if "design" in weights[category]:
                    weights[category]["design"] *= 0.9
        
        elif 'luxury' in vibe_lower or '럭셔리' in vibe_lower:
            # 럭셔리: 프리미엄과 고급 기능
            for category in ["TV", "KITCHEN", "LIVING"]:
                if "design" in weights[category]:
                    weights[category]["design"] *= 1.5
                if "features" in weights[category]:
                    weights[category]["features"] *= 1.3
                if "price_match" in weights[category]:
                    weights[category]["price_match"] *= 0.6
    
    @staticmethod
    def _adjust_by_priority(weights: Dict, priority: List[str]):
        """Priority 기반 가중치 조정"""
        priority_lower = [p.lower() for p in priority]
        
        if 'design' in priority_lower or '디자인' in str(priority_lower):
            # 디자인 우선순위
            for category in ["TV", "KITCHEN", "LIVING"]:
                weights[category]["design"] *= 1.5
                if category == "TV" and "panel_type" in weights[category]:
                    weights[category]["panel_type"] *= 1.2
        
        if 'tech' in priority_lower or 'ai' in priority_lower or '스마트' in str(priority_lower):
            # 기술 우선순위
            for category in ["TV", "KITCHEN", "LIVING"]:
                weights[category]["features"] *= 1.5
                if category == "TV":
                    if "resolution" in weights[category]:
                        weights[category]["resolution"] *= 1.3
                    if "refresh_rate" in weights[category]:
                        weights[category]["refresh_rate"] *= 1.3
        
        if 'value' in priority_lower or '가성비' in str(priority_lower) or '실용' in str(priority_lower):
            # 가성비 우선순위
            for category in ["TV", "KITCHEN", "LIVING"]:
                if "price_match" in weights[category]:
                    weights[category]["price_match"] *= 1.5
                if "energy_efficiency" in weights[category]:
                    weights[category]["energy_efficiency"] *= 1.2
                if "design" in weights[category]:
                    weights[category]["design"] *= 0.8
        
        if 'eco' in priority_lower or '친환경' in str(priority_lower) or '에너지' in str(priority_lower):
            # 친환경 우선순위
            for category in ["TV", "KITCHEN", "LIVING"]:
                if "energy_efficiency" in weights[category]:
                    weights[category]["energy_efficiency"] *= 1.5
                if "power_consumption" in weights[category]:
                    weights[category]["power_consumption"] *= 1.5
                if "price_match" in weights[category]:
                    weights[category]["price_match"] *= 1.1
    
    @staticmethod
    def _adjust_by_budget(weights: Dict, budget_level: str):
        """Budget 기반 가중치 조정"""
        budget_lower = budget_level.lower()
        
        if 'low' in budget_lower or '낮' in budget_lower or '실속' in budget_lower:
            # 낮은 예산: 가격 최우선
            for category in ["TV", "KITCHEN", "LIVING"]:
                if "price_match" in weights[category]:
                    weights[category]["price_match"] *= 1.5
                if "design" in weights[category]:
                    weights[category]["design"] *= 0.7
                if "features" in weights[category]:
                    weights[category]["features"] *= 0.8
        
        elif 'high' in budget_lower or '높' in budget_lower or '고급' in budget_lower:
            # 높은 예산: 디자인과 기능 중시
            for category in ["TV", "KITCHEN", "LIVING"]:
                if "design" in weights[category]:
                    weights[category]["design"] *= 1.3
                if "features" in weights[category]:
                    weights[category]["features"] *= 1.3
                if "price_match" in weights[category]:
                    weights[category]["price_match"] *= 0.7
    
    @staticmethod
    def _adjust_by_household_size(weights: Dict, household_size: int):
        """Household size 기반 가중치 조정"""
        if household_size >= 4:
            # 대가족: 용량과 기능 중시
            if "capacity" in weights["KITCHEN"]:
                weights["KITCHEN"]["capacity"] *= 1.5
            if "features" in weights["KITCHEN"]:
                weights["KITCHEN"]["features"] *= 1.2
            if "size" in weights["LIVING"]:
                weights["LIVING"]["size"] *= 1.2
        elif household_size == 1:
            # 1인 가구: 소형과 효율 중시
            if "capacity" in weights["KITCHEN"]:
                weights["KITCHEN"]["capacity"] *= 0.7
            if "size" in weights["KITCHEN"]:
                weights["KITCHEN"]["size"] *= 1.3
            if "size" in weights["TV"]:
                weights["TV"]["size"] *= 0.9
            if "size" in weights["LIVING"]:
                weights["LIVING"]["size"] *= 0.9
    
    @staticmethod
    def _adjust_by_pyung(weights: Dict, pyung: int):
        """평수 기반 가중치 조정"""
        if pyung <= 20:
            # 소형 주택: 크기와 효율 중시
            if "size" in weights["TV"]:
                weights["TV"]["size"] *= 0.8
            if "size" in weights["KITCHEN"]:
                weights["KITCHEN"]["size"] *= 1.3
            if "capacity" in weights["KITCHEN"]:
                weights["KITCHEN"]["capacity"] *= 0.8
            if "size" in weights["LIVING"]:
                weights["LIVING"]["size"] *= 0.8
        elif pyung >= 40:
            # 대형 주택: 크기와 용량 중시
            if "size" in weights["TV"]:
                weights["TV"]["size"] *= 1.3
            if "capacity" in weights["KITCHEN"]:
                weights["KITCHEN"]["capacity"] *= 1.3
            if "size" in weights["LIVING"]:
                weights["LIVING"]["size"] *= 1.3
    
    @staticmethod
    def _adjust_by_lifestyle(weights: Dict, cooking: str, laundry: str, media: str):
        """생활 패턴 기반 가중치 조정"""
        # 요리 빈도
        if cooking in ['daily', '매일']:
            if "features" in weights["KITCHEN"]:
                weights["KITCHEN"]["features"] *= 1.3
            if "capacity" in weights["KITCHEN"]:
                weights["KITCHEN"]["capacity"] *= 1.2
        elif cooking in ['rarely', '거의 안함']:
            if "capacity" in weights["KITCHEN"]:
                weights["KITCHEN"]["capacity"] *= 0.8
            if "price_match" in weights["KITCHEN"]:
                weights["KITCHEN"]["price_match"] *= 1.2
        
        # 세탁 빈도
        if laundry in ['daily', '매일']:
            if "features" in weights["LIVING"]:
                weights["LIVING"]["features"] *= 1.2
            if "capacity" in weights["LIVING"]:
                weights["LIVING"]["capacity"] *= 1.2
        
        # 미디어 사용
        if media in ['high', '높음']:
            if "resolution" in weights["TV"]:
                weights["TV"]["resolution"] *= 1.4
            if "brightness" in weights["TV"]:
                weights["TV"]["brightness"] *= 1.3
            if "refresh_rate" in weights["TV"]:
                weights["TV"]["refresh_rate"] *= 1.3
        elif media in ['low', '낮음']:
            if "price_match" in weights["TV"]:
                weights["TV"]["price_match"] *= 1.2
            if "resolution" in weights["TV"]:
                weights["TV"]["resolution"] *= 0.8
    
    @staticmethod
    def _normalize_weights(weight_dict: Dict):
        """가중치 정규화 (합이 1.0이 되도록)"""
        total = sum(weight_dict.values())
        if total > 0:
            for key in weight_dict:
                weight_dict[key] /= total
    
    @staticmethod
    def _generate_bonuses(onboarding_data: Dict) -> List[Dict]:
        """보너스 생성"""
        bonuses = []
        priority = onboarding_data.get('priority', [])
        if isinstance(priority, str):
            priority = [priority]
        priority_lower = [p.lower() for p in priority]
        household_size = onboarding_data.get('household_size', 2)
        budget_level = onboarding_data.get('budget_level', 'medium')
        
        # 디자인 우선순위: OBJET/SIGNATURE 보너스
        if 'design' in priority_lower or '디자인' in str(priority_lower):
            bonuses.append({
                "condition": "OBJET 또는 오브제 라인업",
                "bonus": 0.15,
                "reason": "디자인 우선순위에 부합"
            })
            bonuses.append({
                "condition": "SIGNATURE 또는 시그니처 라인업",
                "bonus": 0.12,
                "reason": "프리미엄 디자인"
            })
        
        # 기술 우선순위: AI/스마트 기능 보너스
        if 'tech' in priority_lower or 'ai' in priority_lower or '스마트' in str(priority_lower):
            bonuses.append({
                "condition": "AI 또는 스마트 기능 포함",
                "bonus": 0.15,
                "reason": "기술 우선순위에 부합"
            })
        
        # 대가족: 대용량 보너스
        if household_size >= 4:
            bonuses.append({
                "condition": "대용량 제품 (800L 이상 냉장고, 20kg 이상 세탁기)",
                "bonus": 0.12,
                "reason": "가족 구성에 적합한 용량"
            })
        
        # 높은 예산: 프리미엄 기능 보너스
        if 'high' in budget_level.lower() or '고급' in budget_level.lower():
            bonuses.append({
                "condition": "프리미엄 기능 포함",
                "bonus": 0.10,
                "reason": "고급형 예산에 적합"
            })
        
        return bonuses
    
    @staticmethod
    def _generate_penalties(onboarding_data: Dict) -> List[Dict]:
        """페널티 생성"""
        penalties = []
        household_size = onboarding_data.get('household_size', 2)
        pyung = onboarding_data.get('pyung', 25)
        budget_level = onboarding_data.get('budget_level', 'medium')
        
        # 대가족: 소형 제품 페널티
        if household_size >= 4:
            penalties.append({
                "condition": "소형 제품 (300L 이하 냉장고, 미니 세탁기 등)",
                "penalty": -0.2,
                "reason": "가족 구성에 부적합한 용량"
            })
        
        # 소형 주택: 대형 제품 페널티
        if pyung <= 20:
            penalties.append({
                "condition": "대형 제품 (75인치 이상 TV, 대형 가전)",
                "penalty": -0.15,
                "reason": "주거 공간에 부적합한 크기"
            })
        
        # 낮은 예산: 고가 제품 페널티
        if 'low' in budget_level.lower() or '실속' in budget_level.lower():
            penalties.append({
                "condition": "고가 제품 (프리미엄 라인업)",
                "penalty": -0.15,
                "reason": "예산 범위를 초과"
            })
        
        return penalties


def get_dynamic_scoring_logic_for_taste(taste_id: int, onboarding_data: Dict) -> Dict:
    """
    taste_id와 온보딩 데이터를 기반으로 동적 scoring logic 반환
    
    Args:
        taste_id: 취향 ID
        onboarding_data: 온보딩 데이터
    
    Returns:
        scoring logic 딕셔너리
    """
    # 온보딩 데이터를 기반으로 동적 logic 생성
    logic = DynamicTasteScoring.generate_scoring_logic(onboarding_data)
    
    return {
        "logic_id": f"dynamic_{taste_id}",
        "logic_name": f"Dynamic_Scoring_Logic_{taste_id:03d}",
        "taste_id": taste_id,
        "weights": logic["weights"],
        "bonuses": logic["bonuses"],
        "penalties": logic["penalties"],
    }

