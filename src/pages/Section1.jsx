import React, { useState } from 'react'
import ProductCard from '../components/ProductCard'
import StepIndicator from '../components/StepIndicator'

const Section1 = () => {
  const [selectedCategory, setSelectedCategory] = useState('냉장고')
  
  const categories = ['에어컨', '냉장고', '에어컨', 'TV']
  
  const products = [
    {
      id: 1,
      name: 'LG 올레드 TV (스탠드형)',
      model: 'OLED65B4NNA',
      rating: '5.0(340)',
      reason: '우리 아이에게 영화관 같은 기분을 선물할 수 있어요',
      price: {
        original: '월 65,400원',
        discount: '월 -26,000원',
        final: '월 39,400원',
      },
      specs: {
        color: '베이지/베이지',
        door: '네이처(메탈)',
        capacity: '367L/503L',
        power: '49.0kW',
      },
      isRecommended: false,
    },
    {
      id: 2,
      name: 'LG 올레드 TV (스탠드형)',
      model: 'OLED65B4NNA',
      rating: '5.0(340)',
      reason: '우리 아이에게 영화관 같은 기분을 선물할 수 있어요',
      price: {
        original: '월 65,400원',
        discount: '월 -26,000원',
        final: '월 39,400원',
      },
      specs: {
        color: '베이지/베이지',
        door: '네이처(메탈)',
        capacity: '367L/503L',
        power: '49.0kW',
      },
      isRecommended: true,
    },
    {
      id: 3,
      name: 'LG 올레드 TV (스탠드형)',
      model: 'OLED65B4NNA',
      rating: '5.0(340)',
      reason: '우리 아이에게 영화관 같은 기분을 선물할 수 있어요',
      price: {
        original: '월 65,400원',
        discount: '월 -26,000원',
        final: '월 39,400원',
      },
      specs: {
        color: '베이지/베이지',
        door: '네이처(메탈)',
        capacity: '367L/503L',
        power: '49.0kW',
      },
      isRecommended: false,
    },
  ]

  return (
    <div className="min-h-screen bg-[#444444] relative overflow-hidden">
      {/* Background Image Section */}
      <div className="relative w-full max-w-[1920px] mx-auto h-[1080px]">
        {/* Background Image */}
        <div className="absolute inset-0">
          <div className="w-full h-full bg-gradient-to-b from-gray-200 to-gray-400" />
          {/* 실제 배경 이미지가 있다면 여기에 추가 */}
        </div>
        
        {/* Top Beige Bar */}
        <div className="absolute top-0 left-[390px] w-[521px] h-[34px] bg-[#ece0db]" />
        
        {/* Bottom Gray Bar */}
        <div className="absolute top-[976px] left-[834px] w-[539px] h-[41px] bg-[#f1f1f1]" />
        
        {/* White Content Area */}
        <div className="absolute top-[280px] left-0 w-full h-[799px] bg-[#f9f9f9]">
          {/* Left Side - Step Indicators */}
          <div className="absolute left-[116px] top-[105px] w-[215px]">
            <StepIndicator />
          </div>
          
          {/* Title */}
          <div className="absolute left-[463px] top-[76px] text-center">
            <div className="text-[15px] text-black mb-1 leading-[16.275px]">
              고객님에게 꼭 맞는
            </div>
            <div className="text-[20px] font-bold text-black leading-[21.7px]">
              추천 후보 목록
            </div>
          </div>
          
          {/* Category Filter */}
          <div className="absolute left-[750px] top-[207px] flex gap-2">
            {categories.map((category, index) => (
              <button
                key={index}
                onClick={() => setSelectedCategory(category)}
                className={`px-4 py-2 rounded-full text-[14px] font-normal border transition-colors h-8 ${
                  selectedCategory === category
                    ? 'bg-black text-white border-[#eeeeee]'
                    : 'bg-white text-black border-[#eeeeee]'
                }`}
              >
                {category}
              </button>
            ))}
          </div>
          
          {/* Product Cards */}
          <div className="absolute left-[480px] top-[207px] flex gap-[13px]">
            {products.map((product) => (
              <ProductCard key={product.id} product={product} />
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}

export default Section1

