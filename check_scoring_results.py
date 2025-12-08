"""
Taste별 제품 Scoring 결과 확인 스크립트
"""
import oracledb
from api.db.oracle_client import get_connection
import json

def check_results(taste_id=None):
    """결과 확인"""
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                if taste_id:
                    # 특정 taste_id 확인
                    cur.execute("""
                        SELECT 
                            TASTE_ID,
                            RECOMMENDED_CATEGORIES,
                            RECOMMENDED_PRODUCTS,
                            RECOMMENDED_PRODUCT_SCORES
                        FROM TASTE_CONFIG
                        WHERE TASTE_ID = :taste_id
                    """, {'taste_id': taste_id})
                else:
                    # 전체 통계
                    cur.execute("""
                        SELECT 
                            COUNT(*) as total,
                            COUNT(CASE WHEN RECOMMENDED_PRODUCTS IS NOT NULL THEN 1 END) as has_products,
                            COUNT(CASE WHEN RECOMMENDED_PRODUCT_SCORES IS NOT NULL THEN 1 END) as has_scores
                        FROM TASTE_CONFIG
                        WHERE TASTE_ID BETWEEN 1 AND 120
                    """)
                    result = cur.fetchone()
                    print("=== 전체 통계 ===")
                    print(f"총 Taste 수: {result[0]}개")
                    print(f"제품이 있는 Taste: {result[1]}개")
                    print(f"점수가 있는 Taste: {result[2]}개")
                    print()
                    
                    # 샘플 몇 개 확인
                    cur.execute("""
                        SELECT 
                            TASTE_ID,
                            RECOMMENDED_CATEGORIES,
                            RECOMMENDED_PRODUCTS,
                            RECOMMENDED_PRODUCT_SCORES
                        FROM TASTE_CONFIG
                        WHERE TASTE_ID BETWEEN 1 AND 120
                        AND RECOMMENDED_PRODUCTS IS NOT NULL
                        AND ROWNUM <= 5
                        ORDER BY TASTE_ID
                    """)
                    print("=== 샘플 결과 (처음 5개) ===")
                    for row in cur.fetchall():
                        tid, rec_cats, rec_prods, rec_scores = row
                        
                        # CLOB 처리
                        if hasattr(rec_cats, 'read'):
                            rec_cats = json.loads(rec_cats.read())
                        elif isinstance(rec_cats, str):
                            rec_cats = json.loads(rec_cats)
                        else:
                            rec_cats = rec_cats
                            
                        if hasattr(rec_prods, 'read'):
                            rec_prods = json.loads(rec_prods.read())
                        elif isinstance(rec_prods, str):
                            rec_prods = json.loads(rec_prods)
                        else:
                            rec_prods = rec_prods
                            
                        if hasattr(rec_scores, 'read'):
                            rec_scores = json.loads(rec_scores.read())
                        elif isinstance(rec_scores, str):
                            rec_scores = json.loads(rec_scores)
                        else:
                            rec_scores = rec_scores
                        
                        print(f"\n[Taste {tid}]")
                        print(f"  카테고리: {list(rec_cats.keys()) if isinstance(rec_cats, dict) else rec_cats}")
                        if isinstance(rec_prods, dict):
                            for cat, prods in rec_prods.items():
                                scores = rec_scores.get(cat, []) if isinstance(rec_scores, dict) else []
                                print(f"  [{cat}]")
                                if prods:
                                    for i, (prod_id, score) in enumerate(zip(prods, scores), 1):
                                        print(f"    {i}. Product ID: {prod_id}, Score: {score}")
                                else:
                                    print(f"    (제품 없음)")
                        print("-" * 50)
                    return
                
                # 특정 taste_id 상세 확인
                result = cur.fetchone()
                if not result:
                    print(f"Taste {taste_id}를 찾을 수 없습니다.")
                    return
                
                tid, rec_cats, rec_prods, rec_scores = result
                
                # CLOB 처리
                if hasattr(rec_cats, 'read'):
                    rec_cats = json.loads(rec_cats.read())
                elif isinstance(rec_cats, str):
                    rec_cats = json.loads(rec_cats)
                    
                if hasattr(rec_prods, 'read'):
                    rec_prods = json.loads(rec_prods.read())
                elif isinstance(rec_prods, str):
                    rec_prods = json.loads(rec_prods)
                    
                if hasattr(rec_scores, 'read'):
                    rec_scores = json.loads(rec_scores.read())
                elif isinstance(rec_scores, str):
                    rec_scores = json.loads(rec_scores)
                
                print(f"=== Taste {tid} 상세 결과 ===")
                print(f"\n[추천 카테고리]")
                if isinstance(rec_cats, dict):
                    for cat in rec_cats.keys():
                        print(f"  - {cat}")
                else:
                    print(f"  {rec_cats}")
                
                print(f"\n[추천 제품 및 점수]")
                if isinstance(rec_prods, dict):
                    for cat, prods in rec_prods.items():
                        scores = rec_scores.get(cat, []) if isinstance(rec_scores, dict) else []
                        print(f"\n  [{cat}]")
                        if prods:
                            for i, (prod_id, score) in enumerate(zip(prods, scores), 1):
                                print(f"    {i}. Product ID: {prod_id}, Score: {score}")
                        else:
                            print(f"    (제품 없음)")
                else:
                    print(f"  {rec_prods}")
                    
    except Exception as e:
        print(f"오류 발생: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    import sys
    if len(sys.argv) > 1:
        taste_id = int(sys.argv[1])
        check_results(taste_id)
    else:
        check_results()

