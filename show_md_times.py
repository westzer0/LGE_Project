import os
from datetime import datetime

docs = ['CSV_TO_ORACLE_GUIDE.md', 'DATABASE_SCHEMA.md', 'DEPLOYMENT_GUIDE.md', 
        'ONBOARDING_특성_전체_목록.md', 'ORACLE_DB_QUICK_REFERENCE.md',
        'ORACLE_DB_SETUP_GUIDE_WINDOWS10.md', 'ORACLE_DB_TROUBLESHOOTING.md',
        'QUICK_START_SQLITE.md', 'QUICK_START_SQLITE_POWERSHELL.md',
        'README_ENV_SETUP.md', 'SERVER_START_GUIDE.md',
        'TEST_RESULT_ANALYSIS.md', 'TEST_TROUBLESHOOTING.md', 'VERIFICATION_GOALS.md']

times = []
for doc in docs:
    if os.path.isfile(doc):
        mtime = os.path.getmtime(doc)
        times.append((datetime.fromtimestamp(mtime), doc))

times.sort(reverse=True)

output_lines = []
output_lines.append("=" * 70)
output_lines.append("문서 파일들의 마지막 수정 시간 (최신순)")
output_lines.append("=" * 70)
for dt, name in times:
    output_lines.append(f"{dt.strftime('%Y-%m-%d %H:%M:%S')} | {name}")

if times:
    output_lines.append("=" * 70)
    output_lines.append(f"가장 최근 수정: {times[0][1]}")
    output_lines.append(f"최근 수정 시간: {times[0][0].strftime('%Y-%m-%d %H:%M:%S')}")
    output_lines.append("=" * 70)

result = "\n".join(output_lines)

# 파일로 저장 (먼저)
with open('md_times_output.txt', 'w', encoding='utf-8') as f:
    f.write(result)

# 콘솔 출력 (나중에)
import sys
sys.stdout.buffer.write(result.encode('utf-8'))
sys.stdout.flush()
