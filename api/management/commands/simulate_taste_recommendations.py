"""
모든 Taste별 추천 제품군 시뮬레이션

각 taste_id (1~120)에 대해 추천 엔진을 실행하여
어떤 제품군(MAIN_CATEGORY)이 추천되는지 분석합니다.

사용법:
    python manage.py simulate_taste_recommendations
    python manage.py simulate_taste_recommendations --output results.json
    python manage.py simulate_taste_recommendations --format csv
    python manage.py simulate_taste_recommendations --visualize
"""
import json
import csv
import os
from collections import defaultdict
from pathlib import Path
from django.core.management.base import BaseCommand
from api.services.recommendation_engine import recommendation_engine

try:
    import matplotlib.pyplot as plt
    import matplotlib
    matplotlib.use('Agg')  # GUI 없이 사용
    import numpy as np
    HAS_VISUALIZATION = True
except ImportError:
    HAS_VISUALIZATION = False


class Command(BaseCommand):
    help = '모든 taste(1~120)별로 추천 제품군을 시뮬레이션합니다'

    def add_arguments(self, parser):
        parser.add_argument(
            '--output',
            type=str,
            default='data/simulation/taste_recommendations_simulation.json',
            help='결과 저장 경로 (JSON)',
        )
        parser.add_argument(
            '--format',
            type=str,
            choices=['json', 'csv', 'both'],
            default='both',
            help='출력 형식 (json, csv, both)',
        )
        parser.add_argument(
            '--taste-range',
            type=str,
            default='1-120',
            help='시뮬레이션할 taste 범위 (예: 1-120, 1-10)',
        )
        parser.add_argument(
            '--sample',
            action='store_true',
            help='샘플 모드 (taste 1-10만 실행)',
        )
        parser.add_argument(
            '--visualize',
            action='store_true',
            help='시각화 생성 (matplotlib 필요)',
        )
        parser.add_argument(
            '--no-visualize',
            action='store_true',
            help='시각화 생성 안 함',
        )

    def handle(self, *args, **options):
        output_path = options['output']
        output_format = options['format']
        taste_range = options['taste_range']
        sample_mode = options['sample']

        self.stdout.write(self.style.SUCCESS('\n=== Taste별 추천 제품군 시뮬레이션 ===\n'))

        # Taste 범위 파싱
        if sample_mode:
            taste_ids = list(range(1, 11))  # 샘플: 1-10
            self.stdout.write(f'[모드] 샘플 모드 (taste 1-10)\n')
        else:
            taste_ids = self._parse_taste_range(taste_range)
            self.stdout.write(f'[범위] Taste {taste_ids[0]} ~ {taste_ids[-1]} (총 {len(taste_ids)}개)\n')

        # 출력 디렉토리 생성
        output_dir = os.path.dirname(output_path)
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)

        def generate_onboarding_data_for_taste(taste_id: int) -> dict:
            """
            taste_id에 따라 다양한 onboarding_data 생성
            taste_id를 기반으로 다른 조합의 답변 생성
            """
            # taste_id를 기반으로 다양한 조합 생성
            vibes = ['modern', 'cozy', 'pop', 'luxury']
            household_sizes = [1, 2, 3, 4, 5]
            housing_types = ['apartment', 'detached', 'villa', 'officetel', 'studio']
            priorities = ['design', 'tech', 'eco', 'value']
            budget_levels = ['low', 'medium', 'high']
            main_spaces = ['living', 'kitchen', 'dressing', 'bedroom']
            cooking_options = ['daily', 'sometimes', 'rarely']
            laundry_options = ['daily', 'weekly', 'biweekly']
            media_options = ['balanced', 'entertainment', 'minimal']
            
            # taste_id를 기반으로 인덱스 생성 (다양한 조합 보장)
            idx = taste_id - 1  # 0-based index
            
            return {
                'vibe': vibes[idx % len(vibes)],
                'household_size': household_sizes[idx % len(household_sizes)],
                'housing_type': housing_types[idx % len(housing_types)],
                'pyung': 20 + (idx % 20),  # 20-39 평
                'priority': priorities[idx % len(priorities)],
                'budget_level': budget_levels[idx % len(budget_levels)],
                'has_pet': (idx % 3 == 0),  # 1/3 확률로 반려동물 있음
                'cooking': cooking_options[idx % len(cooking_options)],
                'laundry': laundry_options[idx % len(laundry_options)],
                'media': media_options[idx % len(media_options)],
                'main_space': main_spaces[idx % len(main_spaces)],
            }

        # 시뮬레이션 실행
        results = []
        category_stats = defaultdict(lambda: {'count': 0, 'tastes': []})

        self.stdout.write('[진행] 시뮬레이션 실행 중...\n')

        for idx, taste_id in enumerate(taste_ids, 1):
            try:
                self.stdout.write(f'[{idx}/{len(taste_ids)}] Taste {taste_id} 처리 중...', ending=' ')
                
                # taste_id에 따라 다른 onboarding_data 생성
                onboarding_data = generate_onboarding_data_for_taste(taste_id)
                
                # 사용자 프로필 생성 (taste_id별로 다른 데이터)
                user_profile = {
                    'vibe': onboarding_data['vibe'],
                    'household_size': onboarding_data['household_size'],
                    'housing_type': onboarding_data['housing_type'],
                    'pyung': onboarding_data['pyung'],
                    'priority': onboarding_data['priority'],
                    'budget_level': onboarding_data['budget_level'],
                    'has_pet': onboarding_data['has_pet'],
                    'cooking': onboarding_data['cooking'],
                    'laundry': onboarding_data['laundry'],
                    'media': onboarding_data['media'],
                    'main_space': onboarding_data['main_space'],
                    'categories': [],  # taste_id가 있으면 자동 선택되므로 빈 리스트
                    'onboarding_data': onboarding_data,  # answer_ID 추정용
                }

                # 추천 엔진 호출
                result = recommendation_engine.get_recommendations(
                    user_profile=user_profile,
                    taste_id=taste_id,
                    limit=10
                )

                if not result.get('success'):
                    self.stdout.write(self.style.WARNING(f'실패: {result.get("message", "알 수 없는 오류")}'))
                    continue

                recommendations = result.get('recommendations', [])
                
                # 카테고리별 집계
                categories = set()
                for rec in recommendations:
                    main_category = rec.get('main_category') or rec.get('category', '')
                    if main_category:
                        categories.add(main_category)
                        category_stats[main_category]['count'] += 1
                        if taste_id not in category_stats[main_category]['tastes']:
                            category_stats[main_category]['tastes'].append(taste_id)

                # 결과 저장
                taste_result = {
                    'taste_id': taste_id,
                    'success': True,
                    'recommendation_count': len(recommendations),
                    'categories': sorted(list(categories)),
                    'category_count': len(categories),
                    'recommendations': [
                        {
                            'product_id': rec.get('product_id'),
                            'name': rec.get('name') or rec.get('model'),
                            'main_category': rec.get('main_category'),
                            'category': rec.get('category'),
                            'score': rec.get('score'),
                            'price': rec.get('price'),
                        }
                        for rec in recommendations
                    ]
                }

                results.append(taste_result)
                self.stdout.write(self.style.SUCCESS(
                    f'완료: {len(categories)}개 카테고리, {len(recommendations)}개 제품'
                ))

            except Exception as e:
                self.stdout.write(self.style.ERROR(f'오류: {str(e)}'))
                results.append({
                    'taste_id': taste_id,
                    'success': False,
                    'error': str(e),
                    'categories': [],
                    'recommendation_count': 0
                })

        # 통계 계산
        self.stdout.write('\n[통계] 결과 집계 중...\n')

        summary = {
            'total_tastes': len(taste_ids),
            'successful_tastes': sum(1 for r in results if r.get('success')),
            'failed_tastes': sum(1 for r in results if not r.get('success')),
            'category_distribution': {
                cat: {
                    'recommendation_count': stats['count'],
                    'taste_count': len(stats['tastes']),
                    'taste_percentage': round(len(stats['tastes']) / len(taste_ids) * 100, 2),
                    'tastes': sorted(stats['tastes'])
                }
                for cat, stats in sorted(category_stats.items(), key=lambda x: x[1]['count'], reverse=True)
            },
            'average_categories_per_taste': round(
                sum(r.get('category_count', 0) for r in results if r.get('success')) / 
                max(sum(1 for r in results if r.get('success')), 1), 
                2
            ),
            'average_products_per_taste': round(
                sum(r.get('recommendation_count', 0) for r in results if r.get('success')) / 
                max(sum(1 for r in results if r.get('success')), 1), 
                2
            ),
        }

        # 결과 저장
        output_data = {
            'summary': summary,
            'results': results
        }

        # JSON 저장
        if output_format in ['json', 'both']:
            json_path = output_path if output_path.endswith('.json') else output_path.replace('.csv', '.json')
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, ensure_ascii=False, indent=2)
            self.stdout.write(self.style.SUCCESS(f'\n[JSON] 결과 저장: {json_path}'))

        # CSV 저장
        if output_format in ['csv', 'both']:
            csv_path = output_path if output_path.endswith('.csv') else output_path.replace('.json', '.csv')
            self._save_csv(csv_path, results, summary)
            self.stdout.write(self.style.SUCCESS(f'[CSV] 결과 저장: {csv_path}'))

        # 요약 출력
        self._print_summary(summary)

        # 시각화 생성
        if options.get('visualize') and not options.get('no_visualize'):
            if HAS_VISUALIZATION:
                self.stdout.write('\n[시각화] 그래프 생성 중...\n')
                viz_dir = os.path.join(os.path.dirname(output_path), 'visualization')
                os.makedirs(viz_dir, exist_ok=True)
                self._create_visualizations(output_data, viz_dir)
                self.stdout.write(self.style.SUCCESS(f'[시각화] 결과 저장: {viz_dir}'))
            else:
                self.stdout.write(self.style.WARNING(
                    '\n[시각화] matplotlib이 설치되지 않았습니다. '
                    '설치: pip install matplotlib numpy'
                ))

        self.stdout.write(self.style.SUCCESS('\n[완료] 시뮬레이션 완료!\n'))

    def _parse_taste_range(self, range_str: str) -> list:
        """Taste 범위 문자열 파싱 (예: "1-120", "1-10")"""
        try:
            if '-' in range_str:
                start, end = map(int, range_str.split('-'))
                return list(range(start, end + 1))
            else:
                return [int(range_str)]
        except:
            return list(range(1, 121))  # 기본값: 1-120

    def _save_csv(self, csv_path: str, results: list, summary: dict):
        """CSV 형식으로 저장"""
        with open(csv_path, 'w', encoding='utf-8-sig', newline='') as f:
            writer = csv.writer(f)
            
            # 헤더
            writer.writerow([
                'Taste ID',
                '성공 여부',
                '추천 제품 수',
                '카테고리 수',
                '카테고리 목록',
                '오류 메시지'
            ])
            
            # 데이터
            for result in results:
                categories_str = ', '.join(result.get('categories', []))
                writer.writerow([
                    result.get('taste_id'),
                    '성공' if result.get('success') else '실패',
                    result.get('recommendation_count', 0),
                    result.get('category_count', 0),
                    categories_str,
                    result.get('error', '')
                ])

        # 카테고리별 통계 CSV
        stats_csv_path = csv_path.replace('.csv', '_category_stats.csv')
        with open(stats_csv_path, 'w', encoding='utf-8-sig', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                '카테고리',
                '추천 횟수',
                '추천된 Taste 수',
                'Taste 비율 (%)',
                'Taste 목록'
            ])
            
            for cat, stats in sorted(
                summary['category_distribution'].items(),
                key=lambda x: x[1]['taste_count'],
                reverse=True
            ):
                tastes_str = ', '.join(map(str, stats['tastes']))
                writer.writerow([
                    cat,
                    stats['recommendation_count'],
                    stats['taste_count'],
                    stats['taste_percentage'],
                    tastes_str
                ])

    def _print_summary(self, summary: dict):
        """요약 정보 출력"""
        self.stdout.write('\n' + '=' * 60)
        self.stdout.write('시뮬레이션 요약')
        self.stdout.write('=' * 60)
        self.stdout.write(f"총 Taste 수: {summary['total_tastes']}개")
        self.stdout.write(f"성공: {summary['successful_tastes']}개")
        self.stdout.write(f"실패: {summary['failed_tastes']}개")
        self.stdout.write(f"Taste당 평균 카테고리 수: {summary['average_categories_per_taste']}개")
        self.stdout.write(f"Taste당 평균 제품 수: {summary['average_products_per_taste']}개")
        
        self.stdout.write('\n카테고리별 추천 통계:')
        self.stdout.write('-' * 60)
        for cat, stats in sorted(
            summary['category_distribution'].items(),
            key=lambda x: x[1]['taste_count'],
            reverse=True
        ):
            self.stdout.write(
                f"  {cat:20s} | "
                f"추천 횟수: {stats['recommendation_count']:4d} | "
                f"Taste 수: {stats['taste_count']:3d}개 "
                f"({stats['taste_percentage']:5.1f}%)"
            )

    def _create_visualizations(self, output_data: dict, output_dir: str):
        """시각화 생성"""
        if not HAS_VISUALIZATION:
            return

        summary = output_data['summary']
        results = output_data['results']

        # 한글 폰트 설정
        plt.rcParams['font.family'] = 'Malgun Gothic'  # Windows
        plt.rcParams['axes.unicode_minus'] = False

        # 1. 카테고리별 추천 분포 (Bar Chart)
        fig, axes = plt.subplots(2, 2, figsize=(16, 12))

        # 1-1. 카테고리별 Taste 수 (상위 10개)
        category_dist = summary['category_distribution']
        sorted_cats = sorted(
            category_dist.items(),
            key=lambda x: x[1]['taste_count'],
            reverse=True
        )[:10]

        cats = [cat for cat, _ in sorted_cats]
        taste_counts = [stats['taste_count'] for _, stats in sorted_cats]
        percentages = [stats['taste_percentage'] for _, stats in sorted_cats]

        axes[0, 0].barh(range(len(cats)), taste_counts, color='skyblue')
        axes[0, 0].set_yticks(range(len(cats)))
        axes[0, 0].set_yticklabels(cats)
        axes[0, 0].set_xlabel('추천된 Taste 수')
        axes[0, 0].set_title('카테고리별 추천 Taste 수 (상위 10개)')
        axes[0, 0].grid(True, alpha=0.3, axis='x')
        
        # 값 표시
        for i, (count, pct) in enumerate(zip(taste_counts, percentages)):
            axes[0, 0].text(count + 1, i, f'{count}개 ({pct:.1f}%)', 
                          va='center', fontsize=9)

        # 1-2. 카테고리별 추천 횟수
        rec_counts = [stats['recommendation_count'] for _, stats in sorted_cats]
        axes[0, 1].barh(range(len(cats)), rec_counts, color='lightcoral')
        axes[0, 1].set_yticks(range(len(cats)))
        axes[0, 1].set_yticklabels(cats)
        axes[0, 1].set_xlabel('추천 횟수')
        axes[0, 1].set_title('카테고리별 총 추천 횟수 (상위 10개)')
        axes[0, 1].grid(True, alpha=0.3, axis='x')
        
        for i, count in enumerate(rec_counts):
            axes[0, 1].text(count + 5, i, f'{count}회', 
                          va='center', fontsize=9)

        # 1-3. Taste별 카테고리 수 분포
        category_counts = [r.get('category_count', 0) for r in results if r.get('success')]
        if category_counts:
            axes[1, 0].hist(category_counts, bins=range(0, max(category_counts) + 2), 
                          color='lightgreen', edgecolor='black', alpha=0.7)
            axes[1, 0].set_xlabel('카테고리 수')
            axes[1, 0].set_ylabel('Taste 수')
            axes[1, 0].set_title('Taste별 추천 카테고리 수 분포')
            axes[1, 0].grid(True, alpha=0.3, axis='y')
            axes[1, 0].axvline(np.mean(category_counts), color='red', linestyle='--',
                             label=f'평균: {np.mean(category_counts):.1f}개')
            axes[1, 0].legend()

        # 1-4. Taste별 제품 수 분포
        product_counts = [r.get('recommendation_count', 0) for r in results if r.get('success')]
        if product_counts:
            axes[1, 1].hist(product_counts, bins=range(0, max(product_counts) + 2),
                          color='gold', edgecolor='black', alpha=0.7)
            axes[1, 1].set_xlabel('추천 제품 수')
            axes[1, 1].set_ylabel('Taste 수')
            axes[1, 1].set_title('Taste별 추천 제품 수 분포')
            axes[1, 1].grid(True, alpha=0.3, axis='y')
            axes[1, 1].axvline(np.mean(product_counts), color='red', linestyle='--',
                             label=f'평균: {np.mean(product_counts):.1f}개')
            axes[1, 1].legend()

        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, 'category_distribution.png'), 
                   dpi=300, bbox_inches='tight')
        plt.close()
        self.stdout.write('  - 카테고리 분포 그래프 저장: category_distribution.png')

        # 2. 카테고리 히트맵 (Taste × Category)
        self._create_heatmap(results, summary, output_dir)

        # 3. 통계 요약 그래프
        self._create_summary_charts(summary, output_dir)

    def _create_heatmap(self, results: list, summary: dict, output_dir: str):
        """Taste × Category 히트맵 생성"""
        # Taste별 카테고리 매트릭스 생성
        taste_ids = sorted([r['taste_id'] for r in results if r.get('success')])
        categories = sorted(summary['category_distribution'].keys())
        
        if not taste_ids or not categories:
            return

        matrix = np.zeros((len(taste_ids), len(categories)))
        taste_to_idx = {tid: idx for idx, tid in enumerate(taste_ids)}
        cat_to_idx = {cat: idx for idx, cat in enumerate(categories)}

        for result in results:
            if not result.get('success'):
                continue
            taste_idx = taste_to_idx[result['taste_id']]
            for cat in result.get('categories', []):
                if cat in cat_to_idx:
                    cat_idx = cat_to_idx[cat]
                    matrix[taste_idx, cat_idx] = 1

        # 히트맵 생성 (샘플링: 너무 크면 일부만)
        max_tastes = 50
        if len(taste_ids) > max_tastes:
            # 샘플링
            step = len(taste_ids) // max_tastes
            sampled_tastes = taste_ids[::step][:max_tastes]
            sampled_matrix = np.zeros((len(sampled_tastes), len(categories)))
            sampled_taste_to_idx = {tid: idx for idx, tid in enumerate(sampled_tastes)}
            
            for result in results:
                if not result.get('success') or result['taste_id'] not in sampled_taste_to_idx:
                    continue
                taste_idx = sampled_taste_to_idx[result['taste_id']]
                for cat in result.get('categories', []):
                    if cat in cat_to_idx:
                        cat_idx = cat_to_idx[cat]
                        sampled_matrix[taste_idx, cat_idx] = 1
            
            taste_ids = sampled_tastes
            matrix = sampled_matrix

        fig, ax = plt.subplots(figsize=(max(12, len(categories) * 0.8), max(8, len(taste_ids) * 0.15)))
        im = ax.imshow(matrix, cmap='YlOrRd', aspect='auto', interpolation='nearest')
        
        ax.set_xticks(range(len(categories)))
        ax.set_xticklabels(categories, rotation=45, ha='right', fontsize=8)
        ax.set_yticks(range(len(taste_ids)))
        ax.set_yticklabels([f'Taste {tid}' for tid in taste_ids], fontsize=7)
        ax.set_xlabel('카테고리', fontsize=10)
        ax.set_ylabel('Taste ID', fontsize=10)
        ax.set_title('Taste × Category 추천 히트맵\n(노란색: 추천됨, 흰색: 추천 안 됨)', fontsize=12)
        
        plt.colorbar(im, ax=ax, label='추천 여부')
        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, 'taste_category_heatmap.png'),
                   dpi=300, bbox_inches='tight')
        plt.close()
        self.stdout.write('  - 히트맵 저장: taste_category_heatmap.png')

    def _create_summary_charts(self, summary: dict, output_dir: str):
        """통계 요약 차트 생성"""
        fig, axes = plt.subplots(1, 3, figsize=(18, 5))

        # 1. 성공률
        success_rate = (summary['successful_tastes'] / summary['total_tastes'] * 100) if summary['total_tastes'] > 0 else 0
        if summary['successful_tastes'] > 0 or summary['failed_tastes'] > 0:
            axes[0].pie(
                [summary['successful_tastes'], summary['failed_tastes']],
                labels=['성공', '실패'],
                autopct='%1.1f%%',
                colors=['lightgreen', 'lightcoral'],
                startangle=90
            )
            axes[0].set_title(f'시뮬레이션 성공률\n({summary["successful_tastes"]}/{summary["total_tastes"]})')
        else:
            axes[0].text(0.5, 0.5, '데이터 없음', ha='center', va='center', fontsize=14)
            axes[0].set_title('시뮬레이션 성공률')

        # 2. 평균 통계
        stats_data = {
            '평균 카테고리 수': summary['average_categories_per_taste'],
            '평균 제품 수': summary['average_products_per_taste']
        }
        axes[1].bar(stats_data.keys(), stats_data.values(), color=['skyblue', 'gold'])
        axes[1].set_ylabel('개수')
        axes[1].set_title('Taste당 평균 통계')
        axes[1].grid(True, alpha=0.3, axis='y')
        for i, (key, value) in enumerate(stats_data.items()):
            axes[1].text(i, value + 0.1, f'{value:.1f}', ha='center', fontweight='bold')

        # 3. 상위 카테고리 비율 (Pie Chart)
        category_dist = summary['category_distribution']
        sorted_cats = sorted(
            category_dist.items(),
            key=lambda x: x[1]['taste_count'],
            reverse=True
        )[:8]  # 상위 8개

        if sorted_cats and any(stats['taste_count'] > 0 for _, stats in sorted_cats):
            cat_names = [cat for cat, _ in sorted_cats]
            cat_counts = [stats['taste_count'] for _, stats in sorted_cats]
            
            axes[2].pie(
                cat_counts,
                labels=cat_names,
                autopct='%1.1f%%',
                startangle=90,
                textprops={'fontsize': 8}
            )
            axes[2].set_title('상위 카테고리 추천 비율\n(상위 8개)')
        else:
            axes[2].text(0.5, 0.5, '데이터 없음', ha='center', va='center', fontsize=14)
            axes[2].set_title('상위 카테고리 추천 비율')

        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, 'summary_statistics.png'),
                   dpi=300, bbox_inches='tight')
        plt.close()
        self.stdout.write('  - 통계 요약 그래프 저장: summary_statistics.png')

