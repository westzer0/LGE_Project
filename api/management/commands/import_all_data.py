import os
from django.core.management.base import BaseCommand
from django.core.management import call_command


class Command(BaseCommand):
    help = "Import all CSV data files automatically"

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true", help="Dry run mode")
        parser.add_argument("--limit", type=int, default=0, help="Limit rows per CSV (0=all)")

    def handle(self, *args, **opts):
        dry_run = opts["dry_run"]
        limit = opts["limit"]

        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
        data_dir = os.path.join(base_dir, "data")

        if not os.path.exists(data_dir):
            self.stdout.write(self.style.ERROR(f"Data directory not found: {data_dir}"))
            return

        # CSV 파일 목록
        csv_files = {
            "TV": "TV_제품스펙.csv",
            "LIVING": "오디오_제품스펙.csv",
            "LIVING": "홈오디오_제품스펙.csv",
            "TV": "스탠바이미_제품스펙.csv",
            "TV": "프로젝터_제품스펙.csv",
            "TV": "상업용 디스플레이_제품스펙.csv",
        }

        self.stdout.write(self.style.SUCCESS("=== CSV 데이터 자동 Import 시작 ===\n"))

        # 제품 스펙 CSV import
        imported_categories = {}
        for category, filename in csv_files.items():
            csv_path = os.path.join(data_dir, filename)
            if os.path.exists(csv_path):
                self.stdout.write(f"[IMPORT] Importing: {filename} (Category: {category})")
                try:
                    call_command(
                        "import_specs",
                        csv=csv_path,
                        category=category,
                        limit=limit,
                        dry_run=dry_run,
                    )
                    if category not in imported_categories:
                        imported_categories[category] = 0
                    imported_categories[category] += 1
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"  [ERROR] Error: {e}"))
            else:
                self.stdout.write(self.style.WARNING(f"  [WARNING] File not found: {filename}"))

        # 사용자 샘플 CSV import
        user_csv = os.path.join(data_dir, "recommendation_dummy_data.csv")
        if os.path.exists(user_csv):
            self.stdout.write(f"\n[IMPORT] Importing: recommendation_dummy_data.csv")
            try:
                call_command(
                    "import_user_samples",
                    csv=user_csv,
                    limit=limit,
                    dry_run=dry_run,
                )
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"  [ERROR] Error: {e}"))
        else:
            self.stdout.write(self.style.WARNING(f"  [WARNING] File not found: recommendation_dummy_data.csv"))

        self.stdout.write(self.style.SUCCESS("\n=== Import 완료 ==="))
        if dry_run:
            self.stdout.write(self.style.WARNING("[DRY RUN] 실제로는 데이터가 저장되지 않았습니다."))

