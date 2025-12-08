import os
import json
from datetime import datetime

md_files = [
    'CSV_TO_ORACLE_GUIDE.md',
    'DATABASE_SCHEMA.md',
    'DEPLOYMENT_GUIDE.md',
    'ONBOARDING_특성_전체_목록.md',
    'ORACLE_DB_QUICK_REFERENCE.md',
    'ORACLE_DB_SETUP_GUIDE_WINDOWS10.md',
    'ORACLE_DB_TROUBLESHOOTING.md',
    'QUICK_START_SQLITE.md',
    'QUICK_START_SQLITE_POWERSHELL.md',
    'README_ENV_SETUP.md',
    'SERVER_START_GUIDE.md',
    'TEST_RESULT_ANALYSIS.md',
    'TEST_TROUBLESHOOTING.md',
    'VERIFICATION_GOALS.md',
]

result = []
for f in md_files:
    if os.path.exists(f):
        mtime = os.path.getmtime(f)
        dt = datetime.fromtimestamp(mtime)
        result.append({
            'file': f,
            'last_modified': dt.strftime('%Y-%m-%d %H:%M:%S'),
            'timestamp': mtime
        })

result.sort(key=lambda x: x['timestamp'], reverse=True)

# Save to JSON
with open('md_file_times.json', 'w', encoding='utf-8') as f:
    json.dump(result, f, indent=2, ensure_ascii=False)

# Also print
print("문서 파일들의 마지막 수정 시간 (최신순):\n")
for item in result:
    print(f"{item['last_modified']} - {item['file']}")
