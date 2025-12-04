from pathlib import Path
from typing import Dict, Iterable, Optional, Tuple

import pandas as pd
from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import transaction
from tqdm import tqdm

from api.models import Product


class Command(BaseCommand):
    help = "제품스펙 폴더의 엑셀 데이터를 Product 모델로 import 합니다."

    COLUMN_MAPPING = {
        '제품군': 'category',
        'URL': 'detail_page_url',
        '제품명': 'product_name',
        '모델명': 'model_name',
        '상태': 'status',
        '정가': 'original_price',
        '판매가': 'price',
        '최대혜택': 'max_benefit',
        '가구매혜택안내': 'benefit_guide',
        '6년구독가격': 'subscription_price_6yr',
        '최대혜택구독가격': 'max_benefit_subscription_price',
        '평점': 'rating',
        '이미지리스트': 'image_url',
    }

    CURRENCY_FIELDS = {
        'original_price',
        'price',
        'subscription_price_6yr',
        'max_benefit_subscription_price',
    }
    FLOAT_FIELDS = {'rating'}

    def add_arguments(self, parser):
        parser.add_argument(
            '--file',
            type=str,
            help='특정 엑셀 파일 경로 (기본: data/제품스펙 하위 모든 엑셀)',
        )
        parser.add_argument(
            '--limit',
            type=int,
            default=0,
            help='파일별 최대 처리 행 수 (0이면 전체)',
        )

    def handle(self, *args, **options):
        limit = options['limit']
        target_files = self._resolve_target_files(options.get('file'))

        if not target_files:
            self.stdout.write(self.style.ERROR("처리할 엑셀 파일을 찾을 수 없습니다."))
            return

        total_created = 0
        total_updated = 0

        for excel_path in target_files:
            created, updated = self._import_file(excel_path, limit)
            total_created += created
            total_updated += updated

            self.stdout.write(
                self.style.SUCCESS(
                    f"[{excel_path.name}] created={created}, updated={updated}"
                )
            )

        self.stdout.write(self.style.SUCCESS("\n=== Import Summary ==="))
        self.stdout.write(f"Total files: {len(target_files)}")
        self.stdout.write(f"Total created: {total_created}")
        self.stdout.write(f"Total updated: {total_updated}")

    def _resolve_target_files(self, file_option: Optional[str]) -> Iterable[Path]:
        base_dir = Path(settings.BASE_DIR) / 'data' / '제품스펙'
        if file_option:
            candidate = Path(file_option)
            if not candidate.is_absolute():
                candidate = (base_dir / file_option).resolve()
            if candidate.exists():
                return [candidate]
            self.stdout.write(self.style.WARNING(f"지정한 파일을 찾을 수 없습니다: {candidate}"))
            return []

        if not base_dir.exists():
            self.stdout.write(self.style.ERROR(f"폴더가 존재하지 않습니다: {base_dir}"))
            return []

        excel_files = [
            path for path in base_dir.rglob('*')
            if path.suffix.lower() in {'.xls', '.xlsx'}
        ]
        return sorted(excel_files)

    def _import_file(self, excel_path: Path, limit: int) -> Tuple[int, int]:
        try:
            df = pd.read_excel(excel_path)
        except Exception as exc:
            self.stdout.write(
                self.style.ERROR(f"[{excel_path.name}] 엑셀 로딩 실패: {exc}")
            )
            return 0, 0

        created_count = 0
        updated_count = 0
        total_rows = len(df)

        progress_bar = tqdm(
            total=total_rows if not limit else min(limit, total_rows),
            desc=excel_path.name,
            unit="rows",
        )

        try:
            processed_rows = 0
            for idx, row in df.iterrows():
                if limit and processed_rows >= limit:
                    break
                processed_rows += 1

                product_data = self._build_product_payload(row)
                if not product_data:
                    progress_bar.update(1)
                    continue

                try:
                    with transaction.atomic():
                        product, created = Product.objects.update_or_create(
                            model_name=product_data['model_name'],
                            defaults=product_data,
                        )
                        if created:
                            created_count += 1
                        else:
                            updated_count += 1
                except Exception as exc:
                    self.stdout.write(
                        self.style.WARNING(
                            f"[{excel_path.name}] 행 {idx + 2} 처리 실패: {exc}"
                        )
                    )
                finally:
                    progress_bar.update(1)
        finally:
            progress_bar.close()

        return created_count, updated_count

    def _build_product_payload(self, row) -> Optional[Dict[str, object]]:
        row_dict = row.to_dict()
        model_name = self._clean_text(row_dict.get('모델명'))
        if not model_name:
            return None

        category = self._clean_category(row_dict.get('제품군'))
        product_name = self._clean_text(row_dict.get('제품명')) or model_name

        payload: Dict[str, object] = {
            'category': category,
            'detail_page_url': self._clean_text(row_dict.get('URL')),
            'product_name': product_name,
            'model_name': model_name,
            'status': self._clean_text(row_dict.get('상태')),
            'original_price': self._clean_currency(row_dict.get('정가')),
            'price': self._clean_currency(row_dict.get('판매가')),
            'max_benefit': self._clean_text(row_dict.get('최대혜택')),
            'benefit_guide': self._clean_text(row_dict.get('가구매혜택안내')),
            'subscription_price_6yr': self._clean_currency(row_dict.get('6년구독가격')),
            'max_benefit_subscription_price': self._clean_currency(
                row_dict.get('최대혜택구독가격')
            ),
            'rating': self._clean_rating(row_dict.get('평점')),
            'image_url': self._clean_text(row_dict.get('이미지리스트')),
            'specs': self._build_specs(row_dict),
            # Legacy 필드 동시 업데이트
            'name': product_name,
            'model_number': model_name,
        }

        # NaN -> 빈 문자열/None 처리
        for key, value in payload.items():
            if isinstance(value, str) and value.lower() == 'nan':
                payload[key] = ''

        return payload

    def _build_specs(self, row_dict: Dict[str, object]) -> Dict[str, object]:
        specs: Dict[str, object] = {}
        for column, value in row_dict.items():
            if column in self.COLUMN_MAPPING:
                continue
            if pd.isna(value):
                continue
            cleaned = self._clean_text(value)
            if cleaned:
                specs[column] = cleaned
        return specs

    def _clean_currency(self, value) -> int:
        if pd.isna(value):
            return 0
        if isinstance(value, (int, float)):
            return int(value)

        digits = ''.join(ch for ch in str(value) if ch.isdigit())
        return int(digits) if digits else 0

    def _clean_rating(self, value) -> float:
        if pd.isna(value):
            return 0.0
        try:
            return float(str(value).replace(',', '.'))
        except (TypeError, ValueError):
            return 0.0

    def _clean_text(self, value) -> str:
        if pd.isna(value):
            return ''
        text = str(value).strip()
        return '' if text.lower() == 'nan' else text

    def _clean_category(self, raw_value) -> str:
        cleaned = self._clean_text(raw_value).upper()
        valid_codes = {choice[0] for choice in Product.CATEGORY_CHOICES}
        if cleaned in valid_codes:
            return cleaned
        return 'TV'

