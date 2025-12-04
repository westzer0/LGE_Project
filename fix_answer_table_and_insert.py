#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
ONBOARDING_ANSWER 테이블 수정 및 답변 선택지 추가
"""
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

from api.db.oracle_client import get_connection


def fix_and_insert():
    """테이블 수정 및 답변 선택지 추가"""
    print("=" * 60)
    print("ONBOARDING_ANSWER 테이블 수정 및 답변 선택지 추가")
    print("=" * 60)
    
    try:
        conn = get_connection()
        print("\n[1] Oracle DB 연결 성공!")
        
        # SESSION_ID를 NULL 허용으로 변경 (선택지는 SESSION_ID가 없음)
        print("\n[2] ONBOARDING_ANSWER 테이블 수정 중...")
        with conn.cursor() as cur:
            try:
                # SESSION_ID를 NULL 허용으로 변경
                cur.execute("ALTER TABLE ONBOARDING_ANSWER MODIFY (SESSION_ID NULL)")
                print("  ✓ SESSION_ID를 NULL 허용으로 변경 완료")
            except Exception as e:
                error_msg = str(e)
                if '01442' in error_msg or 'column to be modified to NULL' in error_msg.lower():
                    print("  ⚠ SESSION_ID가 이미 NULL 허용입니다")
                else:
                    print(f"  ⚠ SESSION_ID 수정 실패 (무시): {str(e)}")
        
        conn.commit()
        
        # 답변 선택지 추가
        answer_options = [
            # Q001: vibe (4개)
            ('Q001', 'modern', '모던 & 미니멀', 1),
            ('Q001', 'cozy', '코지 & 네이처', 2),
            ('Q001', 'pop', '유니크 & 팝', 3),
            ('Q001', 'luxury', '럭셔리 & 아티스틱', 4),
            
            # Q002: mate (4개)
            ('Q002', 'alone', '나 혼자 산다', 1),
            ('Q002', 'couple', '우리 둘이 알콩달콩', 2),
            ('Q002', 'family_3_4', '아이가 있는 3~4인 가족', 3),
            ('Q002', 'family_5plus', '5인 이상 대가족', 4),
            
            # Q003: pet (2개)
            ('Q003', 'yes', '네, 사랑스러운 댕냥이가 있어요', 1),
            ('Q003', 'no', '아니요, 없어요', 2),
            
            # Q004: housing_type (4개)
            ('Q004', 'apartment', '아파트', 1),
            ('Q004', 'officetel', '오피스텔', 2),
            ('Q004', 'detached', '주택(단독/다가구)', 3),
            ('Q004', 'studio', '원룸', 4),
            
            # Q005: main_space (6개)
            ('Q005', 'living', '거실', 1),
            ('Q005', 'bedroom', '방', 2),
            ('Q005', 'kitchen', '주방', 3),
            ('Q005', 'dressing', '드레스룸', 4),
            ('Q005', 'study', '서재', 5),
            ('Q005', 'all', '전체', 6),
            
            # Q007: cooking (3개)
            ('Q007', 'rarely', '거의 하지 않아요(배달, 간편식 위주)', 1),
            ('Q007', 'sometimes', '가끔 해요(주말 위주)', 2),
            ('Q007', 'often', '요리하는 걸 좋아하고 자주 해요', 3),
            
            # Q008: laundry (3개)
            ('Q008', 'weekly', '일주일 1번 정도', 1),
            ('Q008', 'few_times', '일주일 2번~3번 정도', 2),
            ('Q008', 'daily', '매일 조금씩', 3),
            
            # Q009: media (4개)
            ('Q009', 'ott', '넷플릭스, 영화, 드라마 등 OTT를 즐기는 편', 1),
            ('Q009', 'gaming', '게임이 취미라 주로 게임을 즐기는 편', 2),
            ('Q009', 'tv', '뉴스나 예능 등 일반 프로그램 시청하는 편', 3),
            ('Q009', 'none', 'TV나 영상을 즐기는 편은 아니에요', 4),
            
            # Q010: priority (4개)
            ('Q010', 'design', '디자인/무드', 1),
            ('Q010', 'tech', '기술/성능', 2),
            ('Q010', 'eco', '에너지효율', 3),
            ('Q010', 'value', '가성비', 4),
            
            # Q011: budget (3개)
            ('Q011', 'budget', '500만원 이하', 1),
            ('Q011', 'standard', '500~2000만원', 2),
            ('Q011', 'premium', '2000만원 이상', 3),
        ]
        
        print("\n[3] 답변 선택지 추가 중...")
        with conn.cursor() as cur:
            inserted = 0
            skipped = 0
            
            for q_code, answer_value, answer_text, order in answer_options:
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
                        
                        # 선택지는 SESSION_ID를 NULL로 저장
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
                        print(f"  ✓ {q_code} - {answer_value}: {answer_text[:40]}...")
                    else:
                        skipped += 1
                        print(f"  ⚠ {q_code} - {answer_value} 이미 존재")
                except Exception as e:
                    print(f"  ✗ {q_code} - {answer_value} 추가 실패: {str(e)}")
            
            conn.commit()
            print(f"\n[4] 총 {inserted}개 답변 선택지 추가 완료!")
            if skipped > 0:
                print(f"    (이미 존재: {skipped}개)")
        
        # 최종 확인
        print("\n[5] 최종 확인:")
        from api.db.oracle_client import fetch_all_dict
        
        with conn.cursor() as cur:
            cur.execute("""
                SELECT q.QUESTION_CODE, q.QUESTION_TYPE, q.QUESTION_TEXT,
                       COUNT(a.ANSWER_ID) as ANSWER_COUNT
                FROM ONBOARDING_QUESTION q
                LEFT JOIN ONBOARDING_ANSWER a ON q.QUESTION_CODE = a.QUESTION_CODE AND a.SESSION_ID IS NULL
                GROUP BY q.QUESTION_CODE, q.QUESTION_TYPE, q.QUESTION_TEXT
                ORDER BY q.QUESTION_CODE
            """)
            results = cur.fetchall()
            
            print("\n  질문별 답변 선택지 개수:")
            total_answers = 0
            for row in results:
                q_code, q_type, q_text, count = row
                total_answers += count
                status = "✓" if count > 0 else "✗"
                print(f"    {status} {q_code} [{q_type}]: {count}개 - {q_text[:40]}...")
            
            print(f"\n  총 답변 선택지: {total_answers}개")
        
        # 샘플 답변 목록
        print("\n[6] 답변 선택지 샘플:")
        for q_code in ['Q001', 'Q002', 'Q003', 'Q004', 'Q005']:
            answers = fetch_all_dict(f"""
                SELECT ANSWER_ID, ANSWER_VALUE
                FROM ONBOARDING_ANSWER
                WHERE QUESTION_CODE = '{q_code}' AND SESSION_ID IS NULL
                ORDER BY ANSWER_ID
            """)
            if answers:
                print(f"\n  {q_code}:")
                for a in answers:
                    print(f"    - {a['ANSWER_VALUE']}")
        
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
    fix_and_insert()

