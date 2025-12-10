import React, { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { apiRequest, initCSRFToken } from '../utils/api'

const Onboarding = () => {
  const navigate = useNavigate()
  const [currentStep, setCurrentStep] = useState(1)
  const [formData, setFormData] = useState({
    // Step 1: Vibe Check
    vibe: '',
    // Step 2: Household DNA
    household_size: '',
    has_pet: null,
    // Step 3: Reality Check
    housing_type: '',
    main_space: [],
    pyung: 25,
    // Step 4: Lifestyle Info
    cooking: '',
    laundry: '',
    media: '',
    // Step 5: Priorities
    priority: '',
    priority_list: [],
    // Step 6: Budget
    budget_level: '',
    // 카테고리 (온보딩 완료 시 자동 선택 또는 사용자 선택)
    selected_categories: [],
  })
  const [loading, setLoading] = useState(false)

  const generateSessionId = () => {
    // UUID v4 형식으로 생성 (완전히 고유한 ID 보장)
    // 형식: xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx
    return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function (c) {
      const r = Math.random() * 16 | 0
      const v = c === 'x' ? r : (r & 0x3 | 0x8)
      return v.toString(16)
    })
  }

  useEffect(() => {
    initCSRFToken()
  }, [])

  const handleNext = () => {
    if (currentStep < 6) {
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
        !formData.priority || !formData.budget_level) {
        alert('모든 필수 항목을 선택해주세요.')
        setLoading(false)
        return
      }

      // household_size를 정수로 변환
      let householdSize = formData.household_size
      if (typeof householdSize === 'string') {
        householdSize = parseInt(householdSize.replace('인', '').replace(' 이상', '').trim()) || 2
      }

      // priority_list가 비어있으면 priority를 첫 번째로 추가
      const priorityList = formData.priority_list.length > 0
        ? formData.priority_list
        : [formData.priority]

      const data = await apiRequest('/api/onboarding/complete/', {
        method: 'POST',
        body: JSON.stringify({
          session_id: sessionId,
          // Step 1
          vibe: formData.vibe,
          // Step 2
          household_size: householdSize,
          has_pet: formData.has_pet,
          // Step 3
          housing_type: formData.housing_type,
          main_space: formData.main_space.length > 0 ? formData.main_space : ['living'],
          pyung: formData.pyung || 25,
          // Step 4
          cooking: formData.cooking || 'sometimes',
          laundry: formData.laundry || 'weekly',
          media: formData.media || 'balanced',
          // Step 5
          priority: formData.priority,
          priority_list: priorityList,
          // Step 6
          budget_level: formData.budget_level,
          // 카테고리 (자동 선택 또는 빈 배열)
          selected_categories: formData.selected_categories.length > 0
            ? formData.selected_categories
            : ['TV', 'KITCHEN', 'LIVING', 'AIR'],
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

  const toggleMainSpace = (space) => {
    setFormData(prev => ({
      ...prev,
      main_space: prev.main_space.includes(space)
        ? prev.main_space.filter(s => s !== space)
        : [...prev.main_space, space]
    }))
  }

  const togglePriority = (priority) => {
    setFormData(prev => {
      const priorityList = prev.priority_list.includes(priority)
        ? prev.priority_list.filter(p => p !== priority)
        : [...prev.priority_list, priority]

      // 첫 번째 우선순위는 priority 필드에도 저장
      return {
        ...prev,
        priority: priorityList.length > 0 ? priorityList[0] : '',
        priority_list: priorityList
      }
    })
  }

  // Step 1: Vibe Check
  const renderStep1 = () => (
    <div className="onboarding-step">
      <h2 className="question-title">새로운 가전과 함께할 공간, 어떤 분위기를 꿈꾸시나요?</h2>
      <p className="question-subtitle">원하시는 인테리어 스타일을 선택해주세요</p>
      <div className="options-grid grid-2">
        {[
          { value: 'modern', label: '모던 & 미니멀', icon: '🏠', desc: '깔끔하고 심플한 스타일' },
          { value: 'cozy', label: '코지 & 네이처', icon: '🌿', desc: '따뜻하고 자연스러운 톤' },
          { value: 'pop', label: '유니크 & 팝', icon: '✨', desc: '생기있고 개성있는 스타일' },
          { value: 'luxury', label: '럭셔리 & 아티스틱', icon: '💎', desc: '고급스럽고 예술적인 분위기' },
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

  // Step 2: Household DNA
  const renderStep2 = () => (
    <div className="onboarding-step">
      <h2 className="question-title">이 공간에서 함께 생활하는 메이트는 누구인가요?</h2>
      <p className="question-subtitle">가구 구성을 알려주세요</p>

      <div className="form-group">
        <label>가구 구성</label>
        <div className="options-grid grid-2">
          {[
            { value: 1, label: '나 혼자 산다', desc: '1인 가구' },
            { value: 2, label: '우리 둘이 알콩달콩', desc: '2인 가구 (부부/연인)' },
            { value: 3, label: '아이가 있는 3~4인 가족', desc: '자녀 있는 가족' },
            { value: 5, label: '5인 이상 대가족', desc: '대가족' },
          ].map(option => (
            <div
              key={option.value}
              className={`option-card ${formData.household_size === option.value ? 'selected' : ''}`}
              onClick={() => updateFormData('household_size', option.value)}
            >
              <div className="option-title">{option.label}</div>
              <div className="option-description">{option.desc}</div>
            </div>
          ))}
        </div>
      </div>

      {formData.household_size && (
        <div className="form-group">
          <label>혹시 반려동물과 함께하시나요?</label>
          <div className="options-grid grid-2">
            {[
              { value: true, label: '네, 사랑스러운 댕냥이가 있어요', icon: '🐕' },
              { value: false, label: '아니요, 없어요', icon: '🚫' },
            ].map(option => (
              <div
                key={option.value}
                className={`option-card ${formData.has_pet === option.value ? 'selected' : ''}`}
                onClick={() => updateFormData('has_pet', option.value)}
              >
                <span className="option-icon">{option.icon}</span>
                <div className="option-title">{option.label}</div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )

  // Step 3: Reality Check
  const renderStep3 = () => (
    <div className="onboarding-step">
      <h2 className="question-title">가전을 설치할 곳의 주거 형태는 무엇인가요?</h2>
      <p className="question-subtitle">공간 정보를 알려주세요</p>

      <div className="form-group">
        <label>주거 형태</label>
        <div className="options-grid grid-2">
          {[
            { value: 'apartment', label: '아파트', icon: '🏢' },
            { value: 'officetel', label: '오피스텔', icon: '🏬' },
            { value: 'detached', label: '주택(단독/다가구)', icon: '🏡' },
            { value: 'studio', label: '원룸', icon: '🏠' },
          ].map(option => (
            <div
              key={option.value}
              className={`option-card ${formData.housing_type === option.value ? 'selected' : ''}`}
              onClick={() => {
                // PRD: 원룸 선택 시 main_space를 'all'로 자동 설정하고 pyung을 작은 값으로 설정
                if (option.value === 'studio') {
                  updateFormData('housing_type', option.value)
                  updateFormData('main_space', ['all'])
                  updateFormData('pyung', 15) // 원룸은 작은 크기로 자동 설정
                } else {
                  updateFormData('housing_type', option.value)
                }
              }}
            >
              <span className="option-icon">{option.icon}</span>
              <div className="option-title">{option.label}</div>
            </div>
          ))}
        </div>
      </div>

      {/* PRD: 원룸 선택 시 Q3-2(주요 공간) 건너뛰기 → 바로 Q3-3(공간 크기)로 이동 */}
      {formData.housing_type && formData.housing_type !== 'studio' && (
        <div className="form-group">
          <label>가전을 배치할 주요 공간은 어디인가요? (복수 선택 가능)</label>
          <p className="question-subtitle">공간의 목적에 맞춰 꼭 필요한 기능을 추천해 드릴게요</p>
          <div className="options-grid grid-3">
            {[
              { value: 'living', label: '거실', icon: '🛋️', desc: 'TV, 공기청정기' },
              { value: 'bedroom', label: '방', icon: '🛏️', desc: '공기청정기, TV(서브)' },
              { value: 'kitchen', label: '주방', icon: '🍳', desc: '냉장고, 식기세척기, 오븐' },
              { value: 'dressing', label: '드레스룸', icon: '👔', desc: '스타일러, 세탁기/건조기' },
              { value: 'study', label: '서재', icon: '📚', desc: '모니터, 공기청정기' },
              { value: 'all', label: '전체', icon: '🏠', desc: '전체 공간 패키지' },
            ].map(option => (
              <div
                key={option.value}
                className={`option-card ${formData.main_space.includes(option.value) ? 'selected' : ''}`}
                onClick={() => {
                  if (option.value === 'all') {
                    updateFormData('main_space', ['all'])
                  } else {
                    toggleMainSpace(option.value)
                  }
                }}
              >
                <span className="option-icon">{option.icon}</span>
                <div className="option-title">{option.label}</div>
                <div className="option-description">{option.desc}</div>
                {formData.main_space.includes(option.value) && (
                  <div className="option-check">✓</div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* PRD: 원룸이 아닌 경우에만 공간 크기 질문 표시 (원룸은 자동으로 작은 편으로 처리) */}
      {(formData.housing_type === 'studio' || formData.main_space.length > 0) && (
        <div className="form-group">
          <label>해당 공간의 크기는 대략 어느 정도인가요?</label>
          <p className="question-subtitle">가전이 공간에 딱 맞게 들어가도록, 크기를 알려주세요</p>
          {formData.housing_type === 'studio' && (
            <p className="info-message">원룸은 공간 효율성을 최우선으로 고려하여 컴팩트 모델을 추천해드려요.</p>
          )}
          <div className="range-container">
            <div className="range-value">{formData.pyung}평</div>
            <input
              type="range"
              min="10"
              max="50"
              value={formData.pyung}
              onChange={(e) => updateFormData('pyung', parseInt(e.target.value))}
              className="range-slider"
              disabled={formData.housing_type === 'studio'} // 원룸은 자동으로 작은 크기로 처리
            />
            <div className="range-labels">
              <span>작은 편 (Small)</span>
              <span>넓은 편 (Large)</span>
            </div>
          </div>
          {formData.housing_type === 'studio' && (
            <div className="info-box">
              <strong>원룸 추천 기준:</strong> 공간 효율성 최우선 (컴팩트/슬림 모델 우선 추천)
            </div>
          )}
        </div>
      )}
    </div>
  )

  // Step 4: Lifestyle Info
  // PRD: Q3의 응답에 따라 질문이 동적으로 변경됨
  // - 주방 선택 시: 요리 빈도만 활성화, 미디어 소비 비활성화
  // - 드레스룸 선택 시: 세탁 패턴만 활성화, 미디어 소비 비활성화
  // - 거실/방/서재 선택 시: 미디어 소비만 활성화
  // - 전체 선택 시: 모든 질문 활성화
  const renderStep4 = () => {
    // PRD 분기 로직: 원룸인 경우 main_space가 비어있을 수 있으므로 housing_type 확인
    const isStudio = formData.housing_type === 'studio'
    const mainSpaces = isStudio ? ['all'] : formData.main_space

    const hasKitchen = mainSpaces.includes('kitchen') || mainSpaces.includes('all')
    const hasDressing = mainSpaces.includes('dressing') || mainSpaces.includes('all')
    const hasMedia = mainSpaces.includes('living') || mainSpaces.includes('bedroom') ||
      mainSpaces.includes('study') || mainSpaces.includes('all')

    // 디버깅 로그 추가
    console.log('[Step 4 Render]', {
      housing_type: formData.housing_type,
      isStudio,
      mainSpaces,
      formData_main_space: formData.main_space,
      hasKitchen,
      hasDressing,
      hasMedia
    })

    // PRD: 주방만 선택된 경우 미디어 소비 비활성화
    const onlyKitchen = hasKitchen && !hasDressing && !hasMedia && !mainSpaces.includes('all')
    // PRD: 드레스룸만 선택된 경우 미디어 소비 비활성화
    const onlyDressing = hasDressing && !hasKitchen && !hasMedia && !mainSpaces.includes('all')

    return (
      <div className="onboarding-step">
        <h2 className="question-title">라이프스타일을 알려주세요</h2>
        <p className="question-subtitle">일상 생활 패턴을 선택해주세요</p>

        {hasKitchen && (
          <div className="form-group">
            <label>평소 집에서 요리는 얼마나 자주 하시나요?</label>
            <div className="options-grid grid-3">
              {[
                { value: 'rarely', label: '거의 하지 않아요', desc: '배달, 간편식 위주' },
                { value: 'sometimes', label: '가끔 해요', desc: '주말 위주' },
                { value: 'often', label: '자주 해요', desc: '요리하는 걸 좋아해요' },
              ].map(option => (
                <div
                  key={option.value}
                  className={`option-card ${formData.cooking === option.value ? 'selected' : ''}`}
                  onClick={() => updateFormData('cooking', option.value)}
                >
                  <div className="option-title">{option.label}</div>
                  <div className="option-description">{option.desc}</div>
                </div>
              ))}
            </div>
          </div>
        )}

        {hasDressing && (
          <div className="form-group">
            <label>세탁은 주로 어떻게 하시나요?</label>
            <div className="options-grid grid-3">
              {[
                { value: 'weekly', label: '일주일 1번 정도', desc: '주 1회 세탁' },
                { value: 'few_times', label: '일주일 2~3번 정도', desc: '주 2-3회 세탁' },
                { value: 'daily', label: '매일 조금씩', desc: '매일 세탁' },
              ].map(option => (
                <div
                  key={option.value}
                  className={`option-card ${formData.laundry === option.value ? 'selected' : ''}`}
                  onClick={() => updateFormData('laundry', option.value)}
                >
                  <div className="option-title">{option.label}</div>
                  <div className="option-description">{option.desc}</div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* PRD: 주방만 선택 시 미디어 소비 비활성화, 드레스룸만 선택 시도 비활성화 */}
        {hasMedia && !onlyKitchen && !onlyDressing && (
          <div className="form-group">
            <label>집에서 TV나 영상을 주로 어떻게 즐기시나요?</label>
            <p className="question-subtitle">거실, 방, 서재 선택 시에만 표시됩니다</p>
            <div className="options-grid grid-2">
              {[
                { value: 'ott', label: 'OTT를 즐기는 편', desc: '넷플릭스, 영화, 드라마 등' },
                { value: 'gaming', label: '게임이 취미', desc: '게임 중심' },
                { value: 'tv', label: '일반 프로그램 시청', desc: '뉴스나 예능 등' },
                { value: 'none', label: 'TV/영상을 즐기지 않음', desc: '미디어 사용 적음' },
              ].map(option => (
                <div
                  key={option.value}
                  className={`option-card ${formData.media === option.value ? 'selected' : ''}`}
                  onClick={() => updateFormData('media', option.value)}
                >
                  <div className="option-title">{option.label}</div>
                  <div className="option-description">{option.desc}</div>
                </div>
              ))}
            </div>
          </div>
        )}

        {!hasKitchen && !hasDressing && !hasMedia && (
          <div className="form-group">
            <p className="text-gray-500">선택한 공간에 대한 라이프스타일 질문이 없습니다.</p>
            <p className="text-sm text-gray-400 mt-2">다음 단계로 진행하세요.</p>
          </div>
        )}
      </div>
    )
  }

  // Step 5: Priorities
  const renderStep5 = () => (
    <div className="onboarding-step">
      <h2 className="question-title">구매 시 가장 중요하게 생각하는 것은 무엇인가요?</h2>
      <p className="question-subtitle">우선순위를 순서대로 선택해주세요 (복수 선택 가능)</p>

      <div className="options-grid grid-2">
        {[
          { value: 'design', label: '디자인/무드', icon: '🎨', desc: '외관과 스타일' },
          { value: 'tech', label: '기술/성능', icon: '💻', desc: '최신 기능과 성능' },
          { value: 'eco', label: '에너지효율', icon: '🌱', desc: '친환경' },
          { value: 'value', label: '가성비', icon: '💰', desc: '합리적인 가격' },
        ].map(option => {
          const isSelected = formData.priority_list.includes(option.value)
          const order = formData.priority_list.indexOf(option.value) + 1

          return (
            <div
              key={option.value}
              className={`option-card ${isSelected ? 'selected' : ''}`}
              onClick={() => togglePriority(option.value)}
            >
              <span className="option-icon">{option.icon}</span>
              <div className="option-title">{option.label}</div>
              <div className="option-description">{option.desc}</div>
              {isSelected && (
                <div className="option-order">{order}순위</div>
              )}
            </div>
          )
        })}
      </div>

      {formData.priority_list.length > 0 && (
        <div className="selected-priorities mt-4">
          <p className="text-sm text-gray-600">선택한 우선순위:</p>
          <div className="flex gap-2 mt-2">
            {formData.priority_list.map((priority, index) => (
              <span key={priority} className="px-3 py-1 bg-blue-100 text-blue-800 rounded-full text-sm">
                {index + 1}. {priority === 'design' ? '디자인' : priority === 'tech' ? '기술' : priority === 'eco' ? '에너지효율' : '가성비'}
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  )

  // Step 6: Budget
  const renderStep6 = () => (
    <div className="onboarding-step">
      <h2 className="question-title">예산 범위를 선택해주세요</h2>
      <p className="question-subtitle">가전 패키지 구매 예산을 알려주세요</p>

      <div className="budget-cards">
        {[
          { value: 'budget', label: '500만원 이하', desc: '저예산', icon: '💰' },
          { value: 'standard', label: '500~2000만원', desc: '중간 예산', icon: '💵' },
          { value: 'premium', label: '2000만원 이상', desc: '고예산', icon: '💎' },
        ].map(option => (
          <div
            key={option.value}
            className={`budget-card ${formData.budget_level === option.value ? 'selected' : ''}`}
            onClick={() => updateFormData('budget_level', option.value)}
          >
            <div className="budget-icon">{option.icon}</div>
            <div className="budget-info">
              <div className="budget-title">{option.label}</div>
              <div className="budget-desc">{option.desc}</div>
            </div>
            <div className="budget-check">
              {formData.budget_level === option.value && '✓'}
            </div>
          </div>
        ))}
      </div>
    </div>
  )

  const canProceed = () => {
    switch (currentStep) {
      case 1: return formData.vibe !== ''
      case 2: return formData.household_size !== '' && formData.has_pet !== null
      case 3: return formData.housing_type !== '' && formData.main_space.length > 0
      case 4: {
        // 조건부 질문이므로 선택된 공간에 따라 검증
        // renderStep4와 동일한 로직 사용 (원룸 케이스 고려)
        const isStudio = formData.housing_type === 'studio'
        const mainSpaces = isStudio ? ['all'] : formData.main_space
        
        const hasKitchen = mainSpaces.includes('kitchen') || mainSpaces.includes('all')
        const hasDressing = mainSpaces.includes('dressing') || mainSpaces.includes('all')
        const hasMedia = mainSpaces.includes('living') || mainSpaces.includes('bedroom') ||
          mainSpaces.includes('study') || mainSpaces.includes('all')

        // 디버깅 로그 추가
        console.log('[Step 4 Validation]', {
          housing_type: formData.housing_type,
          isStudio,
          mainSpaces,
          hasKitchen,
          hasDressing,
          hasMedia,
          cooking: formData.cooking,
          laundry: formData.laundry,
          media: formData.media
        })

        // 선택된 공간에 해당하는 질문이 모두 답변되었는지 확인
        if (hasKitchen && !formData.cooking) return false
        if (hasDressing && !formData.laundry) return false
        if (hasMedia && !formData.media) return false

        // 질문이 하나도 없으면 통과
        if (!hasKitchen && !hasDressing && !hasMedia) return true

        return true
      }
      case 5: return formData.priority !== '' && formData.priority_list.length > 0
      case 6: return formData.budget_level !== ''
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
        <div className="header-title">온보딩 {currentStep}/6</div>
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
            style={{ width: `${(currentStep / 6) * 100}%` }}
          />
        </div>

        <div className="onboarding-content">
          {currentStep === 1 && renderStep1()}
          {currentStep === 2 && renderStep2()}
          {currentStep === 3 && renderStep3()}
          {currentStep === 4 && renderStep4()}
          {currentStep === 5 && renderStep5()}
          {currentStep === 6 && renderStep6()}
        </div>

        <div className="nav-buttons">
          <button
            onClick={handleNext}
            disabled={!canProceed()}
            className={`nav-btn-primary ${!canProceed() ? 'disabled' : ''}`}
          >
            {currentStep === 6 ? '완료하고 추천받기' : '다음'}
          </button>
        </div>
      </div>
    </div>
  )
}

export default Onboarding
