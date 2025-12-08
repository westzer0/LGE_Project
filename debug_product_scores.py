"""
제품별 점수 계산 디버깅 스크립트
"""
import oracledb
from api.db.oracle_client import get_connection
import json

def debug_taste_category(taste_id=1, category='TV'):
    """특정 taste_id와 category의 제품별 점수 계산 과정 확인"""
    print(f"=== Taste {taste_id}, Category: {category} 디버깅 ===\n")
    
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                # 1. TasteConfig 조회
                cur.execute("""
                    SELECT 
                        REPRESENTATIVE_VIBE,
                        REPRESENTATIVE_HOUSEHOLD_SIZE,
                        REPRESENTATIVE_PRIORITY,
                        REPRESENTATIVE_BUDGET_LEVEL,
                        REPRESENTATIVE_HAS_PET
                    FROM TASTE_CONFIG
                    WHERE TASTE_ID = :tid
                """, {'tid': taste_id})
                
                taste_row = cur.fetchone()
                if not taste_row:
                    print("TasteConfig를 찾을 수 없습니다.")
                    return
                
                vibe, household_size, priority, budget_level, has_pet = taste_row
                print(f"[Taste 설정]")
                print(f"  Vibe: {vibe}")
                print(f"  Household Size: {household_size}")
                print(f"  Priority: {priority}")
                print(f"  Budget Level: {budget_level}")
                print(f"  Has Pet: {has_pet}")
                print()
                
                # 2. 해당 카테고리의 제품 조회 (상위 5개)
                cur.execute("""
                    SELECT 
                        P.PRODUCT_ID,
                        P.MODEL_CODE,
                        P.PRODUCT_NAME,
                        P.PRICE
                    FROM (
                        SELECT 
                            PRODUCT_ID,
                            MODEL_CODE,
                            PRODUCT_NAME,
                            PRICE
                        FROM PRODUCT
                        WHERE STATUS = '판매중'
                          AND PRICE > 0
                          AND MAIN_CATEGORY = :cat
                        ORDER BY PRICE ASC
                    ) P
                    WHERE ROWNUM <= 5
                """, {'cat': category})
                
                products = cur.fetchall()
                print(f"[제품 목록] (상위 5개)")
                for i, (pid, model_code, name, price) in enumerate(products, 1):
                    print(f"  {i}. Product ID: {pid}, Model: {model_code}, Name: {name[:30]}, Price: {price:,.0f}원")
                print()
                
                # 3. 각 제품의 COMMON SPEC 조회
                for pid, model_code, name, price in products:
                    print(f"\n[Product ID: {pid}] {name[:40]}")
                    print(f"  Model: {model_code}, Price: {price:,.0f}원")
                    
                    cur.execute("""
                        SELECT SPEC_KEY, SPEC_VALUE
                        FROM PRODUCT_SPEC
                        WHERE PRODUCT_ID = :pid
                          AND SPEC_TYPE = 'COMMON'
                          AND SPEC_VALUE IS NOT NULL
                          AND SPEC_VALUE != 'nan'
                        ORDER BY SPEC_KEY
                    """, {'pid': pid})
                    
                    specs = cur.fetchall()
                    print(f"  COMMON SPEC 개수: {len(specs)}")
                    for spec_key, spec_value in specs:
                        print(f"    - {spec_key}: {spec_value}")
                    
                    if not specs:
                        print("    (COMMON SPEC 없음)")
                
                # 4. 점수 확인
                print(f"\n[저장된 점수]")
                cur.execute("""
                    SELECT RECOMMENDED_PRODUCTS, RECOMMENDED_PRODUCT_SCORES
                    FROM TASTE_CONFIG
                    WHERE TASTE_ID = :tid
                """, {'tid': taste_id})
                
                row = cur.fetchone()
                if row:
                    rec_prods, rec_scores = row
                    
                    if hasattr(rec_prods, 'read'):
                        rec_prods = json.loads(rec_prods.read())
                    elif isinstance(rec_prods, str):
                        rec_prods = json.loads(rec_prods)
                    
                    if hasattr(rec_scores, 'read'):
                        rec_scores = json.loads(rec_scores.read())
                    elif isinstance(rec_scores, str):
                        rec_scores = json.loads(rec_scores)
                    
                    if isinstance(rec_prods, dict) and category in rec_prods:
                        prods = rec_prods[category]
                        scores = rec_scores.get(category, []) if isinstance(rec_scores, dict) else []
                        print(f"  {category} 카테고리:")
                        for i, (prod_id, score) in enumerate(zip(prods, scores), 1):
                            print(f"    {i}. Product ID: {prod_id}, Score: {score}")
                    
    except Exception as e:
        print(f"오류 발생: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    import sys
    taste_id = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    category = sys.argv[2] if len(sys.argv) > 2 else 'TV'
    debug_taste_category(taste_id, category)

