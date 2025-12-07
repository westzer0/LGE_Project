"""
카카오 로그인 서비스
"""
import requests
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import User
import json

User = get_user_model()


class KakaoAuthService:
    """카카오 인증 서비스"""
    
    REST_API_KEY = settings.KAKAO_REST_API_KEY
    
    @classmethod
    def get_authorization_url(cls, redirect_uri):
        """
        카카오 로그인 인증 URL 생성
        
        Args:
            redirect_uri: 콜백 URL
            
        Returns:
            카카오 인증 URL
        """
        if not cls.REST_API_KEY:
            raise ValueError("KAKAO_REST_API_KEY가 설정되지 않았습니다.")
        
        base_url = "https://kauth.kakao.com/oauth/authorize"
        params = {
            "client_id": cls.REST_API_KEY,
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "scope": "profile_nickname,account_email"  # 필요한 정보 요청
        }
        
        url = f"{base_url}?client_id={params['client_id']}&redirect_uri={params['redirect_uri']}&response_type={params['response_type']}&scope={params['scope']}"
        return url
    
    @classmethod
    def get_access_token(cls, code, redirect_uri):
        """
        인증 코드로 액세스 토큰 발급
        
        Args:
            code: 카카오 인증 코드
            redirect_uri: 콜백 URL
            
        Returns:
            액세스 토큰
        """
        if not cls.REST_API_KEY:
            raise ValueError("KAKAO_REST_API_KEY가 설정되지 않았습니다.")
        
        url = "https://kauth.kakao.com/oauth/token"
        data = {
            "grant_type": "authorization_code",
            "client_id": cls.REST_API_KEY,
            "redirect_uri": redirect_uri,
            "code": code
        }
        
        response = requests.post(url, data=data)
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"토큰 발급 실패: {response.text}")
    
    @classmethod
    def get_user_info(cls, access_token):
        """
        액세스 토큰으로 사용자 정보 조회
        
        Args:
            access_token: 카카오 액세스 토큰
            
        Returns:
            사용자 정보 딕셔너리
        """
        url = "https://kapi.kakao.com/v2/user/me"
        headers = {
            "Authorization": f"Bearer {access_token}"
        }
        
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"사용자 정보 조회 실패: {response.text}")
    
    @classmethod
    def get_or_create_user(cls, kakao_user_info):
        """
        카카오 사용자 정보로 Django User 생성/조회
        
        Args:
            kakao_user_info: 카카오 사용자 정보
            
        Returns:
            (User 객체, created 여부)
        """
        kakao_id = str(kakao_user_info.get('id'))
        kakao_account = kakao_user_info.get('kakao_account', {})
        
        # 이메일 또는 닉네임 추출
        email = kakao_account.get('email', f'kakao_{kakao_id}@kakao.com')
        nickname = kakao_account.get('profile', {}).get('nickname', f'카카오사용자_{kakao_id[:6]}')
        
        # 기존 사용자 조회 (username을 kakao_id로 사용)
        username = f"kakao_{kakao_id}"
        
        try:
            user = User.objects.get(username=username)
            created = False
        except User.DoesNotExist:
            # 새 사용자 생성
            user = User.objects.create_user(
                username=username,
                email=email,
                first_name=nickname
            )
            created = True
        
        # 카카오 ID를 user의 추가 정보로 저장 (필요시)
        # user.profile.kakao_id = kakao_id  # 커스텀 프로필 모델이 있다면
        
        return user, created


# 싱글톤 인스턴스
kakao_auth_service = KakaoAuthService()

