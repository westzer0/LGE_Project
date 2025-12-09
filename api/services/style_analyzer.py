"""
스타일 분석 메시지 분석기
엑셀 파일에서 스타일 분석 메시지를 로드하고 온보딩 데이터와 매칭
"""
import pandas as pd
import json
import re
from typing import Dict, Optional, List
import os


class StyleAnalyzer:
    """스타일 분석 메시지 분석기"""
    
    def __init__(self, excel_path: str = 'data/스타일분석 메세지.xls'):
        """
        스타일 분석기 초기화
        
        Args:
            excel_path: 엑셀 파일 경로
        """
        self.excel_path = excel_path
        self.messages = []
        self.df = None
        self.load_messages()
    
    def load_messages(self):
        """엑셀 파일에서 메시지 로드"""
        try:
            # 엑셀 파일 읽기
            self.df = pd.read_excel(self.excel_path)
            print(f"[StyleAnalyzer] 엑셀 파일 로드 완료: {len(self.df)}개 행")
            
            # 컬럼명을 간단한 이름으로 매핑
            column_mapping = {
                '질문 1 ) 새로운 가전이 놓일 공간, 어떤 무드를 꿈꾸시나요? (가장 마음에 드는 인테리어 스타일을 하나 선택해주세요.)': 'q1_vibe',
                '질문 2 ) 이 공간에서 함께 생활하는 메이트는 누구인가요?': 'q2_mate',
                '질문 2-1) 혹시 사랑스러운 반려동물(댕냥이)과 함께하시나요?': 'q2_1_pet',
                "질문 3) 가전을 설치할 곳의 '주거 형태'는 무엇인가요?": 'q3_housing',
                "질문 3-1) (원룸 제외) 가전을 배치할 '주요 공간'은 어디인가요?": 'q3_1_space',
                '질문 3-2) 해당 공간의 크기는 대략 어느 정도인가요? ( 정확한 수치 입력: ____ 평 / ____ ㎡  )\n* 전체 선택 시 전체 공간 크기 입력': 'q3_2_size',
                '질문 4 ) 가전 선택 시, 나에게 절대 포기할 수 없는 한 가지는? (추천 결과의 1 순위를 결정하는 중요한 질문이에요.)': 'q4_priority',
                '질문 5) 생각하고 계신 전체 가전 구매 예산 범위는 어느 정도인가요? [가전 구매 예산 범위 (전체 금액)]': 'q5_budget',
                '질문 5) 생각하고 계신 전체 가전 구매 예산 범위는 어느 정도인가요? [선호하는 제품 라인업]': 'q5_line',
                '스타일 분석 결과': 'style_result'
            }
            
            # 컬럼명 변경
            self.df = self.df.rename(columns=column_mapping)
            
            # 메시지 파싱 및 저장
            for idx, row in self.df.iterrows():
                try:
                    # 스타일 분석 결과 파싱
                    style_result = self._parse_style_result(row.get('style_result', ''))
                    
                    if style_result:
                        # 온보딩 데이터 추출
                        onboarding_data = {
                            'q1_vibe': str(row.get('q1_vibe', '')) if pd.notna(row.get('q1_vibe')) else '',
                            'q2_mate': str(row.get('q2_mate', '')) if pd.notna(row.get('q2_mate')) else '',
                            'q2_1_pet': str(row.get('q2_1_pet', '')) if pd.notna(row.get('q2_1_pet')) else '',
                            'q3_housing': str(row.get('q3_housing', '')) if pd.notna(row.get('q3_housing')) else '',
                            'q3_1_space': str(row.get('q3_1_space', '')) if pd.notna(row.get('q3_1_space')) else '',
                            'q3_2_size': str(row.get('q3_2_size', '')) if pd.notna(row.get('q3_2_size')) else '',
                            'q4_priority': str(row.get('q4_priority', '')) if pd.notna(row.get('q4_priority')) else '',
                            'q5_budget': str(row.get('q5_budget', '')) if pd.notna(row.get('q5_budget')) else '',
                            'q5_line': str(row.get('q5_line', '')) if pd.notna(row.get('q5_line')) else '',
                        }
                        
                        self.messages.append({
                            'style': style_result.get('style', ''),
                            'message': style_result.get('message', ''),
                            'onboarding_data': onboarding_data
                        })
                except Exception as e:
                    # 개별 행 파싱 오류는 무시하고 계속 진행
                    continue
            
            print(f"[StyleAnalyzer] 메시지 로드 완료: {len(self.messages)}개")
            
        except Exception as e:
            print(f"[StyleAnalyzer] 엑셀 파일 로드 실패: {e}")
            self.messages = []
    
    def _parse_style_result(self, raw_text: str) -> Optional[Dict[str, str]]:
        """
        스타일 분석 결과 문자열 파싱
        
        Args:
            raw_text: 원본 텍스트 (예: "style": "모던 & 미니멀", "message": "...")
            
        Returns:
            {'style': str, 'message': str} 또는 None
        """
        if not raw_text or pd.isna(raw_text):
            return None
        
        raw_text = str(raw_text).strip()
        
        # 방법 1: JSON 파싱 시도
        try:
            # 중괄호가 없으면 추가
            if not raw_text.startswith('{'):
                raw_text = '{' + raw_text
            if not raw_text.endswith('}'):
                raw_text = raw_text + '}'
            
            # JSON 파싱
            data = json.loads(raw_text)
            if 'style' in data and 'message' in data:
                return {
                    'style': str(data['style']).strip(),
                    'message': str(data['message']).strip()
                }
        except (json.JSONDecodeError, ValueError):
            # JSON 파싱 실패 시 정규표현식 사용
            pass
        
        # 방법 2: 정규표현식으로 파싱
        try:
            # style 추출
            style_match = re.search(r'"style":\s*"([^"]+)"', raw_text)
            # message 추출 (긴 텍스트이므로 DOTALL 모드 사용)
            message_match = re.search(r'"message":\s*"(.+?)"', raw_text, re.DOTALL)
            
            if style_match and message_match:
                return {
                    'style': style_match.group(1).strip(),
                    'message': message_match.group(1).strip()
                }
        except Exception:
            pass
        
        return None
    
    def get_result_message(self, user_answers: Dict[str, str]) -> Optional[str]:
        """
        사용자 온보딩 답변에 맞는 스타일 분석 메시지 반환
        
        Args:
            user_answers: 사용자 답변 딕셔너리
                예: {
                    'q1_vibe': '모던 & 미니멀 (Modern & Minimal): 화이트/블랙 톤의 깔끔한 공간을 선호',
                    'q2_mate': '2인 (커플/부부)',
                    'q3_housing': '아파트',
                    'q4_priority': '디자인',
                    ...
                }
        
        Returns:
            스타일 분석 메시지 문자열 또는 None
        """
        if not self.messages:
            return None
        
        best_match = None
        best_score = 0
        
        # 각 메시지와 비교하여 가장 많이 일치하는 것 찾기
        for msg in self.messages:
            score = 0
            msg_data = msg['onboarding_data']
            
            # 각 질문별로 일치 여부 확인
            for key in user_answers:
                if key in msg_data:
                    user_value = str(user_answers[key]).strip().lower()
                    msg_value = str(msg_data[key]).strip().lower()
                    
                    # 완전 일치
                    if user_value == msg_value:
                        score += 10
                    # 부분 일치 (포함 관계)
                    elif user_value and msg_value:
                        if user_value in msg_value or msg_value in user_value:
                            score += 5
                        # 키워드 매칭
                        elif self._keyword_match(user_value, msg_value):
                            score += 3
            
            if score > best_score:
                best_score = score
                best_match = msg
        
        # 매칭된 메시지 반환
        if best_match and best_score > 0:
            return best_match['message']
        
        # 매칭 실패 시 vibe만으로 찾기
        if 'q1_vibe' in user_answers:
            vibe = str(user_answers['q1_vibe']).lower()
            for msg in self.messages:
                msg_vibe = str(msg['onboarding_data'].get('q1_vibe', '')).lower()
                if vibe in msg_vibe or msg_vibe in vibe:
                    return msg['message']
        
        return None
    
    def _keyword_match(self, text1: str, text2: str) -> bool:
        """키워드 매칭 (주요 단어가 일치하는지 확인)"""
        # 주요 키워드 추출
        keywords1 = set(re.findall(r'\w+', text1))
        keywords2 = set(re.findall(r'\w+', text2))
        
        # 공통 키워드가 있으면 매칭
        common = keywords1 & keywords2
        return len(common) > 0
    
    def get_style_info(self, user_answers: Dict[str, str]) -> Optional[Dict[str, str]]:
        """
        사용자 온보딩 답변에 맞는 스타일 정보 반환 (style과 message 모두)
        
        Args:
            user_answers: 사용자 답변 딕셔너리
        
        Returns:
            {'style': str, 'message': str} 또는 None
        """
        if not self.messages:
            return None
        
        best_match = None
        best_score = 0
        
        for msg in self.messages:
            score = 0
            msg_data = msg['onboarding_data']
            
            for key in user_answers:
                if key in msg_data:
                    user_value = str(user_answers[key]).strip().lower()
                    msg_value = str(msg_data[key]).strip().lower()
                    
                    if user_value == msg_value:
                        score += 10
                    elif user_value and msg_value:
                        if user_value in msg_value or msg_value in user_value:
                            score += 5
                        elif self._keyword_match(user_value, msg_value):
                            score += 3
            
            if score > best_score:
                best_score = score
                best_match = msg
        
        if best_match and best_score > 0:
            return {
                'style': best_match['style'],
                'message': best_match['message']
            }
        
        # vibe만으로 찾기
        if 'q1_vibe' in user_answers:
            vibe = str(user_answers['q1_vibe']).lower()
            for msg in self.messages:
                msg_vibe = str(msg['onboarding_data'].get('q1_vibe', '')).lower()
                if vibe in msg_vibe or msg_vibe in vibe:
                    return {
                        'style': msg['style'],
                        'message': msg['message']
                    }
        
        return None


