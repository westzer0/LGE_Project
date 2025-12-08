"""누락된 컬럼 추가"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from api.db.oracle_client import get_connection

missing_columns = [
    '"정수기_SCORE" NUMBER(5,2)',
    'TV_SCORE NUMBER(5,2)',  # 확인
    'AIHOME_SCORE NUMBER(5,2)',  # 확인
]

try:
    with get_connection() as conn:
        with conn.cursor() as cur:
            for col_def in missing_columns:
                try:
                    print(f'추가 중: {col_def[:30]}...', end=' ')
                    cur.execute(f'ALTER TABLE TASTE_CONFIG ADD {col_def}')
                    conn.commit()
                    print('✓ 완료')
                except Exception as e:
                    if 'ORA-01430' in str(e):
                        print('건너뜀 (이미 존재)')
                    else:
                        print(f'오류: {str(e)[:50]}')
                        
    print('\n=== 완료 ===')
except Exception as e:
    print(f'오류 발생: {str(e)}')



