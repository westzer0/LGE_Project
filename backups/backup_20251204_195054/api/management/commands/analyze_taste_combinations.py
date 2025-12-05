"""
온보딩 설문 데이터로 가능한 취향 조합 수 분석

사용법:
    python manage.py analyze_taste_combinations
"""
import csv
import os
from collections import defaultdict
from itertools import product
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = '온보딩 설문 데이터로 가능한 취향 조합 수를 분석합니다'

    def add_arguments(self, parser):
        parser.add_argument(
            '--csv-path',
            type=str,
            default='data/온보딩/onboarding_survey_aug_1000.csv',
            help='CSV 파일 경로',
        )

    def handle(self, *args, **options):
        csv_path = options['csv_path']
        
        self.stdout.write(self.style.SUCCESS('\n=== 취향 조합 분석 ===\n'))
        
        # CSV 파일 읽기
        if not os.path.exists(csv_path):
            self.stdout.write(self.style.ERROR(f'CSV 파일을 찾을 수 없습니다: {csv_path}'))
            return
        
        # CSV 파싱
        columns_data = self._parse_csv(csv_path)
        
        # 각 칼럼별 고유 값 개수 출력
        self.stdout.write('\n[각 칼럼별 고유 값 개수]\n')
        for col_name, values in columns_data.items():
            self.stdout.write(f'  {col_name}: {len(values)}개')
            if len(values) <= 10:
                self.stdout.write(f'    → {list(values)}')
            else:
                self.stdout.write(f'    → {list(values)[:5]} ... (총 {len(values)}개)')
        
        # 이론적 최대 조합 수 계산
        self.stdout.write('\n\n[이론적 최대 조합 수]\n')
        total_combinations = 1
        for col_name, values in columns_data.items():
            count = len(values)
            total_combinations *= count
            self.stdout.write(f'  {col_name}: {count}가지')
        
        self.stdout.write(f'\n  총 조합 수: {total_combinations:,}가지')
        
        # 실제 데이터에서 나타난 조합 수
        self.stdout.write('\n\n[실제 데이터 조합 분석]\n')
        actual_combinations = self._count_actual_combinations(csv_path)
        self.stdout.write(f'  실제 나타난 조합: {actual_combinations:,}가지')
        
        # 주요 칼럼만으로 조합 계산 (취향 분석에 중요한 것들)
        self.stdout.write('\n\n[주요 취향 요소 조합]\n')
        key_columns = [
            '질문 1 ) 새로운 가전이 놓일 공간, 어떤 무드를 꿈꾸시나요? (가장 마음에 드는 인테리어 스타일을 하나 선택해주세요.)',
            '질문 2 ) 이 공간에서 함께 생활하는 메이트는 누구인가요?',
            '질문 4 ) 가전 선택 시, 나에게 절대 포기할 수 없는 한 가지는? (추천 결과의 1순위를 결정하는 중요한 질문이에요.)',
            '질문 5) 생각하고 계신 전체 가전 구매 예산 범위는 어느 정도인가요? [가전 구매 예산 범위 (전체 금액)]',
            '질문 5) 생각하고 계신 전체 가전 구매 예산 범위는 어느 정도인가요? [선호하는 제품 라인업]',
        ]
        
        key_combinations = 1
        for col_name in key_columns:
            if col_name in columns_data:
                count = len(columns_data[col_name])
                key_combinations *= count
                self.stdout.write(f'  {col_name.split(")")[0] if ")" in col_name else col_name[:30]}...: {count}가지')
        
        self.stdout.write(f'\n  주요 요소 조합 수: {key_combinations:,}가지')
        
        # 취향 분류 제안
        self.stdout.write('\n\n[취향 분류 제안]\n')
        self._suggest_taste_categories(columns_data)

    def _parse_csv(self, csv_path):
        """CSV 파일을 파싱하여 각 칼럼별 고유 값 추출"""
        columns_data = defaultdict(set)
        
        with open(csv_path, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            for row in reader:
                for col_name, value in row.items():
                    if value and value.strip():
                        columns_data[col_name].add(value.strip())
        
        return columns_data

    def _count_actual_combinations(self, csv_path):
        """실제 데이터에서 나타난 고유 조합 수 계산"""
        combinations = set()
        
        with open(csv_path, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # 모든 칼럼 값을 튜플로 만들어서 조합으로 취급
                combo = tuple(sorted([(k, v.strip()) for k, v in row.items() if v and v.strip()]))
                combinations.add(combo)
        
        return len(combinations)

    def _suggest_taste_categories(self, columns_data):
        """취향 분류 제안"""
        # 질문 1: 인테리어 스타일
        vibe_col = '질문 1 ) 새로운 가전이 놓일 공간, 어떤 무드를 꿈꾸시나요? (가장 마음에 드는 인테리어 스타일을 하나 선택해주세요.)'
        vibe_count = len(columns_data.get(vibe_col, set()))
        
        # 질문 2: 메이트 (가족 구성)
        mate_col = '질문 2 ) 이 공간에서 함께 생활하는 메이트는 누구인가요?'
        mate_count = len(columns_data.get(mate_col, set()))
        
        # 질문 4: 우선순위
        priority_col = '질문 4 ) 가전 선택 시, 나에게 절대 포기할 수 없는 한 가지는? (추천 결과의 1순위를 결정하는 중요한 질문이에요.)'
        priority_count = len(columns_data.get(priority_col, set()))
        
        # 질문 5: 예산
        budget_col = '질문 5) 생각하고 계신 전체 가전 구매 예산 범위는 어느 정도인가요? [가전 구매 예산 범위 (전체 금액)]'
        budget_count = len(columns_data.get(budget_col, set()))
        
        # 질문 5: 라인업
        lineup_col = '질문 5) 생각하고 계신 전체 가전 구매 예산 범위는 어느 정도인가요? [선호하는 제품 라인업]'
        lineup_count = len(columns_data.get(lineup_col, set()))
        
        # 기본 조합
        basic_combinations = vibe_count * mate_count * priority_count * budget_count * lineup_count
        
        self.stdout.write(f'  기본 조합 (스타일 × 메이트 × 우선순위 × 예산 × 라인업):')
        self.stdout.write(f'    = {vibe_count} × {mate_count} × {priority_count} × {budget_count} × {lineup_count}')
        self.stdout.write(f'    = {basic_combinations:,}가지')
        
        # 추가 요소들
        pet_col = '질문 2-1) 혹시 사랑스러운 반려동물(댕냥이)과 함께하시나요?'
        pet_count = len(columns_data.get(pet_col, set()))
        
        housing_col = '질문 3) 가전을 설치할 곳의 \'주거 형태\'는 무엇인가요?'
        housing_count = len(columns_data.get(housing_col, set()))
        
        space_col = '질문 3-1) (원룸 제외) 가전을 배치할 \'주요 공간\'은 어디인가요?'
        space_count = len(columns_data.get(space_col, set()))
        
        self.stdout.write(f'\n  추가 요소 포함:')
        self.stdout.write(f'    반려동물: {pet_count}가지')
        self.stdout.write(f'    주거형태: {housing_count}가지')
        self.stdout.write(f'    주요공간: {space_count}가지')
        
        extended_combinations = basic_combinations * pet_count * housing_count * space_count
        self.stdout.write(f'\n  확장 조합: {extended_combinations:,}가지')
        
        # 실용적 제안
        self.stdout.write(f'\n  [실용적 제안]')
        self.stdout.write(f'    - 핵심 취향: {basic_combinations:,}가지로 분류 가능')
        self.stdout.write(f'    - 세부 취향: {extended_combinations:,}가지로 분류 가능')
        self.stdout.write(f'    - 권장: 핵심 취향 {basic_combinations:,}가지 + 추가 요소는 가중치로 반영')

