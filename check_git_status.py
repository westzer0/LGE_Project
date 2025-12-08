import subprocess
import sys
import os

os.chdir(r"c:\Users\Tissue\Desktop\LGE_Project-main")

print("=" * 60)
print("Git Status Check")
print("=" * 60)

# Check git status
print("\n1. Git Status:")
result = subprocess.run(["git", "status"], capture_output=True, text=True, encoding='utf-8', errors='ignore')
print(result.stdout)
if result.stderr:
    print("STDERR:", result.stderr)

# Check modified files
print("\n2. Modified files:")
result = subprocess.run(["git", "diff", "--name-only"], capture_output=True, text=True, encoding='utf-8', errors='ignore')
if result.stdout.strip():
    print(result.stdout)
else:
    print("  No modified files")

# Check staged files
print("\n3. Staged files:")
result = subprocess.run(["git", "diff", "--cached", "--name-only"], capture_output=True, text=True, encoding='utf-8', errors='ignore')
if result.stdout.strip():
    print(result.stdout)
else:
    print("  No staged files")

# Check untracked files
print("\n4. Untracked files:")
result = subprocess.run(["git", "ls-files", "--others", "--exclude-standard"], capture_output=True, text=True, encoding='utf-8', errors='ignore')
if result.stdout.strip():
    print(result.stdout)
else:
    print("  No untracked files")

# Check recent commits
print("\n5. Recent commits:")
result = subprocess.run(["git", "log", "--oneline", "-5"], capture_output=True, text=True, encoding='utf-8', errors='ignore')
print(result.stdout)

print("\n" + "=" * 60)

# Save to file
with open("git_status_result.txt", "w", encoding="utf-8") as f:
    f.write("=" * 60 + "\n")
    f.write("Git Status Check\n")
    f.write("=" * 60 + "\n\n")
    
    result = subprocess.run(["git", "status"], capture_output=True, text=True, encoding='utf-8', errors='ignore')
    f.write("1. Git Status:\n")
    f.write(result.stdout + "\n")
    
    result = subprocess.run(["git", "diff", "--name-only"], capture_output=True, text=True, encoding='utf-8', errors='ignore')
    f.write("\n2. Modified files:\n")
    f.write(result.stdout if result.stdout.strip() else "  No modified files\n")
    
    result = subprocess.run(["git", "diff", "--cached", "--name-only"], capture_output=True, text=True, encoding='utf-8', errors='ignore')
    f.write("\n3. Staged files:\n")
    f.write(result.stdout if result.stdout.strip() else "  No staged files\n")
    
    result = subprocess.run(["git", "ls-files", "--others", "--exclude-standard"], capture_output=True, text=True, encoding='utf-8', errors='ignore')
    f.write("\n4. Untracked files:\n")
    f.write(result.stdout if result.stdout.strip() else "  No untracked files\n")
    
    result = subprocess.run(["git", "log", "--oneline", "-5"], capture_output=True, text=True, encoding='utf-8', errors='ignore')
    f.write("\n5. Recent commits:\n")
    f.write(result.stdout)

print("\nResults saved to git_status_result.txt")

