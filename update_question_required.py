#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
ONBOARDING_QUESTION의 IS_REQUIRED 필드 수정
조건부 질문이지만, 나타나면 필수로 처리
"""
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

from api.db.oracle_client import get_connection


def update_required():
    """IS_REQUIRED 필드 업데이트"""
    print("=" * 60)
    print("질문 필수 여부 수정")
    print("=" * 60)
    
    try:
        conn = get_connection()
        print("\n[1] Oracle DB 연결 성공!")
        
        # 조건부 질문이지만 나타나면 필수인 경우
        # cooking, laundry, media는 조건부로 나타나지만, 나타나면 필수로 답변해야 함
        # 하지만 DB에서는 조건부로 표시하고, 애플리케이션 로직에서 필수 처리
        
        # 사용자 요청: 모든 질문을 필수로 변경
        questions_to_update = [
            ('cooking', 'Y', '주방을 선택한 경우 필수'),
            ('laundry', 'Y', '드레스룸을 선택한 경우 필수'),
            ('media', 'Y', '거실/방/서재를 선택한 경우 필수'),
        ]
        
        print("\n[2] IS_REQUIRED 필드 업데이트 중...")
        with conn.cursor() as cur:
            for q_type, is_required, reason in questions_to_update:
                try:
                    cur.execute("""
                        UPDATE ONBOARDING_QUESTION
                        SET IS_REQUIRED = :is_required
                        WHERE QUESTION_TYPE = :q_type
                    """, {
                        'is_required': is_required,
                        'q_type': q_type
                    })
                    affected = cur.rowcount
                    if affected > 0:
                        print(f"  ✓ {q_type}: IS_REQUIRED = {is_required} ({reason})")
                    else:
                        print(f"  ⚠ {q_type}: 질문을 찾을 수 없습니다")
                except Exception as e:
                    print(f"  ✗ {q_type} 업데이트 실패: {str(e)}")
        
        conn.commit()
        
        # 최종 확인
        print("\n[3] 최종 확인:")
        from api.db.oracle_client import fetch_all_dict
        questions = fetch_all_dict("""
            SELECT QUESTION_CODE, QUESTION_TEXT, QUESTION_TYPE, IS_REQUIRED
            FROM ONBOARDING_QUESTION
            WHERE QUESTION_TYPE IN ('cooking', 'laundry', 'media')
            ORDER BY QUESTION_TYPE
        """)
        
        for q in questions:
            req = "필수" if q['IS_REQUIRED'] == 'Y' else "선택"
            print(f"  {q['QUESTION_CODE']} [{q['QUESTION_TYPE']}]: {req} - {q['QUESTION_TEXT'][:50]}...")
        
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
    update_required()

