#!/usr/bin/env python
# -*- coding: utf-8 -*-
import subprocess
import sys
import os

os.chdir(r"c:\Users\134\Desktop\DX Project")

print("=" * 60)
print("Git Commit Verification")
print("=" * 60)

# 1. Fetch and pull
print("\n1. Fetching and pulling from origin/main...")
try:
    result = subprocess.run(["git", "fetch", "origin"], capture_output=True, text=True, encoding='utf-8', errors='ignore')
    if result.returncode == 0:
        print("   ✓ Fetch completed")
    else:
        print(f"   ✗ Fetch failed: {result.stderr}")
except Exception as e:
    print(f"   ✗ Error: {e}")

try:
    result = subprocess.run(["git", "pull", "origin", "main"], capture_output=True, text=True, encoding='utf-8', errors='ignore')
    if result.returncode == 0:
        print("   ✓ Pull completed")
        if result.stdout.strip():
            print(f"   Output: {result.stdout.strip()}")
    else:
        print(f"   ✗ Pull failed: {result.stderr}")
except Exception as e:
    print(f"   ✗ Error: {e}")

# 2. Check for commit c5fda2a
print("\n2. Checking for commit c5fda2a...")
try:
    result = subprocess.run(["git", "log", "--all", "--oneline"], capture_output=True, text=True, encoding='utf-8', errors='ignore')
    commits = result.stdout.split('\n')
    found_commits = [c for c in commits if 'c5fda2a' in c]
    
    if found_commits:
        print(f"   ✓ Found {len(found_commits)} commit(s) containing c5fda2a:")
        for commit in found_commits[:3]:
            print(f"     {commit}")
    else:
        print("   ✗ Commit c5fda2a NOT found in local repository")
except Exception as e:
    print(f"   ✗ Error: {e}")

# 3. Show recent local commits
print("\n3. Recent local commits (HEAD):")
try:
    result = subprocess.run(["git", "log", "--oneline", "-10"], capture_output=True, text=True, encoding='utf-8', errors='ignore')
    print(result.stdout)
except Exception as e:
    print(f"   ✗ Error: {e}")

# 4. Show recent remote commits
print("\n4. Recent remote commits (origin/main):")
try:
    result = subprocess.run(["git", "log", "origin/main", "--oneline", "-10"], capture_output=True, text=True, encoding='utf-8', errors='ignore')
    print(result.stdout)
except Exception as e:
    print(f"   ✗ Error: {e}")

# 5. Check if local is behind
print("\n5. Checking if local is behind remote...")
try:
    result = subprocess.run(["git", "log", "HEAD..origin/main", "--oneline"], capture_output=True, text=True, encoding='utf-8', errors='ignore')
    if result.stdout.strip():
        print("   ⚠ Local is behind remote. Missing commits:")
        print(result.stdout)
    else:
        print("   ✓ Local is up to date with remote")
except Exception as e:
    print(f"   ✗ Error: {e}")

# 6. Try to show commit c5fda2a directly
print("\n6. Attempting to show commit c5fda2a...")
try:
    result = subprocess.run(["git", "show", "c5fda2a", "--oneline", "-s"], capture_output=True, text=True, encoding='utf-8', errors='ignore')
    if result.returncode == 0:
        print(f"   ✓ Commit exists: {result.stdout.strip()}")
    else:
        print(f"   ✗ Commit not found: {result.stderr.strip()}")
except Exception as e:
    print(f"   ✗ Error: {e}")

print("\n" + "=" * 60)

# Save results to file
with open("verify_commit_result.txt", "w", encoding="utf-8") as f:
    f.write("Git Commit Verification Results\n")
    f.write("=" * 60 + "\n\n")
    
    # Fetch and pull results
    f.write("1. Fetch and Pull:\n")
    result = subprocess.run(["git", "fetch", "origin"], capture_output=True, text=True, encoding='utf-8', errors='ignore')
    f.write(f"   Fetch: {'Success' if result.returncode == 0 else 'Failed'}\n")
    
    result = subprocess.run(["git", "pull", "origin", "main"], capture_output=True, text=True, encoding='utf-8', errors='ignore')
    f.write(f"   Pull: {'Success' if result.returncode == 0 else 'Failed'}\n")
    if result.stdout.strip():
        f.write(f"   Output: {result.stdout.strip()}\n")
    
    # Check for commit
    f.write("\n2. Commit c5fda2a check:\n")
    result = subprocess.run(["git", "log", "--all", "--oneline"], capture_output=True, text=True, encoding='utf-8', errors='ignore')
    commits = result.stdout.split('\n')
    found_commits = [c for c in commits if 'c5fda2a' in c]
    if found_commits:
        f.write(f"   ✓ Found: {found_commits[0]}\n")
    else:
        f.write("   ✗ Not found\n")
    
    # Recent commits
    f.write("\n3. Recent local commits:\n")
    result = subprocess.run(["git", "log", "--oneline", "-5"], capture_output=True, text=True, encoding='utf-8', errors='ignore')
    f.write(result.stdout)
    
    f.write("\n4. Recent remote commits:\n")
    result = subprocess.run(["git", "log", "origin/main", "--oneline", "-5"], capture_output=True, text=True, encoding='utf-8', errors='ignore')
    f.write(result.stdout)
    
    f.write("\n5. Missing commits (HEAD..origin/main):\n")
    result = subprocess.run(["git", "log", "HEAD..origin/main", "--oneline"], capture_output=True, text=True, encoding='utf-8', errors='ignore')
    f.write(result.stdout if result.stdout.strip() else "   None (up to date)\n")

print("\nResults saved to verify_commit_result.txt")
