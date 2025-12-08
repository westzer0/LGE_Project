"""Oracle 데이터 간단 확인"""
import os
import django
import json

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from api.db.oracle_client import get_connection

try:
    with get_connection() as conn:
        with conn.cursor() as cur:
            # 컬럼명 확인
            cur.execute("""
                SELECT column_name 
                FROM user_tab_columns 
                WHERE table_name = 'TASTE_CONFIG' 
                AND (column_name LIKE '%SCORE%' OR column_name LIKE '%ILL%')
                ORDER BY column_name
            """)
            columns = cur.fetchall()
            print(f"\n=== 관련 컬럼 목록 ===")
            for col in columns:
                print(f"  {col[0]}")
            
            # 데이터 확인 (간단하게)
            cur.execute("""
                SELECT 
                    TASTE_ID,
                    ILL_SUITED_CATEGORIES,
                    CATEGORY_SCORES
                FROM TASTE_CONFIG
                WHERE TASTE_ID IN (1, 2, 3, 4, 5)
                ORDER BY TASTE_ID
            """)
            results = cur.fetchall()
            
            print(f"\n=== 데이터 확인 (Taste 1-5) ===")
            for row in results:
                taste_id, ill_suited, category_scores = row
                print(f"\nTaste {taste_id}:")
                
                if ill_suited:
                    try:
                        ill_list = json.loads(ill_suited) if isinstance(ill_suited, str) else ill_suited
                        print(f"  ILL_SUITED: {ill_list[:3] if len(ill_list) > 3 else ill_list}... ({len(ill_list)}개)")
                    except:
                        print(f"  ILL_SUITED: {str(ill_suited)[:50]}...")
                else:
                    print(f"  ILL_SUITED: (NULL)")
                
                if category_scores:
                    try:
                        scores = json.loads(category_scores) if isinstance(category_scores, str) else category_scores
                        non_zero = {k: v for k, v in scores.items() if v > 0}
                        print(f"  CATEGORY_SCORES: {len(scores)}개 카테고리, {len(non_zero)}개 점수 > 0")
                        # 점수가 높은 상위 3개만
                        top3 = sorted(non_zero.items(), key=lambda x: x[1], reverse=True)[:3]
                        for cat, score in top3:
                            print(f"    {cat}: {score}")
                    except:
                        print(f"  CATEGORY_SCORES: 데이터 있음 (파싱 실패)")
                else:
                    print(f"  CATEGORY_SCORES: (NULL)")
                    
except Exception as e:
    print(f'오류 발생: {str(e)}')
    import traceback
    traceback.print_exc()



