#!/usr/bin/env python3
"""
프론트엔드 스타일 검증 스크립트

이 스크립트는 프론트엔드 템플릿 파일들이 스타일 가이드를 준수하는지 검증합니다.
백엔드 개발 시 이 스크립트를 실행하여 스타일 무결성을 확인하세요.

사용법:
    python validate_frontend_style.py
"""

import os
import re
import sys
from pathlib import Path

# 프로젝트 루트 디렉토리
PROJECT_ROOT = Path(__file__).parent
TEMPLATES_DIR = PROJECT_ROOT / "api" / "templates"

# 필수 스타일 규칙
REQUIRED_STYLES = {
    "breadcrumb_padding": {
        "pattern": r"\.breadcrumb-nav\s*\{[^}]*padding:\s*7px\s+0px\s+0px",
        "message": "❌ Breadcrumb padding이 '7px 0px 0px'가 아닙니다",
        "required_files": [
            "main.html",
            "mypage.html",
            "onboarding.html",
            "onboarding_step2.html",
            "onboarding_step3.html",
            "onboarding_step4.html",
            "onboarding_step5.html",
            "onboarding_step6.html",
            "onboarding_step7.html",
            "other_recommendations.html",
        ]
    },
    "onboarding_steps": {
        "pattern": r"(\d+)단계\s*/\s*7단계",
        "message": "❌ 온보딩 단계가 '7단계'로 표시되지 않습니다",
        "required_files": [
            "onboarding.html",
            "onboarding_step2.html",
            "onboarding_step3.html",
            "onboarding_step4.html",
            "onboarding_step5.html",
            "onboarding_step6.html",
            "onboarding_step7.html",
        ]
    },
    "progress_bar_widths": {
        "patterns": {
            "onboarding.html": r"width:\s*14\.29%",
            "onboarding_step2.html": r"width:\s*28\.57%",
            "onboarding_step3.html": r"width:\s*42\.86%",
            "onboarding_step4.html": r"width:\s*57\.14%",
            "onboarding_step5.html": r"width:\s*71\.43%",
            "onboarding_step6.html": r"width:\s*85\.7%",
            "onboarding_step7.html": r"width:\s*100%",
        },
        "message": "❌ 프로그레스 바 너비가 올바르지 않습니다",
    },
    "other_recommendations_padding": {
        "pattern": r"padding:\s*0\s+60px\s+0\s+20px",
        "message": "❌ other_recommendations.html의 padding이 '0 60px 0 20px'가 아닙니다",
        "required_files": ["other_recommendations.html"]
    }
}

# 검증 결과
validation_results = {
    "passed": [],
    "failed": [],
    "warnings": []
}


