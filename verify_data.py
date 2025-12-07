"""생성된 데이터 확인"""
import os
import django
import json

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from api.db.oracle_client import get_connection

try:
    with get_connection() as conn:
        with conn.cursor() as cur:
            # Taste 1 데이터 확인
            cur.execute("""
                SELECT 
                    TASTE_ID,
                    ILL_SUITED_CATEGORIES,
                    CATEGORY_SCORES,
                    TV_SCORE,
                    "냉장고_SCORE",
                    "세탁기_SCORE",
                    "에어컨_SCORE"
                FROM TASTE_CONFIG
                WHERE TASTE_ID = 1
            """)
            result = cur.fetchone()
            
            if result:
                taste_id, ill_suited, category_scores, tv_score, fridge_score, washer_score, ac_score = result
                print(f"\n=== Taste {taste_id} 데이터 확인 ===\n")
                
                # ILL_SUITED_CATEGORIES
                if ill_suited:
                    try:
                        ill_suited_list = json.loads(ill_suited) if isinstance(ill_suited, str) else ill_suited
                        print(f"ILL_SUITED_CATEGORIES: {ill_suited_list}")
                    except:
                        print(f"ILL_SUITED_CATEGORIES: {ill_suited}")
                else:
                    print("ILL_SUITED_CATEGORIES: (NULL)")
                
                # CATEGORY_SCORES
                if category_scores:
                    try:
                        scores_dict = json.loads(category_scores) if isinstance(category_scores, str) else category_scores
                        print(f"\nCATEGORY_SCORES (일부):")
                        for cat, score in list(scores_dict.items())[:5]:
                            print(f"  {cat}: {score}")
                    except:
                        print(f"\nCATEGORY_SCORES: {category_scores}")
                
                # 개별 컬럼 점수
                print(f"\n개별 컬럼 점수:")
                print(f"  TV_SCORE: {tv_score}")
                print(f"  냉장고_SCORE: {fridge_score}")
                print(f"  세탁기_SCORE: {washer_score}")
                print(f"  에어컨_SCORE: {ac_score}")
            else:
                print("Taste 1 데이터가 없습니다.")
                
except Exception as e:
    print(f'오류 발생: {str(e)}')
    import traceback
    traceback.print_exc()



