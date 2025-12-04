#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
깨진 커밋 메시지 수정 스크립트
"""
import subprocess
import os
import sys

# 커밋 메시지 매핑
COMMIT_MESSAGES = {
    '75904086becfce396e99402cb6dfc100ab3a5cc8': """feat: Add taste-based scoring logic and recommendation phrase generation

- Add taste-based scoring logic system
- Add recommendation phrase generation based on taste combinations
- Add analysis commands for taste recommendations
- Add scoring logic explanation and JSON data
- Update recommendation engine with taste scoring""",

    '57880e5a23913a3eb6438a59622be6a7e59dd242': """feat: Add main page integration, AI chatbot, API key configuration

- Add main page template (main.html)
- Add AI chatbot functionality (ai-chatbot.js)
- Add API key configuration using python-dotenv (.env file)
- Improve Kakao SDK integration (error handling, loading logic)
- Improve recommendation logic (result formatting, error handling)
- Add documentation (DRF guide, server start guide, view products guide)
- Add environment setup files (env.example)""",

    'ca8c15bb196cdcf8ac2e6ff35c945cfa4695fc5b': """merge: Main page integration and banner image application (previous commit recovery)

- Add banner images (banner2.png)
- Update main.html template
- Add backup files from previous commit""",

    'a122c68e44e320da4b4901bd455df4805d347b9f': """merge: Main page integration and image assets addition

- Add import excel command
- Add product specs migration
- Add banner and icon images
- Add backup files from previous commits
- Update views and URLs"""
}

def get_commit_hash(short_hash):
    """짧은 해시를 전체 해시로 변환"""
    try:
        result = subprocess.run(
            ['git', 'rev-parse', short_hash],
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout.strip()
    except:
        return None

def fix_commit_message(commit_hash, new_message):
    """커밋 메시지 수정"""
    # 메시지를 임시 파일에 저장
    temp_file = 'temp_commit_msg.txt'
    with open(temp_file, 'w', encoding='utf-8') as f:
        f.write(new_message)
    
    try:
        # git commit --amend 사용 (현재 HEAD인 경우)
        # 또는 git rebase를 사용해야 함
        print(f"커밋 {commit_hash[:8]} 메시지 수정 필요")
        print(f"새 메시지: {new_message[:50]}...")
        return True
    except Exception as e:
        print(f"오류: {e}")
        return False
    finally:
        if os.path.exists(temp_file):
            os.remove(temp_file)

def main():
    print("깨진 커밋 메시지 수정")
    print("=" * 50)
    
    # 각 커밋에 대해 메시지 확인
    for short_hash, message in [
        ('7590408', COMMIT_MESSAGES['75904086becfce396e99402cb6dfc100ab3a5cc8']),
        ('57880e5', COMMIT_MESSAGES['57880e5a23913a3eb6438a59622be6a7e59dd242']),
        ('ca8c15b', COMMIT_MESSAGES['ca8c15bb196cdcf8ac2e6ff35c945cfa4695fc5b']),
        ('a122c68', COMMIT_MESSAGES['a122c68e44e320da4b4901bd455df4805d347b9f']),
    ]:
        full_hash = get_commit_hash(short_hash)
        if full_hash and full_hash in COMMIT_MESSAGES:
            print(f"\n커밋 {short_hash} 발견: {full_hash[:16]}...")
            print("수정 방법:")
            print(f"  git rebase -i {short_hash}^")
            print(f"  (커밋 라인에서 'pick'을 'reword'로 변경)")
            print(f"  (나오는 편집기에서 다음 메시지로 교체):")
            print(f"\n{message}\n")
            print("-" * 50)

if __name__ == '__main__':
    main()

