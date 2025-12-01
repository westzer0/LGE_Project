"""PDF 파일 상세 읽기"""
import PyPDF2
import os

pdf_path = r'data\피그마UI\Wireframe.pdf'

if os.path.exists(pdf_path):
    with open(pdf_path, 'rb') as pdf_file:
        reader = PyPDF2.PdfReader(pdf_file)
        print(f'총 페이지 수: {len(reader.pages)}')
        print('\n=== 전체 텍스트 추출 ===\n')
        
        all_text = []
        for i, page in enumerate(reader.pages):
            text = page.extract_text()
            all_text.append(text)
            print(f'--- 페이지 {i+1} (길이: {len(text)}자) ---')
            # 인코딩 문제를 피하기 위해 바이트로 출력
            try:
                print(text)
            except:
                print(text.encode('utf-8', errors='ignore').decode('utf-8', errors='ignore'))
            print('\n' + '='*80 + '\n')
        
        # 전체 텍스트를 파일로 저장
        with open('pdf_content.txt', 'w', encoding='utf-8') as f:
            f.write('\n\n'.join(all_text))
        print('전체 텍스트를 pdf_content.txt에 저장했습니다.')
else:
    print(f'파일을 찾을 수 없습니다: {pdf_path}')

