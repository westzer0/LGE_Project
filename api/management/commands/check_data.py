from django.core.management.base import BaseCommand
from api.models import (
    Product, ProductSpec, UserSample,
    ProductDemographics, ProductReview, ProductRecommendReason
)
import json


class Command(BaseCommand):
    help = "Check current data status in database"

    def handle(self, *args, **opts):
        self.stdout.write(self.style.SUCCESS("=" * 60))
        self.stdout.write(self.style.SUCCESS("데이터베이스 상태 확인"))
        self.stdout.write(self.style.SUCCESS("=" * 60))
        
        # 1. 제품스펙 Import 상태
        self.stdout.write("\n┌─────────────────────────────────────────────────────────────┐")
        self.stdout.write("│  [1] 1단계: 제품스펙 Import                                    │")
        self.stdout.write("│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━│")
        
        product_count = Product.objects.count()
        spec_count = ProductSpec.objects.count()
        
        if product_count > 0 and spec_count > 0:
            self.stdout.write(self.style.SUCCESS(f"│  [OK] 완료! 100%"))
            self.stdout.write(f"│  Product 테이블: {product_count}개")
            self.stdout.write(f"│  ProductSpec 테이블: {spec_count}개")
            
            # 카테고리별 통계
            self.stdout.write("\n│  카테고리별 제품 수:")
            for category_code, category_name in Product.CATEGORY_CHOICES:
                count = Product.objects.filter(category=category_code).count()
                if count > 0:
                    self.stdout.write(f"│    - {category_name} ({category_code}): {count}개")
        else:
            self.stdout.write(self.style.WARNING("│  [WARN] 미완료"))
            self.stdout.write(f"│  Product: {product_count}개")
            self.stdout.write(f"|  ProductSpec: {spec_count}개")
        
        self.stdout.write("└─────────────────────────────────────────────────────────────┘")
        
        # 2. 인구통계 Import 상태
        self.stdout.write("\n┌─────────────────────────────────────────────────────────────┐")
        self.stdout.write("│  [2] 2단계: 인구통계 Import                                    │")
        self.stdout.write("│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━│")
        
        demo_count = ProductDemographics.objects.count()
        
        if demo_count > 0:
            self.stdout.write(self.style.SUCCESS(f"│  [OK] 완료! 100%"))
            self.stdout.write(f"│  ProductDemographics: {demo_count}개")
            
            # 스펙이 있는 제품 중 인구통계가 있는 제품 수
            products_with_spec = Product.objects.filter(spec__isnull=False).count()
            products_with_demo = Product.objects.filter(demographics__isnull=False).distinct().count()
            skipped = products_with_spec - products_with_demo
            
            if skipped > 0:
                self.stdout.write(f"│  → 스킵 {skipped}개 (제품스펙에 없는 모델)")
        else:
            self.stdout.write(self.style.WARNING("│  [WARN] 미완료"))
            self.stdout.write(f"│  ProductDemographics: {demo_count}개")
        
        self.stdout.write("└─────────────────────────────────────────────────────────────┘")
        
        # 3. 추천이유 Import 상태
        self.stdout.write("\n┌─────────────────────────────────────────────────────────────┐")
        self.stdout.write("│  [3] 3단계: 추천이유 Import                                    │")
        self.stdout.write("│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━│")
        
        reason_count = ProductRecommendReason.objects.count()
        
        if reason_count > 0:
            self.stdout.write(self.style.SUCCESS(f"│  [OK] 완료! 100%"))
            self.stdout.write(f"│  ProductRecommendReason: {reason_count}개")
            
            # 카테고리별 통계
            from django.db.models import Count
            reason_by_category = (
                ProductRecommendReason.objects
                .values('product__category')
                .annotate(count=Count('id'))
            )
            if reason_by_category:
                self.stdout.write("│  카테고리별:")
                for item in reason_by_category:
                    category = item['product__category']
                    count = item['count']
                    self.stdout.write(f"│    - {category}: {count}개")
        else:
            self.stdout.write(self.style.WARNING("│  [WARN] 미완료"))
            self.stdout.write(f"│  ProductRecommendReason: {reason_count}개")
        
        self.stdout.write("└─────────────────────────────────────────────────────────────┘")
        
        # 4. 리뷰 Import 상태
        self.stdout.write("\n┌─────────────────────────────────────────────────────────────┐")
        self.stdout.write("│  [4] 4단계: 리뷰 Import                                        │")
        self.stdout.write("│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━│")
        
        review_count = ProductReview.objects.count()
        
        if review_count > 0:
            # 진행률 계산 (예상 13만개 기준)
            expected_reviews = 130000
            progress = min(100, int((review_count / expected_reviews) * 100))
            
            if progress >= 100:
                self.stdout.write(self.style.SUCCESS(f"│  [OK] 완료! 100%"))
            else:
                self.stdout.write(f"│  [진행중] {progress}%")
            
            self.stdout.write(f"│  ProductReview: {review_count:,}개")
            
            # 제품별 평균 리뷰 수
            from django.db.models import Count
            products_with_reviews = Product.objects.annotate(
                review_count=Count('reviews')
            ).filter(review_count__gt=0).count()
            
            self.stdout.write(f"│  → 리뷰가 있는 제품: {products_with_reviews}개")
        else:
            self.stdout.write(self.style.WARNING("│  [WARN] 미완료"))
            self.stdout.write(f"│  ProductReview: {review_count}개")
        
        self.stdout.write("└─────────────────────────────────────────────────────────────┘")
        
        # 최종 요약
        self.stdout.write("\n" + "=" * 60)
        self.stdout.write(self.style.SUCCESS("최종 요약"))
        self.stdout.write("=" * 60)
        self.stdout.write(f"  제품: {product_count}개")
        self.stdout.write(f"  스펙: {spec_count}개")
        self.stdout.write(f"  인구통계: {demo_count}개")
        self.stdout.write(f"  추천이유: {reason_count}개")
        self.stdout.write(f"  리뷰: {review_count:,}개")
        self.stdout.write("=" * 60)
        
        # 상태 판단
        if product_count >= 1400 and spec_count >= 1400:
            if demo_count >= 500 and reason_count >= 200:
                if review_count >= 100000:
                    self.stdout.write(self.style.SUCCESS("\n[OK] 모든 데이터가 정상적으로 import되었습니다!"))
                else:
                    self.stdout.write(self.style.WARNING(f"\n[WARN] 리뷰 데이터가 아직 완료되지 않았습니다 ({review_count:,}개 / 예상 130,000개)"))
            else:
                self.stdout.write(self.style.WARNING("\n[WARN] 인구통계 또는 추천이유 데이터가 부족합니다."))
        else:
            self.stdout.write(self.style.ERROR("\n[ERROR] 제품/스펙 데이터가 부족합니다. import 명령어를 실행하세요."))

