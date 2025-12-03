"""
Oracle 직접 연결 클라이언트
Django ORM 대신 oracledb를 직접 사용하여 Oracle 11g에 연결

사용 예시:
    from api.db import fetch_all, fetch_one
    
    # SELECT 쿼리
    results = fetch_all("SELECT * FROM users WHERE id = :id", {"id": 1})
    
    # 단일 행 조회
    user = fetch_one("SELECT * FROM users WHERE id = :id", {"id": 1})
    
    # INSERT/UPDATE/DELETE
    execute("INSERT INTO users (name, email) VALUES (:name, :email)", 
            {"name": "홍길동", "email": "test@example.com"})
"""
import oracledb
import os
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple
from contextlib import contextmanager

# .env 파일 로드
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent.parent
load_dotenv(BASE_DIR / ".env")

# Thick 모드 초기화 (한 번만 실행)
_oracle_initialized = False

def _ensure_oracle_client():
    """Oracle Instant Client 초기화 (Thick 모드)"""
    global _oracle_initialized
    if _oracle_initialized:
        return
    
    try:
        oracledb.init_oracle_client()  # PATH에서 oci.dll 찾기
        _oracle_initialized = True
    except Exception as e:
        error_msg = str(e).lower()
        if "already initialized" in error_msg:
            _oracle_initialized = True
        else:
            raise RuntimeError(f"Oracle Instant Client 초기화 실패: {e}") from e

# 모듈 임포트 시 초기화
_ensure_oracle_client()

# 연결 정보
USER = os.getenv("ORACLE_USER", "campus_24K_LG3_DX7_p3_4")
PASSWORD = os.getenv("ORACLE_PASSWORD", "smhrd4")
HOST = os.getenv("ORACLE_HOST", "project-db-campus.smhrd.com")
PORT = int(os.getenv("ORACLE_PORT", "1524"))
SID = os.getenv("ORACLE_SID", "xe")

# DSN 생성
DSN = oracledb.makedsn(HOST, PORT, sid=SID)


@contextmanager
def get_connection():
    """
    Oracle 연결 컨텍스트 매니저
    
    사용 예시:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users")
            results = cursor.fetchall()
    """
    conn = None
    try:
        conn = oracledb.connect(user=USER, password=PASSWORD, dsn=DSN)
        yield conn
        conn.commit()
    except Exception:
        if conn:
            conn.rollback()
        raise
    finally:
        if conn:
            conn.close()


def fetch_all(sql: str, params: Optional[Dict[str, Any]] = None) -> List[Tuple]:
    """
    SELECT 쿼리 실행 후 모든 결과 반환
    
    Args:
        sql: SQL 쿼리 문자열
        params: 바인딩 파라미터 딕셔너리
        
    Returns:
        결과 튜플 리스트
        
    사용 예시:
        users = fetch_all("SELECT * FROM users WHERE age > :age", {"age": 18})
    """
    params = params or {}
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, params)
            return cur.fetchall()


def fetch_one(sql: str, params: Optional[Dict[str, Any]] = None) -> Optional[Tuple]:
    """
    SELECT 쿼리 실행 후 첫 번째 결과만 반환
    
    Args:
        sql: SQL 쿼리 문자열
        params: 바인딩 파라미터 딕셔너리
        
    Returns:
        결과 튜플 또는 None
        
    사용 예시:
        user = fetch_one("SELECT * FROM users WHERE id = :id", {"id": 1})
    """
    params = params or {}
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, params)
            return cur.fetchone()


def execute(sql: str, params: Optional[Dict[str, Any]] = None) -> int:
    """
    INSERT, UPDATE, DELETE 쿼리 실행
    
    Args:
        sql: SQL 쿼리 문자열
        params: 바인딩 파라미터 딕셔너리
        
    Returns:
        영향을 받은 행 수
        
    사용 예시:
        rows = execute("INSERT INTO users (name, email) VALUES (:name, :email)",
                      {"name": "홍길동", "email": "test@example.com"})
    """
    params = params or {}
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, params)
            return cur.rowcount


def execute_many(sql: str, params_list: List[Dict[str, Any]]) -> int:
    """
    여러 개의 INSERT, UPDATE, DELETE 쿼리를 한 번에 실행 (배치 처리)
    
    Args:
        sql: SQL 쿼리 문자열
        params_list: 바인딩 파라미터 딕셔너리 리스트
        
    Returns:
        영향을 받은 총 행 수
        
    사용 예시:
        users = [
            {"name": "홍길동", "email": "hong@example.com"},
            {"name": "김철수", "email": "kim@example.com"},
        ]
        rows = execute_many("INSERT INTO users (name, email) VALUES (:name, :email)", users)
    """
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.executemany(sql, params_list)
            return cur.rowcount


def fetch_all_dict(sql: str, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
    """
    SELECT 쿼리 실행 후 모든 결과를 딕셔너리 리스트로 반환
    
    Args:
        sql: SQL 쿼리 문자열
        params: 바인딩 파라미터 딕셔너리
        
    Returns:
        딕셔너리 리스트 (각 행이 딕셔너리)
        
    사용 예시:
        users = fetch_all_dict("SELECT * FROM users")
        # [{"id": 1, "name": "홍길동", ...}, {"id": 2, "name": "김철수", ...}]
    """
    params = params or {}
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, params)
            columns = [desc[0] for desc in cur.description]
            results = cur.fetchall()
            return [dict(zip(columns, row)) for row in results]


def fetch_one_dict(sql: str, params: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
    """
    SELECT 쿼리 실행 후 첫 번째 결과를 딕셔너리로 반환
    
    Args:
        sql: SQL 쿼리 문자열
        params: 바인딩 파라미터 딕셔너리
        
    Returns:
        딕셔너리 또는 None
        
    사용 예시:
        user = fetch_one_dict("SELECT * FROM users WHERE id = :id", {"id": 1})
        # {"id": 1, "name": "홍길동", "email": "hong@example.com"}
    """
    params = params or {}
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, params)
            row = cur.fetchone()
            if row is None:
                return None
            columns = [desc[0] for desc in cur.description]
            return dict(zip(columns, row))

