#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
PRD 기반 전체 플로우 시뮬레이션

PRD 요구사항:
1. 온보딩 6단계 (Vibe, Household, Space, Lifestyle, Priority, Budget)
2. 가전 추천 포트폴리오 생성
3. 추천 결과 분석 및 리포트
4. Oracle DB에 데이터 저장

실행:
    python simulate_prd_flow.py
"""

import os
import sys
import csv
import json
import uuid
import re
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional

# Django 설정
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

import django
django.setup()

from api.db.oracle_client import get_connection, fetch_all_dict
from api.services.onboarding_db_service import onboarding_db_service
from api.services.recommendation_engine import recommendation_engine
from api.utils.taste_classifier import taste_classifier


class PRDSimulator:
    """PRD 기반 시뮬레이터"""
    
    def __init__(self):
        self.results = {
            'total_sessions': 0,
            'onboarding_completed': 0,
            'recommendation_success': 0,
            'recommendation_failed': 0,
            'total_recommendations': 0,
            'category_distribution': {},
            'budget_distribution': {},
            'household_distribution': {},
            'errors': []
        }
    
    def parse_vibe(self, vibe_text: str) -> str:
        """Step 1: Vibe 파싱"""
        if not vibe_text:
            return 'modern'
        
        vibe_lower = vibe_text.lower()
        if '모던' in vibe_text or 'modern' in vibe_lower or '미니멀' in vibe_text:
            return 'modern'
        elif '코지' in vibe_text or 'cozy' in vibe_lower or '네이처' in vibe_text:
            return 'cozy'
        elif '유니크' in vibe_text or 'unique' in vibe_lower or '팝' in vibe_text:
            return 'pop'
        elif '럭셔리' in vibe_text or 'luxury' in vibe_lower or '아티스틱' in vibe_text:
            return 'luxury'
        return 'modern'
    
    def parse_household(self, mate_text: str) -> int:
        """Step 2: Household Size 파싱"""
        if not mate_text:
            return 2
        
        if '혼자' in mate_text or '1인' in mate_text:
            return 1
        elif '둘이' in mate_text or '2인' in mate_text or '신혼' in mate_text:
            return 2
        elif '3~4인' in mate_text or '3-4인' in mate_text or '아이' in mate_text:
            return 3  # 3-4인 가족
        elif '5인' in mate_text or '대가족' in mate_text:
            return 5
        return 2
    
    def parse_has_pet(self, pet_text: str) -> bool:
        """Step 2-1: Pet 여부"""
        if not pet_text:
            return False
        return '네' in pet_text or '있어요' in pet_text or '함께합니다' in pet_text
    
    def parse_housing_type(self, housing_text: str) -> str:
        """Step 3-1: Housing Type"""
        if not housing_text:
            return 'apartment'
        
        if '아파트' in housing_text:
            return 'apartment'
        elif '주택' in housing_text:
            return 'detached'
        elif '오피스텔' in housing_text:
            return 'officetel'
        elif '원룸' in housing_text or '투룸' in housing_text:
            return 'studio'
        return 'apartment'
    
    def parse_main_space(self, space_text: str) -> List[str]:
        """Step 3-2: Main Space (다중 선택)"""
        if not space_text or space_text.strip() == '':
            return ['living']
        
        spaces = []
        if '거실' in space_text:
            spaces.append('living')
        if '주방' in space_text:
            spaces.append('kitchen')
        if '드레스룸' in space_text:
            spaces.append('dressing')
        if '방' in space_text or '침실' in space_text:
            spaces.append('bedroom')
        if '서재' in space_text:
            spaces.append('study')
        if '전체' in space_text:
            return ['living', 'kitchen', 'bedroom']
        
        return spaces if spaces else ['living']
    
    def parse_pyung(self, pyung_text: str) -> int:
        """Step 3-3: 공간 크기"""
        if not pyung_text or '모르' in pyung_text:
            return 25
        
        numbers = re.findall(r'\d+', pyung_text)
        if numbers:
            return int(numbers[0])
        return 25
    
    def parse_lifestyle(self, row: Dict) -> Dict:
        """Step 4: Lifestyle Info (요리/세탁/미디어)"""
        # CSV에 직접 없으면 기본값 사용
        cooking = 'sometimes'
        laundry = 'weekly'
        media = 'balanced'
        
        # 필요시 CSV 컬럼에서 파싱
        for key, value in row.items():
            if '요리' in key:
                if '거의' in str(value) or '안' in str(value):
                    cooking = 'rarely'
                elif '가끔' in str(value):
                    cooking = 'sometimes'
                elif '자주' in str(value):
                    cooking = 'often'
            elif '세탁' in key:
                if '주 1회' in str(value) or '몰아서' in str(value):
                    laundry = 'weekly'
                elif '2~3회' in str(value) or '2-3회' in str(value):
                    laundry = 'few_times'
                elif '매일' in str(value):
                    laundry = 'daily'
            elif '미디어' in key or 'TV' in key or '영상' in key:
                if '넷플릭스' in str(value) or '영화' in str(value) or 'OTT' in str(value):
                    media = 'ott'
                elif '게임' in str(value):
                    media = 'gaming'
                elif '뉴스' in str(value) or '예능' in str(value):
                    media = 'tv'
                elif '아니' in str(value) or '없' in str(value):
                    media = 'none'
        
        return {
            'cooking': cooking,
            'laundry': laundry,
            'media': media
        }
    
    def parse_priority(self, priority_text: str) -> str:
        """Step 5: Priority"""
        if not priority_text:
            return 'value'
        
        if 'AI' in priority_text or '스마트' in priority_text or '기술' in priority_text:
            return 'tech'
        elif '디자인' in priority_text:
            return 'design'
        elif '에너지' in priority_text or '효율' in priority_text:
            return 'eco'
        elif '가성비' in priority_text or '성능' in priority_text:
            return 'value'
        return 'value'
    
    def parse_budget_level(self, budget_text: str) -> str:
        """Step 6: Budget Level"""
        if not budget_text:
            return 'medium'
        
        if '500만원 미만' in budget_text or '실속형' in budget_text:
            return 'low'
        elif '500만원 ~ 1,500만원' in budget_text or '표준형' in budget_text:
            return 'medium'
        elif '1,500만원 ~ 3,000만원' in budget_text or '고급형' in budget_text:
            return 'medium'  # medium-high
        elif '3,000만원 이상' in budget_text or '하이엔드' in budget_text:
            return 'high'
        return 'medium'
    
    def parse_budget_amount(self, budget_text: str) -> int:
        """예산 금액 파싱"""
        if '500만원 미만' in budget_text:
            return 500000
        elif '500만원 ~ 1,500만원' in budget_text:
            return 1000000
        elif '1,500만원 ~ 3,000만원' in budget_text:
            return 2000000
        elif '3,000만원 이상' in budget_text:
            return 5000000
        return 2000000
    
    def csv_to_session_data(self, row: Dict) -> Optional[Dict]:
        """CSV 행을 PRD 기반 세션 데이터로 변환"""
        try:
            # 컬럼명 찾기
            columns = list(row.keys())
            
            vibe_col = None
            mate_col = None
            pet_col = None
            housing_col = None
            space_col = None
            pyung_col = None
            priority_col = None
            budget_col = None
            
            for col in columns:
                if '무드' in col or '인테리어' in col or ('질문 1' in col):
                    vibe_col = col
                elif ('메이트' in col or '질문 2' in col) and '반려동물' not in col:
                    mate_col = col
                elif '반려동물' in col or '질문 2-1' in col:
                    pet_col = col
                elif '주거 형태' in col or ('질문 3' in col and '주거' in col):
                    housing_col = col
                elif '주요 공간' in col or '질문 3-1' in col:
                    space_col = col
                elif '크기' in col or '평' in col or '질문 3-2' in col:
                    pyung_col = col
                elif '포기' in col or '질문 4' in col:
                    priority_col = col
                elif '예산' in col and '라인업' not in col and '선호' not in col:
                    budget_col = col
            
            # 데이터 추출
            vibe = self.parse_vibe(row.get(vibe_col, ''))
            household_size = self.parse_household(row.get(mate_col, ''))
            has_pet = self.parse_has_pet(row.get(pet_col, ''))
            housing_type = self.parse_housing_type(row.get(housing_col, ''))
            main_space = self.parse_main_space(row.get(space_col, ''))
            pyung = self.parse_pyung(row.get(pyung_col, ''))
            priority = self.parse_priority(row.get(priority_col, ''))
            budget_level = self.parse_budget_level(row.get(budget_col, ''))
            budget_amount = self.parse_budget_amount(row.get(budget_col, ''))
            
            # Lifestyle 정보
            lifestyle = self.parse_lifestyle(row)
            
            # onboarding_data 구성 (taste 계산용)
            onboarding_data = {
                'vibe': vibe,
                'household_size': household_size,
                'housing_type': housing_type,
                'pyung': pyung,
                'main_space': main_space,
                'priority': priority,
                'budget_level': budget_level,
                'has_pet': has_pet,
                **lifestyle
            }
            
            return {
                'vibe': vibe,
                'household_size': household_size,
                'has_pet': has_pet,
                'housing_type': housing_type,
                'pyung': pyung,
                'main_space': main_space,
                'priority': priority,
                'budget_level': budget_level,
                'budget_amount': budget_amount,
                'onboarding_data': onboarding_data
            }
        except Exception as e:
            self.results['errors'].append(f"파싱 오류: {str(e)}")
            return None
    
    def create_user_profile(self, session_data: Dict) -> Dict:
        """User Profile 생성 (추천 엔진용)"""
        return {
            'vibe': session_data['vibe'],
            'household_size': session_data['household_size'],
            'housing_type': session_data['housing_type'],
            'pyung': session_data['pyung'],
            'priority': session_data['priority'],
            'budget_level': session_data['budget_level'],
            'budget_amount': session_data.get('budget_amount', 0),
            'categories': ['TV', 'KITCHEN', 'LIVING'],  # 기본 카테고리
            'has_pet': session_data['has_pet'],
            'main_space': session_data['main_space'][0] if session_data['main_space'] else 'living',
            'space_size': 'medium',
            'onboarding_data': session_data['onboarding_data']
        }
    
    def run_simulation(self, csv_file: Path, limit: Optional[int] = None):
        """시뮬레이션 실행"""
        print("=" * 80)
        print("PRD 기반 가전 추천 포트폴리오 시뮬레이션")
        print("=" * 80)
        print()
        
        # 1. CSV 파일 읽기
        print("[1/4] CSV 파일 읽기 중...")
        if not csv_file.exists():
            print(f"[ERROR] CSV 파일을 찾을 수 없습니다: {csv_file}")
            return
        
        sessions_data = []
        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for idx, row in enumerate(reader, 1):
                if limit and idx > limit:
                    break
                
                session_data = self.csv_to_session_data(row)
                if session_data:
                    sessions_data.append(session_data)
                
                if idx % 100 == 0:
                    print(f"  [{idx}행] 파싱 중... (성공: {len(sessions_data)}개)")
        
        self.results['total_sessions'] = len(sessions_data)
        print(f"[OK] 총 {len(sessions_data)}개 세션 데이터 파싱 완료")
        print()
        
        # 2. Oracle DB 연결 확인
        print("[2/4] Oracle DB 연결 확인 중...")
        try:
            with get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT 1 FROM DUAL")
            print("  [OK] Oracle DB 연결 성공")
        except Exception as e:
            print(f"  [ERROR] Oracle DB 연결 실패: {str(e)}")
            return
        print()
        
        # 3. 데이터 삽입 및 추천 시뮬레이션
        print("[3/4] 데이터 삽입 및 추천 시뮬레이션 중...")
        
        for idx, session_data in enumerate(sessions_data, 1):
            try:
                # 세션 ID 생성 (NUMBER 타입이므로 시퀀스 사용 또는 숫자로 생성)
                # 기존 데이터와 충돌 방지를 위해 큰 숫자 사용
                import time
                session_id = int(time.time() * 1000) + idx  # 타임스탬프 + 인덱스
                # MEMBER 테이블에 존재하는 MEMBER_ID 사용 (user_1 ~ user_1000 형식)
                user_id = f"user_{idx}"
                member_id = user_id  # MEMBER_ID와 동일하게 설정
                
                # 디버깅: 첫 번째 세션만 상세 로그
                if idx == 1:
                    print(f"  [DEBUG] 세션 1 데이터:")
                    print(f"    household_size: {session_data.get('household_size')} (type: {type(session_data.get('household_size'))})")
                    print(f"    pyung: {session_data.get('pyung')} (type: {type(session_data.get('pyung'))})")
                    print(f"    main_space: {session_data.get('main_space')} (type: {type(session_data.get('main_space'))})")
                
                # ONBOARDING_SESSION에 INSERT (onboarding_data는 제외하고 필요한 필드만 전달)
                session_data_for_db = {
                    'vibe': session_data.get('vibe'),
                    'household_size': session_data.get('household_size'),
                    'has_pet': session_data.get('has_pet'),
                    'housing_type': session_data.get('housing_type'),
                    'pyung': session_data.get('pyung'),
                    'main_space': session_data.get('main_space'),
                    'priority': session_data.get('priority'),
                    'budget_level': session_data.get('budget_level'),
                    'cooking': session_data.get('onboarding_data', {}).get('cooking'),
                    'laundry': session_data.get('onboarding_data', {}).get('laundry'),
                    'media': session_data.get('onboarding_data', {}).get('media'),
                }
                
                onboarding_db_service.create_or_update_session(
                    session_id=session_id,
                    user_id=user_id,
                    member_id=member_id,  # MEMBER_ID 명시적으로 전달
                    current_step=7,
                    status='COMPLETED',
                    **session_data_for_db
                )
                self.results['onboarding_completed'] += 1
                
                # User Profile 생성
                user_profile = self.create_user_profile(session_data)
                
                # Taste ID 계산
                taste_id = taste_classifier.calculate_taste_from_onboarding(
                    session_data['onboarding_data']
                )
                
                # 추천 엔진 실행
                rec_result = recommendation_engine.get_recommendations(
                    user_profile=user_profile,
                    taste_id=taste_id,
                    limit=5
                )
                
                if rec_result.get('success'):
                    self.results['recommendation_success'] += 1
                    count = rec_result.get('count', 0)
                    self.results['total_recommendations'] += count
                    
                    # 통계 수집
                    recommendations = rec_result.get('recommendations', [])
                    for rec in recommendations:
                        category = rec.get('category', 'UNKNOWN')
                        self.results['category_distribution'][category] = \
                            self.results['category_distribution'].get(category, 0) + 1
                    
                    # 예산 분포
                    budget = session_data['budget_level']
                    self.results['budget_distribution'][budget] = \
                        self.results['budget_distribution'].get(budget, 0) + 1
                    
                    # 가구 분포
                    household = session_data['household_size']
                    self.results['household_distribution'][household] = \
                        self.results['household_distribution'].get(household, 0) + 1
                else:
                    self.results['recommendation_failed'] += 1
                    self.results['errors'].append(
                        f"세션 {idx}: {rec_result.get('message', 'Unknown error')}"
                    )
                
                # 진행 상황 출력
                if idx % 10 == 0 or idx == len(sessions_data):
                    success_rate = (self.results['recommendation_success'] / idx) * 100
                    print(f"  [{idx}/{len(sessions_data)}] 진행 중... "
                          f"(완료: {self.results['onboarding_completed']}, "
                          f"추천 성공: {self.results['recommendation_success']}, "
                          f"성공률: {success_rate:.1f}%)")
            
            except Exception as e:
                self.results['recommendation_failed'] += 1
                self.results['errors'].append(f"세션 {idx} 처리 실패: {str(e)}")
                print(f"  [ERROR] 세션 {idx} 처리 실패: {str(e)}")
        
        print()
        
        # 4. 결과 리포트
        print("[4/4] 결과 리포트 생성 중...")
        self.print_report()
        
        # 리포트 파일 저장
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = BASE_DIR / f"prd_simulation_report_{timestamp}.json"
        
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, ensure_ascii=False, indent=2, default=str)
        
        print(f"\n상세 리포트 저장: {report_file}")
        print()
        print("=" * 80)
        print("시뮬레이션 완료!")
        print("=" * 80)
    
    def print_report(self):
        """결과 리포트 출력"""
        print("\n" + "=" * 80)
        print("PRD 시뮬레이션 결과 리포트")
        print("=" * 80)
        
        total = self.results['total_sessions']
        completed = self.results['onboarding_completed']
        rec_success = self.results['recommendation_success']
        rec_failed = self.results['recommendation_failed']
        
        print(f"\n[전체 통계]")
        print(f"  총 세션: {total}개")
        print(f"  온보딩 완료: {completed}개 ({completed/total*100:.1f}%)")
        print(f"  추천 성공: {rec_success}개 ({rec_success/total*100:.1f}%)")
        print(f"  추천 실패: {rec_failed}개 ({rec_failed/total*100:.1f}%)")
        print(f"  총 추천 제품 수: {self.results['total_recommendations']}개")
        
        if rec_success > 0:
            avg_recs = self.results['total_recommendations'] / rec_success
            print(f"  세션당 평균 추천 수: {avg_recs:.1f}개")
        
        print(f"\n[카테고리별 추천 분포]")
        for category, count in sorted(
            self.results['category_distribution'].items(),
            key=lambda x: x[1],
            reverse=True
        ):
            print(f"  {category}: {count}개")
        
        print(f"\n[예산별 분포]")
        for budget, count in sorted(
            self.results['budget_distribution'].items(),
            key=lambda x: x[1],
            reverse=True
        ):
            print(f"  {budget}: {count}개")
        
        print(f"\n[가구 구성별 분포]")
        for household, count in sorted(
            self.results['household_distribution'].items()
        ):
            print(f"  {household}인 가구: {count}개")
        
        if self.results['errors']:
            print(f"\n[WARNING] 오류 ({len(self.results['errors'])}개)")
            for error in self.results['errors'][:10]:  # 처음 10개만
                print(f"  - {error}")
            if len(self.results['errors']) > 10:
                print(f"  ... 외 {len(self.results['errors']) - 10}개 오류")


def main():
    """메인 함수"""
    csv_file = BASE_DIR / 'data' / '온보딩' / 'onboarding_survey_aug_1000.csv'
    
    simulator = PRDSimulator()
    
    # 전체 또는 일부만 실행 (테스트용)
    # limit = 100  # 처음 100개만 테스트
    limit = None  # 전체 실행
    
    simulator.run_simulation(csv_file, limit=limit)


if __name__ == '__main__':
    main()

