#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Step 1: Taste 계산 및 할당 기본 인프라 검증

검증 항목:
1. Oracle DB 연결 확인
2. 필요한 테이블 존재 여부 확인
3. MEMBER.TASTE 컬럼 확인
4. 제약조건 확인
"""
import sys
import os

# Django 설정 로드
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

import django
django.setup()

from api.db.oracle_client import get_connection


class TasteInfrastructureValidator:
    """Taste 계산 인프라 검증 클래스"""
    
    def __init__(self):
        self.results = {
            'db_connection': False,
            'tables': {},
            'columns': {},
            'constraints': {},
            'errors': []
        }
    
    def validate_all(self):
        """모든 검증 실행"""
        print("=" * 80)
        print("Step 1: Taste 계산 및 할당 기본 인프라 검증")
        print("=" * 80)
        print()
        
        try:
            # 1. DB 연결 확인
            self._validate_db_connection()
            
            # 2. 테이블 존재 여부 확인
            self._validate_tables()
            
            # 3. 컬럼 존재 여부 확인
            self._validate_columns()
            
            # 4. 제약조건 확인
            self._validate_constraints()
            
            # 5. 결과 출력
            self._print_results()
            
        except Exception as e:
            print(f"\n❌ 검증 중 예외 발생: {e}")
            import traceback
            traceback.print_exc()
            return False
        
        return self._is_all_passed()
    
    def _validate_db_connection(self):
        """DB 연결 확인"""
        print("[1] Oracle DB 연결 확인...")
        try:
            with get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT 1 FROM DUAL")
                    result = cur.fetchone()
                    if result:
                        self.results['db_connection'] = True
                        print("  ✅ DB 연결 성공")
                    else:
                        self.results['errors'].append("DB 연결은 되었지만 쿼리 결과가 없습니다")
                        print("  ⚠️ DB 연결은 되었지만 쿼리 결과가 없습니다")
        except Exception as e:
            self.results['errors'].append(f"DB 연결 실패: {str(e)}")
            print(f"  ❌ DB 연결 실패: {e}")
        print()
    
    def _validate_tables(self):
        """필요한 테이블 존재 여부 확인"""
        print("[2] 테이블 존재 여부 확인...")
        
        required_tables = [
            'ONBOARDING_SESSION',
            'ONBOARD_SESS_MAIN_SPACES',
            'ONBOARD_SESS_PRIORITIES',
            'MEMBER'
        ]
        
        try:
            with get_connection() as conn:
                with conn.cursor() as cur:
                    for table_name in required_tables:
                        exists = self._table_exists(cur, table_name)
                        self.results['tables'][table_name] = exists
                        
                        if exists:
                            print(f"  ✅ {table_name} 테이블 존재")
                        else:
                            print(f"  ❌ {table_name} 테이블 없음")
                            self.results['errors'].append(f"{table_name} 테이블이 존재하지 않습니다")
        except Exception as e:
            self.results['errors'].append(f"테이블 확인 중 오류: {str(e)}")
            print(f"  ❌ 테이블 확인 중 오류: {e}")
        print()
    
    def _validate_columns(self):
        """필요한 컬럼 존재 여부 확인"""
        print("[3] 컬럼 존재 여부 확인...")
        
        # ONBOARDING_SESSION 테이블 컬럼
        onboarding_columns = [
            'SESSION_ID', 'MEMBER_ID', 'STATUS',
            'VIBE', 'HOUSEHOLD_SIZE', 'HOUSING_TYPE', 'PYUNG',
            'BUDGET_LEVEL', 'PRIORITY', 'HAS_PET',
            'COOKING', 'LAUNDRY', 'MEDIA'
        ]
        
        # MEMBER 테이블 컬럼
        member_columns = ['MEMBER_ID', 'TASTE']
        
        try:
            with get_connection() as conn:
                with conn.cursor() as cur:
                    # ONBOARDING_SESSION 컬럼 확인
                    print("  [ONBOARDING_SESSION 테이블]")
                    for col_name in onboarding_columns:
                        exists = self._column_exists(cur, 'ONBOARDING_SESSION', col_name)
                        self.results['columns'][f'ONBOARDING_SESSION.{col_name}'] = exists
                        
                        if exists:
                            print(f"    ✅ {col_name}")
                        else:
                            print(f"    ❌ {col_name} 없음")
                            self.results['errors'].append(f"ONBOARDING_SESSION.{col_name} 컬럼이 없습니다")
                    
                    # MEMBER 컬럼 확인
                    print("  [MEMBER 테이블]")
                    for col_name in member_columns:
                        exists = self._column_exists(cur, 'MEMBER', col_name)
                        self.results['columns'][f'MEMBER.{col_name}'] = exists
                        
                        if exists:
                            print(f"    ✅ {col_name}")
                            
                            # TASTE 컬럼의 경우 타입도 확인
                            if col_name == 'TASTE':
                                data_type = self._get_column_type(cur, 'MEMBER', 'TASTE')
                                print(f"      타입: {data_type}")
                                self.results['columns']['MEMBER.TASTE_TYPE'] = data_type
                        else:
                            print(f"    ❌ {col_name} 없음")
                            self.results['errors'].append(f"MEMBER.{col_name} 컬럼이 없습니다")
        except Exception as e:
            self.results['errors'].append(f"컬럼 확인 중 오류: {str(e)}")
            print(f"  ❌ 컬럼 확인 중 오류: {e}")
        print()
    
    def _validate_constraints(self):
        """제약조건 확인"""
        print("[4] 제약조건 확인...")
        
        try:
            with get_connection() as conn:
                with conn.cursor() as cur:
                    # MEMBER.TASTE 범위 제약조건 확인
                    constraint_exists = self._check_taste_constraint(cur)
                    self.results['constraints']['MEMBER.TASTE_RANGE'] = constraint_exists
                    
                    if constraint_exists:
                        print("  ✅ MEMBER.TASTE 범위 제약조건 존재 (1~120)")
                    else:
                        print("  ⚠️ MEMBER.TASTE 범위 제약조건 없음 (애플리케이션 레벨에서 검증 필요)")
                    
                    # FK 제약조건 확인
                    fk_exists = self._check_fk_constraint(cur, 'ONBOARDING_SESSION', 'MEMBER_ID', 'MEMBER', 'MEMBER_ID')
                    self.results['constraints']['ONBOARDING_SESSION.MEMBER_ID_FK'] = fk_exists
                    
                    if fk_exists:
                        print("  ✅ ONBOARDING_SESSION.MEMBER_ID → MEMBER.MEMBER_ID FK 존재")
                    else:
                        print("  ⚠️ ONBOARDING_SESSION.MEMBER_ID FK 없음")
        except Exception as e:
            self.results['errors'].append(f"제약조건 확인 중 오류: {str(e)}")
            print(f"  ❌ 제약조건 확인 중 오류: {e}")
        print()
    
    def _table_exists(self, cur, table_name):
        """테이블 존재 여부 확인"""
        try:
            cur.execute("""
                SELECT COUNT(*) 
                FROM USER_TABLES 
                WHERE TABLE_NAME = :table_name
            """, {'table_name': table_name})
            return cur.fetchone()[0] > 0
        except:
            return False
    
    def _column_exists(self, cur, table_name, column_name):
        """컬럼 존재 여부 확인"""
        try:
            cur.execute("""
                SELECT COUNT(*) 
                FROM USER_TAB_COLUMNS 
                WHERE TABLE_NAME = :table_name 
                  AND COLUMN_NAME = :column_name
            """, {
                'table_name': table_name,
                'column_name': column_name
            })
            return cur.fetchone()[0] > 0
        except:
            return False
    
    def _get_column_type(self, cur, table_name, column_name):
        """컬럼 타입 확인"""
        try:
            cur.execute("""
                SELECT DATA_TYPE, DATA_PRECISION, DATA_SCALE
                FROM USER_TAB_COLUMNS 
                WHERE TABLE_NAME = :table_name 
                  AND COLUMN_NAME = :column_name
            """, {
                'table_name': table_name,
                'column_name': column_name
            })
            result = cur.fetchone()
            if result:
                data_type, precision, scale = result
                if precision:
                    return f"{data_type}({precision}{f',{scale}' if scale else ''})"
                return data_type
            return None
        except:
            return None
    
    def _check_taste_constraint(self, cur):
        """MEMBER.TASTE 범위 제약조건 확인"""
        try:
            cur.execute("""
                SELECT COUNT(*) 
                FROM USER_CONSTRAINTS 
                WHERE TABLE_NAME = 'MEMBER' 
                  AND CONSTRAINT_NAME LIKE '%TASTE%'
                  AND CONSTRAINT_TYPE = 'C'
            """)
            return cur.fetchone()[0] > 0
        except:
            return False
    
    def _check_fk_constraint(self, cur, table_name, column_name, ref_table, ref_column):
        """FK 제약조건 확인"""
        try:
            cur.execute("""
                SELECT COUNT(*) 
                FROM USER_CONSTRAINTS c
                JOIN USER_CONS_COLUMNS cc ON c.CONSTRAINT_NAME = cc.CONSTRAINT_NAME
                WHERE c.TABLE_NAME = :table_name
                  AND cc.COLUMN_NAME = :column_name
                  AND c.CONSTRAINT_TYPE = 'R'
                  AND c.R_TABLE_NAME = :ref_table
            """, {
                'table_name': table_name,
                'column_name': column_name,
                'ref_table': ref_table
            })
            return cur.fetchone()[0] > 0
        except:
            return False
    
    def _print_results(self):
        """검증 결과 출력"""
        print("=" * 80)
        print("검증 결과 요약")
        print("=" * 80)
        
        # DB 연결
        if self.results['db_connection']:
            print("✅ DB 연결: 성공")
        else:
            print("❌ DB 연결: 실패")
        
        # 테이블
        print("\n[테이블]")
        all_tables_exist = True
        for table_name, exists in self.results['tables'].items():
            status = "✅" if exists else "❌"
            print(f"  {status} {table_name}")
            if not exists:
                all_tables_exist = False
        
        # 컬럼 (주요 컬럼만)
        print("\n[주요 컬럼]")
        key_columns = [
            'ONBOARDING_SESSION.SESSION_ID',
            'ONBOARDING_SESSION.MEMBER_ID',
            'ONBOARDING_SESSION.STATUS',
            'MEMBER.MEMBER_ID',
            'MEMBER.TASTE'
        ]
        all_columns_exist = True
        for col_key in key_columns:
            exists = self.results['columns'].get(col_key, False)
            status = "✅" if exists else "❌"
            print(f"  {status} {col_key}")
            if not exists:
                all_columns_exist = False
        
        # TASTE 타입
        if 'MEMBER.TASTE_TYPE' in self.results['columns']:
            taste_type = self.results['columns']['MEMBER.TASTE_TYPE']
            print(f"    타입: {taste_type}")
            if taste_type and 'NUMBER' in taste_type.upper():
                print("    ✅ TASTE 컬럼 타입이 NUMBER입니다")
            else:
                print("    ⚠️ TASTE 컬럼 타입이 NUMBER가 아닙니다")
        
        # 제약조건
        print("\n[제약조건]")
        for constraint_name, exists in self.results['constraints'].items():
            status = "✅" if exists else "⚠️"
            print(f"  {status} {constraint_name}")
        
        # 에러
        if self.results['errors']:
            print("\n[에러]")
            for error in self.results['errors']:
                print(f"  ❌ {error}")
        
        print()
    
    def _is_all_passed(self):
        """모든 검증 통과 여부"""
        # 필수 항목 체크
        if not self.results['db_connection']:
            return False
        
        required_tables = ['ONBOARDING_SESSION', 'MEMBER']
        for table_name in required_tables:
            if not self.results['tables'].get(table_name, False):
                return False
        
        required_columns = [
            'ONBOARDING_SESSION.SESSION_ID',
            'ONBOARDING_SESSION.MEMBER_ID',
            'ONBOARDING_SESSION.STATUS',
            'MEMBER.MEMBER_ID',
            'MEMBER.TASTE'
        ]
        for col_key in required_columns:
            if not self.results['columns'].get(col_key, False):
                return False
        
        return True


def main():
    """메인 함수"""
    validator = TasteInfrastructureValidator()
    success = validator.validate_all()
    
    if success:
        print("=" * 80)
        print("✅ Step 1 검증 완료: 모든 필수 인프라가 준비되어 있습니다!")
        print("=" * 80)
        return 0
    else:
        print("=" * 80)
        print("❌ Step 1 검증 실패: 일부 인프라가 준비되지 않았습니다.")
        print("=" * 80)
        return 1


if __name__ == '__main__':
    exit(main())

