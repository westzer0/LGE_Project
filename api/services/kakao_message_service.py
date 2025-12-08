"""
카카오톡 메시지 전송 서비스
"""
import requests
import logging
from django.conf import settings
import json

logger = logging.getLogger(__name__)


class KakaoMessageService:
    """카카오톡 메시지 전송 서비스"""
    
    REST_API_KEY = settings.KAKAO_REST_API_KEY
    
    @classmethod
    def send_template_message(cls, access_token, template_id, template_args=None):
        """
        템플릿 메시지 전송 (알림톡/친구톡)
        
        Args:
            access_token: 카카오 액세스 토큰 (사용자 토큰 또는 앱 토큰)
            template_id: 메시지 템플릿 ID
            template_args: 템플릿 변수 딕셔너리
            
        Returns:
            전송 결과
        """
        if not cls.REST_API_KEY:
            raise ValueError("KAKAO_REST_API_KEY가 설정되지 않았습니다.")
        
        url = "https://kapi.kakao.com/v1/api/talk/messages/default/send"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/x-www-form-urlencoded"
        }
        
        data = {
            "template_id": template_id
        }
        
        if template_args:
            data["template_args"] = json.dumps(template_args, ensure_ascii=False)
        
        return cls._send_request(url, headers, data, f"template_id={template_id}")
    
    @classmethod
    def send_custom_message(cls, access_token, receiver_id, message_text, link_url=None):
        """
        커스텀 메시지 전송 (개발용)
        
        Args:
            access_token: 카카오 액세스 토큰
            receiver_id: 수신자 카카오 ID
            message_text: 메시지 내용
            link_url: 링크 URL (선택)
            
        Returns:
            전송 결과
        """
        if not cls.REST_API_KEY:
            raise ValueError("KAKAO_REST_API_KEY가 설정되지 않았습니다.")
        
        url = "https://kapi.kakao.com/v2/api/talk/memo/default/send"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/x-www-form-urlencoded"
        }
        
        template_object = {
            "object_type": "text",
            "text": message_text,
            "link": {
                "web_url": link_url or "https://www.lge.co.kr",
                "mobile_web_url": link_url or "https://www.lge.co.kr"
            }
        }
        
        data = {
            "template_object": json.dumps(template_object, ensure_ascii=False)
        }
        
        return cls._send_request(url, headers, data, "custom_message")
    
    @classmethod
    def _send_request(cls, url, headers, data, log_context=""):
        """
        공통 HTTP 요청 처리 (에러 처리 및 로깅)
        
        Args:
            url: 요청 URL
            headers: 요청 헤더
            data: 요청 데이터
            log_context: 로그 컨텍스트
            
        Returns:
            응답 JSON
        """
        try:
            response = requests.post(url, headers=headers, data=data, timeout=10)
            
            # 토큰 만료 처리
            if response.status_code == 401:
                logger.warning(f"[Kakao Message] 액세스 토큰 만료: {log_context}")
                raise Exception("카카오 로그인이 만료되었습니다. 다시 로그인해주세요.")
            
            response.raise_for_status()
            result = response.json()
            logger.info(f"[Kakao Message] 메시지 전송 성공: {log_context}")
            return result
        except requests.exceptions.Timeout:
            logger.error(f"[Kakao Message] 메시지 전송 타임아웃: {log_context}")
            raise Exception("카카오 서버 응답 시간이 초과되었습니다.")
        except requests.exceptions.RequestException as e:
            logger.error(f"[Kakao Message] 메시지 전송 실패 ({log_context}): {e}")
            raise Exception(f"메시지 전송 실패: {str(e)}")
        except Exception as e:
            logger.error(f"[Kakao Message] 메시지 전송 예외 ({log_context}): {e}")
            raise
    
    @classmethod
    def send_consultation_notification(cls, user_access_token, portfolio_title, consultation_date, store_location):
        """
        상담 예약 알림 메시지 전송
        
        Args:
            user_access_token: 사용자 카카오 액세스 토큰
            portfolio_title: 포트폴리오 제목
            consultation_date: 상담 예약 날짜
            store_location: 매장 위치
            
        Returns:
            전송 결과
        """
        message = f"""LG 홈스타일링 상담 예약이 완료되었습니다.

포트폴리오: {portfolio_title}
예약일시: {consultation_date}
매장: {store_location}

베스트샵에서 전문 상담사와 함께 최적의 가전을 선택하세요!"""
        
        link_url = "https://bestshop.lge.co.kr"
        
        try:
            result = cls.send_custom_message(
                access_token=user_access_token,
                receiver_id=None,  # 자기 자신에게 전송
                message_text=message,
                link_url=link_url
            )
            logger.info(f"[Kakao Message] 상담 예약 알림 전송 성공: portfolio_title={portfolio_title}")
            return result
        except Exception as e:
            logger.error(f"[Kakao Message] 상담 예약 알림 전송 실패: {e}")
            # 실패해도 사용자에게는 성공으로 표시 (비동기 처리 고려)
            return None


# 싱글톤 인스턴스
kakao_message_service = KakaoMessageService()

