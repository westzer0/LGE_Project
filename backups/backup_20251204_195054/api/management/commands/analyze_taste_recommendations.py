"""
취향 추천 문구 분석 및 시각화

- 리뷰_기반_추천문구와 AI_기반_추천문구의 분포도 분석
- 두 문구 간 유사도 분석
- 시각화 생성

사용법:
    python manage.py analyze_taste_recommendations
"""
import csv
import os
import re
from collections import Counter
from pathlib import Path
import numpy as np
from django.core.management.base import BaseCommand

try:
    import matplotlib.pyplot as plt
    import matplotlib
    matplotlib.use('Agg')  # GUI 없이 사용
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
    HAS_VISUALIZATION = True
except ImportError:
    HAS_VISUALIZATION = False


class Command(BaseCommand):
    help = '취향 추천 문구의 분포도와 유사도를 분석하고 시각화합니다'

    def add_arguments(self, parser):
        parser.add_argument(
            '--csv-path',
            type=str,
            default='data/온보딩/taste_recommendations_768.csv',
            help='분석할 CSV 파일 경로',
        )
        parser.add_argument(
            '--output-dir',
            type=str,
            default='data/온보딩/analysis',
            help='시각화 결과 저장 디렉토리',
        )

    def handle(self, *args, **options):
        csv_path = options['csv_path']
        output_dir = options['output_dir']
        
        self.stdout.write(self.style.SUCCESS('\n=== 취향 추천 문구 분석 ===\n'))
        
        if not HAS_VISUALIZATION:
            self.stdout.write(self.style.ERROR(
                '시각화 라이브러리가 없습니다. 설치 필요:\n'
                '  pip install matplotlib scikit-learn'
            ))
            return
        
        # CSV 파일 읽기
        if not os.path.exists(csv_path):
            self.stdout.write(self.style.ERROR(f'CSV 파일을 찾을 수 없습니다: {csv_path}'))
            return
        
        self.stdout.write(f'[1] CSV 파일 읽기: {csv_path}')
        data = self._load_csv(csv_path)
        self.stdout.write(f'  - 총 {len(data)}개 데이터 로드\n')
        
        # 분석
        self.stdout.write('[2] 문구 분석 중...')
        review_texts = [row['리뷰_기반_추천문구'] for row in data]
        ai_texts = [row['AI_기반_추천문구'] for row in data]
        
        # 기본 통계
        stats = self._calculate_statistics(review_texts, ai_texts)
        self._print_statistics(stats)
        
        # 유사도 분석
        self.stdout.write('\n[3] 유사도 분석 중...')
        similarity_results = self._analyze_similarity(review_texts, ai_texts)
        self._print_similarity_results(similarity_results)
        
        # 시각화
        self.stdout.write(f'\n[4] 시각화 생성 중...')
        os.makedirs(output_dir, exist_ok=True)
        self._create_visualizations(data, review_texts, ai_texts, similarity_results, output_dir)
        
        self.stdout.write(self.style.SUCCESS(f'\n[OK] 분석 완료!'))
        self.stdout.write(f'[FILE] 결과 저장 위치: {output_dir}')

    def _load_csv(self, csv_path):
        """CSV 파일 로드"""
        data = []
        with open(csv_path, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            for row in reader:
                data.append(row)
        return data

    def _calculate_statistics(self, review_texts, ai_texts):
        """기본 통계 계산"""
        def get_text_stats(texts):
            lengths = [len(text) for text in texts]
            word_counts = [len(text.split()) for text in texts]
            unique_texts = len(set(texts))
            return {
                'lengths': lengths,
                'word_counts': word_counts,
                'unique_count': unique_texts,
                'total_count': len(texts),
                'avg_length': np.mean(lengths),
                'avg_words': np.mean(word_counts),
                'min_length': np.min(lengths),
                'max_length': np.max(lengths),
            }
        
        return {
            'review': get_text_stats(review_texts),
            'ai': get_text_stats(ai_texts),
        }

    def _print_statistics(self, stats):
        """통계 출력"""
        self.stdout.write('\n[기본 통계]')
        self.stdout.write(f'\n리뷰_기반_추천문구:')
        self.stdout.write(f'  - 총 개수: {stats["review"]["total_count"]}개')
        self.stdout.write(f'  - 고유 문구: {stats["review"]["unique_count"]}개')
        self.stdout.write(f'  - 고유도: {stats["review"]["unique_count"]/stats["review"]["total_count"]*100:.1f}%')
        self.stdout.write(f'  - 평균 길이: {stats["review"]["avg_length"]:.0f}자')
        self.stdout.write(f'  - 평균 단어 수: {stats["review"]["avg_words"]:.1f}개')
        self.stdout.write(f'  - 최소/최대 길이: {stats["review"]["min_length"]}/{stats["review"]["max_length"]}자')
        
        self.stdout.write(f'\nAI_기반_추천문구:')
        self.stdout.write(f'  - 총 개수: {stats["ai"]["total_count"]}개')
        self.stdout.write(f'  - 고유 문구: {stats["ai"]["unique_count"]}개')
        self.stdout.write(f'  - 고유도: {stats["ai"]["unique_count"]/stats["ai"]["total_count"]*100:.1f}%')
        self.stdout.write(f'  - 평균 길이: {stats["ai"]["avg_length"]:.0f}자')
        self.stdout.write(f'  - 평균 단어 수: {stats["ai"]["avg_words"]:.1f}개')
        self.stdout.write(f'  - 최소/최대 길이: {stats["ai"]["min_length"]}/{stats["ai"]["max_length"]}자')

    def _analyze_similarity(self, review_texts, ai_texts):
        """유사도 분석"""
        # TF-IDF 벡터화
        vectorizer = TfidfVectorizer(max_features=1000, ngram_range=(1, 2))
        
        # 각각 벡터화
        review_vectors = vectorizer.fit_transform(review_texts)
        ai_vectors = vectorizer.transform(ai_texts)
        
        # 쌍별 유사도 계산
        similarities = []
        for i in range(len(review_texts)):
            sim = cosine_similarity(
                review_vectors[i:i+1],
                ai_vectors[i:i+1]
            )[0][0]
            similarities.append(sim)
        
        # 전체 유사도
        all_texts = review_texts + ai_texts
        all_vectors = vectorizer.fit_transform(all_texts)
        all_similarity_matrix = cosine_similarity(all_vectors)
        
        return {
            'pairwise_similarities': similarities,
            'review_internal_similarity': np.mean(cosine_similarity(review_vectors)),
            'ai_internal_similarity': np.mean(cosine_similarity(ai_vectors)),
            'cross_similarity': np.mean(similarities),
        }

    def _print_similarity_results(self, results):
        """유사도 결과 출력"""
        self.stdout.write(f'\n[유사도 분석]')
        self.stdout.write(f'  - 리뷰_기반 내부 유사도: {results["review_internal_similarity"]:.3f}')
        self.stdout.write(f'  - AI_기반 내부 유사도: {results["ai_internal_similarity"]:.3f}')
        self.stdout.write(f'  - 리뷰-AI 간 평균 유사도: {results["cross_similarity"]:.3f}')
        self.stdout.write(f'  - 최소 유사도: {np.min(results["pairwise_similarities"]):.3f}')
        self.stdout.write(f'  - 최대 유사도: {np.max(results["pairwise_similarities"]):.3f}')
        self.stdout.write(f'  - 유사도 표준편차: {np.std(results["pairwise_similarities"]):.3f}')

    def _create_visualizations(self, data, review_texts, ai_texts, similarity_results, output_dir):
        """시각화 생성"""
        # 한글 폰트 설정
        plt.rcParams['font.family'] = 'Malgun Gothic'  # Windows
        plt.rcParams['axes.unicode_minus'] = False
        
        # 1. 길이 분포 비교
        fig, axes = plt.subplots(2, 2, figsize=(15, 12))
        
        # 1-1. 길이 히스토그램
        review_lengths = [len(text) for text in review_texts]
        ai_lengths = [len(text) for text in ai_texts]
        
        axes[0, 0].hist(review_lengths, bins=30, alpha=0.7, label='리뷰_기반', color='skyblue')
        axes[0, 0].hist(ai_lengths, bins=30, alpha=0.7, label='AI_기반', color='lightcoral')
        axes[0, 0].set_xlabel('문구 길이 (자)')
        axes[0, 0].set_ylabel('빈도')
        axes[0, 0].set_title('문구 길이 분포 비교')
        axes[0, 0].legend()
        axes[0, 0].grid(True, alpha=0.3)
        
        # 1-2. 단어 수 분포
        review_words = [len(text.split()) for text in review_texts]
        ai_words = [len(text.split()) for text in ai_texts]
        
        axes[0, 1].hist(review_words, bins=30, alpha=0.7, label='리뷰_기반', color='skyblue')
        axes[0, 1].hist(ai_words, bins=30, alpha=0.7, label='AI_기반', color='lightcoral')
        axes[0, 1].set_xlabel('단어 수')
        axes[0, 1].set_ylabel('빈도')
        axes[0, 1].set_title('단어 수 분포 비교')
        axes[0, 1].legend()
        axes[0, 1].grid(True, alpha=0.3)
        
        # 1-3. 유사도 분포
        similarities = similarity_results['pairwise_similarities']
        axes[1, 0].hist(similarities, bins=30, alpha=0.7, color='green')
        axes[1, 0].axvline(np.mean(similarities), color='red', linestyle='--', 
                          label=f'평균: {np.mean(similarities):.3f}')
        axes[1, 0].set_xlabel('유사도 (Cosine Similarity)')
        axes[1, 0].set_ylabel('빈도')
        axes[1, 0].set_title('리뷰-AI 문구 간 유사도 분포')
        axes[1, 0].legend()
        axes[1, 0].grid(True, alpha=0.3)
        
        # 1-4. 길이 vs 유사도 산점도
        axes[1, 1].scatter(review_lengths, similarities, alpha=0.5, s=20, color='blue', label='리뷰 길이')
        axes[1, 1].scatter(ai_lengths, similarities, alpha=0.5, s=20, color='red', label='AI 길이')
        axes[1, 1].set_xlabel('문구 길이 (자)')
        axes[1, 1].set_ylabel('유사도')
        axes[1, 1].set_title('문구 길이와 유사도 관계')
        axes[1, 1].legend()
        axes[1, 1].grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, 'distribution_analysis.png'), dpi=300, bbox_inches='tight')
        plt.close()
        self.stdout.write('  - 분포도 분석 그래프 저장: distribution_analysis.png')
        
        # 2. 유사도 히트맵 (샘플)
        fig, axes = plt.subplots(1, 2, figsize=(16, 6))
        
        # 2-1. 리뷰 내부 유사도 (상위 50개 샘플)
        sample_size = min(50, len(review_texts))
        sample_indices = np.random.choice(len(review_texts), sample_size, replace=False)
        
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.metrics.pairwise import cosine_similarity
        
        review_sample = [review_texts[i] for i in sample_indices]
        review_vec = TfidfVectorizer(max_features=500).fit_transform(review_sample)
        review_sim_matrix = cosine_similarity(review_vec)
        
        im1 = axes[0].imshow(review_sim_matrix, cmap='YlOrRd', aspect='auto')
        axes[0].set_title(f'리뷰_기반 내부 유사도 (샘플 {sample_size}개)')
        axes[0].set_xlabel('문구 인덱스')
        axes[0].set_ylabel('문구 인덱스')
        plt.colorbar(im1, ax=axes[0])
        
        # 2-2. AI 내부 유사도 (상위 50개 샘플)
        ai_sample = [ai_texts[i] for i in sample_indices]
        ai_vec = TfidfVectorizer(max_features=500).fit_transform(ai_sample)
        ai_sim_matrix = cosine_similarity(ai_vec)
        
        im2 = axes[1].imshow(ai_sim_matrix, cmap='YlGnBu', aspect='auto')
        axes[1].set_title(f'AI_기반 내부 유사도 (샘플 {sample_size}개)')
        axes[1].set_xlabel('문구 인덱스')
        axes[1].set_ylabel('문구 인덱스')
        plt.colorbar(im2, ax=axes[1])
        
        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, 'similarity_heatmap.png'), dpi=300, bbox_inches='tight')
        plt.close()
        self.stdout.write('  - 유사도 히트맵 저장: similarity_heatmap.png')
        
        # 3. 통계 요약 그래프
        fig, axes = plt.subplots(1, 3, figsize=(18, 5))
        
        # 3-1. 고유도 비교
        review_unique = len(set(review_texts))
        ai_unique = len(set(ai_texts))
        total = len(review_texts)
        
        axes[0].bar(['리뷰_기반', 'AI_기반'], 
                    [review_unique/total*100, ai_unique/total*100],
                    color=['skyblue', 'lightcoral'])
        axes[0].set_ylabel('고유도 (%)')
        axes[0].set_title('문구 고유도 비교')
        axes[0].set_ylim(0, 100)
        for i, v in enumerate([review_unique/total*100, ai_unique/total*100]):
            axes[0].text(i, v + 2, f'{v:.1f}%', ha='center', fontweight='bold')
        axes[0].grid(True, alpha=0.3, axis='y')
        
        # 3-2. 평균 길이 비교
        axes[1].bar(['리뷰_기반', 'AI_기반'],
                    [np.mean(review_lengths), np.mean(ai_lengths)],
                    color=['skyblue', 'lightcoral'])
        axes[1].set_ylabel('평균 길이 (자)')
        axes[1].set_title('평균 문구 길이 비교')
        for i, v in enumerate([np.mean(review_lengths), np.mean(ai_lengths)]):
            axes[1].text(i, v + 5, f'{v:.0f}자', ha='center', fontweight='bold')
        axes[1].grid(True, alpha=0.3, axis='y')
        
        # 3-3. 유사도 비교
        axes[2].bar(['리뷰 내부', 'AI 내부', '리뷰-AI 간'],
                    [similarity_results['review_internal_similarity'],
                     similarity_results['ai_internal_similarity'],
                     similarity_results['cross_similarity']],
                    color=['skyblue', 'lightcoral', 'lightgreen'])
        axes[2].set_ylabel('평균 유사도')
        axes[2].set_title('유사도 비교')
        axes[2].set_ylim(0, 1)
        for i, v in enumerate([similarity_results['review_internal_similarity'],
                               similarity_results['ai_internal_similarity'],
                               similarity_results['cross_similarity']]):
            axes[2].text(i, v + 0.02, f'{v:.3f}', ha='center', fontweight='bold')
        axes[2].grid(True, alpha=0.3, axis='y')
        
        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, 'summary_statistics.png'), dpi=300, bbox_inches='tight')
        plt.close()
        self.stdout.write('  - 통계 요약 그래프 저장: summary_statistics.png')
        
        # 4. 텍스트 분석 리포트 생성
        self._create_text_report(data, review_texts, ai_texts, similarity_results, output_dir)

    def _create_text_report(self, data, review_texts, ai_texts, similarity_results, output_dir):
        """텍스트 분석 리포트 생성"""
        report_path = os.path.join(output_dir, 'analysis_report.txt')
        
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write("=" * 60 + "\n")
            f.write("취향 추천 문구 분석 리포트\n")
            f.write("=" * 60 + "\n\n")
            
            # 기본 통계
            f.write("[1] 기본 통계\n")
            f.write("-" * 60 + "\n")
            f.write(f"총 데이터 수: {len(data)}개\n\n")
            
            review_unique = len(set(review_texts))
            ai_unique = len(set(ai_texts))
            f.write("리뷰_기반_추천문구:\n")
            f.write(f"  - 고유 문구: {review_unique}개 ({review_unique/len(review_texts)*100:.1f}%)\n")
            f.write(f"  - 평균 길이: {np.mean([len(t) for t in review_texts]):.0f}자\n")
            f.write(f"  - 평균 단어 수: {np.mean([len(t.split()) for t in review_texts]):.1f}개\n\n")
            
            f.write("AI_기반_추천문구:\n")
            f.write(f"  - 고유 문구: {ai_unique}개 ({ai_unique/len(ai_texts)*100:.1f}%)\n")
            f.write(f"  - 평균 길이: {np.mean([len(t) for t in ai_texts]):.0f}자\n")
            f.write(f"  - 평균 단어 수: {np.mean([len(t.split()) for t in ai_texts]):.1f}개\n\n")
            
            # 유사도 분석
            f.write("[2] 유사도 분석\n")
            f.write("-" * 60 + "\n")
            f.write(f"리뷰_기반 내부 유사도: {similarity_results['review_internal_similarity']:.3f}\n")
            f.write(f"AI_기반 내부 유사도: {similarity_results['ai_internal_similarity']:.3f}\n")
            f.write(f"리뷰-AI 간 평균 유사도: {similarity_results['cross_similarity']:.3f}\n")
            f.write(f"유사도 범위: {np.min(similarity_results['pairwise_similarities']):.3f} ~ {np.max(similarity_results['pairwise_similarities']):.3f}\n")
            f.write(f"유사도 표준편차: {np.std(similarity_results['pairwise_similarities']):.3f}\n\n")
            
            # 해석
            f.write("[3] 해석\n")
            f.write("-" * 60 + "\n")
            if similarity_results['review_internal_similarity'] < 0.3:
                f.write("✓ 리뷰_기반 문구는 다양성이 높습니다 (내부 유사도 낮음)\n")
            else:
                f.write("⚠ 리뷰_기반 문구는 유사한 패턴이 많습니다 (내부 유사도 높음)\n")
            
            if similarity_results['ai_internal_similarity'] < 0.3:
                f.write("✓ AI_기반 문구는 다양성이 높습니다 (내부 유사도 낮음)\n")
            else:
                f.write("⚠ AI_기반 문구는 유사한 패턴이 많습니다 (내부 유사도 높음)\n")
            
            if similarity_results['cross_similarity'] < 0.3:
                f.write("✓ 리뷰_기반과 AI_기반 문구는 서로 다릅니다 (차별화됨)\n")
            else:
                f.write("⚠ 리뷰_기반과 AI_기반 문구가 유사합니다 (차별화 필요)\n")
        
        self.stdout.write('  - 분석 리포트 저장: analysis_report.txt')

