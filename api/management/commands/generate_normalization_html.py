"""
정규화 마이그레이션 상태 HTML 리포트 생성

시각화된 HTML 리포트를 생성합니다.

사용법:
    python manage.py generate_normalization_html --output report.html
"""
from django.core.management.base import BaseCommand
from api.management.commands.check_normalization_status import Command as StatusCommand
import json


class Command(BaseCommand):
    help = '정규화 마이그레이션 상태 HTML 리포트 생성'

    def add_arguments(self, parser):
        parser.add_argument(
            '--output',
            type=str,
            default='normalization_status.html',
            help='출력 HTML 파일 경로',
        )

    def handle(self, *args, **options):
        output_path = options['output']
        
        # 상태 확인 명령어 실행하여 데이터 수집
        status_cmd = StatusCommand()
        status_cmd.stdout = self.stdout
        
        status_data = {}
        status_data['taste_config'] = status_cmd._check_taste_config_status(False, return_data=True)
        status_data['onboarding_session'] = status_cmd._check_onboarding_session_status(False, return_data=True)
        status_data['product_demographics'] = status_cmd._check_product_demographics_status(False, return_data=True)
        status_data['user_sample'] = status_cmd._check_user_sample_status(False, return_data=True)
        
        # HTML 생성
        html_content = self._generate_html(status_data)
        
        # 파일 저장
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        self.stdout.write(self.style.SUCCESS(f'\nHTML 리포트 생성 완료: {output_path}'))

    def _generate_html(self, status_data):
        """HTML 리포트 생성"""
        html = f"""<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>정규화 마이그레이션 상태 리포트</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 10px;
            padding: 30px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.3);
        }}
        h1 {{
            color: #333;
            text-align: center;
            margin-bottom: 30px;
            font-size: 2.5em;
        }}
        .section {{
            margin-bottom: 40px;
            padding: 20px;
            background: #f8f9fa;
            border-radius: 8px;
            border-left: 4px solid #667eea;
        }}
        .section h2 {{
            color: #667eea;
            margin-top: 0;
        }}
        .stat {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin: 15px 0;
            padding: 15px;
            background: white;
            border-radius: 5px;
        }}
        .stat-label {{
            font-weight: bold;
            color: #555;
        }}
        .stat-value {{
            font-size: 1.2em;
            color: #667eea;
        }}
        .progress-container {{
            margin: 20px 0;
        }}
        .progress-bar {{
            width: 100%;
            height: 30px;
            background: #e0e0e0;
            border-radius: 15px;
            overflow: hidden;
            position: relative;
        }}
        .progress-fill {{
            height: 100%;
            background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
            transition: width 0.3s ease;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-weight: bold;
        }}
        .progress-text {{
            position: absolute;
            width: 100%;
            text-align: center;
            line-height: 30px;
            font-weight: bold;
            color: #333;
        }}
        .status-badge {{
            display: inline-block;
            padding: 5px 15px;
            border-radius: 20px;
            font-size: 0.9em;
            font-weight: bold;
        }}
        .status-success {{
            background: #4caf50;
            color: white;
        }}
        .status-warning {{
            background: #ff9800;
            color: white;
        }}
        .status-error {{
            background: #f44336;
            color: white;
        }}
        .table-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 15px;
            margin-top: 20px;
        }}
        .table-card {{
            background: white;
            padding: 15px;
            border-radius: 5px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }}
        .table-card h3 {{
            margin-top: 0;
            color: #667eea;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>📊 정규화 마이그레이션 상태 리포트</h1>
        
        {self._generate_section_html('TASTE_CONFIG', status_data.get('taste_config', {}))}
        {self._generate_section_html('ONBOARDING_SESSION', status_data.get('onboarding_session', {}))}
        {self._generate_section_html('PRODUCT_DEMOGRAPHICS', status_data.get('product_demographics', {}))}
        {self._generate_section_html('USER_SAMPLE', status_data.get('user_sample', {}))}
        
        <div class="section">
            <h2>📝 요약</h2>
            <p>이 리포트는 정규화 마이그레이션의 현재 상태를 보여줍니다.</p>
            <p>생성 시간: <script>document.write(new Date().toLocaleString('ko-KR'));</script></p>
        </div>
    </div>
</body>
</html>"""
        return html

    def _generate_section_html(self, table_name, data):
        """섹션 HTML 생성"""
        if not data or data.get('status') == 'error':
            status_badge = '<span class="status-badge status-error">오류</span>'
            content = f'<p>오류: {data.get("error", "알 수 없는 오류")}</p>'
        elif data.get('status') == 'not_created':
            status_badge = '<span class="status-badge status-warning">대기 중</span>'
            content = '<p>정규화 테이블이 아직 생성되지 않았습니다.</p>'
        else:
            progress = data.get('progress', 0)
            if progress >= 100:
                status_badge = '<span class="status-badge status-success">완료</span>'
            elif progress > 0:
                status_badge = '<span class="status-badge status-warning">진행 중</span>'
            else:
                status_badge = '<span class="status-badge status-warning">대기 중</span>'
            
            content = f"""
            <div class="stat">
                <span class="stat-label">기본 테이블 레코드 수:</span>
                <span class="stat-value">{data.get('base_count', 0)}개</span>
            </div>
            <div class="stat">
                <span class="stat-label">정규화 테이블 레코드 수:</span>
                <span class="stat-value">{data.get('normalized_count', 0)}개</span>
            </div>
            <div class="progress-container">
                <div class="progress-bar">
                    <div class="progress-fill" style="width: {min(100, progress)}%"></div>
                    <div class="progress-text">{progress:.1f}%</div>
                </div>
            </div>
            """
        
        return f"""
        <div class="section">
            <h2>{table_name} {status_badge}</h2>
            {content}
        </div>
        """


