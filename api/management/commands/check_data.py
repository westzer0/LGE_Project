from django.core.management.base import BaseCommand
from api.models import Product, ProductSpec, UserSample
import json


class Command(BaseCommand):
    help = "Check current data status in database"

    def handle(self, *args, **opts):
        self.stdout.write(self.style.SUCCESS("=== 데이터베이스 상태 확인 ===\n"))

        # Product 테이블 확인
        product_count = Product.objects.count()
        self.stdout.write(f"[Product] Product 테이블: {product_count}개")
        
        if product_count > 0:
            # 카테고리별 통계
            self.stdout.write("\n카테고리별 제품 수:")
            for category_code, category_name in Product.CATEGORY_CHOICES:
                count = Product.objects.filter(category=category_code).count()
                if count > 0:
                    self.stdout.write(f"  - {category_name} ({category_code}): {count}개")
            
            # 샘플 제품 출력
            self.stdout.write("\n샘플 제품 (최신 5개):")
            for product in Product.objects.all()[:5]:
                self.stdout.write(f"  - {product.name} ({product.model_number}) - {product.get_category_display()}")
        else:
            self.stdout.write(self.style.WARNING("  [WARNING] 제품 데이터가 없습니다."))

        # ProductSpec 테이블 확인
        spec_count = ProductSpec.objects.count()
        self.stdout.write(f"\n[ProductSpec] ProductSpec 테이블: {spec_count}개")
        
        if spec_count > 0:
            # 샘플 스펙 출력
            self.stdout.write("\n샘플 ProductSpec (3개):")
            for spec in ProductSpec.objects.all()[:3]:
                try:
                    spec_data = json.loads(spec.spec_json)
                    self.stdout.write(f"  - Product ID: {spec.product_id}")
                    self.stdout.write(f"    Source: {spec.source}")
                    self.stdout.write(f"    Keys in spec_json: {len(spec_data)}개")
                except:
                    self.stdout.write(f"  - Product ID: {spec.product_id} (JSON 파싱 오류)")
        else:
            self.stdout.write(self.style.WARNING("  [WARNING] 스펙 데이터가 없습니다."))

        # UserSample 테이블 확인
        user_count = UserSample.objects.count()
        self.stdout.write(f"\n[UserSample] UserSample 테이블: {user_count}개")
        
        if user_count > 0:
            # 샘플 사용자 출력
            self.stdout.write("\n샘플 UserSample (3개):")
            for user in UserSample.objects.all()[:3]:
                self.stdout.write(f"  - User ID: {user.user_id}")
                self.stdout.write(f"    Household: {user.household_size}, Budget: {user.budget_range}")
        else:
            self.stdout.write(self.style.WARNING("  [WARNING] 사용자 샘플 데이터가 없습니다."))

        # 요약
        self.stdout.write(self.style.SUCCESS("\n=== 요약 ==="))
        self.stdout.write(f"총 제품: {product_count}개")
        self.stdout.write(f"총 스펙: {spec_count}개")
        self.stdout.write(f"총 사용자 샘플: {user_count}개")
        
        if product_count == 0:
            self.stdout.write(self.style.ERROR("\n[ERROR] 제품 데이터가 없습니다. import_specs 커맨드를 실행하세요."))
        elif product_count < 10:
            self.stdout.write(self.style.WARNING(f"\n[WARNING] 제품 데이터가 적습니다 ({product_count}개). 더 많은 CSV를 import하세요."))
        else:
            self.stdout.write(self.style.SUCCESS("\n[SUCCESS] 데이터 상태가 정상입니다."))

