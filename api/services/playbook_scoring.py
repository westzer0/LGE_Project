"""
Playbook Scoring Service

점수 breakdown을 활용한 스코어링 로직
"""
from dataclasses import dataclass
from typing import Dict, Any, List
import json
import re


@dataclass
class ScoreBreakdown:
    """점수 Breakdown 구조"""
    spec_score: float = 0.0
    preference_score: float = 0.0
    lifestyle_score: float = 0.0
    review_score: float = 0.0
    price_score: float = 0.0
    total_score: float = 0.0
    
    def to_dict(self) -> Dict[str, float]:
        """딕셔너리로 변환"""
        return {
            "SpecScore": round(self.spec_score, 1),
            "PreferenceScore": round(self.preference_score, 1),
            "LifestyleScore": round(self.lifestyle_score, 1),
            "ReviewScore": round(self.review_score, 1),
            "PriceScore": round(self.price_score, 1),
            "TotalScore": round(self.total_score, 1)
        }


class PlaybookScoring:
    """Playbook Scoring 클래스"""
    
    @staticmethod
    def parse_spec_json(spec_json: str) -> Dict[str, str]:
        """스펙 JSON 파싱"""
        specs = {}
        if isinstance(spec_json, dict):
            return spec_json
        try:
            specs = json.loads(spec_json)
        except:
            lines = spec_json.split('\n')
            for line in lines:
                if ':' in line:
                    key, value = line.split(':', 1)
                    specs[key.strip()] = value.strip().strip('"\'')
        return specs
    
    @staticmethod
    def calculate_spec_score(spec: Dict[str, str], household_size: int) -> float:
        """스펙 점수 계산"""
        score = 0.0
        capacity_str = spec.get('용량', '') or spec.get('총 용량', '') or spec.get('세탁 용량', '')
        
        if capacity_str:
            capacity_match = re.findall(r'\d+', str(capacity_str))
            if capacity_match:
                try:
                    cap = float(capacity_match[0])
                    
                    if household_size == 1 and 300 <= cap <= 500:
                        score += 10
                    elif household_size == 4 and 750 <= cap <= 850:
                        score += 10
                except ValueError:
                    pass
        
        return score
    
    @staticmethod
    def calculate_price_score(price: float, budget: float) -> float:
        """가격 점수 계산"""
        if price <= budget:
            return 10.0
        elif price <= budget * 1.1:
            return -5.0
        return -15.0


