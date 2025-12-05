"""
시뮬레이션 결과 시각화

JSON 결과 파일을 읽어서 다양한 차트로 시각화합니다.

사용법:
    python manage.py visualize_simulation_results --input simulation_results_full.json
"""
import json
import os
import csv
from collections import defaultdict, Counter
from django.core.management.base import BaseCommand
import numpy as np

try:
    import matplotlib.pyplot as plt
    import matplotlib
    matplotlib.use('Agg')  # GUI 없이 사용
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False


class Command(BaseCommand):
    help = '시뮬레이션 결과를 시각화합니다'

    def add_arguments(self, parser):
        parser.add_argument(
            '--input',
            type=str,
            default='simulation_results_full.json',
            help='입력 JSON 파일 경로',
        )
        parser.add_argument(
            '--output-dir',
            type=str,
            default='data/온보딩/visualization',
            help='시각화 결과 저장 디렉토리',
        )

    def handle(self, *args, **options):
        input_path = options['input']
        output_dir = options['output_dir']
        
        if not HAS_MATPLOTLIB:
            self.stdout.write(self.style.ERROR(
                'matplotlib이 설치되지 않았습니다. 설치 필요:\n'
                '  pip install matplotlib'
            ))
            return
        
        if not os.path.exists(input_path):
            self.stdout.write(self.style.ERROR(f'파일을 찾을 수 없습니다: {input_path}'))
            return
        
        self.stdout.write(self.style.SUCCESS('\n=== 시뮬레이션 결과 시각화 ===\n'))
        
        # JSON 파일 읽기
        self.stdout.write(f'[1] JSON 파일 읽기: {input_path}')
        with open(input_path, 'r', encoding='utf-8') as f:
            results = json.load(f)
        self.stdout.write(f'  - 총 {len(results)}개 케이스 로드\n')
        
        # 데이터 분석
        self.stdout.write('[2] 데이터 분석 중...')
        analysis = self._analyze_results(results)
        
        # 시각화 생성
        self.stdout.write(f'[3] 시각화 생성 중...')
        os.makedirs(output_dir, exist_ok=True)
        self._create_visualizations(analysis, output_dir)
        
        # CSV 표 생성
        self.stdout.write(f'[4] CSV 표 생성 중...')
        self._create_csv_tables(results, analysis, output_dir)
        
        self.stdout.write(self.style.SUCCESS(f'\n[완료] 시각화 완료!'))
        self.stdout.write(f'[FILE] 결과 저장 위치: {output_dir}')

    def _analyze_results(self, results):
        """결과 데이터 분석"""
        category_scores = defaultdict(list)
        category_counts = Counter()
        logic_usage = defaultdict(lambda: {'count': 0, 'categories': Counter()})
        taste_to_categories = defaultdict(lambda: defaultdict(list))
        score_distribution = defaultdict(int)
        
        for result in results:
            if not result.get('success'):
                continue
            
            taste_id = result.get('taste_id')
            logic_id = result.get('logic_id', 'default')
            
            # Logic 사용 통계
            logic_usage[logic_id]['count'] += 1
            
            # 추천 제품 분석
            for rec in result.get('recommendations', []):
                category = rec.get('category', 'UNKNOWN')
                score = rec.get('score', 0)
                
                category_scores[category].append(score)
                category_counts[category] += 1
                logic_usage[logic_id]['categories'][category] += 1
                taste_to_categories[taste_id][category].append(score)
                
                # 점수 분포
                if score >= 0.8:
                    score_distribution['high'] += 1
                elif score >= 0.6:
                    score_distribution['mid_high'] += 1
                elif score >= 0.5:
                    score_distribution['mid'] += 1
                else:
                    score_distribution['low'] += 1
        
        return {
            'category_scores': dict(category_scores),
            'category_counts': dict(category_counts),
            'logic_usage': dict(logic_usage),
            'taste_to_categories': dict(taste_to_categories),
            'score_distribution': dict(score_distribution),
            'total_cases': len(results),
        }

    def _create_visualizations(self, analysis, output_dir):
        """시각화 생성"""
        # 한글 폰트 설정
        plt.rcParams['font.family'] = 'Malgun Gothic'  # Windows
        plt.rcParams['axes.unicode_minus'] = False
        
        # 1. 카테고리별 추천 분포 (파이 차트)
        self._plot_category_distribution(analysis, output_dir)
        
        # 2. 카테고리별 점수 분포 (박스플롯)
        self._plot_category_scores(analysis, output_dir)
        
        # 3. 점수 분포 히스토그램
        self._plot_score_distribution(analysis, output_dir)
        
        # 4. Scoring Logic별 사용 현황 (상위 20개)
        self._plot_logic_usage(analysis, output_dir)
        
        # 5. 카테고리별 점수 범위 (바 차트)
        self._plot_category_score_ranges(analysis, output_dir)
        
        # 6. Logic별 카테고리 추천 비율 (히트맵)
        self._plot_logic_category_heatmap(analysis, output_dir)

    def _plot_category_distribution(self, analysis, output_dir):
        """카테고리별 추천 분포 파이 차트"""
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 8))
        
        category_counts = analysis['category_counts']
        labels = list(category_counts.keys())
        sizes = list(category_counts.values())
        colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#FFA07A', '#98D8C8']
        
        # 파이 차트
        ax1.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=90, colors=colors[:len(labels)])
        ax1.set_title('카테고리별 추천 분포', fontsize=16, fontweight='bold', pad=20)
        
        # 바 차트
        bars = ax2.bar(labels, sizes, color=colors[:len(labels)])
        ax2.set_title('카테고리별 추천 횟수', fontsize=16, fontweight='bold')
        ax2.set_ylabel('추천 횟수', fontsize=12)
        ax2.set_xlabel('카테고리', fontsize=12)
        ax2.grid(True, alpha=0.3, axis='y')
        
        # 값 표시
        for bar in bars:
            height = bar.get_height()
            ax2.text(bar.get_x() + bar.get_width()/2., height,
                    f'{int(height)}',
                    ha='center', va='bottom', fontweight='bold')
        
        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, '01_category_distribution.png'), dpi=300, bbox_inches='tight')
        plt.close()
        self.stdout.write('  - 카테고리별 분포 차트 저장: 01_category_distribution.png')

    def _plot_category_scores(self, analysis, output_dir):
        """카테고리별 점수 분포 박스플롯"""
        fig, ax = plt.subplots(figsize=(12, 8))
        
        category_scores = analysis['category_scores']
        data = [scores for scores in category_scores.values()]
        labels = list(category_scores.keys())
        
        bp = ax.boxplot(data, labels=labels, patch_artist=True, 
                       showmeans=True, meanline=True)
        
        # 색상 설정
        colors = ['#FF6B6B', '#4ECDC4', '#45B7D1']
        for patch, color in zip(bp['boxes'], colors[:len(bp['boxes'])]):
            patch.set_facecolor(color)
            patch.set_alpha(0.7)
        
        ax.set_title('카테고리별 점수 분포', fontsize=16, fontweight='bold', pad=20)
        ax.set_ylabel('점수', fontsize=12)
        ax.set_xlabel('카테고리', fontsize=12)
        ax.set_ylim(0, 1)
        ax.grid(True, alpha=0.3, axis='y')
        
        # 통계 정보 추가
        stats_text = []
        for label, scores in category_scores.items():
            mean_score = np.mean(scores)
            stats_text.append(f'{label}: 평균 {mean_score:.3f}')
        
        ax.text(0.02, 0.98, '\n'.join(stats_text), transform=ax.transAxes,
                fontsize=10, verticalalignment='top',
                bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
        
        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, '02_category_scores.png'), dpi=300, bbox_inches='tight')
        plt.close()
        self.stdout.write('  - 카테고리별 점수 분포 차트 저장: 02_category_scores.png')

    def _plot_score_distribution(self, analysis, output_dir):
        """점수 분포 히스토그램"""
        fig, axes = plt.subplots(2, 2, figsize=(16, 12))
        
        category_scores = analysis['category_scores']
        score_distribution = analysis['score_distribution']
        
        # 전체 점수 분포
        all_scores = []
        for scores in category_scores.values():
            all_scores.extend(scores)
        
        axes[0, 0].hist(all_scores, bins=30, color='#4ECDC4', alpha=0.7, edgecolor='black')
        axes[0, 0].axvline(np.mean(all_scores), color='red', linestyle='--', 
                          label=f'평균: {np.mean(all_scores):.3f}')
        axes[0, 0].set_title('전체 점수 분포', fontsize=14, fontweight='bold')
        axes[0, 0].set_xlabel('점수', fontsize=11)
        axes[0, 0].set_ylabel('빈도', fontsize=11)
        axes[0, 0].legend()
        axes[0, 0].grid(True, alpha=0.3)
        
        # 카테고리별 점수 분포
        colors = ['#FF6B6B', '#4ECDC4', '#45B7D1']
        for idx, (category, scores) in enumerate(category_scores.items()):
            axes[0, 1].hist(scores, bins=20, alpha=0.6, label=category, 
                           color=colors[idx % len(colors)])
        axes[0, 1].set_title('카테고리별 점수 분포', fontsize=14, fontweight='bold')
        axes[0, 1].set_xlabel('점수', fontsize=11)
        axes[0, 1].set_ylabel('빈도', fontsize=11)
        axes[0, 1].legend()
        axes[0, 1].grid(True, alpha=0.3)
        
        # 점수 구간별 분포
        dist_labels = ['높음\n(≥0.8)', '중상\n(0.6~0.8)', '중간\n(0.5~0.6)', '낮음\n(<0.5)']
        dist_values = [
            score_distribution.get('high', 0),
            score_distribution.get('mid_high', 0),
            score_distribution.get('mid', 0),
            score_distribution.get('low', 0)
        ]
        bars = axes[1, 0].bar(dist_labels, dist_values, color=['#2ECC71', '#3498DB', '#F39C12', '#E74C3C'])
        axes[1, 0].set_title('점수 구간별 분포', fontsize=14, fontweight='bold')
        axes[1, 0].set_ylabel('추천 횟수', fontsize=11)
        axes[1, 0].grid(True, alpha=0.3, axis='y')
        for bar in bars:
            height = bar.get_height()
            axes[1, 0].text(bar.get_x() + bar.get_width()/2., height,
                           f'{int(height)}',
                           ha='center', va='bottom', fontweight='bold')
        
        # 카테고리별 평균 점수
        category_means = {cat: np.mean(scores) for cat, scores in category_scores.items()}
        bars = axes[1, 1].bar(category_means.keys(), category_means.values(),
                              color=['#FF6B6B', '#4ECDC4', '#45B7D1'])
        axes[1, 1].set_title('카테고리별 평균 점수', fontsize=14, fontweight='bold')
        axes[1, 1].set_ylabel('평균 점수', fontsize=11)
        axes[1, 1].set_ylim(0, 1)
        axes[1, 1].grid(True, alpha=0.3, axis='y')
        for bar in bars:
            height = bar.get_height()
            axes[1, 1].text(bar.get_x() + bar.get_width()/2., height,
                           f'{height:.3f}',
                           ha='center', va='bottom', fontweight='bold')
        
        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, '03_score_distribution.png'), dpi=300, bbox_inches='tight')
        plt.close()
        self.stdout.write('  - 점수 분포 차트 저장: 03_score_distribution.png')

    def _plot_logic_usage(self, analysis, output_dir):
        """Scoring Logic별 사용 현황"""
        logic_usage = analysis['logic_usage']
        
        # 사용 횟수로 정렬
        sorted_logics = sorted(logic_usage.items(), key=lambda x: x[1]['count'], reverse=True)[:20]
        
        fig, ax = plt.subplots(figsize=(14, 10))
        
        logic_ids = [f"Logic {k}" for k, v in sorted_logics]
        counts = [v['count'] for k, v in sorted_logics]
        
        bars = ax.barh(logic_ids, counts, color='#4ECDC4')
        ax.set_title('Scoring Logic별 사용 횟수 (상위 20개)', fontsize=16, fontweight='bold', pad=20)
        ax.set_xlabel('사용 횟수', fontsize=12)
        ax.set_ylabel('Logic ID', fontsize=12)
        ax.grid(True, alpha=0.3, axis='x')
        
        # 값 표시
        for bar in bars:
            width = bar.get_width()
            ax.text(width, bar.get_y() + bar.get_height()/2.,
                   f' {int(width)}',
                   ha='left', va='center', fontweight='bold')
        
        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, '04_logic_usage.png'), dpi=300, bbox_inches='tight')
        plt.close()
        self.stdout.write('  - Logic 사용 현황 차트 저장: 04_logic_usage.png')

    def _plot_category_score_ranges(self, analysis, output_dir):
        """카테고리별 점수 범위 바 차트"""
        fig, ax = plt.subplots(figsize=(12, 8))
        
        category_scores = analysis['category_scores']
        
        categories = list(category_scores.keys())
        means = [np.mean(scores) for scores in category_scores.values()]
        mins = [np.min(scores) for scores in category_scores.values()]
        maxs = [np.max(scores) for scores in category_scores.values()]
        stds = [np.std(scores) for scores in category_scores.values()]
        
        x = np.arange(len(categories))
        width = 0.6
        
        bars = ax.bar(x, means, width, yerr=stds, capsize=5,
                     color=['#FF6B6B', '#4ECDC4', '#45B7D1'], alpha=0.7)
        
        # 최소/최대 점수 표시
        for i, (mean, min_val, max_val) in enumerate(zip(means, mins, maxs)):
            ax.plot([i, i], [min_val, max_val], 'k-', linewidth=2, alpha=0.5)
            ax.plot([i-0.1, i+0.1], [min_val, min_val], 'k-', linewidth=2)
            ax.plot([i-0.1, i+0.1], [max_val, max_val], 'k-', linewidth=2)
        
        ax.set_title('카테고리별 점수 범위 및 평균', fontsize=16, fontweight='bold', pad=20)
        ax.set_ylabel('점수', fontsize=12)
        ax.set_xlabel('카테고리', fontsize=12)
        ax.set_xticks(x)
        ax.set_xticklabels(categories)
        ax.set_ylim(0, 1)
        ax.grid(True, alpha=0.3, axis='y')
        
        # 값 표시
        for i, (bar, mean, min_val, max_val) in enumerate(zip(bars, means, mins, maxs)):
            ax.text(bar.get_x() + bar.get_width()/2., mean + stds[i] + 0.02,
                   f'{mean:.3f}',
                   ha='center', va='bottom', fontweight='bold')
            ax.text(bar.get_x() + bar.get_width()/2., min_val - 0.03,
                   f'min: {min_val:.3f}',
                   ha='center', va='top', fontsize=9)
            ax.text(bar.get_x() + bar.get_width()/2., max_val + 0.02,
                   f'max: {max_val:.3f}',
                   ha='center', va='bottom', fontsize=9)
        
        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, '05_category_score_ranges.png'), dpi=300, bbox_inches='tight')
        plt.close()
        self.stdout.write('  - 카테고리별 점수 범위 차트 저장: 05_category_score_ranges.png')

    def _plot_logic_category_heatmap(self, analysis, output_dir):
        """Logic별 카테고리 추천 비율 히트맵"""
        logic_usage = analysis['logic_usage']
        
        # 상위 15개 Logic 선택
        sorted_logics = sorted(logic_usage.items(), key=lambda x: x[1]['count'], reverse=True)[:15]
        
        # 데이터 준비
        logic_ids = [f"L{k}" for k, v in sorted_logics]
        categories = ['KITCHEN', 'TV', 'LIVING']
        
        # 비율 계산
        heatmap_data = []
        for logic_id, data in sorted_logics:
            total = data['count']
            row = []
            for cat in categories:
                count = data['categories'].get(cat, 0)
                ratio = count / total if total > 0 else 0
                row.append(ratio)
            heatmap_data.append(row)
        
        heatmap_data = np.array(heatmap_data)
        
        fig, ax = plt.subplots(figsize=(10, 12))
        
        im = ax.imshow(heatmap_data, cmap='YlOrRd', aspect='auto', vmin=0, vmax=1)
        
        ax.set_xticks(np.arange(len(categories)))
        ax.set_yticks(np.arange(len(logic_ids)))
        ax.set_xticklabels(categories)
        ax.set_yticklabels(logic_ids)
        
        ax.set_title('Logic별 카테고리 추천 비율 (상위 15개)', fontsize=16, fontweight='bold', pad=20)
        
        # 값 표시
        for i in range(len(logic_ids)):
            for j in range(len(categories)):
                text = ax.text(j, i, f'{heatmap_data[i, j]:.2f}',
                             ha="center", va="center", color="black", fontweight='bold')
        
        plt.colorbar(im, ax=ax, label='추천 비율')
        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, '06_logic_category_heatmap.png'), dpi=300, bbox_inches='tight')
        plt.close()
        self.stdout.write('  - Logic별 카테고리 히트맵 저장: 06_logic_category_heatmap.png')

    def _create_csv_tables(self, results, analysis, output_dir):
        """CSV 표 생성"""
        # 1. 카테고리별 통계 표
        category_stats_path = os.path.join(output_dir, '01_category_statistics.csv')
        with open(category_stats_path, 'w', encoding='utf-8-sig', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['카테고리', '추천 횟수', '평균 점수', '최소 점수', '최대 점수', '표준편차'])
            
            category_scores = analysis['category_scores']
            for category, scores in sorted(category_scores.items()):
                writer.writerow([
                    category,
                    len(scores),
                    f'{np.mean(scores):.3f}',
                    f'{np.min(scores):.3f}',
                    f'{np.max(scores):.3f}',
                    f'{np.std(scores):.3f}'
                ])
        self.stdout.write('  - 카테고리별 통계 표 저장: 01_category_statistics.csv')
        
        # 2. Logic별 사용 통계 표
        logic_stats_path = os.path.join(output_dir, '02_logic_statistics.csv')
        with open(logic_stats_path, 'w', encoding='utf-8-sig', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['Logic ID', '사용 횟수', 'KITCHEN 추천', 'TV 추천', 'LIVING 추천'])
            
            logic_usage = analysis['logic_usage']
            for logic_id in sorted(logic_usage.keys(), key=lambda x: int(x) if str(x).isdigit() else 999):
                data = logic_usage[logic_id]
                categories = data['categories']
                writer.writerow([
                    logic_id,
                    data['count'],
                    categories.get('KITCHEN', 0),
                    categories.get('TV', 0),
                    categories.get('LIVING', 0)
                ])
        self.stdout.write('  - Logic별 통계 표 저장: 02_logic_statistics.csv')
        
        # 3. Taste ID별 추천 요약 표
        taste_summary_path = os.path.join(output_dir, '03_taste_summary.csv')
        with open(taste_summary_path, 'w', encoding='utf-8-sig', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                'Taste ID', '인테리어 스타일', '메이트 구성', '우선순위', '예산',
                'Logic ID', '추천 개수', 'KITCHEN 추천', 'TV 추천', 'LIVING 추천',
                '평균 점수', '최고 점수'
            ])
            
            for result in results:
                if not result.get('success'):
                    continue
                
                recommendations = result.get('recommendations', [])
                category_counts = Counter(rec.get('category', 'UNKNOWN') for rec in recommendations)
                scores = [rec.get('score', 0) for rec in recommendations]
                
                writer.writerow([
                    result.get('taste_id', ''),
                    result.get('interior_style', ''),
                    result.get('mate', ''),
                    result.get('priority', ''),
                    result.get('budget', ''),
                    result.get('logic_id', ''),
                    len(recommendations),
                    category_counts.get('KITCHEN', 0),
                    category_counts.get('TV', 0),
                    category_counts.get('LIVING', 0),
                    f'{np.mean(scores):.3f}' if scores else '0.000',
                    f'{np.max(scores):.3f}' if scores else '0.000'
                ])
        self.stdout.write('  - Taste ID별 요약 표 저장: 03_taste_summary.csv')
        
        # 4. 상위 추천 제품 표 (점수 높은 순)
        top_products_path = os.path.join(output_dir, '04_top_recommendations.csv')
        all_recommendations = []
        for result in results:
            if not result.get('success'):
                continue
            for rec in result.get('recommendations', []):
                all_recommendations.append({
                    'taste_id': result.get('taste_id', ''),
                    'product_id': rec.get('product_id', ''),
                    'model': rec.get('model', ''),
                    'category': rec.get('category', ''),
                    'score': rec.get('score', 0),
                    'price': rec.get('price', 0)
                })
        
        # 점수 높은 순으로 정렬
        all_recommendations.sort(key=lambda x: x['score'], reverse=True)
        
        with open(top_products_path, 'w', encoding='utf-8-sig', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['순위', 'Taste ID', '제품 ID', '모델명', '카테고리', '점수', '가격'])
            
            for idx, rec in enumerate(all_recommendations[:1000], 1):  # 상위 1000개
                writer.writerow([
                    idx,
                    rec['taste_id'],
                    rec['product_id'],
                    rec['model'],
                    rec['category'],
                    f'{rec["score"]:.3f}',
                    int(rec['price']) if rec['price'] else 0
                ])
        self.stdout.write('  - 상위 추천 제품 표 저장: 04_top_recommendations.csv (상위 1000개)')
        
        # 5. 점수 분포 통계 표
        score_dist_path = os.path.join(output_dir, '05_score_distribution.csv')
        with open(score_dist_path, 'w', encoding='utf-8-sig', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['점수 구간', '추천 횟수', '비율 (%)'])
            
            score_distribution = analysis['score_distribution']
            total = sum(score_distribution.values())
            
            dist_map = {
                'high': '높음 (≥0.8)',
                'mid_high': '중상 (0.6~0.8)',
                'mid': '중간 (0.5~0.6)',
                'low': '낮음 (<0.5)'
            }
            
            for key, label in dist_map.items():
                count = score_distribution.get(key, 0)
                ratio = (count / total * 100) if total > 0 else 0
                writer.writerow([label, count, f'{ratio:.2f}'])
        self.stdout.write('  - 점수 분포 통계 표 저장: 05_score_distribution.csv')

