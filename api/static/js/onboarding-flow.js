/**
 * 온보딩 플로우 관리
 */

class OnboardingFlow {
    constructor() {
        this.sessionId = this.generateSessionId();
        this.currentStep = 1;
        this.formData = {
            vibe: null,
            household_size: null,
            housing_type: null,
            pyung: null,
            priority: null,
            budget_level: null,
            selected_categories: [],
        };
        
        this.init();
    }
    
    generateSessionId() {
        return `sess_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    }
    
    init() {
        this.attachEventListeners();
        this.showStep(1);
        this.updateUI();
    }
    
    attachEventListeners() {
        // 다음 버튼
        document.getElementById('nextBtn').addEventListener('click', () => this.nextStep());
        
        // 이전 버튼
        document.getElementById('prevBtn').addEventListener('click', () => this.prevStep());
        
        // 건너뛰기 버튼
        const skipBtn = document.getElementById('skipBtn');
        if (skipBtn) {
            skipBtn.addEventListener('click', () => this.skipStep());
        }
        
        // 다시 시작 버튼
        document.getElementById('restartBtn').addEventListener('click', () => this.restart());
        
        // 옵션 선택 시 자동 저장
        document.querySelectorAll('input[type="radio"], input[type="checkbox"]').forEach(input => {
            input.addEventListener('change', () => this.saveFormData());
        });
        
        // 텍스트 입력 시 자동 저장
        document.querySelectorAll('input[type="number"]').forEach(input => {
            input.addEventListener('change', () => this.saveFormData());
        });
    }
    
    saveFormData() {
        // 라디오 버튼
        ['vibe', 'household_size', 'housing_type', 'priority', 'budget_level'].forEach(field => {
            const element = document.querySelector(`input[name="${field}"]:checked`);
            if (element) {
                this.formData[field] = element.value;
            }
        });
        
        // 평수 입력
        const pyungInput = document.querySelector('input[name="pyung"]');
        if (pyungInput && pyungInput.value) {
            this.formData.pyung = parseInt(pyungInput.value);
        }
        
        // 체크박스
        const categories = [];
        document.querySelectorAll('input[name="selected_categories"]:checked').forEach(checkbox => {
            categories.push(checkbox.value);
        });
        this.formData.selected_categories = categories;
        
        console.log('Form Data:', this.formData);
    }
    
    isStepValid(step) {
        switch(step) {
            case 1:
                return this.formData.vibe !== null;
            case 2:
                return this.formData.household_size !== null;
            case 3:
                return this.formData.housing_type !== null && this.formData.pyung !== null;
            case 4:
                return this.formData.priority !== null;
            case 5:
                return this.formData.budget_level !== null && this.formData.selected_categories.length > 0;
            default:
                return true;
        }
    }
    
    nextStep() {
        this.saveFormData();
        
        if (!this.isStepValid(this.currentStep)) {
            alert(`${this.currentStep}단계를 완료해주세요.`);
            return;
        }
        
        if (this.currentStep < 5) {
            this.currentStep++;
            this.showStep(this.currentStep);
            this.updateUI();
            this.scrollToTop();
        } else if (this.currentStep === 5) {
            this.submitOnboarding();
        }
    }
    
    prevStep() {
        if (this.currentStep > 1) {
            this.currentStep--;
            this.showStep(this.currentStep);
            this.updateUI();
            this.scrollToTop();
        }
    }
    
    skipStep() {
        if (this.currentStep < 5) {
            this.currentStep = 5;
            this.showStep(this.currentStep);
            this.updateUI();
            this.scrollToTop();
        }
    }
    
    showStep(step) {
        // 모든 스텝 숨기기
        document.querySelectorAll('.step-container').forEach(el => {
            el.classList.add('hidden');
        });
        
        // 현재 스텝만 보이기
        const stepId = typeof step === 'string' ? step : `step${step}`;
        const currentStepEl = document.getElementById(stepId);
        if (currentStepEl) {
            currentStepEl.classList.remove('hidden');
        }
    }
    
    updateUI() {
        // 진행률 바 업데이트
        const progress = (this.currentStep / 5) * 100;
        document.getElementById('progressFill').style.width = `${progress}%`;
        document.getElementById('currentStep').textContent = this.currentStep;
        
        // 버튼 상태 업데이트
        document.getElementById('prevBtn').classList.toggle('hidden', this.currentStep === 1);
        const skipBtn = document.getElementById('skipBtn');
        if (skipBtn) {
            skipBtn.classList.toggle('hidden', this.currentStep === 5);
        }
        
        // 다음 버튼 텍스트
        const nextBtn = document.getElementById('nextBtn');
        if (this.currentStep === 5) {
            nextBtn.textContent = '추천 받기';
        } else {
            nextBtn.textContent = '다음';
        }
    }
    
    async submitOnboarding() {
        this.saveFormData();
        
        // 로딩 화면 표시
        this.showStep('loading');
        this.hideButtons();
        
        try {
            // API 호출
            const response = await fetch('/api/onboarding/complete/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken(),
                },
                body: JSON.stringify({
                    session_id: this.sessionId,
                    vibe: this.formData.vibe,
                    household_size: parseInt(this.formData.household_size),
                    housing_type: this.formData.housing_type,
                    pyung: this.formData.pyung,
                    priority: this.formData.priority,
                    budget_level: this.formData.budget_level,
                    selected_categories: this.formData.selected_categories,
                }),
            });
            
            const data = await response.json();
            
            if (data.success) {
                // 포트폴리오 ID 저장 (새로운 백엔드 로직에서 반환)
                if (data.portfolio_id) {
                    sessionStorage.setItem('portfolio_id', data.portfolio_id);
                }
                if (data.internal_key) {
                    sessionStorage.setItem('portfolio_internal_key', data.internal_key);
                }
                
                // 결과 화면 표시
                this.showResults(data.recommendations);
            } else {
                throw new Error(data.error || '추천 실패');
            }
        } catch (error) {
            alert(`오류: ${error.message}`);
            this.showStep(5);
            this.updateUI();
        }
    }
    
    showResults(recommendations) {
        const container = document.getElementById('recommendationsContainer');
        container.innerHTML = '';
        
        if (!recommendations || recommendations.length === 0) {
            container.innerHTML = '<p style="text-align: center; padding: 40px;">추천 결과가 없습니다.</p>';
            return;
        }
        
        recommendations.forEach((rec, index) => {
            const card = document.createElement('div');
            card.className = 'recommendation-card';
            
            const price = rec.discount_price || rec.price || 0;
            const originalPrice = rec.discount_price && rec.price && rec.discount_price < rec.price ? rec.price : null;
            
            card.innerHTML = `
                <div class="rec-category">${this.escapeHtml(rec.category_display || rec.category || '')}</div>
                <div class="rec-title">${this.escapeHtml(rec.model || rec.name || '')}</div>
                ${rec.model_number ? `<div style="font-size: 12px; color: #666; margin-bottom: 10px;">${this.escapeHtml(rec.model_number)}</div>` : ''}
                <div class="rec-score">${Math.round((rec.score || 0) * 100)}점 일치</div>
                <div class="rec-price">₩${price.toLocaleString()}</div>
                ${originalPrice ? `
                    <div class="rec-discount">할인가: ₩${originalPrice.toLocaleString()}</div>
                ` : ''}
                <div class="rec-reason">${this.escapeHtml(rec.reason || '')}</div>
            `;
            container.appendChild(card);
        });
        
        // 결과 화면 표시
        this.showStep('results');
        document.getElementById('restartBtn').classList.remove('hidden');
    }
    
    hideButtons() {
        document.getElementById('prevBtn').classList.add('hidden');
        document.getElementById('nextBtn').classList.add('hidden');
        const skipBtn = document.getElementById('skipBtn');
        if (skipBtn) {
            skipBtn.classList.add('hidden');
        }
    }
    
    restart() {
        this.currentStep = 1;
        this.formData = {
            vibe: null,
            household_size: null,
            housing_type: null,
            pyung: null,
            priority: null,
            budget_level: null,
            selected_categories: [],
        };
        
        // 폼 초기화
        document.querySelectorAll('input[type="radio"], input[type="checkbox"]').forEach(input => {
            input.checked = false;
        });
        document.querySelectorAll('input[type="number"]').forEach(input => {
            input.value = '';
        });
        
        // UI 업데이트
        this.showStep(1);
        this.updateUI();
        document.getElementById('restartBtn').classList.add('hidden');
        document.getElementById('nextBtn').classList.remove('hidden');
        document.getElementById('prevBtn').classList.add('hidden');
        
        this.scrollToTop();
    }
    
    scrollToTop() {
        window.scrollTo({ behavior: 'smooth', top: 0 });
    }
    
    getCSRFToken() {
        const name = 'csrftoken';
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }
    
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

// 페이지 로드 시 초기화
document.addEventListener('DOMContentLoaded', () => {
    new OnboardingFlow();
});

