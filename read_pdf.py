"""PDF 파일 읽기"""
import PyPDF2
import os

pdf_path = r'data\피그마UI\Wireframe.pdf'

if os.path.exists(pdf_path):
    with open(pdf_path, 'rb') as pdf_file:
        reader = PyPDF2.PdfReader(pdf_file)
        print(f'총 페이지 수: {len(reader.pages)}')
        print('\n=== 각 페이지 텍스트 추출 ===\n')
        
        for i, page in enumerate(reader.pages):
            text = page.extract_text()
            if text.strip():
                print(f'--- 페이지 {i+1} ---')
                print(text[:500])
                print('\n')
else:
    print(f'파일을 찾을 수 없습니다: {pdf_path}')

