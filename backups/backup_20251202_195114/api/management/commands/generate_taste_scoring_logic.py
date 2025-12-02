"""
취향별 독립적인 Scoring Logic 생성

768개 취향 조합을 분석하여 유사한 그룹으로 묶고,
각 그룹별로 독립적인 scoring logic을 생성합니다.

사용법:
    python manage.py generate_taste_scoring_logic
"""
import csv
import json
import os
import hashlib
from collections import defaultdict
from pathlib import Path
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = '취향별 독립적인 Scoring Logic을 생성합니다'

    def add_arguments(self, parser):
        parser.add_argument(
            '--csv-path',
            type=str,
            default='data/온보딩/taste_recommendations_768.csv',
            help='취향 조합 CSV 파일 경로',
        )
        parser.add_argument(
            '--output-dir',
            type=str,
            default='api/scoring_logic',
            help='Scoring Logic 저장 디렉토리',
        )
        parser.add_argument(
            '--target-groups',
            type=int,
            default=400,
            help='생성할 Scoring Logic 그룹 수 (기본: 400개)',
        )

    def handle(self, *args, **options):
        csv_path = options['csv_path']
        output_dir = options['output_dir']
        target_groups = options['target_groups']
        
        self.stdout.write(self.style.SUCCESS('\n=== 취향별 Scoring Logic 생성 ===\n'))
        
        # 1. 취향 조합 로드
        self.stdout.write('[1] 취향 조합 분석 중...')
        taste_combinations = self._load_taste_combinations(csv_path)
        self.stdout.write(f'  - 총 {len(taste_combinations)}개 취향 조합\n')
        
        # 2. 취향 조합을 유사한 그룹으로 클러스터링
        self.stdout.write(f'[2] 취향 조합을 {target_groups}개 그룹으로 클러스터링...')
        groups = self._cluster_taste_combinations(taste_combinations, target_groups)
        self.stdout.write(f'  - {len(groups)}개 그룹 생성\n')
        
        # 3. 각 그룹별 Scoring Logic 생성
        self.stdout.write('[3] 각 그룹별 Scoring Logic 생성 중...')
        scoring_logics = []
        
        for group_id, group_combinations in enumerate(groups, 1):
            if group_id % 50 == 0:
                self.stdout.write(f'  진행 중... {group_id}/{len(groups)}')
            
            # 그룹의 대표 취향 추출
            representative = self._get_representative_taste(group_combinations)
            
            # Scoring Logic 생성
            scoring_logic = self._generate_scoring_logic(group_id, representative, group_combinations)
            scoring_logics.append(scoring_logic)
        
        # 4. Scoring Logic 저장
        self.stdout.write(f'\n[4] Scoring Logic 저장 중...')
        os.makedirs(output_dir, exist_ok=True)
        
        # JSON 파일로 저장
        logic_file = Path(output_dir) / 'taste_scoring_logics.json'
        with open(logic_file, 'w', encoding='utf-8') as f:
            json.dump(scoring_logics, f, ensure_ascii=False, indent=2)
        
        # 설명 문서 생성
        doc_file = Path(output_dir) / 'scoring_logic_explanation.md'
        self._generate_explanation_doc(scoring_logics, doc_file)
        
        # 그룹별 통계
        self._print_group_statistics(groups, scoring_logics)
        
        self.stdout.write(self.style.SUCCESS(f'\n[OK] 완료! {len(scoring_logics)}개 Scoring Logic 생성'))
        self.stdout.write(f'[FILE] Logic 파일: {logic_file}')
        self.stdout.write(f'[FILE] 설명 문서: {doc_file}')

    def _load_taste_combinations(self, csv_path):
        """취향 조합 CSV 로드"""
        combinations = []
        with open(csv_path, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            for row in reader:
                combinations.append({
                    'taste_id': int(row['taste_id']),
                    'vibe': row['인테리어_스타일'],
                    'mate': row['메이트_구성'],
                    'priority': row['우선순위'],
                    'budget': row['예산_범위'],
                    'lineup': row['선호_라인업'],
                })
        return combinations

    def _cluster_taste_combinations(self, combinations, target_groups):
        """취향 조합을 유사한 그룹으로 클러스터링"""
        # 취향 요소별 인코딩
        encoded_combinations = []
        for combo in combinations:
            # 각 취향 요소를 숫자로 인코딩
            vibe_code = self._encode_vibe(combo['vibe'])
            mate_code = self._encode_mate(combo['mate'])
            priority_code = self._encode_priority(combo['priority'])
            budget_code = self._encode_budget(combo['budget'])
            lineup_code = self._encode_lineup(combo['lineup'])
            
            encoded_combinations.append({
                'combo': combo,
                'encoding': (vibe_code, mate_code, priority_code, budget_code, lineup_code),
            })
        
        # 간단한 해시 기반 클러스터링
        # 유사한 취향 조합끼리 묶기
        groups = defaultdict(list)
        
        for item in encoded_combinations:
            # 취향 조합의 해시값으로 그룹 결정
            combo = item['combo']
            group_key = self._get_group_key(combo, target_groups)
            groups[group_key].append(combo)
        
        # 그룹 크기 조정 (너무 작은 그룹은 병합)
        final_groups = self._adjust_group_sizes(list(groups.values()), target_groups)
        
        return final_groups

    def _encode_vibe(self, vibe):
        """인테리어 스타일 인코딩"""
        if '모던' in vibe or '미니멀' in vibe:
            return 0
        elif '코지' in vibe or '네이처' in vibe:
            return 1
        elif '럭셔리' in vibe or '아티스틱' in vibe:
            return 2
        elif '유니크' in vibe or '팝' in vibe:
            return 3
        return 0

    def _encode_mate(self, mate):
        """메이트 구성 인코딩"""
        if '1인' in mate or '혼자' in mate:
            return 0
        elif '2인' in mate or '신혼' in mate:
            return 1
        elif '3~4인' in mate or '가족' in mate:
            return 2
        return 1

    def _encode_priority(self, priority):
        """우선순위 인코딩"""
        if '디자인' in priority:
            return 0
        elif 'AI' in priority or '스마트' in priority:
            return 1
        elif '에너지' in priority or '효율' in priority:
            return 2
        elif '가격' in priority or '가성비' in priority:
            return 3
        return 0

    def _encode_budget(self, budget):
        """예산 인코딩"""
        if '500만원 미만' in budget or '실속형' in budget:
            return 0
        elif '500만원 ~ 1,500만원' in budget or '표준형' in budget:
            return 1
        elif '1,500만원 ~ 3,000만원' in budget or '고급형' in budget:
            return 2
        elif '3,000만원 이상' in budget or '하이엔드' in budget:
            return 3
        return 1

    def _encode_lineup(self, lineup):
        """라인업 인코딩"""
        return self._encode_budget(lineup)  # 예산과 동일한 인코딩

    def _get_group_key(self, combo, target_groups):
        """그룹 키 생성"""
        # 취향 조합의 해시값으로 그룹 결정
        combo_str = f"{combo['vibe']}_{combo['mate']}_{combo['priority']}_{combo['budget']}_{combo['lineup']}"
        combo_hash = int(hashlib.md5(combo_str.encode()).hexdigest(), 16)
        return combo_hash % target_groups

    def _adjust_group_sizes(self, groups, target_groups):
        """그룹 크기 조정"""
        # 너무 작은 그룹은 병합
        min_group_size = 1
        final_groups = []
        
        for group in groups:
            if len(group) >= min_group_size:
                final_groups.append(group)
            else:
                # 작은 그룹은 가장 유사한 그룹에 병합
                if final_groups:
                    final_groups[-1].extend(group)
                else:
                    final_groups.append(group)
        
        return final_groups

    def _get_representative_taste(self, group_combinations):
        """그룹의 대표 취향 추출"""
        # 가장 빈도가 높은 취향 요소 선택
        vibes = [c['vibe'] for c in group_combinations]
        mates = [c['mate'] for c in group_combinations]
        priorities = [c['priority'] for c in group_combinations]
        budgets = [c['budget'] for c in group_combinations]
        lineups = [c['lineup'] for c in group_combinations]
        
        from collections import Counter
        return {
            'vibe': Counter(vibes).most_common(1)[0][0],
            'mate': Counter(mates).most_common(1)[0][0],
            'priority': Counter(priorities).most_common(1)[0][0],
            'budget': Counter(budgets).most_common(1)[0][0],
            'lineup': Counter(lineups).most_common(1)[0][0],
            'group_size': len(group_combinations),
        }

    def _generate_scoring_logic(self, group_id, representative, group_combinations):
        """Scoring Logic 생성"""
        vibe = representative['vibe']
        mate = representative['mate']
        priority = representative['priority']
        budget = representative['budget']
        lineup = representative['lineup']
        
        # 취향 요소 분석
        vibe_key = self._extract_vibe_key(vibe)
        mate_type = self._extract_mate_type(mate)
        priority_type = self._extract_priority_type(priority)
        budget_level = self._extract_budget_level(budget)
        
        # Scoring Logic 생성
        logic = {
            'logic_id': group_id,
            'logic_name': f"Scoring_Logic_{group_id:03d}",
            'representative_taste': representative,
            'applies_to_taste_ids': [c['taste_id'] for c in group_combinations],
            'taste_count': len(group_combinations),
            
            # 가중치 설정
            'weights': self._generate_weights(vibe_key, priority_type, mate_type, budget_level),
            
            # 필터링 규칙
            'filters': self._generate_filters(vibe_key, mate_type, priority_type, budget_level),
            
            # 보너스/페널티 규칙
            'bonuses': self._generate_bonuses(vibe_key, mate_type, priority_type),
            'penalties': self._generate_penalties(vibe_key, mate_type, priority_type),
            
            # 설명
            'explanation': self._generate_explanation(group_id, vibe, mate, priority, budget, lineup),
            
            # 도출 근거
            'rationale': self._generate_rationale(vibe_key, mate_type, priority_type, budget_level),
        }
        
        return logic

    def _extract_vibe_key(self, vibe):
        """인테리어 스타일 키 추출"""
        if '모던' in vibe or '미니멀' in vibe:
            return 'modern'
        elif '코지' in vibe or '네이처' in vibe:
            return 'cozy'
        elif '럭셔리' in vibe or '아티스틱' in vibe:
            return 'luxury'
        elif '유니크' in vibe or '팝' in vibe:
            return 'pop'
        return 'modern'

    def _extract_mate_type(self, mate):
        """메이트 타입 추출"""
        if '1인' in mate or '혼자' in mate:
            return 'single'
        elif '2인' in mate or '신혼' in mate:
            return 'couple'
        elif '3~4인' in mate or '가족' in mate:
            return 'family'
        return 'couple'

    def _extract_priority_type(self, priority):
        """우선순위 타입 추출"""
        if '디자인' in priority:
            return 'design'
        elif 'AI' in priority or '스마트' in priority:
            return 'tech'
        elif '에너지' in priority or '효율' in priority:
            return 'eco'
        elif '가격' in priority or '가성비' in priority:
            return 'value'
        return 'value'

    def _extract_budget_level(self, budget):
        """예산 레벨 추출"""
        if '500만원 미만' in budget or '실속형' in budget:
            return 'low'
        elif '500만원 ~ 1,500만원' in budget or '표준형' in budget:
            return 'medium'
        elif '1,500만원 ~ 3,000만원' in budget or '고급형' in budget:
            return 'high'
        elif '3,000만원 이상' in budget or '하이엔드' in budget:
            return 'premium'
        return 'medium'

    def _generate_weights(self, vibe_key, priority_type, mate_type, budget_level):
        """가중치 생성"""
        # 기본 가중치
        base_weights = {
            'TV': {
                'resolution': 0.25,
                'brightness': 0.15,
                'refresh_rate': 0.15,
                'panel_type': 0.10,
                'power_consumption': 0.10,
                'size': 0.10,
                'price_match': 0.15,
            },
            'KITCHEN': {
                'capacity': 0.25,
                'energy_efficiency': 0.20,
                'features': 0.15,
                'size': 0.10,
                'price_match': 0.20,
                'design': 0.10,
            },
            'LIVING': {
                'audio_quality': 0.25,
                'connectivity': 0.15,
                'power_consumption': 0.10,
                'size': 0.10,
                'price_match': 0.20,
                'features': 0.20,
            },
        }
        
        # 우선순위별 가중치 조정
        adjusted_weights = {}
        for category, weights in base_weights.items():
            adjusted = weights.copy()
            
            if priority_type == 'design':
                adjusted['design'] = adjusted.get('design', 0.1) * 1.5
                adjusted['panel_type'] = adjusted.get('panel_type', 0.1) * 1.3
            elif priority_type == 'tech':
                adjusted['resolution'] = adjusted.get('resolution', 0.25) * 1.5
                adjusted['refresh_rate'] = adjusted.get('refresh_rate', 0.15) * 1.4
                adjusted['features'] = adjusted.get('features', 0.15) * 1.2
            elif priority_type == 'eco':
                adjusted['power_consumption'] = adjusted.get('power_consumption', 0.1) * 1.5
                adjusted['energy_efficiency'] = adjusted.get('energy_efficiency', 0.2) * 1.5
            elif priority_type == 'value':
                adjusted['price_match'] = adjusted.get('price_match', 0.15) * 1.5
            
            # 정규화
            total = sum(adjusted.values())
            adjusted = {k: v/total for k, v in adjusted.items()}
            adjusted_weights[category] = adjusted
        
        return adjusted_weights

    def _generate_filters(self, vibe_key, mate_type, priority_type, budget_level):
        """필터링 규칙 생성"""
        filters = {
            'must_have': [],
            'should_have': [],
            'exclude': [],
        }
        
        # 인테리어 스타일 필터
        if vibe_key == 'luxury':
            filters['should_have'].append('SIGNATURE 또는 시그니처 라인업')
        elif vibe_key in ['modern', 'cozy', 'pop']:
            filters['should_have'].append('OBJET 또는 오브제 라인업')
        
        # 메이트 타입 필터
        if mate_type == 'single':
            filters['exclude'].append('대용량 제품 (800L 이상 냉장고, 대형 세탁기 등)')
        elif mate_type == 'family':
            filters['exclude'].append('소형 제품 (300L 이하 냉장고, 미니 세탁기 등)')
        
        # 우선순위 필터
        if priority_type == 'tech':
            filters['should_have'].append('AI 또는 스마트 기능')
        elif priority_type == 'eco':
            filters['should_have'].append('에너지 1등급 또는 인버터 기술')
        
        # 예산 필터
        if budget_level == 'low':
            filters['exclude'].append('프리미엄 라인업 (시그니처 등)')
        elif budget_level == 'premium':
            filters['should_have'].append('프리미엄 라인업 또는 하이엔드 제품')
        
        return filters

    def _generate_bonuses(self, vibe_key, mate_type, priority_type):
        """보너스 규칙 생성"""
        bonuses = []
        
        if priority_type == 'design':
            bonuses.append({
                'condition': 'OBJET 또는 SIGNATURE 라인업',
                'bonus': 0.15,
                'reason': '디자인 우선순위에 맞는 프리미엄 디자인 라인업'
            })
        
        if mate_type == 'single':
            bonuses.append({
                'condition': '소형 또는 컴팩트 제품',
                'bonus': 0.10,
                'reason': '1인 가구에 적합한 크기'
            })
        elif mate_type == 'family':
            bonuses.append({
                'condition': '대용량 제품 (800L 이상)',
                'bonus': 0.10,
                'reason': '가족 구성에 적합한 용량'
            })
        
        if priority_type == 'tech':
            bonuses.append({
                'condition': 'AI 또는 스마트 기능 포함',
                'bonus': 0.12,
                'reason': '기술 우선순위에 부합'
            })
        
        return bonuses

    def _generate_penalties(self, vibe_key, mate_type, priority_type):
        """페널티 규칙 생성"""
        penalties = []
        
        if mate_type == 'single':
            penalties.append({
                'condition': '대용량 제품 (800L 이상)',
                'penalty': -0.20,
                'reason': '1인 가구에 부적합한 크기'
            })
        elif mate_type == 'family':
            penalties.append({
                'condition': '소형 제품 (300L 이하)',
                'penalty': -0.20,
                'reason': '가족 구성에 부적합한 용량'
            })
        
        if priority_type == 'design':
            penalties.append({
                'condition': '기본형 또는 실용형 디자인',
                'penalty': -0.10,
                'reason': '디자인 우선순위에 부합하지 않음'
            })
        
        return penalties

    def _generate_explanation(self, logic_id, vibe, mate, priority, budget, lineup):
        """Scoring Logic 설명 생성"""
        return f"""
이 Scoring Logic은 다음 취향 조합을 대표합니다:
- 인테리어 스타일: {vibe}
- 메이트 구성: {mate}
- 우선순위: {priority}
- 예산 범위: {budget}
- 선호 라인업: {lineup}

이 취향 조합의 특성을 반영하여 제품 추천 점수를 계산합니다.
"""

    def _generate_rationale(self, vibe_key, mate_type, priority_type, budget_level):
        """도출 근거 생성"""
        rationale = {
            'vibe_impact': self._get_vibe_rationale(vibe_key),
            'mate_impact': self._get_mate_rationale(mate_type),
            'priority_impact': self._get_priority_rationale(priority_type),
            'budget_impact': self._get_budget_rationale(budget_level),
        }
        return rationale

    def _get_vibe_rationale(self, vibe_key):
        """인테리어 스타일 근거"""
        rationale_map = {
            'modern': '모던 & 미니멀 스타일은 깔끔하고 세련된 디자인을 선호하므로, OBJET 라인업에 가중치를 부여합니다.',
            'cozy': '코지 & 네이처 스타일은 따뜻하고 자연스러운 디자인을 선호하므로, OBJET 라인업에 가중치를 부여합니다.',
            'luxury': '럭셔리 & 아티스틱 스타일은 고급스러운 디자인을 선호하므로, SIGNATURE 라인업에 가중치를 부여합니다.',
            'pop': '유니크 & 팝 스타일은 개성 있는 디자인을 선호하므로, OBJET 라인업에 가중치를 부여합니다.',
        }
        return rationale_map.get(vibe_key, rationale_map['modern'])

    def _get_mate_rationale(self, mate_type):
        """메이트 구성 근거"""
        rationale_map = {
            'single': '1인 가구는 작은 용량의 제품이 적합하므로, 소형 제품에 보너스를 부여하고 대용량 제품에 페널티를 적용합니다.',
            'couple': '2인 가구는 중간 용량의 제품이 적합하므로, 표준형 제품에 가중치를 부여합니다.',
            'family': '가족 구성은 큰 용량의 제품이 적합하므로, 대용량 제품에 보너스를 부여하고 소형 제품에 페널티를 적용합니다.',
        }
        return rationale_map.get(mate_type, rationale_map['couple'])

    def _get_priority_rationale(self, priority_type):
        """우선순위 근거"""
        rationale_map = {
            'design': '디자인 우선순위는 시각적 완성도를 중시하므로, 디자인 관련 속성(패널 타입, 디자인 라인업)에 높은 가중치를 부여합니다.',
            'tech': 'AI/스마트 기능 우선순위는 첨단 기술을 중시하므로, 기술 관련 속성(해상도, 주사율, AI 기능)에 높은 가중치를 부여합니다.',
            'eco': '에너지 효율 우선순위는 환경 친화성을 중시하므로, 에너지 관련 속성(전력소비, 에너지 등급)에 높은 가중치를 부여합니다.',
            'value': '가성비 우선순위는 가격 대비 성능을 중시하므로, 가격 적합도에 높은 가중치를 부여합니다.',
        }
        return rationale_map.get(priority_type, rationale_map['value'])

    def _get_budget_rationale(self, budget_level):
        """예산 근거"""
        rationale_map = {
            'low': '실속형 예산은 가격이 낮은 제품을 선호하므로, 가격 필터링과 가격 적합도에 높은 가중치를 부여합니다.',
            'medium': '표준형 예산은 균형 잡힌 선택을 선호하므로, 모든 속성에 균등한 가중치를 부여합니다.',
            'high': '고급형 예산은 품질을 중시하므로, 기능성과 디자인에 높은 가중치를 부여합니다.',
            'premium': '하이엔드 예산은 최고 품질을 선호하므로, 프리미엄 라인업과 최고 사양에 높은 가중치를 부여합니다.',
        }
        return rationale_map.get(budget_level, rationale_map['medium'])

    def _generate_explanation_doc(self, scoring_logics, doc_file):
        """설명 문서 생성"""
        with open(doc_file, 'w', encoding='utf-8') as f:
            f.write("# 취향별 Scoring Logic 설명서\n\n")
            f.write(f"총 {len(scoring_logics)}개의 독립적인 Scoring Logic이 생성되었습니다.\n\n")
            f.write("## 목차\n\n")
            f.write("1. [개요](#개요)\n")
            f.write("2. [Logic 구조](#logic-구조)\n")
            f.write("3. [각 Logic별 상세 설명](#각-logic별-상세-설명)\n\n")
            
            f.write("## 개요\n\n")
            f.write("768개의 취향 조합을 유사한 그룹으로 묶어 ")
            f.write(f"{len(scoring_logics)}개의 독립적인 Scoring Logic을 생성했습니다.\n\n")
            f.write("각 Logic은 해당 취향 그룹의 특성을 반영하여 제품 추천 점수를 계산합니다.\n\n")
            
            f.write("## Logic 구조\n\n")
            f.write("각 Scoring Logic은 다음 요소로 구성됩니다:\n\n")
            f.write("- **weights**: 카테고리별 속성 가중치\n")
            f.write("- **filters**: 필터링 규칙 (must_have, should_have, exclude)\n")
            f.write("- **bonuses**: 보너스 점수 규칙\n")
            f.write("- **penalties**: 페널티 점수 규칙\n")
            f.write("- **explanation**: Logic 설명\n")
            f.write("- **rationale**: 도출 근거\n\n")
            
            f.write("## 각 Logic별 상세 설명\n\n")
            for logic in scoring_logics[:50]:  # 처음 50개만 상세 설명
                f.write(f"### {logic['logic_name']}\n\n")
                f.write(f"**적용 취향 ID**: {', '.join(map(str, logic['applies_to_taste_ids'][:10]))}")
                if len(logic['applies_to_taste_ids']) > 10:
                    f.write(f" 외 {len(logic['applies_to_taste_ids'])-10}개")
                f.write("\n\n")
                f.write(f"**대표 취향**:\n")
                f.write(f"- 인테리어: {logic['representative_taste']['vibe']}\n")
                f.write(f"- 메이트: {logic['representative_taste']['mate']}\n")
                f.write(f"- 우선순위: {logic['representative_taste']['priority']}\n")
                f.write(f"- 예산: {logic['representative_taste']['budget']}\n\n")
                f.write(f"**도출 근거**:\n")
                for key, value in logic['rationale'].items():
                    f.write(f"- {key}: {value}\n")
                f.write("\n")

    def _print_group_statistics(self, groups, scoring_logics):
        """그룹별 통계 출력"""
        self.stdout.write('\n[그룹 통계]')
        group_sizes = [len(g) for g in groups]
        self.stdout.write(f'  - 평균 그룹 크기: {sum(group_sizes)/len(group_sizes):.1f}개')
        self.stdout.write(f'  - 최소 그룹 크기: {min(group_sizes)}개')
        self.stdout.write(f'  - 최대 그룹 크기: {max(group_sizes)}개')
        
        # Logic별 적용 취향 수 분포
        taste_counts = [logic['taste_count'] for logic in scoring_logics]
        self.stdout.write(f'\n  - Logic별 평균 적용 취향 수: {sum(taste_counts)/len(taste_counts):.1f}개')

