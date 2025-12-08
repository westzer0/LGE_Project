#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
MEMBER 테이블에 더미 데이터 1000명 생성 스크립트

AGE: 평균 35, 표준편차 8인 정규분포에서 샘플링, 18~70 사이로 클리핑
POINT: 평균 10000, 표준편차 3000인 정규분포에서 샘플링, 0 미만은 0으로
"""

import os
import sys
from pathlib import Path
import random
import string
import re
from datetime import datetime, timedelta
import numpy as np

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

import django
django.setup()

from api.db.oracle_client import get_connection

# ============================================================
# 분포 파라미터 상수 정의
# ============================================================
# AGE 분포 파라미터
AGE_MEAN = 35
AGE_STD = 8
AGE_MIN = 18
AGE_MAX = 70

# POINT 분포 파라미터
POINT_MEAN = 10000
POINT_STD = 3000
POINT_MIN = 0

# 생성할 데이터 개수
NUM_MEMBERS = 1000

# ============================================================
# 랜덤 데이터 생성 함수
# ============================================================

# 한국 성씨 리스트
KOREAN_SURNAMES = [
    '김', '이', '박', '최', '정', '강', '조', '윤', '장', '임',
    '한', '오', '서', '신', '권', '황', '안', '송', '류', '전',
    '홍', '고', '문', '양', '손', '배', '조', '백', '허', '유',
    '남', '심', '노', '정', '하', '곽', '성', '차', '주', '우',
    '구', '신', '임', '나', '전', '민', '유', '진', '지', '엄',
    '채', '원', '천', '방', '공', '강', '현', '함', '변', '염',
    '양', '변', '여', '추', '노', '도', '소', '신', '석', '선',
    '설', '마', '길', '주', '연', '방', '위', '표', '명', '기',
    '반', '왕', '금', '옥', '육', '인', '맹', '제', '모', '장',
    '남', '탁', '국', '여', '진', '어', '은', '편', '견', '추',
    '가', '경', '고', '공', '곽', '관', '교', '구', '국', '군',
    '궉', '권', '금', '기', '길', '김', '나', '남', '노', '뇌',
    '다', '단', '당', '대', '도', '독', '동', '두', '라', '래',
    '로', '뢰', '류', '리', '마', '만', '매', '맹', '명', '모',
    '목', '문', '미', '민', '박', '반', '방', '배', '백', '범',
    '변', '보', '복', '봉', '부', '비', '빈', '사', '산', '삼',
    '상', '서', '석', '선', '설', '섭', '성', '소', '손', '송',
    '수', '순', '승', '시', '신', '심', '아', '안', '애', '야',
    '양', '어', '엄', '여', '연', '영', '예', '오', '옥', '온',
    '완', '왕', '요', '용', '우', '운', '원', '위', '유', '육',
    '윤', '은', '음', '의', '이', '인', '임', '자', '잠', '장',
    '재', '전', '정', '제', '조', '종', '주', '준', '중', '지',
    '진', '차', '찬', '창', '채', '천', '철', '청', '초', '최',
    '추', '춘', '충', '탁', '탄', '태', '판', '팽', '편', '평',
    '포', '표', '풍', '피', '필', '하', '한', '함', '해', '허',
    '현', '형', '호', '홍', '화', '황', '후', '훈', '흥', '희'
]

# 한국 이름(이름 부분) 리스트
KOREAN_GIVEN_NAMES = [
    '민준', '서준', '도윤', '예준', '시우', '하준', '주원', '지호', '준서', '건우',
    '현우', '우진', '선우', '연우', '정우', '승우', '지훈', '유준', '승현', '준혁',
    '시윤', '지우', '동현', '준영', '성민', '은우', '재윤', '민성', '준호', '시현',
    '지원', '윤서', '하람', '지안', '서진', '예성', '민재', '준수', '은찬', '도현',
    '서연', '서윤', '지우', '서현', '민서', '하은', '예은', '윤서', '채원', '지원',
    '지유', '수아', '지은', '소율', '예린', '시은', '유나', '채은', '지안', '하린',
    '서아', '예나', '다은', '윤아', '소은', '지율', '예원', '나은', '하연', '서영',
    '민지', '예진', '채윤', '지수', '은서', '수민', '예지', '하영', '서우', '지하',
    '윤지', '소연', '예서', '채린', '지연', '하율', '서율', '예린', '민주', '지율',
    '서하', '예원', '하은', '지은', '서은', '예은', '채원', '하린', '서린', '예린',
    '민경', '지혜', '서영', '예영', '하영', '지영', '서진', '예진', '민진', '채진',
    '하진', '서진', '예진', '지진', '민진', '채진', '하진', '서진', '예진', '지진'
]

# 취향 태그 리스트
TASTE_TAGS = [
    '미니멀', '모던', '빈티지', '내추럴', '인더스트리얼', '스칸디나비아', '로맨틱', '클래식',
    '럭셔리', '컨템포러리', '프로방스', '아시아틱', '보헤미안', '아르데코', '팝아트', '레트로',
    '심플', '엘레강트', '캐주얼', '세련', '따뜻한', '시원한', '컬러풀', '모노톤',
    '우드톤', '화이트톤', '그레이톤', '파스텔', '비비드', '어스톤', '네이비', '블랙',
    '가구중심', '액세서리중심', '조명중심', '커튼중심', '벽지중심', '바닥중심', '수납중심', '장식중심'
]


def generate_korean_name():
    """한국 이름 생성"""
    surname = random.choice(KOREAN_SURNAMES)
    given_name = random.choice(KOREAN_GIVEN_NAMES)
    return f"{surname}{given_name}"


def generate_password(length=12):
    """랜덤 비밀번호 생성"""
    chars = string.ascii_letters + string.digits + "!@#$%^&*"
    return ''.join(random.choice(chars) for _ in range(length))


def generate_phone_number():
    """한국 전화번호 생성 (010-XXXX-XXXX)"""
    middle = random.randint(1000, 9999)
    last = random.randint(1000, 9999)
    return f"010-{middle}-{last}"


def generate_profile_image_url():
    """프로필 이미지 URL 생성"""
    image_id = random.randint(1, 1000)
    return f"https://example.com/profile/{image_id}.jpg"


def generate_taste_tags():
    """취향 태그 생성 (1~3개 랜덤 선택)"""
    num_tags = random.randint(1, 3)
    selected_tags = random.sample(TASTE_TAGS, num_tags)
    return ','.join(selected_tags)


def generate_age():
    """AGE 생성: 평균 35, 표준편차 8, 18~70 사이 클리핑"""
    age = np.random.normal(AGE_MEAN, AGE_STD)
    age = int(np.clip(age, AGE_MIN, AGE_MAX))
    return age


def generate_point():
    """POINT 생성: 평균 10000, 표준편차 3000, 0 미만은 0으로"""
    point = np.random.normal(POINT_MEAN, POINT_STD)
    point = max(int(point), POINT_MIN)
    return point


def generate_gender():
    """성별 생성 ('M' 또는 'F')"""
    return random.choice(['M', 'F'])


def generate_created_date():
    """생성일시 생성 (최근 1년 내 랜덤)"""
    days_ago = random.randint(0, 365)
    created_date = datetime.now() - timedelta(days=days_ago)
    return created_date


def generate_member_id():
    """MEMBER_ID 생성 (시퀀스 사용하지 않고 랜덤 숫자)"""
    # 실제로는 시퀀스를 사용하지만, 여기서는 큰 랜덤 숫자 사용
    # DB에서 시퀀스를 사용한다면 이 함수는 사용하지 않음
    return random.randint(1000000, 9999999)


def generate_members(num_members):
    """더미 회원 데이터 생성"""
    members = []
    
    for i in range(num_members):
        # MEMBER_ID는 시퀀스를 사용하므로 None으로 설정 (DB에서 자동 생성)
        # 또는 시퀀스가 없다면 generate_member_id() 사용
        member = (
            None,  # MEMBER_ID (시퀀스 사용 시 None)
            generate_password(),
            generate_korean_name(),
            generate_age(),
            generate_gender(),
            generate_phone_number(),
            generate_profile_image_url(),
            generate_point(),
            generate_created_date(),
            generate_taste_tags()
        )
        members.append(member)
    
    return members


def get_member_id_column_type():
    """MEMBER 테이블의 MEMBER_ID 컬럼 타입 확인"""
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT DATA_TYPE, DATA_LENGTH
                    FROM USER_TAB_COLUMNS
                    WHERE TABLE_NAME = 'MEMBER' AND COLUMN_NAME = 'MEMBER_ID'
                """)
                result = cur.fetchone()
                if result:
                    return result[0]  # DATA_TYPE 반환 (NUMBER, VARCHAR2 등)
                return None
    except Exception as e:
        print(f"[경고] MEMBER_ID 컬럼 타입 확인 중 오류: {e}")
        return None


