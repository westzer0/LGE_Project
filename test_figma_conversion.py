"""
Figma 이미지 변환 테스트 스크립트

사용법:
    python test_figma_conversion.py [이미지_파일_경로]
"""
import os
import sys
import django

# Django 설정
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from api.services.figma_to_code_service import figma_to_code_service

def test_figma_conversion(image_path: str):
    """Figma 이미지 변환 테스트"""
    print(f"\n{'='*60}")
    print(f"Figma 이미지 변환 테스트")
    print(f"{'='*60}")
    print(f"\n📁 이미지 파일: {image_path}")
    
    # 파일 존재 확인
    if not os.path.exists(image_path):
        print(f"❌ 파일을 찾을 수 없습니다: {image_path}")
        return
    
    # API 키 확인
    if not figma_to_code_service.is_available():
        print("❌ OpenAI Vision API를 사용할 수 없습니다.")
        print("   .env 파일에 OPENAI_API_KEY가 설정되어 있는지 확인하세요.")
        return
    
    print("✅ OpenAI Vision API 사용 가능")
    
    # 변환 실행
    print("\n🔄 변환 중...")
    result = figma_to_code_service.convert_image_to_code(
        image_path=image_path,
        design_type='web_page'
    )
    
    if not result.get('success'):
        print(f"\n❌ 변환 실패: {result.get('error', '알 수 없는 오류')}")
        if 'raw_response' in result:
            print(f"\n원본 응답:\n{result['raw_response'][:500]}")
        return
    
    print("\n✅ 변환 성공!")
    
    # 결과 출력
    print(f"\n{'='*60}")
    print("생성된 코드 미리보기")
    print(f"{'='*60}")
    
    html = result.get('html', '')
    css = result.get('css', '')
    js = result.get('javascript', '')
    
    print(f"\n📄 HTML ({len(html)} 문자):")
    print(html[:300] + "..." if len(html) > 300 else html)
    
    print(f"\n🎨 CSS ({len(css)} 문자):")
    print(css[:300] + "..." if len(css) > 300 else css)
    
    if js:
        print(f"\n⚙️ JavaScript ({len(js)} 문자):")
        print(js[:300] + "..." if len(js) > 300 else js)
    
    # 메타데이터 출력
    print(f"\n{'='*60}")
    print("추출된 메타데이터")
    print(f"{'='*60}")
    
    colors = result.get('colors', {})
    if colors:
        print(f"\n🎨 색상:")
        for name, value in colors.items():
            print(f"  - {name}: {value}")
    
    fonts = result.get('fonts', [])
    if fonts:
        print(f"\n📝 폰트:")
        for font in fonts:
            print(f"  - {font.get('name', 'Unknown')}: {font.get('weights', [])}")
    
    components = result.get('components', [])
    if components:
        print(f"\n🧩 컴포넌트 ({len(components)}개):")
        for comp in components:
            print(f"  - {comp.get('name', 'Unknown')}: {comp.get('description', '')}")
    
    # 파일 저장
    output_dir = 'output/figma_converted'
    print(f"\n💾 파일 저장 중... ({output_dir})")
    
    saved_files = figma_to_code_service.save_code_to_files(
        result,
        output_dir
    )
    
    if saved_files:
        print("\n✅ 저장 완료:")
        for file_type, file_path in saved_files.items():
            print(f"  - {file_type}: {file_path}")
    
    print(f"\n{'='*60}")
    print("테스트 완료!")
    print(f"{'='*60}\n")


if __name__ == '__main__':
    # 명령줄 인자로 이미지 파일 경로 받기
    if len(sys.argv) > 1:
        image_path = sys.argv[1]
    else:
        # 기본값: 피그마 UI 폴더의 첫 번째 PDF
        image_path = 'data/피그마UI/1. LG Main.pdf'
    
    test_figma_conversion(image_path)

