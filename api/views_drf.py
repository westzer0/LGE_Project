"""
Django REST Framework API Views

기존 views_drf.py에 Figma 변환 엔드포인트 추가
"""
from rest_framework.decorators import api_view, parser_classes
from rest_framework.response import Response
from rest_framework import status
from rest_framework.parsers import MultiPartParser, FormParser
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
import os
from .services.figma_to_code_service import figma_to_code_service

# 기존 import는 유지
# ... (기존 코드)

@api_view(['POST'])
@parser_classes([MultiPartParser, FormParser])
def convert_figma_to_code(request):
    """
    Figma 이미지를 프론트엔드 코드로 변환
    
    POST /api/figma-to-code/
    
    Form Data:
    - image: 이미지 파일 (PNG, JPG, JPEG)
    - design_type: 디자인 타입 (선택, 기본값: 'web_page')
    
    Returns:
    {
        'success': True,
        'html': '...',
        'css': '...',
        'javascript': '...',
        'components': [...],
        'colors': {...},
        'fonts': [...],
        'files': {
            'html': '/path/to/index.html',
            'css': '/path/to/styles.css',
            ...
        }
    }
    """
    if 'image' not in request.FILES:
        return Response(
            {'error': '이미지 파일이 필요합니다.'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    image_file = request.FILES['image']
    design_type = request.data.get('design_type', 'web_page')
    
    # 파일 저장
    file_name = default_storage.save(
        f'temp_figma/{image_file.name}',
        ContentFile(image_file.read())
    )
    file_path = default_storage.path(file_name)
    
    try:
        # 이미지 변환
        result = figma_to_code_service.convert_image_to_code(
            image_path=file_path,
            design_type=design_type
        )
        
        if not result.get('success'):
            return Response(
                {'error': result.get('error', '변환 실패')},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        # 코드 파일 저장 (선택)
        output_dir = None
        saved_files = {}
        
        if request.data.get('save_files', 'false').lower() == 'true':
            output_dir = os.path.join(
                default_storage.location,
                'figma_output',
                os.path.splitext(image_file.name)[0]
            )
            saved_files = figma_to_code_service.save_code_to_files(
                result,
                output_dir
            )
        
        # 임시 파일 삭제
        default_storage.delete(file_name)
        
        return Response({
            'success': True,
            'html': result.get('html', ''),
            'css': result.get('css', ''),
            'javascript': result.get('javascript', ''),
            'components': result.get('components', []),
            'colors': result.get('colors', {}),
            'fonts': result.get('fonts', []),
            'layout': result.get('layout', {}),
            'breakpoints': result.get('breakpoints', {}),
            'files': saved_files,
        })
    
    except Exception as e:
        # 임시 파일 삭제
        if default_storage.exists(file_name):
            default_storage.delete(file_name)
        
        return Response(
            {'error': f'변환 중 오류 발생: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
