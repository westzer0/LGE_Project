"""
Django Oracle 백엔드 커스터마이징
Oracle 11g 지원을 위해 버전 체크 우회
"""
from django.db.backends.oracle.base import DatabaseWrapper as OracleDatabaseWrapper


class DatabaseWrapper(OracleDatabaseWrapper):
    """
    Oracle 11g 지원을 위한 커스텀 백엔드
    Django 5.2의 버전 체크를 우회하여 Oracle 11g 사용
    """
    
    def check_database_version_supported(self):
        """버전 체크 우회 - Oracle 11g 허용"""
        # 버전 체크를 건너뛰고 항상 통과
        pass