def get_member_sequence_name():
    """MEMBER 테이블의 시퀀스 이름 확인"""
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                # 가능한 시퀀스 이름들 확인
                possible_names = ['SEQ_MEMBER', 'MEMBER_SEQ', 'MEMBER_ID_SEQ']
                for seq_name in possible_names:
                    cur.execute("""
                        SELECT COUNT(*) FROM USER_SEQUENCES 
                        WHERE SEQUENCE_NAME = :seq_name
                    """, {'seq_name': seq_name})
                    if cur.fetchone()[0] > 0:
                        return seq_name
                return None
    except Exception as e:
        print(f"[경고] 시퀀스 확인 중 오류: {e}")
        return None


def clean_profile_image_url(url):
    """프로필 이미지 URL에서 Markdown 링크 형식 제거
    
    예: "[text](https://example.com/image.jpg)" -> "https://example.com/image.jpg"
    """
    if not url or not isinstance(url, str):
        return ''
    
    # Markdown 링크 형식 [text](url) 처리
    if '](' in url and url.endswith(')'):
        try:
            # ]( 이후의 URL 부분 추출
            url = url.split('](')[1].split(')')[0]
        except (IndexError, ValueError):
            pass
    
    # 특수문자 제거 (괄호 등)
    url = url.strip()
    
    return url


