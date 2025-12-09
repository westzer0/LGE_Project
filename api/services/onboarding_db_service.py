"""
온보딩 데이터를 Oracle DB에 저장하는 서비스
"""
import json
import uuid
from datetime import datetime
from api.db.oracle_client import get_connection, fetch_all_dict, fetch_one


class OnboardingDBService:
    """온보딩 데이터를 Oracle DB에 저장/조회하는 서비스"""
    
    _member_id_nullable_checked = False
    _guest_member_checked = False
    _table_columns_checked = False
    _session_id_type_checked = False
    
    @staticmethod
    def _ensure_member_id_default_guest(conn, cur):
        """MEMBER_ID 컬럼이 NOT NULL이고 기본값 'GUEST'인지 확인하고, 필요시 수정"""
        if OnboardingDBService._member_id_nullable_checked:
            return
        
        try:
            # MEMBER_ID 컬럼의 NULL 허용 여부 및 기본값 확인
            cur.execute("""
                SELECT NULLABLE, DATA_DEFAULT
                FROM USER_TAB_COLUMNS
                WHERE TABLE_NAME = 'ONBOARDING_SESSION'
                  AND COLUMN_NAME = 'MEMBER_ID'
            """)
            result = cur.fetchone()
            
            if result:
                nullable = result[0]
                data_default = result[1] if result[1] else ''
                
                # NULL 허용이거나 기본값이 'GUEST'가 아니면 수정
                needs_update = False
                if nullable == 'Y':
                    needs_update = True
                    print(f"[OnboardingDBService] MEMBER_ID를 NOT NULL로 변경하고 기본값 'GUEST' 설정 중...", flush=True)
                elif "'GUEST'" not in data_default.upper() and "GUEST" not in data_default.upper():
                    needs_update = True
                    print(f"[OnboardingDBService] MEMBER_ID 기본값을 'GUEST'로 설정 중...", flush=True)
                
                if needs_update:
                    # 먼저 기존 NULL 값을 'GUEST'로 업데이트
                    cur.execute("""
                        UPDATE ONBOARDING_SESSION 
                        SET MEMBER_ID = 'GUEST' 
                        WHERE MEMBER_ID IS NULL
                    """)
                    updated_count = cur.rowcount
                    if updated_count > 0:
                        print(f"[OnboardingDBService] {updated_count}개의 NULL MEMBER_ID를 'GUEST'로 업데이트했습니다.", flush=True)
                    
                    # NOT NULL 및 기본값 설정
                    cur.execute("ALTER TABLE ONBOARDING_SESSION MODIFY MEMBER_ID VARCHAR2(30) DEFAULT 'GUEST' NOT NULL")
                    conn.commit()
                    print(f"[OnboardingDBService] ✅ MEMBER_ID가 NOT NULL이고 기본값 'GUEST'로 설정되었습니다.", flush=True)
                else:
                    print(f"[OnboardingDBService] ✅ MEMBER_ID는 이미 NOT NULL이고 기본값이 설정되어 있습니다.", flush=True)
            else:
                print(f"[OnboardingDBService] ⚠️ MEMBER_ID 컬럼을 찾을 수 없습니다.", flush=True)
            
            OnboardingDBService._member_id_nullable_checked = True
        except Exception as e:
            print(f"[OnboardingDBService] ⚠️ MEMBER_ID 기본값 설정 중 오류: {e}", flush=True)
            # 오류가 발생해도 계속 진행
    
    @staticmethod
    def _ensure_session_id_type(conn, cur):
        """SESSION_ID 컬럼이 VARCHAR2 타입인지 확인하고, NUMBER면 VARCHAR2로 변경"""
        if OnboardingDBService._session_id_type_checked:
            return
        
        try:
            # SESSION_ID 컬럼 타입 확인
            cur.execute("""
                SELECT DATA_TYPE, DATA_LENGTH
                FROM USER_TAB_COLUMNS
                WHERE TABLE_NAME = 'ONBOARDING_SESSION' AND COLUMN_NAME = 'SESSION_ID'
            """)
            result = cur.fetchone()
            
            if result:
                data_type, data_length = result
                if data_type == 'NUMBER':
                    print(f"[OnboardingDBService] ⚠️ SESSION_ID가 NUMBER 타입입니다. VARCHAR2(100)로 변경 중...", flush=True)
                    
                    # SESSION_ID_NEW 컬럼이 이미 존재하는지 확인 (이전 마이그레이션 실패 시)
                    cur.execute("""
                        SELECT COUNT(*) 
                        FROM USER_TAB_COLUMNS 
                        WHERE TABLE_NAME = 'ONBOARDING_SESSION' AND COLUMN_NAME = 'SESSION_ID_NEW'
                    """)
                    temp_column_exists = cur.fetchone()[0] > 0
                    
                    try:
                        if not temp_column_exists:
                            # 임시 컬럼 추가
                            cur.execute("ALTER TABLE ONBOARDING_SESSION ADD SESSION_ID_NEW VARCHAR2(100)")
                            print(f"[OnboardingDBService] 임시 컬럼 SESSION_ID_NEW 추가 완료", flush=True)
                        else:
                            print(f"[OnboardingDBService] ⚠️ SESSION_ID_NEW 컬럼이 이미 존재합니다. 이전 마이그레이션을 완료합니다.", flush=True)
                        
                        # 기존 NUMBER 값을 문자열로 변환하여 복사 (아직 복사되지 않은 경우만)
                        cur.execute("""
                            UPDATE ONBOARDING_SESSION 
                            SET SESSION_ID_NEW = TO_CHAR(SESSION_ID)
                            WHERE SESSION_ID_NEW IS NULL AND SESSION_ID IS NOT NULL
                        """)
                        migrated_count = cur.rowcount
                        if migrated_count > 0:
                            print(f"[OnboardingDBService] {migrated_count}개 레코드 마이그레이션 완료", flush=True)
                        
                        # SESSION_ID 컬럼이 여전히 존재하는지 확인
                        cur.execute("""
                            SELECT COUNT(*) 
                            FROM USER_TAB_COLUMNS 
                            WHERE TABLE_NAME = 'ONBOARDING_SESSION' AND COLUMN_NAME = 'SESSION_ID'
                        """)
                        old_column_exists = cur.fetchone()[0] > 0
                        
                        if old_column_exists:
                            # 기존 컬럼 삭제 (PRIMARY KEY 제약조건이 있으면 먼저 삭제)
                            try:
                                # PRIMARY KEY 제약조건 확인 및 삭제
                                cur.execute("""
                                    SELECT CONSTRAINT_NAME 
                                    FROM USER_CONSTRAINTS 
                                    WHERE TABLE_NAME = 'ONBOARDING_SESSION' 
                                      AND CONSTRAINT_TYPE = 'P'
                                """)
                                pk_result = cur.fetchone()
                                if pk_result:
                                    pk_name = pk_result[0]
                                    cur.execute(f"ALTER TABLE ONBOARDING_SESSION DROP CONSTRAINT {pk_name}")
                                    print(f"[OnboardingDBService] 기존 PRIMARY KEY 제약조건 삭제 완료", flush=True)
                            except Exception as pk_drop_error:
                                print(f"[OnboardingDBService] ⚠️ PRIMARY KEY 제약조건 삭제 중 오류 (없을 수 있음): {pk_drop_error}", flush=True)
                            
                            # 기존 컬럼 삭제
                            cur.execute("ALTER TABLE ONBOARDING_SESSION DROP COLUMN SESSION_ID")
                            print(f"[OnboardingDBService] 기존 SESSION_ID 컬럼 삭제 완료", flush=True)
                        
                        # SESSION_ID_NEW가 아직 존재하는지 확인 (이름 변경 전)
                        cur.execute("""
                            SELECT COUNT(*) 
                            FROM USER_TAB_COLUMNS 
                            WHERE TABLE_NAME = 'ONBOARDING_SESSION' AND COLUMN_NAME = 'SESSION_ID_NEW'
                        """)
                        new_column_exists = cur.fetchone()[0] > 0
                        
                        if new_column_exists:
                            # 새 컬럼 이름 변경
                            cur.execute("ALTER TABLE ONBOARDING_SESSION RENAME COLUMN SESSION_ID_NEW TO SESSION_ID")
                            print(f"[OnboardingDBService] SESSION_ID_NEW를 SESSION_ID로 변경 완료", flush=True)
                        
                        # PRIMARY KEY 재생성
                        try:
                            cur.execute("ALTER TABLE ONBOARDING_SESSION ADD CONSTRAINT PK_ONBOARDING_SESSION PRIMARY KEY (SESSION_ID)")
                            print(f"[OnboardingDBService] PRIMARY KEY 재생성 완료", flush=True)
                        except Exception as pk_error:
                            print(f"[OnboardingDBService] ⚠️ PRIMARY KEY 재생성 중 오류 (이미 존재할 수 있음): {pk_error}", flush=True)
                        
                        conn.commit()
                        print(f"[OnboardingDBService] ✅ SESSION_ID가 VARCHAR2(100)로 변경되었습니다.", flush=True)
                    except Exception as alter_error:
                        error_msg = str(alter_error)
                        print(f"[OnboardingDBService] ⚠️ SESSION_ID 타입 변경 중 오류: {alter_error}", flush=True)
                        conn.rollback()
                        # 오류가 발생해도 플래그를 설정하여 무한 반복 방지
                        OnboardingDBService._session_id_type_checked = True
                        return
                elif data_type == 'VARCHAR2':
                    print(f"[OnboardingDBService] ✅ SESSION_ID는 이미 VARCHAR2({data_length}) 타입입니다.", flush=True)
                else:
                    print(f"[OnboardingDBService] ⚠️ SESSION_ID 타입: {data_type} (예상: VARCHAR2)", flush=True)
            else:
                print(f"[OnboardingDBService] ⚠️ SESSION_ID 컬럼을 찾을 수 없습니다.", flush=True)
            
            OnboardingDBService._session_id_type_checked = True
        except Exception as e:
            print(f"[OnboardingDBService] ⚠️ SESSION_ID 타입 확인 중 오류: {e}", flush=True)
            # 오류가 발생해도 플래그를 설정하여 무한 반복 방지
            OnboardingDBService._session_id_type_checked = True
    
    @staticmethod
    def _ensure_table_columns_exist(conn, cur):
        """ONBOARDING_SESSION 테이블에 필요한 컬럼들이 존재하는지 확인하고, 없으면 추가"""
        if OnboardingDBService._table_columns_checked:
            return
        
        try:
            # 필요한 컬럼 목록 (컬럼명, 타입, 기본값)
            required_columns = [
                ('CURRENT_STEP', 'NUMBER', 'DEFAULT 1'),
                ('STATUS', 'VARCHAR2(20)', "DEFAULT 'IN_PROGRESS'"),
                ('VIBE', 'VARCHAR2(20)', None),
                ('HOUSEHOLD_SIZE', 'NUMBER', None),
                ('HAS_PET', 'CHAR(1)', None),
                ('HOUSING_TYPE', 'VARCHAR2(20)', None),
                ('PYUNG', 'NUMBER', None),
                ('COOKING', 'VARCHAR2(20)', None),
                ('LAUNDRY', 'VARCHAR2(20)', None),
                ('MEDIA', 'VARCHAR2(20)', None),
                ('PRIORITY', 'VARCHAR2(20)', None),
                ('BUDGET_LEVEL', 'VARCHAR2(20)', None),
                ('COMPLETED_AT', 'DATE', None),
                ('USER_ID', 'VARCHAR2(100)', None),
            ]
            
            # 테이블 존재 여부 확인
            cur.execute("""
                SELECT COUNT(*) FROM USER_TABLES WHERE TABLE_NAME = 'ONBOARDING_SESSION'
            """)
            table_exists = cur.fetchone()[0] > 0
            
            if not table_exists:
                print(f"[OnboardingDBService] ⚠️ ONBOARDING_SESSION 테이블이 존재하지 않습니다.", flush=True)
                return
            
            # 각 컬럼 존재 여부 확인 및 추가
            for column_name, column_type, default_value in required_columns:
                try:
                    cur.execute("""
                        SELECT COUNT(*) 
                        FROM USER_TAB_COLUMNS 
                        WHERE TABLE_NAME = 'ONBOARDING_SESSION' 
                          AND COLUMN_NAME = :column_name
                    """, {'column_name': column_name})
                    exists = cur.fetchone()[0] > 0
                    
                    if not exists:
                        # 컬럼 추가
                        alter_sql = f"ALTER TABLE ONBOARDING_SESSION ADD {column_name} {column_type}"
                        if default_value:
                            alter_sql += f" {default_value}"
                        
                        print(f"[OnboardingDBService] {column_name} 컬럼 추가 중...", flush=True)
                        cur.execute(alter_sql)
                        conn.commit()
                        print(f"[OnboardingDBService] ✅ {column_name} 컬럼이 추가되었습니다.", flush=True)
                    else:
                        print(f"[OnboardingDBService] ✅ {column_name} 컬럼이 이미 존재합니다.", flush=True)
                except Exception as col_error:
                    error_msg = str(col_error)
                    if 'ORA-01430' in error_msg or 'already exists' in error_msg.lower():
                        print(f"[OnboardingDBService] ✅ {column_name} 컬럼이 이미 존재합니다.", flush=True)
                    else:
                        print(f"[OnboardingDBService] ⚠️ {column_name} 컬럼 추가 중 오류: {col_error}", flush=True)
            
            OnboardingDBService._table_columns_checked = True
        except Exception as e:
            print(f"[OnboardingDBService] ⚠️ 테이블 컬럼 확인 중 오류: {e}", flush=True)
            # 오류가 발생해도 계속 진행
    
    @staticmethod
    def _ensure_guest_member_exists(conn, cur):
        """GUEST 레코드가 MEMBER 테이블에 존재하는지 확인하고, 없으면 생성"""
        if OnboardingDBService._guest_member_checked:
            return
        
        try:
            # GUEST 레코드 존재 여부 확인
            cur.execute("SELECT COUNT(*) FROM MEMBER WHERE MEMBER_ID = 'GUEST'")
            exists = cur.fetchone()[0] > 0
            
            if not exists:
                print(f"[OnboardingDBService] GUEST 레코드가 없습니다. 생성 중...", flush=True)
                
                # MEMBER 테이블의 필수 컬럼 확인
                cur.execute("""
                    SELECT COLUMN_NAME, NULLABLE, DATA_DEFAULT
                    FROM USER_TAB_COLUMNS
                    WHERE TABLE_NAME = 'MEMBER'
                    ORDER BY COLUMN_ID
                """)
                columns = cur.fetchall()
                
                # MEMBER_ID 타입 확인
                cur.execute("""
                    SELECT DATA_TYPE, DATA_LENGTH
                    FROM USER_TAB_COLUMNS
                    WHERE TABLE_NAME = 'MEMBER' AND COLUMN_NAME = 'MEMBER_ID'
                """)
                member_id_info = cur.fetchone()
                
                if member_id_info:
                    data_type, data_length = member_id_info
                    
                    # MEMBER_ID가 VARCHAR2인 경우에만 GUEST 생성
                    if 'VARCHAR' in data_type.upper():
                        # 최소한의 필수 컬럼만으로 GUEST 생성
                        cur.execute("""
                            INSERT INTO MEMBER (MEMBER_ID, CREATED_DATE, CREATED_AT) 
                            VALUES ('GUEST', SYSDATE, SYSDATE)
                        """)
                        conn.commit()
                        print(f"[OnboardingDBService] ✅ GUEST 레코드가 생성되었습니다.", flush=True)
                    else:
                        print(f"[OnboardingDBService] ⚠️ MEMBER_ID가 NUMBER 타입입니다. GUEST를 생성할 수 없습니다.", flush=True)
                else:
                    print(f"[OnboardingDBService] ⚠️ MEMBER_ID 컬럼 정보를 찾을 수 없습니다.", flush=True)
            else:
                print(f"[OnboardingDBService] ✅ GUEST 레코드가 이미 존재합니다.", flush=True)
            
            OnboardingDBService._guest_member_checked = True
        except Exception as e:
            print(f"[OnboardingDBService] ⚠️ GUEST 레코드 확인/생성 중 오류: {e}", flush=True)
            # 오류가 발생해도 계속 진행 (NULL로 처리 가능)
    
    @staticmethod
    def _convert_to_numeric(value):
        """
        값을 Oracle NUMBER 타입으로 변환
        - None → None (NULL 허용)
        - 빈 문자열 → None
        - 숫자 문자열 → int/float
        - 이미 숫자 → 그대로 반환
        - 변환 불가능한 값 → None (안전하게 처리)
        """
        if value is None:
            return None
        if isinstance(value, (int, float)):
            return value
        if isinstance(value, str):
            value = value.strip()
            if value == '':
                return None
            try:
                # 정수로 변환 시도
                if '.' in value:
                    return float(value)
                else:
                    return int(value)
            except (ValueError, TypeError):
                print(f"[OnboardingDBService] ⚠️ 숫자 변환 실패: '{value}' → None으로 설정", flush=True)
                return None
        # 기타 타입은 None으로 처리
        print(f"[OnboardingDBService] ⚠️ 예상치 못한 타입: {type(value).__name__} ('{value}') → None으로 설정", flush=True)
        return None
    
    @staticmethod
    def create_or_update_session(session_id=None, user_id=None, member_id=None, current_step=1, status='IN_PROGRESS', **kwargs):
        """
        온보딩 세션 생성 또는 업데이트 (수정 버전)
        
        Args:
            session_id: 세션 ID (UUID 문자열, 없으면 자동 생성)
            user_id: 사용자 ID (선택적, 제거됨)
            member_id: 회원 ID (선택적, 기본값 'GUEST')
            current_step: 현재 단계
            status: 상태 (IN_PROGRESS, COMPLETED, ABANDONED)
            **kwargs: 추가 필드 (vibe, household_size, housing_type, pyung, priority, budget_level 등)
        """
        print(f"\n[create_or_update_session] 함수 진입 - session_id={session_id}, step={current_step}", flush=True)
        try:
            print(f"[create_or_update_session] Oracle DB 연결 시도...", flush=True)
            with get_connection() as conn:
                print(f"[create_or_update_session] Oracle DB 연결 성공!", flush=True)
                
                with conn.cursor() as cur:
                    # 1. SESSION_ID 타입 확인 및 수정 (가장 먼저 실행)
                    OnboardingDBService._ensure_session_id_type(conn, cur)
                    
                    # 2. 필요한 컬럼 존재 확인 및 추가
                    OnboardingDBService._ensure_table_columns_exist(conn, cur)
                    
                    # 3. MEMBER_ID NOT NULL 및 기본값 'GUEST' 확인 및 수정
                    OnboardingDBService._ensure_member_id_default_guest(conn, cur)
                    
                    # 4. GUEST 레코드 존재 확인 및 생성
                    OnboardingDBService._ensure_guest_member_exists(conn, cur)
                    
                    # 테이블 존재 여부 확인
                    try:
                        cur.execute("""
                            SELECT COUNT(*) FROM USER_TABLES WHERE TABLE_NAME = 'ONBOARDING_SESSION'
                        """)
                        table_exists = cur.fetchone()[0] > 0
                        print(f"[create_or_update_session] ONBOARDING_SESSION 테이블 존재 여부: {table_exists}", flush=True)
                        if not table_exists:
                            print(f"[create_or_update_session] ⚠️ 경고: ONBOARDING_SESSION 테이블이 존재하지 않습니다!", flush=True)
                    except Exception as e:
                        print(f"[create_or_update_session] 테이블 존재 여부 확인 중 오류: {str(e)}", flush=True)
                    
                    # session_id 처리: Step 1에서만 생성, Step 2~7에서는 필수
                    if not session_id:
                        if current_step == 1:
                            # Step 1: 타임스탬프 기반 정수 생성
                            import time
                            session_id = str(int(time.time() * 1000))  # 밀리초 단위 타임스탬프
                            print(f"[create_or_update_session] Step 1: session_id가 없어서 타임스탬프로 생성: {session_id}", flush=True)
                        else:
                            # Step 2~7: session_id가 없으면 에러
                            raise ValueError(f"Step {current_step}에서는 session_id가 필수입니다. Step 1부터 다시 시작해주세요.")
                    
                    # session_id를 문자열로 변환 (VARCHAR2 타입 호환성)
                    session_id = str(session_id)
                    
                    # 세션 ID 중복 체크 및 재생성 (SESSION_ID 타입 확인 후)
                    try:
                        cur.execute("""
                            SELECT DATA_TYPE FROM USER_TAB_COLUMNS
                            WHERE TABLE_NAME = 'ONBOARDING_SESSION' AND COLUMN_NAME = 'SESSION_ID'
                        """)
                        type_result = cur.fetchone()
                        session_id_is_varchar = type_result and type_result[0] == 'VARCHAR2'
                    except:
                        session_id_is_varchar = False
                    
                    # Step 2~7에서는 중복 체크를 하지 않음 (이미 존재하는 세션을 사용해야 함)
                    # Step 1에서만 중복 체크 (새로 생성하는 경우)
                    if current_step == 1 and session_id_is_varchar:
                        # Step 1: VARCHAR2 타입이면 중복 체크 가능
                        max_retries = 5
                        retry_count = 0
                        original_session_id = session_id
                        while retry_count < max_retries:
                            try:
                                cur.execute("""
                                    SELECT COUNT(*) FROM ONBOARDING_SESSION WHERE SESSION_ID = :session_id
                                """, {'session_id': str(session_id)})
                                exists = cur.fetchone()[0] > 0
                                
                                if not exists:
                                    break  # 중복 없음, 사용 가능
                                
                                # 중복 발견 시 새 타임스탬프 생성 (매우 드문 경우)
                                import time
                                session_id = str(int(time.time() * 1000) + retry_count)  # 밀리초 단위 타임스탬프 + 재시도 횟수
                                retry_count += 1
                                print(f"[create_or_update_session] Step 1: 세션 ID 중복 발견 ({original_session_id}), 재생성 시도 {retry_count}/{max_retries}: {session_id}", flush=True)
                            except Exception as e:
                                error_msg = str(e)
                                if 'ORA-01722' in error_msg:
                                    print(f"[create_or_update_session] ⚠️ SESSION_ID 타입 불일치 오류. 중복 체크를 건너뜁니다.", flush=True)
                                else:
                                    print(f"[create_or_update_session] 세션 ID 중복 체크 중 오류: {e}. 기존 ID 사용", flush=True)
                                break
                        
                        if retry_count >= max_retries:
                            raise ValueError(f"세션 ID 생성 실패 (최대 재시도 횟수 초과). 원본 ID: {original_session_id}")
                    else:
                        # Step 2~7: 중복 체크 안 함, 기존 session_id 그대로 사용
                        if current_step > 1:
                            print(f"[create_or_update_session] Step {current_step}: 중복 체크 건너뜀, 기존 session_id 사용: {session_id}", flush=True)
                        elif not session_id_is_varchar:
                            print(f"[create_or_update_session] ⚠️ SESSION_ID가 VARCHAR2가 아니어서 중복 체크를 건너뜁니다. SESSION_ID 타입 변경이 필요합니다.", flush=True)
                    
                    # 세션이 존재하는지 확인 (SESSION_ID 타입 확인 후)
                    print(f"[create_or_update_session] 세션 존재 여부 확인 - SESSION_ID={session_id}", flush=True)
                    exists = False
                    try:
                        # SESSION_ID 타입 확인
                        cur.execute("""
                            SELECT DATA_TYPE FROM USER_TAB_COLUMNS
                            WHERE TABLE_NAME = 'ONBOARDING_SESSION' AND COLUMN_NAME = 'SESSION_ID'
                        """)
                        type_result = cur.fetchone()
                        session_id_is_varchar = type_result and type_result[0] == 'VARCHAR2'
                        
                        # session_id를 문자열로 변환
                        session_id_str = str(session_id)
                        
                        if session_id_is_varchar:
                            # VARCHAR2 타입이면 문자열로 조회
                            cur.execute("""
                                SELECT COUNT(*) FROM ONBOARDING_SESSION WHERE SESSION_ID = :session_id
                            """, {'session_id': session_id_str})
                            count = cur.fetchone()[0]
                            exists = count > 0
                            print(f"[create_or_update_session] 세션 존재 여부: {exists} (COUNT={count})", flush=True)
                        else:
                            # NUMBER 타입이면 숫자로 변환 시도
                            try:
                                session_id_num = int(session_id) if session_id and str(session_id).isdigit() else None
                                if session_id_num is not None:
                                    cur.execute("""
                                        SELECT COUNT(*) FROM ONBOARDING_SESSION WHERE SESSION_ID = :session_id
                                    """, {'session_id': session_id_num})
                                    count = cur.fetchone()[0]
                                    exists = count > 0
                                    print(f"[create_or_update_session] 세션 존재 여부: {exists} (COUNT={count}, NUMBER 타입)", flush=True)
                                else:
                                    # 숫자로 변환 불가능
                                    exists = False
                                    print(f"[create_or_update_session] ⚠️ SESSION_ID가 NUMBER 타입인데 숫자로 변환 불가: {session_id}", flush=True)
                            except (ValueError, TypeError) as convert_error:
                                exists = False
                                print(f"[create_or_update_session] ⚠️ SESSION_ID 숫자 변환 실패: {convert_error}", flush=True)
                    except Exception as e:
                        error_msg = str(e)
                        if 'ORA-01722' in error_msg:
                            print(f"[create_or_update_session] ⚠️ 세션 조회 오류: SESSION_ID 타입 불일치. exists=False로 설정합니다.", flush=True)
                            exists = False
                        else:
                            print(f"[create_or_update_session] 세션 조회 오류: {str(e)}", flush=True)
                            import traceback
                            traceback.print_exc()
                            exists = False  # 오류 발생 시 False로 설정
                    
                    print(f"[create_or_update_session] 최종 세션 존재 여부: {exists}", flush=True)
                    
                    # 정규화 테이블용 데이터 준비
                    selected_categories = kwargs.get('selected_categories', [])
                    if not isinstance(selected_categories, list):
                        selected_categories = []
                    
                    recommended_products = kwargs.get('recommended_products', [])
                    if not isinstance(recommended_products, list):
                        recommended_products = []
                    
                    # 디버깅: 전달된 값 확인
                    print(f"[create_or_update_session] selected_categories = {selected_categories} (타입: {type(selected_categories).__name__}, 길이: {len(selected_categories)})", flush=True)
                    print(f"[create_or_update_session] recommended_products = {recommended_products[:5] if len(recommended_products) > 5 else recommended_products} (타입: {type(recommended_products).__name__}, 길이: {len(recommended_products)})", flush=True)
                    
                    # recommendation_result에서 추천 상세 정보 추출 (category, score 포함)
                    recommendation_result = kwargs.get('recommendation_result', {})
                    recommendations_detail = {}
                    if recommendation_result and isinstance(recommendation_result, dict):
                        recommendations_list = recommendation_result.get('recommendations', [])
                        if isinstance(recommendations_list, list):
                            for rec in recommendations_list:
                                product_id = rec.get('product_id') or rec.get('id')
                                if product_id:
                                    recommendations_detail[int(product_id)] = {
                                        'category': rec.get('category') or rec.get('main_category') or rec.get('category_name'),
                                        'score': rec.get('score') or rec.get('taste_score')
                                    }
                    
                    # 정규화 테이블용 데이터 준비
                    main_spaces = kwargs.get('main_spaces', kwargs.get('main_space', []))
                    if isinstance(main_spaces, str):
                        try:
                            main_spaces = json.loads(main_spaces)
                        except:
                            main_spaces = [main_spaces] if main_spaces else []
                    elif not isinstance(main_spaces, list):
                        main_spaces = []
                    
                    priority_list = kwargs.get('priorities', kwargs.get('priority_list', []))
                    if isinstance(priority_list, str):
                        try:
                            priority_list = json.loads(priority_list)
                        except:
                            priority_list = [priority_list] if priority_list else []
                    elif not isinstance(priority_list, list):
                        priority_list = []
                    
                    # MEMBER_ID 처리 - GUEST 기본값 사용 (NULL 허용 안 함)
                    raw_member_id = member_id or kwargs.get('member_id')
                    
                    # MEMBER_ID 유효성 검증: MEMBER 테이블에 존재하는지 확인
                    final_member_id = 'GUEST'  # 기본값은 항상 'GUEST'
                    if raw_member_id:
                        try:
                            cur.execute("""
                                SELECT COUNT(*) FROM MEMBER WHERE MEMBER_ID = :member_id
                            """, {'member_id': raw_member_id})
                            member_exists = cur.fetchone()[0] > 0
                            
                            if member_exists:
                                final_member_id = raw_member_id
                                print(f"[create_or_update_session] MEMBER_ID '{raw_member_id}' 검증 성공", flush=True)
                            else:
                                # MEMBER_ID가 존재하지 않으면 'GUEST'로 설정
                                print(f"[create_or_update_session] ⚠️ 경고: MEMBER_ID '{raw_member_id}'가 MEMBER 테이블에 존재하지 않습니다. 'GUEST'로 설정합니다.", flush=True)
                                final_member_id = 'GUEST'
                        except Exception as validation_error:
                            # 검증 중 오류 발생 시에도 'GUEST'로 설정하여 계속 진행
                            print(f"[create_or_update_session] ⚠️ 경고: MEMBER_ID 검증 중 오류 발생: {validation_error}. 'GUEST'로 설정합니다.", flush=True)
                            final_member_id = 'GUEST'
                    else:
                        # member_id가 없으면 항상 'GUEST' 사용
                        final_member_id = 'GUEST'
                        print(f"[create_or_update_session] MEMBER_ID가 없어서 기본값 'GUEST' 사용", flush=True)
                    
                    # has_pet, cooking, laundry, media는 kwargs에서 직접 가져옴
                    has_pet = kwargs.get('has_pet')
                    if has_pet is True:
                        has_pet = 'Y'
                    elif has_pet is False:
                        has_pet = 'N'
                    elif has_pet is None:
                        has_pet = None
                    
                    cooking = kwargs.get('cooking')
                    laundry = kwargs.get('laundry')
                    media = kwargs.get('media')
                    
                    # 숫자 필드 변환 (Oracle NUMBER 타입 호환성)
                    household_size = OnboardingDBService._convert_to_numeric(kwargs.get('household_size'))
                    pyung = OnboardingDBService._convert_to_numeric(kwargs.get('pyung'))
                    
                    print(f"[create_or_update_session] 숫자 필드 변환 결과:", flush=True)
                    print(f"  household_size: {kwargs.get('household_size')} → {household_size} (타입: {type(household_size).__name__})", flush=True)
                    print(f"  pyung: {kwargs.get('pyung')} → {pyung} (타입: {type(pyung).__name__})", flush=True)
                    
                    # 업데이트
                    rows_updated = 0  # 초기화
                    rows_inserted = 0  # 초기화
                    error_already_logged = False  # 에러 로그 중복 방지 플래그
                    
                    # 변환된 SESSION_ID를 저장할 변수 (정규화 테이블에서도 사용)
                    converted_session_id = None
                    
                    # UPDATE 실행 전에 SESSION_ID 타입 확인 (타입 불일치 방지)
                    print(f"\n{'='*80}", flush=True)
                    print(f"[Oracle DB] ONBOARDING_SESSION 테이블 UPDATE 실행", flush=True)
                    print(f"{'='*80}", flush=True)
                    print(f"  SESSION_ID: {session_id}", flush=True)
                    print(f"  세션 존재 여부: {exists}", flush=True)
                    
                    # SESSION_ID 타입 재확인 (UPDATE 문 실행 전)
                    try:
                        cur.execute("""
                            SELECT DATA_TYPE FROM USER_TAB_COLUMNS
                            WHERE TABLE_NAME = 'ONBOARDING_SESSION' AND COLUMN_NAME = 'SESSION_ID'
                        """)
                        type_result = cur.fetchone()
                        session_id_is_varchar = type_result and type_result[0] == 'VARCHAR2'
                        
                        # NUMBER 타입인데 UUID 문자열이면 UPDATE 건너뛰기
                        if not session_id_is_varchar:
                            # UUID 문자열인지 확인 (숫자로 변환 불가능한 경우)
                            try:
                                session_id_num = int(session_id) if session_id and str(session_id).isdigit() else None
                                if session_id_num is None:
                                    # UUID 문자열이므로 UPDATE 불가능
                                    print(f"  ⚠️ SESSION_ID가 NUMBER 타입인데 UUID 문자열을 사용 중입니다.", flush=True)
                                    print(f"  ⚠️ UPDATE를 건너뛰고 INSERT로 전환합니다.", flush=True)
                                    rows_updated = 0  # UPDATE 건너뛰기
                                    session_id_for_update = None
                                    converted_session_id = None
                                else:
                                    # 숫자로 변환 가능하면 UPDATE 시도
                                    print(f"  [UPDATE 실행 중...] (SESSION_ID를 숫자로 변환: {session_id_num})", flush=True)
                                    session_id_for_update = session_id_num
                                    converted_session_id = session_id_num  # 정규화 테이블에서도 사용
                            except (ValueError, TypeError):
                                # UUID 문자열이므로 UPDATE 불가능
                                print(f"  ⚠️ SESSION_ID가 NUMBER 타입인데 UUID 문자열을 사용 중입니다.", flush=True)
                                print(f"  ⚠️ UPDATE를 건너뛰고 INSERT로 전환합니다.", flush=True)
                                rows_updated = 0  # UPDATE 건너뛰기
                                session_id_for_update = None
                                converted_session_id = None
                        else:
                            # VARCHAR2 타입이면 그대로 사용
                            print(f"  [UPDATE 실행 중...] (SESSION_ID 타입: VARCHAR2)", flush=True)
                            session_id_for_update = session_id
                            converted_session_id = session_id  # 정규화 테이블에서도 사용
                    except Exception as type_check_error:
                        # 타입 확인 실패 시 기존 로직대로 진행 (하위 호환성)
                        print(f"  ⚠️ SESSION_ID 타입 확인 실패: {type_check_error}. 기존 로직대로 진행합니다.", flush=True)
                        session_id_for_update = session_id
                        converted_session_id = session_id  # 정규화 테이블에서도 사용
                    
                    # UPDATE 실행 (session_id_for_update가 None이 아니고 exists가 True일 때만)
                    if session_id_for_update is not None and exists is True:
                        try:
                            cur.execute("""
                                UPDATE ONBOARDING_SESSION SET
                                    MEMBER_ID = :member_id,
                                    CURRENT_STEP = :current_step,
                                    STATUS = :status,
                                    VIBE = :vibe,
                                    HOUSEHOLD_SIZE = :household_size,
                                    HAS_PET = :has_pet,
                                    HOUSING_TYPE = :housing_type,
                                    PYUNG = :pyung,
                                    COOKING = :cooking,
                                    LAUNDRY = :laundry,
                                    MEDIA = :media,
                                    PRIORITY = :priority,
                                    BUDGET_LEVEL = :budget_level,
                                    UPDATED_AT = SYSDATE,
                                    COMPLETED_AT = CASE WHEN :status = 'COMPLETED' THEN SYSDATE ELSE COMPLETED_AT END
                                WHERE SESSION_ID = :session_id
                            """, {
                                'session_id': session_id_for_update,
                                'member_id': final_member_id,
                                'current_step': current_step,
                                'status': status,
                                'vibe': kwargs.get('vibe'),
                                'household_size': household_size,
                                'has_pet': has_pet,
                                'housing_type': kwargs.get('housing_type'),
                                'pyung': pyung,
                                'cooking': cooking,
                                'laundry': laundry,
                                'media': media,
                                'priority': kwargs.get('priority'),
                                'budget_level': kwargs.get('budget_level'),
                            })
                            rows_updated = cur.rowcount
                            print(f"  [UPDATE 실행 완료]", flush=True)
                            print(f"    rows_updated = {rows_updated} (타입: {type(rows_updated).__name__})", flush=True)
                            if rows_updated == 0:
                                print(f"    ⚠️ 경고: UPDATE가 실행되었지만 영향받은 행이 없습니다! INSERT로 전환합니다.", flush=True)
                            else:
                                print(f"    ✅ UPDATE 성공 - {rows_updated}개 행 업데이트됨", flush=True)
                        except Exception as update_error:
                            rows_updated = 0  # 예외 발생 시 0으로 설정
                            error_already_logged = True  # 에러 로그 출력 완료 표시
                            
                            # 에러 정보 추출
                            error_type = type(update_error).__name__
                            error_message = str(update_error)
                            error_code = ""
                            if "ORA-" in error_message:
                                import re
                                match = re.search(r'ORA-\d+', error_message)
                                if match:
                                    error_code = match.group()
                            
                            # 에러 발생 시점부터 명확한 설명 먼저 표시
                            print(f"\n{'='*80}", flush=True)
                            print(f"[create_or_update_session] ❌ Oracle DB 저장 실패", flush=True)
                            print(f"{'='*80}", flush=True)
                            print(f"  발생 위치: UPDATE ONBOARDING_SESSION 실행 중", flush=True)
                            print(f"  SESSION_ID: {session_id}", flush=True)
                            if error_code:
                                print(f"  에러 코드: {error_code}", flush=True)
                                if error_code == 'ORA-01722':
                                    print(f"  ⚠️ 숫자 타입 불일치: SESSION_ID가 NUMBER 타입인데 문자열을 사용했습니다.", flush=True)
                                    print(f"     가능한 원인:", flush=True)
                                    print(f"     1. SESSION_ID 컬럼이 NUMBER 타입인데 UUID 문자열을 사용", flush=True)
                                    print(f"     2. SESSION_ID 타입 변환이 필요합니다 (NUMBER → VARCHAR2)", flush=True)
                                    print(f"     해결 방법:", flush=True)
                                    print(f"     - ONBOARDING_SESSION 테이블의 SESSION_ID 컬럼을 VARCHAR2(100)로 변경", flush=True)
                                    print(f"     - 또는 숫자 형식의 SESSION_ID 사용", flush=True)
                                elif error_code == 'ORA-02291':
                                    print(f"  ⚠️ 외래키 제약조건 위반: 참조하는 부모 키가 존재하지 않습니다.", flush=True)
                                    print(f"     가능한 원인:", flush=True)
                                    print(f"     1. MEMBER_ID '{final_member_id}'가 MEMBER 테이블에 존재하지 않음", flush=True)
                                    print(f"     2. 다른 외래키 제약조건 위반 (정규화 테이블 등)", flush=True)
                                    print(f"     해결 방법:", flush=True)
                                    print(f"     - MEMBER_ID가 NULL 허용이므로 NULL로 설정하거나", flush=True)
                                    print(f"     - 유효한 MEMBER_ID를 사용하거나", flush=True)
                                    print(f"     - 'GUEST' 멤버를 생성하려면 create_guest_member.py 실행", flush=True)
                            print(f"  에러 타입: {error_type}", flush=True)
                            print(f"  에러 메시지: {error_message}", flush=True)
                            print(f"{'='*80}", flush=True)
                            print(f"  [상세 정보]", flush=True)
                            print(f"    세션 존재 여부: {exists}", flush=True)
                            print(f"    UPDATE 시도한 데이터:", flush=True)
                            print(f"      MEMBER_ID = {final_member_id}", flush=True)
                            print(f"      CURRENT_STEP = {current_step}", flush=True)
                            print(f"      STATUS = {status}", flush=True)
                            print(f"      VIBE = {kwargs.get('vibe')}", flush=True)
                            print(f"      HOUSEHOLD_SIZE = {household_size} (원본: {kwargs.get('household_size')})", flush=True)
                            print(f"      HOUSING_TYPE = {kwargs.get('housing_type')}", flush=True)
                            print(f"      PYUNG = {pyung} (원본: {kwargs.get('pyung')})", flush=True)
                            print(f"      PRIORITY = {kwargs.get('priority')}", flush=True)
                            print(f"      BUDGET_LEVEL = {kwargs.get('budget_level')}", flush=True)
                            print(f"  [전체 트레이스백]", flush=True)
                            import traceback
                            traceback.print_exc()
                            print(f"{'='*80}\n", flush=True)
                            raise
                    else:
                        # UPDATE를 건너뛴 경우
                        if session_id_for_update is None:
                            print(f"  ⚠️ SESSION_ID 타입 불일치로 UPDATE를 건너뛰었습니다. INSERT로 전환합니다.", flush=True)
                        elif not exists:
                            print(f"  ⚠️ 세션이 존재하지 않아 UPDATE를 건너뛰었습니다. INSERT로 전환합니다.", flush=True)
                        rows_updated = 0
                    
                    if rows_updated > 0:
                        # 정규화 테이블 업데이트 (변환된 SESSION_ID 사용)
                        session_id_for_normalized = converted_session_id if converted_session_id is not None else session_id
                        
                        # MAIN_SPACE
                        if main_spaces:
                            print(f"[Oracle DB] ONBOARD_SESS_MAIN_SPACES 테이블 DELETE 후 INSERT", flush=True)
                            cur.execute("DELETE FROM ONBOARD_SESS_MAIN_SPACES WHERE SESSION_ID = :session_id", {'session_id': session_id_for_normalized})
                            for space in main_spaces:
                                print(f"  INSERT: SESSION_ID={session_id_for_normalized}, MAIN_SPACE={space}", flush=True)
                                cur.execute("""
                                    INSERT INTO ONBOARD_SESS_MAIN_SPACES (SESSION_ID, MAIN_SPACE)
                                    VALUES (:session_id, :main_space)
                                """, {'session_id': session_id_for_normalized, 'main_space': str(space)})
                        
                        # PRIORITY_LIST
                        if priority_list:
                            print(f"[Oracle DB] ONBOARD_SESS_PRIORITIES 테이블 DELETE 후 INSERT", flush=True)
                            cur.execute("DELETE FROM ONBOARD_SESS_PRIORITIES WHERE SESSION_ID = :session_id", {'session_id': session_id_for_normalized})
                            for idx, priority in enumerate(priority_list, start=1):
                                print(f"  INSERT: SESSION_ID={session_id_for_normalized}, PRIORITY={priority}, PRIORITY_ORDER={idx}", flush=True)
                                cur.execute("""
                                    INSERT INTO ONBOARD_SESS_PRIORITIES (SESSION_ID, PRIORITY, PRIORITY_ORDER)
                                    VALUES (:session_id, :priority, :priority_order)
                                """, {'session_id': session_id_for_normalized, 'priority': str(priority), 'priority_order': idx})
                        
                        # SELECTED_CATEGORIES
                        print(f"[Oracle DB] selected_categories 조건 체크 (UPDATE 블록): {selected_categories} (bool: {bool(selected_categories)})", flush=True)
                        if selected_categories:
                            print(f"[Oracle DB] ONBOARD_SESS_CATEGORIES 테이블 DELETE 후 INSERT", flush=True)
                            cur.execute("DELETE FROM ONBOARD_SESS_CATEGORIES WHERE SESSION_ID = :session_id", {'session_id': session_id_for_normalized})
                            for category in selected_categories:
                                print(f"  INSERT: SESSION_ID={session_id_for_normalized}, CATEGORY_NAME={category}", flush=True)
                                cur.execute("""
                                    INSERT INTO ONBOARD_SESS_CATEGORIES (SESSION_ID, CATEGORY_NAME)
                                    VALUES (:session_id, :category_name)
                                """, {'session_id': session_id_for_normalized, 'category_name': str(category)})
                        else:
                            print(f"[Oracle DB] ⚠️ selected_categories가 비어있어서 INSERT 실행 안됨 (UPDATE 블록)", flush=True)
                        
                        # RECOMMENDED_PRODUCTS
                        print(f"[Oracle DB] recommended_products 조건 체크 (UPDATE 블록): {recommended_products[:5] if len(recommended_products) > 5 else recommended_products} (bool: {bool(recommended_products)})", flush=True)
                        if recommended_products:
                            print(f"[Oracle DB] ONBOARD_SESS_REC_PRODUCTS 테이블 DELETE 후 INSERT", flush=True)
                            cur.execute("DELETE FROM ONBOARD_SESS_REC_PRODUCTS WHERE SESSION_ID = :session_id", {'session_id': session_id_for_normalized})
                            
                            # 카테고리별 순위를 추적하기 위한 딕셔너리
                            category_ranks = {}
                            
                            for idx, product_id in enumerate(recommended_products, start=1):
                                product_id_int = int(product_id)
                                rec_detail = recommendations_detail.get(product_id_int, {})
                                category_name = rec_detail.get('category')
                                score = rec_detail.get('score')
                                
                                # 카테고리별 순위 계산
                                if category_name:
                                    if category_name not in category_ranks:
                                        category_ranks[category_name] = 0
                                    category_ranks[category_name] += 1
                                    rank_order = category_ranks[category_name]
                                else:
                                    rank_order = idx
                                
                                # SCORE를 0-100 범위로 변환 (0-1 범위인 경우)
                                score_value = None
                                if score is not None:
                                    try:
                                        score_float = float(score)
                                        # 0-1 범위면 100을 곱함
                                        if 0 <= score_float <= 1:
                                            score_value = round(score_float * 100, 2)
                                        # 이미 0-100 범위면 그대로 사용
                                        elif 0 <= score_float <= 100:
                                            score_value = round(score_float, 2)
                                    except (ValueError, TypeError):
                                        score_value = None
                                
                                print(f"  INSERT: SESSION_ID={session_id_for_normalized}, PRODUCT_ID={product_id_int}, CATEGORY={category_name}, RANK_ORDER={rank_order}, SCORE={score_value}", flush=True)
                                cur.execute("""
                                    INSERT INTO ONBOARD_SESS_REC_PRODUCTS (SESSION_ID, PRODUCT_ID, CATEGORY_NAME, RANK_ORDER, SCORE, CREATED_AT)
                                    VALUES (:session_id, :product_id, :category_name, :rank_order, :score, SYSDATE)
                                """, {
                                    'session_id': session_id_for_normalized,
                                    'product_id': product_id_int,
                                    'category_name': category_name,
                                    'rank_order': rank_order,
                                    'score': score_value
                                })
                        else:
                            print(f"[Oracle DB] ⚠️ recommended_products가 비어있어서 INSERT 실행 안됨 (UPDATE 블록)", flush=True)
                    else:  # INSERT (Step 1에서만 허용)
                        # Step 2~7에서는 INSERT 금지
                        if current_step > 1:
                            raise ValueError(f"Step {current_step}에서는 INSERT가 불가능합니다. Step 1에서 생성된 세션을 찾을 수 없습니다. (session_id: {session_id})")
                        
                        print(f"\n{'='*80}", flush=True)
                        print(f"[Oracle DB] ONBOARDING_SESSION 테이블 INSERT 실행 (Step 1만 허용)", flush=True)
                        print(f"{'='*80}", flush=True)
                        print(f"  [INSERT 전 상태]", flush=True)
                        print(f"    SESSION_ID = {session_id} (타입: {type(session_id).__name__})", flush=True)
                        print(f"    세션 존재 여부: {exists} (Step 1이므로 INSERT 실행)", flush=True)
                        print(f"    MEMBER_ID = {final_member_id}", flush=True)
                        print(f"    CURRENT_STEP = {current_step}", flush=True)
                        print(f"    STATUS = {status}", flush=True)
                        print(f"    VIBE = {kwargs.get('vibe')}", flush=True)
                        print(f"    HOUSEHOLD_SIZE = {household_size} (원본: {kwargs.get('household_size')})", flush=True)
                        print(f"    HAS_PET = {has_pet}", flush=True)
                        print(f"    HOUSING_TYPE = {kwargs.get('housing_type')}", flush=True)
                        print(f"    PYUNG = {pyung} (원본: {kwargs.get('pyung')})", flush=True)
                        print(f"    COOKING = {cooking}", flush=True)
                        print(f"    LAUNDRY = {laundry}", flush=True)
                        print(f"    MEDIA = {media}", flush=True)
                        print(f"    PRIORITY = {kwargs.get('priority')}", flush=True)
                        print(f"    BUDGET_LEVEL = {kwargs.get('budget_level')}", flush=True)
                        
                        # INSERT 실행 전에 SESSION_ID 타입 확인 및 변환
                        try:
                            cur.execute("""
                                SELECT DATA_TYPE FROM USER_TAB_COLUMNS
                                WHERE TABLE_NAME = 'ONBOARDING_SESSION' AND COLUMN_NAME = 'SESSION_ID'
                            """)
                            type_result = cur.fetchone()
                            session_id_is_varchar = type_result and type_result[0] == 'VARCHAR2'
                            
                            # NUMBER 타입인데 UUID 문자열이면 숫자로 변환 시도
                            if not session_id_is_varchar:
                                try:
                                    session_id_num = int(session_id) if session_id and str(session_id).isdigit() else None
                                    if session_id_num is None:
                                        # UUID 문자열은 NUMBER 타입에 삽입 불가능
                                        raise ValueError(f"SESSION_ID가 NUMBER 타입인데 UUID 문자열 '{session_id}'를 사용할 수 없습니다. SESSION_ID 컬럼을 VARCHAR2(100)로 변경하거나 숫자 형식의 SESSION_ID를 사용해야 합니다.")
                                    else:
                                        # 숫자로 변환 가능하면 변환된 값 사용
                                        print(f"  [INSERT 실행 중...] (SESSION_ID를 숫자로 변환: {session_id_num})", flush=True)
                                        session_id_for_insert = session_id_num
                                except (ValueError, TypeError) as convert_error:
                                    raise ValueError(f"SESSION_ID가 NUMBER 타입인데 UUID 문자열 '{session_id}'를 사용할 수 없습니다. SESSION_ID 컬럼을 VARCHAR2(100)로 변경하거나 숫자 형식의 SESSION_ID를 사용해야 합니다. 변환 오류: {convert_error}")
                            else:
                                # VARCHAR2 타입이면 그대로 사용
                                print(f"  [INSERT 실행 중...] (SESSION_ID 타입: VARCHAR2)", flush=True)
                                session_id_for_insert = session_id
                        except Exception as type_check_error:
                            # 타입 확인 실패 시 기존 로직대로 진행 (하위 호환성)
                            print(f"  ⚠️ SESSION_ID 타입 확인 실패: {type_check_error}. 기존 로직대로 진행합니다.", flush=True)
                            session_id_for_insert = session_id
                        
                        try:
                            cur.execute("""
                                INSERT INTO ONBOARDING_SESSION (
                                    SESSION_ID, MEMBER_ID, CURRENT_STEP, STATUS,
                                    VIBE, HOUSEHOLD_SIZE, HAS_PET, HOUSING_TYPE, PYUNG,
                                    COOKING, LAUNDRY, MEDIA,
                                    PRIORITY, BUDGET_LEVEL,
                                    CREATED_AT, UPDATED_AT, COMPLETED_AT
                                ) VALUES (
                                    :session_id, :member_id, :current_step, :status,
                                    :vibe, :household_size, :has_pet, :housing_type, :pyung,
                                    :cooking, :laundry, :media,
                                    :priority, :budget_level,
                                    SYSDATE, SYSDATE,
                                    CASE WHEN :status = 'COMPLETED' THEN SYSDATE ELSE NULL END
                                )
                            """, {
                                'session_id': session_id_for_insert,
                                'member_id': final_member_id,
                                'current_step': current_step,
                                'status': status,
                                'vibe': kwargs.get('vibe'),
                                'household_size': household_size,
                                'has_pet': has_pet,
                                'housing_type': kwargs.get('housing_type'),
                                'pyung': pyung,
                                'cooking': cooking,
                                'laundry': laundry,
                                'media': media,
                                'priority': kwargs.get('priority'),
                                'budget_level': kwargs.get('budget_level'),
                            })
                            rows_inserted = cur.rowcount
                            print(f"  [INSERT 실행 완료]", flush=True)
                            print(f"    rows_inserted = {rows_inserted} (타입: {type(rows_inserted).__name__})", flush=True)
                            if rows_inserted == 0:
                                print(f"    ⚠️ 경고: INSERT가 실행되었지만 영향받은 행이 없습니다!", flush=True)
                            else:
                                print(f"    ✅ INSERT 성공 - {rows_inserted}개 행 삽입됨", flush=True)
                        except Exception as insert_error:
                            error_type = type(insert_error).__name__
                            error_message = str(insert_error)
                            error_code = ""
                            if "ORA-" in error_message:
                                import re
                                match = re.search(r'ORA-\d+', error_message)
                                if match:
                                    error_code = match.group()
                            
                            print(f"  [INSERT 실행 중 예외 발생!]", flush=True)
                            print(f"    예외 타입: {error_type}", flush=True)
                            print(f"    예외 메시지: {error_message}", flush=True)
                            if error_code == 'ORA-01722':
                                print(f"    ⚠️ 숫자 타입 불일치: SESSION_ID가 NUMBER 타입인데 문자열을 사용했습니다.", flush=True)
                                print(f"       해결 방법: ONBOARDING_SESSION 테이블의 SESSION_ID 컬럼을 VARCHAR2(100)로 변경", flush=True)
                            import traceback
                            print(f"    트레이스백:", flush=True)
                            traceback.print_exc()
                            raise
                        
                        # 정규화 테이블 업데이트/저장 (생성/업데이트 공통) - 변환된 SESSION_ID 사용
                        session_id_for_normalized_insert = session_id_for_insert
                        
                        # MAIN_SPACE
                        if main_spaces:
                            print(f"[Oracle DB] ONBOARD_SESS_MAIN_SPACES 테이블 DELETE 후 INSERT (생성/업데이트 공통)", flush=True)
                            cur.execute("DELETE FROM ONBOARD_SESS_MAIN_SPACES WHERE SESSION_ID = :session_id", {'session_id': session_id_for_normalized_insert})
                            for space in main_spaces:
                                print(f"  INSERT: SESSION_ID={session_id_for_normalized_insert}, MAIN_SPACE={space}", flush=True)
                                cur.execute("""
                                    INSERT INTO ONBOARD_SESS_MAIN_SPACES (SESSION_ID, MAIN_SPACE, CREATED_AT)
                                    VALUES (:session_id, :main_space, SYSDATE)
                                """, {'session_id': session_id_for_normalized_insert, 'main_space': str(space)})
                        
                        # PRIORITY_LIST
                        if priority_list:
                            print(f"[Oracle DB] ONBOARD_SESS_PRIORITIES 테이블 DELETE 후 INSERT (생성/업데이트 공통)", flush=True)
                            cur.execute("DELETE FROM ONBOARD_SESS_PRIORITIES WHERE SESSION_ID = :session_id", {'session_id': session_id_for_normalized_insert})
                            for idx, priority in enumerate(priority_list, start=1):
                                print(f"  INSERT: SESSION_ID={session_id_for_normalized_insert}, PRIORITY={priority}, PRIORITY_ORDER={idx}", flush=True)
                                cur.execute("""
                                    INSERT INTO ONBOARD_SESS_PRIORITIES (SESSION_ID, PRIORITY, PRIORITY_ORDER, CREATED_AT)
                                    VALUES (:session_id, :priority, :priority_order, SYSDATE)
                                """, {'session_id': session_id_for_normalized_insert, 'priority': str(priority), 'priority_order': idx})
                        
                        # SELECTED_CATEGORIES
                        print(f"[Oracle DB] selected_categories 조건 체크 (INSERT 블록): {selected_categories} (bool: {bool(selected_categories)})", flush=True)
                        if selected_categories:
                            print(f"[Oracle DB] ONBOARD_SESS_CATEGORIES 테이블 DELETE 후 INSERT (생성/업데이트 공통)", flush=True)
                            cur.execute("DELETE FROM ONBOARD_SESS_CATEGORIES WHERE SESSION_ID = :session_id", {'session_id': session_id_for_normalized_insert})
                            for category in selected_categories:
                                print(f"  INSERT: SESSION_ID={session_id_for_normalized_insert}, CATEGORY_NAME={category}", flush=True)
                                cur.execute("""
                                    INSERT INTO ONBOARD_SESS_CATEGORIES (SESSION_ID, CATEGORY_NAME, CREATED_AT)
                                    VALUES (:session_id, :category_name, SYSDATE)
                                """, {'session_id': session_id_for_normalized_insert, 'category_name': str(category)})
                        else:
                            print(f"[Oracle DB] ⚠️ selected_categories가 비어있어서 INSERT 실행 안됨 (INSERT 블록)", flush=True)
                        
                        # RECOMMENDED_PRODUCTS
                        print(f"[Oracle DB] recommended_products 조건 체크 (INSERT 블록): {recommended_products[:5] if len(recommended_products) > 5 else recommended_products} (bool: {bool(recommended_products)})", flush=True)
                        if recommended_products:
                            print(f"[Oracle DB] ONBOARD_SESS_REC_PRODUCTS 테이블 DELETE 후 INSERT (생성/업데이트 공통)", flush=True)
                            cur.execute("DELETE FROM ONBOARD_SESS_REC_PRODUCTS WHERE SESSION_ID = :session_id", {'session_id': session_id_for_normalized_insert})
                            
                            # 카테고리별 순위를 추적하기 위한 딕셔너리
                            category_ranks = {}
                            
                            for idx, product_id in enumerate(recommended_products, start=1):
                                product_id_int = int(product_id)
                                rec_detail = recommendations_detail.get(product_id_int, {})
                                category_name = rec_detail.get('category')
                                score = rec_detail.get('score')
                                
                                # 카테고리별 순위 계산
                                if category_name:
                                    if category_name not in category_ranks:
                                        category_ranks[category_name] = 0
                                    category_ranks[category_name] += 1
                                    rank_order = category_ranks[category_name]
                                else:
                                    rank_order = idx
                                
                                # SCORE를 0-100 범위로 변환 (0-1 범위인 경우)
                                score_value = None
                                if score is not None:
                                    try:
                                        score_float = float(score)
                                        # 0-1 범위면 100을 곱함
                                        if 0 <= score_float <= 1:
                                            score_value = round(score_float * 100, 2)
                                        # 이미 0-100 범위면 그대로 사용
                                        elif 0 <= score_float <= 100:
                                            score_value = round(score_float, 2)
                                    except (ValueError, TypeError):
                                        score_value = None
                                
                                print(f"  INSERT: SESSION_ID={session_id_for_normalized_insert}, PRODUCT_ID={product_id_int}, CATEGORY={category_name}, RANK_ORDER={rank_order}, SCORE={score_value}", flush=True)
                                cur.execute("""
                                    INSERT INTO ONBOARD_SESS_REC_PRODUCTS (SESSION_ID, PRODUCT_ID, CATEGORY_NAME, RANK_ORDER, SCORE, CREATED_AT)
                                    VALUES (:session_id, :product_id, :category_name, :rank_order, :score, SYSDATE)
                                """, {
                                    'session_id': session_id_for_normalized_insert,
                                    'product_id': product_id_int,
                                    'category_name': category_name,
                                    'rank_order': rank_order,
                                    'score': score_value
                                })
                        else:
                            print(f"[Oracle DB] ⚠️ recommended_products가 비어있어서 INSERT 실행 안됨 (INSERT 블록)", flush=True)
                    
                    print(f"\n{'='*80}", flush=True)
                    print(f"[create_or_update_session] 커밋 실행 전 상태", flush=True)
                    print(f"{'='*80}", flush=True)
                    print(f"  rows_updated = {rows_updated}", flush=True)
                    print(f"  rows_inserted = {rows_inserted}", flush=True)
                    print(f"  SESSION_ID = {session_id}", flush=True)
                    print(f"  [커밋 실행 중...]", flush=True)
                    try:
                        conn.commit()
                        print(f"  [커밋 완료!]", flush=True)
                        print(f"    ✅ 트랜잭션이 성공적으로 커밋되었습니다.", flush=True)
                    except Exception as commit_error:
                        print(f"  [커밋 실행 중 예외 발생!]", flush=True)
                        print(f"    예외 타입: {type(commit_error).__name__}", flush=True)
                        print(f"    예외 메시지: {str(commit_error)}", flush=True)
                        import traceback
                        print(f"    트레이스백:", flush=True)
                        traceback.print_exc()
                        raise
                    
                    # 커밋 후 실제로 저장되었는지 확인
                    try:
                        cur.execute("""
                            SELECT SESSION_ID, CURRENT_STEP, STATUS, VIBE, HOUSING_TYPE, PYUNG
                            FROM ONBOARDING_SESSION 
                            WHERE SESSION_ID = :session_id
                        """, {'session_id': session_id})
                        verify_result = cur.fetchone()
                        if verify_result:
                            print(f"[create_or_update_session] ✅ 저장 확인 성공!", flush=True)
                            print(f"  SESSION_ID={verify_result[0]}, STEP={verify_result[1]}, STATUS={verify_result[2]}", flush=True)
                            print(f"  VIBE={verify_result[3]}, HOUSING_TYPE={verify_result[4]}, PYUNG={verify_result[5]}", flush=True)
                        else:
                            print(f"[create_or_update_session] ⚠️ 경고: 커밋 후에도 데이터를 찾을 수 없습니다!", flush=True)
                    except Exception as e:
                        print(f"[create_or_update_session] 저장 확인 중 오류: {str(e)}", flush=True)
                    
                    print(f"\n{'='*80}", flush=True)
                    print(f"[create_or_update_session] ✅ Oracle DB 저장 성공", flush=True)
                    print(f"{'='*80}", flush=True)
                    print(f"  SESSION_ID: {session_id}", flush=True)
                    print(f"  UPDATE: {rows_updated}개 행", flush=True)
                    print(f"  INSERT: {rows_inserted}개 행", flush=True)
                    print(f"{'='*80}\n", flush=True)
                    
                    print(f"[create_or_update_session] session_id={session_id} 반환", flush=True)
                    return session_id
        except Exception as e:
            error_type = type(e).__name__
            error_message = str(e)
            # Oracle 에러 코드 추출 (예: ORA-00904)
            error_code = ""
            if "ORA-" in error_message:
                import re
                match = re.search(r'ORA-\d+', error_message)
                if match:
                    error_code = match.group()
            
            print(f"\n{'='*80}", flush=True)
            print(f"[create_or_update_session] ❌ Oracle DB 저장 실패", flush=True)
            print(f"{'='*80}", flush=True)
            print(f"  SESSION_ID: {session_id if 'session_id' in locals() else 'N/A'}", flush=True)
            if error_code:
                print(f"  에러 코드: {error_code}", flush=True)
                if error_code == 'ORA-02291':
                    print(f"  ⚠️ 외래키 제약조건 위반: 참조하는 부모 키가 존재하지 않습니다.", flush=True)
                    print(f"     가능한 원인:", flush=True)
                    print(f"     1. MEMBER_ID가 MEMBER 테이블에 존재하지 않음", flush=True)
                    print(f"     2. PRODUCT_ID가 PRODUCT 테이블에 존재하지 않음 (정규화 테이블)", flush=True)
                    print(f"     3. 다른 외래키 제약조건 위반", flush=True)
                    print(f"     해결 방법:", flush=True)
                    print(f"     - MEMBER_ID는 NULL 허용이므로 NULL로 설정됨", flush=True)
                    print(f"     - 유효한 MEMBER_ID를 사용하거나", flush=True)
                    print(f"     - 'GUEST' 멤버를 생성하려면 create_guest_member.py 실행", flush=True)
            print(f"  에러 타입: {error_type}", flush=True)
            print(f"  에러 메시지: {error_message}", flush=True)
            if 'rows_updated' in locals():
                print(f"  rows_updated: {rows_updated}", flush=True)
            if 'rows_inserted' in locals():
                print(f"  rows_inserted: {rows_inserted}", flush=True)
            import traceback
            print(f"  [전체 트레이스백]", flush=True)
            traceback.print_exc()
            print(f"{'='*80}\n", flush=True)
            raise
    
    @staticmethod
    def save_user_response(session_id, step_number, question_type, answer_value, answer_text=None, question_id=None, answer_id=None):
        """
        사용자 응답 저장
        
        Args:
            session_id: 세션 ID
            step_number: 단계 번호
            question_type: 질문 유형 (vibe, mate, pet, housing_type, main_space, pyung, cooking, laundry, media, priority, budget)
            answer_value: 선택한 값
            answer_text: 텍스트 입력 값 (평수 등)
            question_id: 질문 ID (선택적, 자동 조회)
            answer_id: 답변 ID (선택적, 자동 조회)
        """
        with get_connection() as conn:
            with conn.cursor() as cur:
                # ONBOARDING_QUESTION 테이블 존재 여부 확인
                try:
                    cur.execute("""
                        SELECT COUNT(*) FROM USER_TABLES WHERE TABLE_NAME = 'ONBOARDING_QUESTION'
                    """)
                    table_exists = cur.fetchone()[0] > 0
                    
                    if not table_exists:
                        print(f"[save_user_response] ⚠️ ONBOARDING_QUESTION 테이블이 존재하지 않습니다. 응답 저장을 건너뜁니다.", flush=True)
                        return
                    
                    # STEP_NUMBER 컬럼 존재 여부 확인
                    cur.execute("""
                        SELECT COUNT(*) FROM USER_TAB_COLUMNS 
                        WHERE TABLE_NAME = 'ONBOARDING_QUESTION' AND COLUMN_NAME = 'STEP_NUMBER'
                    """)
                    column_exists = cur.fetchone()[0] > 0
                    
                    if not column_exists:
                        print(f"[save_user_response] ⚠️ ONBOARDING_QUESTION 테이블에 STEP_NUMBER 컬럼이 없습니다. 응답 저장을 건너뜁니다.", flush=True)
                        return
                except Exception as e:
                    print(f"[save_user_response] ⚠️ 테이블 확인 중 오류: {e}. 응답 저장을 건너뜁니다.", flush=True)
                    return
                
                # question_id가 없으면 자동 조회
                if not question_id:
                    try:
                        cur.execute("""
                            SELECT QUESTION_ID FROM ONBOARDING_QUESTION
                            WHERE STEP_NUMBER = :step_number AND QUESTION_TYPE = :question_type
                            AND ROWNUM = 1
                        """, {
                            'step_number': step_number,
                            'question_type': question_type
                        })
                        result = cur.fetchone()
                        if result:
                            question_id = result[0]
                        else:
                            print(f"[save_user_response] ⚠️ Question not found: step={step_number}, type={question_type}. 응답 저장을 건너뜁니다.", flush=True)
                            return
                    except Exception as e:
                        print(f"[save_user_response] ⚠️ Question 조회 중 오류: {e}. 응답 저장을 건너뜁니다.", flush=True)
                        return
                
                # answer_id가 없고 answer_value가 있으면 자동 조회
                if not answer_id and answer_value:
                    cur.execute("""
                        SELECT ANSWER_ID FROM ONBOARDING_ANSWER
                        WHERE QUESTION_ID = :question_id AND ANSWER_VALUE = :answer_value
                        AND ROWNUM = 1
                    """, {
                        'question_id': question_id,
                        'answer_value': answer_value
                    })
                    result = cur.fetchone()
                    if result:
                        answer_id = result[0]
                
                # 기존 응답이 있는지 확인 (같은 세션, 같은 질문)
                cur.execute("""
                    SELECT RESPONSE_ID FROM ONBOARDING_USER_RESPONSE
                    WHERE SESSION_ID = :session_id AND QUESTION_ID = :question_id
                    AND ROWNUM = 1
                """, {
                    'session_id': session_id,
                    'question_id': question_id
                })
                existing = cur.fetchone()
                
                if existing:
                    # 업데이트
                    print(f"[Oracle DB] ONBOARDING_USER_RESPONSE 테이블 UPDATE", flush=True)
                    print(f"  WHERE RESPONSE_ID={existing[0]}, SESSION_ID={session_id}, QUESTION_ID={question_id}", flush=True)
                    print(f"  SET: ANSWER_ID={answer_id}, ANSWER_VALUE={answer_value}, RESPONSE_TEXT={answer_text}", flush=True)
                    cur.execute("""
                        UPDATE ONBOARDING_USER_RESPONSE SET
                            ANSWER_ID = :answer_id,
                            ANSWER_VALUE = :answer_value,
                            RESPONSE_TEXT = :response_text,
                            CURRENT_STEP = :step_number
                        WHERE RESPONSE_ID = :response_id
                    """, {
                        'response_id': existing[0],
                        'answer_id': answer_id,
                        'answer_value': answer_value,
                        'response_text': answer_text,
                        'step_number': step_number
                    })
                else:  # 생성
                    print(f"[Oracle DB] ONBOARDING_USER_RESPONSE 테이블 INSERT", flush=True)
                    print(f"  SESSION_ID={session_id}, QUESTION_ID={question_id}, ANSWER_ID={answer_id}", flush=True)
                    print(f"  ANSWER_VALUE={answer_value}, RESPONSE_TEXT={answer_text}", flush=True)
                    
                    # 시퀀스 존재 여부 확인
                    cur.execute("""
                        SELECT COUNT(*) FROM USER_SEQUENCES 
                        WHERE SEQUENCE_NAME = 'SEQ_ONBOARDING_USER_RESPONSE'
                    """)
                    has_sequence = cur.fetchone()[0] > 0
                    
                    # RESPONSE_ID 생성 방법 결정
                    if has_sequence:
                        response_id_sql = "SEQ_ONBOARDING_USER_RESPONSE.NEXTVAL"
                    else:
                        # 시퀀스가 없으면 MAX+1 사용
                        try:
                            cur.execute("SELECT NVL(MAX(RESPONSE_ID), 0) + 1 FROM ONBOARDING_USER_RESPONSE")
                            next_id = cur.fetchone()[0]
                            response_id_sql = str(next_id)
                        except:
                            response_id_sql = "1"  # 기본값
                    
                    cur.execute(f"""
                        INSERT INTO ONBOARDING_USER_RESPONSE (
                            RESPONSE_ID, SESSION_ID, QUESTION_CODE, ANSWER_ID,
                            INPUT_VALUE, CREATED_DATE
                        ) VALUES (
                            {response_id_sql},
                            :session_id, :question_id, :answer_id,
                            :answer_value, :response_text,  SYSDATE
                        )
                    """, {
                        'session_id': session_id,
                        'question_id': question_id,
                        'answer_id': answer_id,
                        'answer_value': answer_value,
                        'response_text': answer_text
                    })
                
                conn.commit()
                return True
    
    @staticmethod
    def save_multiple_responses(session_id, step_number, question_type, answer_values):
        """
        다중 선택 응답 저장 (main_space, priority 등)
        
        Args:
            session_id: 세션 ID
            step_number: 단계 번호
            question_type: 질문 유형
            answer_values: 선택한 값 리스트
        """
        # 기존 응답 삭제 (같은 세션, 같은 질문 타입)
        with get_connection() as conn:
            with conn.cursor() as cur:
                # 질문 CODE 조회 (ERD 기준: QUESTION_CODE가 PK)
                # STEP_NUMBER가 없으면 QUESTION_TYPE만으로 조회
                try:
                    # 먼저 STEP_NUMBER 컬럼 존재 여부 확인
                    cur.execute("""
                        SELECT COUNT(*) FROM USER_TAB_COLUMNS 
                        WHERE TABLE_NAME = 'ONBOARDING_QUESTION' AND COLUMN_NAME = 'STEP_NUMBER'
                    """)
                    has_step_number = cur.fetchone()[0] > 0
                    
                    if has_step_number:
                        # STEP_NUMBER가 있으면 사용
                        cur.execute("""
                            SELECT QUESTION_CODE FROM ONBOARDING_QUESTION
                            WHERE STEP_NUMBER = :step_number AND QUESTION_TYPE = :question_type
                            AND ROWNUM = 1
                        """, {
                            'step_number': step_number,
                            'question_type': question_type
                        })
                    else:
                        # STEP_NUMBER가 없으면 QUESTION_TYPE만으로 조회
                        cur.execute("""
                            SELECT QUESTION_CODE FROM ONBOARDING_QUESTION
                            WHERE QUESTION_TYPE = :question_type
                            AND ROWNUM = 1
                        """, {
                            'question_type': question_type
                        })
                    
                    result = cur.fetchone()
                    if not result:
                        # QUESTION_CODE가 없으면 QUESTION_ID 시도 (하위 호환성)
                        if has_step_number:
                            cur.execute("""
                                SELECT QUESTION_ID FROM ONBOARDING_QUESTION
                                WHERE STEP_NUMBER = :step_number AND QUESTION_TYPE = :question_type
                                AND ROWNUM = 1
                            """, {
                                'step_number': step_number,
                                'question_type': question_type
                            })
                        else:
                            cur.execute("""
                                SELECT QUESTION_ID FROM ONBOARDING_QUESTION
                                WHERE QUESTION_TYPE = :question_type
                                AND ROWNUM = 1
                            """, {
                                'question_type': question_type
                            })
                        result = cur.fetchone()
                        if not result:
                            raise ValueError(f"Question not found: step={step_number}, type={question_type}")
                except Exception as e:
                    print(f"[save_multiple_responses] ⚠️ 질문 조회 중 오류: {e}. 응답 저장을 건너뜁니다.", flush=True)
                    return
                
                question_id = result[0]
                
                # 기존 응답 삭제 (QUESTION_CODE 또는 QUESTION_ID 사용 가능하도록)
                try:
                    # QUESTION_CODE 컬럼 존재 여부 확인
                    cur.execute("""
                        SELECT COUNT(*) FROM USER_TAB_COLUMNS 
                        WHERE TABLE_NAME = 'ONBOARDING_USER_RESPONSE' AND COLUMN_NAME = 'QUESTION_CODE'
                    """)
                    has_question_code = cur.fetchone()[0] > 0
                    
                    if has_question_code:
                        cur.execute("""
                            DELETE FROM ONBOARDING_USER_RESPONSE
                            WHERE SESSION_ID = :session_id AND QUESTION_CODE = :question_id
                        """, {
                            'session_id': session_id,
                            'question_id': question_id
                        })
                    else:
                        cur.execute("""
                            DELETE FROM ONBOARDING_USER_RESPONSE
                            WHERE SESSION_ID = :session_id AND QUESTION_ID = :question_id
                        """, {
                            'session_id': session_id,
                            'question_id': question_id
                        })
                except Exception as e:
                    print(f"[save_multiple_responses] ⚠️ 기존 응답 삭제 중 오류: {e}", flush=True)
                
                # 새 응답 저장
                for answer_value in answer_values:
                    # answer_id 조회 (QUESTION_ID 또는 QUESTION_CODE 사용)
                    try:
                        # ONBOARDING_ANSWER 테이블의 FK 컬럼 확인
                        cur.execute("""
                            SELECT COLUMN_NAME FROM USER_CONS_COLUMNS
                            WHERE TABLE_NAME = 'ONBOARDING_ANSWER' 
                              AND CONSTRAINT_NAME IN (
                                  SELECT CONSTRAINT_NAME FROM USER_CONSTRAINTS 
                                  WHERE CONSTRAINT_TYPE = 'R' 
                                    AND TABLE_NAME = 'ONBOARDING_ANSWER'
                              )
                              AND POSITION = 1
                        """)
                        fk_result = cur.fetchone()
                        fk_column = fk_result[0] if fk_result else 'QUESTION_ID'
                        
                        if fk_column == 'QUESTION_CODE':
                            cur.execute("""
                                SELECT ANSWER_ID FROM ONBOARDING_ANSWER
                                WHERE QUESTION_CODE = :question_id AND ANSWER_VALUE = :answer_value
                                AND ROWNUM = 1
                            """, {
                                'question_id': question_id,
                                'answer_value': answer_value
                            })
                        else:
                            cur.execute("""
                                SELECT ANSWER_ID FROM ONBOARDING_ANSWER
                                WHERE QUESTION_ID = :question_id AND ANSWER_VALUE = :answer_value
                                AND ROWNUM = 1
                            """, {
                                'question_id': question_id,
                                'answer_value': answer_value
                            })
                        result = cur.fetchone()
                        answer_id = result[0] if result else None
                    except Exception as e:
                        print(f"[save_multiple_responses] ⚠️ ANSWER_ID 조회 중 오류: {e}", flush=True)
                        answer_id = None
                    
                    # INSERT (ERD 기준: QUESTION_CODE, CREATED_AT 사용)
                    try:
                        # 컬럼 존재 여부 확인
                        cur.execute("""
                            SELECT COLUMN_NAME FROM USER_TAB_COLUMNS
                            WHERE TABLE_NAME = 'ONBOARDING_USER_RESPONSE'
                            ORDER BY COLUMN_ID
                        """)
                        columns = [row[0] for row in cur.fetchall()]
                        
                        has_question_code = 'QUESTION_CODE' in columns
                        has_created_at = 'CREATED_AT' in columns
                        
                        # 시퀀스 존재 여부 확인
                        cur.execute("""
                            SELECT COUNT(*) FROM USER_SEQUENCES 
                            WHERE SEQUENCE_NAME = 'SEQ_ONBOARDING_USER_RESPONSE'
                        """)
                        has_sequence = cur.fetchone()[0] > 0
                        
                        # RESPONSE_ID 생성 방법 결정
                        if has_sequence:
                            response_id_sql = "SEQ_ONBOARDING_USER_RESPONSE.NEXTVAL"
                        else:
                            # 시퀀스가 없으면 MAX+1 사용
                            try:
                                cur.execute("SELECT NVL(MAX(RESPONSE_ID), 0) + 1 FROM ONBOARDING_USER_RESPONSE")
                                next_id = cur.fetchone()[0]
                                response_id_sql = str(next_id)
                            except:
                                response_id_sql = "1"  # 기본값
                        
                        if has_question_code:
                            if has_created_at:
                                cur.execute(f"""
                                    INSERT INTO ONBOARDING_USER_RESPONSE (
                                        RESPONSE_ID, SESSION_ID, QUESTION_CODE, ANSWER_ID,
                                        INPUT_VALUE, CREATED_AT
                                    ) VALUES (
                                        {response_id_sql},
                                        :session_id, :question_id, :answer_id,
                                        :answer_value, SYSDATE
                                    )
                                """, {
                                    'session_id': session_id,
                                    'question_id': question_id,
                                    'answer_id': answer_id,
                                    'answer_value': answer_value
                                })
                            else:
                                cur.execute(f"""
                                    INSERT INTO ONBOARDING_USER_RESPONSE (
                                        RESPONSE_ID, SESSION_ID, QUESTION_CODE, ANSWER_ID,
                                        INPUT_VALUE, CREATED_DATE
                                    ) VALUES (
                                        {response_id_sql},
                                        :session_id, :question_id, :answer_id,
                                        :answer_value, SYSDATE
                                    )
                                """, {
                                    'session_id': session_id,
                                    'question_id': question_id,
                                    'answer_id': answer_id,
                                    'answer_value': answer_value
                                })
                        else:
                            # QUESTION_ID 사용
                            if has_created_at:
                                cur.execute(f"""
                                    INSERT INTO ONBOARDING_USER_RESPONSE (
                                        RESPONSE_ID, SESSION_ID, QUESTION_ID, ANSWER_ID,
                                        INPUT_VALUE, CREATED_AT
                                    ) VALUES (
                                        {response_id_sql},
                                        :session_id, :question_id, :answer_id,
                                        :answer_value, SYSDATE
                                    )
                                """, {
                                    'session_id': session_id,
                                    'question_id': question_id,
                                    'answer_id': answer_id,
                                    'answer_value': answer_value
                                })
                            else:
                                cur.execute(f"""
                                    INSERT INTO ONBOARDING_USER_RESPONSE (
                                        RESPONSE_ID, SESSION_ID, QUESTION_ID, ANSWER_ID,
                                        INPUT_VALUE, CREATED_DATE
                                    ) VALUES (
                                        {response_id_sql},
                                        :session_id, :question_id, :answer_id,
                                        :answer_value, SYSDATE
                                    )
                                """, {
                                    'session_id': session_id,
                                    'question_id': question_id,
                                    'answer_id': answer_id,
                                    'answer_value': answer_value
                                })
                    except Exception as e:
                        print(f"[save_multiple_responses] ⚠️ 응답 저장 중 오류: {e}", flush=True)
                        continue
                
                conn.commit()
                return True
    
    @staticmethod
    def get_session(session_id):
        """
        세션 정보 조회 (정규화 테이블에서 데이터 읽기)
        """
        result = fetch_one("""
            SELECT * FROM ONBOARDING_SESSION 
            WHERE SESSION_ID = :session_id
            ORDER BY MEMBER_ID ASC
        """, {'session_id': session_id})
        
        if not result:
            return None
        
        # 컬럼명 가져오기
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM ONBOARDING_SESSION WHERE SESSION_ID = :session_id ORDER BY MEMBER_ID ASC", {'session_id': session_id})
                cols = [c[0] for c in cur.description]
                session_dict = dict(zip(cols, result))
                
                # 정규화 테이블에서 데이터 읽기
                # MAIN_SPACE
                cur.execute("""
                    SELECT MAIN_SPACE FROM ONBOARD_SESS_MAIN_SPACES
                    WHERE SESSION_ID = :session_id
                    ORDER BY MAIN_SPACE
                """, {'session_id': session_id})
                main_spaces = [row[0] for row in cur.fetchall()]
                session_dict['MAIN_SPACE'] = json.dumps(main_spaces, ensure_ascii=False) if main_spaces else None
                
                # PRIORITY_LIST
                cur.execute("""
                    SELECT PRIORITY FROM ONBOARD_SESS_PRIORITIES
                    WHERE SESSION_ID = :session_id
                    ORDER BY PRIORITY_ORDER
                """, {'session_id': session_id})
                priorities = [row[0] for row in cur.fetchall()]
                session_dict['PRIORITY_LIST'] = json.dumps(priorities, ensure_ascii=False) if priorities else None
                
                # SELECTED_CATEGORIES
                cur.execute("""
                    SELECT CATEGORY_NAME FROM ONBOARD_SESS_CATEGORIES
                    WHERE SESSION_ID = :session_id
                    ORDER BY CATEGORY_NAME
                """, {'session_id': session_id})
                categories = [row[0] for row in cur.fetchall()]
                session_dict['SELECTED_CATEGORIES'] = categories
                
                # RECOMMENDED_PRODUCTS
                cur.execute("""
                    SELECT PRODUCT_ID FROM ONBOARD_SESS_REC_PRODUCTS
                    WHERE SESSION_ID = :session_id
                    ORDER BY RANK_ORDER
                """, {'session_id': session_id})
                products = [row[0] for row in cur.fetchall()]
                session_dict['RECOMMENDED_PRODUCTS'] = products
                
                # RECOMMENDATION_RESULT 필드 제거됨 (CLOB 제거)
                
                return session_dict
    
    @staticmethod
    def get_user_responses(session_id, step_number=None):
        """
        사용자 응답 조회
        """
        if step_number:
            sql = """
                SELECT r.*, q.QUESTION_TYPE, q.QUESTION_TEXT, a.ANSWER_TEXT
                FROM ONBOARDING_USER_RESPONSE r
                JOIN ONBOARDING_QUESTION q ON r.QUESTION_ID = q.QUESTION_ID
                LEFT JOIN ONBOARDING_ANSWER a ON r.ANSWER_ID = a.ANSWER_ID
                WHERE r.SESSION_ID = :session_id AND r.STEP_NUMBER = :step_number
                ORDER BY r.STEP_NUMBER, q.QUESTION_ORDER
            """
            params = {'session_id': session_id, 'step_number': step_number}
        else:
            sql = """
                SELECT r.*, q.QUESTION_TYPE, q.QUESTION_TEXT, a.ANSWER_TEXT
                FROM ONBOARDING_USER_RESPONSE r
                JOIN ONBOARDING_QUESTION q ON r.QUESTION_ID = q.QUESTION_ID
                LEFT JOIN ONBOARDING_ANSWER a ON r.ANSWER_ID = a.ANSWER_ID
                WHERE r.SESSION_ID = :session_id
                ORDER BY r.STEP_NUMBER, q.QUESTION_ORDER
            """
            params = {'session_id': session_id}
        
        return fetch_all_dict(sql, params)


# 싱글톤 인스턴스
onboarding_db_service = OnboardingDBService()

