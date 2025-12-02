"""
온보딩 설문 데이터로 개인별 스코어링 차이 테스트

사용법:
    python manage.py test_survey_scoring
    python manage.py test_survey_scoring --sample 5
"""
import csv
import os
from django.core.management.base import BaseCommand
from api.services.recommendation_engine import RecommendationEngine
from django.conf import settings


class Command(BaseCommand):
    help = '온보딩 설문 데이터로 개인별 스코어링 차이를 테스트합니다'

    def add_arguments(self, parser):
        parser.add_argument(
            '--sample',
            type=int,
            default=10,
            help='테스트할 샘플 수 (기본: 10)',
        )
        parser.add_argument(
            '--csv-path',
            type=str,
            default='data/온보딩/onboarding_survey_aug_1000.csv',
            help='CSV 파일 경로',
        )

    def handle(self, *args, **options):
        sample_size = options['sample']
        csv_path = options['csv_path']
        
        self.stdout.write(self.style.SUCCESS('\n=== 온보딩 설문 데이터 스코어링 테스트 ===\n'))
        
        # CSV 파일 읽기
        if not os.path.exists(csv_path):
            self.stdout.write(self.style.ERROR(f'CSV 파일을 찾을 수 없습니다: {csv_path}'))
            return
        
        # CSV 파싱 및 변환
        profiles = self._parse_csv(csv_path, sample_size)
        
        if not profiles:
            self.stdout.write(self.style.ERROR('프로필을 생성할 수 없습니다.'))
            return
        
        self.stdout.write(f'총 {len(profiles)}개의 프로필로 테스트합니다.\n')
        
        # 추천 엔진 초기화
        engine = RecommendationEngine()
        
        # 각 프로필별로 추천 결과 비교
        results = []
        for i, profile in enumerate(profiles, 1):
            self.stdout.write(f'\n--- 프로필 {i}: {profile.get("name", "Unknown")} ---')
            result = self._test_profile(engine, profile)
            results.append(result)
        
        # 결과 요약
        self._print_summary(results)

    def _parse_csv(self, csv_path, sample_size):
        """CSV 파일을 파싱하여 프로필 리스트 생성"""
        profiles = []
        
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)[:sample_size]
            
            for row in rows:
                profile = self._convert_csv_to_profile(row)
                if profile:
                    profiles.append(profile)
        
        return profiles

    def _convert_csv_to_profile(self, row):
        """CSV 행을 추천 엔진 프로필로 변환"""
        try:
            # 질문 1: 인테리어 스타일 → vibe
            vibe_text = row.get('질문 1 ) 새로운 가전이 놓일 공간, 어떤 무드를 꿈꾸시나요? (가장 마음에 드는 인테리어 스타일을 하나 선택해주세요.)', '')
            vibe = self._map_vibe(vibe_text)
            
            # 질문 2: 메이트 → household_size
            mate_text = row.get('질문 2 ) 이 공간에서 함께 생활하는 메이트는 누구인가요?', '')
            household_size = self._map_household_size(mate_text)
            
            # 질문 2-1: 반려동물 → has_pet
            pet_text = row.get('질문 2-1) 혹시 사랑스러운 반려동물(댕냥이)과 함께하시나요?', '')
            has_pet = '네' in pet_text or '있' in pet_text
            
            # 질문 3: 주거 형태 → housing_type
            housing_text = row.get('질문 3) 가전을 설치할 곳의 \'주거 형태\'는 무엇인가요?', '')
            housing_type = self._map_housing_type(housing_text)
            
            # 질문 3-1: 주요 공간 → main_space
            space_text = row.get('질문 3-1) (원룸 제외) 가전을 배치할 \'주요 공간\'은 어디인가요?', '')
            main_space = self._map_main_space(space_text)
            
            # 질문 3-2: 공간 크기 → space_size
            size_text = row.get('질문 3-2) 해당 공간의 크기는 대략 어느 정도인가요? ( 정확한 수치 입력: ____ 평 / ____ ㎡  )\n* 전체 선택 시 전체 공간 크기 입력', '')
            space_size = self._map_space_size(size_text)
            
            # 질문 4: 절대 포기할 수 없는 것 → priority
            priority_text = row.get('질문 4 ) 가전 선택 시, 나에게 절대 포기할 수 없는 한 가지는? (추천 결과의 1순위를 결정하는 중요한 질문이에요.)', '')
            priority = self._map_priority(priority_text)
            
            # 질문 5: 예산 범위 → budget_level
            budget_text = row.get('질문 5) 생각하고 계신 전체 가전 구매 예산 범위는 어느 정도인가요? [가전 구매 예산 범위 (전체 금액)]', '')
            budget_level = self._map_budget_level(budget_text)
            
            # 카테고리는 기본값 (TV, KITCHEN, LIVING)
            categories = ['TV', 'KITCHEN', 'LIVING']
            
            return {
                'name': f"{vibe}_{household_size}인_{priority}",
                'vibe': vibe,
                'household_size': household_size,
                'has_pet': has_pet,
                'housing_type': housing_type,
                'main_space': main_space,
                'space_size': space_size,
                'priority': priority,
                'budget_level': budget_level,
                'categories': categories,
            }
        except Exception as e:
            self.stdout.write(self.style.WARNING(f'프로필 변환 실패: {e}'))
            return None

    def _map_vibe(self, text):
        """인테리어 스타일 텍스트를 vibe 코드로 변환"""
        text_lower = text.lower()
        if '모던' in text or '미니멀' in text:
            return 'modern'
        elif '코지' in text or '네이처' in text or 'cozy' in text_lower:
            return 'cozy'
        elif '유니크' in text or '팝' in text or 'unique' in text_lower or 'pop' in text_lower:
            return 'pop'
        elif '럭셔리' in text or '아티스틱' in text or 'luxury' in text_lower:
            return 'luxury'
        return 'modern'  # 기본값

    def _map_household_size(self, text):
        """메이트 텍스트를 가족 인원수로 변환"""
        if '1인' in text or '혼자' in text:
            return 1
        elif '2인' in text or '신혼' in text or '둘이' in text:
            return 2
        elif '3' in text or '4인' in text or '가족' in text:
            # "3~4인 가족" 같은 경우
            if '3' in text:
                return 3
            elif '4' in text:
                return 4
            return 4  # 기본값
        return 2  # 기본값

    def _map_housing_type(self, text):
        """주거 형태 텍스트를 housing_type 코드로 변환"""
        if '아파트' in text:
            return 'apartment'
        elif '주택' in text or 'house' in text.lower():
            return 'house'
        elif '원룸' in text or '투룸' in text:
            return 'studio'
        elif '오피스텔' in text:
            return 'officetel'
        return 'apartment'  # 기본값

    def _map_main_space(self, text):
        """주요 공간 텍스트를 main_space 코드로 변환"""
        if '거실' in text:
            return 'living'
        elif '주방' in text:
            return 'kitchen'
        elif '방' in text or '침실' in text:
            return 'bedroom'
        return 'living'  # 기본값

    def _map_space_size(self, text):
        """공간 크기 텍스트를 space_size 코드로 변환"""
        # 평수 추출
        import re
        numbers = re.findall(r'\d+', text)
        if numbers:
            pyung = int(numbers[0])
            if pyung <= 10:
                return 'small'
            elif pyung <= 20:
                return 'medium'
            else:
                return 'large'
        return 'medium'  # 기본값

    def _map_priority(self, text):
        """절대 포기할 수 없는 것 텍스트를 priority 코드로 변환"""
        if 'AI' in text or '스마트' in text or '기능' in text:
            return 'tech'
        elif '디자인' in text:
            return 'design'
        elif '가성비' in text or '가격' in text:
            return 'value'
        elif '에너지' in text or '효율' in text:
            return 'eco'
        return 'value'  # 기본값

    def _map_budget_level(self, text):
        """예산 범위 텍스트를 budget_level 코드로 변환"""
        if '500만원 미만' in text or '실속' in text:
            return 'low'
        elif '500만원 ~ 1,500만원' in text or '표준' in text:
            return 'medium'
        elif '1,500만원 ~ 3,000만원' in text or '고급' in text:
            return 'high'
        elif '3,000만원 이상' in text or '하이엔드' in text:
            return 'high'
        return 'medium'  # 기본값

    def _test_profile(self, engine, profile):
        """개별 프로필로 추천 테스트"""
        try:
            result = engine.get_recommendations(profile, limit=5)
            
            if result.get('success') and result.get('recommendations'):
                recommendations = result['recommendations']
                scores = [r.get('score', 0) for r in recommendations]
                
                self.stdout.write(f"  Vibe: {profile['vibe']}, Priority: {profile['priority']}, "
                               f"가족: {profile['household_size']}인, 예산: {profile['budget_level']}")
                self.stdout.write(f"  추천 개수: {len(recommendations)}")
                self.stdout.write(f"  점수 범위: {min(scores):.3f} ~ {max(scores):.3f} (평균: {sum(scores)/len(scores):.3f})")
                self.stdout.write(f"  상위 3개 제품:")
                for i, rec in enumerate(recommendations[:3], 1):
                    self.stdout.write(f"    {i}. {rec.get('model', 'N/A')} - 점수: {rec.get('score', 0):.3f}")
                
                return {
                    'profile': profile,
                    'success': True,
                    'count': len(recommendations),
                    'scores': scores,
                    'top_products': recommendations[:3],
                }
            else:
                self.stdout.write(self.style.WARNING(f"  추천 실패: {result.get('error', 'Unknown error')}"))
                return {
                    'profile': profile,
                    'success': False,
                    'error': result.get('error', 'Unknown error'),
                }
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"  오류: {e}"))
            return {
                'profile': profile,
                'success': False,
                'error': str(e),
            }

    def _print_summary(self, results):
        """결과 요약 출력"""
        self.stdout.write(self.style.SUCCESS('\n=== 결과 요약 ===\n'))
        
        successful = [r for r in results if r.get('success')]
        failed = [r for r in results if not r.get('success')]
        
        self.stdout.write(f'성공: {len(successful)}/{len(results)}')
        if failed:
            self.stdout.write(self.style.ERROR(f'실패: {len(failed)}개'))
        
        if successful:
            # 점수 분포 분석
            all_scores = []
            for r in successful:
                all_scores.extend(r.get('scores', []))
            
            if all_scores:
                self.stdout.write(f'\n전체 점수 통계:')
                self.stdout.write(f'  평균: {sum(all_scores)/len(all_scores):.3f}')
                self.stdout.write(f'  최소: {min(all_scores):.3f}')
                self.stdout.write(f'  최대: {max(all_scores):.3f}')
            
            # 프로필별 점수 차이 확인
            self.stdout.write(f'\n프로필별 점수 차이:')
            for r in successful:
                profile = r['profile']
                avg_score = sum(r['scores']) / len(r['scores']) if r['scores'] else 0
                self.stdout.write(f"  {profile['name']}: 평균 {avg_score:.3f}")

