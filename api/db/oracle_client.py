#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Oracle 11g (XE, SID=xe) 에 Thick 모드로 직접 붙는 전용 클라이언트 모듈.
Django ORM 은 사용하지 않고, 이 모듈에서만 oracledb 로 쿼리를 실행한다.
"""

import os
from pathlib import Path

import oracledb
from dotenv import load_dotenv

# 프로젝트 루트 기준 .env 로드
BASE_DIR = Path(__file__).resolve().parent.parent.parent
env_path = BASE_DIR / ".env"
if env_path.exists():
    try:
        # UTF-8로 시도
        with open(env_path, 'r', encoding='utf-8') as f:
            from dotenv import dotenv_values
            env_vars = dotenv_values(stream=f)
            for key, value in env_vars.items():
                if value is not None:
                    os.environ.setdefault(key, value)
    except UnicodeDecodeError:
        # UTF-8 실패 시 CP949 (Windows 기본 인코딩)로 시도
        try:
            with open(env_path, 'r', encoding='cp949') as f:
                from dotenv import dotenv_values
                env_vars = dotenv_values(stream=f)
                for key, value in env_vars.items():
                    if value is not None:
                        os.environ.setdefault(key, value)
        except Exception as e:
            print(f"[WARNING] .env 파일 로드 실패 (CP949): {e}")
    except Exception as e:
        print(f"[WARNING] .env 파일 로드 실패: {e}")

# Thick 모드 초기화 (oracle_init.py의 초기화 함수 사용)
# Oracle 11g는 thin mode를 지원하지 않으므로 Thick mode 필수
_thick_mode_initialized = False

# oracle_init.py의 초기화 함수 사용 (manage.py에서 이미 호출했을 수 있음)
try:
    from oracle_init import init_oracle_client
    init_oracle_client()
    _thick_mode_initialized = True
except ImportError:
    # oracle_init.py가 없으면 직접 초기화 시도
    try:
        oracledb.init_oracle_client()
        _thick_mode_initialized = True
        print("[Oracle] Thick 모드 초기화 완료 (직접)")
    except Exception as e:
        error_msg = str(e).lower()
        if "already initialized" in error_msg:
            _thick_mode_initialized = True
            print("[Oracle] Thick 모드 이미 초기화됨")
        else:
            print(f"[Oracle Warning] Thick 모드 초기화 실패: {e}")
            print("  Oracle 11g는 thin mode를 지원하지 않습니다.")
            print("  Oracle Instant Client를 설치하고 PATH에 추가하거나")
            print("  ORACLE_INSTANT_CLIENT_PATH 환경변수를 설정하세요.")
except Exception as e:
    error_msg = str(e).lower()
    if "already initialized" in error_msg:
        _thick_mode_initialized = True
        print("[Oracle] Thick 모드 이미 초기화됨")
    else:
        print(f"[Oracle Warning] Thick 모드 초기화 실패: {e}")
        print("  Oracle 11g는 thin mode를 지원하지 않습니다.")
        print("  Oracle Instant Client를 설치하고 PATH에 추가하거나")
        print("  ORACLE_INSTANT_CLIENT_PATH 환경변수를 설정하세요.")

# DISABLE_DB 환경 변수 확인 (먼저 확인)
DISABLE_DB = os.getenv("DISABLE_DB", "false").lower() == "true"

# PRD 개선: 환경 변수 필수 설정 (보안 강화)
ORACLE_USER = os.getenv("ORACLE_USER")
ORACLE_PASSWORD = os.getenv("ORACLE_PASSWORD")
ORACLE_HOST = os.getenv("ORACLE_HOST")
ORACLE_PORT = int(os.getenv("ORACLE_PORT", "1521"))
ORACLE_SID = os.getenv("ORACLE_SID", "xe")

# 개발 환경에서만 기본값 허용 (DISABLE_DB가 아닌 경우)
if not DISABLE_DB:
    if not ORACLE_USER:
        # 개발 환경 기본값 (프로덕션에서는 환경 변수 필수)
        ORACLE_USER = os.getenv("ORACLE_USER", "campus_24K_LG3_DX7_p3_4")
        ORACLE_PASSWORD = os.getenv("ORACLE_PASSWORD", "smhrd4")
        ORACLE_HOST = os.getenv("ORACLE_HOST", "project-db-campus.smhrd.com")
        ORACLE_PORT = int(os.getenv("ORACLE_PORT", "1524"))
        print("[WARNING] Oracle DB 기본값 사용 중 (개발 환경). 프로덕션에서는 환경 변수를 설정하세요.")
    elif not all([ORACLE_USER, ORACLE_PASSWORD, ORACLE_HOST]):
        raise ValueError(
            "Oracle DB 환경 변수가 설정되지 않았습니다. "
            "ORACLE_USER, ORACLE_PASSWORD, ORACLE_HOST를 설정하거나 "
            "DISABLE_DB=true로 설정하세요."
        )
    # DSN은 DISABLE_DB가 false일 때만 생성
    DSN = oracledb.makedsn(ORACLE_HOST, ORACLE_PORT, sid=ORACLE_SID)
else:
    # DISABLE_DB가 true일 때는 DSN을 None으로 설정
    DSN = None


class DatabaseDisabledError(Exception):
    """DB가 비활성화된 상태에서 DB 접근을 시도할 때 발생하는 예외"""
    pass


def get_connection():
    """새 Oracle 연결 생성."""
    # DISABLE_DB가 설정되어 있으면 예외 발생
    if DISABLE_DB:
        raise DatabaseDisabledError(
            "데이터베이스 연결이 비활성화되었습니다. (DISABLE_DB=true) "
            "DB를 사용하는 기능은 작동하지 않습니다."
        )
    
    if not _thick_mode_initialized:
        raise RuntimeError(
            "Oracle Thick mode가 초기화되지 않았습니다. "
            "Oracle 11g는 thin mode를 지원하지 않으므로 "
            "Oracle Instant Client를 설치하고 초기화해야 합니다."
        )
    return oracledb.connect(
        user=ORACLE_USER,
        password=ORACLE_PASSWORD,
        dsn=DSN,
    )


def fetch_all(sql, params=None):
    """모든 행을 튜플 리스트로 반환."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, params or {})
            return cur.fetchall()


def fetch_all_dict(sql, params=None):
    """각 행을 dict 로 변환해 리스트로 반환."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, params or {})
            cols = [c[0] for c in cur.description]
            return [dict(zip(cols, row)) for row in cur]


def fetch_one(sql, params=None):
    """단일 행 반환 (없으면 None)."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, params or {})
            return cur.fetchone()
