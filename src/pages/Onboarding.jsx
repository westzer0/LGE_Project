import React, { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { apiRequest, initCSRFToken } from '../utils/api'

const Onboarding = () => {
  const navigate = useNavigate()
  const [currentStep, setCurrentStep] = useState(1)
  const [formData, setFormData] = useState({
    vibe: '',
    household_size: '',
    housing_type: '',
    pyung: 25,
    priority: '',
    budget_level: '',
    selected_categories: [],
    pet: '',
    cooking: '',
    laundry: '',
    media: '',
  })
  const [loading, setLoading] = useState(false)

  const generateSessionId = () => {
    return `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
  }

  useEffect(() => {
    initCSRFToken()
  }, [])

  const handleNext = () => {
    if (currentStep < 4) {
      setCurrentStep(currentStep + 1)
    } else {
      handleSubmit()
    }
  }

  const handleBack = () => {
    if (currentStep > 1) {
      setCurrentStep(currentStep - 1)
    }
  }

  const handleSubmit = async () => {
    setLoading(true)
    
    try {
      const sessionId = generateSessionId()

      // 데이터 검증
      if (!formData.vibe || !formData.household_size || !formData.housing_type || 
          !formData.priority || !formData.budget_level || formData.selected_categories.length === 0) {
        alert('모든 항목을 선택해주세요.')
        setLoading(false)
        return
      }

      // household_size를 정수로 변환
      let householdSize = formData.household_size
      if (typeof householdSize === 'string') {
        householdSize = parseInt(householdSize.replace('인', '').replace(' 이상', '').trim()) || 2
      }

      const data = await apiRequest('/api/onboarding/complete/', {
        method: 'POST',
        body: JSON.stringify({
          session_id: sessionId,
          vibe: formData.vibe,
          household_size: householdSize,
          housing_type: formData.housing_type,
          pyung: formData.pyung || 25,
          priority: formData.priority,
          budget_level: formData.budget_level,
          selected_categories: formData.selected_categories,
          pet: formData.pet || 'no',
          cooking: formData.cooking || 'sometimes',
          laundry: formData.laundry || 'weekly',
          media: formData.media || 'balanced',
        }),
      })

      if (data.success) {
        if (data.portfolio_id) {
          navigate(`/result?portfolio_id=${data.portfolio_id}`)
        } else if (data.recommendations && data.recommendations.length > 0) {
          navigate('/result', { 
            state: { 
              recommendations: data.recommendations,
              portfolio_id: data.portfolio_id 
            } 
          })
        } else {
          alert('추천 결과를 받지 못했습니다. 다시 시도해주세요.')
          setLoading(false)
        }
      } else {
        const errorMsg = data.error || '추천 실패'
        alert(`오류: ${errorMsg}`)
        setLoading(false)
      }
    } catch (error) {
      console.error('[Onboarding] 제출 실패:', error)
      alert(`오류: ${error.message || '서버 연결 실패'}`)
      setLoading(false)
    }
  }

  const updateFormData = (key, value) => {
    setFormData(prev => ({
      ...prev,
      [key]: value
    }))
  }

  const toggleCategory = (category) => {
    setFormData(prev => ({
      ...prev,
      selected_categories: prev.selected_categories.includes(category)
        ? prev.selected_categories.filter(c => c !== category)
        : [...prev.selected_categories, category]
    }))
  }

  // Step 1: Vibe 선택
  const renderStep1 = () => (
    <div className="onboarding-step">
      <h2 className="question-title">어떤 스타일을 선호하시나요?</h2>
      <p className="question-subtitle">원하시는 인테리어 스타일을 선택해주세요</p>
      <div className="options-grid grid-3">
        {[
          { value: 'modern', label: '모던', icon: '🏠', desc: '깔끔하고 세련된' },
          { value: 'classic', label: '클래식', icon: '🏛️', desc: '전통적이고 우아한' },
          { value: 'minimal', label: '미니멀', icon: '✨', desc: '심플하고 절제된' },
          { value: 'natural', label: '내추럴', icon: '🌿', desc: '자연스럽고 편안한' },
          { value: 'industrial', label: '인더스트리얼', icon: '⚙️', desc: '거칠고 개성있는' },
          { value: 'scandinavian', label: '스칸디나비안', icon: '❄️', desc: '밝고 따뜻한' },
        ].map(option => (
          <div
            key={option.value}
            className={`option-card ${formData.vibe === option.value ? 'selected' : ''}`}
            onClick={() => updateFormData('vibe', option.value)}
          >
            <span className="option-icon">{option.icon}</span>
            <div className="option-title">{option.label}</div>
            <div className="option-description">{option.desc}</div>
          </div>
        ))}
      </div>
    </div>
  )

  // Step 2: 가구 정보
  const renderStep2 = () => (
    <div className="onboarding-step">
      <h2 className="question-title">가구 정보를 알려주세요</h2>
      <p className="question-subtitle">정확한 추천을 위해 필요합니다</p>
      
      <div className="form-group">
        <label>가구원 수</label>
        <div className="options-grid grid-4">
          {['1인', '2인', '3인', '4인', '5인 이상'].map(size => (
            <div
              key={size}
              className={`option-card ${formData.household_size === size.replace('인', '').replace(' 이상', '') ? 'selected' : ''}`}
              onClick={() => updateFormData('household_size', size.replace('인', '').replace(' 이상', ''))}
            >
              <div className="option-title">{size}</div>
            </div>
          ))}
        </div>
      </div>

      <div className="form-group">
        <label>주거 형태</label>
        <div className="options-grid grid-3">
          {[
            { value: 'apartment', label: '아파트', icon: '🏢' },
            { value: 'house', label: '단독주택', icon: '🏡' },
            { value: 'officetel', label: '오피스텔', icon: '🏬' },
          ].map(option => (
            <div
              key={option.value}
              className={`option-card ${formData.housing_type === option.value ? 'selected' : ''}`}
              onClick={() => updateFormData('housing_type', option.value)}
            >
              <span className="option-icon">{option.icon}</span>
              <div className="option-title">{option.label}</div>
            </div>
          ))}
        </div>
      </div>

      <div className="form-group">
        <label>평수</label>
        <div className="range-container">
          <div className="range-value">{formData.pyung}평</div>
          <input
            type="range"
            min="10"
            max="50"
            value={formData.pyung}
            onChange={(e) => updateFormData('pyung', parseInt(e.target.value))}
            className="range-slider"
          />
          <div className="range-labels">
            <span>10평</span>
            <span>50평</span>
          </div>
        </div>
      </div>
    </div>
  )

  // Step 3: 우선순위 및 예산
  const renderStep3 = () => (
    <div className="onboarding-step">
      <h2 className="question-title">가전 선택 시 우선순위는?</h2>
      <p className="question-subtitle">가장 중요하게 생각하는 요소를 선택해주세요</p>
      
      <div className="form-group">
        <label>우선순위</label>
        <div className="options-grid grid-2">
          {[
            { value: 'design', label: '디자인', icon: '🎨', desc: '외관과 스타일' },
            { value: 'tech', label: '기술', icon: '💻', desc: '최신 기능과 성능' },
            { value: 'eco', label: '친환경', icon: '🌱', desc: '에너지 효율' },
            { value: 'value', label: '가성비', icon: '💰', desc: '합리적인 가격' },
          ].map(option => (
            <div
              key={option.value}
              className={`option-card ${formData.priority === option.value ? 'selected' : ''}`}
              onClick={() => updateFormData('priority', option.value)}
            >
              <span className="option-icon">{option.icon}</span>
              <div className="option-title">{option.label}</div>
              <div className="option-description">{option.desc}</div>
            </div>
          ))}
        </div>
      </div>

      <div className="form-group">
        <label>예산 수준</label>
        <div className="budget-cards">
          {[
            { value: 'budget', label: '예산형', range: '~50만원', desc: '합리적인 가격' },
            { value: 'standard', label: '표준형', range: '50~200만원', desc: '균형잡힌 선택' },
            { value: 'premium', label: '프리미엄', range: '200~500만원', desc: '고급 기능' },
            { value: 'luxury', label: '럭셔리', range: '500만원~', desc: '최고급 라인' },
          ].map(option => (
            <div
              key={option.value}
              className={`budget-card ${formData.budget_level === option.value ? 'selected' : ''}`}
              onClick={() => updateFormData('budget_level', option.value)}
            >
              <div className="budget-icon">💰</div>
              <div className="budget-info">
                <div className="budget-title">{option.label}</div>
                <div className="budget-range">{option.range}</div>
                <div className="budget-desc">{option.desc}</div>
              </div>
              <div className="budget-check">
                {formData.budget_level === option.value && '✓'}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )

  // Step 4: 카테고리 선택
  const renderStep4 = () => (
    <div className="onboarding-step">
      <h2 className="question-title">관심 있는 가전 카테고리를 선택해주세요</h2>
      <p className="question-subtitle">복수 선택 가능합니다</p>
      
      <div className="options-grid grid-3">
        {[
          { value: 'TV', label: 'TV', icon: '📺' },
          { value: 'REFRIGERATOR', label: '냉장고', icon: '❄️' },
          { value: 'WASHER', label: '세탁기', icon: '🌀' },
          { value: 'AIR_CONDITIONER', label: '에어컨', icon: '❄️' },
          { value: 'KITCHEN', label: '주방가전', icon: '🍳' },
          { value: 'LIVING', label: '거실가전', icon: '🛋️' },
        ].map(option => (
          <div
            key={option.value}
            className={`option-card ${formData.selected_categories.includes(option.value) ? 'selected' : ''}`}
            onClick={() => toggleCategory(option.value)}
          >
            <span className="option-icon">{option.icon}</span>
            <div className="option-title">{option.label}</div>
            {formData.selected_categories.includes(option.value) && (
              <div className="option-check">✓</div>
            )}
          </div>
        ))}
      </div>
      
      {formData.selected_categories.length > 0 && (
        <div className="selected-categories">
          <p>선택된 카테고리: {formData.selected_categories.length}개</p>
        </div>
      )}
    </div>
  )

  const canProceed = () => {
    switch (currentStep) {
      case 1: return formData.vibe !== ''
      case 2: return formData.household_size !== '' && formData.housing_type !== ''
      case 3: return formData.priority !== '' && formData.budget_level !== ''
      case 4: return formData.selected_categories.length > 0
      default: return false
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-[#F7F4EF] flex items-center justify-center">
        <div className="text-center">
          <div className="loading-spinner mb-4"></div>
          <div className="text-2xl font-bold mb-2 text-[#1A1A1A]">추천 중...</div>
          <div className="text-gray-600">잠시만 기다려주세요</div>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-[#F7F4EF]">
      <div className="onboarding-header">
        <button 
          onClick={handleBack} 
          className="header-back" 
          disabled={currentStep === 1}
          aria-label="이전"
        >
          ←
        </button>
        <div className="header-title">온보딩 {currentStep}/4</div>
        <button 
          onClick={() => navigate('/')} 
          className="header-close"
          aria-label="닫기"
        >
          ✕
        </button>
      </div>

      <div className="onboarding-container">
        <div className="progress-bar">
          <div 
            className="progress-fill" 
            style={{ width: `${(currentStep / 4) * 100}%` }}
          />
        </div>

        <div className="onboarding-content">
          {currentStep === 1 && renderStep1()}
          {currentStep === 2 && renderStep2()}
          {currentStep === 3 && renderStep3()}
          {currentStep === 4 && renderStep4()}
        </div>

        <div className="nav-buttons">
          <button
            onClick={handleNext}
            disabled={!canProceed()}
            className={`nav-btn-primary ${!canProceed() ? 'disabled' : ''}`}
          >
            {currentStep === 4 ? '완료하고 추천받기' : '다음'}
          </button>
        </div>
      </div>
    </div>
  )
}

export default Onboarding
