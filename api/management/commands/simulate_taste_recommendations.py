"""
taste_recommendations_768.csv의 모든 케이스에 대해 추천 시뮬레이션 실행

각 taste_id에 대해:
1. 추천 엔진 실행
2. 추천된 제품군(카테고리)과 점수 수집
3. 사용된 scoring logic 정보 수집
4. 결과 요약 출력

사용법:
    python manage.py simulate_taste_recommendations
    python manage.py simulate_taste_recommendations --limit 10  # 처음 10개만
    python manage.py simulate_taste_recommendations --output results.json  # JSON 출력
"""
import csv
import json
import os
from collections import defaultdict
from pathlib import Path
from django.core.management.base import BaseCommand
from api.services.recommendation_engine import RecommendationEngine
from api.utils.taste_scoring import get_logic_for_taste_id


class Command(BaseCommand):
    help = 'taste_recommendations_768.csv의 모든 케이스에 대해 추천 시뮬레이션 실행'

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
            default=None,
            help='결과를 JSON 파일로 저장할 경로',
        )
        parser.add_argument(
            '--categories',
            type=str,
            nargs='+',
            default=None,  # None이면 DB에 있는 모든 카테고리 사용
            help='테스트할 카테고리 목록 (지정하지 않으면 DB에 있는 모든 카테고리 사용)',
        )

    def handle(self, *args, **options):
        csv_path = options['csv_path']
        limit = options['limit']
        output_path = options['output']
        categories = options['categories']
        
        self.stdout.write(self.style.SUCCESS('\n=== 취향별 추천 시뮬레이션 ===\n'))
        
        # CSV 파일 읽기
        if not os.path.exists(csv_path):
            self.stdout.write(self.style.ERROR(f'CSV 파일을 찾을 수 없습니다: {csv_path}'))
            return
        
        self.stdout.write(f'[1] CSV 파일 읽기: {csv_path}')
        data = self._load_csv(csv_path)
        self.stdout.write(f'  - 총 {len(data)}개 데이터 로드\n')
        
        if limit:
            data = data[:limit]
            self.stdout.write(f'  - 제한 적용: {limit}개만 처리\n')
        
        # 카테고리 설정 (지정하지 않으면 DB에 있는 모든 카테고리 사용)
        if categories is None:
            from api.models import Product
            categories = sorted(list(Product.objects.values_list('category', flat=True).distinct()))
            self.stdout.write(f'[1-1] 카테고리 자동 감지: {categories}')
        else:
            self.stdout.write(f'[1-1] 지정된 카테고리: {categories}')
        
        # 추천 엔진 초기화
        self.stdout.write('[2] 추천 엔진 초기화...')
        engine = RecommendationEngine()
        
        # 결과 수집
        self.stdout.write(f'\n[3] 시뮬레이션 실행 중... (총 {len(data)}개 케이스)')
        results = []
        category_stats = defaultdict(lambda: {'count': 0, 'total_score': 0.0, 'scores': []})
        logic_stats = defaultdict(lambda: {'count': 0, 'categories': defaultdict(int)})
        taste_to_categories = defaultdict(lambda: defaultdict(list))  # taste_id별 카테고리별 추천 제품
        
        for idx, row in enumerate(data, 1):
            if idx % 50 == 0:
                self.stdout.write(f'  진행 중: {idx}/{len(data)}...')
            
            try:
                result = self._simulate_single_case(engine, row, categories)
                results.append(result)
                
                # 카테고리별 통계
                for rec in result['recommendations']:
                    cat = rec['category']
                    score = rec['score']
                    category_stats[cat]['count'] += 1
                    category_stats[cat]['total_score'] += score
                    category_stats[cat]['scores'].append(score)
                
                # Logic별 통계
                logic_id = result.get('logic_id', 'default')
                for rec in result['recommendations']:
                    logic_stats[logic_id]['count'] += 1
                    logic_stats[logic_id]['categories'][rec['category']] += 1
                
                # taste_id별 카테고리별 추천 수집
                taste_id = result.get('taste_id')
                for rec in result['recommendations']:
                    taste_to_categories[taste_id][rec['category']].append({
                        'model': rec['model'],
                        'score': rec['score']
                    })
                    
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'  [오류] taste_id {row.get("taste_id", "?")}: {e}'))
                results.append({
                    'taste_id': row.get('taste_id', '?'),
                    'success': False,
                    'error': str(e),
                    'recommendations': []
                })
        
        # 결과 출력
        self.stdout.write(f'\n[4] 결과 분석 및 출력...\n')
        self._print_summary(results, category_stats, logic_stats, taste_to_categories)
        
        # JSON 저장
        if output_path:
            self._save_json(results, output_path)
            self.stdout.write(f'\n[5] JSON 저장: {output_path}')
        
        self.stdout.write(self.style.SUCCESS(f'\n[완료] 시뮬레이션 완료!'))

    def _load_csv(self, csv_path):
        """CSV 파일 로드"""
        data = []
        with open(csv_path, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            for row in reader:
                data.append(row)
        return data

    def _simulate_single_case(self, engine, row, categories):
        """단일 케이스 시뮬레이션"""
        taste_id = int(row.get('taste_id', 0))
        
        # CSV 데이터를 user_profile로 변환
        user_profile = self._csv_to_user_profile(row, categories)
        
        # 취향 정보 준비 (CSV 행 전체를 taste_info로 전달)
        taste_info = {
            '인테리어_스타일': row.get('인테리어_스타일', ''),
            '메이트_구성': row.get('메이트_구성', ''),
            '우선순위': row.get('우선순위', ''),
            '예산_범위': row.get('예산_범위', ''),
            '선호_라인업': row.get('선호_라인업', ''),
            '리뷰_기반_추천문구': row.get('리뷰_기반_추천문구', ''),
            'AI_기반_추천문구': row.get('AI_기반_추천문구', ''),
        }
        
        # 추천 실행
        result = engine.get_recommendations(
            user_profile=user_profile,
            limit=10,  # 상위 10개까지
            taste_id=taste_id,
            taste_info=taste_info
        )
        
        # Logic 정보 가져오기
        logic = get_logic_for_taste_id(taste_id)
        logic_id = None
        logic_name = None
        if logic:
            logic_id = logic.get('logic_id', f'logic_{taste_id}')
            logic_name = logic.get('name', logic_id)
        
        # 결과 포맷팅
        recommendations = result.get('recommendations', [])
        
        # 각 추천에 추천 문구 추가 (이미 포함되어 있지만 확인)
        for rec in recommendations:
            if 'reason' not in rec or not rec.get('reason'):
                # 추천 문구가 없으면 기본값
                rec['reason'] = "조건에 맞는 추천 제품입니다."
        
        return {
            'taste_id': taste_id,
            'interior_style': row.get('인테리어_스타일', ''),
            'mate': row.get('메이트_구성', ''),
            'priority': row.get('우선순위', ''),
            'budget': row.get('예산_범위', ''),
            'success': result.get('success', False),
            'logic_id': logic_id,
            'logic_name': logic_name,
            'recommendations': recommendations,
            'recommendation_count': len(recommendations),
            'review_based_reason': row.get('리뷰_기반_추천문구', '')[:100],  # 샘플
        }

    def _csv_to_user_profile(self, row, categories):
        """CSV 행을 user_profile 딕셔너리로 변환"""
        # 인테리어 스타일 매핑
        interior = row.get('인테리어_스타일', '')
        vibe_map = {
            '모던 & 미니멀': 'modern',
            '코지 & 네이처': 'cozy',
            '럭셔리 & 아티스틱': 'luxury',
            '유니크 & 팝': 'unique',
        }
        vibe = 'modern'
        for key, value in vibe_map.items():
            if key in interior:
                vibe = value
                break
        
        # 메이트 구성 매핑
        mate = row.get('메이트_구성', '')
        household_size = 2
        if '1인' in mate or '혼자' in mate:
            household_size = 1
        elif '2인' in mate or '신혼' in mate:
            household_size = 2
        elif '3~4인' in mate or '3인' in mate or '4인' in mate:
            household_size = 4
        elif '5인' in mate or '대가족' in mate:
            household_size = 5
        
        # 우선순위 매핑
        priority = row.get('우선순위', '')
        priority_map = {
            '디자인': 'design',
            'AI/스마트': 'tech',
            '에너지 효율': 'eco',
            '가성비': 'value',
            '인테리어': 'design',
        }
        priority_value = 'value'
        for key, value in priority_map.items():
            if key in priority:
                priority_value = value
                break
        
        # 예산 범위 매핑
        budget = row.get('예산_범위', '')
        budget_map = {
            '500만원 미만': 'low',
            '500만원~1000만원': 'medium',
            '1000만원~2000만원': 'high',
            '2000만원 이상': 'high',
            '실속형': 'low',
            '표준형': 'medium',
            '고급형': 'high',
            '하이엔드': 'high',
        }
        budget_level = 'medium'
        for key, value in budget_map.items():
            if key in budget:
                budget_level = value
                break
        
        return {
            'vibe': vibe,
            'household_size': household_size,
            'priority': priority_value,
            'budget_level': budget_level,
            'categories': categories,
            'has_pet': False,  # 기본값
        }

    def _print_summary(self, results, category_stats, logic_stats, taste_to_categories):
        """결과 요약 출력"""
        total_cases = len(results)
        success_cases = sum(1 for r in results if r.get('success', False))
        
        self.stdout.write('\n' + '='*80)
        self.stdout.write('시뮬레이션 결과 요약')
        self.stdout.write('='*80)
        self.stdout.write(f'\n전체 케이스: {total_cases}개')
        self.stdout.write(f'성공: {success_cases}개 ({success_cases/total_cases*100:.1f}%)')
        self.stdout.write(f'실패: {total_cases - success_cases}개')
        
        # 카테고리별 통계
        self.stdout.write('\n' + '-'*80)
        self.stdout.write('카테고리별 추천 통계')
        self.stdout.write('-'*80)
        for category in sorted(category_stats.keys()):
            stats = category_stats[category]
            avg_score = stats['total_score'] / stats['count'] if stats['count'] > 0 else 0
            min_score = min(stats['scores']) if stats['scores'] else 0
            max_score = max(stats['scores']) if stats['scores'] else 0
            self.stdout.write(f'\n{category}:')
            self.stdout.write(f'  추천 횟수: {stats["count"]}회')
            self.stdout.write(f'  평균 점수: {avg_score:.3f}')
            self.stdout.write(f'  점수 범위: {min_score:.3f} ~ {max_score:.3f}')
        
        # Logic별 통계
        self.stdout.write('\n' + '-'*80)
        self.stdout.write('Scoring Logic별 통계')
        self.stdout.write('-'*80)
        for logic_id in sorted(logic_stats.keys()):
            stats = logic_stats[logic_id]
            self.stdout.write(f'\n{logic_id}:')
            self.stdout.write(f'  사용 횟수: {stats["count"]}회')
            self.stdout.write(f'  추천된 카테고리:')
            for cat, count in sorted(stats['categories'].items(), key=lambda x: -x[1]):
                self.stdout.write(f'    - {cat}: {count}회')
        
        # 카테고리별 상세 통계
        self.stdout.write('\n' + '-'*80)
        self.stdout.write('카테고리별 상세 통계 (제품군별 추천 횟수 및 점수)')
        self.stdout.write('-'*80)
        for category in sorted(category_stats.keys()):
            stats = category_stats[category]
            avg_score = stats['total_score'] / stats['count'] if stats['count'] > 0 else 0
            min_score = min(stats['scores']) if stats['scores'] else 0
            max_score = max(stats['scores']) if stats['scores'] else 0
            
            # 점수 분포
            high_scores = sum(1 for s in stats['scores'] if s >= 0.8)
            mid_scores = sum(1 for s in stats['scores'] if 0.5 <= s < 0.8)
            low_scores = sum(1 for s in stats['scores'] if s < 0.5)
            
            self.stdout.write(f'\n{category}:')
            self.stdout.write(f'  총 추천 횟수: {stats["count"]}회')
            self.stdout.write(f'  평균 점수: {avg_score:.3f}')
            self.stdout.write(f'  점수 범위: {min_score:.3f} ~ {max_score:.3f}')
            self.stdout.write(f'  점수 분포: 높음(≥0.8) {high_scores}회, 중간(0.5~0.8) {mid_scores}회, 낮음(<0.5) {low_scores}회')
        
        # 샘플 결과 (상위 10개)
        self.stdout.write('\n' + '-'*80)
        self.stdout.write('샘플 결과 (처음 10개 케이스)')
        self.stdout.write('-'*80)
        for result in results[:10]:
            if result.get('success'):
                self.stdout.write(f'\n[taste_id: {result["taste_id"]}]')
                self.stdout.write(f'  취향: {result.get("interior_style", "")} / {result.get("mate", "")}')
                self.stdout.write(f'  우선순위: {result.get("priority", "")}')
                self.stdout.write(f'  예산: {result.get("budget", "")}')
                self.stdout.write(f'  사용된 Logic: {result.get("logic_id", "default")} ({result.get("logic_name", "")})')
                self.stdout.write(f'  추천 개수: {result["recommendation_count"]}개')
                self.stdout.write(f'  추천 제품군 및 점수:')
                
                # 카테고리별로 그룹화
                by_category = {}
                for rec in result['recommendations']:
                    cat = rec['category']
                    if cat not in by_category:
                        by_category[cat] = []
                    by_category[cat].append({
                        'model': rec['model'],
                        'score': rec['score'],
                        'reason': rec.get('reason', '')
                    })
                
                for cat in sorted(by_category.keys()):
                    self.stdout.write(f'    [{cat}]')
                    for item in by_category[cat][:3]:  # 카테고리당 상위 3개만
                        reason_preview = item['reason'][:50] + '...' if len(item['reason']) > 50 else item['reason']
                        self.stdout.write(f'      - {item["model"]}: {item["score"]:.3f}점')
                        self.stdout.write(f'        추천 문구: {reason_preview}')
            else:
                self.stdout.write(f'\n[taste_id: {result["taste_id"]}] 실패: {result.get("error", "알 수 없음")}')
        
        # 전체 taste_id별 제품군 추천 요약
        self.stdout.write('\n' + '='*80)
        self.stdout.write('전체 케이스별 제품군 추천 요약 (처음 20개)')
        self.stdout.write('='*80)
        for taste_id in sorted(taste_to_categories.keys())[:20]:
            self.stdout.write(f'\n[taste_id: {taste_id}]')
            for category in sorted(taste_to_categories[taste_id].keys()):
                items = taste_to_categories[taste_id][category]
                avg_score = sum(item['score'] for item in items) / len(items) if items else 0
                self.stdout.write(f'  {category}: {len(items)}개 추천, 평균 점수 {avg_score:.3f}')
                # 상위 1개만 표시
                if items:
                    top_item = max(items, key=lambda x: x['score'])
                    self.stdout.write(f'    → 최고점: {top_item["model"]} ({top_item["score"]:.3f}점)')

    def _save_json(self, results, output_path):
        """결과를 JSON 파일로 저장"""
        os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else '.', exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)

