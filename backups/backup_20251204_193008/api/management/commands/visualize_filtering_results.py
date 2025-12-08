"""
온보딩 모든 케이스별 필터링 결과 시각화

각 온보딩 케이스에 대해:
1. 필터링 전/후 제품 수 추적
2. 제외된 제품과 제외 이유 기록
3. HTML 리포트 생성 (차트 포함)

사용법:
    python manage.py visualize_filtering_results
    python manage.py visualize_filtering_results --limit 10  # 처음 10개만
    python manage.py visualize_filtering_results --output filtering_report.html
"""
import csv
import json
import os
from collections import defaultdict
from pathlib import Path
from django.core.management.base import BaseCommand
from django.db.models import Q
from api.models import Product
from api.services.recommendation_engine import RecommendationEngine
from api.utils.product_filters import (
    filter_by_household_size,
    filter_by_housing_type,
    filter_by_lifestyle,
    filter_by_priority,
    get_product_spec,
    extract_capacity,
    extract_size,
)


class Command(BaseCommand):
    help = '온보딩 모든 케이스별 필터링 결과 시각화'

    def add_arguments(self, parser):
        parser.add_argument(
            '--csv-path',
            type=str,
            default='data/온보딩/taste_recommendations_768.csv',
            help='CSV 파일 경로',
        )
        parser.add_argument(
            '--limit',
            type=int,
            default=None,
            help='처리할 케이스 수 제한 (None이면 전체)',
        )
        parser.add_argument(
            '--output',
            type=str,
            default='filtering_visualization_report.html',
            help='HTML 리포트 출력 경로',
        )
        parser.add_argument(
            '--categories',
            type=str,
            nargs='+',
            default=None,
            help='테스트할 카테고리 목록',
        )

    def handle(self, *args, **options):
        csv_path = options['csv_path']
        limit = options['limit']
        output_path = options['output']
        categories = options['categories']
        
        print('\n=== 필터링 결과 시각화 ===\n')
        self.stdout.write(self.style.SUCCESS('\n=== 필터링 결과 시각화 ===\n'))
        
        # CSV 파일 읽기
        if not os.path.exists(csv_path):
            error_msg = f'CSV 파일을 찾을 수 없습니다: {csv_path}'
            print(error_msg)
            self.stdout.write(self.style.ERROR(error_msg))
            return
        
        print(f'[1] CSV 파일 읽기: {csv_path}')
        self.stdout.write(f'[1] CSV 파일 읽기: {csv_path}')
        data = self._load_csv(csv_path)
        print(f'  - 총 {len(data)}개 데이터 로드\n')
        self.stdout.write(f'  - 총 {len(data)}개 데이터 로드\n')
        
        if limit:
            data = data[:limit]
            print(f'  - 제한 적용: {limit}개만 처리\n')
            self.stdout.write(f'  - 제한 적용: {limit}개만 처리\n')
        
        # 카테고리 설정 - Product 모델의 실제 카테고리 사용
        # TV, KITCHEN, LIVING, AIR, AI, OBJET, SIGNATURE (7개)
        if categories is None:
            categories = sorted(list(Product.objects.values_list('category', flat=True).distinct()))
            print(f'[1-1] 카테고리 자동 감지 ({len(categories)}개): {categories}')
            self.stdout.write(f'[1-1] 카테고리 자동 감지 ({len(categories)}개): {categories}')
        else:
            print(f'[1-1] 지정된 카테고리 ({len(categories)}개): {categories}')
            self.stdout.write(f'[1-1] 지정된 카테고리 ({len(categories)}개): {categories}')
        
        # 추천 엔진 초기화
        print('[2] 추천 엔진 초기화...')
        self.stdout.write('[2] 추천 엔진 초기화...')
        engine = RecommendationEngine()
        
        # 결과 수집
        print(f'\n[3] 필터링 분석 중... (총 {len(data)}개 케이스)')
        self.stdout.write(f'\n[3] 필터링 분석 중... (총 {len(data)}개 케이스)')
        all_results = []
        filter_stats = defaultdict(int)  # 필터별 제외 통계
        
        for idx, row in enumerate(data, 1):
            if idx % 10 == 0 or idx == 1:
                progress_msg = f'  진행 중: {idx}/{len(data)}...'
                print(progress_msg)
                self.stdout.write(progress_msg)
            
            try:
                result = self._analyze_filtering(engine, row, categories)
                all_results.append(result)
                
                # 필터별 통계 수집
                for excluded in result.get('excluded_products', []):
                    for reason in excluded.get('reasons', []):
                        filter_stats[reason] += 1
                        
            except Exception as e:
                error_msg = f'  [오류] taste_id {row.get("taste_id", "?")}: {e}'
                print(error_msg)
                import traceback
                traceback.print_exc()
                self.stdout.write(self.style.ERROR(error_msg))
                all_results.append({
                    'taste_id': row.get('taste_id', '?'),
                    'success': False,
                    'error': str(e),
                })
        
        # 결과 출력 (터미널)
        print(f'\n[4] 결과 출력...')
        self.stdout.write(f'\n[4] 결과 출력...')
        self._print_summary(all_results, filter_stats)
        
        # HTML 리포트 생성 (옵션)
        if output_path:
            print(f'\n[5] HTML 리포트 생성 중...')
            self.stdout.write(f'\n[5] HTML 리포트 생성 중...')
            self._generate_html_report(all_results, filter_stats, output_path)
            success_msg = f'\n[완료] 리포트 생성 완료!'
            file_msg = f'[FILE] {output_path}'
            print(success_msg)
            print(file_msg)
            self.stdout.write(self.style.SUCCESS(success_msg))
            self.stdout.write(file_msg)

    def _load_csv(self, csv_path):
        """CSV 파일 로드"""
        data = []
        with open(csv_path, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            for row in reader:
                data.append(row)
        return data

    def _analyze_filtering(self, engine, row, categories):
        """단일 케이스 필터링 분석"""
        taste_id = int(row.get('taste_id', 0))
        
        # CSV 데이터를 user_profile로 변환
        user_profile = self._csv_to_user_profile(row, categories)
        
        # Step 1: 기본 필터 전 제품 수집
        from api.services.recommendation_engine import RecommendationEngine
        budget_level = user_profile.get('budget_level', 'medium')
        min_price, max_price = engine.budget_mapping.get(
            budget_level,
            engine.budget_mapping['medium']
        )
        
        # 기본 필터만 적용한 제품 (필터링 전)
        products_before = (
            Product.objects
            .filter(
                is_active=True,
                category__in=categories,
                price__gte=min_price,
                price__lte=max_price,
                price__gt=0,
                spec__isnull=False,
            )
        )
        
        # 반려동물 필터
        has_pet = user_profile.get('has_pet', False) or user_profile.get('pet') in ['yes', 'Y', True, 'true', 'True']
        if not has_pet:
            pet_keywords = ['펫', 'PET', '반려동물', '애완동물', '동물케어', '펫케어', 'PET CARE']
            pet_filter = Q()
            for keyword in pet_keywords:
                pet_filter |= Q(name__icontains=keyword) | Q(description__icontains=keyword)
            products_before = products_before.exclude(pet_filter)
        
        products_before_list = list(products_before)
        
        # Step 2: 추가 필터 적용 (필터링 후)
        excluded_products = []
        excluded_reasons = defaultdict(list)
        
        for product in products_before_list:
            reasons = []
            
            # 가족 구성 필터
            if not filter_by_household_size(product, user_profile.get('household_size', 2)):
                reasons.append('가족 구성 (용량)')
            
            # 주거 형태 필터
            if not filter_by_housing_type(product, user_profile.get('housing_type', 'apartment'), user_profile.get('pyung', 25)):
                reasons.append('주거 형태/평수 (크기)')
            
            # 생활 패턴 필터
            if not filter_by_lifestyle(product, user_profile):
                reasons.append('생활 패턴')
            
            # 우선순위 필터
            if not filter_by_priority(product, user_profile):
                reasons.append('우선순위')
            
            # 제외된 제품 기록
            if reasons:
                excluded_products.append({
                    'product_id': product.id,
                    'product_name': product.name,
                    'category': product.category,
                    'price': float(product.price) if product.price else 0,
                    'reasons': reasons,
                })
                for reason in reasons:
                    excluded_reasons[reason].append(product.id)
        
        # 필터링 후 제품 (포함된 제품)
        products_after = [p for p in products_before_list if p.id not in [ep['product_id'] for ep in excluded_products]]
        
        # 추천 실행 (필터링 후 제품으로)
        # 주의: get_recommendations는 내부적으로 다시 필터링을 적용하므로
        # 여기서는 필터링 후 제품 수만 확인하고, 실제 추천은 실행하지 않음
        # (또는 필터링된 제품으로만 추천하도록 수정 필요)
        recommendations = []
        
        return {
            'taste_id': taste_id,
            'interior_style': row.get('인테리어_스타일', ''),
            'mate': row.get('메이트_구성', ''),
            'priority': row.get('우선순위', ''),
            'budget': row.get('예산_범위', ''),
            'user_profile': user_profile,
            'products_before_count': len(products_before_list),
            'products_after_count': len(products_after),
            'excluded_count': len(excluded_products),
            'excluded_products': excluded_products,
            'excluded_reasons_summary': dict(excluded_reasons),
            'recommendations_count': len(recommendations),
            'recommendations': recommendations,
            'success': True,
        }

    def _csv_to_user_profile(self, row, categories):
        """CSV 행을 user_profile로 변환"""
        # 메이트 구성 파싱
        mate = row.get('메이트_구성', '')
        household_size = 2  # 기본값
        if '1인' in mate or '혼자' in mate:
            household_size = 1
        elif '2인' in mate or '신혼' in mate or '둘이' in mate:
            household_size = 2
        elif '3~4인' in mate or '3-4인' in mate:
            household_size = 4
        elif '5인' in mate or '5인 이상' in mate:
            household_size = 5
        
        # 우선순위 파싱
        priority_text = row.get('우선순위', '')
        priority = 'value'
        if '디자인' in priority_text:
            priority = 'design'
        elif 'AI' in priority_text or '스마트' in priority_text or '기술' in priority_text:
            priority = 'tech'
        elif '에너지' in priority_text or '효율' in priority_text:
            priority = 'eco'
        elif '가격' in priority_text or '가성비' in priority_text:
            priority = 'value'
        
        # 예산 범위 파싱
        budget_text = row.get('예산_범위', '')
        budget_level = 'medium'
        if '500만원 미만' in budget_text or '실속형' in budget_text:
            budget_level = 'low'
        elif '500만원 ~ 1,500만원' in budget_text or '표준형' in budget_text:
            budget_level = 'medium'
        elif '1,500만원 ~ 3,000만원' in budget_text or '고급형' in budget_text:
            budget_level = 'high'
        elif '3,000만원 이상' in budget_text or '하이엔드' in budget_text:
            budget_level = 'high'
        
        # 인테리어 스타일 파싱
        interior = row.get('인테리어_스타일', '')
        vibe = 'modern'
        if '모던' in interior or '미니멀' in interior:
            vibe = 'modern'
        elif '코지' in interior or '따뜻' in interior:
            vibe = 'cozy'
        elif '럭셔리' in interior or '프리미엄' in interior:
            vibe = 'luxury'
        elif '유니크' in interior or '팝' in interior:
            vibe = 'unique'
        
        return {
            'vibe': vibe,
            'household_size': household_size,
            'housing_type': 'apartment',  # 기본값
            'pyung': 25,  # 기본값
            'priority': priority,
            'budget_level': budget_level,
            'categories': categories,
            'has_pet': False,  # 기본값
            'cooking': 'sometimes',  # 기본값
            'laundry': 'weekly',  # 기본값
            'media': 'balanced',  # 기본값
        }

    def _print_summary(self, results, filter_stats):
        """터미널에 요약 출력"""
        successful_results = [r for r in results if r.get('success')]
        
        if not successful_results:
            print("\n❌ 성공한 케이스가 없습니다.")
            return
        
        print("\n" + "="*80)
        print("📊 필터링 결과 요약")
        print("="*80)
        
        # 전체 통계
        total_cases = len(successful_results)
        avg_before = sum(r.get('products_before_count', 0) for r in successful_results) / total_cases
        avg_after = sum(r.get('products_after_count', 0) for r in successful_results) / total_cases
        avg_excluded = sum(r.get('excluded_count', 0) for r in successful_results) / total_cases
        
        print(f"\n✅ 총 케이스: {total_cases}개")
        print(f"📦 평균 필터링 전: {avg_before:.1f}개")
        print(f"✅ 평균 필터링 후: {avg_after:.1f}개")
        print(f"❌ 평균 제외된 수: {avg_excluded:.1f}개")
        print(f"📉 필터링 효과: {(avg_excluded/avg_before*100):.1f}% 제외")
        
        # 필터별 통계
        print("\n" + "-"*80)
        print("🔍 필터별 제외 통계")
        print("-"*80)
        for filter_name, count in sorted(filter_stats.items(), key=lambda x: x[1], reverse=True):
            print(f"  {filter_name}: {count:,}개")
        
        # 상위 10개 케이스 상세
        print("\n" + "-"*80)
        print("📋 케이스별 상세 결과 (상위 10개)")
        print("-"*80)
        print(f"{'ID':<6} {'인테리어':<20} {'가구':<15} {'전':<6} {'후':<6} {'제외':<6} {'추천':<6}")
        print("-"*80)
        
        for result in successful_results[:10]:
            taste_id = result.get('taste_id', '?')
            interior = (result.get('interior_style', '')[:18] + '..') if len(result.get('interior_style', '')) > 20 else result.get('interior_style', '')
            mate = (result.get('mate', '')[:13] + '..') if len(result.get('mate', '')) > 15 else result.get('mate', '')
            before = result.get('products_before_count', 0)
            after = result.get('products_after_count', 0)
            excluded = result.get('excluded_count', 0)
            rec_count = result.get('recommendations_count', 0)
            
            print(f"{taste_id:<6} {interior:<20} {mate:<15} {before:<6} {after:<6} {excluded:<6} {rec_count:<6}")
        
        # 제외된 제품 예시 (첫 번째 케이스)
        if successful_results:
            first_result = successful_results[0]
            excluded_products = first_result.get('excluded_products', [])
            if excluded_products:
                print("\n" + "-"*80)
                print(f"📌 케이스 {first_result.get('taste_id')}의 제외된 제품 예시 (최대 5개)")
                print("-"*80)
                for ep in excluded_products[:5]:
                    reasons = ', '.join(ep.get('reasons', []))
                    print(f"  ❌ {ep.get('product_name', '')[:40]} ({ep.get('category', '')})")
                    print(f"     제외 이유: {reasons}")
        
        print("\n" + "="*80)
    
    def _generate_html_report(self, results, filter_stats, output_path):
        """HTML 리포트 생성"""
        html = f"""<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>필터링 결과 시각화 리포트</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: #f5f5f5;
            padding: 20px;
        }}
        .container {{
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #333;
            margin-bottom: 10px;
        }}
        .summary {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin: 30px 0;
        }}
        .summary-card {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 8px;
            text-align: center;
        }}
        .summary-card h3 {{
            font-size: 14px;
            opacity: 0.9;
            margin-bottom: 10px;
        }}
        .summary-card .value {{
            font-size: 32px;
            font-weight: bold;
        }}
        .chart-container {{
            margin: 30px 0;
            padding: 20px;
            background: #fafafa;
            border-radius: 8px;
        }}
        .case-table {{
            width: 100%;
            border-collapse: collapse;
            margin: 30px 0;
        }}
        .case-table th {{
            background: #667eea;
            color: white;
            padding: 12px;
            text-align: left;
            font-weight: 600;
        }}
        .case-table td {{
            padding: 12px;
            border-bottom: 1px solid #eee;
        }}
        .case-table tr:hover {{
            background: #f5f5f5;
        }}
        .badge {{
            display: inline-block;
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 12px;
            font-weight: 600;
        }}
        .badge-success {{
            background: #10b981;
            color: white;
        }}
        .badge-warning {{
            background: #f59e0b;
            color: white;
        }}
        .badge-danger {{
            background: #ef4444;
            color: white;
        }}
        .excluded-products {{
            max-height: 200px;
            overflow-y: auto;
            margin-top: 10px;
        }}
        .excluded-product-item {{
            padding: 8px;
            background: #fee;
            margin: 4px 0;
            border-radius: 4px;
            font-size: 12px;
        }}
        .reason-tag {{
            display: inline-block;
            padding: 2px 6px;
            background: #ef4444;
            color: white;
            border-radius: 3px;
            font-size: 11px;
            margin: 2px;
        }}
        .filter-stats {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 15px;
            margin: 20px 0;
        }}
        .filter-stat-item {{
            padding: 15px;
            background: #f9fafb;
            border-left: 4px solid #667eea;
            border-radius: 4px;
        }}
        .filter-stat-item h4 {{
            color: #667eea;
            margin-bottom: 8px;
        }}
        .filter-stat-item .count {{
            font-size: 24px;
            font-weight: bold;
            color: #333;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>📊 필터링 결과 시각화 리포트</h1>
        <p style="color: #666; margin-bottom: 30px;">온보딩 케이스별 필터링 전/후 제품 수 및 제외된 제품 분석</p>
        
        <!-- 요약 통계 -->
        <div class="summary">
            <div class="summary-card">
                <h3>총 케이스 수</h3>
                <div class="value">{len(results)}</div>
            </div>
            <div class="summary-card">
                <h3>평균 필터링 전 제품 수</h3>
                <div class="value">{sum(r.get('products_before_count', 0) for r in results if r.get('success')) / max(1, sum(1 for r in results if r.get('success'))):.0f}</div>
            </div>
            <div class="summary-card">
                <h3>평균 필터링 후 제품 수</h3>
                <div class="value">{sum(r.get('products_after_count', 0) for r in results if r.get('success')) / max(1, sum(1 for r in results if r.get('success'))):.0f}</div>
            </div>
            <div class="summary-card">
                <h3>평균 제외된 제품 수</h3>
                <div class="value">{sum(r.get('excluded_count', 0) for r in results if r.get('success')) / max(1, sum(1 for r in results if r.get('success'))):.0f}</div>
            </div>
        </div>
        
        <!-- 필터별 제외 통계 -->
        <div class="filter-stats">
            <h2 style="grid-column: 1 / -1; margin: 30px 0 15px 0;">필터별 제외 통계</h2>
"""
        
        # 필터별 통계 추가
        for filter_name, count in sorted(filter_stats.items(), key=lambda x: x[1], reverse=True):
            html += f"""
            <div class="filter-stat-item">
                <h4>{filter_name}</h4>
                <div class="count">{count:,}개</div>
            </div>
"""
        
        html += """
        </div>
        
        <!-- 차트 -->
        <div class="chart-container">
            <h2>필터링 효과 차트</h2>
            <canvas id="filteringChart" width="400" height="200"></canvas>
        </div>
        
        <!-- 케이스별 상세 테이블 -->
        <h2 style="margin: 40px 0 20px 0;">케이스별 상세 결과</h2>
        <table class="case-table">
            <thead>
                <tr>
                    <th>taste_id</th>
                    <th>인테리어</th>
                    <th>가구 구성</th>
                    <th>우선순위</th>
                    <th>필터링 전</th>
                    <th>필터링 후</th>
                    <th>제외된 수</th>
                    <th>추천 수</th>
                    <th>제외된 제품</th>
                </tr>
            </thead>
            <tbody>
"""
        
        # 케이스별 데이터 추가
        for result in results:
            if not result.get('success'):
                continue
            
            excluded_html = ""
            excluded_products = result.get('excluded_products', [])
            if excluded_products:
                excluded_html = '<div class="excluded-products">'
                for ep in excluded_products[:5]:  # 최대 5개만 표시
                    reasons_html = ''.join([f'<span class="reason-tag">{r}</span>' for r in ep.get('reasons', [])])
                    excluded_html += f'''
                    <div class="excluded-product-item">
                        <strong>{ep.get("product_name", "")}</strong> ({ep.get("category", "")})<br>
                        {reasons_html}
                    </div>
'''
                if len(excluded_products) > 5:
                    excluded_html += f'<div style="padding: 8px; color: #666;">... 외 {len(excluded_products) - 5}개</div>'
                excluded_html += '</div>'
            else:
                excluded_html = '<span style="color: #10b981;">없음</span>'
            
            html += f"""
                <tr>
                    <td><strong>{result.get('taste_id', '')}</strong></td>
                    <td>{result.get('interior_style', '')[:20]}...</td>
                    <td>{result.get('mate', '')[:20]}...</td>
                    <td>{result.get('priority', '')[:20]}...</td>
                    <td><span class="badge badge-warning">{result.get('products_before_count', 0)}</span></td>
                    <td><span class="badge badge-success">{result.get('products_after_count', 0)}</span></td>
                    <td><span class="badge badge-danger">{result.get('excluded_count', 0)}</span></td>
                    <td>{result.get('recommendations_count', 0)}</td>
                    <td>{excluded_html}</td>
                </tr>
"""
        
        html += """
            </tbody>
        </table>
    </div>
    
    <script>
        // 차트 데이터 준비
        const results = """ + json.dumps([{
            'taste_id': r.get('taste_id'),
            'before': r.get('products_before_count', 0),
            'after': r.get('products_after_count', 0),
            'excluded': r.get('excluded_count', 0),
        } for r in results if r.get('success')]) + """;
        
        // 필터링 효과 차트
        const ctx = document.getElementById('filteringChart').getContext('2d');
        new Chart(ctx, {
            type: 'bar',
            data: {
                labels: results.slice(0, 20).map(r => '케이스 ' + r.taste_id),
                datasets: [
                    {
                        label: '필터링 전',
                        data: results.slice(0, 20).map(r => r.before),
                        backgroundColor: 'rgba(255, 159, 64, 0.6)',
                    },
                    {
                        label: '필터링 후',
                        data: results.slice(0, 20).map(r => r.after),
                        backgroundColor: 'rgba(75, 192, 192, 0.6)',
                    },
                    {
                        label: '제외된 수',
                        data: results.slice(0, 20).map(r => r.excluded),
                        backgroundColor: 'rgba(255, 99, 132, 0.6)',
                    }
                ]
            },
            options: {
                responsive: true,
                scales: {
                    y: {
                        beginAtZero: true
                    }
                }
            }
        });
    </script>
</body>
</html>
"""
        
        # HTML 파일 저장
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html)

