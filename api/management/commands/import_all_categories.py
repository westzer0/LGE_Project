import os
import csv
import json
import re
from pathlib import Path
from django.core.management.base import BaseCommand
from api.models import Product, ProductSpec


class Command(BaseCommand):
    help = "동적으로 data/ 폴더의 모든 CSV 파일을 JSON 필드 방식으로 import"

    # ============================================================
    # 카테고리 매핑 (파일명 → 카테고리명)
    # ============================================================
    CATEGORY_MAP = {
        'TV': ('TV', 'TV/오디오'),
        '냉장고': ('KITCHEN', '주방가전'),
        '세탁': ('LIVING', '생활가전'),
        '세탁기': ('LIVING', '생활가전'),
        '식기세척기': ('KITCHEN', '주방가전'),
        '오디오': ('LIVING', '생활가전'),
        '홈오디오': ('LIVING', '생활가전'),
        '프로젝터': ('TV', 'TV/오디오'),
        '스탠바이미': ('TV', 'TV/오디오'),
        '청소기': ('LIVING', '생활가전'),
        '가습기': ('AIR', '에어컨/에어케어'),
        '공기청정기': ('AIR', '에어컨/에어케어'),
        '에어컨': ('AIR', '에어컨/에어케어'),
        '전자레인지': ('KITCHEN', '주방가전'),
        '광파오븐': ('KITCHEN', '주방가전'),
        '가스레인지': ('KITCHEN', '주방가전'),
        '전기레인지': ('KITCHEN', '주방가전'),
        '에어프라이어': ('KITCHEN', '주방가전'),
        '밥솥': ('KITCHEN', '주방가전'),
        '김치냉장고': ('KITCHEN', '주방가전'),
        '상업용': ('TV', 'TV/오디오'),
        '상업용 디스플레이': ('TV', 'TV/오디오'),
        '신발관리': ('LIVING', '생활가전'),
        '와인셀러': ('KITCHEN', '주방가전'),
        'AIHome': ('AI', 'AI Home'),
        '의류관리기': ('LIVING', '생활가전'),
        '의류건조기': ('LIVING', '생활가전'),
        '워시타워': ('LIVING', '생활가전'),
        '워시콤보': ('LIVING', '생활가전'),
        '정수기': ('KITCHEN', '주방가전'),
        '제습기': ('AIR', '에어컨/에어케어'),
        '안마의자': ('LIVING', '생활가전'),
        '식물생활가전': ('LIVING', '생활가전'),
    }

    # ============================================================
    # 공통 필드 필터링 (모든 카테고리)
    # ============================================================
    COMMON_EXCLUDE_FIELDS = {
        '제품명', '상품명', '모델명', '제품군',
        '가격', '정가', '판매가', '할인가', '최대혜택가',
        '이미지URL', '이미지', '사진', '이미지리스트',
        'name', 'model_name', 'product_name',
        'price', 'image_url', 'image',
        '구매혜택안내', '6개월무이자', '최대혜택가구성품',
    }

    def find_category(self, filename):
        """파일명에서 카테고리 찾기"""
        filename_upper = filename.upper()
        
        for key, (code, label) in self.CATEGORY_MAP.items():
            if key in filename or key.upper() in filename_upper:
                return code
        
        # 기본값: TV
        return 'TV'

    def get_category_label(self, category_code):
        """카테고리 코드에서 라벨 가져오기"""
        for key, (code, label) in self.CATEGORY_MAP.items():
            if code == category_code:
                return label
        return category_code

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true", help="Dry run mode (no DB writes)")
        parser.add_argument("--limit", type=int, default=0, help="Limit rows per CSV (0=all)")

    def handle(self, *args, **options):
        """메인 핸들러"""
        self.dry_run = options.get('dry_run', False)
        self.limit = options.get('limit', 0)
        
        base_dir = Path(__file__).parent.parent.parent.parent / 'data'
        
        # 폴더 존재 확인
        if not base_dir.exists():
            self.stdout.write(self.style.ERROR(f"[ERROR] {base_dir} 폴더가 없습니다"))
            return
        
        spec_dir = base_dir / '제품스펙'
        
        if not spec_dir.exists():
            self.stdout.write(self.style.ERROR(f"[ERROR] {spec_dir} 폴더가 없습니다"))
            return
        
        # 모든 CSV 파일 찾기 (재귀적으로)
        csv_files = []
        for pattern in ['**/*.csv', '*.csv']:
            csv_files.extend(spec_dir.glob(pattern))
        
        # 중복 제거 및 정렬
        csv_files = sorted(set(csv_files))
        
        if not csv_files:
            self.stdout.write(self.style.ERROR(f"[ERROR] {spec_dir}에 CSV 파일이 없습니다"))
            return
        
        self.stdout.write(self.style.SUCCESS(f"\n[INFO] 총 {len(csv_files)}개 파일 발견\n"))
        
        total_products = 0
        category_stats = {}
        
        # ============================================================
        # 각 CSV 파일 처리
        # ============================================================
        for filepath in csv_files:
            category = self.find_category(filepath.name)
            count = self.import_csv_file(filepath, category)
            total_products += count
            
            if category not in category_stats:
                category_stats[category] = 0
            category_stats[category] += count
            
            self.stdout.write(
                self.style.SUCCESS(
                    f"[SUCCESS] {filepath.name}: {count}개 제품 import -> {category}"
                )
            )
        
        # 통계 출력
        self.print_statistics(category_stats, total_products)

    def _get_main_category_from_filepath(self, filepath, category):
        """
        파일명에서 MAIN_CATEGORY 추출
        예: "TV.csv" -> "TV", "냉장고.csv" -> "냉장고"
        """
        filename = filepath.name if hasattr(filepath, 'name') else str(filepath)
        filename_lower = filename.lower()
        
        # 파일명 기반으로 MAIN_CATEGORY 추출
        for key, (django_cat, display_name) in self.CATEGORY_MAP.items():
            if key.lower() in filename_lower:
                return key
        
        # 매핑이 없으면 카테고리명 그대로 사용
        return category
    
    def import_csv_file(self, filepath, category):
        """CSV 파일을 JSON 필드 방식으로 import"""
        count = 0
        errors = []
        
        try:
            with open(filepath, 'r', encoding='utf-8-sig', newline='') as f:
                reader = csv.DictReader(f)
                
                if not reader.fieldnames:
                    self.stdout.write(self.style.ERROR(f"[ERROR] {filepath.name}: 헤더 없음"))
                    return 0
                
                for idx, row in enumerate(reader, start=2):  # 2부터 시작 (헤더 제외)
                    # limit 체크 (파일 레벨)
                    if self.limit and count >= self.limit:
                        break
                    
                    try:
                        # ============================================================
                        # 1. 기본 필드 추출 (모든 CSV에 공통)
                        # ============================================================
                        name = self._extract_name(row)
                        if not name:
                            continue
                        
                        model_number = self._extract_model_number(row, name)
                        price = self._extract_price(row)
                        discount_price = self._extract_discount_price(row)
                        image_url = self._extract_image_url(row)
                        description = self._extract_description(row)
                        
                        # limit 체크
                        if self.limit and count >= self.limit:
                            break
                        
                        if self.dry_run:
                            # Dry run 모드: 실제 저장 없이 출력만
                            specs_dict = self._build_specs_dict(row, category)
                            self.stdout.write(f"  [DRY RUN] {name} ({model_number}) -> {category}")
                            count += 1
                            continue
                        
                        # ============================================================
                        # 2. Product 생성 또는 업데이트
                        # ============================================================
                        product, created = Product.objects.update_or_create(
                            model_number=model_number,
                            defaults={
                                'name': name.strip(),
                                'category': category,
                                'price': price,
                                'discount_price': discount_price if discount_price else None,
                                'image_url': image_url.strip() if image_url else '',
                                'description': description.strip() if description else '',
                                'is_active': True,
                            }
                        )
                        
                        # ============================================================
                        # 3. 스펙을 JSON으로 저장 (카테고리별 유연하게)
                        # ============================================================
                        specs_dict = self._build_specs_dict(row, category)
                        # 파일명 기반으로 MAIN_CATEGORY 업데이트
                        main_category = self._get_main_category_from_filepath(filepath, category)
                        specs_dict['MAIN_CATEGORY'] = main_category
                        specs_json = json.dumps(specs_dict, ensure_ascii=False)
                        
                        # ============================================================
                        # 4. ProductSpec 생성 또는 업데이트
                        # ============================================================
                        ProductSpec.objects.update_or_create(
                            product=product,
                            defaults={
                                'source': filepath.name,
                                'spec_json': specs_json,
                            }
                        )
                        
                        count += 1
                    
                    except Exception as e:
                        error_msg = f"행 {idx} 처리 오류: {str(e)[:100]}"
                        errors.append(error_msg)
                        if len(errors) <= 5:  # 처음 5개만 출력
                            self.stdout.write(self.style.WARNING(f"  [WARNING] {error_msg}"))
                        continue
        
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"[ERROR] {filepath.name} 읽기 실패: {e}")
            )
            return 0
        
        if errors:
            self.stdout.write(self.style.WARNING(f"  [WARNING] 총 {len(errors)}개 오류 발생"))
        
        return count

    # ============================================================
    # 필드 추출 헬퍼 함수들
    # ============================================================

    def _extract_name(self, row):
        """제품명 추출"""
        for field in ['제품명', '상품명', 'product_name', 'name']:
            if field in row and row[field] and str(row[field]).strip():
                return str(row[field]).strip()
        return None

    def _extract_model_number(self, row, default_name):
        """모델명 추출 (없으면 제품명 사용)"""
        for field in ['모델명', 'model_number', 'model', '제품코드']:
            if field in row and row[field] and str(row[field]).strip():
                return str(row[field]).strip()
        # 모델명이 없으면 제품명에서 추출 시도
        if default_name:
            # 제품명에서 모델명 패턴 추출 (예: "LG OLED55C5" -> "55C5")
            match = re.search(r'([A-Z0-9]{3,})', default_name)
            if match:
                return match.group(1)
        return default_name or 'UNKNOWN'

    def _extract_price(self, row):
        """가격 추출"""
        for field in ['판매가', '가격', '정가', 'price', '정상가']:
            if field in row and row[field]:
                try:
                    price_str = str(row[field]).replace(',', '').replace('원', '').strip()
                    # 숫자만 추출
                    price_match = re.search(r'(\d+)', price_str)
                    if price_match:
                        return int(price_match.group(1))
                except (ValueError, AttributeError):
                    continue
        return 0

    def _extract_discount_price(self, row):
        """할인가 추출"""
        for field in ['최대혜택가', '할인가', 'discount_price', '실제가격']:
            if field in row and row[field]:
                try:
                    price_str = str(row[field]).replace(',', '').replace('원', '').strip()
                    price_match = re.search(r'(\d+)', price_str)
                    if price_match:
                        return int(price_match.group(1))
                except (ValueError, AttributeError):
                    continue
        return None

    def _extract_image_url(self, row):
        """이미지 URL 추출"""
        for field in ['이미지리스트', '이미지URL', '이미지', 'image_url', 'image']:
            if field in row and row[field]:
                value = str(row[field]).strip()
                if value:
                    # 리스트 형태인 경우 첫 번째 이미지 추출
                    if value.startswith('['):
                        try:
                            import ast
                            img_list = ast.literal_eval(value)
                            if isinstance(img_list, list) and img_list:
                                return str(img_list[0])
                        except:
                            pass
                    return value
        return ''

    def _extract_description(self, row):
        """설명 추출"""
        for field in ['구매혜택안내', '설명', 'description', '상세설명']:
            if field in row and row[field]:
                return str(row[field]).strip()
        return ''

    def _build_specs_dict(self, row, category):
        """
        카테고리별 스펙 딕셔너리 생성
        
        JSON 구조:
        {
            "category": "TV",
            "MAIN_CATEGORY": "TV",  # 파일명 기반 MAIN_CATEGORY
            "common": { ... },
            "specific": { ... }
        }
        """
        # 파일명에서 MAIN_CATEGORY 추출 (filepath는 _build_specs_dict 호출 시 전달 필요)
        # 일단 category 기반으로 추출
        main_category = self._get_main_category_from_category(category)
        
        specs = {
            "category": category,
            "MAIN_CATEGORY": main_category,  # MAIN_CATEGORY 추가
            "common": {},
            "specific": {}
        }
        
        # 모든 필드 순회
        for key, value in row.items():
            # 빈 값 무시
            if not value or str(value).strip() == '':
                continue
            
            # 공통 필드 제외
            if key in self.COMMON_EXCLUDE_FIELDS:
                continue
            
            # ============================================================
            # 카테고리별 필드 분류
            # ============================================================
            
            # TV 카테고리
            if category == 'TV':
                if any(x in key for x in ['해상도', '패널', '주사', '밝기', '응답', '화면', '스크린']):
                    specs["specific"][key] = str(value).strip()
                else:
                    specs["common"][key] = str(value).strip()
            
            # 주방가전 (냉장고, 식기세척기 등)
            elif category == 'KITCHEN':
                if any(x in key for x in ['용량', '에너지', '냉동', '냉장', '온도', '버너', '출력', '모드']):
                    specs["specific"][key] = str(value).strip()
                else:
                    specs["common"][key] = str(value).strip()
            
            # 생활가전 (세탁기, 청소기 등)
            elif category == 'LIVING':
                if any(x in key for x in ['세탁', '용량', '회전', '드럼', '모드', '흡입', '필터', '무게']):
                    specs["specific"][key] = str(value).strip()
                else:
                    specs["common"][key] = str(value).strip()
            
            # 에어컨/에어케어
            elif category == 'AIR':
                if any(x in key for x in ['CADR', '필터', '면적', '음', '풍량', '냉방', '에너지', '소음']):
                    specs["specific"][key] = str(value).strip()
                else:
                    specs["common"][key] = str(value).strip()
            
            # 기본 (모든 필드를 common에 저장)
            else:
                specs["common"][key] = str(value).strip()
        
        return specs

    def print_statistics(self, category_stats, total_products):
        """카테고리별 통계 출력"""
        self.stdout.write(self.style.SUCCESS("\n" + "="*60))
        self.stdout.write(self.style.SUCCESS("[STATS] 카테고리별 제품 통계"))
        self.stdout.write(self.style.SUCCESS("="*60))
        
        for category, count in sorted(category_stats.items(), key=lambda x: x[1], reverse=True):
            label = self.get_category_label(category)
            bar_length = min(30, count // 2) if count > 0 else 0
            bar = "#" * bar_length
            self.stdout.write(f"  {label:20s} {bar:30s} {count:3d}개")
        
        self.stdout.write(self.style.SUCCESS("="*60))
        self.stdout.write(
            self.style.SUCCESS(f"\n[SUCCESS] 총 {total_products}개 제품 import 완료!\n")
        )
        
        # DB에서 최종 확인
        if not self.dry_run:
            db_count = Product.objects.count()
            spec_count = ProductSpec.objects.count()
            self.stdout.write(self.style.SUCCESS(f"[DB] Product: {db_count}개, ProductSpec: {spec_count}개\n"))
        else:
            self.stdout.write(self.style.WARNING("[DRY RUN] 실제로는 데이터가 저장되지 않았습니다.\n"))