def taste_to_code(taste_str):
    """TASTE 문자열을 숫자 코드로 변환
    
    TASTE 컬럼이 NUMBER 타입인 경우 사용
    문자열을 해시 기반 숫자 코드로 변환하거나 매핑 테이블 사용
    """
    if not taste_str or not isinstance(taste_str, str):
        return 0
    
    # 간단한 해시 기반 코드 생성 (일관성 유지)
    # 또는 매핑 테이블 사용 가능
    taste_str = taste_str.strip()
    if not taste_str:
        return 0
    
    # 해시 기반 코드 생성 (문자열 -> 숫자)
    # 같은 문자열은 항상 같은 숫자로 변환됨
    hash_code = hash(taste_str)
    # 음수 방지 및 범위 제한 (0 ~ 9999999999)
    code = abs(hash_code) % 10000000000
    
    return code


def safe_int_conversion(value, field_name, default=0):
    """안전한 정수 변환 함수"""
    if value is None:
        return default
    
    # 이미 정수형이면 그대로 반환
    if isinstance(value, int):
        return value
    
    # float이면 정수로 변환
    if isinstance(value, float):
        return int(value)
    
    # 문자열인 경우
    if isinstance(value, str):
        value = value.strip()
        # 빈 문자열이나 "N/A" 같은 값 처리
        if not value or value.upper() in ('N/A', 'NULL', 'NONE', ''):
            return default
        
        # 숫자 추출 시도
        try:
            # 소수점이 있으면 float로 변환 후 int
            if '.' in value:
                return int(float(value))
            else:
                return int(value)
        except (ValueError, TypeError):
            # 숫자가 아닌 경우 숫자 부분만 추출
            numbers = re.findall(r'\d+', value)
            if numbers:
                return int(numbers[-1])
            return default
    
    # 그 외 타입은 시도 후 실패 시 기본값
    try:
        return int(float(value))
    except (ValueError, TypeError):
        return default


