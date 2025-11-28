import csv, json, ast, re
from django.core.management.base import BaseCommand
from api.models import Product, ProductSpec


def money_to_float(v):
    if v is None:
        return 0.0
    s = str(v)
    digits = re.sub(r"[^0-9]", "", s)
    return float(digits) if digits else 0.0


def first_image(s):
    if not s:
        return ""
    s = str(s).strip()
    try:
        if s.startswith("["):
            arr = ast.literal_eval(s)
            if isinstance(arr, list) and arr:
                return str(arr[0])
    except Exception:
        pass
    return s


class Command(BaseCommand):
    help = "Import Product + ProductSpec(raw JSON) from CSV"

    def add_arguments(self, parser):
        parser.add_argument("--csv", required=True, help="CSV path")
        parser.add_argument("--limit", type=int, default=0, help="0=all")
        parser.add_argument("--category", default="", help="override category (e.g., TV)")
        parser.add_argument("--source", default="", help="source label (e.g., TV_제품스펙.csv)")

    def handle(self, *args, **opts):
        path = opts["csv"]
        limit = opts["limit"]
        force_category = opts["category"].strip()
        source = opts["source"].strip() or path.split("\\")[-1].split("/")[-1]

        created_p, updated_p = 0, 0
        created_s, updated_s = 0, 0

        try:
            f = open(path, "r", encoding="utf-8-sig", newline="")
        except FileNotFoundError:
            self.stdout.write(self.style.ERROR(f"File not found: {path}"))
            return
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error opening file: {e}"))
            return

        with f:
            reader = csv.DictReader(f)
            for idx, row in enumerate(reader):
                if limit and idx >= limit:
                    break

                model_number = row.get("모델명", "").strip()
                if not model_number:
                    continue

                category = force_category or row.get("제품군", "").strip() or "TV"
                # 카테고리 유효성 검사 (CATEGORY_CHOICES에 없는 경우 기본값 사용)
                valid_categories = [choice[0] for choice in Product.CATEGORY_CHOICES]
                if category not in valid_categories:
                    self.stdout.write(self.style.WARNING(
                        f"Invalid category '{category}' for {model_number}, using 'TV'"
                    ))
                    category = "TV"
                
                name = row.get("제품명", "").strip() or model_number
                description = row.get("구매혜택안내", "").strip()
                
                sale_price = row.get("판매가", "")
                price = money_to_float(sale_price)
                
                best_price = row.get("최대혜택가", "")
                discount_price = money_to_float(best_price) if best_price and best_price.strip() else None

                image_list = row.get("이미지리스트", "")
                image_url = first_image(image_list)

                product, is_created = Product.objects.update_or_create(
                    model_number=model_number,
                    defaults={
                        "category": category,
                        "name": name,
                        "description": description,
                        "price": price,
                        "discount_price": discount_price,
                        "image_url": image_url,
                    },
                )
                created_p += 1 if is_created else 0
                updated_p += 0 if is_created else 1

                raw_json = json.dumps(row, ensure_ascii=False)
                spec, s_created = ProductSpec.objects.update_or_create(
                    product=product,
                    defaults={
                        "source": source,
                        "spec_json": raw_json,
                    },
                )
                created_s += 1 if s_created else 0
                updated_s += 0 if s_created else 1

        self.stdout.write(self.style.SUCCESS(
            f"Done. Product(created={created_p}, updated={updated_p}), "
            f"Spec(created={created_s}, updated={updated_s})"
        ))
