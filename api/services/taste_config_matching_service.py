"""
온보딩 세션 정보를 기반으로 TASTE_CONFIG 테이블에서 매칭되는 데이터를 조회하는 서비스
"""
import json
import logging
from api.db.oracle_client import get_connection

logger = logging.getLogger(__name__)


class TasteConfigMatchingService:
    """온보딩 세션과 TASTE_CONFIG 매칭 서비스"""
    
    @staticmethod
    def get_taste_config_by_onboarding(session):
        """
        OnboardingSession 객체를 받아서 TASTE_CONFIG 테이블에서 매칭되는 데이터 조회
        
        Args:
            session: OnboardingSession 모델 인스턴스
            
        Returns:
            dict: {
                'taste_id': int,
                'description': str,
                'recommended_categories': list,
                'recommended_products': dict,
                'recommended_product_scores': dict
            } 또는 None (매칭 실패 시)
        """
        try:
            # 온보딩 세션에서 매칭 조건 추출
            vibe = session.vibe
            household_size = session.household_size
            has_pet = session.has_pet
            priority = session.priority
            budget_level = session.budget_level
            
            # priority 값 매핑 (Step 5의 priority 값을 TASTE_CONFIG의 REPRESENTATIVE_PRIORITY 값으로 변환)
            priority_mapping = {
                'design': 'design',
                'ai_smart': 'tech',  # AI/스마트 기능 → 기술/성능
                'energy': 'eco',  # 에너지 효율 → 에너지효율
                'cost_effective': 'value',  # 가성비 → 가성비
                'tech': 'tech',  # 기존 값도 지원
                'eco': 'eco',  # 기존 값도 지원
                'value': 'value',  # 기존 값도 지원
            }
            
            # priority가 리스트인 경우 첫 번째 값 사용
            if isinstance(priority, list) and len(priority) > 0:
                priority_first = priority[0]
            else:
                priority_first = priority if priority else 'value'
            
            # priority 값을 매핑 (없으면 그대로 사용)
            mapped_priority = priority_mapping.get(priority_first, priority_first)
            
            logger.info(f"[TasteConfigMatching] Priority 매핑: {priority} (first: {priority_first}) → {mapped_priority}")
            
            # budget_level 값 매핑 (온보딩 budget_level 값을 TASTE_CONFIG의 REPRESENTATIVE_BUDGET_LEVEL 값으로 변환)
            budget_level_mapping = {
                'budget': 'low',  # 예산형 → low
                'standard': 'medium',  # 표준형 → medium
                'premium': 'high',  # 프리미엄 → high (TASTE_CONFIG에 premium이 없으므로 high로 매핑)
                'luxury': 'luxury',  # 럭셔리 → luxury
                'low': 'low',  # 기존 값도 지원
                'medium': 'medium',  # 기존 값도 지원
                'high': 'high',  # 기존 값도 지원
            }
            
            # budget_level 값을 매핑 (없으면 그대로 사용)
            mapped_budget_level = budget_level_mapping.get(budget_level, budget_level)
            
            logger.info(f"[TasteConfigMatching] Budget Level 매핑: {budget_level} → {mapped_budget_level}")
            
            # 필수 값 검증
            if not all([vibe, household_size is not None, has_pet is not None, mapped_priority, mapped_budget_level]):
                logger.warning(f"[TasteConfigMatching] 필수 값 누락: vibe={vibe}, household_size={household_size}, "
                             f"has_pet={has_pet}, priority={mapped_priority}, budget_level={mapped_budget_level}")
                return None
            
            # has_pet을 Oracle CHAR(1) 형식으로 변환 ('Y'/'N')
            has_pet_char = 'Y' if has_pet else 'N'
            
            # Oracle DB에서 TASTE_CONFIG 조회
            with get_connection() as conn:
                with conn.cursor() as cur:
                    query = """
                        SELECT 
                            TASTE_ID,
                            DESCRIPTION,
                            RECOMMENDED_CATEGORIES,
                            RECOMMENDED_PRODUCTS,
                            RECOMMENDED_PRODUCT_SCORES
                        FROM TASTE_CONFIG
                        WHERE REPRESENTATIVE_VIBE = :vibe
                          AND REPRESENTATIVE_HOUSEHOLD_SIZE = :household_size
                          AND REPRESENTATIVE_HAS_PET = :has_pet
                          AND REPRESENTATIVE_PRIORITY = :priority
                          AND REPRESENTATIVE_BUDGET_LEVEL = :budget_level
                          AND IS_ACTIVE = 'Y'
                    """
                    
                    cur.execute(query, {
                        'vibe': vibe,
                        'household_size': int(household_size),
                        'has_pet': has_pet_char,
                        'priority': mapped_priority,  # 매핑된 priority 값 사용
                        'budget_level': mapped_budget_level  # 매핑된 budget_level 값 사용
                    })
                    
                    logger.info(f"[TasteConfigMatching] 조회 쿼리 실행: vibe={vibe}, household_size={int(household_size)}, "
                              f"has_pet={has_pet_char}, priority={mapped_priority}, budget_level={mapped_budget_level} (원본: {budget_level})")
                    
                    row = cur.fetchone()
                    
                    if not row:
                        logger.warning(f"[TasteConfigMatching] 매칭되는 TASTE_CONFIG를 찾을 수 없음: "
                                     f"vibe={vibe}, household_size={household_size}, has_pet={has_pet_char}, "
                                     f"priority={mapped_priority} (원본: {priority}), budget_level={mapped_budget_level} (원본: {budget_level})")
                        
                        # 매칭 실패 시 부분 매칭 시도 (priority 제외)
                        logger.info(f"[TasteConfigMatching] 부분 매칭 시도 중 (priority 제외)...")
                        partial_query = """
                            SELECT 
                                TASTE_ID,
                                DESCRIPTION,
                                RECOMMENDED_CATEGORIES,
                                RECOMMENDED_PRODUCTS,
                                RECOMMENDED_PRODUCT_SCORES
                            FROM (
                                SELECT 
                                    TASTE_ID,
                                    DESCRIPTION,
                                    RECOMMENDED_CATEGORIES,
                                    RECOMMENDED_PRODUCTS,
                                    RECOMMENDED_PRODUCT_SCORES
                                FROM TASTE_CONFIG
                                WHERE REPRESENTATIVE_VIBE = :vibe
                                  AND REPRESENTATIVE_HOUSEHOLD_SIZE = :household_size
                                  AND REPRESENTATIVE_HAS_PET = :has_pet
                                  AND REPRESENTATIVE_BUDGET_LEVEL = :budget_level
                                  AND IS_ACTIVE = 'Y'
                                ORDER BY TASTE_ID
                            )
                            WHERE ROWNUM <= 1
                        """
                        cur.execute(partial_query, {
                            'vibe': vibe,
                            'household_size': int(household_size),
                            'has_pet': has_pet_char,
                            'budget_level': mapped_budget_level  # 매핑된 budget_level 값 사용
                        })
                        row = cur.fetchone()
                        
                        if row:
                            logger.info(f"[TasteConfigMatching] 부분 매칭 성공 (priority 무시): taste_id={row[0]}")
                        else:
                            logger.warning(f"[TasteConfigMatching] 부분 매칭도 실패")
                            return None
                    
                    taste_id = row[0]
                    description = row[1] or ""
                    recommended_categories_clob = row[2]
                    recommended_products_clob = row[3]
                    recommended_product_scores_clob = row[4]
                    
                    # CLOB 필드 파싱
                    # 1. RECOMMENDED_CATEGORIES (JSON 배열)
                    recommended_categories = []
                    if recommended_categories_clob:
                        try:
                            clob_text = recommended_categories_clob.read() if hasattr(recommended_categories_clob, 'read') else str(recommended_categories_clob)
                            if clob_text:
                                recommended_categories = json.loads(clob_text)
                                if not isinstance(recommended_categories, list):
                                    recommended_categories = []
                        except json.JSONDecodeError as e:
                            logger.error(f"[TasteConfigMatching] RECOMMENDED_CATEGORIES JSON 파싱 실패 (taste_id={taste_id}): {e}")
                            recommended_categories = []
                        except Exception as e:
                            logger.error(f"[TasteConfigMatching] RECOMMENDED_CATEGORIES 읽기 실패 (taste_id={taste_id}): {e}")
                            recommended_categories = []
                    
                    # 2. RECOMMENDED_PRODUCTS (JSON 객체)
                    recommended_products = {}
                    if recommended_products_clob:
                        try:
                            clob_text = recommended_products_clob.read() if hasattr(recommended_products_clob, 'read') else str(recommended_products_clob)
                            if clob_text:
                                recommended_products = json.loads(clob_text)
                                if not isinstance(recommended_products, dict):
                                    recommended_products = {}
                        except json.JSONDecodeError as e:
                            logger.error(f"[TasteConfigMatching] RECOMMENDED_PRODUCTS JSON 파싱 실패 (taste_id={taste_id}): {e}")
                            recommended_products = {}
                        except Exception as e:
                            logger.error(f"[TasteConfigMatching] RECOMMENDED_PRODUCTS 읽기 실패 (taste_id={taste_id}): {e}")
                            recommended_products = {}
                    
                    # 3. RECOMMENDED_PRODUCT_SCORES (JSON 객체)
                    recommended_product_scores = {}
                    if recommended_product_scores_clob:
                        try:
                            clob_text = recommended_product_scores_clob.read() if hasattr(recommended_product_scores_clob, 'read') else str(recommended_product_scores_clob)
                            if clob_text:
                                recommended_product_scores = json.loads(clob_text)
                                if not isinstance(recommended_product_scores, dict):
                                    recommended_product_scores = {}
                        except json.JSONDecodeError as e:
                            logger.error(f"[TasteConfigMatching] RECOMMENDED_PRODUCT_SCORES JSON 파싱 실패 (taste_id={taste_id}): {e}")
                            recommended_product_scores = {}
                        except Exception as e:
                            logger.error(f"[TasteConfigMatching] RECOMMENDED_PRODUCT_SCORES 읽기 실패 (taste_id={taste_id}): {e}")
                            recommended_product_scores = {}
                    
                    result = {
                        'taste_id': int(taste_id),
                        'description': description,
                        'recommended_categories': recommended_categories,
                        'recommended_products': recommended_products,
                        'recommended_product_scores': recommended_product_scores
                    }
                    
                    logger.info(f"[TasteConfigMatching] 매칭 성공: taste_id={taste_id}, "
                              f"categories={len(recommended_categories)}, "
                              f"products_keys={len(recommended_products)}")
                    
                    return result
                    
        except Exception as e:
            logger.error(f"[TasteConfigMatching] TASTE_CONFIG 조회 중 오류 발생: {e}", exc_info=True)
            return None