def get_member_table_schema():
    """MEMBER 테이블의 모든 컬럼 스키마 정보 조회"""
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT 
                        COLUMN_NAME,
                        DATA_TYPE,
                        DATA_LENGTH,
                        DATA_PRECISION,
                        DATA_SCALE,
                        NULLABLE
                    FROM USER_TAB_COLUMNS
                    WHERE TABLE_NAME = 'MEMBER'
                    ORDER BY COLUMN_ID
                """)
                
                schema = {}
                for row in cur.fetchall():
                    col_name, data_type, data_length, data_precision, data_scale, nullable = row
                    schema[col_name.upper()] = {
                        'data_type': data_type,
                        'data_length': data_length,
                        'data_precision': data_precision,
                        'data_scale': data_scale,
                        'nullable': nullable
                    }
                return schema
    except Exception as e:
        print(f"[경고] 테이블 스키마 조회 중 오류: {e}")
        return {}


def insert_members(members):
    """Oracle DB에 회원 데이터 일괄 삽입"""
    # 테이블 스키마 조회
    table_schema = get_member_table_schema()
    if table_schema:
        print("\n[정보] MEMBER 테이블 스키마:")
        for col_name, col_info in table_schema.items():
            data_type = col_info['data_type']
            precision = col_info.get('data_precision')
            scale = col_info.get('data_scale')
            type_str = data_type
            if precision:
                if scale:
                    type_str += f"({precision},{scale})"
                else:
                    type_str += f"({precision})"
            print(f"  {col_name:30s} {type_str}")
    
    # MEMBER_ID 컬럼 타입 확인
    member_id_type = get_member_id_column_type()
    if member_id_type is None:
        # 타입을 확인할 수 없으면 NUMBER로 가정 (일반적인 경우)
        print(f"\n[경고] MEMBER_ID 컬럼 타입을 확인할 수 없습니다. NUMBER 타입으로 가정합니다.")
        member_id_type = 'NUMBER'
    else:
        print(f"\n[정보] MEMBER_ID 컬럼 타입: {member_id_type}")
    
    # 시퀀스 이름 확인
    seq_name = get_member_sequence_name()
    
    # NUMBER 타입 컬럼 확인
    number_columns = set()
    if table_schema:
        for col_name, col_info in table_schema.items():
            if col_info['data_type'] == 'NUMBER':
                number_columns.add(col_name.upper())
        print(f"\n[정보] NUMBER 타입 컬럼: {sorted(number_columns)}")
    
    if seq_name:
        # 시퀀스 사용
        # TO_NUMBER() 제거 - Python에서 숫자 타입으로 직접 처리
        insert_sql = """
            INSERT INTO MEMBER (
                MEMBER_ID,
                PASSWORD,
                NAME,
                AGE,
                GENDER,
                CONTACT,
                POINT,
                CREATED_DATE,
                TASTE
            ) VALUES (
                {seq_name}.NEXTVAL,
                :password,
                :name,
                :age,
                :gender,
                :contact,
                :point,
                :created_date,
                :taste
            )
        """.format(seq_name=seq_name)
        print(f"[정보] 시퀀스 사용: {seq_name}")
    else:
        # 시퀀스 없음 - MEMBER_ID는 수동 생성
        # MEMBER_ID 컬럼 타입에 따라 처리
        try:
            with get_connection() as conn:
                with conn.cursor() as cur:
                    if member_id_type == 'NUMBER':
                        # NUMBER 타입: 정수만 사용
                        try:
                            cur.execute("SELECT NVL(MAX(MEMBER_ID), 0) FROM MEMBER")
                            result = cur.fetchone()[0]
                            max_id_num = int(result) if result is not None else 0
                        except:
                            # NUMBER 컬럼에 문자열이 들어가 있어서 오류가 나는 경우
                            # 모든 레코드를 확인해서 숫자만 추출
                            cur.execute("SELECT MEMBER_ID FROM MEMBER")
                            all_ids = cur.fetchall()
                            numeric_ids = []
                            for row in all_ids:
                                try:
                                    numeric_ids.append(int(row[0]))
                                except (ValueError, TypeError):
                                    # 문자열이면 숫자 부분 추출
                                    if isinstance(row[0], str):
                                        numbers = re.findall(r'\d+', row[0])
                                        if numbers:
                                            numeric_ids.append(int(numbers[-1]))
                            max_id_num = max(numeric_ids) if numeric_ids else 0
                        print(f"[정보] 시퀀스 없음. 현재 최대 MEMBER_ID (NUMBER): {max_id_num}")
                    else:
                        # VARCHAR2 타입: 문자열에서 숫자 추출
                        cur.execute("SELECT NVL(MAX(MEMBER_ID), '0') FROM MEMBER")
                        max_id_str = cur.fetchone()[0]
                        print(f"[정보] 시퀀스 없음. 현재 최대 MEMBER_ID: {max_id_str}")
                        if isinstance(max_id_str, str):
                            numbers = re.findall(r'\d+', str(max_id_str))
                            max_id_num = int(numbers[-1]) if numbers else 0
                        else:
                            max_id_num = int(max_id_str) if max_id_str else 0
        except Exception as e:
            print(f"[경고] MEMBER_ID 조회 중 오류: {e}")
            import traceback
            print(traceback.format_exc())
            max_id_num = 0
        
        # MEMBER_ID를 포함한 INSERT
        # TO_NUMBER() 제거 - Python에서 숫자 타입으로 직접 처리
        insert_sql = """
            INSERT INTO MEMBER (
                MEMBER_ID,
                PASSWORD,
                NAME,
                AGE,
                GENDER,
                CONTACT,
                POINT,
                CREATED_DATE,
                TASTE
            ) VALUES (
                :member_id,
                :password,
                :name,
                :age,
                :gender,
                :contact,
                :point,
                :created_date,
                :taste
            )
        """
        # MEMBER_ID 추가 - NUMBER 타입이면 정수만, VARCHAR2면 문자열
        # member_id_type이 None이면 NUMBER로 가정 (안전하게)
        if member_id_type is None:
            print("[경고] MEMBER_ID 타입을 확인할 수 없습니다. NUMBER 타입으로 가정합니다.")
            member_id_type = 'NUMBER'
        
        for i, member in enumerate(members):
            if member_id_type == 'NUMBER':
                # NUMBER 타입: 정수만 사용
                new_member_id = max_id_num + i + 1
            else:
                # VARCHAR2 타입: 문자열 형식 (기존 로직 유지)
                new_member_id = f"user_{max_id_num + i + 1}"
            members[i] = (new_member_id,) + member[1:]
    
    # 데이터를 딕셔너리 리스트로 변환 (타입 보장 및 검증)
    member_dicts = []
    validation_errors = []
    
    print("\n[정보] 데이터 검증 및 타입 변환 중...")
    for idx, member in enumerate(members):
        try:
            # AGE 검증 및 변환 (Python에서 숫자 타입으로 직접 처리)
            age_int = safe_int_conversion(member[3], 'AGE', default=0)
            if age_int < 0 or age_int > 150:
                validation_errors.append(f"레코드 {idx+1}: AGE 범위 초과 ({age_int})")
                age_int = max(0, min(age_int, 150))  # 0~150 사이로 클리핑
            
            # POINT 검증 및 변환 (Python에서 숫자 타입으로 직접 처리)
            point_int = safe_int_conversion(member[7], 'POINT', default=0)
            if point_int < 0:
                validation_errors.append(f"레코드 {idx+1}: POINT 음수값 ({point_int})")
                point_int = 0
            
            # TASTE 처리
            taste_value = None
            if member[9]:
                taste_str = str(member[9]).strip()
                if taste_str:
                    # TASTE 컬럼이 NUMBER 타입이면 숫자 코드로 변환
                    if "TASTE" in number_columns:
                        taste_value = taste_to_code(taste_str)
                    else:
                        # VARCHAR2 타입이면 문자열 그대로 사용
                        taste_value = taste_str
            
            # PROFILE_IMAGE 처리 (Markdown 링크 형식 제거)
            profile_image = None
            if len(member) > 5 and member[5]:  # member[5]는 contact이므로 profile_image는 다른 위치일 수 있음
                # 실제로는 generate_members 함수에서 profile_image가 어디에 있는지 확인 필요
                pass
            
            if seq_name:
                # 시퀀스 사용 시 MEMBER_ID 제외
                member_dict = {
                    'password': str(member[1]) if member[1] else '',
                    'name': str(member[2]) if member[2] else '',
                    'age': age_int,  # 숫자 타입 (int)
                    'gender': str(member[4]) if member[4] else 'M',
                    'contact': str(member[5]) if member[5] else '',
                    'point': point_int,  # 숫자 타입 (int)
                    'created_date': member[8] if member[8] and isinstance(member[8], datetime) else datetime.now(),
                    'taste': taste_value  # NUMBER면 숫자, VARCHAR2면 문자열
                }
            else:
                # 시퀀스 없을 시 MEMBER_ID 포함
                member_id = member[0]
                # MEMBER_ID 타입 보장 및 검증
                if member_id_type == 'NUMBER':
                    # NUMBER 타입: 정수로 변환
                    if isinstance(member_id, str) and member_id.startswith('user_'):
                        # user_1 형식이면 숫자 부분만 추출
                        numbers = re.findall(r'\d+', member_id)
                        if numbers:
                            member_id = int(numbers[-1])
                        else:
                            member_id = max_id_num + idx + 1
                    elif isinstance(member_id, str):
                        # 문자열이면 숫자로 변환 시도
                        member_id = safe_int_conversion(member_id, 'MEMBER_ID', default=0)
                        if member_id <= 0:
                            member_id = max_id_num + idx + 1
                    else:
                        # 이미 숫자이거나 다른 타입
                        member_id = safe_int_conversion(member_id, 'MEMBER_ID', default=0)
                        if member_id <= 0:
                            member_id = max_id_num + idx + 1
                else:
                    # VARCHAR2 타입: 문자열로 변환
                    member_id = str(member_id) if member_id else ''
                
                member_dict = {
                    'member_id': member_id,
                    'password': str(member[1]) if member[1] else '',
                    'name': str(member[2]) if member[2] else '',
                    'age': age_int,  # 숫자 타입 (int)
                    'gender': str(member[4]) if member[4] else 'M',
                    'contact': str(member[5]) if member[5] else '',
                    'point': point_int,  # 숫자 타입 (int)
                    'created_date': member[8] if member[8] and isinstance(member[8], datetime) else datetime.now(),
                    'taste': taste_value  # NUMBER면 숫자, VARCHAR2면 문자열
                }
            
            # 추가 검증: age와 point가 숫자 타입인지 확인
            if not isinstance(member_dict.get('age'), int):
                validation_errors.append(f"레코드 {idx+1}: AGE가 정수가 아님 (타입: {type(member_dict.get('age'))}, 값: {member_dict.get('age')})")
            
            if not isinstance(member_dict.get('point'), int):
                validation_errors.append(f"레코드 {idx+1}: POINT가 정수가 아님 (타입: {type(member_dict.get('point'))}, 값: {member_dict.get('point')})")
            
            # TASTE 검증
            if "TASTE" in number_columns:
                # NUMBER 타입이면 숫자여야 함
                if member_dict.get('taste') is not None and not isinstance(member_dict.get('taste'), int):
                    validation_errors.append(f"레코드 {idx+1}: TASTE가 정수가 아님 (타입: {type(member_dict.get('taste'))}, 값: {member_dict.get('taste')})")
            else:
                # VARCHAR2 타입이면 문자열이어야 함
                if member_dict.get('taste') is not None and not isinstance(member_dict.get('taste'), str):
                    validation_errors.append(f"레코드 {idx+1}: TASTE가 문자열이 아님 (타입: {type(member_dict.get('taste'))}, 값: {member_dict.get('taste')})")
            
            member_dicts.append(member_dict)
        except Exception as e:
            validation_errors.append(f"레코드 {idx+1}: 데이터 변환 중 오류 - {e}")
            import traceback
            print(f"[오류] 레코드 {idx+1} 변환 실패:")
            print(traceback.format_exc())
    
    # 검증 오류가 있으면 출력
    if validation_errors:
        print("\n[경고] 데이터 타입 검증 오류:")
        for error in validation_errors[:20]:  # 최대 20개 출력
            print(f"  - {error}")
        if len(validation_errors) > 20:
            print(f"  ... 외 {len(validation_errors) - 20}개 오류")
        print(f"\n총 {len(validation_errors)}개의 검증 오류가 발견되었습니다.")
        print("\n계속 진행하시겠습니까? (y/n): ", end='')
        if input().lower() != 'y':
            print("취소되었습니다.")
            return False
    
    # INSERT 실행 전 샘플 파라미터 로그 출력
    print("\n" + "=" * 80)
    print("INSERT 실행 전 샘플 파라미터 (첫 5개 레코드)")
    print("=" * 80)
    for i, sample in enumerate(member_dicts[:5]):
        print(f"\n[레코드 {i+1}]")
        for key, value in sample.items():
            value_type = type(value).__name__
            # 값이 너무 길면 잘라서 표시
            value_str = str(value)
            if len(value_str) > 50:
                value_str = value_str[:50] + "..."
            print(f"  {key:20s} = {value_str:30s} (타입: {value_type})")
    
    # 전체 데이터셋 검증 리포트
    print("\n" + "=" * 80)
    print("전체 데이터셋 검증 리포트")
    print("=" * 80)
    # 숫자 타입으로 통계 계산
    age_values = [d.get('age', 0) for d in member_dicts]
    point_values = [d.get('point', 0) for d in member_dicts]
    print(f"AGE: 최소={min(age_values)}, 최대={max(age_values)}, 평균={sum(age_values)/len(age_values):.2f}")
    print(f"POINT: 최소={min(point_values)}, 최대={max(point_values)}, 평균={sum(point_values)/len(point_values):.2f}")
    
    # None이나 잘못된 타입이 있는지 확인 (정수여야 함)
    invalid_ages = [i for i, d in enumerate(member_dicts) if not isinstance(d.get('age'), int)]
    invalid_points = [i for i, d in enumerate(member_dicts) if not isinstance(d.get('point'), int)]
    if invalid_ages:
        print(f"[경고] AGE가 정수가 아닌 레코드: {len(invalid_ages)}개 (인덱스: {invalid_ages[:10]})")
    if invalid_points:
        print(f"[경고] POINT가 정수가 아닌 레코드: {len(invalid_points)}개 (인덱스: {invalid_points[:10]})")
    
    # TASTE 타입 확인
    if "TASTE" in number_columns:
        invalid_tastes = [i for i, d in enumerate(member_dicts) if d.get('taste') is not None and not isinstance(d.get('taste'), int)]
        if invalid_tastes:
            print(f"[경고] TASTE가 정수가 아닌 레코드: {len(invalid_tastes)}개 (인덱스: {invalid_tastes[:10]})")
    else:
        invalid_tastes = [i for i, d in enumerate(member_dicts) if d.get('taste') is not None and not isinstance(d.get('taste'), str)]
        if invalid_tastes:
            print(f"[경고] TASTE가 문자열이 아닌 레코드: {len(invalid_tastes)}개 (인덱스: {invalid_tastes[:10]})")
    
    # oracledb 버전 확인
    try:
        import oracledb
        print(f"\n[정보] oracledb 버전: {oracledb.__version__}")
    except:
        print("\n[경고] oracledb 버전 확인 실패")
    
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                # 첫 레코드 단독 테스트
                if member_dicts:
                    print("\n" + "=" * 80)
                    print("첫 레코드 단독 테스트")
                    print("=" * 80)
                    print("\n[디버깅] 파라미터 타입 확인:")
                    for key, value in member_dicts[0].items():
                        value_type = type(value).__name__
                        value_str = str(value)
                        if len(value_str) > 50:
                            value_str = value_str[:50] + "..."
                        print(f"  {key:20s} = {value_str:30s} (타입: {value_type})")
                    
                    print("\n[정보] 첫 레코드 단독 테스트 실행 중...")
                    try:
                        cur.execute(insert_sql, member_dicts[0])
                        conn.rollback()  # 테스트이므로 롤백
                        print("✓ 첫 레코드 테스트 성공")
                    except Exception as e:
                        print(f"✗ 첫 레코드 테스트 실패: {str(e)}")
                        print("\n[오류 상세]")
                        print(f"SQL: {insert_sql}")
                        print(f"\n파라미터:")
                        for key, value in member_dicts[0].items():
                            print(f"  {key}: {value} (타입: {type(value).__name__})")
                        import traceback
                        print("\n[스택 트레이스]")
                        print(traceback.format_exc())
                        return False
                
                # executemany 사용하여 일괄 삽입
                print(f"\n[정보] {len(member_dicts)}개 레코드 일괄 삽입 중...")
                cur.executemany(insert_sql, member_dicts)
                conn.commit()
                print(f"\n✓ {len(member_dicts)}명의 회원 데이터가 성공적으로 삽입되었습니다.")
                return True
    except Exception as e:
        print(f"\n✗ 오류 발생: {str(e)}")
        import traceback
        print(traceback.format_exc())
        
        # 오류 발생 시 문제가 있는 레코드 찾기
        print("\n[디버깅] 문제 레코드 찾기 중...")
        if "ORA-01722" in str(e):
            print("ORA-01722 오류: 숫자 타입 컬럼에 잘못된 값이 전달되었습니다.")
            print("AGE, POINT, TASTE 필드를 다시 확인합니다...")
            for i, d in enumerate(member_dicts[:10]):  # 처음 10개만 확인
                if not isinstance(d.get('age'), int):
                    print(f"  레코드 {i+1}: AGE = {d.get('age')} (타입: {type(d.get('age'))})")
                if not isinstance(d.get('point'), int):
                    print(f"  레코드 {i+1}: POINT = {d.get('point')} (타입: {type(d.get('point'))})")
                if "TASTE" in number_columns and d.get('taste') is not None and not isinstance(d.get('taste'), int):
                    print(f"  레코드 {i+1}: TASTE = {d.get('taste')} (타입: {type(d.get('taste'))})")
        
        return False


def get_child_tables_referencing_member():
    """MEMBER 테이블을 참조하는 자식 테이블 목록 조회"""
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                # MEMBER 테이블의 Primary Key 제약조건 찾기
                cur.execute("""
                    SELECT constraint_name 
                    FROM user_constraints 
                    WHERE table_name = 'MEMBER' AND constraint_type = 'P'
                """)
                pk_constraint = cur.fetchone()
                if not pk_constraint:
                    return []
                
                pk_constraint_name = pk_constraint[0]
                
                # 이 PK를 참조하는 Foreign Key 제약조건 찾기
                cur.execute("""
                    SELECT DISTINCT table_name, constraint_name
                    FROM user_constraints
                    WHERE r_constraint_name = :pk_constraint
                """, {'pk_constraint': pk_constraint_name})
                
                child_tables = []
                for row in cur.fetchall():
                    child_tables.append({
                        'table_name': row[0],
                        'constraint_name': row[1]
                    })
                
                return child_tables
    except Exception as e:
        print(f"[경고] 자식 테이블 조회 중 오류: {e}")
        return []


def delete_child_records(child_tables):
    """자식 테이블의 관련 레코드 삭제"""
    deleted_counts = {}
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                for child in child_tables:
                    table_name = child['table_name']
                    try:
                        # MEMBER_ID 컬럼이 있는지 확인
                        cur.execute("""
                            SELECT column_name 
                            FROM user_tab_columns 
                            WHERE table_name = :table_name 
                            AND column_name = 'MEMBER_ID'
                        """, {'table_name': table_name})
                        
                        if cur.fetchone():
                            # MEMBER_ID 컬럼이 있으면 해당 테이블의 레코드 삭제
                            cur.execute(f"DELETE FROM {table_name}")
                            deleted_count = cur.rowcount
                            deleted_counts[table_name] = deleted_count
                            print(f"  - {table_name}: {deleted_count}개 레코드 삭제")
                    except Exception as e:
                        print(f"  - {table_name}: 삭제 중 오류 ({e})")
                        deleted_counts[table_name] = 0
                
                conn.commit()
                return deleted_counts
    except Exception as e:
        print(f"[경고] 자식 레코드 삭제 중 오류: {e}")
        return deleted_counts


def delete_all_members():
    """MEMBER 테이블의 모든 데이터 삭제 (자식 레코드도 함께 삭제)"""
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                # 먼저 현재 데이터 개수 확인
                cur.execute("SELECT COUNT(*) FROM MEMBER")
                count = cur.fetchone()[0]
                
                if count == 0:
                    print("삭제할 데이터가 없습니다.")
                    return True
                
                # 자식 테이블 확인
                child_tables = get_child_tables_referencing_member()
                
                print(f"\n[경고] MEMBER 테이블에 {count}개의 레코드가 있습니다.")
                
                if child_tables:
                    print(f"\n[정보] MEMBER를 참조하는 자식 테이블 {len(child_tables)}개 발견:")
                    for child in child_tables:
                        print(f"  - {child['table_name']}")
                    
                    # 자식 테이블의 레코드 수 확인
                    print("\n[정보] 자식 테이블 레코드 수:")
                    for child in child_tables:
                        try:
                            cur.execute(f"SELECT COUNT(*) FROM {child['table_name']}")
                            child_count = cur.fetchone()[0]
                            print(f"  - {child['table_name']}: {child_count}개")
                        except:
                            print(f"  - {child['table_name']}: 확인 불가")
                
                confirm = input("\n모든 데이터를 삭제하시겠습니까? (yes 입력): ")
                
                if confirm.lower() != 'yes':
                    print("삭제가 취소되었습니다.")
                    return False
                
                # 자식 테이블 레코드 먼저 삭제
                if child_tables:
                    print("\n[정보] 자식 테이블 레코드 삭제 중...")
                    deleted_counts = delete_child_records(child_tables)
                    total_deleted = sum(deleted_counts.values())
                    print(f"✓ 자식 테이블에서 총 {total_deleted}개 레코드 삭제 완료")
                
                # MEMBER 테이블 레코드 삭제
                print("\n[정보] MEMBER 테이블 레코드 삭제 중...")
                cur.execute("DELETE FROM MEMBER")
                deleted_member_count = cur.rowcount
                conn.commit()
                print(f"✓ MEMBER 테이블에서 {deleted_member_count}개 레코드가 삭제되었습니다.")
                return True
    except Exception as e:
        print(f"✗ 삭제 중 오류 발생: {str(e)}")
        import traceback
        print(traceback.format_exc())
        return False


def print_statistics(members):
    """생성된 데이터의 통계 정보 출력"""
    ages = [m[3] for m in members]
    points = [m[7] for m in members]
    
    print("\n" + "=" * 80)
    print("생성된 데이터 통계")
    print("=" * 80)
    print(f"\nAGE 통계:")
    print(f"  평균: {np.mean(ages):.2f} (목표: {AGE_MEAN})")
    print(f"  표준편차: {np.std(ages):.2f} (목표: {AGE_STD})")
    print(f"  최소: {min(ages)} (목표: {AGE_MIN})")
    print(f"  최대: {max(ages)} (목표: {AGE_MAX})")
    
    print(f"\nPOINT 통계:")
    print(f"  평균: {np.mean(points):.2f} (목표: {POINT_MEAN})")
    print(f"  표준편차: {np.std(points):.2f} (목표: {POINT_STD})")
    print(f"  최소: {min(points)} (목표: {POINT_MIN})")
    print(f"  최대: {max(points)}")
    
    genders = [m[4] for m in members]
    gender_count = {'M': genders.count('M'), 'F': genders.count('F')}
    print(f"\n성별 분포:")
    print(f"  남성(M): {gender_count['M']}명 ({gender_count['M']/len(members)*100:.1f}%)")
    print(f"  여성(F): {gender_count['F']}명 ({gender_count['F']/len(members)*100:.1f}%)")


def main():
    """메인 함수"""
    print("=" * 80)
    print("MEMBER 테이블 더미 데이터 생성")
    print("=" * 80)
    
    # 기존 데이터 확인 및 삭제 옵션
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT COUNT(*) FROM MEMBER")
                existing_count = cur.fetchone()[0]
                if existing_count > 0:
                    print(f"\n[정보] 현재 MEMBER 테이블에 {existing_count}개의 레코드가 있습니다.")
                    print("\n" + "=" * 80)
                    delete_choice = input("기존 데이터를 모두 삭제하고 새로 생성하시겠습니까? (y/n): ")
                    if delete_choice.lower() == 'y':
                        if not delete_all_members():
                            print("삭제가 취소되었습니다. 프로그램을 종료합니다.")
                            return
                    else:
                        print("기존 데이터를 유지하고 새 데이터를 추가합니다.")
    except Exception as e:
        print(f"[경고] 기존 데이터 확인 중 오류: {e}")
        print("계속 진행합니다...")
    
    print(f"\n생성할 회원 수: {NUM_MEMBERS}명")
    print(f"\n분포 파라미터:")
    print(f"  AGE: 평균={AGE_MEAN}, 표준편차={AGE_STD}, 범위=[{AGE_MIN}, {AGE_MAX}]")
    print(f"  POINT: 평균={POINT_MEAN}, 표준편차={POINT_STD}, 최소={POINT_MIN}")
    print("\n데이터 생성 중...")
    
    # 더미 데이터 생성
    members = generate_members(NUM_MEMBERS)
    
    # 통계 정보 출력
    print_statistics(members)
    
    # DB 삽입 확인
    print("\n" + "=" * 80)
    response = input("위 데이터를 Oracle DB에 삽입하시겠습니까? (y/n): ")
    if response.lower() != 'y':
        print("취소되었습니다.")
        return
    
    # DB에 삽입
    print("\nDB 삽입 중...")
    success = insert_members(members)
    
    if success:
        print("\n✓ 완료!")
    else:
        print("\n✗ 실패!")


if __name__ == '__main__':
    main()

