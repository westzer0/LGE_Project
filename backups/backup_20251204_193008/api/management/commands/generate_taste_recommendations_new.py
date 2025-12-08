"""
새로운 온보딩 단계에 맞춘 취향 데이터 생성

실제 온보딩 단계:
1. 분위기 (vibe)
2. 함께 생활하는 메이트 (mate)
3. 반려동물 (pet)
4. 주거형태 (housing_type)
5. 공간의 크기 (pyung)
6. 세탁 주기 (laundry)
7. 가전선택시 중요한 우선순위 (priority)
8. 예산 범위 (budget_level)

각 단계별 옵션:
1. 분위기: modern, cozy, luxury, unique
2. 메이트: 1인, 2인, 3~4인, 5인 이상
3. 반려동물: yes, no
4. 주거형태: apartment, studio, house
5. 공간 크기: 20평 이하, 20~30평, 30평 이상
6. 세탁 주기: weekly, few_times, daily, none
7. 우선순위: design, performance, efficiency, value
8. 예산 범위: budget, standard, premium, luxury

총 조합: 4 * 4 * 2 * 3 * 3 * 4 * 4 * 4 = 12,288개
하지만 실제로는 일부 조합이 의미가 없을 수 있으므로, 합리적인 조합만 생성
"""
import csv
import os
from itertools import product
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = '새로운 온보딩 단계에 맞춘 취향 데이터 생성'

    def add_arguments(self, parser):
        parser.add_argument(
            '--output',
            type=str,
            default='data/온보딩/taste_recommendations_new.csv',
            help='출력 CSV 파일 경로',
        )
        parser.add_argument(
            '--limit',
            type=int,
            default=None,
            help='생성할 조합 수 제한 (None이면 전체)',
        )

    def handle(self, *args, **options):
        output_path = options['output']
        limit = options['limit']
        
        self.stdout.write(self.style.SUCCESS('\n=== 새로운 취향 데이터 생성 ===\n'))
        
        # 각 단계별 옵션 정의 (실제 온보딩 단계에 맞춤)
        # 1. 분위기
        vibes = ['modern', 'cozy', 'pop', 'luxury']  # onboarding.html에서 확인
        
        # 2. 함께 생활하는 메이트
        mates = ['1인', '2인', '3~4인', '5인 이상']
        
        # 3. 반려동물
        pets = ['yes', 'no']
        
        # 4. 주거형태 (onboarding_step3.html에서 확인)
        housing_types = ['apartment', 'officetel', 'detached', 'studio']
        
        # 5. 공간의 크기 (평수)
        pyungs = ['20평 이하', '20~30평', '30평 이상']
        
        # 6. 세탁 주기 (onboarding_step4.html에서 확인)
        laundries = ['weekly', 'few_times', 'daily', 'none']
        
        # 7. 가전선택시 중요한 우선순위
        priorities = ['design', 'performance', 'efficiency', 'value']
        
        # 8. 예산 범위
        budget_levels = ['budget', 'standard', 'premium', 'luxury']
        
        # 모든 조합 생성
        self.stdout.write('[1] 조합 생성 중...')
        all_combinations = list(product(
            vibes, mates, pets, housing_types, pyungs, laundries, priorities, budget_levels
        ))
        
        total = len(all_combinations)
        self.stdout.write(f'  - 총 {total:,}개 조합 생성됨')
        
        if limit:
            all_combinations = all_combinations[:limit]
            self.stdout.write(f'  - 제한 적용: {limit}개만 생성')
        
        # CSV 파일 생성
        self.stdout.write(f'\n[2] CSV 파일 생성 중: {output_path}')
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8-sig', newline='') as f:
            writer = csv.writer(f)
            
            # 헤더 작성
            headers = [
                'taste_id',
                '분위기',
                '메이트_구성',
                '반려동물',
                '주거형태',
                '공간_크기',
                '세탁_주기',
                '우선순위',
                '예산_범위',
                '리뷰_기반_추천문구',
                'AI_기반_추천문구',
            ]
            writer.writerow(headers)
            
            # 데이터 작성
            for idx, combo in enumerate(all_combinations, 1):
                vibe, mate, pet, housing_type, pyung, laundry, priority, budget_level = combo
                
                # taste_id는 1부터 시작
                taste_id = idx
                
                # 추천문구는 나중에 생성 (일단 빈 값)
                review_reason = ''
                ai_reason = ''
                
                writer.writerow([
                    taste_id,
                    vibe,
                    mate,
                    pet,
                    housing_type,
                    pyung,
                    laundry,
                    priority,
                    budget_level,
                    review_reason,
                    ai_reason,
                ])
        
        self.stdout.write(self.style.SUCCESS(f'\n[완료] {len(all_combinations):,}개 취향 데이터 생성 완료!'))
        self.stdout.write(f'[FILE] {output_path}')
        
        # 통계 출력
        self.stdout.write(f'\n[통계]')
        self.stdout.write(f'  - 분위기: {len(vibes)}개 옵션')
        self.stdout.write(f'  - 메이트 구성: {len(mates)}개 옵션')
        self.stdout.write(f'  - 반려동물: {len(pets)}개 옵션')
        self.stdout.write(f'  - 주거형태: {len(housing_types)}개 옵션')
        self.stdout.write(f'  - 공간 크기: {len(pyungs)}개 옵션')
        self.stdout.write(f'  - 세탁 주기: {len(laundries)}개 옵션')
        self.stdout.write(f'  - 우선순위: {len(priorities)}개 옵션')
        self.stdout.write(f'  - 예산 범위: {len(budget_levels)}개 옵션')
        self.stdout.write(f'  - 총 조합: {total:,}개')

