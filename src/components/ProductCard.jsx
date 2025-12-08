import React from 'react'
import { formatPrice } from '../utils/validation'

const ProductCard = ({ product, isRecommended = false, purchaseType = '가전구독', contractPeriod = '6년' }) => {
  // 구매 유형에 따라 표시할 정보 결정
  const showContractInfo = purchaseType === '가전구독'
  const showSpecs = product.specs && Object.keys(product.specs).length > 0 && purchaseType === '일반구매'
  
  // 가격 정보 안전하게 가져오기
  const getPriceDisplay = () => {
    if (product.price?.final) {
      return product.price.final
    }
    if (product.discount_price) {
      return formatPrice(product.discount_price)
    }
    if (product.price) {
      return formatPrice(product.price)
    }
    return '가격 정보 없음'
  }

  // 이미지 에러 처리
  const handleImageError = (e) => {
    e.target.src = 'https://via.placeholder.com/200x150?text=No+Image'
  }

  return (
    <div className={`w-full rounded-xl bg-white shadow-sm hover:shadow-md transition-shadow ${
      isRecommended ? 'border-2 border-[#EA1917]' : 'border border-gray-200'
    }`}>
      <div className="p-4">
        {/* Product Header */}
        <div className="flex justify-between items-start mb-3">
          <div className="flex-1 pr-4">
            <h3 className="text-lg font-bold text-[#1A1A1A] mb-2 line-clamp-2">
              {product.name}
            </h3>
            <div className="flex items-center gap-2 flex-wrap">
              {product.model && (
                <span className="text-xs text-gray-600">{product.model}</span>
              )}
              {product.rating && (
                <span className="text-xs text-gray-600">⭐ {product.rating}</span>
              )}
            </div>
          </div>
          {/* Product Image */}
          <div className="flex-shrink-0">
            {product.image_url ? (
              <img 
                src={product.image_url} 
                alt={product.name}
                className="w-20 h-20 object-contain rounded-lg bg-gray-50"
                onError={handleImageError}
              />
            ) : (
              <div className="w-20 h-20 bg-gray-200 rounded-lg flex items-center justify-center">
                <span className="text-gray-400 text-xs">이미지 없음</span>
              </div>
            )}
          </div>
        </div>
        
        {/* Recommendation Reason */}
        <div className="bg-[#F4F4F4] rounded-lg p-3 mb-4">
          <div className="text-xs font-bold text-[#EA1917] mb-1">
            추천 이유
          </div>
          <div className="text-sm text-[#1C1C1C] leading-relaxed">
            {product.reason || product.recommend_reason || '고객님의 선호도에 맞는 제품입니다.'}
          </div>
        </div>
        
        {/* Product Specs and Price Info */}
        <div className="bg-[#F4F4F4] rounded-lg p-3">
          {showSpecs ? (
            <>
              {/* Specs for 일반구매 */}
              <div className="space-y-2 text-xs mb-4">
                {product.specs.color && (
                  <div className="flex justify-between">
                    <span className="text-gray-600">색상</span>
                    <span className="text-gray-700">{product.specs.color}</span>
                  </div>
                )}
                {product.specs.door && (
                  <div className="flex justify-between">
                    <span className="text-gray-600">도어재질</span>
                    <span className="text-gray-700">{product.specs.door}</span>
                  </div>
                )}
                {product.specs.power && (
                  <div className="flex justify-between">
                    <span className="text-gray-600">소비전력</span>
                    <span className="text-gray-700">{product.specs.power}</span>
                  </div>
                )}
                {product.specs.capacity && (
                  <div className="flex justify-between">
                    <span className="text-gray-600">냉동/냉장</span>
                    <span className="text-gray-700">{product.specs.capacity}</span>
                  </div>
                )}
              </div>
              
              {/* Price Info for 일반구매 */}
              <div className="space-y-2 text-xs">
                {product.price?.discount && (
                  <div className="flex justify-between">
                    <span className="text-gray-700">제휴카드 할인</span>
                    <span className="text-gray-700">{product.price.discount}</span>
                  </div>
                )}
                <div className="flex justify-between items-center pt-2 border-t border-gray-300">
                  <span className="text-xs font-semibold text-gray-700">최대혜택가</span>
                  <span className="text-lg font-bold text-[#EA1917]">
                    {getPriceDisplay()}
                  </span>
                </div>
              </div>
            </>
          ) : showContractInfo ? (
            <>
              {/* Contract Info for 가전구독 */}
              <div className="space-y-2 text-xs mb-4">
                <div className="flex justify-between">
                  <span className="text-gray-600">계약기간</span>
                  <span className="text-gray-700">{contractPeriod || product.contractPeriod || '6년'}</span>
                </div>
                {product.careServiceCycle && (
                  <div className="flex justify-between">
                    <span className="text-gray-600">케어서비스 주기</span>
                    <span className="text-gray-700">{product.careServiceCycle}</span>
                  </div>
                )}
                {product.careServiceType && (
                  <div className="flex justify-between">
                    <span className="text-gray-600">케어서비스 유형</span>
                    <span className="text-gray-700">{product.careServiceType}</span>
                  </div>
                )}
              </div>
              
              {/* Price Info for 가전구독 */}
              <div className="space-y-2 text-xs">
                {product.price?.original && (
                  <div className="flex justify-between">
                    <span className="text-gray-700">이용 요금</span>
                    <span className="text-gray-700">{product.price.original}</span>
                  </div>
                )}
                {product.price?.discount && (
                  <div className="flex justify-between">
                    <span className="text-gray-700">제휴카드 할인</span>
                    <span className="text-gray-700">{product.price.discount}</span>
                  </div>
                )}
                <div className="flex justify-between items-center pt-2 border-t border-gray-300">
                  <span className="text-xs font-semibold text-gray-700">최대혜택가</span>
                  <span className="text-lg font-bold text-[#EA1917]">
                    {getPriceDisplay()}
                  </span>
                </div>
              </div>
            </>
          ) : (
            <>
              {/* 기본 가격 정보 */}
              <div className="space-y-2 text-xs">
                {product.price?.discount && (
                  <div className="flex justify-between">
                    <span className="text-gray-700">제휴카드 할인</span>
                    <span className="text-gray-700">{product.price.discount}</span>
                  </div>
                )}
                <div className="flex justify-between items-center pt-2 border-t border-gray-300">
                  <span className="text-xs font-semibold text-gray-700">최대혜택가</span>
                  <span className="text-lg font-bold text-[#EA1917]">
                    {getPriceDisplay()}
                  </span>
                </div>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  )
}

export default ProductCard
