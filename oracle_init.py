"""
Oracle Instant Client 초기화 모듈
Django에서 Thick 모드를 사용하기 위해 필요한 초기화 코드
"""
import os
import oracledb
from pathlib import Path


def init_oracle_client():
    """
    Oracle Instant Client 초기화 (Thick 모드 활성화)
    이 함수는 한 번만 호출되어야 합니다.
    우선순위:
    1. .env의 ORACLE_INSTANT_CLIENT_PATH
    2. 프로젝트 내 libs/oracle_client/ (상대 경로)
    3. PATH 환경변수
    4. 시스템 기본
    """
    try:
        # 1. .env 파일에서 경로 지정
        instant_client_path = os.environ.get('ORACLE_INSTANT_CLIENT_PATH')
        
        if instant_client_path:
            instant_client_path = Path(instant_client_path)
            if instant_client_path.exists():
                try:
                    oracledb.init_oracle_client(lib_dir=str(instant_client_path))
                    print(f"[Oracle] Thick 모드 활성화 완료: {instant_client_path}")
                    return
                except Exception as e:
                    error_msg = str(e).lower()
                    if "already initialized" in error_msg:
                        return  # 이미 초기화됨
                    # 경로가 잘못되었을 수 있으니 다음 방법 시도
        
        # 2. 프로젝트 내 libs/oracle_client/ 경로 시도 (상대 경로)
        base_dir = Path(__file__).resolve().parent
        project_client_path = base_dir / "libs" / "oracle_client"
        if project_client_path.exists() and (project_client_path / "oci.dll").exists():
            try:
                oracledb.init_oracle_client(lib_dir=str(project_client_path))
                print(f"[Oracle] Thick 모드 활성화 완료 (프로젝트 내): {project_client_path}")
                return
            except Exception as e:
                error_msg = str(e).lower()
                if "already initialized" in error_msg:
                    return  # 이미 초기화됨
        
        # 3. PATH에서 자동으로 찾기 시도
        path_dirs = os.environ.get("PATH", "").split(os.pathsep)
        
        for path_dir in path_dirs:
            if not path_dir:
                continue
            oci_dll = Path(path_dir) / "oci.dll"
            if oci_dll.exists():
                try:
                    oracledb.init_oracle_client(lib_dir=path_dir)
                    print(f"[Oracle] Thick 모드 활성화 완료 (PATH에서 자동 감지): {path_dir}")
                    return
                except Exception as e:
                    error_msg = str(e).lower()
                    if "already initialized" in error_msg:
                        return  # 이미 초기화됨
                    continue
        
        # PATH에서 찾지 못한 경우
        try:
            # PATH 없이도 시도 (시스템에 이미 등록된 경우)
            oracledb.init_oracle_client()
            print("[Oracle] Thick 모드 활성화 완료 (시스템 기본)")
        except Exception as e:
            error_msg = str(e).lower()
            if "already initialized" in error_msg:
                pass  # 이미 초기화됨
            else:
                print(f"[Oracle Warning] Thick 모드 초기화 실패: {e}")
                print("  PATH에서 Oracle Instant Client를 찾을 수 없습니다.")
    except Exception as e:
        error_msg = str(e).lower()
        if "already initialized" in error_msg:
            pass  # 이미 초기화됨, 문제 없음
        else:
            print(f"[Oracle Warning] Thick 모드 초기화 중 오류: {e}")


# 모듈 임포트 시 자동 초기화 (선택 사항)
# Django에서는 manage.py나 wsgi.py에서 명시적으로 호출하는 것을 권장
# AUTO_INIT = os.environ.get('ORACLE_AUTO_INIT', 'false').lower() == 'true'
# if AUTO_INIT:
#     init_oracle_client()

