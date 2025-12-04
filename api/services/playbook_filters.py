"""
Playbook Hard Filter Service

Hard Filter 로직 구현
"""
from typing import Dict, List
import re


class PlaybookHardFilter:
    """Playbook Hard Filter 클래스"""
    
    @staticmethod
    def apply_filters(products: List[Dict], onboarding: Dict) -> List[str]:
        """
        Hard Filter 적용
        
        Args:
            products: 제품 리스트
            onboarding: 온보딩 데이터
            
        Returns:
            필터링된 제품 ID 리스트
        """
        filtered_ids = []
        
        for product in products:
            if PlaybookHardFilter._passes_filter(product, onboarding):
                product_id = product.get('id') or product.get('product_id')
                if product_id:
                    filtered_ids.append(str(product_id))
        
        return filtered_ids
    
    @staticmethod
    def _passes_filter(product: Dict, onboarding: Dict) -> bool:
        """
        제품이 필터를 통과하는지 확인
        
        Args:
            product: 제품 딕셔너리
            onboarding: 온보딩 데이터
            
        Returns:
            True면 통과, False면 제외
        """
        # 원룸 필터
        if onboarding.get('housing_type') == 'studio':
            spec_json = product.get('spec_json', {})
            if isinstance(spec_json, str):
                import json
                try:
                    spec_json = json.loads(spec_json)
                except:
                    spec_json = {}
            
            depth = spec_json.get('깊이(mm)', 0) or spec_json.get('깊이', 0)
            if isinstance(depth, str):
                depth_match = re.findall(r'\d+', str(depth))
                depth = float(depth_match[0]) if depth_match else 0
            else:
                depth = float(depth) if depth else 0
            
            if depth > 750:
                return False
        
        # 1인 세탁기 필터
        if onboarding.get('household_size') == 1:
            spec_json = product.get('spec_json', {})
            if isinstance(spec_json, str):
                import json
                try:
                    spec_json = json.loads(spec_json)
                except:
                    spec_json = {}
            
            capacity = spec_json.get('세탁 용량', 0) or spec_json.get('용량', 0)
            if isinstance(capacity, str):
                capacity_match = re.findall(r'\d+', str(capacity))
                capacity = float(capacity_match[0]) if capacity_match else 0
            else:
                capacity = float(capacity) if capacity else 0
            
            if capacity >= 24:
                return False
        
        return True

