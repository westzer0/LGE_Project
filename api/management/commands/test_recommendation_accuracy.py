"""
추천 엔진 정확도 테스트 커맨드

사용법:
    python manage.py test_recommendation_accuracy
    python manage.py test_recommendation_accuracy --verbose
    python manage.py test_recommendation_accuracy --scenario all
"""
from django.core.management.base import BaseCommand
from api.services.recommendation_engine import RecommendationEngine
from api.models import Product, ProductSpec
import json


class Command(BaseCommand):
    help = '추천 엔진의 정확도를 테스트합니다'

    def add_arguments(self, parser):
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='상세한 출력 표시',
        )
        parser.add_argument(
            '--scenario',
            type=str,
            default='basic',
            choices=['basic', 'all', 'edge'],
            help='테스트 시나리오 선택 (basic, all, edge)',
        )

    def handle(self, *args, **options):
        self.verbose = options['verbose']
        scenario = options['scenario']
        
        self.stdout.write(self.style.SUCCESS('\n=== 추천 엔진 정확도 테스트 ===\n'))
        
        engine = RecommendationEngine()
        test_results = []
        
        # 기본 시나리오
        if scenario in ['basic', 'all']:
            test_results.extend(self._test_basic_scenarios(engine))
        
        # 엣지 케이스
        if scenario in ['edge', 'all']:
            test_results.extend(self._test_edge_cases(engine))
        
        # 결과 요약
        self._print_summary(test_results)
        
        if self.verbose:
            self._print_detailed_results(test_results)

    def _test_basic_scenarios(self, engine):
        """기본 시나리오 테스트"""
        scenarios = [
            {
                'name': '1인 가구 - 저예산',
                'profile': {
                    'vibe': 'modern',
                    'household_size': 1,
                    'housing_type': 'apartment',
                    'main_space': 'living',
                    'space_size': 'small',
                    'priority': 'value',
                    'budget_level': 'low',
                    'categories': ['TV', 'LIVING'],
                    'has_pet': False,
                },
                'expected': {
                    'min_count': 1,
                    'max_price': 500000,
                    'should_exclude_pet': True,
                }
            },
            {
                'name': '4인 가족 - 중예산',
                'profile': {
                    'vibe': 'classic',
                    'household_size': 4,
                    'housing_type': 'house',
                    'main_space': 'living',
                    'space_size': 'large',
                    'priority': 'tech',
                    'budget_level': 'medium',
                    'categories': ['TV', 'KITCHEN', 'LIVING'],
                    'has_pet': False,
                },
                'expected': {
                    'min_count': 1,
                    'min_price': 500000,
                    'max_price': 2000000,
                }
            },
            {
                'name': '프리미엄 가구 - 고예산',
                'profile': {
                    'vibe': 'luxury',
                    'household_size': 2,
                    'housing_type': 'house',
                    'main_space': 'living',
                    'space_size': 'large',
                    'priority': 'design',
                    'budget_level': 'high',
                    'categories': ['TV', 'KITCHEN'],
                    'has_pet': True,
                },
                'expected': {
                    'min_count': 1,
                    'min_price': 2000000,
                }
            },
            {
                'name': '반려동물 있는 가구',
                'profile': {
                    'vibe': 'modern',
                    'household_size': 2,
                    'housing_type': 'apartment',
                    'main_space': 'living',
                    'space_size': 'medium',
                    'priority': 'value',
                    'budget_level': 'medium',
                    'categories': ['LIVING'],
                    'has_pet': True,
                },
                'expected': {
                    'min_count': 0,  # 펫 제품이 있을 수도, 없을 수도 있음
                    'should_allow_pet': True,
                }
            },
        ]
        
        results = []
        for scenario in scenarios:
            result = self._run_test(engine, scenario)
            results.append(result)
        
        return results

    def _test_edge_cases(self, engine):
        """엣지 케이스 테스트"""
        scenarios = [
            {
                'name': '예산 범위 밖',
                'profile': {
                    'vibe': 'modern',
                    'household_size': 1,
                    'housing_type': 'apartment',
                    'main_space': 'living',
                    'space_size': 'small',
                    'priority': 'value',
                    'budget_level': 'low',
                    'categories': ['TV'],
                    'has_pet': False,
                },
                'expected': {
                    'should_handle_gracefully': True,
                }
            },
            {
                'name': '카테고리 없음',
                'profile': {
                    'vibe': 'modern',
                    'household_size': 2,
                    'housing_type': 'apartment',
                    'main_space': 'living',
                    'space_size': 'medium',
                    'priority': 'value',
                    'budget_level': 'medium',
                    'categories': [],
                    'has_pet': False,
                },
                'expected': {
                    'should_handle_gracefully': True,
                }
            },
        ]
        
        results = []
        for scenario in scenarios:
            result = self._run_test(engine, scenario)
            results.append(result)
        
        return results

    def _run_test(self, engine, scenario):
        """개별 테스트 실행"""
        name = scenario['name']
        profile = scenario['profile']
        expected = scenario['expected']
        
        try:
            result = engine.get_recommendations(profile, limit=5)
            
            # 검증
            checks = {
                'success': result.get('success', False),
                'has_recommendations': len(result.get('recommendations', [])) > 0,
            }
            
            if result.get('success') and result.get('recommendations'):
                recommendations = result['recommendations']
                
                # 예산 검증
                if 'max_price' in expected:
                    checks['price_within_max'] = all(
                        rec.get('price', 0) <= expected['max_price']
                        for rec in recommendations
                    )
                
                if 'min_price' in expected:
                    checks['price_above_min'] = all(
                        rec.get('price', 0) >= expected['min_price']
                        for rec in recommendations
                    )
                
                # 개수 검증
                if 'min_count' in expected:
                    checks['min_count_met'] = len(recommendations) >= expected['min_count']
                
                # 펫 필터링 검증
                if 'should_exclude_pet' in expected and expected['should_exclude_pet']:
                    # 펫 관련 키워드가 없는지 확인
                    pet_keywords = ['펫', 'PET', '반려동물', '애완동물']
                    checks['no_pet_products'] = not any(
                        any(keyword in rec.get('model', '') or keyword in rec.get('name', '')
                            for keyword in pet_keywords)
                        for rec in recommendations
                    )
                
                # 점수 검증
                if recommendations:
                    scores = [rec.get('score', 0) for rec in recommendations]
                    checks['scores_valid'] = all(0 <= score <= 1 for score in scores)
                    checks['scores_sorted'] = scores == sorted(scores, reverse=True)
                    checks['score_range'] = {
                        'min': min(scores),
                        'max': max(scores),
                        'avg': sum(scores) / len(scores),
                    }
            
            # 전체 통과 여부
            passed = all(checks.values()) if checks else False
            
            return {
                'name': name,
                'profile': profile,
                'result': result,
                'checks': checks,
                'passed': passed,
            }
            
        except Exception as e:
            return {
                'name': name,
                'profile': profile,
                'result': {'success': False, 'error': str(e)},
                'checks': {},
                'passed': False,
                'error': str(e),
            }

    def _print_summary(self, results):
        """결과 요약 출력"""
        total = len(results)
        passed = sum(1 for r in results if r.get('passed', False))
        failed = total - passed
        
        self.stdout.write(self.style.SUCCESS(f'\n=== 테스트 결과 요약 ==='))
        self.stdout.write(f'전체 테스트: {total}개')
        self.stdout.write(self.style.SUCCESS(f'통과: {passed}개'))
        self.stdout.write(self.style.ERROR(f'실패: {failed}개'))
        self.stdout.write(f'정확도: {passed/total*100:.1f}%\n')
        
        # 실패한 테스트 목록
        if failed > 0:
            self.stdout.write(self.style.WARNING('\n실패한 테스트:'))
            for result in results:
                if not result.get('passed', False):
                    self.stdout.write(f"  - {result['name']}")
                    if 'error' in result:
                        self.stdout.write(f"    오류: {result['error']}")

    def _print_detailed_results(self, results):
        """상세 결과 출력"""
        self.stdout.write(self.style.SUCCESS('\n=== 상세 결과 ===\n'))
        
        for result in results:
            status = self.style.SUCCESS('✓') if result.get('passed') else self.style.ERROR('✗')
            self.stdout.write(f"{status} {result['name']}")
            
            if self.verbose:
                if result.get('result', {}).get('success'):
                    recommendations = result['result'].get('recommendations', [])
                    self.stdout.write(f"  추천 개수: {len(recommendations)}")
                    
                    if recommendations:
                        self.stdout.write("  상위 추천 제품:")
                        for i, rec in enumerate(recommendations[:3], 1):
                            self.stdout.write(
                                f"    {i}. {rec.get('model', 'N/A')} "
                                f"(점수: {rec.get('score', 0):.3f}, "
                                f"가격: {rec.get('price', 0):,}원)"
                            )
                    
                    if 'score_range' in result.get('checks', {}):
                        score_range = result['checks']['score_range']
                        self.stdout.write(
                            f"  점수 범위: {score_range['min']:.3f} ~ {score_range['max']:.3f} "
                            f"(평균: {score_range['avg']:.3f})"
                        )
                
                # 검증 체크리스트
                checks = result.get('checks', {})
                if checks:
                    self.stdout.write("  검증 결과:")
                    for key, value in checks.items():
                        if key != 'score_range':
                            status_icon = '✓' if value else '✗'
                            self.stdout.write(f"    {status_icon} {key}: {value}")
                
                self.stdout.write('')

