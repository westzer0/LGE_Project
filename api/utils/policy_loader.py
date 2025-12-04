"""
정책 테이블 로더

Hard Filter Table과 Weight Table을 JSON 파일에서 로드하고 조회하는 유틸리티
"""
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from functools import lru_cache


class PolicyLoader:
    """정책 테이블 로더 (Singleton)"""
    
    _instance = None
    _hard_filter_rules = None
    _weight_rules = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(PolicyLoader, cls).__new__(cls)
        return cls._instance
    
    @property
    @lru_cache(maxsize=1)
    def hard_filter_rules(self) -> Dict:
        """Hard Filter Table 로드"""
        if self._hard_filter_rules is None:
            rules_file = Path(__file__).parent.parent / 'scoring_logic' / 'hard_filter_rules.json'
            if rules_file.exists():
                with open(rules_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self._hard_filter_rules = data.get('rules', [])
            else:
                self._hard_filter_rules = []
        return self._hard_filter_rules
    
    @property
    @lru_cache(maxsize=1)
    def weight_rules(self) -> Dict:
        """Weight Table 로드"""
        if self._weight_rules is None:
            rules_file = Path(__file__).parent.parent / 'scoring_logic' / 'weight_rules.json'
            if rules_file.exists():
                with open(rules_file, 'r', encoding='utf-8') as f:
                    self._weight_rules = json.load(f)
            else:
                self._weight_rules = {}
        return self._weight_rules
    
    def get_hard_filter_rules(self, key: Tuple[str, str]) -> List[Dict]:
        """
        Hard Filter 규칙 조회
        
        Args:
            key: (onboarding_answer, product_category) 튜플
            
        Returns:
            조건 리스트
        """
        key_list = list(key)
        for rule in self.hard_filter_rules:
            if rule.get('key') == key_list:
                return rule.get('conditions', [])
        return []
    
    def get_spec_score_rules(self, key: Tuple[str, str, str]) -> Optional[Dict]:
        """
        SpecScore 규칙 조회
        
        Args:
            key: (onboarding_answer, product_category, spec_key) 튜플
            
        Returns:
            규칙 딕셔너리
        """
        key_list = list(key)
        for rule in self.weight_rules.get('spec_score_rules', []):
            if rule.get('key') == key_list:
                return rule
        return None
    
    def get_preference_score_rules(self, priority: str, rank: int = 1) -> Optional[Dict]:
        """
        PreferenceScore 규칙 조회
        
        Args:
            priority: 우선순위 (디자인, AI기능, 에너지효율, 가성비)
            rank: 순위 (1, 2, 3)
            
        Returns:
            규칙 딕셔너리
        """
        rank_map = {1: "1순위", 2: "2순위", 3: "3순위"}
        rule_key = [priority, rank_map.get(rank, "1순위")]
        
        for rule in self.weight_rules.get('preference_score_rules', []):
            if rule.get('key') == rule_key:
                return rule
        return None
    
    def get_lifestyle_score_rules(self, lifestyle: str, category: str, spec_key: str) -> Optional[Dict]:
        """
        LifestyleScore 규칙 조회
        
        Args:
            lifestyle: 라이프스타일 (요리_high, 세탁_daily_small, 게임 등)
            category: 제품 카테고리
            spec_key: 스펙 키
            
        Returns:
            규칙 딕셔너리
        """
        rule_key = [lifestyle, category, spec_key]
        
        for rule in self.weight_rules.get('lifestyle_score_rules', []):
            if rule.get('key') == rule_key:
                return rule
        return None
    
    def get_price_score_rules(self) -> List[Dict]:
        """PriceScore 규칙 조회"""
        return self.weight_rules.get('price_score_rules', [])
    
    def get_review_score_rules(self) -> List[Dict]:
        """ReviewScore 규칙 조회"""
        return self.weight_rules.get('review_score_rules', [])


# Singleton 인스턴스
policy_loader = PolicyLoader()