# 전역 인스턴스
_style_analyzer = None

def get_style_analyzer() -> StyleAnalyzer:
    """스타일 분석기 싱글톤"""
    global _style_analyzer
    if _style_analyzer is None:
        _style_analyzer = StyleAnalyzer()
    return _style_analyzer


if __name__ == "__main__":
    # 테스트 코드
    print("=" * 60)
    print("StyleAnalyzer 테스트")
    print("=" * 60)
    
    # 스타일 분석기 초기화
    analyzer = StyleAnalyzer()
    
    # 테스트용 사용자 답변
    test_answers = {
        'q1_vibe': '모던 & 미니멀 (Modern & Minimal): 화이트/블랙 톤의 깔끔한 공간을 선호',
        'q2_mate': '2인 (커플/부부)',
        'q3_housing': '아파트',
        'q4_priority': '디자인',
        'q5_budget': '2000만원 ~ 3000만원'
    }
    
    print("\n[테스트 1] 사용자 답변:")
    for key, value in test_answers.items():
        print(f"  {key}: {value}")
    
    # 메시지 가져오기
    message = analyzer.get_result_message(test_answers)
    print("\n[테스트 1] 결과 메시지:")
    if message:
        print(f"  {message[:200]}...")
    else:
        print("  메시지를 찾을 수 없습니다.")
    
    # 스타일 정보 가져오기
    style_info = analyzer.get_style_info(test_answers)
    print("\n[테스트 2] 스타일 정보:")
    if style_info:
        print(f"  Style: {style_info['style']}")
        print(f"  Message: {style_info['message'][:200]}...")
    else:
        print("  스타일 정보를 찾을 수 없습니다.")
    
    # 다른 테스트 케이스
    print("\n" + "=" * 60)
    test_answers2 = {
        'q1_vibe': '코지 & 네이처 (Cozy & Nature): 우드 톤 가구, 베이지색 벽지 등 따뜻하고 자연적인 공간을 선호',
        'q2_mate': '3인 이상 (패밀리)',
        'q3_housing': '아파트',
        'q4_priority': '가성비'
    }
    
    print("\n[테스트 3] 다른 사용자 답변:")
    for key, value in test_answers2.items():
        print(f"  {key}: {value}")
    
    message2 = analyzer.get_result_message(test_answers2)
    print("\n[테스트 3] 결과 메시지:")
    if message2:
        print(f"  {message2[:200]}...")
    else:
        print("  메시지를 찾을 수 없습니다.")

