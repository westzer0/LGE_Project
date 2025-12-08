"""
768개 취향 조합별 추천 문구 샘플 생성 (고품질 버전)

- 리뷰 데이터 289,755개 활용
- 평균벡터(추천이유) 파일 활용
- 취향별 세분화된 고품질 문구 생성

사용법:
    python manage.py generate_taste_recommendations
"""
import csv
import os
import json
import re
import hashlib
from collections import defaultdict, Counter
from itertools import product
from pathlib import Path
from django.core.management.base import BaseCommand
from api.models import Product, ProductReview, ProductRecommendReason
from django.db.models import Count, Avg


class Command(BaseCommand):
    help = '768개 취향 조합별 고품질 추천 문구 샘플을 생성합니다'

    def add_arguments(self, parser):
        parser.add_argument(
            '--output',
            type=str,
            default='data/온보딩/taste_recommendations_768.csv',
            help='출력 CSV 파일 경로',
        )
        parser.add_argument(
            '--limit',
            type=int,
            default=0,
            help='제한할 조합 수 (0=전체 768개)',
        )
        parser.add_argument(
            '--no-backup',
            action='store_true',
            help='기존 파일을 백업하지 않고 덮어쓰기',
        )
        parser.add_argument(
            '--new-file',
            action='store_true',
            help='기존 파일을 덮어쓰지 않고 타임스탬프가 붙은 새 파일 생성',
        )

    def handle(self, *args, **options):
        output_path = options['output']
        limit = options['limit']
        no_backup = options.get('no_backup', False)
        new_file = options.get('new_file', False)
        
        self.stdout.write(self.style.SUCCESS('\n=== 고품질 취향별 추천 문구 생성 ===\n'))
        
        # 1. 데이터 로드
        self.stdout.write('[1] 데이터 로드 중...')
        taste_combinations = self._generate_taste_combinations(limit)
        products_with_reviews = self._get_products_with_reviews()
        recommend_reasons = self._load_recommend_reasons()
        
        self.stdout.write(f'  - 취향 조합: {len(taste_combinations)}개')
        self.stdout.write(f'  - 리뷰가 있는 제품: {len(products_with_reviews)}개')
        self.stdout.write(f'  - 추천이유 데이터: {len(recommend_reasons)}개\n')
        
        # 2. 각 취향 조합별로 추천 문구 생성 (중복 방지)
        self.stdout.write('[2] 추천 문구 생성 중...')
        recommendations = []
        
        # 중복 방지를 위한 추적
        generated_review_texts = set()
        generated_ai_texts = set()
        
        # 진행 상황 로그 파일 경로
        progress_log_path = str(Path(output_path).parent / 'taste_generation_progress.log')
        
        for i, combo in enumerate(taste_combinations, 1):
            # 진행 상황 로그 기록
            progress = (i / len(taste_combinations)) * 100
            with open(progress_log_path, 'w', encoding='utf-8') as log_file:
                log_file.write(f"진행 중: {i}/{len(taste_combinations)} ({progress:.1f}%)\n")
                log_file.write(f"현재 처리 중: {combo['vibe']} | {combo['mate']} | {combo['priority']}\n")
                log_file.write(f"고유 리뷰 문구: {len(generated_review_texts)}개\n")
                log_file.write(f"고유 AI 문구: {len(generated_ai_texts)}개\n")
            
            if i % 50 == 0:
                self.stdout.write(f'  진행 중... {i}/{len(taste_combinations)} ({progress:.1f}%)')
                self.stdout.write(f'  고유 리뷰 문구: {len(generated_review_texts)}개, 고유 AI 문구: {len(generated_ai_texts)}개')
            
            # 리뷰 기반 문구 생성 (중복 방지)
            max_retries = 5
            review_based_text = None
            for retry in range(max_retries):
                text = self._generate_review_based_recommendation(
                    combo, products_with_reviews, recommend_reasons, retry
                )
                # 중복 체크 (정규화된 텍스트로 비교)
                normalized = self._normalize_text(text)
                if normalized not in generated_review_texts:
                    generated_review_texts.add(normalized)
                    review_based_text = text
                    break
            
            if not review_based_text:
                # 최대 재시도 후에도 중복이면 기본 문구 사용
                review_based_text = self._generate_fallback_recommendation(combo)
                generated_review_texts.add(self._normalize_text(review_based_text))
            
            # AI 기반 문구 생성 (중복 방지)
            ai_based_text = None
            for retry in range(max_retries):
                text = self._generate_ai_based_recommendation(combo, recommend_reasons, retry)
                # 중복 체크
                normalized = self._normalize_text(text)
                if normalized not in generated_ai_texts:
                    generated_ai_texts.add(normalized)
                    ai_based_text = text
                    break
            
            if not ai_based_text:
                # 최대 재시도 후에도 중복이면 기본 문구 사용
                ai_based_text = self._generate_fallback_recommendation(combo)
                generated_ai_texts.add(self._normalize_text(ai_based_text))
            
            recommendations.append({
                'taste_id': i,
                '인테리어_스타일': combo['vibe'],
                '메이트_구성': combo['mate'],
                '우선순위': combo['priority'],
                '예산_범위': combo['budget'],
                '선호_라인업': combo['lineup'],
                '리뷰_기반_추천문구': review_based_text,
                'AI_기반_추천문구': ai_based_text,
            })
        
        # 3. CSV 저장
        self._save_to_csv(recommendations, output_path, no_backup=no_backup, new_file=new_file)
        
        # 완료 로그 기록
        progress_log_path = str(Path(output_path).parent / 'taste_generation_progress.log')
        with open(progress_log_path, 'w', encoding='utf-8') as log_file:
            log_file.write(f"완료: {len(recommendations)}/{len(recommendations)} (100.0%)\n")
            log_file.write("상태: 완료\n")
        
        self.stdout.write(self.style.SUCCESS(f'\n[OK] 완료! {len(recommendations)}개 추천 문구 생성'))
        self.stdout.write(f'[FILE] 저장 위치: {output_path}')

    def _generate_taste_combinations(self, limit):
        """768개 취향 조합 생성"""
        vibes = [
            '모던 & 미니멀 (Modern & Minimal)',
            '코지 & 네이처 (Cozy & Nature)',
            '럭셔리 & 아티스틱 (Luxury & Artistic)',
            '유니크 & 팝 (Unique & Pop)',
        ]
        
        mates = [
            '나 혼자 산다 (1인 가구)',
            '우리 둘이 알콩달콩 (2인/신혼)',
            '함께 사는 3~4인 가족',
        ]
        
        priorities = [
            '인테리어를 완성하는 디자인',
            '삶을 편하게 해주는 AI/스마트 기능',
            '지구를 지키는 에너지 효율',
            '가성비를 추구하는 가격',
        ]
        
        budgets = [
            '500만원 미만 (실속형)',
            '500만원 ~ 1,500만원 (표준형)',
            '1,500만원 ~ 3,000만원 (고급형)',
            '3,000만원 이상 (하이엔드)',
        ]
        
        lineups = [
            '500만원 미만 (실속형)',
            '500만원 ~ 1,500만원 (표준형)',
            '1,500만원 ~ 3,000만원 (고급형)',
            '3,000만원 이상 (하이엔드)',
        ]
        
        combinations = []
        for vibe, mate, priority, budget, lineup in product(vibes, mates, priorities, budgets, lineups):
            combinations.append({
                'vibe': vibe,
                'mate': mate,
                'priority': priority,
                'budget': budget,
                'lineup': lineup,
            })
        
        if limit > 0:
            combinations = combinations[:limit]
        
        return combinations

    def _get_products_with_reviews(self):
        """리뷰 데이터가 있는 제품 조회"""
        products = Product.objects.annotate(
            review_count=Count('reviews')
        ).filter(review_count__gt=0).select_related('spec')
        
        return list(products)

    def _load_recommend_reasons(self):
        """평균벡터(추천이유) 파일 로드"""
        recommend_reasons = {}
        base_dir = Path(__file__).parent.parent.parent.parent / 'data' / '리뷰_평균벡터'
        
        if not base_dir.exists():
            return recommend_reasons
        
        # CSV 파일들 읽기
        for csv_file in base_dir.glob('*.csv'):
            try:
                with open(csv_file, 'r', encoding='utf-8-sig') as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        model_name = row.get('model_name', '').strip()
                        reason = row.get('recommend_reason', '').strip()
                        if model_name and reason:
                            recommend_reasons[model_name] = reason
            except Exception as e:
                self.stdout.write(self.style.WARNING(f'  경고: {csv_file.name} 읽기 실패: {e}'))
        
        return recommend_reasons

    def _normalize_text(self, text):
        """텍스트 정규화 (중복 체크용)"""
        # 공백 제거, 소문자 변환 등으로 정규화
        normalized = re.sub(r'\s+', ' ', text.strip().lower())
        return normalized
    
    def _generate_review_based_recommendation(self, combo, products_with_reviews, recommend_reasons, retry=0):
        """리뷰 데이터 기반 고품질 추천 문구 생성 (중복 방지)"""
        # 취향에 맞는 제품 필터링 및 점수 계산
        scored_products = self._filter_and_score_products(combo, products_with_reviews)
        
        if not scored_products:
            return self._generate_fallback_recommendation(combo)
        
        # 상위 제품 선택 (취향 조합별로 다르게)
        top_products = self._select_diverse_products(scored_products, combo, limit=3)
        
        # 리뷰 데이터에서 특징 추출
        product_features = []
        product_names = []
        
        for product, score in top_products:
            # 리뷰에서 특징 추출
            features = self._extract_product_features(product, combo)
            if features:
                product_features.append(features)
                product_names.append(product.name)
        
        # 추천이유 데이터 활용
        recommend_texts = []
        for product, _ in top_products:
            if product.model_number and product.model_number in recommend_reasons:
                reason = recommend_reasons[product.model_number]
                # 추천이유에서 핵심 문장 추출
                key_sentences = self._extract_key_sentences(reason, combo)
                if key_sentences:
                    recommend_texts.extend(key_sentences[:2])
        
        # 문구 생성 (고유성 강화)
        vibe_name = combo['vibe'].split('(')[0].strip()
        mate_desc = self._get_mate_description(combo['mate'])
        priority_desc = combo['priority']
        budget_desc = combo['budget']
        lineup_desc = combo['lineup']
        
        # 취향 조합별 고유 키 생성 (retry를 포함하여 재시도 시 다른 문구 생성)
        combo_key = f"{combo['vibe']}_{combo['mate']}_{combo['priority']}_{combo['budget']}_{combo['lineup']}_{retry}"
        combo_hash = int(hashlib.md5(combo_key.encode()).hexdigest(), 16)
        
        # 다양한 인트로 템플릿
        intro_templates = [
            f"{mate_desc} {vibe_name} 무드를 완성하는 스타일",
            f"{vibe_name} 감성으로 채우는 {mate_desc} 공간",
            f"{mate_desc} 라이프스타일에 맞는 {vibe_name} 인테리어",
            f"{vibe_name} 스타일의 {mate_desc} 홈",
            f"{mate_desc}만의 {vibe_name} 무드",
        ]
        intro = intro_templates[combo_hash % len(intro_templates)]
        
        # 다양한 바디 템플릿
        body_templates = [
            f"당신의 {priority_desc}를 반영해",
            f"{priority_desc}을 최우선으로 고려해",
            f"{priority_desc}을 중시하는 당신을 위해",
            f"당신의 {priority_desc} 니즈를 충족시키기 위해",
            f"{priority_desc}에 최적화해",
        ]
        body = body_templates[(combo_hash // 10) % len(body_templates)]
        
        text = f"{intro}\n\n{body}\n\n"
        
        # 제품 소개 (다양한 표현)
        if product_names:
            product_list = ', '.join(product_names[:2])
            product_intro_templates = [
                f"{product_list} 중심으로 구성했어요.",
                f"{product_list}를 엄선해 추천드려요.",
                f"{product_list} 조합을 제안합니다.",
                f"{product_list}로 구성한 패키지입니다.",
                f"{product_list}를 골라봤어요.",
            ]
            product_intro = product_intro_templates[(combo_hash // 100) % len(product_intro_templates)]
            text += f"{product_intro}\n\n"
        
        # 특징 문구 추가 (취향별로 다르게)
        if product_features:
            feature_text = self._format_features_unique(product_features, priority_desc, combo_hash)
            text += f"{feature_text}\n\n"
        
        # 추천이유 문구 추가 (다양한 표현)
        if recommend_texts:
            reason_templates = [
                f"{' '.join(recommend_texts[:2])}",
                f"실제 사용자들이 {' '.join(recommend_texts[:1])}라고 평가했어요.",
                f"리뷰에서 {' '.join(recommend_texts[:1])}라는 피드백이 많았습니다.",
            ]
            reason_text = reason_templates[(combo_hash // 50) % len(reason_templates)]
            text += f"{reason_text}\n\n"
        
        # 클로징 (다양한 표현 - 더 확장)
        closing_templates = [
            f"{budget_desc} 예산 안에서 {priority_desc}와 기능성을 모두 담았어요.",
            f"{budget_desc} 범위에서 최적의 가성비를 찾았어요.",
            f"{budget_desc} 예산으로 {priority_desc}를 만족시켜드려요.",
            f"{budget_desc} 안에서 {priority_desc}와 실용성을 모두 고려했어요.",
            f"{budget_desc} 예산으로 완벽한 조합을 제안합니다.",
            f"{budget_desc} 범위에서 {priority_desc}를 최대화했어요.",
            f"{budget_desc} 예산으로 최고의 선택을 제안드립니다.",
            f"{budget_desc} 안에서 {priority_desc}와 디자인의 균형을 맞췄어요.",
            f"{budget_desc} 예산으로 {priority_desc}를 충족하는 솔루션입니다.",
            f"{budget_desc} 범위에서 실용성과 {priority_desc}를 모두 고려했습니다.",
        ]
        closing = closing_templates[(combo_hash // 1000) % len(closing_templates)]
        text += closing
        
        # 추가 고유성 부여: 취향 조합별 추가 문구
        unique_addition = self._get_unique_addition_for_review(combo, combo_hash)
        if unique_addition:
            text += f"\n\n{unique_addition}"
        
        return text
    
    def _get_unique_addition_for_review(self, combo, combo_hash):
        """리뷰 기반 문구에 추가할 고유 문구"""
        # 40% 확률로 추가 문구 삽입
        if combo_hash % 10 < 4:
            mate = combo['mate']
            priority = combo['priority']
            budget = combo['budget']
            
            additions = []
            
            if '1인' in mate or '혼자' in mate:
                additions.extend([
                    "혼자만의 공간을 더욱 특별하게 만들어드려요.",
                    "1인 가구에 최적화된 구성입니다.",
                    "혼자 사는 공간을 완벽하게 채워드립니다.",
                    "1인 생활에 맞춘 실용적인 선택입니다.",
                ])
            elif '2인' in mate or '신혼' in mate:
                additions.extend([
                    "둘만의 특별한 공간을 완성해드려요.",
                    "신혼부부를 위한 로맨틱한 구성입니다.",
                    "둘만의 추억을 쌓을 수 있는 공간을 제안합니다.",
                    "신혼 생활을 더욱 편리하게 만들어드려요.",
                ])
            else:
                additions.extend([
                    "가족 모두가 만족할 수 있는 구성입니다.",
                    "가족의 일상을 더욱 편리하게 만들어드려요.",
                    "가족과 함께하는 따뜻한 공간을 완성합니다.",
                    "가족 구성원 모두를 고려한 선택입니다.",
                ])
            
            # 예산별 추가 문구
            if '실속형' in budget:
                additions.append("실속 있는 선택으로 만족도를 높였어요.")
            elif '하이엔드' in budget:
                additions.append("프리미엄 품질을 경험할 수 있어요.")
            
            return additions[combo_hash % len(additions)]
        return None
    
    def _format_features_unique(self, product_features, priority_desc, combo_hash):
        """특징 문구 포맷팅 (고유성 강화)"""
        if not product_features:
            return ""
        
        all_keywords = []
        for features in product_features:
            if features and 'keywords' in features:
                all_keywords.extend(features['keywords'])
        
        if all_keywords:
            unique_keywords = list(set(all_keywords))[:5]
            keyword_list = ', '.join(unique_keywords)
            
            feature_templates = [
                f"리뷰에서 자주 언급되는 {keyword_list} 등의 특징이 돋보여요.",
                f"실제 사용자들이 {keyword_list} 등을 강점으로 꼽았어요.",
                f"{keyword_list} 등의 장점이 리뷰에서 자주 나타나요.",
                f"사용자들이 {keyword_list} 등을 높이 평가했어요.",
                f"리뷰에서 {keyword_list} 등의 긍정적 피드백이 많았어요.",
            ]
            return feature_templates[combo_hash % len(feature_templates)]
        
        return "실제 사용자들의 긍정적인 피드백이 많은 제품들이에요."

    def _generate_ai_based_recommendation(self, combo, recommend_reasons, retry=0):
        """AI 기반 고품질 추천 문구 생성 (고유성 강화, 중복 방지)"""
        vibe_name = combo['vibe'].split('(')[0].strip()
        vibe_key = combo['vibe'].split('(')[1].split(')')[0].strip() if '(' in combo['vibe'] else ''
        mate_desc = self._get_mate_description(combo['mate'])
        priority_desc = combo['priority']
        budget_desc = combo['budget']
        lineup_desc = combo['lineup']
        mate = combo['mate']
        
        design_lineup = self._get_design_lineup(vibe_key)
        recommended_categories = self._get_recommended_categories(combo)
        
        # 취향 조합의 모든 요소를 활용한 고유 키 생성 (retry 포함)
        combo_key = f"{vibe_key}_{priority_desc}_{budget_desc}_{lineup_desc}_{mate}_{retry}"
        combo_hash = int(hashlib.md5(combo_key.encode()).hexdigest(), 16)
        
        # 취향 조합별 고유한 문구 생성 (모든 요소 반영)
        text = self._generate_unique_text(combo, combo_hash, vibe_name, vibe_key, mate_desc, 
                                         priority_desc, budget_desc, lineup_desc, 
                                         design_lineup, recommended_categories, retry)
        
        return text
    
    def _generate_unique_text(self, combo, combo_hash, vibe_name, vibe_key, mate_desc,
                             priority_desc, budget_desc, lineup_desc, design_lineup, recommended_categories, retry=0):
        """취향 조합별 고유한 문구 생성 (중복 최소화)"""
        # 다양한 인트로 문구 (취향 조합별로 다르게)
        intro_templates = [
            f"{mate_desc} {vibe_name} 무드를 완성하는 {design_lineup} 스타일",
            f"{vibe_name} 감성으로 채우는 {mate_desc} 공간",
            f"{mate_desc} 라이프스타일에 맞는 {vibe_name} 인테리어",
            f"{vibe_name} 스타일의 {mate_desc} 홈을 위한",
            f"{mate_desc} {vibe_name} 무드를 완성하는",
            f"{vibe_name}로 꾸미는 {mate_desc} 공간",
            f"{mate_desc}만의 {vibe_name} 스타일",
            f"{vibe_name} 감성의 {mate_desc} 홈",
            f"{mate_desc} {vibe_name} 무드를 담은",
            f"{vibe_name}로 완성하는 {mate_desc} 공간",
            f"{mate_desc} {vibe_name} 스타일의",
            f"{vibe_name} 무드로 채우는 {mate_desc} 공간",
        ]
        
        # 다양한 바디 문구
        body_templates = [
            f"당신의 공간 분위기와 {priority_desc}를 반영해",
            f"{priority_desc}을 최우선으로 고려한",
            f"{priority_desc}을 중시하는 당신을 위해",
            f"당신의 {priority_desc} 니즈를 충족시키는",
            f"{priority_desc}에 최적화된",
            f"{priority_desc}을 최우선으로 한",
            f"당신의 {priority_desc}를 고려해",
            f"{priority_desc}을 중심으로",
            f"{priority_desc}에 맞춘",
            f"{priority_desc}을 반영한",
            f"{priority_desc}을 우선시하는",
            f"{priority_desc}에 특화된",
        ]
        
        # 다양한 제품 소개 문구
        product_templates = [
            f"{', '.join(recommended_categories)} 중심으로 구성했어요.",
            f"{', '.join(recommended_categories)} 조합을 제안드려요.",
            f"{', '.join(recommended_categories)}를 엄선했어요.",
            f"{', '.join(recommended_categories)} 패키지",
            f"{', '.join(recommended_categories)} 세트",
            f"{', '.join(recommended_categories)}로 구성했습니다.",
            f"{', '.join(recommended_categories)}를 추천드려요.",
            f"{', '.join(recommended_categories)} 중심의 조합",
            f"{', '.join(recommended_categories)}를 골라봤어요.",
            f"{', '.join(recommended_categories)}로 완성합니다.",
        ]
        
        # 다양한 클로징 문구
        closing_templates = [
            f"{budget_desc} 예산 안에서 {priority_desc}와 기능성을 모두 담았어요.",
            f"{budget_desc} 범위에서 최적의 가성비를 찾았어요.",
            f"{budget_desc} 예산으로 {design_lineup}의 품격을 경험하세요.",
            f"{budget_desc} 안에서 디자인과 기능의 균형을 맞췄어요.",
            f"{budget_desc} 예산으로 완벽한 조합을 제안합니다.",
            f"{budget_desc} 범위에서 {priority_desc}를 최대화했어요.",
            f"{budget_desc} 예산으로 최고의 선택을 제안드립니다.",
            f"{budget_desc} 안에서 {design_lineup}의 가치를 느껴보세요.",
            f"{budget_desc} 예산으로 {priority_desc}를 만족시켜드려요.",
            f"{budget_desc} 범위에서 최적의 솔루션을 제안합니다.",
        ]
        
        # 해시값과 retry를 이용해 각 조합별로 다른 템플릿 선택 (더 다양하게)
        intro_idx = (combo_hash + retry * 7) % len(intro_templates)
        body_idx = ((combo_hash // 10) + retry * 11) % len(body_templates)
        product_idx = ((combo_hash // 100) + retry * 13) % len(product_templates)
        closing_idx = ((combo_hash // 1000) + retry * 17) % len(closing_templates)
        
        # 추가 변형: 예산과 라인업이 다르면 추가 문구 삽입
        if budget_desc != lineup_desc:
            budget_variation = self._get_budget_variation(combo_hash, budget_desc, lineup_desc)
            text = f"{intro_templates[intro_idx]}\n\n"
            text += f"{body_templates[body_idx]}\n\n"
            text += f"{product_templates[product_idx]}\n"
            if budget_variation:
                text += f"{budget_variation}\n"
            text += f"{closing_templates[closing_idx]}"
        else:
            text = f"{intro_templates[intro_idx]}\n\n"
            text += f"{body_templates[body_idx]}\n\n"
            text += f"{product_templates[product_idx]}\n"
            text += f"{closing_templates[closing_idx]}"
        
        # 취향 조합별 추가 고유성 부여
        unique_suffix = self._get_unique_suffix(combo, combo_hash)
        if unique_suffix:
            text += f"\n\n{unique_suffix}"
        
        return text
    
    def _get_budget_variation(self, combo_hash, budget_desc, lineup_desc):
        """예산과 라인업이 다를 때 추가 변형 문구"""
        variations = [
            f"예산은 {budget_desc}이지만, 선호 라인업인 {lineup_desc} 제품도 고려했어요.",
            f"{budget_desc} 예산 안에서 {lineup_desc} 스타일을 반영했습니다.",
            f"예산 범위는 {budget_desc}이며, {lineup_desc} 제품을 우선 추천드려요.",
        ]
        return variations[combo_hash % len(variations)]
    
    def _get_unique_suffix(self, combo, combo_hash):
        """취향 조합별 고유한 추가 문구"""
        # 30% 확률로 추가 문구 삽입 (다양성 확보)
        if combo_hash % 10 < 3:
            mate = combo['mate']
            priority = combo['priority']
            
            if '1인' in mate or '혼자' in mate:
                suffixes = [
                    "혼자만의 공간을 더욱 특별하게 만들어드려요.",
                    "1인 가구에 최적화된 구성입니다.",
                    "혼자 사는 공간을 완벽하게 채워드립니다.",
                ]
            elif '2인' in mate or '신혼' in mate:
                suffixes = [
                    "둘만의 특별한 공간을 완성해드려요.",
                    "신혼부부를 위한 로맨틱한 구성입니다.",
                    "둘만의 추억을 쌓을 수 있는 공간을 제안합니다.",
                ]
            else:
                suffixes = [
                    "가족 모두가 만족할 수 있는 구성입니다.",
                    "가족의 일상을 더욱 편리하게 만들어드려요.",
                    "가족과 함께하는 따뜻한 공간을 완성합니다.",
                ]
            
            return suffixes[combo_hash % len(suffixes)]
        return None

    def _filter_and_score_products(self, combo, products):
        """취향에 맞는 제품 필터링 및 점수 계산 (고품질)"""
        scored = []
        vibe_key = combo['vibe'].split('(')[1].split(')')[0].strip() if '(' in combo['vibe'] else ''
        priority = combo['priority']
        budget_min, budget_max = self._parse_budget_range(combo['budget'])
        lineup_min, lineup_max = self._parse_budget_range(combo['lineup'])
        mate = combo['mate']
        
        for product in products:
            score = 0.0
            
            # 1. 인테리어 스타일 매칭 (가중치: 4.0)
            score += self._score_vibe_match(product, vibe_key) * 4.0
            
            # 2. 우선순위 매칭 (가중치: 3.0)
            score += self._score_priority_match(product, priority) * 3.0
            
            # 3. 예산 매칭 (가중치: 2.5)
            score += self._score_budget_match(product, budget_min, budget_max) * 2.5
            
            # 4. 라인업 매칭 (가중치: 1.5)
            score += self._score_lineup_match(product, lineup_min, lineup_max) * 1.5
            
            # 5. 메이트 구성 매칭 (가중치: 1.0)
            score += self._score_mate_match(product, mate) * 1.0
            
            # 6. 리뷰 품질 보너스 (가중치: 1.0)
            review_bonus = self._calculate_review_bonus(product)
            score += review_bonus * 1.0
            
            if score >= 5.0:  # 최소 점수 이상만 선택
                scored.append((product, score))
        
        # 점수 순으로 정렬
        scored.sort(key=lambda x: x[1], reverse=True)
        return scored

    def _score_vibe_match(self, product, vibe_key):
        """인테리어 스타일 매칭 점수"""
        name_upper = product.name.upper()
        if vibe_key == 'Modern & Minimal':
            if 'OBJET' in name_upper or '오브제' in product.name:
                return 1.0
        elif vibe_key == 'Cozy & Nature':
            if 'OBJET' in name_upper or '오브제' in product.name:
                return 1.0
        elif vibe_key == 'Luxury & Artistic':
            if 'SIGNATURE' in name_upper or '시그니처' in product.name:
                return 1.0
        elif vibe_key == 'Unique & Pop':
            if 'OBJET' in name_upper or '오브제' in product.name:
                return 1.0
        return 0.0

    def _score_priority_match(self, product, priority):
        """우선순위 매칭 점수"""
        name_upper = product.name.upper()
        if '디자인' in priority:
            if 'OBJET' in name_upper or 'SIGNATURE' in name_upper or '오브제' in product.name or '시그니처' in product.name:
                return 1.0
        elif 'AI' in priority or '스마트' in priority:
            if 'AI' in name_upper or '스마트' in product.name or '음성' in product.name:
                return 1.0
        elif '에너지' in priority or '효율' in priority:
            if '인버터' in product.name or '효율' in product.name or '에너지' in product.name or '1등급' in product.name:
                return 1.0
        elif '가격' in priority or '가성비' in priority:
            if product.price and product.price < 2000000:
                return 1.0
        return 0.5

    def _score_budget_match(self, product, budget_min, budget_max):
        """예산 매칭 점수"""
        if not product.price:
            return 0.0
        price = float(product.price)
        if budget_min and budget_max:
            if budget_min <= price <= budget_max:
                return 1.0
            elif price < budget_min:
                return 0.3
            elif price <= budget_max * 1.2:  # 20% 초과까지 허용
                return 0.5
        elif budget_min:
            if price >= budget_min:
                return 1.0
        return 0.0

    def _score_lineup_match(self, product, lineup_min, lineup_max):
        """라인업 매칭 점수"""
        return self._score_budget_match(product, lineup_min, lineup_max)

    def _score_mate_match(self, product, mate):
        """메이트 구성 매칭 점수"""
        name = product.name
        if '1인' in mate or '혼자' in mate:
            if any(kw in name for kw in ['소형', '1인', '미니', '컴팩트', '300L', '400L']):
                return 1.0
        elif '2인' in mate or '신혼' in mate:
            if any(kw in name for kw in ['2인', '중형', '스탠다드', '500L', '600L']):
                return 1.0
        elif '3~4인' in mate or '가족' in mate:
            if any(kw in name for kw in ['대용량', '4인', '5인', '6인', '패밀리', '800L', '900L', '1000L']):
                return 1.0
        return 0.5

    def _calculate_review_bonus(self, product):
        """리뷰 품질 보너스 점수"""
        review_count = ProductReview.objects.filter(product=product).count()
        if review_count >= 100:
            return 1.0
        elif review_count >= 50:
            return 0.7
        elif review_count >= 20:
            return 0.5
        elif review_count >= 10:
            return 0.3
        return 0.0

    def _select_diverse_products(self, scored_products, combo, limit=3):
        """취향 조합별로 다양한 제품 선택"""
        if not scored_products:
            return []
        
        combo_key = f"{combo['vibe']}_{combo['priority']}_{combo['budget']}_{combo['mate']}"
        combo_hash = int(hashlib.md5(combo_key.encode()).hexdigest(), 16)
        
        # 상위 제품 중에서 해시 기반으로 선택
        top_n = min(20, len(scored_products))
        start_idx = combo_hash % top_n
        
        selected = []
        for i in range(limit):
            idx = (start_idx + i) % top_n
            selected.append(scored_products[idx])
        
        return selected

    def _extract_product_features(self, product, combo):
        """제품의 리뷰에서 특징 추출"""
        reviews = ProductReview.objects.filter(product=product)[:50]
        if not reviews:
            return None
        
        review_texts = [r.review_text for r in reviews if r.review_text]
        if not review_texts:
            return None
        
        # 키워드 추출
        keywords = self._extract_meaningful_keywords(review_texts, combo)
        
        # 특징 문구 생성
        if keywords:
            return {
                'keywords': keywords[:5],
                'review_count': len(reviews),
                'positive_aspects': self._extract_positive_aspects(review_texts, combo)
            }
        return None

    def _extract_meaningful_keywords(self, texts, combo):
        """의미 있는 키워드 추출"""
        # 불용어 제거
        stopwords = {'이', '가', '을', '를', '의', '에', '와', '과', '도', '로', '으로', '에서', '까지', '부터', '만', '도', '는', '은', '것', '수', '등', '및', '또한', '그리고', '하지만', '그런데', '그래서', '그러나', '그러므로', '따라서', '그러면', '그렇지만', '그런', '이런', '저런', '그', '이', '저', '그것', '이것', '저것', '그때', '이때', '저때', '그곳', '이곳', '저곳', '그분', '이분', '저분', '그녀', '그들', '이들', '저들', '그녀들', '그분들', '이분들', '저분들', '그것들', '이것들', '저것들', '그때들', '이때들', '저때들', '그곳들', '이곳들', '저곳들', '그녀들', '그들들', '이들들', '저들들', '그녀들들', '그분들들', '이분들들', '저분들들', '그것들들', '이것들들', '저것들들', '그때들들', '이때들들', '저때들들', '그곳들들', '이곳들들', '저곳들들'}
        
        all_words = []
        for text in texts:
            # 한글, 영문, 숫자만 추출
            words = re.findall(r'[가-힣a-zA-Z0-9]+', text)
            words = [w for w in words if len(w) >= 2 and w not in stopwords]
            all_words.extend(words)
        
        # 빈도 계산
        word_counts = Counter(all_words)
        
        # 우선순위에 맞는 키워드 필터링
        priority_keywords = {
            '디자인': ['디자인', '예쁘', '깔끔', '스타일', '색상', '컬러', '무드', '인테리어', '세련', '고급'],
            'AI': ['AI', '스마트', '음성', '인식', '자동', '편리', '편하', '쉽', '간편'],
            '에너지': ['에너지', '효율', '절전', '1등급', '인버터', '전력', '소비'],
            '가격': ['가격', '가성비', '합리', '저렴', '실용', '기본', '표준']
        }
        
        priority = combo['priority']
        relevant_keywords = []
        for keyword_type, keywords in priority_keywords.items():
            if keyword_type in priority or any(kw in priority for kw in ['AI', '스마트', '에너지', '효율', '가격', '가성비']):
                relevant_keywords.extend(keywords)
        
        # 관련 키워드 우선 선택
        selected = []
        for word, count in word_counts.most_common(30):
            if any(kw in word for kw in relevant_keywords):
                selected.append(word)
            elif len(selected) < 10:
                selected.append(word)
        
        return selected[:10]

    def _extract_positive_aspects(self, texts, combo):
        """긍정적인 측면 추출"""
        positive_patterns = [
            r'좋[아이]', r'만족', r'훌륭', r'최고', r'완벽', r'추천', r'감사', r'행복',
            r'편리', r'편하', r'쉽', r'깔끔', r'예쁘', r'멋있', r'고급', r'세련'
        ]
        
        aspects = []
        for text in texts[:20]:
            for pattern in positive_patterns:
                if re.search(pattern, text):
                    # 문장 추출
                    sentences = re.split(r'[.!?]', text)
                    for sentence in sentences:
                        if re.search(pattern, sentence) and len(sentence) > 10:
                            aspects.append(sentence.strip()[:100])
                            break
                    break
        
        return aspects[:3]

    def _extract_key_sentences(self, reason_text, combo):
        """추천이유에서 핵심 문장 추출"""
        if not reason_text:
            return []
        
        # 문장 분리
        sentences = re.split(r'[.!?]\s+', reason_text)
        
        # 우선순위에 맞는 문장 필터링
        priority_keywords = {
            '디자인': ['디자인', '예쁘', '깔끔', '스타일', '색상'],
            'AI': ['AI', '스마트', '음성', '인식'],
            '에너지': ['에너지', '효율', '절전'],
            '가격': ['가격', '가성비', '합리']
        }
        
        priority = combo['priority']
        relevant_keywords = []
        for keyword_type, keywords in priority_keywords.items():
            if keyword_type in priority or any(kw in priority for kw in keywords):
                relevant_keywords.extend(keywords)
        
        selected = []
        for sentence in sentences:
            if any(kw in sentence for kw in relevant_keywords) and len(sentence) > 20:
                selected.append(sentence.strip())
        
        return selected[:2]

    def _format_features(self, product_features, priority_desc):
        """특징 문구 포맷팅"""
        if not product_features:
            return ""
        
        all_keywords = []
        for features in product_features:
            if features and 'keywords' in features:
                all_keywords.extend(features['keywords'])
        
        if all_keywords:
            unique_keywords = list(set(all_keywords))[:5]
            return f"리뷰에서 자주 언급되는 {', '.join(unique_keywords)} 등의 특징이 돋보여요."
        
        return "실제 사용자들의 긍정적인 피드백이 많은 제품들이에요."

    def _generate_fallback_recommendation(self, combo):
        """대체 추천 문구 (제품을 찾지 못한 경우)"""
        vibe_name = combo['vibe'].split('(')[0].strip()
        mate_desc = self._get_mate_description(combo['mate'])
        priority_desc = combo['priority']
        
        text = f"{mate_desc} {vibe_name} 무드를 완성하는 스타일\n\n"
        text += f"당신의 {priority_desc}를 반영한 추천입니다.\n"
        text += f"{combo['budget']} 예산 안에서 최적의 선택을 제안드려요."
        
        return text

    def _get_quality_templates(self, combo, design_lineup, recommended_categories):
        """고품질 템플릿 생성"""
        vibe_name = combo['vibe'].split('(')[0].strip()
        mate_desc = self._get_mate_description(combo['mate'])
        priority_desc = combo['priority']
        budget_desc = combo['budget']
        
        templates = [
            {
                'intro': f"{mate_desc} {vibe_name} 무드를 완성하는 {design_lineup} 스타일",
                'body': f"당신의 공간 분위기와 {priority_desc}를 반영해",
                'products': f"{', '.join(recommended_categories)} 중심으로 구성했어요.",
                'closing': f"{budget_desc} 예산 안에서 {priority_desc}와 기능성을 모두 담았어요."
            },
            {
                'intro': f"{mate_desc} 라이프스타일에 맞는 {vibe_name} 인테리어",
                'body': f"{priority_desc}을 최우선으로 고려한",
                'products': f"{', '.join(recommended_categories)} 조합을 제안드려요.",
                'closing': f"{budget_desc} 범위에서 최적의 가성비를 찾았어요."
            },
            {
                'intro': f"{vibe_name} 감성으로 채우는 {mate_desc} 공간",
                'body': f"{priority_desc}을 중시하는 당신을 위해",
                'products': f"{', '.join(recommended_categories)}를 엄선했어요.",
                'closing': f"{budget_desc} 예산으로 {design_lineup}의 품격을 경험하세요."
            },
            {
                'intro': f"{mate_desc} {vibe_name} 무드를 완성하는 {design_lineup}",
                'body': f"당신의 {priority_desc} 니즈를 충족시키는",
                'products': f"{', '.join(recommended_categories)} 패키지",
                'closing': f"{budget_desc} 안에서 디자인과 기능의 균형을 맞췄어요."
            },
            {
                'intro': f"{vibe_name} 스타일의 {mate_desc} 홈을 위한",
                'body': f"{priority_desc}에 최적화된",
                'products': f"{', '.join(recommended_categories)} 세트",
                'closing': f"{budget_desc} 예산으로 완벽한 조합을 제안합니다."
            },
        ]
        
        return templates

    def _get_mate_description(self, mate):
        """메이트 구성에 따른 설명 문구"""
        if '1인' in mate or '혼자' in mate:
            return "혼자만의"
        elif '2인' in mate or '신혼' in mate or '둘이' in mate:
            return "둘만의 신혼"
        elif '3~4인' in mate or '가족' in mate:
            return "가족과 함께하는"
        return "당신만의"

    def _get_design_lineup(self, vibe_key):
        """인테리어 스타일별 디자인 라인업"""
        lineup_map = {
            'Modern & Minimal': '오브제컬렉션',
            'Cozy & Nature': '오브제컬렉션',
            'Luxury & Artistic': '시그니처컬렉션',
            'Unique & Pop': '오브제컬렉션',
        }
        return lineup_map.get(vibe_key, '오브제컬렉션')

    def _get_recommended_categories(self, combo):
        """우선순위, 예산, 라인업, 메이트를 모두 고려한 추천 제품 카테고리"""
        priority = combo['priority']
        budget = combo['budget']
        mate = combo['mate']
        
        categories = []
        
        # 우선순위 기반
        if '디자인' in priority:
            if '하이엔드' in budget or '고급형' in budget:
                categories = ['시그니처 냉장고', '프리미엄 인덕션', '디자인 식기세척기']
            else:
                categories = ['오브제컬렉션 냉장고', '스타일리시 인덕션', '세련된 식기세척기']
        elif 'AI' in priority or '스마트' in priority:
            categories = ['AI 냉장고', '스마트 TV', '음성인식 가전']
        elif '에너지' in priority or '효율' in priority:
            categories = ['1등급 에너지 냉장고', '인버터 세탁기', '절전형 TV']
        elif '가격' in priority or '가성비' in priority:
            categories = ['실용 냉장고', '기본형 세탁기', '표준형 TV']
        else:
            categories = ['냉장고', '세탁기', 'TV']
        
        # 메이트 구성에 따른 조정
        if '1인' in mate or '혼자' in mate:
            categories = [c.replace('냉장고', '소형 냉장고').replace('세탁기', '미니 세탁기') for c in categories]
        elif '3~4인' in mate or '가족' in mate:
            categories = [c.replace('냉장고', '대용량 냉장고').replace('세탁기', '대용량 세탁기') for c in categories]
        
        # 예산에 따른 조정
        if '실속형' in budget:
            categories = [c.replace('시그니처', '기본형').replace('프리미엄', '실용') for c in categories]
        elif '하이엔드' in budget:
            categories = [c.replace('기본형', '프리미엄').replace('표준형', '하이엔드') for c in categories]
        
        return categories[:3]

    def _parse_budget_range(self, budget_text):
        """예산 범위 텍스트를 파싱하여 최소/최대값 반환"""
        if '500만원 미만' in budget_text or '실속형' in budget_text:
            return (0, 5000000)
        elif '500만원 ~ 1,500만원' in budget_text or '표준형' in budget_text:
            return (5000000, 15000000)
        elif '1,500만원 ~ 3,000만원' in budget_text or '고급형' in budget_text:
            return (15000000, 30000000)
        elif '3,000만원 이상' in budget_text or '하이엔드' in budget_text:
            return (30000000, None)
        return (None, None)

    def _save_to_csv(self, recommendations, output_path, no_backup=False, new_file=False):
        """CSV 파일로 저장"""
        # 절대 경로로 변환
        if not os.path.isabs(output_path):
            base_dir = Path(__file__).parent.parent.parent.parent
            output_path = str(base_dir / output_path)
        
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # new_file 옵션이면 타임스탬프 추가
        if new_file and os.path.exists(output_path):
            import time
            timestamp = int(time.time())
            output_path = output_path.replace('.csv', f'_{timestamp}.csv')
            self.stdout.write(f'  [새파일] 타임스탬프가 붙은 새 파일 생성: {os.path.basename(output_path)}')
        
        # 기존 파일이 있으면 백업 시도 (new_file이 아니고 no_backup이 아닐 때만)
        elif os.path.exists(output_path) and not no_backup:
            backup_path = output_path.replace('.csv', '_backup.csv')
            try:
                # 기존 백업 파일이 있으면 삭제
                if os.path.exists(backup_path):
                    os.remove(backup_path)
                # 기존 파일을 백업으로 이동
                os.rename(output_path, backup_path)
                self.stdout.write(f'  [백업] 기존 파일을 백업했습니다: {os.path.basename(backup_path)}')
                self.stdout.write(f'  [덮어쓰기] 기존 파일을 새 데이터로 덮어씁니다.')
            except PermissionError:
                # 파일이 열려있어서 백업 실패 시, 타임스탬프 추가한 새 파일 생성
                import time
                timestamp = int(time.time())
                output_path = output_path.replace('.csv', f'_{timestamp}.csv')
                self.stdout.write(self.style.WARNING(
                    f'  [경고] 기존 파일이 열려있어 백업할 수 없습니다.\n'
                    f'  [대안] 새 파일로 생성합니다: {os.path.basename(output_path)}'
                ))
            except Exception as e:
                # 기타 오류 시에도 타임스탬프 추가
                import time
                timestamp = int(time.time())
                output_path = output_path.replace('.csv', f'_{timestamp}.csv')
                self.stdout.write(self.style.WARNING(
                    f'  [경고] 백업 실패: {e}\n'
                    f'  [대안] 새 파일로 생성합니다: {os.path.basename(output_path)}'
                ))
        elif os.path.exists(output_path) and no_backup:
            self.stdout.write(self.style.WARNING(
                f'  [경고] --no-backup 옵션: 기존 파일을 백업하지 않고 덮어씁니다.'
            ))
        
        # 새 파일 생성 (기존 파일 덮어쓰기 또는 새 파일)
        try:
            with open(output_path, 'w', encoding='utf-8-sig', newline='') as f:
                if not recommendations:
                    return
                
                fieldnames = [
                    'taste_id',
                    '인테리어_스타일',
                    '메이트_구성',
                    '우선순위',
                    '예산_범위',
                    '선호_라인업',
                    '리뷰_기반_추천문구',
                    'AI_기반_추천문구',
                ]
                
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(recommendations)
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'  [오류] 파일 저장 실패: {e}'))
            raise
