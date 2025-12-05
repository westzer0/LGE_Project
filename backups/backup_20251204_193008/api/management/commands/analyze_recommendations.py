"""
추천 결과 분석 및 통계 도구

사용법:
    python manage.py analyze_recommendations
    python manage.py analyze_recommendations --sample-size 100
"""
from django.core.management.base import BaseCommand
from api.services.recommendation_engine import RecommendationEngine
from api.models import Product, ProductSpec
from django.db.models import Q, Count, Avg, Min, Max
import json
import random


class Command(BaseCommand):
    help = '추천 엔진의 추천 결과를 분석합니다'

    def add_arguments(self, parser):
        parser.add_argument(
            '--sample-size',
            type=int,
            default=50,
            help='테스트할 샘플 수 (기본: 50)',
        )
        parser.add_argument(
            '--category',
            type=str,
            help='특정 카테고리만 분석',
        )

    def handle(self, *args, **options):
        sample_size = options['sample_size']
        category = options.get('category')
        
        self.stdout.write(self.style.SUCCESS('\n=== 추천 엔진 분석 ===\n'))
        
        engine = RecommendationEngine()
        
        # 1. 데이터베이스 통계
        self._print_database_stats(category)
        
        # 2. 샘플 추천 테스트
        self._analyze_sample_recommendations(engine, sample_size, category)
        
        # 3. 점수 분포 분석
        self._analyze_score_distribution(engine, category)

    def _print_database_stats(self, category):
        """데이터베이스 통계 출력"""
        self.stdout.write(self.style.SUCCESS('=== 데이터베이스 통계 ===\n'))
        
        products = Product.objects.filter(is_active=True)
        if category:
            products = products.filter(category=category)
        
        total_products = products.count()
        products_with_spec = products.filter(spec__isnull=False).count()
        
        self.stdout.write(f'전체 제품 수: {total_products}개')
        self.stdout.write(f'스펙 있는 제품: {products_with_spec}개')
        self.stdout.write(f'스펙 없는 제품: {total_products - products_with_spec}개\n')
        
        # 카테고리별 통계
        category_stats = products.values('category').annotate(
            count=Count('id'),
            avg_price=Avg('price'),
            min_price=Min('price'),
            max_price=Max('price'),
        )
        
        self.stdout.write('카테고리별 통계:')
        for stat in category_stats:
            self.stdout.write(
                f"  {stat['category']}: {stat['count']}개, "
                f"평균가격: {stat['avg_price']:,.0f}원 "
                f"({stat['min_price']:,.0f}원 ~ {stat['max_price']:,.0f}원)"
            )
        self.stdout.write('')

    def _analyze_sample_recommendations(self, engine, sample_size, category):
        """샘플 추천 결과 분석"""
        self.stdout.write(self.style.SUCCESS(f'=== 샘플 추천 분석 ({sample_size}개) ===\n'))
        
        # 다양한 프로필 생성
        test_profiles = self._generate_test_profiles(sample_size, category)
        
        results = {
            'total_tests': 0,
            'successful': 0,
            'failed': 0,
            'avg_recommendations': 0,
            'avg_score': 0,
            'score_distribution': {
                'high': 0,  # 0.8 이상
                'medium': 0,  # 0.5 ~ 0.8
                'low': 0,  # 0.5 미만
            },
            'category_distribution': {},
            'price_ranges': {
                'low': 0,  # 50만원 이하
                'medium': 0,  # 50만원 ~ 200만원
                'high': 0,  # 200만원 이상
            },
        }
        
        all_scores = []
        total_recommendations = 0
        
        for profile in test_profiles:
            results['total_tests'] += 1
            try:
                result = engine.get_recommendations(profile, limit=5)
                
                if result.get('success'):
                    results['successful'] += 1
                    recommendations = result.get('recommendations', [])
                    total_recommendations += len(recommendations)
                    
                    for rec in recommendations:
                        score = rec.get('score', 0)
                        all_scores.append(score)
                        
                        # 점수 분포
                        if score >= 0.8:
                            results['score_distribution']['high'] += 1
                        elif score >= 0.5:
                            results['score_distribution']['medium'] += 1
                        else:
                            results['score_distribution']['low'] += 1
                        
                        # 가격 분포
                        price = rec.get('price', 0)
                        if price <= 500000:
                            results['price_ranges']['low'] += 1
                        elif price <= 2000000:
                            results['price_ranges']['medium'] += 1
                        else:
                            results['price_ranges']['high'] += 1
                        
                        # 카테고리 분포
                        cat = rec.get('category', 'UNKNOWN')
                        results['category_distribution'][cat] = \
                            results['category_distribution'].get(cat, 0) + 1
                else:
                    results['failed'] += 1
                    
            except Exception as e:
                results['failed'] += 1
                if self.verbose:
                    self.stdout.write(self.style.ERROR(f'오류: {e}'))
        
        # 결과 계산
        if all_scores:
            results['avg_score'] = sum(all_scores) / len(all_scores)
        if results['successful'] > 0:
            results['avg_recommendations'] = total_recommendations / results['successful']
        
        # 결과 출력
        self.stdout.write(f"성공률: {results['successful']}/{results['total_tests']} "
                         f"({results['successful']/results['total_tests']*100:.1f}%)")
        self.stdout.write(f"평균 추천 개수: {results['avg_recommendations']:.1f}개")
        self.stdout.write(f"평균 점수: {results['avg_score']:.3f}\n")
        
        self.stdout.write("점수 분포:")
        self.stdout.write(f"  높음 (0.8 이상): {results['score_distribution']['high']}개")
        self.stdout.write(f"  중간 (0.5 ~ 0.8): {results['score_distribution']['medium']}개")
        self.stdout.write(f"  낮음 (0.5 미만): {results['score_distribution']['low']}개\n")
        
        self.stdout.write("가격 분포:")
        self.stdout.write(f"  저예산 (50만원 이하): {results['price_ranges']['low']}개")
        self.stdout.write(f"  중예산 (50만원 ~ 200만원): {results['price_ranges']['medium']}개")
        self.stdout.write(f"  고예산 (200만원 이상): {results['price_ranges']['high']}개\n")
        
        if results['category_distribution']:
            self.stdout.write("카테고리 분포:")
            for cat, count in sorted(results['category_distribution'].items(), 
                                   key=lambda x: x[1], reverse=True):
                self.stdout.write(f"  {cat}: {count}개")
        self.stdout.write('')

    def _analyze_score_distribution(self, engine, category):
        """점수 분포 상세 분석"""
        self.stdout.write(self.style.SUCCESS('=== 점수 분포 분석 ===\n'))
        
        # 대표적인 프로필로 테스트
        test_profiles = [
            {
                'vibe': 'modern',
                'household_size': 1,
                'housing_type': 'apartment',
                'main_space': 'living',
                'space_size': 'small',
                'priority': 'value',
                'budget_level': 'low',
                'categories': ['TV'] if not category else [category],
                'has_pet': False,
            },
            {
                'vibe': 'classic',
                'household_size': 4,
                'housing_type': 'house',
                'main_space': 'living',
                'space_size': 'large',
                'priority': 'tech',
                'budget_level': 'medium',
                'categories': ['TV', 'KITCHEN'] if not category else [category],
                'has_pet': False,
            },
        ]
        
        for i, profile in enumerate(test_profiles, 1):
            self.stdout.write(f"\n프로필 {i}:")
            result = engine.get_recommendations(profile, limit=10)
            
            if result.get('success') and result.get('recommendations'):
                scores = [rec.get('score', 0) for rec in result['recommendations']]
                self.stdout.write(f"  추천 개수: {len(scores)}")
                self.stdout.write(f"  점수 범위: {min(scores):.3f} ~ {max(scores):.3f}")
                self.stdout.write(f"  평균 점수: {sum(scores)/len(scores):.3f}")
                self.stdout.write(f"  중앙값: {sorted(scores)[len(scores)//2]:.3f}")

    def _generate_test_profiles(self, count, category):
        """테스트용 프로필 생성"""
        vibes = ['modern', 'classic', 'luxury', 'minimal']
        housing_types = ['apartment', 'house']
        space_sizes = ['small', 'medium', 'large']
        priorities = ['value', 'tech', 'design', 'eco']
        budget_levels = ['low', 'medium', 'high']
        categories_list = [category] if category else ['TV', 'KITCHEN', 'LIVING', 'AIR']
        
        profiles = []
        for i in range(count):
            # 카테고리 선택
            num_categories = random.randint(1, min(3, len(categories_list)))
            selected_categories = random.sample(categories_list, num_categories)
            
            profile = {
                'vibe': random.choice(vibes),
                'household_size': random.randint(1, 5),
                'housing_type': random.choice(housing_types),
                'main_space': 'living',
                'space_size': random.choice(space_sizes),
                'priority': random.choice(priorities),
                'budget_level': random.choice(budget_levels),
                'categories': selected_categories,
                'has_pet': random.choice([True, False]),
            }
            profiles.append(profile)
        
        return profiles

