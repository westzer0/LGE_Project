#!/usr/bin/env python
"""
마이그레이션 완료 여부 확인 스크립트
코드 수정 없이 Oracle DB에서 테이블 존재 여부만 확인
"""
import os
import sys
import django

# Django 설정
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from api.db.oracle_client import get_connection

def check_migration_status():
    """마이그레이션 완료 여부 확인"""
    print("=" * 60)
    print("마이그레이션 완료 여부 확인")
    print("=" * 60)
    print()
    
    # 확인할 테이블 목록
    required_tables = [
        'PORTFOLIO_SESSION',
        'SHARE_LINK',
        'PORTFOLIO_VERSION',
        'STYLE_MESSAGE',
        'ONBOARD_SESS_MAIN_SPACES',
        'ONBOARD_SESS_PRIORITIES',
        'ONBOARD_SESS_CATEGORIES',
        'ONBOARD_SESS_REC_PRODUCTS',
    ]
    
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                # 테이블 존재 여부 확인
                print("📋 테이블 존재 여부 확인 중...")
                print()
                
                cur.execute("""
                    SELECT TABLE_NAME 
                    FROM USER_TABLES 
                    WHERE TABLE_NAME IN (
                        'PORTFOLIO_SESSION',
                        'SHARE_LINK',
                        'PORTFOLIO_VERSION',
                        'STYLE_MESSAGE',
                        'ONBOARD_SESS_MAIN_SPACES',
                        'ONBOARD_SESS_PRIORITIES',
                        'ONBOARD_SESS_CATEGORIES',
                        'ONBOARD_SESS_REC_PRODUCTS'
                    )
                    ORDER BY TABLE_NAME
                """)
                
                existing_tables = [row[0] for row in cur.fetchall()]
                
                # 결과 출력
                print("✅ 존재하는 테이블:")
                for table in required_tables:
                    if table in existing_tables:
                        print(f"   ✓ {table}")
                    else:
                        print(f"   ✗ {table} (없음)")
                
                print()
                
                # 마이그레이션 완료 여부 판단
                critical_tables = ['PORTFOLIO_SESSION', 'SHARE_LINK', 'PORTFOLIO_VERSION']
                missing_critical = [t for t in critical_tables if t not in existing_tables]
                
                if missing_critical:
                    print("=" * 60)
                    print("⚠️  마이그레이션이 완료되지 않았습니다!")
                    print("=" * 60)
                    print(f"누락된 중요 테이블: {', '.join(missing_critical)}")
                    print()
                    print("마이그레이션 실행 방법:")
                    print("  python execute_migration.py")
                    return False
                else:
                    print("=" * 60)
                    print("✅ 마이그레이션이 완료되었습니다!")
                    print("=" * 60)
                    
                    # 추가 정보: 테이블 구조 확인
                    print()
                    print("📊 테이블 상세 정보:")
                    print()
                    
                    for table in critical_tables:
                        if table in existing_tables:
                            try:
                                cur.execute(f"""
                                    SELECT COLUMN_NAME, DATA_TYPE, NULLABLE
                                    FROM USER_TAB_COLUMNS
                                    WHERE TABLE_NAME = '{table}'
                                    ORDER BY COLUMN_ID
                                """)
                                columns = cur.fetchall()
                                
                                print(f"  [{table}]")
                                for col_name, data_type, nullable in columns:
                                    null_str = "NULL" if nullable == 'Y' else "NOT NULL"
                                    print(f"    - {col_name}: {data_type} ({null_str})")
                                print()
                            except Exception as e:
                                print(f"  [{table}] 구조 확인 실패: {e}")
                    
                    return True
                
    except Exception as e:
        print(f"❌ 데이터베이스 연결 실패: {e}")
        print()
        print("확인 사항:")
        print("  1. Oracle DB 연결 정보가 .env 파일에 설정되어 있는지 확인")
        print("  2. 데이터베이스 서버가 실행 중인지 확인")
        return False

if __name__ == '__main__':
    try:
        success = check_migration_status()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n❌ 사용자가 중단했습니다.")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ 예상치 못한 오류: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

