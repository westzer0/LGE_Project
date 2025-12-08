import subprocess
import sys

def run_git(cmd):
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True, encoding='utf-8', errors='ignore')
    return result.stdout.strip(), result.stderr.strip(), result.returncode

# Check status
stdout, stderr, code = run_git('git status --porcelain')
print("Git Status (porcelain):")
print(stdout if stdout else "(empty - no changes)")
print()

# Check if there are changes to commit
stdout, stderr, code = run_git('git diff --name-only')
modified = stdout.split('\n') if stdout else []
print(f"Modified files: {len([f for f in modified if f])}")
for f in modified[:10]:
    if f:
        print(f"  - {f}")

stdout, stderr, code = run_git('git diff --cached --name-only')
staged = stdout.split('\n') if stdout else []
print(f"\nStaged files: {len([f for f in staged if f])}")
for f in staged[:10]:
    if f:
        print(f"  - {f}")

# Try to commit
print("\nAttempting commit...")
stdout, stderr, code = run_git('git commit -m "Update taste category selector and scoring utilities"')
print(f"Exit code: {code}")
if stdout:
    print(f"STDOUT: {stdout}")
if stderr:
    print(f"STDERR: {stderr}")

