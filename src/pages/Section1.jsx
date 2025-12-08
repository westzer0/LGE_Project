import React from 'react'
import { useNavigate } from 'react-router-dom'

const Section1 = () => {
  const navigate = useNavigate()

  const handleStartOnboarding = () => {
    navigate('/onboarding')
  }

  return (
    <div className="min-h-screen bg-gradient-to-b from-[#F7F4EF] to-white">
      {/* Hero Section */}
      <div className="max-w-7xl mx-auto px-4 py-20">
        <div className="text-center mb-16">
          <h1 className="text-5xl font-bold text-[#1A1A1A] mb-6">
            LG 가전 패키지 추천
          </h1>
          <p className="text-xl text-gray-600 mb-8 max-w-2xl mx-auto">
            공간·취향·예산 데이터를 바탕으로<br />
            최적의 LG 가전 패키지를 제안합니다
          </p>
          <button
            onClick={handleStartOnboarding}
            className="px-8 py-4 bg-[#A50034] text-white rounded-lg text-lg font-semibold hover:bg-[#C4314B] transition-colors shadow-lg hover:shadow-xl"
          >
            추천받기 시작하기
          </button>
        </div>

        {/* Features */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8 mt-20">
          <div className="text-center p-6">
            <div className="text-4xl mb-4">🎨</div>
            <h3 className="text-xl font-bold mb-2">취향 분석</h3>
            <p className="text-gray-600">
              디자인 스타일과 선호도를 분석하여<br />
              맞춤형 제품을 추천합니다
            </p>
          </div>
          <div className="text-center p-6">
            <div className="text-4xl mb-4">🏠</div>
            <h3 className="text-xl font-bold mb-2">공간 최적화</h3>
            <p className="text-gray-600">
              주거 형태와 평수를 고려하여<br />
              공간에 맞는 가전을 제안합니다
            </p>
          </div>
          <div className="text-center p-6">
            <div className="text-4xl mb-4">💰</div>
            <h3 className="text-xl font-bold mb-2">예산 고려</h3>
            <p className="text-gray-600">
              예산 수준에 맞는<br />
              최적의 가전 패키지를 구성합니다
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}

export default Section1
