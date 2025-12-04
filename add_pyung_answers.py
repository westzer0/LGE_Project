#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Q006 (평수) 질문에 대한 답변 선택지 추가
"""
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

from api.db.oracle_client import get_connection


def add_pyung_answers():
    """평수 답변 선택지 추가"""
    print("=" * 60)
    print("Q006 (평수) 답변 선택지 추가")
    print("=" * 60)
    
    try:
        conn = get_connection()
        print("\n[1] Oracle DB 연결 성공!")
        
        # 평수 범위별 선택지 (int 값으로 저장)
        pyung_options = [
            ('Q006', '10', '10평 이하', 1),
            ('Q006', '15', '11-15평', 2),
            ('Q006', '20', '16-20평', 3),
            ('Q006', '25', '21-25평', 4),
            ('Q006', '30', '26-30평', 5),
            ('Q006', '35', '31-35평', 6),
            ('Q006', '40', '36-40평', 7),
            ('Q006', '50', '41-50평', 8),
            ('Q006', '60', '51-60평', 9),
            ('Q006', '70', '61평 이상', 10),
        ]
        
        print("\n[2] 평수 답변 선택지 추가 중...")
        with conn.cursor() as cur:
            inserted = 0
            skipped = 0
            
            for q_code, answer_value, answer_text, order in pyung_options:
                try:
                    # 이미 존재하는지 확인
                    cur.execute("""
                        SELECT COUNT(*) FROM ONBOARDING_ANSWER
                        WHERE QUESTION_CODE = :q_code AND ANSWER_VALUE = :answer_value
                        AND SESSION_ID IS NULL
                    """, {
                        'q_code': q_code,
                        'answer_value': answer_value
                    })
                    exists = cur.fetchone()[0]
                    
                    if exists == 0:
                        # 현재 최대 ANSWER_ID 조회
                        cur.execute("SELECT NVL(MAX(ANSWER_ID), 0) FROM ONBOARDING_ANSWER")
                        max_id = cur.fetchone()[0]
                        next_id = max_id + 1
                        
                        cur.execute("""
                            INSERT INTO ONBOARDING_ANSWER (
                                ANSWER_ID, SESSION_ID, QUESTION_CODE, ANSWER_VALUE, CREATED_DATE
                            ) VALUES (
                                :answer_id, NULL, :q_code, :answer_value, SYSDATE
                            )
                        """, {
                            'answer_id': next_id,
                            'q_code': q_code,
                            'answer_value': answer_value
                        })
                        inserted += 1
                        print(f"  ✓ {q_code} - {answer_value}평: {answer_text}")
                    else:
                        skipped += 1
                        print(f"  ⚠ {q_code} - {answer_value}평 이미 존재")
                except Exception as e:
                    print(f"  ✗ {q_code} - {answer_value}평 추가 실패: {str(e)}")
            
            conn.commit()
            print(f"\n[3] 총 {inserted}개 평수 선택지 추가 완료!")
            if skipped > 0:
                print(f"    (이미 존재: {skipped}개)")
        
        # 최종 확인
        print("\n[4] 최종 확인:")
        from api.db.oracle_client import fetch_all_dict
        
        answers = fetch_all_dict("""
            SELECT ANSWER_ID, ANSWER_VALUE
            FROM ONBOARDING_ANSWER
            WHERE QUESTION_CODE = 'Q006' AND SESSION_ID IS NULL
            ORDER BY TO_NUMBER(ANSWER_VALUE)
        """)
        
        if answers:
            print(f"\n  Q006 (평수) 선택지: {len(answers)}개")
            for a in answers:
                print(f"    - {a['ANSWER_VALUE']}평")
        else:
            print("  ⚠ Q006 선택지가 없습니다")
        
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
    add_pyung_answers()

