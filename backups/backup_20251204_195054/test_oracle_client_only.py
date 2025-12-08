from api.db.oracle_client import fetch_all_dict

try:
    rows = fetch_all_dict("SELECT user, SYSDATE AS NOW FROM dual")
    print("✅ Oracle 연결 성공!")
    print(f"결과: {rows}")
except Exception as e:
    print(f"❌ 오류 발생: {e}")
    import traceback
    traceback.print_exc()

