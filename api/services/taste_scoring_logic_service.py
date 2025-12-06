"""
Taste별 독립적인 Scoring Logic 관리 서비스

각 taste_id마다 완전히 독립적인 scoring logic을 관리하고 적용합니다.
기본 로직을 유지하면서 taste별로 override 가능한 구조입니다.
"""
import json
from pathlib import Path
from typing import Dict, Optional, List
from django.conf import settings
from api.utils.category_mapping import MAIN_CATEGORY_TO_DJANGO_CATEGORY, DJANGO_CATEGORY_TO_MAIN_CATEGORIES
from api.utils.dynamic_taste_scoring import DynamicTasteScoring


class TasteScoringLogicService:
    """
    Taste별 Scoring Logic 관리 서비스
    
    각 taste_id마다 독립적인 scoring logic을 제공합니다.
    - 기본 로직 유지
    - Taste별 독립 파일 지원
    - 동적 생성 지원
    - 모든 MAIN_CATEGORY 지원
    """
    
    _instance = None
    _logic_cache = {}  # taste_id -> logic 캐시
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(TasteScoringLogicService, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        # 경로 설정
        self.base_logic_path = Path(__file__).parent.parent / 'scoring_logic' / 'taste_scoring_logics.json'
        self.tastes_dir = Path(__file__).parent.parent / 'scoring_logic' / 'tastes'
        
        # tastes 디렉토리 생성 (없으면)
        self.tastes_dir.mkdir(parents=True, exist_ok=True)
        
        self._initialized = True
    
    def get_logic_for_taste(
        self,
        taste_id: int,
        onboarding_data: Optional[Dict] = None
    ) -> Optional[Dict]:
        """
        taste_id에 해당하는 Scoring Logic 반환
        
        우선순위:
        1. Taste별 독립 파일 (tastes/taste_{taste_id}.json)
        2. 기존 로직 파일에서 적용되는 logic
        3. 동적 생성 (onboarding_data 제공 시)
        4. 기본 로직
        
        Args:
            taste_id: 취향 ID (1~120)
            onboarding_data: 온보딩 데이터 (동적 생성 시 사용)
        
        Returns:
            Scoring Logic 딕셔너리
        """
        # 캐시 확인
        cache_key = f"{taste_id}_{hash(str(onboarding_data)) if onboarding_data else 'default'}"
        if cache_key in self._logic_cache:
            return self._logic_cache[cache_key]
        
        logic = None
        
        # 1. Taste별 독립 파일 확인
        taste_file = self.tastes_dir / f"taste_{taste_id:03d}.json"
        if taste_file.exists():
            try:
                with open(taste_file, 'r', encoding='utf-8') as f:
                    logic = json.load(f)
                logic['source'] = 'taste_file'
            except Exception as e:
                print(f"[TasteScoringLogicService] Error loading taste file {taste_file}: {e}")
        
        # 2. 기존 로직 파일에서 찾기
        if logic is None:
            logic = self._get_logic_from_shared_file(taste_id)
            if logic:
                logic['source'] = 'shared_file'
        
        # 3. 동적 생성 (onboarding_data 제공 시)
        if logic is None and onboarding_data:
            logic = self._create_dynamic_logic(taste_id, onboarding_data)
            if logic:
                logic['source'] = 'dynamic'
        
        # 4. 기본 로직 생성
        if logic is None:
            logic = self.create_base_logic_for_taste(taste_id, onboarding_data)
            logic['source'] = 'default'
        
        # 캐시 저장
        if logic:
            self._logic_cache[cache_key] = logic
        
        return logic
    
    def _get_logic_from_shared_file(self, taste_id: int) -> Optional[Dict]:
        """기존 공유 로직 파일에서 taste_id에 해당하는 logic 찾기"""
        if not self.base_logic_path.exists():
            return None
        
        try:
            with open(self.base_logic_path, 'r', encoding='utf-8') as f:
                logics = json.load(f)
            
            for logic in logics:
                applies_to = logic.get('applies_to_taste_ids', [])
                if taste_id in applies_to:
                    # 복사본 반환 (수정 가능하도록)
                    return json.loads(json.dumps(logic))
        
        except Exception as e:
            print(f"[TasteScoringLogicService] Error loading shared logic file: {e}")
        
        return None
    
    def _create_dynamic_logic(self, taste_id: int, onboarding_data: Dict) -> Optional[Dict]:
        """온보딩 데이터 기반 동적 logic 생성"""
        try:
            dynamic_logic = DynamicTasteScoring.generate_scoring_logic(onboarding_data)
            
            # 모든 MAIN_CATEGORY 지원하도록 확장
            base_logic = self.create_base_logic_for_taste(taste_id, onboarding_data)
            
            # 동적 가중치를 base_logic에 병합
            if 'weights' in dynamic_logic:
                for category, weights in dynamic_logic['weights'].items():
                    if category in base_logic.get('weights', {}):
                        base_logic['weights'][category].update(weights)
            
            # 보너스/페널티 병합
            base_logic['bonuses'] = dynamic_logic.get('bonuses', base_logic.get('bonuses', []))
            base_logic['penalties'] = dynamic_logic.get('penalties', base_logic.get('penalties', []))
            
            return base_logic
        
        except Exception as e:
            print(f"[TasteScoringLogicService] Error creating dynamic logic: {e}")
            return None
    
    def create_base_logic_for_taste(
        self,
        taste_id: int,
        onboarding_data: Optional[Dict] = None
    ) -> Dict:
        """
        Taste별 기본 로직 생성
        
        모든 MAIN_CATEGORY를 지원하는 기본 로직을 생성합니다.
        
        Args:
            taste_id: 취향 ID
            onboarding_data: 온보딩 데이터 (없으면 기본값 사용)
        
        Returns:
            기본 로직 딕셔너리
        """
        from api.utils.scoring import CATEGORY_WEIGHTS
        
        # 모든 MAIN_CATEGORY 목록 가져오기
        all_main_categories = self._get_all_main_categories()
        
        # 기본 가중치 생성 (각 MAIN_CATEGORY별로)
        weights = {}
        
        for main_category in all_main_categories:
            django_category = MAIN_CATEGORY_TO_DJANGO_CATEGORY.get(main_category, 'LIVING')
            
            # Django category의 기본 가중치 복사
            if django_category in CATEGORY_WEIGHTS:
                weights[main_category] = CATEGORY_WEIGHTS[django_category].copy()
            else:
                weights[main_category] = CATEGORY_WEIGHTS.get('default', {}).copy()
        
        # 온보딩 데이터 기반 조정 (있는 경우)
        if onboarding_data:
            weights = self._adjust_weights_by_onboarding(weights, onboarding_data)
        
        return {
            "logic_id": f"base_{taste_id}",
            "logic_name": f"Base_Logic_{taste_id:03d}",
            "taste_id": taste_id,
            "weights": weights,
            "bonuses": [],
            "penalties": [],
            "filters": {
                "must_have": [],
                "should_have": [],
                "exclude": []
            }
        }
    
    def _get_all_main_categories(self) -> List[str]:
        """모든 MAIN_CATEGORY 목록 반환"""
        all_categories = set()
        
        # 매핑에서 모든 MAIN_CATEGORY 수집
        for main_cat in MAIN_CATEGORY_TO_DJANGO_CATEGORY.keys():
            all_categories.add(main_cat)
        
        # 역매핑에서도 수집
        for main_cats in DJANGO_CATEGORY_TO_MAIN_CATEGORIES.values():
            all_categories.update(main_cats)
        
        return sorted(list(all_categories))
    
    def _adjust_weights_by_onboarding(self, weights: Dict, onboarding_data: Dict) -> Dict:
        """온보딩 데이터 기반 가중치 조정"""
        # DynamicTasteScoring의 조정 로직 활용
        try:
            # 기본 조정
            adjusted_weights = {}
            
            vibe = onboarding_data.get('vibe', 'modern')
            priority = onboarding_data.get('priority', [])
            if isinstance(priority, str):
                priority = [priority]
            budget_level = onboarding_data.get('budget_level', 'medium')
            household_size = onboarding_data.get('household_size', 2)
            pyung = onboarding_data.get('pyung', 25)
            
            # 각 MAIN_CATEGORY별로 조정
            for main_category, category_weights in weights.items():
                adjusted_weights[main_category] = category_weights.copy()
                
                # Vibe 기반 조정
                self._apply_vibe_adjustment(adjusted_weights[main_category], vibe)
                
                # Priority 기반 조정
                self._apply_priority_adjustment(adjusted_weights[main_category], priority)
                
                # Budget 기반 조정
                self._apply_budget_adjustment(adjusted_weights[main_category], budget_level)
                
                # 가중치 정규화
                self._normalize_weights(adjusted_weights[main_category])
            
            return adjusted_weights
        
        except Exception as e:
            print(f"[TasteScoringLogicService] Error adjusting weights: {e}")
            return weights
    
    def _apply_vibe_adjustment(self, weights: Dict, vibe: str):
        """Vibe 기반 가중치 조정"""
        vibe_lower = vibe.lower()
        
        if 'modern' in vibe_lower:
            if "design" in weights:
                weights["design"] *= 1.2
            if "features" in weights:
                weights["features"] *= 1.1
        
        elif 'cozy' in vibe_lower:
            if "price_match" in weights:
                weights["price_match"] *= 1.2
            if "power_consumption" in weights:
                weights["power_consumption"] *= 1.1
        
        elif 'luxury' in vibe_lower:
            if "design" in weights:
                weights["design"] *= 1.3
            if "features" in weights:
                weights["features"] *= 1.2
    
    def _apply_priority_adjustment(self, weights: Dict, priority: List[str]):
        """Priority 기반 가중치 조정"""
        priority_lower = [p.lower() for p in priority]
        
        if 'design' in priority_lower:
            if "design" in weights:
                weights["design"] *= 1.3
        
        if 'tech' in priority_lower or 'ai' in priority_lower:
            if "features" in weights:
                weights["features"] *= 1.3
            if "resolution" in weights:
                weights["resolution"] *= 1.2
        
        if 'value' in priority_lower:
            if "price_match" in weights:
                weights["price_match"] *= 1.3
        
        if 'eco' in priority_lower:
            if "energy_efficiency" in weights:
                weights["energy_efficiency"] *= 1.3
            if "power_consumption" in weights:
                weights["power_consumption"] *= 1.3
    
    def _apply_budget_adjustment(self, weights: Dict, budget_level: str):
        """Budget 기반 가중치 조정"""
        budget_lower = budget_level.lower()
        
        if 'low' in budget_lower:
            if "price_match" in weights:
                weights["price_match"] *= 1.3
        
        elif 'high' in budget_lower:
            if "design" in weights:
                weights["design"] *= 1.2
            if "features" in weights:
                weights["features"] *= 1.2
    
    def _normalize_weights(self, weights: Dict):
        """가중치 정규화 (합이 1.0이 되도록)"""
        total = sum(weights.values())
        if total > 0:
            for key in weights:
                weights[key] /= total
    
    def save_taste_logic(self, taste_id: int, logic: Dict) -> bool:
        """
        Taste별 logic을 파일로 저장
        
        Args:
            taste_id: 취향 ID
            logic: 저장할 로직 딕셔너리
        
        Returns:
            저장 성공 여부
        """
        try:
            taste_file = self.tastes_dir / f"taste_{taste_id:03d}.json"
            
            # taste_id 추가
            logic['taste_id'] = taste_id
            
            with open(taste_file, 'w', encoding='utf-8') as f:
                json.dump(logic, f, ensure_ascii=False, indent=2)
            
            # 캐시 무효화
            self._invalidate_cache(taste_id)
            
            return True
        
        except Exception as e:
            print(f"[TasteScoringLogicService] Error saving taste logic: {e}")
            return False
    
    def _invalidate_cache(self, taste_id: int):
        """특정 taste_id의 캐시 무효화"""
        keys_to_remove = [k for k in self._logic_cache.keys() if k.startswith(f"{taste_id}_")]
        for key in keys_to_remove:
            del self._logic_cache[key]
    
    def clear_cache(self):
        """전체 캐시 초기화"""
        self._logic_cache.clear()


# 싱글톤 인스턴스
taste_scoring_logic_service = TasteScoringLogicService()
