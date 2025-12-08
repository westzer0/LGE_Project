#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
온보딩 CSV 데이터를 Oracle DB에 삽입하고 시뮬레이션 실행

사용법:
    python simulate_onboarding_data.py

기능:
1. onboarding_survey_aug_1000.csv 파일 읽기
2. 각 행을 ONBOARDING_SESSION 테이블에 INSERT
3. 각 세션에 대해 추천 엔진 실행
4. 결과 통계 출력
"""

import os
import sys
import csv
import json
import uuid
import re
from pathlib import Path
from datetime import datetime

# Django 설정 로드
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

import django
django.setup()

from api.db.oracle_client import get_connection
from api.services.onboarding_db_service import onboarding_db_service
from api.services.recommendation_engine import recommendation_engine
from api.utils.taste_classifier import taste_classifier


def parse_vibe(vibe_text):
    """Vibe 텍스트를 코드로 변환"""
    if '모던' in vibe_text or 'Modern' in vibe_text:
        return 'modern'
    elif '코지' in vibe_text or 'Cozy' in vibe_text:
        return 'cozy'
    elif '유니크' in vibe_text or 'Unique' in vibe_text or '팝' in vibe_text:
        return 'pop'
    elif '럭셔리' in vibe_text or 'Luxury' in vibe_text:
        return 'luxury'
    return 'modern'  # 기본값


def parse_household_size(mate_text):
    """가구 구성 텍스트를 숫자로 변환"""
    if '혼자' in mate_text or '1인' in mate_text:
        return 1
    elif '둘이' in mate_text or '2인' in mate_text or '신혼' in mate_text:
        return 2
    elif '3~4인' in mate_text or '3-4인' in mate_text:
        return 3  # 또는 4, 여기서는 3으로
    elif '5인' in mate_text or '대가족' in mate_text:
        return 5
    return 2  # 기본값


def parse_has_pet(pet_text):
    """반려동물 여부"""
    if '네' in pet_text or '있어요' in pet_text or '함께합니다' in pet_text:
        return True
    return False


def parse_housing_type(housing_text):
    """주거 형태"""
    if '아파트' in housing_text:
        return 'apartment'
    elif '주택' in housing_text:
        return 'detached'
    elif '오피스텔' in housing_text:
        return 'officetel'
    elif '원룸' in housing_text or '투룸' in housing_text:
        return 'studio'
    return 'apartment'  # 기본값


def parse_main_space(space_text):
    """주요 공간 파싱 (다중 선택 가능)"""
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
        spaces = ['living', 'kitchen', 'bedroom']
    
    return spaces if spaces else ['living']


def parse_pyung(pyung_text):
    """평수 파싱"""
    if not pyung_text or pyung_text.strip() == '' or '모르' in pyung_text:
        return 25  # 기본값
    
    # 숫자 추출
    numbers = re.findall(r'\d+', pyung_text)
    if numbers:
        return int(numbers[0])
    
    return 25  # 기본값


def parse_priority(priority_text):
    """우선순위 파싱"""
    if 'AI' in priority_text or '스마트' in priority_text or '기술' in priority_text:
        return 'tech'
    elif '디자인' in priority_text:
        return 'design'
    elif '에너지' in priority_text or '효율' in priority_text:
        return 'eco'
    elif '가성비' in priority_text or '성능' in priority_text:
        return 'value'
    return 'value'  # 기본값


def parse_budget_level(budget_text):
    """예산 레벨 파싱"""
    if '500만원 미만' in budget_text or '실속형' in budget_text:
        return 'low'
    elif '500만원 ~ 1,500만원' in budget_text or '표준형' in budget_text:
        return 'medium'
    elif '1,500만원 ~ 3,000만원' in budget_text or '고급형' in budget_text:
        return 'medium'  # medium-high
    elif '3,000만원 이상' in budget_text or '하이엔드' in budget_text:
        return 'high'
    return 'medium'  # 기본값


def parse_budget_amount(budget_text):
    """예산 금액 파싱"""
    if '500만원 미만' in budget_text:
        return 500000
    elif '500만원 ~ 1,500만원' in budget_text:
        return 1000000
    elif '1,500만원 ~ 3,000만원' in budget_text:
        return 2000000
    elif '3,000만원 이상' in budget_text:
        return 5000000
    return 2000000  # 기본값


def parse_cooking_laundry_media(row):
    """요리/세탁/미디어 패턴 파싱 (CSV에 직접 없으면 기본값)"""
    # CSV에 추가 질문이 있으면 파싱, 없으면 기본값
    cooking = 'sometimes'  # 기본값
    laundry = 'weekly'  # 기본값
    media = 'balanced'  # 기본값
    
    # 필요하면 CSV의 추가 컬럼에서 파싱
    return cooking, laundry, media


def csv_row_to_session_data(row):
    """CSV 행을 ONBOARDING_SESSION 데이터로 변환"""
    try:
        # CSV 컬럼명 직접 매핑 (실제 CSV 파일의 컬럼명 사용)
        columns = list(row.keys())
        
        # 컬럼명 찾기 (정확한 매칭)
        vibe_col = None
        mate_col = None
        pet_col = None
        housing_col = None
        space_col = None
        pyung_col = None
        priority_col = None
        budget_col = None
        
        for col in columns:
            col_lower = col.lower()
            if '무드' in col or '인테리어' in col or ('질문 1' in col and '무드' in col):
                vibe_col = col
            elif ('메이트' in col or '질문 2' in col) and '반려동물' not in col and '질문 2-1' not in col:
                mate_col = col
            elif '반려동물' in col or '질문 2-1' in col:
                pet_col = col
            elif '주거 형태' in col or ('질문 3' in col and '주거' in col):
                housing_col = col
            elif '주요 공간' in col or ('질문 3-1' in col):
                space_col = col
            elif '크기' in col or '평' in col or ('질문 3-2' in col):
                pyung_col = col
            elif '포기' in col or ('질문 4' in col):
                priority_col = col
            elif '예산' in col and '라인업' not in col and '선호' not in col:
                budget_col = col
        
        # 디버깅: 첫 번째 행만 컬럼명 출력
        if len(columns) > 0 and columns[0] == '타임스탬프':
            print(f"  CSV 컬럼: {len(columns)}개")
            print(f"    vibe: {vibe_col}")
            print(f"    mate: {mate_col}")
            print(f"    pet: {pet_col}")
            print(f"    housing: {housing_col}")
            print(f"    space: {space_col}")
            print(f"    pyung: {pyung_col}")
            print(f"    priority: {priority_col}")
            print(f"    budget: {budget_col}")
        
        # 데이터 추출
        vibe = parse_vibe(row.get(vibe_col, ''))
        household_size = parse_household_size(row.get(mate_col, ''))
        has_pet = parse_has_pet(row.get(pet_col, ''))
        housing_type = parse_housing_type(row.get(housing_col, ''))
        main_space = parse_main_space(row.get(space_col, ''))
        pyung = parse_pyung(row.get(pyung_col, ''))
        priority = parse_priority(row.get(priority_col, ''))
        budget_level = parse_budget_level(row.get(budget_col, ''))
        budget_amount = parse_budget_amount(row.get(budget_col, ''))
        
        cooking, laundry, media = parse_cooking_laundry_media(row)
        
        # onboarding_data에 taste 계산에 필요한 모든 필드 포함
        onboarding_data = {
            'vibe': vibe,
            'household_size': household_size,
            'housing_type': housing_type,
            'pyung': pyung,
            'main_space': main_space,
            'priority': priority,
            'budget_level': budget_level,
            'has_pet': has_pet,
            'cooking': cooking,
            'laundry': laundry,
            'media': media
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
        print(f"  ⚠ 파싱 오류: {str(e)}")
        import traceback
        print(f"  상세: {traceback.format_exc()[:200]}")
        return None


def main():
    """메인 함수"""
    print("=" * 80)
    print("온보딩 데이터 시뮬레이션 시작")
    print("=" * 80)
    print()
    
    # CSV 파일 경로
    csv_file = BASE_DIR / 'data' / '온보딩' / 'onboarding_survey_aug_1000.csv'
    
    if not csv_file.exists():
        print(f"✗ CSV 파일을 찾을 수 없습니다: {csv_file}")
        return
    
    print(f"✓ CSV 파일 로드: {csv_file}")
    
    # CSV 읽기
    sessions_data = []
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for idx, row in enumerate(reader, 1):
            # 첫 번째 행만 디버깅 정보 출력
            if idx == 1:
                print(f"  첫 번째 행 샘플:")
                for key, value in list(row.items())[:5]:
                    print(f"    {key}: {value[:50]}...")
                print()
            
            session_data = csv_row_to_session_data(row)
            if session_data:
                sessions_data.append(session_data)
            else:
                print(f"  ⚠ 행 {idx} 파싱 실패")
            
            if idx % 100 == 0:
                print(f"  [{idx}행] 파싱 중... (성공: {len(sessions_data)}개)")
    
    print(f"✓ 총 {len(sessions_data)}개 세션 데이터 파싱 완료")
    print()
    
    # Oracle DB 연결 확인
    print("[1/3] Oracle DB 연결 확인 중...")
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1 FROM DUAL")
        print("  ✓ Oracle DB 연결 성공")
    except Exception as e:
        print(f"  ✗ Oracle DB 연결 실패: {str(e)}")
        return
    print()
    
    # 데이터 삽입 및 시뮬레이션
    print("[2/3] 데이터 삽입 및 추천 시뮬레이션 중...")
    
    results = {
        'total': len(sessions_data),
        'inserted': 0,
        'recommendation_success': 0,
        'recommendation_failed': 0,
        'total_recommendations': 0
    }
    
    for idx, session_data in enumerate(sessions_data, 1):
        try:
            # 세션 ID 생성
            session_id = f"sim_{uuid.uuid4().hex[:16]}"
            user_id = f"user_{idx:04d}"
            
            # ONBOARDING_SESSION에 INSERT
            onboarding_db_service.create_or_update_session(
                session_id=session_id,
                user_id=user_id,
                current_step=7,
                status='COMPLETED',
                **session_data
            )
            results['inserted'] += 1
            
            # 추천 엔진 실행
            user_profile = {
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
            
            # taste_id 계산 (onboarding_data에 필요한 모든 필드 포함)
            taste_id = taste_classifier.calculate_taste_from_onboarding(
                session_data['onboarding_data']
            )
            
            # 추천 실행
            rec_result = recommendation_engine.get_recommendations(
                user_profile=user_profile,
                taste_id=taste_id,
                limit=5
            )
            
            if rec_result.get('success'):
                results['recommendation_success'] += 1
                results['total_recommendations'] += rec_result.get('count', 0)
            else:
                results['recommendation_failed'] += 1
            
            # 진행 상황 출력 (10개마다)
            if idx % 10 == 0 or idx == len(sessions_data):
                print(f"  [{idx}/{len(sessions_data)}] 진행 중... (삽입: {results['inserted']}, 추천 성공: {results['recommendation_success']})")
            
        except Exception as e:
            print(f"  ✗ 세션 {idx} 처리 실패: {str(e)}")
            results['recommendation_failed'] += 1
    
    print()
    
    # 결과 출력
    print("[3/3] 결과 통계")
    print("=" * 80)
    print(f"총 세션: {results['total']}개")
    print(f"DB 삽입 성공: {results['inserted']}개")
    print(f"추천 성공: {results['recommendation_success']}개")
    print(f"추천 실패: {results['recommendation_failed']}개")
    print(f"총 추천 제품 수: {results['total_recommendations']}개")
    print(f"추천 성공률: {results['recommendation_success']/results['total']*100:.1f}%")
    print()
    
    # 결과 저장
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_file = BASE_DIR / f"simulation_report_{timestamp}.json"
    
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2, default=str)
    
    print(f"상세 리포트 저장: {report_file}")
    print()
    print("=" * 80)
    print("시뮬레이션 완료!")
    print("=" * 80)


if __name__ == '__main__':
    main()