def validate_file(file_path, rule_name, pattern, message):
    """파일이 특정 패턴을 만족하는지 검증"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        if re.search(pattern, content, re.MULTILINE | re.DOTALL):
            return True, None
        else:
            return False, message
    except FileNotFoundError:
        return False, f"파일을 찾을 수 없습니다: {file_path}"
    except Exception as e:
        return False, f"오류 발생: {str(e)}"


def validate_breadcrumb_padding():
    """Breadcrumb padding 검증"""
    print("\n📋 Breadcrumb Padding 검증 중...")
    
    for filename in REQUIRED_STYLES["breadcrumb_padding"]["required_files"]:
        file_path = TEMPLATES_DIR / filename
        pattern = REQUIRED_STYLES["breadcrumb_padding"]["pattern"]
        message = REQUIRED_STYLES["breadcrumb_padding"]["message"]
        
        if not file_path.exists():
            validation_results["warnings"].append(f"⚠️  {filename}: 파일이 존재하지 않습니다")
            continue
        
        passed, error = validate_file(file_path, "breadcrumb_padding", pattern, message)
        
        if passed:
            validation_results["passed"].append(f"✅ {filename}: Breadcrumb padding 올바름")
        else:
            validation_results["failed"].append(f"{filename}: {error}")


def validate_onboarding_steps():
    """온보딩 단계 검증"""
    print("\n📋 온보딩 단계 검증 중...")
    
    for filename in REQUIRED_STYLES["onboarding_steps"]["required_files"]:
        file_path = TEMPLATES_DIR / filename
        pattern = REQUIRED_STYLES["onboarding_steps"]["pattern"]
        message = REQUIRED_STYLES["onboarding_steps"]["message"]
        
        if not file_path.exists():
            validation_results["warnings"].append(f"⚠️  {filename}: 파일이 존재하지 않습니다")
            continue
        
        passed, error = validate_file(file_path, "onboarding_steps", pattern, message)
        
        if passed:
            validation_results["passed"].append(f"✅ {filename}: 온보딩 단계 표시 올바름")
        else:
            validation_results["failed"].append(f"{filename}: {error}")


def validate_progress_bar_widths():
    """프로그레스 바 너비 검증"""
    print("\n📋 프로그레스 바 너비 검증 중...")
    
    for filename, pattern in REQUIRED_STYLES["progress_bar_widths"]["patterns"].items():
        file_path = TEMPLATES_DIR / filename
        message = REQUIRED_STYLES["progress_bar_widths"]["message"]
        
        if not file_path.exists():
            validation_results["warnings"].append(f"⚠️  {filename}: 파일이 존재하지 않습니다")
            continue
        
        passed, error = validate_file(file_path, "progress_bar_widths", pattern, message)
        
        if passed:
            validation_results["passed"].append(f"✅ {filename}: 프로그레스 바 너비 올바름")
        else:
            validation_results["failed"].append(f"{filename}: {error}")


def validate_other_recommendations_padding():
    """other_recommendations.html padding 검증"""
    print("\n📋 other_recommendations.html Padding 검증 중...")
    
    filename = "other_recommendations.html"
    file_path = TEMPLATES_DIR / filename
    pattern = REQUIRED_STYLES["other_recommendations_padding"]["pattern"]
    message = REQUIRED_STYLES["other_recommendations_padding"]["message"]
    
    if not file_path.exists():
        validation_results["warnings"].append(f"⚠️  {filename}: 파일이 존재하지 않습니다")
        return
    
    passed, error = validate_file(file_path, "other_recommendations_padding", pattern, message)
    
    if passed:
        validation_results["passed"].append(f"✅ {filename}: Padding 올바름")
    else:
        validation_results["failed"].append(f"{filename}: {error}")


def print_results():
    """검증 결과 출력"""
    print("\n" + "="*60)
    print("프론트엔드 스타일 검증 결과")
    print("="*60)
    
    if validation_results["passed"]:
        print("\n✅ 통과한 검증:")
        for result in validation_results["passed"]:
            print(f"  {result}")
    
    if validation_results["warnings"]:
        print("\n⚠️  경고:")
        for warning in validation_results["warnings"]:
            print(f"  {warning}")
    
    if validation_results["failed"]:
        print("\n❌ 실패한 검증:")
        for failure in validation_results["failed"]:
            print(f"  {failure}")
        print("\n" + "="*60)
        print("❌ 스타일 검증 실패!")
        print("FRONTEND_STYLE_GUIDE.md를 참고하여 수정하세요.")
        print("="*60)
        return False
    else:
        print("\n" + "="*60)
        print("✅ 모든 스타일 검증 통과!")
        print("="*60)
        return True


def main():
    """메인 함수"""
    print("🔍 프론트엔드 스타일 검증 시작...")
    print(f"📁 템플릿 디렉토리: {TEMPLATES_DIR}")
    
    # 각 검증 실행
    validate_breadcrumb_padding()
    validate_onboarding_steps()
    validate_progress_bar_widths()
    validate_other_recommendations_padding()
    
    # 결과 출력 및 반환
    success = print_results()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
