#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""정규화 테이블 생성 스크립트"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

import django
django.setup()

from api.db.oracle_client import get_connection

def create_normalized_tables():
    """정규화 테이블 생성"""
    print("=" * 80)
    print("정규화 테이블 생성 시작")
    print("=" * 80)
    
    with get_connection() as conn:
        with conn.cursor() as cur:
            # ONBOARD_SESS_MAIN_SPACES 테이블 생성
            print("\n[1] ONBOARD_SESS_MAIN_SPACES 테이블 생성...")
            try:
                cur.execute("""
                    CREATE TABLE ONBOARD_SESS_MAIN_SPACES (
                        SESSION_ID VARCHAR2(100) NOT NULL,
                        MAIN_SPACE VARCHAR2(50) NOT NULL,
                        CREATED_AT DATE DEFAULT SYSDATE,
                        PRIMARY KEY (SESSION_ID, MAIN_SPACE),
                        CONSTRAINT FK_SESS_MAIN_SPACES 
                            FOREIGN KEY (SESSION_ID) REFERENCES ONBOARDING_SESSION(SESSION_ID) ON DELETE CASCADE
                    )
                """)
                print("  ✅ ONBOARD_SESS_MAIN_SPACES 테이블 생성 완료")
                
                cur.execute("CREATE INDEX IDX_SESS_MAIN_SP ON ONBOARD_SESS_MAIN_SPACES(SESSION_ID)")
                print("  ✅ 인덱스 생성 완료")
            except Exception as e:
                if 'ORA-00955' in str(e) or 'already exists' in str(e).lower():
                    print("  ⚠️ ONBOARD_SESS_MAIN_SPACES 테이블이 이미 존재합니다")
                else:
                    print(f"  ❌ 오류: {e}")
                    raise
            
            # ONBOARD_SESS_PRIORITIES 테이블 생성
            print("\n[2] ONBOARD_SESS_PRIORITIES 테이블 생성...")
            try:
                cur.execute("""
                    CREATE TABLE ONBOARD_SESS_PRIORITIES (
                        SESSION_ID VARCHAR2(100) NOT NULL,
                        PRIORITY VARCHAR2(20) NOT NULL,
                        PRIORITY_ORDER NUMBER NOT NULL,
                        CREATED_AT DATE DEFAULT SYSDATE,
                        PRIMARY KEY (SESSION_ID, PRIORITY_ORDER),
                        CONSTRAINT FK_SESS_PRIORITIES 
                            FOREIGN KEY (SESSION_ID) REFERENCES ONBOARDING_SESSION(SESSION_ID) ON DELETE CASCADE
                    )
                """)
                print("  ✅ ONBOARD_SESS_PRIORITIES 테이블 생성 완료")
                
                cur.execute("CREATE INDEX IDX_SESS_PRIORITIES ON ONBOARD_SESS_PRIORITIES(SESSION_ID)")
                print("  ✅ 인덱스 생성 완료")
            except Exception as e:
                if 'ORA-00955' in str(e) or 'already exists' in str(e).lower():
                    print("  ⚠️ ONBOARD_SESS_PRIORITIES 테이블이 이미 존재합니다")
                else:
                    print(f"  ❌ 오류: {e}")
                    raise
            
            conn.commit()
            print("\n" + "=" * 80)
            print("✅ 정규화 테이블 생성 완료!")
            print("=" * 80)

if __name__ == '__main__':
    try:
        create_normalized_tables()
    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        exit(1)

