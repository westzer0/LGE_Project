"""
Oracle 직접 연결 모듈
Django ORM을 사용하지 않고 oracledb를 직접 사용하여 Oracle 11g에 연결
"""
from .oracle_client import (
    get_connection,
    fetch_all,
    fetch_one,
    fetch_all_dict,
)

__all__ = [
    'get_connection',
    'fetch_all',
    'fetch_one',
    'fetch_all_dict',
]

