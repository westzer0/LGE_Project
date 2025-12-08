import os
import glob
from datetime import datetime
import sys

files = glob.glob('*.md')
times = [(f, os.path.getmtime(f)) for f in files]
times.sort(key=lambda x: x[1], reverse=True)

result = []
result.append("문서 파일들의 마지막 수정 시간 (최신순):\n")
for f, mtime in times:
    dt = datetime.fromtimestamp(mtime)
    result.append(f"{dt.strftime('%Y-%m-%d %H:%M:%S')} - {f}")

output = "\n".join(result)
print(output, file=sys.stdout)
sys.stdout.flush()

with open('md_times_result.txt', 'w', encoding='utf-8') as f:
    f.write(output)
