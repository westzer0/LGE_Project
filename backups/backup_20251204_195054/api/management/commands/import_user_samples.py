import csv
import os
from django.core.management.base import BaseCommand
from api.models import UserSample


def safe_int(v):
    if not v or str(v).strip() == "":
        return None
    try:
        return int(float(str(v).strip()))
    except (ValueError, TypeError):
        return None


def safe_float(v):
    if not v or str(v).strip() == "":
        return None
    try:
        return float(str(v).strip())
    except (ValueError, TypeError):
        return None


def safe_str(v, default=""):
    if v is None:
        return default
    s = str(v).strip()
    return s if s else default


class Command(BaseCommand):
    help = "Import UserSample from CSV"

    def add_arguments(self, parser):
        parser.add_argument("--csv", required=True, help="CSV path")
        parser.add_argument("--limit", type=int, default=0, help="0=all")
        parser.add_argument("--dry-run", action="store_true", help="Dry run mode (no DB writes)")

    def handle(self, *args, **opts):
        path = opts["csv"]
        limit = opts["limit"]
        dry_run = opts["dry_run"]

        # 경로 정규화 (상대 경로 처리)
        if not os.path.isabs(path):
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
            path = os.path.join(base_dir, path)

        created, updated = 0, 0
        errors = []

        try:
            f = open(path, "r", encoding="utf-8-sig", newline="")
        except FileNotFoundError:
            self.stdout.write(self.style.ERROR(f"File not found: {path}"))
            return
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error opening file: {e}"))
            return

        with f:
            try:
                reader = csv.DictReader(f)
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Error reading CSV: {e}"))
                return

            for idx, row in enumerate(reader):
                if limit and idx >= limit:
                    break

                try:
                    user_id = safe_str(row.get("user_id", ""))
                    if not user_id:
                        continue

                    if not dry_run:
                        user_sample, is_created = UserSample.objects.update_or_create(
                            user_id=user_id,
                            defaults={
                                "household_size": safe_str(row.get("household_size", "")),
                                "space_type": safe_str(row.get("space_type", "")),
                                "space_purpose": safe_str(row.get("space_purpose", "")),
                                "space_sqm": safe_float(row.get("space_sqm", "")),
                                "space_size_cat": safe_str(row.get("space_size_cat", "")),
                                "style_pref": safe_str(row.get("style_pref", "")),
                                "cooking_freq": safe_str(row.get("cooking_freq", "")),
                                "laundry_pattern": safe_str(row.get("laundry_pattern", "")),
                                "media_pref": safe_str(row.get("media_pref", "")),
                                "pet": safe_str(row.get("pet", "")),
                                "budget_range": safe_str(row.get("budget_range", "")),
                                "payment_pref": safe_str(row.get("payment_pref", "")),
                                "recommended_fridge_l": safe_int(row.get("recommended_fridge_l", "")),
                                "recommended_washer_kg": safe_int(row.get("recommended_washer_kg", "")),
                                "recommended_tv_inch": safe_int(row.get("recommended_tv_inch", "")),
                                "recommended_vacuum": safe_str(row.get("recommended_vacuum", "")),
                                "recommended_oven": safe_str(row.get("recommended_oven", "")),
                                "purchased_items": safe_str(row.get("purchased_items", "")),
                            },
                        )
                        created += 1 if is_created else 0
                        updated += 0 if is_created else 1
                    else:
                        self.stdout.write(f"[DRY RUN] Would create/update: UserSample({user_id})")

                except Exception as e:
                    error_msg = f"Row {idx+2}: {str(e)}"
                    errors.append(error_msg)
                    self.stdout.write(self.style.ERROR(error_msg))
                    continue

        if errors:
            self.stdout.write(self.style.WARNING(f"\nTotal errors: {len(errors)}"))

        if dry_run:
            self.stdout.write(self.style.SUCCESS(f"[DRY RUN] Would process {idx+1} rows"))
        else:
            self.stdout.write(self.style.SUCCESS(
                f"Done. UserSample(created={created}, updated={updated})"
            ))
