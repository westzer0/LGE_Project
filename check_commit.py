import subprocess
import sys
import os

os.chdir(r"c:\Users\134\Desktop\DX Project")

output = []

# Fetch from origin
output.append("Fetching from origin...")
result = subprocess.run(["git", "fetch", "origin"], capture_output=True, text=True)
output.append(result.stdout)
if result.stderr:
    output.append(f"STDERR: {result.stderr}")

# Pull from origin/main
output.append("\nPulling from origin/main...")
result = subprocess.run(["git", "pull", "origin", "main"], capture_output=True, text=True)
output.append(result.stdout)
if result.stderr:
    output.append(f"STDERR: {result.stderr}")

# Check if commit c5fda2a exists
output.append("\nChecking for commit c5fda2a...")
result = subprocess.run(["git", "log", "--all", "--oneline"], capture_output=True, text=True)
commits = result.stdout.split('\n')
found = False
for commit in commits:
    if 'c5fda2a' in commit:
        output.append(f"Found: {commit}")
        found = True

if not found:
    output.append("Commit c5fda2a not found in local repository")

# Show recent commits
output.append("\nRecent commits:")
result = subprocess.run(["git", "log", "--oneline", "-10"], capture_output=True, text=True)
output.append(result.stdout)

# Show remote commits
output.append("\nRemote origin/main commits:")
result = subprocess.run(["git", "log", "origin/main", "--oneline", "-10"], capture_output=True, text=True)
output.append(result.stdout)

# Check if local is behind remote
output.append("\nChecking if local is behind remote...")
result = subprocess.run(["git", "log", "HEAD..origin/main", "--oneline"], capture_output=True, text=True)
if result.stdout.strip():
    output.append("Local is behind remote. Missing commits:")
    output.append(result.stdout)
else:
    output.append("Local is up to date with remote")

# Write to file
with open("check_commit_result.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(output))

# Also print to console
print("\n".join(output))
