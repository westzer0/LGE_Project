"""
스타일 분석 메시지 로더
엑셀 파일에서 스타일 분석 메시지를 로드하고 온보딩 데이터와 매칭
"""
import pandas as pd
import json
import re
from typing import Dict, List, Optional
import os

class StyleMessageLoader:
    """스타일 분석 메시지 로더"""
    
    def __init__(self, excel_path: str = 'data/스타일분석 메세지.xls'):
        self.excel_path = excel_path
        self.messages = []
        self.load_messages()
    
    def load_messages(self):
        """엑셀 파일에서 메시지 로드"""
        try:
            df = pd.read_excel(self.excel_path)
            print(f"[StyleMessageLoader] 엑셀 파일 로드 완료: {len(df)}개 행")
            
            # 컬럼명 정리 (실제 엑셀 파일의 컬럼명 사용)
            q1_col = '질문 1 ) 새로운 가전이 놓일 공간, 어떤 무드를 꿈꾸시나요? (가장 마음에 드는 인테리어 스타일을 하나 선택해주세요.)'
            q2_col = '질문 2 ) 이 공간에서 함께 생활하는 메이트는 누구인가요?'
            q2_1_col = '질문 2-1) 혹시 사랑스러운 반려동물(댕냥이)과 함께하시나요?'
            q3_col = "질문 3) 가전을 설치할 곳의 '주거 형태'는 무엇인가요?"
            q3_1_col = "질문 3-1) (원룸 제외) 가전을 배치할 '주요 공간'은 어디인가요?"
            q3_2_col = '질문 3-2) 해당 공간의 크기는 대략 어느 정도인가요? ( 정확한 수치 입력: ____ 평 / ____ ㎡  )\n* 전체 선택 시 전체 공간 크기 입력'
            q4_col = '질문 4 ) 가전 선택 시, 나에게 절대 포기할 수 없는 한 가지는? (추천 결과의 1 순위를 결정하는 중요한 질문이에요.)'
            q5_budget_col = '질문 5) 생각하고 계신 전체 가전 구매 예산 범위는 어느 정도인가요? [가전 구매 예산 범위 (전체 금액)]'
            q5_line_col = '질문 5) 생각하고 계신 전체 가전 구매 예산 범위는 어느 정도인가요? [선호하는 제품 라인업]'
            result_col = '스타일 분석 결과'
            
            for idx, row in df.iterrows():
                try:
                    # 스타일 분석 결과 파싱
                    result_text = str(row[result_col]) if pd.notna(row[result_col]) else ''
                    
                    # JSON 형식이 아닌 경우 정규식으로 파싱
                    style_match = re.search(r'"style":\s*"([^"]+)"', result_text)
                    # message는 따옴표 안의 긴 텍스트이므로 더 유연하게 파싱
                    message_match = re.search(r'"message":\s*"([^"]+(?:"[^"]*")*[^"]*)"', result_text)
                    if not message_match:
                        # 더 간단한 패턴 시도
                        message_match = re.search(r'"message":\s*"(.+?)"', result_text, re.DOTALL)
                    
                    if style_match and message_match:
                        style = style_match.group(1).strip()
                        message = message_match.group(1).strip()
                        
                        # 온보딩 데이터 추출
                        onboarding_data = {
                            'q1_vibe': str(row[q1_col]) if pd.notna(row[q1_col]) else None,
                            'q2_mate': str(row[q2_col]) if pd.notna(row[q2_col]) else None,
                            'q2_1_pet': str(row[q2_1_col]) if pd.notna(row[q2_1_col]) else None,
                            'q3_housing': str(row[q3_col]) if pd.notna(row[q3_col]) else None,
                            'q3_1_space': str(row[q3_1_col]) if pd.notna(row[q3_1_col]) else None,
                            'q3_2_size': str(row[q3_2_col]) if pd.notna(row[q3_2_col]) else None,
                            'q4_priority': str(row[q4_col]) if pd.notna(row[q4_col]) else None,
                            'q5_budget': str(row[q5_budget_col]) if pd.notna(row[q5_budget_col]) else None,
                            'q5_line': str(row[q5_line_col]) if pd.notna(row[q5_line_col]) else None,
                        }
                        
                        self.messages.append({
                            'style': style,
                            'message': message,
                            'onboarding_data': onboarding_data
                        })
                except Exception as e:
                    print(f"[StyleMessageLoader] 행 {idx} 파싱 오류: {e}")
                    continue
            
            print(f"[StyleMessageLoader] 메시지 로드 완료: {len(self.messages)}개")
            
        except Exception as e:
            print(f"[StyleMessageLoader] 엑셀 파일 로드 실패: {e}")
            self.messages = []
    
    def normalize_vibe(self, vibe: str) -> str:
        """vibe 값을 정규화"""
        if not vibe:
            return 'modern'
        
        vibe_lower = vibe.lower()
        if '모던' in vibe or '미니멀' in vibe or 'modern' in vibe_lower or 'minimal' in vibe_lower:
            return 'modern'
        elif '코지' in vibe or '네이처' in vibe or 'cozy' in vibe_lower or 'nature' in vibe_lower:
            return 'cozy'
        elif '유니크' in vibe or '팝' in vibe or 'unique' in vibe_lower or 'pop' in vibe_lower:
            return 'pop'
        elif '럭셔리' in vibe or '아티스틱' in vibe or 'luxury' in vibe_lower or 'artistic' in vibe_lower:
            return 'luxury'
        return 'modern'
    
    def normalize_household_size(self, mate: str) -> int:
        """가족 구성원 수 정규화"""
        if not mate:
            return 2
        
        mate_lower = mate.lower()
        if '1인' in mate or '혼자' in mate or 'single' in mate_lower:
            return 1
        elif '2인' in mate or '둘' in mate or '커플' in mate or 'couple' in mate_lower:
            return 2
        elif '3인' in mate or '셋' in mate or '3' in mate:
            return 3
        elif '4인' in mate or '넷' in mate or '4' in mate or '패밀리' in mate or 'family' in mate_lower:
            return 4
        elif '5인' in mate or '다섯' in mate or '5' in mate:
            return 5
        return 2
    
    def normalize_housing_type(self, housing: str) -> str:
        """주거 형태 정규화"""
        if not housing:
            return 'apartment'
        
        housing_lower = housing.lower()
        if '원룸' in housing or 'oneroom' in housing_lower:
            return 'oneroom'
        elif '오피스텔' in housing or 'officetel' in housing_lower:
            return 'officetel'
        elif '아파트' in housing or 'apartment' in housing_lower:
            return 'apartment'
        elif '빌라' in housing or 'villa' in housing_lower:
            return 'villa'
        elif '단독주택' in housing or 'house' in housing_lower:
            return 'house'
        return 'apartment'
    
    def extract_pyung(self, size_text: str) -> int:
        """평수 추출"""
        if not size_text:
            return 25
        
        # 숫자 추출
        numbers = re.findall(r'\d+', str(size_text))
        if numbers:
            pyung = int(numbers[0])
            # ㎡로 입력된 경우 평수로 변환 (1평 = 3.3㎡)
            if '㎡' in size_text or 'm2' in size_text.lower():
                pyung = int(pyung / 3.3)
            return pyung
        return 25
    
    def normalize_priority(self, priority: str) -> str:
        """우선순위 정규화"""
        if not priority:
            return 'value'
        
        priority_lower = priority.lower()
        if '디자인' in priority or 'design' in priority_lower:
            return 'design'
        elif 'ai' in priority_lower or '스마트' in priority:
            return 'tech'
        elif '에너지' in priority or 'energy' in priority_lower:
            return 'energy'
        elif '가성비' in priority or 'value' in priority_lower or '예산' in priority:
            return 'value'
        return 'value'
    
    def normalize_budget(self, budget: str) -> str:
        """예산 정규화"""
        if not budget:
            return 'medium'
        
        budget_lower = budget.lower()
        if '500만' in budget or '500' in budget:
            return 'low'
        elif '1000만' in budget or '1000' in budget or '1000만원 이하' in budget:
            return 'low'
        elif '2000만' in budget or '2000' in budget:
            return 'medium'
        elif '3000만' in budget or '3000' in budget:
            return 'medium'
        elif '5000만' in budget or '5000' in budget:
            return 'high'
        elif '1억' in budget or '10000' in budget:
            return 'high'
        return 'medium'
    
    def match_message(self, onboarding_data: dict) -> Optional[Dict]:
        """
        온보딩 데이터와 가장 유사한 메시지 찾기
        
        Args:
            onboarding_data: 온보딩 데이터
            
        Returns:
            {'style': str, 'message': str} 또는 None
        """
        if not self.messages:
            return None
        
        # 온보딩 데이터 정규화
        vibe = self.normalize_vibe(onboarding_data.get('vibe'))
        household_size = onboarding_data.get('household_size', 2)
        housing_type = self.normalize_housing_type(onboarding_data.get('housing_type'))
        pyung = onboarding_data.get('pyung', 25)
        priority = self.normalize_priority(onboarding_data.get('priority'))
        budget = self.normalize_budget(onboarding_data.get('budget_level'))
        
        # 매칭 점수 계산
        best_match = None
        best_score = 0
        
        for msg in self.messages:
            score = 0
            msg_data = msg['onboarding_data']
            
            # vibe 매칭 (가장 중요)
            msg_vibe = self.normalize_vibe(msg_data.get('q1_vibe', ''))
            if msg_vibe == vibe:
                score += 10
            
            # 가족 구성원 수 매칭
            msg_household = self.normalize_household_size(msg_data.get('q2_mate', ''))
            if msg_household == household_size:
                score += 5
            elif abs(msg_household - household_size) <= 1:
                score += 2
            
            # 주거 형태 매칭
            msg_housing = self.normalize_housing_type(msg_data.get('q3_housing', ''))
            if msg_housing == housing_type:
                score += 3
            
            # 우선순위 매칭
            msg_priority = self.normalize_priority(msg_data.get('q4_priority', ''))
            if msg_priority == priority:
                score += 3
            
            # 예산 매칭
            msg_budget = self.normalize_budget(msg_data.get('q5_budget', ''))
            if msg_budget == budget:
                score += 2
            
            if score > best_score:
                best_score = score
                best_match = msg
        
        if best_match:
            return {
                'style': best_match['style'],
                'message': best_match['message'],
                'match_score': best_score
            }
        
        # 매칭 실패 시 vibe만으로 찾기
        for msg in self.messages:
            msg_vibe = self.normalize_vibe(msg['onboarding_data'].get('q1_vibe', ''))
            if msg_vibe == vibe:
                return {
                    'style': msg['style'],
                    'message': msg['message'],
                    'match_score': 5
                }
        
        return None


# 전역 인스턴스
_style_message_loader = None

def get_style_message_loader() -> StyleMessageLoader:
    """스타일 메시지 로더 싱글톤"""
    global _style_message_loader
    if _style_message_loader is None:
        _style_message_loader = StyleMessageLoader()
    return _style_message_loader


if __name__ == '__main__':
    # 테스트
    loader = StyleMessageLoader()
    
    # 테스트 온보딩 데이터
    test_data = {
        'vibe': 'modern',
        'household_size': 2,
        'housing_type': 'apartment',
        'pyung': 30,
        'priority': 'design',
        'budget_level': 'medium'
    }
    
    result = loader.match_message(test_data)
    print(f"\n테스트 결과:")
    print(f"스타일: {result['style'] if result else 'None'}")
    print(f"메시지: {result['message'][:100] if result else 'None'}...")
    print(f"매칭 점수: {result['match_score'] if result else 0}")

