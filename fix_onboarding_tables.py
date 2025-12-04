#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
1. ONBOARDING_SESSION에서 잘못 추가된 칼럼 제거
2. ONBOARDING_QUESTION에 질문 튜플 추가
"""
import sys
from pathlib import Path
from datetime import datetime

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

from api.db.oracle_client import get_connection, fetch_all_dict


def fix_tables():
    """테이블 수정"""
    print("=" * 60)
    print("온보딩 테이블 수정")
    print("=" * 60)
    
    try:
        conn = get_connection()
        print("\n[1] Oracle DB 연결 성공!")
        
        # 1. ONBOARDING_SESSION에서 잘못 추가된 칼럼 제거
        print("\n[2] ONBOARDING_SESSION에서 잘못 추가된 칼럼 제거 중...")
        columns_to_drop = ['HAS_PET', 'MAIN_SPACE', 'COOKING', 'LAUNDRY', 'MEDIA', 'PRIORITY_LIST']
        
        with conn.cursor() as cur:
            for col_name in columns_to_drop:
                try:
                    # 칼럼 존재 여부 확인
                    cur.execute("""
                        SELECT COUNT(*) FROM USER_TAB_COLUMNS
                        WHERE TABLE_NAME = 'ONBOARDING_SESSION' AND COLUMN_NAME = :col_name
                    """, {'col_name': col_name})
                    exists = cur.fetchone()[0]
                    
                    if exists > 0:
                        cur.execute(f"ALTER TABLE ONBOARDING_SESSION DROP COLUMN {col_name}")
                        print(f"  ✓ {col_name} 칼럼 제거 완료")
                    else:
                        print(f"  ⚠ {col_name} 칼럼이 존재하지 않습니다")
                except Exception as e:
                    print(f"  ✗ {col_name} 칼럼 제거 실패: {str(e)}")
        
        conn.commit()
        
        # 2. ONBOARDING_QUESTION에 질문 추가
        print("\n[3] ONBOARDING_QUESTION에 질문 추가 중...")
        
        questions = [
            # Step 1
            ('Q001', '새로운 가전과 함께할 공간, 어떤 분위기를 꿈꾸시나요?', 'vibe', 'Y'),
            # Step 2
            ('Q002', '이 공간에서 함께 생활하는 메이트는 누구인가요?', 'mate', 'Y'),
            ('Q003', '혹시 반려동물과 함께하시나요?', 'pet', 'Y'),
            # Step 3
            ('Q004', '가전을 설치할 곳의 주거 형태는 무엇인가요?', 'housing_type', 'Y'),
            ('Q005', '가전을 배치할 주요 공간은 어디인가요?', 'main_space', 'Y'),
            ('Q006', '해당 공간의 크기는 대략 어느 정도인가요?', 'pyung', 'Y'),
            # Step 4
            ('Q007', '평소 집에서 요리는 얼마나 자주 하시나요?', 'cooking', 'N'),
            ('Q008', '세탁은 주로 어떻게 하시나요?', 'laundry', 'N'),
            ('Q009', '집에서 TV나 영상을 주로 어떻게 즐기시나요?', 'media', 'N'),
            # Step 5
            ('Q010', '구매 시 가장 중요하게 생각하는 것은 무엇인가요?', 'priority', 'Y'),
            # Step 6
            ('Q011', '예산 범위를 선택해주세요.', 'budget', 'Y'),
        ]
        
        with conn.cursor() as cur:
            inserted = 0
            for q_code, q_text, q_type, is_required in questions:
                try:
                    # 질문이 이미 존재하는지 확인
                    cur.execute("""
                        SELECT COUNT(*) FROM ONBOARDING_QUESTION
                        WHERE QUESTION_CODE = :q_code
                    """, {'q_code': q_code})
                    exists = cur.fetchone()[0]
                    
                    if exists == 0:
                        cur.execute("""
                            INSERT INTO ONBOARDING_QUESTION (
                                QUESTION_CODE, QUESTION_TEXT, QUESTION_TYPE, IS_REQUIRED, CREATED_DATE
                            ) VALUES (
                                :q_code, :q_text, :q_type, :is_required, SYSDATE
                            )
                        """, {
                            'q_code': q_code,
                            'q_text': q_text,
                            'q_type': q_type,
                            'is_required': is_required
                        })
                        inserted += 1
                        print(f"  ✓ {q_code} - {q_type} 질문 추가")
                    else:
                        print(f"  ⚠ {q_code} 질문은 이미 존재합니다")
                except Exception as e:
                    print(f"  ✗ {q_code} 질문 추가 실패: {str(e)}")
            
            conn.commit()
            print(f"\n[4] 총 {inserted}개 질문 추가 완료!")
        
        # 최종 확인
        print("\n[5] 최종 확인:")
        with conn.cursor() as cur:
            # 질문 개수
            cur.execute("SELECT COUNT(*) FROM ONBOARDING_QUESTION")
            q_count = cur.fetchone()[0]
            print(f"  - ONBOARDING_QUESTION: {q_count}개 질문")
            
            # 질문 목록
            questions_list = fetch_all_dict("""
                SELECT QUESTION_CODE, QUESTION_TEXT, QUESTION_TYPE, IS_REQUIRED
                FROM ONBOARDING_QUESTION
                ORDER BY QUESTION_CODE
            """)
            
            print("\n[6] 질문 목록:")
            for q in questions_list:
                req = "필수" if q['IS_REQUIRED'] == 'Y' else "선택"
                print(f"  {q['QUESTION_CODE']}: [{q['QUESTION_TYPE']}] {q['QUESTION_TEXT'][:50]}... ({req})")
            
            # ONBOARDING_SESSION 칼럼 확인
            cur.execute("""
                SELECT COLUMN_NAME FROM USER_TAB_COLUMNS
                WHERE TABLE_NAME = 'ONBOARDING_SESSION'
                AND COLUMN_NAME IN ('HAS_PET', 'MAIN_SPACE', 'COOKING', 'LAUNDRY', 'MEDIA', 'PRIORITY_LIST')
            """)
            remaining_cols = [row[0] for row in cur.fetchall()]
            if remaining_cols:
                print(f"\n  ⚠ ONBOARDING_SESSION에 남아있는 칼럼: {', '.join(remaining_cols)}")
            else:
                print(f"\n  ✓ ONBOARDING_SESSION에서 잘못된 칼럼 모두 제거됨")
        
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
    fix_tables()

