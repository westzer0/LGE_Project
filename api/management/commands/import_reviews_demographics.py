"""
리뷰, 인구통계, 추천이유 데이터를 import하는 스크립트

사용법:
    python manage.py import_reviews_demographics
    python manage.py import_reviews_demographics --dry-run
"""

import csv
import ast
from pathlib import Path
from django.core.management.base import BaseCommand
from api.models import Product, ProductDemographics, ProductReview, ProductRecommendReason


class Command(BaseCommand):
    help = "리뷰, 인구통계, 추천이유 데이터를 import"

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true", help="실제 저장 없이 테스트")
        parser.add_argument("--limit", type=int, default=0, help="각 파일당 최대 행 수 (0=전체)")

    def handle(self, *args, **options):
        self.dry_run = options.get('dry_run', False)
        self.limit = options.get('limit', 0)
        
        base_dir = Path(__file__).parent.parent.parent.parent / 'data'
        
        self.stdout.write(self.style.SUCCESS("=" * 60))
        self.stdout.write(self.style.SUCCESS("리뷰/인구통계/추천이유 Import 시작"))
        self.stdout.write(self.style.SUCCESS("=" * 60))
        
        # 1. 인구통계 Import
        self.import_demographics(base_dir)
        
        # 2. 추천이유 Import
        self.import_recommend_reasons(base_dir)
        
        # 3. 리뷰 Import
        self.import_reviews(base_dir)
        
        # 최종 통계
        self.print_final_stats()

    def import_demographics(self, base_dir):
        """인구통계 데이터 Import"""
        self.stdout.write("\n[1] 인구통계 Import...")
        
        demo_dir = base_dir / '리뷰_인구통계, 추천이유'
        if not demo_dir.exists():
            self.stdout.write(self.style.ERROR(f"  폴더 없음: {demo_dir}"))
            return
        
        total_created = 0
        total_updated = 0
        total_skipped = 0
        
        for csv_file in demo_dir.glob('*인구통계*.csv'):
            self.stdout.write(f"  [FILE] {csv_file.name}")
            
            try:
                with open(csv_file, 'r', encoding='utf-8-sig', newline='') as f:
                    reader = csv.DictReader(f)
                    
                    for idx, row in enumerate(reader):
                        if self.limit and idx >= self.limit:
                            break
                        
                        product_code = row.get('Product_code', '').strip()
                        if not product_code:
                            continue
                        
                        # Product 찾기
                        try:
                            product = Product.objects.get(model_number=product_code)
                        except Product.DoesNotExist:
                            total_skipped += 1
                            continue
                        
                        # JSON 리스트 파싱
                        family_types = self._parse_list(row.get('family_list', '[]'))
                        house_sizes = self._parse_list(row.get('size_list', '[]'))
                        house_types = self._parse_list(row.get('house_list', '[]'))
                        
                        if self.dry_run:
                            self.stdout.write(f"    [DRY] {product_code}: {family_types}")
                            total_created += 1
                            continue
                        
                        # DB 저장
                        obj, created = ProductDemographics.objects.update_or_create(
                            product=product,
                            defaults={
                                'family_types': family_types,
                                'house_sizes': house_sizes,
                                'house_types': house_types,
                                'source': csv_file.name,
                            }
                        )
                        
                        if created:
                            total_created += 1
                        else:
                            total_updated += 1
                            
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"    Error: {e}"))
        
        self.stdout.write(self.style.SUCCESS(
            f"  [OK] 인구통계: 생성 {total_created}, 업데이트 {total_updated}, 스킵 {total_skipped}"
        ))

    def import_recommend_reasons(self, base_dir):
        """추천이유 데이터 Import"""
        self.stdout.write("\n[2] 추천이유 Import...")
        
        demo_dir = base_dir / '리뷰_인구통계, 추천이유'
        if not demo_dir.exists():
            self.stdout.write(self.style.ERROR(f"  폴더 없음: {demo_dir}"))
            return
        
        total_created = 0
        total_updated = 0
        total_skipped = 0
        
        for csv_file in demo_dir.glob('*추천이유*.csv'):
            self.stdout.write(f"  [FILE] {csv_file.name}")
            
            try:
                with open(csv_file, 'r', encoding='utf-8-sig', newline='') as f:
                    reader = csv.DictReader(f)
                    
                    for idx, row in enumerate(reader):
                        if self.limit and idx >= self.limit:
                            break
                        
                        model_name = row.get('model_name', '').strip()
                        reason_text = row.get('recommend_reason', '').strip()
                        
                        if not model_name or not reason_text:
                            continue
                        
                        # Product 찾기
                        try:
                            product = Product.objects.get(model_number=model_name)
                        except Product.DoesNotExist:
                            total_skipped += 1
                            continue
                        
                        if self.dry_run:
                            self.stdout.write(f"    [DRY] {model_name}: {reason_text[:50]}...")
                            total_created += 1
                            continue
                        
                        # DB 저장
                        obj, created = ProductRecommendReason.objects.update_or_create(
                            product=product,
                            defaults={
                                'reason_text': reason_text,
                                'source': csv_file.name,
                            }
                        )
                        
                        if created:
                            total_created += 1
                        else:
                            total_updated += 1
                            
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"    Error: {e}"))
        
        self.stdout.write(self.style.SUCCESS(
            f"  [OK] 추천이유: 생성 {total_created}, 업데이트 {total_updated}, 스킵 {total_skipped}"
        ))

    def import_reviews(self, base_dir):
        """리뷰 데이터 Import"""
        self.stdout.write("\n[3] 리뷰 Import...")
        
        review_dir = base_dir / '리뷰'
        if not review_dir.exists():
            self.stdout.write(self.style.ERROR(f"  폴더 없음: {review_dir}"))
            return
        
        total_created = 0
        total_skipped = 0
        
        for csv_file in review_dir.glob('*.csv'):
            self.stdout.write(f"  [FILE] {csv_file.name}")
            file_count = 0
            
            try:
                with open(csv_file, 'r', encoding='utf-8-sig', newline='') as f:
                    reader = csv.DictReader(f)
                    
                    for idx, row in enumerate(reader):
                        if self.limit and idx >= self.limit:
                            break
                        
                        product_code = row.get('Product_code', '').strip()
                        star = row.get('Star', '').strip()
                        review_text = row.get('Review', '').strip()
                        
                        if not product_code or not review_text:
                            continue
                        
                        # Product 찾기
                        try:
                            product = Product.objects.get(model_number=product_code)
                        except Product.DoesNotExist:
                            total_skipped += 1
                            continue
                        
                        if self.dry_run:
                            if file_count < 3:  # 파일당 3개만 출력
                                self.stdout.write(f"    [DRY] {product_code}: {review_text[:30]}...")
                            file_count += 1
                            total_created += 1
                            continue
                        
                        # DB 저장 (리뷰는 중복 허용 - 같은 제품에 여러 리뷰)
                        ProductReview.objects.create(
                            product=product,
                            star=star,
                            review_text=review_text,
                            source=csv_file.name,
                        )
                        
                        total_created += 1
                        file_count += 1
                        
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"    Error: {e}"))
            
            self.stdout.write(f"    → {file_count}개 처리")
        
        self.stdout.write(self.style.SUCCESS(
            f"  [OK] 리뷰: 생성 {total_created}, 스킵 {total_skipped}"
        ))

    def _parse_list(self, value):
        """문자열 리스트를 Python 리스트로 변환"""
        if not value or value == '[]':
            return []
        try:
            result = ast.literal_eval(value)
            if isinstance(result, list):
                return result
            return []
        except:
            return []

    def print_final_stats(self):
        """최종 통계 출력"""
        self.stdout.write("\n" + "=" * 60)
        self.stdout.write(self.style.SUCCESS("최종 통계"))
        self.stdout.write("=" * 60)
        
        if self.dry_run:
            self.stdout.write(self.style.WARNING("[DRY RUN] 실제로는 저장되지 않았습니다."))
        else:
            from api.models import ProductDemographics, ProductReview, ProductRecommendReason
            
            demo_count = ProductDemographics.objects.count()
            review_count = ProductReview.objects.count()
            reason_count = ProductRecommendReason.objects.count()
            
            self.stdout.write(f"  인구통계: {demo_count}개")
            self.stdout.write(f"  리뷰: {review_count}개")
            self.stdout.write(f"  추천이유: {reason_count}개")
        
        self.stdout.write("=" * 60)
        self.stdout.write(self.style.SUCCESS("[OK] Import 완료!"))

