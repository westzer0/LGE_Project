"""
Figma 이미지를 입력받아 프론트엔드 코드로 변환하는 서비스

Vision API를 활용하여 디자인 이미지를 분석하고 HTML/CSS/JavaScript를 생성합니다.
"""
import json
import base64
from typing import Dict, Optional, List
from django.conf import settings

try:
    from openai import OpenAI
    client = OpenAI(api_key=settings.OPENAI_API_KEY)
    OPENAI_AVAILABLE = True
except Exception as e:
    print(f"[WARNING] OpenAI 초기화 실패: {e}")
    client = None
    OPENAI_AVAILABLE = False


class FigmaToCodeService:
    """Figma 이미지 → 코드 변환 서비스"""
    
    MODEL = "gpt-4o"  # Vision API 지원 모델
    
    @classmethod
    def is_available(cls):
        """Vision API 사용 가능 여부 확인"""
        return OPENAI_AVAILABLE and client is not None
    
    @classmethod
    def convert_image_to_code(
        cls,
        image_path: str,
        design_type: str = "web_page"
    ) -> Dict:
        """
        Figma 이미지를 코드로 변환
        
        Args:
            image_path: 이미지 파일 경로
            design_type: 디자인 타입 ('web_page', 'component', 'mobile')
        
        Returns:
            {
                'html': '...',
                'css': '...',
                'javascript': '...',
                'components': [...],
                'colors': {...},
                'fonts': [...],
            }
        """
        if not cls.is_available():
            return cls._fallback_response()
        
        try:
            # 이미지 파일 읽기
            with open(image_path, 'rb') as f:
                image_data = f.read()
            
            # Base64 인코딩
            image_base64 = base64.b64encode(image_data).decode('utf-8')
            
            # Vision API 호출
            response = client.chat.completions.create(
                model=cls.MODEL,
                messages=[
                    {
                        "role": "system",
                        "content": """당신은 전문 프론트엔드 개발자입니다. 
Figma 디자인 이미지를 분석하여 정확한 HTML/CSS/JavaScript 코드를 생성합니다.

요구사항:
1. 레이아웃 구조를 정확히 파악
2. 색상, 폰트, 간격을 정확히 추출
3. 반응형 디자인 고려
4. 접근성(accessibility) 고려
5. 모던한 CSS (Flexbox, Grid) 사용
6. 컴포넌트 기반 구조
7. 한국어 주석 포함"""
                    },
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": f"""다음 Figma 디자인 이미지를 분석하여 완전한 프론트엔드 코드를 생성해주세요.

디자인 타입: {design_type}

다음 JSON 형식으로 응답해주세요:
{{
    "html": "<!DOCTYPE html>...",
    "css": "/* CSS 코드 */",
    "javascript": "// JavaScript 코드",
    "components": [
        {{
            "name": "Header",
            "description": "헤더 컴포넌트",
            "html": "...",
            "css": "..."
        }}
    ],
    "colors": {{
        "primary": "#000000",
        "secondary": "#ffffff",
        ...
    }},
    "fonts": [
        {{
            "name": "Pretendard",
            "weights": [400, 500, 600, 700]
        }}
    ],
    "layout": {{
        "type": "grid",
        "columns": 12,
        "gap": "20px"
    }},
    "breakpoints": {{
        "mobile": "768px",
        "tablet": "1024px",
        "desktop": "1280px"
    }}
}}

중요:
- 실제 사용 가능한 완전한 코드 생성
- 색상 코드는 정확히 추출
- 폰트는 실제 사용 가능한 폰트로 (Pretendard, Noto Sans KR 등)
- 반응형 미디어 쿼리 포함
- 접근성 속성 (aria-label 등) 포함"""
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/png;base64,{image_base64}"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=4000,
                temperature=0.3
            )
            
            # JSON 파싱
            content = response.choices[0].message.content.strip()
            
            # JSON 코드 블록 추출
            if "```json" in content:
                json_start = content.find("```json") + 7
                json_end = content.find("```", json_start)
                json_str = content[json_start:json_end].strip()
            elif "```" in content:
                json_start = content.find("```") + 3
                json_end = content.find("```", json_start)
                json_str = content[json_start:json_end].strip()
            else:
                json_str = content
            
            result = json.loads(json_str)
            
            return {
                'success': True,
                'html': result.get('html', ''),
                'css': result.get('css', ''),
                'javascript': result.get('javascript', ''),
                'components': result.get('components', []),
                'colors': result.get('colors', {}),
                'fonts': result.get('fonts', []),
                'layout': result.get('layout', {}),
                'breakpoints': result.get('breakpoints', {}),
            }
        
        except json.JSONDecodeError as e:
            print(f"JSON 파싱 오류: {e}")
            return {
                'success': False,
                'error': 'JSON 파싱 실패',
                'raw_response': content if 'content' in locals() else ''
            }
        except Exception as e:
            print(f"Figma 변환 오류: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    @classmethod
    def convert_multiple_images(
        cls,
        image_paths: List[str],
        design_type: str = "web_page"
    ) -> Dict:
        """
        여러 이미지를 한 번에 변환 (페이지별, 컴포넌트별)
        
        Args:
            image_paths: 이미지 파일 경로 리스트
            design_type: 디자인 타입
        
        Returns:
            {
                'pages': [
                    {
                        'name': 'main',
                        'html': '...',
                        'css': '...',
                        ...
                    }
                ],
                'shared_components': [...],
                'global_styles': {...}
            }
        """
        results = []
        
        for idx, image_path in enumerate(image_paths):
            result = cls.convert_image_to_code(image_path, design_type)
            if result.get('success'):
                results.append({
                    'name': f'page_{idx + 1}',
                    **result
                })
        
        # 공통 컴포넌트 추출
        shared_components = []
        all_colors = {}
        all_fonts = []
        
        for result in results:
            shared_components.extend(result.get('components', []))
            all_colors.update(result.get('colors', {}))
            all_fonts.extend(result.get('fonts', []))
        
        # 중복 제거
        all_fonts = list({f['name']: f for f in all_fonts}.values())
        
        return {
            'success': True,
            'pages': results,
            'shared_components': shared_components,
            'global_styles': {
                'colors': all_colors,
                'fonts': all_fonts,
            }
        }
    
    @classmethod
    def _fallback_response(cls) -> Dict:
        """API 사용 불가 시 기본 응답"""
        return {
            'success': False,
            'error': 'OpenAI Vision API를 사용할 수 없습니다. API 키를 설정해주세요.',
            'html': '',
            'css': '',
            'javascript': '',
            'components': [],
            'colors': {},
            'fonts': [],
        }
    
    @classmethod
    def save_code_to_files(
        cls,
        result: Dict,
        output_dir: str
    ) -> Dict:
        """
        생성된 코드를 파일로 저장
        
        Args:
            result: convert_image_to_code()의 결과
            output_dir: 출력 디렉토리
        
        Returns:
            저장된 파일 경로 딕셔너리
        """
        import os
        from pathlib import Path
        
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        saved_files = {}
        
        if result.get('html'):
            html_path = output_path / 'index.html'
            with open(html_path, 'w', encoding='utf-8') as f:
                f.write(result['html'])
            saved_files['html'] = str(html_path)
        
        if result.get('css'):
            css_path = output_path / 'styles.css'
            with open(css_path, 'w', encoding='utf-8') as f:
                f.write(result['css'])
            saved_files['css'] = str(css_path)
        
        if result.get('javascript'):
            js_path = output_path / 'script.js'
            with open(js_path, 'w', encoding='utf-8') as f:
                f.write(result['javascript'])
            saved_files['javascript'] = str(js_path)
        
        # 컴포넌트별 파일 저장
        components_dir = output_path / 'components'
        components_dir.mkdir(exist_ok=True)
        
        for component in result.get('components', []):
            comp_name = component.get('name', 'component').lower().replace(' ', '_')
            comp_html = component.get('html', '')
            comp_css = component.get('css', '')
            
            if comp_html:
                comp_html_path = components_dir / f'{comp_name}.html'
                with open(comp_html_path, 'w', encoding='utf-8') as f:
                    f.write(comp_html)
            
            if comp_css:
                comp_css_path = components_dir / f'{comp_name}.css'
                with open(comp_css_path, 'w', encoding='utf-8') as f:
                    f.write(comp_css)
        
        # 메타데이터 저장
        metadata = {
            'colors': result.get('colors', {}),
            'fonts': result.get('fonts', []),
            'layout': result.get('layout', {}),
            'breakpoints': result.get('breakpoints', {}),
        }
        
        metadata_path = output_path / 'metadata.json'
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)
        saved_files['metadata'] = str(metadata_path)
        
        return saved_files


# Singleton 인스턴스
figma_to_code_service = FigmaToCodeService()

