#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Oracle 11g 호환 oracledb 클라이언트 (Thick 모드로 11g 지원)
"""
import os
from pathlib import Path
import oracledb
from dotenv import load_dotenv

# Oracle 11g 호환을 위해 Thick 모드 활성화
_thick_mode_initialized = False
try:
    # 이미 초기화되었는지 확인 (이미 초기화된 경우 예외 발생)
    # Oracle Client 라이브러리 경로 자동 감지
    oracle_home = os.environ.get('ORACLE_HOME')
    if oracle_home:
        try:
            oracledb.init_oracle_client(lib_dir=oracle_home)
            _thick_mode_initialized = True
        except Exception as e:
            if "already initialized" in str(e).lower() or "ORA-24315" in str(e):
                _thick_mode_initialized = True
            else:
                raise
    else:
        # PATH에서 자동 감지 시도
        oracle_paths = [
            r"C:\oraclexe\app\oracle\product\11.2.0\server\bin",
            r"C:\app\oracle\product\11.2.0\server\bin",
            r"C:\instantclient_21_3",
            r"C:\instantclient_19_8",
        ]
        for path in oracle_paths:
            if os.path.exists(path):
                try:
                    oracledb.init_oracle_client(lib_dir=path)
                    _thick_mode_initialized = True
                    break
                except Exception as e:
                    if "already initialized" in str(e).lower() or "ORA-24315" in str(e):
                        _thick_mode_initialized = True
                        break
                    continue
except Exception as e:
    error_msg = str(e).lower()
    if "already initialized" in error_msg or "ORA-24315" in str(e):
        _thick_mode_initialized = True

# .env 로드 (기존 코드 그대로)
BASE_DIR = Path(__file__).resolve().parent.parent.parent
env_path = BASE_DIR / ".env"
if env_path.exists():
    try:
        with open(env_path, 'r', encoding='utf-8') as f:
            from dotenv import dotenv_values
            env_vars = dotenv_values(stream=f)
            for key, value in env_vars.items():
                if value is not None:
                    os.environ.setdefault(key, value)
    except:
        try:
            with open(env_path, 'r', encoding='cp949') as f:
                from dotenv import dotenv_values
                env_vars = dotenv_values(stream=f)
                for key, value in env_vars.items():
                    if value is not None:
                        os.environ.setdefault(key, value)
        except Exception:
            pass

# 환경 변수 설정 (기존 그대로)
DISABLE_DB = os.getenv("DISABLE_DB", "false").lower() == "true"
ORACLE_USER = os.getenv("ORACLE_USER", "campus_24K_LG3_DX7_p3_4")
ORACLE_PASSWORD = os.getenv("ORACLE_PASSWORD", "smhrd4")
ORACLE_HOST = os.getenv("ORACLE_HOST", "project-db-campus.smhrd.com")
ORACLE_PORT = int(os.getenv("ORACLE_PORT", "1524"))
ORACLE_SID = os.getenv("ORACLE_SID", "xe")

if not DISABLE_DB:
    DSN = f"{ORACLE_HOST}:{ORACLE_PORT}/{ORACLE_SID}"
else:
    DSN = None

class DatabaseDisabledError(Exception):
    pass

def get_connection():
    """oracledb 연결 (11g 완벽 지원)"""
    if DISABLE_DB:
        raise DatabaseDisabledError("DISABLE_DB=true")
    
    return oracledb.connect(
        user=ORACLE_USER,
        password=ORACLE_PASSWORD,
        dsn=DSN,
    )

def fetch_all(sql, params=None):
    """모든 행 반환"""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, params or {})
            return cur.fetchall()

def fetch_all_dict(sql, params=None):
    """Dict 리스트 반환"""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, params or {})
            cols = [c[0] for c in cur.description]
            return [dict(zip(cols, row)) for row in cur.fetchall()]

def fetch_one(sql, params=None):
    """단일 행 반환"""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, params or {})
            return cur.fetchone()


# ============================================================
# 데이터 로드 함수 (Oracle → Django)
# ============================================================

def load_all_lg_products():
    """
    Oracle DB의 PRODUCT 테이블에서 모든 LG 가전 제품을 Django Product 모델로 로드
    
    사용법:
        from api.db.oracle_client import load_all_lg_products
        load_all_lg_products()
    """
    try:
        from api.models import Product
        
        print("[데이터 로드] Oracle DB에서 제품 데이터 로드 시작...")
        
        # Oracle DB에서 제품 조회
        products = fetch_all_dict("""
            SELECT 
                PRODUCT_ID,
                PRODUCT_NAME,
                MAIN_CATEGORY,
                SUB_CATEGORY,
                MODEL_CODE,
                STATUS,
                PRICE,
                DISCOUNT_PRICE,
                RATING,
                URL,
                IMAGE_URL
            FROM PRODUCT
            WHERE PRODUCT_NAME IS NOT NULL
            ORDER BY PRODUCT_ID
        """)
        
        print(f"[데이터 로드] Oracle DB에서 {len(products)}개 제품 조회 완료")
        
        created_count = 0
        updated_count = 0
        
        for prod_data in products:
            product_id = prod_data.get('PRODUCT_ID')
            if not product_id:
                continue
            
            # Django Product 모델에 저장/업데이트
            product, created = Product.objects.update_or_create(
                product_id=product_id,
                defaults={
                    'product_name': prod_data.get('PRODUCT_NAME', ''),
                    'main_category': prod_data.get('MAIN_CATEGORY', ''),
                    'sub_category': prod_data.get('SUB_CATEGORY'),
                    'model_code': prod_data.get('MODEL_CODE'),
                    'status': prod_data.get('STATUS'),
                    'price': prod_data.get('PRICE'),
                    'discount_price': prod_data.get('DISCOUNT_PRICE'),
                    'rating': prod_data.get('RATING'),
                    'url': prod_data.get('URL'),
                    'image_url': prod_data.get('IMAGE_URL', ''),
                    'name': prod_data.get('PRODUCT_NAME', ''),  # 하위 호환성
                    'model_number': prod_data.get('MODEL_CODE'),
                    'category': prod_data.get('MAIN_CATEGORY', ''),
                }
            )
            
            if created:
                created_count += 1
            else:
                updated_count += 1
        
        print(f"[데이터 로드] 완료: {created_count}개 생성, {updated_count}개 업데이트")
        print(f"[데이터 로드] 총 {Product.objects.count()}개 제품이 Django DB에 저장됨")
        
        return {
            'total': len(products),
            'created': created_count,
            'updated': updated_count,
        }
        
    except Exception as e:
        print(f"[데이터 로드] 오류 발생: {str(e)}")
        import traceback
        traceback.print_exc()
        raise


def load_taste_configs():
    """
    Oracle DB의 TASTE_CONFIG 테이블에서 Taste 설정을 Django TasteConfig 모델로 로드
    
    사용법:
        from api.db.oracle_client import load_taste_configs
        load_taste_configs()
    """
    try:
        from api.models import TasteConfig
        import json
        
        print("[데이터 로드] Oracle DB에서 Taste 설정 로드 시작...")
        
        # Oracle DB에서 Taste 설정 조회
        taste_configs = fetch_all_dict("""
            SELECT 
                TASTE_ID,
                DESCRIPTION,
                REPRESENTATIVE_VIBE,
                REPRESENTATIVE_HOUSEHOLD_SIZE,
                REPRESENTATIVE_MAIN_SPACE,
                REPRESENTATIVE_HAS_PET,
                REPRESENTATIVE_PRIORITY,
                REPRESENTATIVE_BUDGET_LEVEL,
                RECOMMENDED_CATEGORIES,
                CATEGORY_SCORES,
                RECOMMENDED_PRODUCTS,
                ILL_SUITED_CATEGORIES,
                IS_ACTIVE,
                AUTO_GENERATED
            FROM TASTE_CONFIG
            ORDER BY TASTE_ID
        """)
        
        print(f"[데이터 로드] Oracle DB에서 {len(taste_configs)}개 Taste 설정 조회 완료")
        
        created_count = 0
        updated_count = 0
        
        for taste_data in taste_configs:
            taste_id = taste_data.get('TASTE_ID')
            if not taste_id:
                continue
            
            # JSON 필드 파싱
            recommended_categories = []
            if taste_data.get('RECOMMENDED_CATEGORIES'):
                try:
                    if isinstance(taste_data['RECOMMENDED_CATEGORIES'], str):
                        recommended_categories = json.loads(taste_data['RECOMMENDED_CATEGORIES'])
                    else:
                        recommended_categories = taste_data['RECOMMENDED_CATEGORIES']
                except:
                    recommended_categories = []
            
            category_scores = {}
            if taste_data.get('CATEGORY_SCORES'):
                try:
                    if isinstance(taste_data['CATEGORY_SCORES'], str):
                        category_scores = json.loads(taste_data['CATEGORY_SCORES'])
                    else:
                        category_scores = taste_data['CATEGORY_SCORES']
                except:
                    category_scores = {}
            
            recommended_products = {}
            if taste_data.get('RECOMMENDED_PRODUCTS'):
                try:
                    if isinstance(taste_data['RECOMMENDED_PRODUCTS'], str):
                        recommended_products = json.loads(taste_data['RECOMMENDED_PRODUCTS'])
                    else:
                        recommended_products = taste_data['RECOMMENDED_PRODUCTS']
                except:
                    recommended_products = {}
            
            ill_suited_categories = []
            if taste_data.get('ILL_SUITED_CATEGORIES'):
                try:
                    if isinstance(taste_data['ILL_SUITED_CATEGORIES'], str):
                        ill_suited_categories = json.loads(taste_data['ILL_SUITED_CATEGORIES'])
                    else:
                        ill_suited_categories = taste_data['ILL_SUITED_CATEGORIES']
                except:
                    ill_suited_categories = []
            
            # Django TasteConfig 모델에 저장/업데이트
            taste_config, created = TasteConfig.objects.update_or_create(
                taste_id=taste_id,
                defaults={
                    'description': taste_data.get('DESCRIPTION', ''),
                    'representative_vibe': taste_data.get('REPRESENTATIVE_VIBE', ''),
                    'representative_household_size': taste_data.get('REPRESENTATIVE_HOUSEHOLD_SIZE'),
                    'representative_main_space': taste_data.get('REPRESENTATIVE_MAIN_SPACE', ''),
                    'representative_has_pet': taste_data.get('REPRESENTATIVE_HAS_PET') == 1 if taste_data.get('REPRESENTATIVE_HAS_PET') is not None else None,
                    'representative_priority': taste_data.get('REPRESENTATIVE_PRIORITY', ''),
                    'representative_budget_level': taste_data.get('REPRESENTATIVE_BUDGET_LEVEL', ''),
                    'recommended_categories': recommended_categories,
                    'recommended_categories_with_scores': category_scores,
                    'recommended_products': recommended_products,
                    'ill_suited_categories': ill_suited_categories,
                    'is_active': taste_data.get('IS_ACTIVE', 'Y') == 'Y' if isinstance(taste_data.get('IS_ACTIVE'), str) else bool(taste_data.get('IS_ACTIVE', True)),
                    'auto_generated': taste_data.get('AUTO_GENERATED', 'N') == 'Y' if isinstance(taste_data.get('AUTO_GENERATED'), str) else bool(taste_data.get('AUTO_GENERATED', False)),
                }
            )
            
            if created:
                created_count += 1
            else:
                updated_count += 1
        
        print(f"[데이터 로드] 완료: {created_count}개 생성, {updated_count}개 업데이트")
        print(f"[데이터 로드] 총 {TasteConfig.objects.count()}개 Taste 설정이 Django DB에 저장됨")
        
        return {
            'total': len(taste_configs),
            'created': created_count,
            'updated': updated_count,
        }
        
    except Exception as e:
        print(f"[데이터 로드] 오류 발생: {str(e)}")
        import traceback
        traceback.print_exc()
        raise


def load_onboarding_questions():
    """
    Oracle DB의 ONBOARDING_QUESTION 테이블에서 온보딩 질문을 Django OnboardingQuestion 모델로 로드
    
    사용법:
        from api.db.oracle_client import load_onboarding_questions
        load_onboarding_questions()
    """
    try:
        from api.models import OnboardingQuestion, OnboardingAnswer
        
        print("[데이터 로드] Oracle DB에서 온보딩 질문 로드 시작...")
        
        # Oracle DB에서 온보딩 질문 조회
        questions = fetch_all_dict("""
            SELECT 
                QUESTION_CODE,
                QUESTION_TEXT,
                QUESTION_TYPE,
                IS_REQUIRED
            FROM ONBOARDING_QUESTION
            ORDER BY QUESTION_CODE
        """)
        
        print(f"[데이터 로드] Oracle DB에서 {len(questions)}개 질문 조회 완료")
        
        created_count = 0
        updated_count = 0
        
        for q_data in questions:
            question_code = q_data.get('QUESTION_CODE')
            if not question_code:
                continue
            
            # Django OnboardingQuestion 모델에 저장/업데이트
            question, created = OnboardingQuestion.objects.update_or_create(
                question_code=question_code,
                defaults={
                    'question_text': q_data.get('QUESTION_TEXT', ''),
                    'question_type': q_data.get('QUESTION_TYPE', ''),
                    'is_required': q_data.get('IS_REQUIRED', 'Y'),
                }
            )
            
            if created:
                created_count += 1
            else:
                updated_count += 1
            
            # 답변 선택지도 로드
            answers = fetch_all_dict("""
                SELECT 
                    ANSWER_ID,
                    ANSWER_VALUE,
                    ANSWER_TEXT
                FROM ONBOARDING_ANSWER
                WHERE QUESTION_CODE = :question_code
                ORDER BY ANSWER_ID
            """, {'question_code': question_code})
            
            for a_data in answers:
                answer_id = a_data.get('ANSWER_ID')
                if not answer_id:
                    continue
                
                OnboardingAnswer.objects.update_or_create(
                    answer_id=answer_id,
                    defaults={
                        'question': question,
                        'answer_value': a_data.get('ANSWER_VALUE'),
                        'answer_text': a_data.get('ANSWER_TEXT'),
                    }
                )
        
        print(f"[데이터 로드] 완료: {created_count}개 질문 생성, {updated_count}개 질문 업데이트")
        print(f"[데이터 로드] 총 {OnboardingQuestion.objects.count()}개 질문이 Django DB에 저장됨")
        
        return {
            'total': len(questions),
            'created': created_count,
            'updated': updated_count,
        }
        
    except Exception as e:
        print(f"[데이터 로드] 오류 발생: {str(e)}")
        import traceback
        traceback.print_exc()
        raise

# oracledb Oracle 11g 클라이언트 로드 완료
