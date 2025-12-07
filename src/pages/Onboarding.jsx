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

  // 컴포넌트 마운트 시 CSRF 토큰 초기화
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

      const data = await apiRequest('/api/onboarding/complete/', {
        method: 'POST',
        body: JSON.stringify({
          session_id: sessionId,
          vibe: formData.vibe,
          household_size: parseInt(formData.household_size),
          housing_type: formData.housing_type,
          pyung: formData.pyung,
          priority: formData.priority,
          budget_level: formData.budget_level,
          selected_categories: formData.selected_categories,
          pet: formData.pet,
          cooking: formData.cooking,
          laundry: formData.laundry,
          media: formData.media,
        }),
      })

      if (data.success) {
        // 포트폴리오 ID가 있으면 결과 페이지로 이동
        if (data.portfolio_id) {
          navigate(`/result?portfolio_id=${data.portfolio_id}`)
        } else {
          // 추천 결과를 state로 전달
          navigate('/result', { 
            state: { 
              recommendations: data.recommendations,
              portfolio_id: data.portfolio_id 
            } 
          })
        }
      } else {
        alert(`오류: ${data.error || '추천 실패'}`)
        setLoading(false)
      }
    } catch (error) {
      console.error('온보딩 제출 실패:', error)
      alert(`오류: ${error.message}`)
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
      <div className="options-grid grid-3">
        {[
          { value: 'modern', label: '모던', icon: '🏠' },
          { value: 'classic', label: '클래식', icon: '🏛️' },
          { value: 'minimal', label: '미니멀', icon: '✨' },
          { value: 'natural', label: '내추럴', icon: '🌿' },
          { value: 'industrial', label: '인더스트리얼', icon: '⚙️' },
          { value: 'scandinavian', label: '스칸디나비안', icon: '❄️' },
        ].map(option => (
          <div
            key={option.value}
            className={`option-card ${formData.vibe === option.value ? 'selected' : ''}`}
            onClick={() => updateFormData('vibe', option.value)}
          >
            <span className="option-icon">{option.icon}</span>
            <div className="option-title">{option.label}</div>
          </div>
        ))}
      </div>
    </div>
  )

  // Step 2: 가구 정보
  const renderStep2 = () => (
    <div className="onboarding-step">
      <h2 className="question-title">가구 정보를 알려주세요</h2>
      
      <div className="form-group">
        <label>가구원 수</label>
        <div className="options-grid grid-4">
          {['1인', '2인', '3인', '4인', '5인 이상'].map(size => (
            <div
              key={size}
              className={`option-card ${formData.household_size === size ? 'selected' : ''}`}
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
            { value: 'apartment', label: '아파트' },
            { value: 'house', label: '단독주택' },
            { value: 'officetel', label: '오피스텔' },
          ].map(option => (
            <div
              key={option.value}
              className={`option-card ${formData.housing_type === option.value ? 'selected' : ''}`}
              onClick={() => updateFormData('housing_type', option.value)}
            >
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
      
      <div className="form-group">
        <label>우선순위</label>
        <div className="options-grid grid-2">
          {[
            { value: 'design', label: '디자인', icon: '🎨' },
            { value: 'tech', label: '기술', icon: '💻' },
            { value: 'eco', label: '친환경', icon: '🌱' },
            { value: 'value', label: '가성비', icon: '💰' },
          ].map(option => (
            <div
              key={option.value}
              className={`option-card ${formData.priority === option.value ? 'selected' : ''}`}
              onClick={() => updateFormData('priority', option.value)}
            >
              <span className="option-icon">{option.icon}</span>
              <div className="option-title">{option.label}</div>
            </div>
          ))}
        </div>
      </div>

      <div className="form-group">
        <label>예산 수준</label>
        <div className="budget-cards">
          {[
            { value: 'budget', label: '예산형', range: '~50만원' },
            { value: 'standard', label: '표준형', range: '50~200만원' },
            { value: 'premium', label: '프리미엄', range: '200~500만원' },
            { value: 'luxury', label: '럭셔리', range: '500만원~' },
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
      
      <div className="options-grid grid-3">
        {[
          { value: 'TV', label: 'TV' },
          { value: 'REFRIGERATOR', label: '냉장고' },
          { value: 'WASHER', label: '세탁기' },
          { value: 'AIR_CONDITIONER', label: '에어컨' },
          { value: 'KITCHEN', label: '주방가전' },
          { value: 'LIVING', label: '거실가전' },
        ].map(option => (
          <div
            key={option.value}
            className={`option-card ${formData.selected_categories.includes(option.value) ? 'selected' : ''}`}
            onClick={() => toggleCategory(option.value)}
          >
            <div className="option-title">{option.label}</div>
          </div>
        ))}
      </div>
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
          <div className="text-2xl font-bold mb-4">추천 중...</div>
          <div className="text-gray-600">잠시만 기다려주세요</div>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-[#F7F4EF]">
      <div className="onboarding-header">
        <button onClick={handleBack} className="header-back" disabled={currentStep === 1}>
          ←
        </button>
        <div className="header-title">온보딩 {currentStep}/4</div>
        <button onClick={() => navigate('/')} className="header-close">
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
            {currentStep === 4 ? '완료' : '다음'}
          </button>
        </div>
      </div>
    </div>
  )
}

export default Onboarding

