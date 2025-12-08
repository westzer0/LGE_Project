"""
Oracle DB에서 모든 온보딩 질문/답변을 조회하여 모든 경우의 수 생성
평수(pyung) 제외, 나머지 모든 질문의 조합 생성

사용법:
    python manage.py generate_all_onboarding_combinations
"""
import json
from itertools import product, combinations
from django.core.management.base import BaseCommand
from api.db.oracle_client import fetch_all_dict
from api.utils.taste_classifier_weighted import WeightedTasteClassifier


class Command(BaseCommand):
    help = 'Oracle DB에서 모든 온보딩 질문/답변을 조회하여 모든 경우의 수를 생성하고 120개 taste로 매핑합니다'

    def add_arguments(self, parser):
        parser.add_argument(
            '--output',
            type=str,
            default=None,
            help='출력 JSON 파일 경로 (지정하지 않으면 콘솔에만 출력)',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('\n=== 온보딩 모든 경우의 수 생성 ===\n'))
        
        # 1. Oracle DB에서 질문과 답변 조회
        self.stdout.write('[1] Oracle DB에서 질문/답변 조회 중...')
        questions_data = self._load_questions_from_db()
        
        # 2. 각 질문별 답변 목록 구성 (평수 5개 단위 클러스터링 포함)
        self.stdout.write('[2] 질문별 답변 목록 구성 중 (평수 5개 단위 클러스터링)...')
        question_answers = self._build_question_answers(questions_data)
        
        # 각 질문별 선택지 수 출력
        self.stdout.write('\n  질문별 선택지 수:')
        for q_type, answers in sorted(question_answers.items()):
            count = len(answers)
            self.stdout.write(f'    {q_type}: {count}개')
        
        # 3. 모든 조합 생성
        self.stdout.write('[3] 모든 조합 생성 중...')
        all_combinations = self._generate_all_combinations(question_answers)
        
        self.stdout.write(f'  - 총 조합 수: {len(all_combinations):,}개')
        
        # 4. 각 조합을 80개 taste로 매핑 (Question 중요도 고려)
        self.stdout.write('[4] 80개 taste로 매핑 중 (Question 중요도 고려)...')
        taste_mapping = self._map_to_tastes(all_combinations)
        
        # 5. 결과 출력
        self._print_statistics(taste_mapping, all_combinations)
        
        # 6. 파일 저장 (옵션)
        if options['output']:
            self._save_to_file(taste_mapping, all_combinations, options['output'])
        
        self.stdout.write(self.style.SUCCESS('\n[OK] 완료!'))

    def _load_questions_from_db(self):
        """Oracle DB에서 모든 질문과 답변 조회 (평수 포함)"""
        # 질문 조회 (실제 Oracle DB 구조에 맞게)
        questions_sql = """
            SELECT 
                QUESTION_CODE,
                QUESTION_TEXT,
                QUESTION_TYPE,
                IS_REQUIRED,
                CREATED_DATE
            FROM ONBOARDING_QUESTION
            ORDER BY QUESTION_CODE
        """
        
        questions = fetch_all_dict(questions_sql)
        
        # 각 질문의 답변 조회
        for question in questions:
            answers_sql = """
                SELECT 
                    ANSWER_ID,
                    ANSWER_VALUE,
                    ANSWER_TEXT
                FROM ONBOARDING_ANSWER
                WHERE QUESTION_CODE = :question_code
                ORDER BY ANSWER_ID
            """
            question['answers'] = fetch_all_dict(answers_sql, {'question_code': question['QUESTION_CODE']})
        
        return questions

    def _build_question_answers(self, questions_data):
        """질문별 답변 목록 구성 (다중선택 고려, 평수 5개 단위 클러스터링)"""
        question_answers = {}
        question_metadata = {}  # 조건부 질문 정보 저장
        
        for question in questions_data:
            q_type = question['QUESTION_TYPE']
            answers = question.get('answers', [])
            
            # 평수는 특별 처리 (5개 단위로 클러스터링)
            if q_type == 'pyung':
                # 평수를 5개 단위로 클러스터링: 10, 15, 20, 25, 30, 35, 40, 45, 50, 55, 60...
                # 일반적인 평수 범위: 10평 ~ 60평 (5평 단위)
                pyung_clusters = []
                for pyung in range(10, 65, 5):  # 10, 15, 20, ..., 60
                    pyung_clusters.append(pyung)
                question_answers[q_type] = pyung_clusters
                continue
            
            if not answers:
                continue
            
            # 조건부 질문 정보 저장 (실제 DB에 컬럼이 없으면 스킵)
            # 조건부 질문은 main_space 선택에 따라 결정됨
            
            # 다중선택 가능한 질문 처리
            if q_type == 'main_space':
                # main_space는 다중선택 가능 (1개 이상 선택)
                # 6개 중 1개 이상 선택 = 2^6 - 1 = 63가지
                answer_values = [a['ANSWER_VALUE'] for a in answers]
                # 모든 가능한 조합 생성 (1개 이상)
                combinations_list = []
                for r in range(1, len(answer_values) + 1):
                    for combo in combinations(answer_values, r):
                        combinations_list.append(list(combo))
                question_answers[q_type] = combinations_list
                
            elif q_type == 'priority':
                # priority도 다중선택 가능 (1개 이상 선택)
                # 4개 중 1개 이상 선택 = 2^4 - 1 = 15가지
                answer_values = [a['ANSWER_VALUE'] for a in answers]
                combinations_list = []
                for r in range(1, len(answer_values) + 1):
                    for combo in combinations(answer_values, r):
                        combinations_list.append(list(combo))
                question_answers[q_type] = combinations_list
                
            else:
                # 단일 선택 질문
                question_answers[q_type] = [a['ANSWER_VALUE'] for a in answers]
        
        # 조건부 질문 메타데이터 저장
        self.question_metadata = question_metadata
        return question_answers

    def _generate_all_combinations(self, question_answers):
        """모든 조합 생성 (조건부 질문 고려, 평수 포함)"""
        # 필수 질문부터 처리 (평수 포함)
        required_questions = ['vibe', 'mate', 'pet', 'housing_type', 'main_space', 'pyung', 'priority', 'budget']
        optional_questions = ['cooking', 'laundry', 'media']
        
        # 필수 질문의 조합 생성
        required_types = [q for q in required_questions if q in question_answers]
        required_answer_lists = [question_answers[q_type] for q_type in required_types]
        
        all_combinations = []
        total_required = 1
        for lst in required_answer_lists:
            total_required *= len(lst)
        
        self.stdout.write(f'  - 필수 질문 조합 수: {total_required:,}개')
        
        # 필수 질문 조합 생성
        for idx, required_combo in enumerate(product(*required_answer_lists)):
            if idx % 10000 == 0 and idx > 0:
                self.stdout.write(f'    진행 중... {idx:,}개 처리됨')
            
            combination_dict = {}
            for i, q_type in enumerate(required_types):
                combination_dict[q_type] = required_combo[i]
            
            # 조건부 질문 처리
            main_space_value = combination_dict.get('main_space', [])
            if isinstance(main_space_value, str):
                main_space_list = [main_space_value]
            else:
                main_space_list = main_space_value
            
            # cooking: kitchen 또는 all이 선택된 경우만
            if 'kitchen' in main_space_list or 'all' in main_space_list:
                if 'cooking' in question_answers:
                    for cooking_value in question_answers['cooking']:
                        combo_with_cooking = combination_dict.copy()
                        combo_with_cooking['cooking'] = cooking_value
                        # laundry 처리
                        self._add_optional_questions(combo_with_cooking, main_space_list, question_answers, all_combinations)
                else:
                    combo_with_cooking = combination_dict.copy()
                    combo_with_cooking['cooking'] = None
                    self._add_optional_questions(combo_with_cooking, main_space_list, question_answers, all_combinations)
            else:
                combo_with_cooking = combination_dict.copy()
                combo_with_cooking['cooking'] = None
                self._add_optional_questions(combo_with_cooking, main_space_list, question_answers, all_combinations)
        
        return all_combinations
    
    def _add_optional_questions(self, combo_dict, main_space_list, question_answers, all_combinations):
        """조건부 질문 추가 (laundry, media)"""
        # laundry: dressing 또는 all이 선택된 경우만
        if 'dressing' in main_space_list or 'all' in main_space_list:
            if 'laundry' in question_answers:
                for laundry_value in question_answers['laundry']:
                    combo_with_laundry = combo_dict.copy()
                    combo_with_laundry['laundry'] = laundry_value
                    # media 처리
                    self._add_media_question(combo_with_laundry, main_space_list, question_answers, all_combinations)
            else:
                combo_with_laundry = combo_dict.copy()
                combo_with_laundry['laundry'] = None
                self._add_media_question(combo_with_laundry, main_space_list, question_answers, all_combinations)
        else:
            combo_with_laundry = combo_dict.copy()
            combo_with_laundry['laundry'] = None
            self._add_media_question(combo_with_laundry, main_space_list, question_answers, all_combinations)
    
    def _add_media_question(self, combo_dict, main_space_list, question_answers, all_combinations):
        """media 질문 추가"""
        # media: living, bedroom, study, all 중 하나라도 선택된 경우
        if any(space in main_space_list for space in ['living', 'bedroom', 'study', 'all']):
            if 'media' in question_answers:
                for media_value in question_answers['media']:
                    combo_with_media = combo_dict.copy()
                    combo_with_media['media'] = media_value
                    all_combinations.append(combo_with_media)
            else:
                combo_with_media = combo_dict.copy()
                combo_with_media['media'] = None
                all_combinations.append(combo_with_media)
        else:
            combo_with_media = combo_dict.copy()
            combo_with_media['media'] = None
            all_combinations.append(combo_with_media)

    def _map_to_tastes(self, all_combinations):
        """각 조합을 80개 taste로 매핑"""
        taste_mapping = {}  # {taste_id: [combinations]}
        
        for combo in all_combinations:
            # 온보딩 데이터 형식으로 변환
            onboarding_data = self._convert_to_onboarding_data(combo)
            
            # taste_id 계산 (가중치 기반, 100개 이하)
            taste_id = WeightedTasteClassifier.calculate_taste_from_onboarding(onboarding_data)
            
            if taste_id not in taste_mapping:
                taste_mapping[taste_id] = []
            taste_mapping[taste_id].append(combo)
        
        return taste_mapping

    def _convert_to_onboarding_data(self, combo):
        """조합 딕셔너리를 온보딩 데이터 형식으로 변환 (평수 포함)"""
        # main_space 처리 (리스트로)
        main_space = combo.get('main_space', [])
        if isinstance(main_space, str):
            main_space = [main_space]
        
        # priority 처리 (리스트로)
        priority = combo.get('priority', [])
        if isinstance(priority, str):
            priority = [priority]
        
        # has_pet 처리
        has_pet = combo.get('pet') == 'yes' if 'pet' in combo else False
        
        # household_size 변환 (mate 값에 따라)
        household_size = self._mate_to_household_size(combo.get('mate', 'alone'))
        
        # pyung 처리 (5개 단위 클러스터링된 값 사용)
        pyung = combo.get('pyung', 25)
        
        return {
            'vibe': combo.get('vibe', 'modern'),
            'household_size': household_size,
            'housing_type': combo.get('housing_type', 'apartment'),
            'pyung': pyung,  # 5개 단위로 클러스터링된 평수 사용
            'budget_level': self._budget_to_budget_level(combo.get('budget', 'standard')),
            'priority': priority,
            'main_space': main_space,
            'has_pet': has_pet,
            'cooking': combo.get('cooking', 'sometimes'),
            'laundry': combo.get('laundry', 'weekly'),
            'media': combo.get('media', 'balanced'),
        }

    def _mate_to_household_size(self, mate_value):
        """mate 값을 household_size로 변환"""
        mapping = {
            'alone': 1,
            'couple': 2,
            'family_3_4': 3,
            'family_5plus': 5,
        }
        return mapping.get(mate_value, 2)

    def _budget_to_budget_level(self, budget_value):
        """budget 값을 budget_level로 변환"""
        mapping = {
            'budget': 'low',
            'standard': 'medium',
            'premium': 'high',
        }
        return mapping.get(budget_value, 'medium')

    def _print_statistics(self, taste_mapping, all_combinations):
        """통계 출력"""
        self.stdout.write('\n=== 통계 ===')
        self.stdout.write(f'총 조합 수: {len(all_combinations):,}개')
        self.stdout.write(f'Taste 그룹 수: {len(taste_mapping)}개')
        
        # Taste별 조합 수 분포
        taste_counts = [len(combos) for combos in taste_mapping.values()]
        if taste_counts:
            self.stdout.write(f'\nTaste별 조합 수:')
            self.stdout.write(f'  최소: {min(taste_counts):,}개')
            self.stdout.write(f'  최대: {max(taste_counts):,}개')
            self.stdout.write(f'  평균: {sum(taste_counts) / len(taste_counts):.1f}개')
        
        # 상위 5개 taste
        sorted_tastes = sorted(taste_mapping.items(), key=lambda x: len(x[1]), reverse=True)
        self.stdout.write(f'\n상위 5개 Taste (조합 수 기준):')
        for taste_id, combos in sorted_tastes[:5]:
            self.stdout.write(f'  Taste {taste_id}: {len(combos):,}개 조합')

    def _save_to_file(self, taste_mapping, all_combinations, output_path):
        """결과를 파일로 저장"""
        output_data = {
            'total_combinations': len(all_combinations),
            'taste_count': len(taste_mapping),
            'taste_mapping': {
                str(taste_id): {
                    'combination_count': len(combos),
                    'sample_combinations': combos[:3]  # 샘플 3개만
                }
                for taste_id, combos in taste_mapping.items()
            },
            'statistics': {
                'taste_distribution': {
                    str(taste_id): len(combos)
                    for taste_id, combos in taste_mapping.items()
                }
            }
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)
        
        self.stdout.write(f'\n[FILE] 결과 저장: {output_path}')

