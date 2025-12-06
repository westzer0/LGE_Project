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
load_dotenv(BASE_DIR / ".env")

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

ORACLE_USER = os.getenv("ORACLE_USER", "campus_24K_LG3_DX7_p3_4")
ORACLE_PASSWORD = os.getenv("ORACLE_PASSWORD", "smhrd4")
ORACLE_HOST = os.getenv("ORACLE_HOST", "project-db-campus.smhrd.com")
ORACLE_PORT = int(os.getenv("ORACLE_PORT", "1524"))
ORACLE_SID = "xe"

DSN = oracledb.makedsn(ORACLE_HOST, ORACLE_PORT, sid=ORACLE_SID)


def get_connection():
    """새 Oracle 연결 생성."""
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
