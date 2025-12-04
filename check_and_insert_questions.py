#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
ONBOARDING_QUESTION 테이블에 질문 데이터 확인 및 추가
"""
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

from api.db.oracle_client import get_connection, fetch_all_dict


def check_questions():
    """질문 데이터 확인"""
    print("=" * 60)
    print("ONBOARDING_QUESTION 테이블 확인")
    print("=" * 60)
    
    try:
        conn = get_connection()
        print("\n[1] Oracle DB 연결 성공!")
        
        # 현재 질문 개수 확인
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM ONBOARDING_QUESTION")
            count = cur.fetchone()[0]
            print(f"\n[2] 현재 질문 개수: {count}개")
            
            if count > 0:
                # 기존 질문 목록 조회
                questions = fetch_all_dict("""
                    SELECT QUESTION_ID, STEP_NUMBER, QUESTION_TYPE, QUESTION_TEXT, QUESTION_ORDER
                    FROM ONBOARDING_QUESTION
                    ORDER BY STEP_NUMBER, QUESTION_ORDER
                """)
                
                print("\n[3] 기존 질문 목록:")
                for q in questions:
                    print(f"  - Step {q['STEP_NUMBER']}: {q['QUESTION_TYPE']} - {q['QUESTION_TEXT'][:50]}...")
                
                if count >= 8:
                    print(f"\n✅ 질문이 이미 {count}개 존재합니다. 추가 작업이 필요 없습니다.")
                    return
            else:
                print("\n[3] 질문이 없습니다. 질문을 추가합니다...")
        
        # 질문 추가
        print("\n[4] 질문 데이터 삽입 중...")
        with conn.cursor() as cur:
            questions_data = [
                # Step 1
                (1, 'vibe', '새로운 가전과 함께할 공간, 어떤 분위기를 꿈꾸시나요?', 1, 'Y', None, None),
                # Step 2
                (2, 'mate', '이 공간에서 함께 생활하는 메이트는 누구인가요?', 1, 'Y', None, None),
                (2, 'pet', '혹시 반려동물과 함께하시나요?', 2, 'Y', 'mate_selected', 'any'),
                # Step 3
                (3, 'housing_type', '가전을 설치할 곳의 주거 형태는 무엇인가요?', 1, 'Y', None, None),
                (3, 'main_space', '가전을 배치할 주요 공간은 어디인가요?', 2, 'Y', 'housing_type_selected', 'any'),
                (3, 'pyung', '해당 공간의 크기는 대략 어느 정도인가요?', 3, 'Y', 'main_space_selected', 'any'),
                # Step 4
                (4, 'cooking', '평소 집에서 요리는 얼마나 자주 하시나요?', 1, 'N', 'main_space_selected', 'kitchen,all'),
                (4, 'laundry', '세탁은 주로 어떻게 하시나요?', 2, 'N', 'main_space_selected', 'dressing,all'),
                (4, 'media', '집에서 TV나 영상을 주로 어떻게 즐기시나요?', 3, 'N', 'main_space_selected', 'living,bedroom,study,all'),
                # Step 5
                (5, 'priority', '구매 시 가장 중요하게 생각하는 것은 무엇인가요?', 1, 'Y', None, None),
                # Step 6
                (6, 'budget', '예산 범위를 선택해주세요.', 1, 'Y', None, None),
            ]
            
            inserted = 0
            for step_num, q_type, q_text, q_order, is_required, cond_type, cond_value in questions_data:
                try:
                    # 질문이 이미 존재하는지 확인
                    cur.execute("""
                        SELECT COUNT(*) FROM ONBOARDING_QUESTION
                        WHERE STEP_NUMBER = :step_num AND QUESTION_TYPE = :q_type
                    """, {'step_num': step_num, 'q_type': q_type})
                    exists = cur.fetchone()[0]
                    
                    if exists == 0:
                        cur.execute("""
                            INSERT INTO ONBOARDING_QUESTION (
                                QUESTION_ID, STEP_NUMBER, QUESTION_TYPE, QUESTION_TEXT,
                                QUESTION_ORDER, IS_REQUIRED, CONDITION_TYPE, CONDITION_VALUE,
                                CREATED_AT, UPDATED_AT
                            ) VALUES (
                                SEQ_ONBOARDING_QUESTION.NEXTVAL,
                                :step_num, :q_type, :q_text, :q_order, :is_required,
                                :cond_type, :cond_value, SYSDATE, SYSDATE
                            )
                        """, {
                            'step_num': step_num,
                            'q_type': q_type,
                            'q_text': q_text,
                            'q_order': q_order,
                            'is_required': is_required,
                            'cond_type': cond_type,
                            'cond_value': cond_value
                        })
                        inserted += 1
                        print(f"  ✓ Step {step_num} - {q_type} 질문 추가")
                    else:
                        print(f"  ⚠ Step {step_num} - {q_type} 질문은 이미 존재합니다")
                except Exception as e:
                    print(f"  ✗ Step {step_num} - {q_type} 질문 추가 실패: {str(e)}")
            
            conn.commit()
            print(f"\n[5] 총 {inserted}개 질문 추가 완료!")
        
        # 최종 확인
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM ONBOARDING_QUESTION")
            final_count = cur.fetchone()[0]
            print(f"\n[6] 최종 질문 개수: {final_count}개")
            
            # 질문 목록 출력
            questions = fetch_all_dict("""
                SELECT QUESTION_ID, STEP_NUMBER, QUESTION_TYPE, QUESTION_TEXT, QUESTION_ORDER
                FROM ONBOARDING_QUESTION
                ORDER BY STEP_NUMBER, QUESTION_ORDER
            """)
            
            print("\n[7] 질문 목록:")
            for q in questions:
                print(f"  {q['QUESTION_ID']:3d}. Step {q['STEP_NUMBER']} - {q['QUESTION_TYPE']:15s} | {q['QUESTION_TEXT'][:60]}...")
        
        conn.close()
        print("\n" + "=" * 60)
        print("✅ 완료!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n✗ 오류 발생: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    check_questions()

