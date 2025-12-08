"""
JWT + Kakao OAuth 인증 API 엔드포인트

엔드포인트:
- POST /api/v1/auth/kakao/ - 카카오 로그인 → MEMBER 생성 → JWT 발급
- POST /api/v1/auth/refresh/ - JWT 토큰 갱신
- GET /api/v1/auth/me/ - 현재 로그인한 사용자 정보
"""
from rest_framework import status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model
from django.conf import settings
import logging

from api.services.kakao_auth_service import kakao_auth_service
from api.models import Member

User = get_user_model()
logger = logging.getLogger(__name__)


def get_tokens_for_user(user):
    """
    사용자에 대한 JWT 토큰 생성
    
    Args:
        user: Django User 객체
        
    Returns:
        dict: {'access': access_token, 'refresh': refresh_token}
    """
    refresh = RefreshToken.for_user(user)
    return {
        'access': str(refresh.access_token),
        'refresh': str(refresh),
    }


@api_view(['POST'])
@permission_classes([AllowAny])
def kakao_login_view(request):
    """
    카카오 로그인 → MEMBER 생성 → JWT 발급
    
    POST /api/v1/auth/kakao/
    
    Request Body:
    {
        "access_token": "카카오 액세스 토큰"  # 또는 "code": "인증 코드"
    }
    
    Response:
    {
        "success": true,
        "access": "JWT 액세스 토큰",
        "refresh": "JWT 리프레시 토큰",
        "member": {
            "member_id": "kakao_123456",
            "name": "홍길동",
            ...
        },
        "created": true  # 새로 생성된 회원인지 여부
    }
    """
    try:
        access_token = request.data.get('access_token')
        code = request.data.get('code')
        redirect_uri = request.data.get('redirect_uri')
        
        # access_token이 없으면 code로 토큰 발급
        if not access_token and code:
            if not redirect_uri:
                redirect_uri = request.build_absolute_uri('/api/v1/auth/kakao/callback/')
            
            token_response = kakao_auth_service.get_access_token(code, redirect_uri)
            access_token = token_response.get('access_token')
            
            if not access_token:
                return Response({
                    'success': False,
                    'error': '카카오 토큰 발급 실패'
                }, status=status.HTTP_400_BAD_REQUEST)
        
        if not access_token:
            return Response({
                'success': False,
                'error': 'access_token 또는 code가 필요합니다.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # 카카오 사용자 정보 조회
        kakao_user_info = kakao_auth_service.get_user_info(access_token)
        kakao_id = str(kakao_user_info.get('id'))
        kakao_account = kakao_user_info.get('kakao_account', {})
        
        # 이메일, 닉네임 추출
        email = kakao_account.get('email', f'kakao_{kakao_id}@kakao.com')
        nickname = kakao_account.get('profile', {}).get('nickname', f'카카오사용자_{kakao_id[:6]}')
        
        # Django User 생성/조회
        username = f"kakao_{kakao_id}"
        user, user_created = kakao_auth_service.get_or_create_user(kakao_user_info)
        
        # MEMBER 모델 생성/조회 (ERD 기반)
        member_id = f"kakao_{kakao_id}"
        member, member_created = Member.objects.get_or_create(
            member_id=member_id,
            defaults={
                'name': nickname,
                'password': '',  # 카카오 로그인은 비밀번호 없음
                'contact': email,
            }
        )
        
        # JWT 토큰 발급
        tokens = get_tokens_for_user(user)
        
        return Response({
            'success': True,
            'access': tokens['access'],
            'refresh': tokens['refresh'],
            'member': {
                'member_id': member.member_id,
                'name': member.name,
                'age': member.age,
                'gender': member.gender,
                'contact': member.contact,
                'point': member.point,
                'taste': member.taste,
                'created_date': member.created_date,
            },
            'created': member_created,
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"[Kakao Login] 오류: {str(e)}", exc_info=True)
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([AllowAny])
def jwt_refresh_view(request):
    """
    JWT 리프레시 토큰으로 액세스 토큰 갱신
    
    POST /api/v1/auth/refresh/
    
    Request Body:
    {
        "refresh": "리프레시 토큰"
    }
    
    Response:
    {
        "access": "새로운 액세스 토큰",
        "refresh": "새로운 리프레시 토큰"  # ROTATE_REFRESH_TOKENS=True인 경우
    }
    """
    try:
        refresh_token = request.data.get('refresh')
        if not refresh_token:
            return Response({
                'success': False,
                'error': 'refresh 토큰이 필요합니다.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        refresh = RefreshToken(refresh_token)
        access_token = str(refresh.access_token)
        
        # ROTATE_REFRESH_TOKENS=True인 경우 새 리프레시 토큰 발급
        response_data = {
            'success': True,
            'access': access_token,
        }
        
        if settings.SIMPLE_JWT.get('ROTATE_REFRESH_TOKENS', True):
            new_refresh = RefreshToken()
            new_refresh.set_jti(refresh.get('jti'))
            new_refresh.set_exp(refresh.get('exp'))
            response_data['refresh'] = str(new_refresh)
        
        return Response(response_data, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"[JWT Refresh] 오류: {str(e)}", exc_info=True)
        return Response({
            'success': False,
            'error': '유효하지 않은 리프레시 토큰입니다.'
        }, status=status.HTTP_401_UNAUTHORIZED)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def jwt_me_view(request):
    """
    현재 로그인한 사용자 정보 조회
    
    GET /api/v1/auth/me/
    Header: Authorization: Bearer {access_token}
    
    Response:
    {
        "success": true,
        "user": {
            "id": 1,
            "username": "kakao_123456",
            "email": "user@example.com",
            ...
        },
        "member": {
            "member_id": "kakao_123456",
            "name": "홍길동",
            ...
        }
    }
    """
    try:
        user = request.user
        
        # MEMBER 정보 조회 (username에서 kakao_id 추출)
        member = None
        if user.username.startswith('kakao_'):
            kakao_id = user.username.replace('kakao_', '')
            member_id = f"kakao_{kakao_id}"
            try:
                member = Member.objects.get(member_id=member_id)
            except Member.DoesNotExist:
                pass
        
        response_data = {
            'success': True,
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'is_staff': user.is_staff,
                'is_superuser': user.is_superuser,
            },
        }
        
        if member:
            response_data['member'] = {
                'member_id': member.member_id,
                'name': member.name,
                'age': member.age,
                'gender': member.gender,
                'contact': member.contact,
                'point': member.point,
                'taste': member.taste,
                'created_date': member.created_date,
            }
        
        return Response(response_data, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"[JWT Me] 오류: {str(e)}", exc_info=True)
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_400_BAD_REQUEST)
