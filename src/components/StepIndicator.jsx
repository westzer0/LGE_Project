import React from 'react'

const StepIndicator = () => {
  const steps = [
    {
      number: 1,
      title: 'STEP 1 취향 파악',
      status: 'active',
      description: '디자인 취향에 맞는 모델 찾는중',
      items: ['OLED65B4NNA', 'OLED65B4NNA', 'OLED65B4NNA', 'OLED65B4NNA', 'OLED65B4NNA', 'OLED65B4NNA'],
    },
    {
      number: 2,
      title: 'STEP 2 공간 정보 파악',
      status: 'active',
      description: '공간 정보에 적합한 사이즈 모델 검색중',
      items: ['OLED65B4NNA', 'OLED65B4NNA', 'OLED65B4NNA', 'OLED65B4NNA', 'OLED65B4NNA', 'OLED65B4NNA'],
    },
    {
      number: 3,
      title: 'STEP 3 가족 구성 정보 파악',
      status: 'active',
      description: '가족 구성원들과 함께 사용하기 편한 모델은?',
      items: ['OLED65B4NNA', 'OLED65B4NNA', 'OLED65B4NNA', 'OLED65B4NNA', 'OLED65B4NNA', 'OLED65B4NNA'],
    },
  ]

  return (
    <div className="flex flex-col">
      {steps.map((step, index) => (
        <div key={step.number} className="flex items-start gap-3 relative">
          {/* Circle Indicator */}
          <div className="flex flex-col items-center mt-1">
            <div className={`w-4 h-4 rounded-full ${
              step.status === 'active' ? 'bg-[#e4e4e4]' : 'bg-[#d9d9d9]'
            }`} />
            {index < steps.length - 1 && (
              <div className="w-0.5 h-[253px] bg-transparent" />
            )}
          </div>
          
          {/* Step Content */}
          <div className="flex-1">
            <div className="text-[12px] font-bold text-[#d9d9d9] mb-2 leading-[14.52px]">
              {step.title}
            </div>
            <div className="text-[12px] text-[#d9d9d9] mb-2 leading-[13.02px]">
              {step.description}
            </div>
            <div className="space-y-1 mb-2">
              {step.items.map((item, itemIndex) => (
                <div key={itemIndex} className="text-[12px] text-[#d9d9d9] leading-[14.32px]">
                  {item}
                </div>
              ))}
            </div>
            {/* Loading dots */}
            <div className="flex gap-1 mt-2">
              <div className="w-0.5 h-0.5 rounded-full bg-[#d9d9d9]" />
              <div className="w-0.5 h-0.5 rounded-full bg-[#d9d9d9]" />
              <div className="w-0.5 h-0.5 rounded-full bg-[#d9d9d9]" />
            </div>
          </div>
        </div>
      ))}
    </div>
  )
}

export default StepIndicator

