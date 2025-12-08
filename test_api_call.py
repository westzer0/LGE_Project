#!/usr/bin/env python
# -*- coding: utf-8 -*-
import requests
import time
import json

# 서버가 시작될 때까지 대기
print("서버 시작 대기 중...")
time.sleep(5)

try:
    url = "http://localhost:8000/api/oracle/test/"
    print(f"\nAPI 호출: {url}")
    print("=" * 60)
    
    response = requests.get(url, timeout=10)
    
    print(f"상태 코드: {response.status_code}")
    print("\n응답 내용:")
    print("=" * 60)
    
    if response.status_code == 200:
        data = response.json()
        print(json.dumps(data, indent=2, ensure_ascii=False))
    else:
        print(response.text)
        
except requests.exceptions.ConnectionError:
    print("❌ 서버에 연결할 수 없습니다. 서버가 실행 중인지 확인하세요.")
except Exception as e:
    print(f"❌ 오류 발생: {e}")
    import traceback
    traceback.print_exc()
