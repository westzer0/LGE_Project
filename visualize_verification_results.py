#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
검증 테스트 결과 시각화
"""

import json
import os
import sys
from pathlib import Path
from datetime import datetime
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import numpy as np

# 한글 폰트 설정
import platform
if platform.system() == 'Windows':
    # Windows에서 사용 가능한 한글 폰트 찾기
    font_list = fm.findSystemFonts(fontpaths=None, fontext='ttf')
    korean_fonts = ['Malgun Gothic', 'NanumGothic', 'Gulim', 'Batang']
    for font_name in korean_fonts:
        try:
            plt.rcParams['font.family'] = font_name
            break
        except:
            continue
else:
    plt.rcParams['font.family'] = 'DejaVu Sans'
plt.rcParams['axes.unicode_minus'] = False  # 마이너스 기호 깨짐 방지

BASE_DIR = Path(__file__).resolve().parent


def load_latest_report():
    """가장 최근 리포트 파일 로드"""
    report_files = list(BASE_DIR.glob('prd_simulation_report_*.json'))
    if not report_files:
        print("[ERROR] 리포트 파일을 찾을 수 없습니다.")
        return None
    
    # 가장 최근 파일 선택
    latest_file = max(report_files, key=lambda p: p.stat().st_mtime)
    print(f"[INFO] 리포트 파일 로드: {latest_file.name}")
    
    with open(latest_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    return data


def create_visualization(data):
    """시각화 생성"""
    if not data:
        return
    
    # Figure 생성 (2x3 그리드)
    fig = plt.figure(figsize=(18, 12))
    fig.suptitle('검증 테스트 결과 시각화', fontsize=20, fontweight='bold', y=0.98)
    
    # 1. 전체 통계 (상단 왼쪽)
    ax1 = plt.subplot(2, 3, 1)
    total = data['total_sessions']
    completed = data['onboarding_completed']
    rec_success = data['recommendation_success']
    rec_failed = data['recommendation_failed']
    
    stats_labels = ['온보딩\n완료', '추천\n성공', '추천\n실패']
    stats_values = [
        completed / total * 100,
        rec_success / total * 100,
        rec_failed / total * 100
    ]
    colors = ['#4CAF50', '#2196F3', '#F44336']
    
    bars = ax1.bar(stats_labels, stats_values, color=colors, alpha=0.8, edgecolor='black', linewidth=1.5)
    ax1.set_ylabel('비율 (%)', fontsize=12)
    ax1.set_title('전체 통계', fontsize=14, fontweight='bold')
    ax1.set_ylim(0, 110)
    ax1.grid(axis='y', alpha=0.3, linestyle='--')
    
    # 값 표시
    for bar, value in zip(bars, stats_values):
        height = bar.get_height()
        ax1.text(bar.get_x() + bar.get_width()/2., height + 2,
                f'{value:.1f}%',
                ha='center', va='bottom', fontsize=11, fontweight='bold')
    
    # 2. 카테고리별 추천 분포 (상단 중앙) - 막대 그래프
    ax2 = plt.subplot(2, 3, 2)
    category_data = data.get('category_distribution', {})
    if category_data:
        categories = list(category_data.keys())
        counts = list(category_data.values())
        colors_cat = plt.cm.Set3(np.linspace(0, 1, len(categories)))
        
        bars = ax2.bar(categories, counts, color=colors_cat, alpha=0.8, edgecolor='black', linewidth=1.5)
        ax2.set_ylabel('추천 수', fontsize=12)
        ax2.set_title('카테고리별 추천 분포', fontsize=14, fontweight='bold')
        ax2.grid(axis='y', alpha=0.3, linestyle='--')
        
        # 값 표시
        for bar, count in zip(bars, counts):
            height = bar.get_height()
            ax2.text(bar.get_x() + bar.get_width()/2., height + max(counts)*0.01,
                    f'{count}',
                    ha='center', va='bottom', fontsize=10, fontweight='bold')
    
    # 3. 카테고리별 추천 분포 (상단 오른쪽) - 파이 차트
    ax3 = plt.subplot(2, 3, 3)
    if category_data:
        categories = list(category_data.keys())
        counts = list(category_data.values())
        colors_pie = plt.cm.Set3(np.linspace(0, 1, len(categories)))
        
        wedges, texts, autotexts = ax3.pie(
            counts, 
            labels=categories, 
            autopct='%1.1f%%',
            colors=colors_pie,
            startangle=90,
            textprops={'fontsize': 11, 'fontweight': 'bold'}
        )
        ax3.set_title('카테고리별 비율', fontsize=14, fontweight='bold')
    
    # 4. 예산별 분포 (하단 왼쪽)
    ax4 = plt.subplot(2, 3, 4)
    budget_data = data.get('budget_distribution', {})
    if budget_data:
        budgets = list(budget_data.keys())
        counts = list(budget_data.values())
        budget_labels = {'low': '저예산', 'medium': '중예산', 'high': '고예산'}
        labels = [budget_labels.get(b, b) for b in budgets]
        colors_budget = ['#FF9800', '#2196F3', '#9C27B0']
        
        bars = ax4.bar(labels, counts, color=colors_budget[:len(budgets)], alpha=0.8, edgecolor='black', linewidth=1.5)
        ax4.set_ylabel('세션 수', fontsize=12)
        ax4.set_title('예산별 분포', fontsize=14, fontweight='bold')
        ax4.grid(axis='y', alpha=0.3, linestyle='--')
        
        # 값 표시
        for bar, count in zip(bars, counts):
            height = bar.get_height()
            ax4.text(bar.get_x() + bar.get_width()/2., height + max(counts)*0.01,
                    f'{count}',
                    ha='center', va='bottom', fontsize=10, fontweight='bold')
    
    # 5. 가구 구성별 분포 (하단 중앙)
    ax5 = plt.subplot(2, 3, 5)
    household_data = data.get('household_distribution', {})
    if household_data:
        households = sorted([int(k) for k in household_data.keys()])
        counts = [household_data[str(h)] for h in households]
        labels = [f'{h}인 가구' for h in households]
        colors_household = plt.cm.Pastel1(np.linspace(0, 1, len(households)))
        
        bars = ax5.bar(labels, counts, color=colors_household, alpha=0.8, edgecolor='black', linewidth=1.5)
        ax5.set_ylabel('세션 수', fontsize=12)
        ax5.set_title('가구 구성별 분포', fontsize=14, fontweight='bold')
        ax5.grid(axis='y', alpha=0.3, linestyle='--')
        
        # 값 표시
        for bar, count in zip(bars, counts):
            height = bar.get_height()
            ax5.text(bar.get_x() + bar.get_width()/2., height + max(counts)*0.01,
                    f'{count}',
                    ha='center', va='bottom', fontsize=10, fontweight='bold')
    
    # 6. 요약 통계 (하단 오른쪽) - 텍스트 박스
    ax6 = plt.subplot(2, 3, 6)
    ax6.axis('off')
    
    total = data['total_sessions']
    completed = data['onboarding_completed']
    rec_success = data['recommendation_success']
    rec_failed = data['recommendation_failed']
    total_recs = data.get('total_recommendations', 0)
    avg_recs = total_recs / rec_success if rec_success > 0 else 0
    
    summary_text = f"""
    [전체 통계 요약]
    
    총 세션: {total:,}개
    온보딩 완료: {completed:,}개 ({completed/total*100:.1f}%)
    추천 성공: {rec_success:,}개 ({rec_success/total*100:.1f}%)
    추천 실패: {rec_failed:,}개 ({rec_failed/total*100:.1f}%)
    
    총 추천 제품 수: {total_recs:,}개
    세션당 평균 추천: {avg_recs:.1f}개
    
    오류 수: {len(data.get('errors', []))}개
    """
    
    ax6.text(0.1, 0.5, summary_text, 
            fontsize=12, 
            verticalalignment='center',
            family='monospace',
            bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
    ax6.set_title('요약 통계', fontsize=14, fontweight='bold')
    
    plt.tight_layout(rect=[0, 0, 1, 0.96])
    
    # 저장
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = BASE_DIR / f"verification_visualization_{timestamp}.png"
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"\n[OK] 시각화 저장: {output_file}")
    
    # 화면에 표시
    plt.show()


def main():
    """메인 함수"""
    print("=" * 80)
    print("검증 테스트 결과 시각화")
    print("=" * 80)
    
    # 리포트 로드
    data = load_latest_report()
    if not data:
        return
    
    # 시각화 생성
    print("\n[INFO] 시각화 생성 중...")
    create_visualization(data)
    
    print("\n" + "=" * 80)
    print("시각화 완료!")
    print("=" * 80)


if __name__ == '__main__':
    main()

