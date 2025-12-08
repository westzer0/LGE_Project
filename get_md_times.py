#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import glob
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

times = []
for f in md_files:
    if os.path.exists(f):
        mtime = os.path.getmtime(f)
        dt = datetime.fromtimestamp(mtime)
        times.append((dt, f))

times.sort(reverse=True)

print("=" * 60)
print("문서 파일들의 마지막 수정 시간 (최신순)")
print("=" * 60)
for dt, f in times:
    print(f"{dt.strftime('%Y-%m-%d %H:%M:%S')} - {f}")
print("=" * 60)
print(f"\n가장 최근 수정된 문서: {times[0][1]}")
print(f"최근 수정 시간: {times[0][0].strftime('%Y-%m-%d %H:%M:%S')}")
