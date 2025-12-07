import React from 'react'

const ProductCard = ({ product, isRecommended = false, purchaseType = '가전구독', contractPeriod = '6년' }) => {
  // 구매 유형에 따라 표시할 정보 결정
  const showContractInfo = purchaseType === '가전구독' && !product.specs
  const showSpecs = product.specs && purchaseType === '일반구매'

  return (
    <div className={`w-[320px] rounded-[10px] bg-white ${
      isRecommended ? 'border-2 border-[#ff456d]' : 'border border-[#eeeeee]'
    }`}>
      <div className="p-[14px]">
        {/* Product Header */}
        <div className="flex justify-between items-start mb-[10px]">
          <div className="flex-1">
            <div className="text-[16px] font-bold text-black mb-[6px] leading-[19.09px] font-pretendard">
              {product.name}
            </div>
            <div className="flex items-center gap-2">
              <span className="text-[12px] text-black leading-[14.32px] font-pretendard">{product.model || product.model_number}</span>
              {product.rating && (
                <span className="text-[12px] text-black leading-[14.32px] font-pretendard">{product.rating}</span>
              )}
            </div>
          </div>
          {/* Product Image */}
          {product.image_url ? (
            <img 
              src={product.image_url} 
              alt={product.name}
              className="w-[69px] h-[36px] object-cover rounded flex-shrink-0"
            />
          ) : (
            <div className="w-[69px] h-[36px] bg-gray-200 rounded flex-shrink-0" />
          )}
        </div>
        
        {/* Recommendation Reason */}
        <div className="bg-[#f4f4f4] rounded-[5px] p-3 mb-4 min-h-[65px]">
          <div className="text-[11px] font-bold text-[#ff456d] mb-1 leading-[13.13px] font-pretendard">
            추천 이유
          </div>
          <div className="text-[14px] text-[#1c1c1c] leading-[16.71px] font-pretendard">
            {product.reason || product.recommend_reason || '고객님의 선호도에 맞는 제품입니다.'}
          </div>
        </div>
        
        {/* Product Specs and Price Info */}
        <div className="bg-[#f4f4f4] rounded-[5px] p-3">
          {showSpecs ? (
            <>
              {/* Specs for 일반구매 */}
              <div className="space-y-[14px] text-[11px] mb-4">
                {product.specs.color && (
                  <div className="flex justify-between">
                    <span className="text-[#666666] leading-[13.13px] font-pretendard">색상</span>
                    <span className="text-[#666666] leading-[13.13px] font-pretendard">{product.specs.color}</span>
                  </div>
                )}
                {product.specs.door && (
                  <div className="flex justify-between">
                    <span className="text-[#666666] leading-[13.13px] font-pretendard">도어재질</span>
                    <span className="text-[#666666] leading-[13.13px] font-pretendard">{product.specs.door}</span>
                  </div>
                )}
                {product.specs.power && (
                  <div className="flex justify-between">
                    <span className="text-[#666666] leading-[13.13px] font-pretendard">소비전력</span>
                    <span className="text-[#666666] leading-[13.13px] font-pretendard">{product.specs.power}</span>
                  </div>
                )}
                {product.specs.capacity && (
                  <div className="flex justify-between">
                    <span className="text-[#666666] leading-[13.13px] font-pretendard">냉동/냉장</span>
                    <span className="text-[#666666] leading-[13.13px] font-pretendard">{product.specs.capacity}</span>
                  </div>
                )}
              </div>
              
              {/* Price Info for 일반구매 */}
              <div className="space-y-[14px] text-[11px]">
                {product.price?.discount && (
                  <div className="flex justify-between">
                    <span className="text-black leading-[13.13px] font-pretendard">제휴카드 할인 &gt;</span>
                    <span className="text-black leading-[13.13px] font-pretendard">{product.price.discount}</span>
                  </div>
                )}
                <div className="flex justify-between items-center">
                  <span className="text-[11px] text-black leading-[13.13px] font-pretendard">최대혜택가</span>
                  <span className="text-[16px] font-bold text-[#ea1917] leading-[19.09px] font-pretendard">
                    {product.price?.final || formatPrice(product.discount_price || product.price)}
                  </span>
                </div>
              </div>
            </>
          ) : showContractInfo ? (
            <>
              {/* Contract Info for 가전구독 */}
              <div className="space-y-[14px] text-[11px] mb-4">
                <div className="flex justify-between">
                  <span className="text-[#666666] leading-[13.13px] font-pretendard">계약기간</span>
                  <span className="text-[#666666] leading-[13.13px] font-pretendard">{contractPeriod || product.contractPeriod}</span>
                </div>
                {product.careServiceCycle && (
                  <div className="flex justify-between">
                    <span className="text-[#666666] leading-[13.13px] font-pretendard">케어서비스 주기</span>
                    <span className="text-[#666666] leading-[13.13px] font-pretendard">{product.careServiceCycle}</span>
                  </div>
                )}
                {product.careServiceType && (
                  <div className="flex justify-between">
                    <span className="text-[#666666] leading-[13.13px] font-pretendard">케어서비스 유형</span>
                    <span className="text-[#666666] leading-[13.13px] font-pretendard">{product.careServiceType}</span>
                  </div>
                )}
              </div>
              
              {/* Price Info for 가전구독 */}
              <div className="space-y-[14px] text-[11px]">
                {product.price?.original && (
                  <div className="flex justify-between">
                    <span className="text-black leading-[13.13px] font-pretendard">이용 요금 &gt;</span>
                    <span className="text-black leading-[12.87px] font-pretendard">{product.price.original}</span>
                  </div>
                )}
                {product.price?.discount && (
                  <div className="flex justify-between">
                    <span className="text-black leading-[13.13px] font-pretendard">제휴카드 할인 &gt;</span>
                    <span className="text-black leading-[13.13px] font-pretendard">{product.price.discount}</span>
                  </div>
                )}
                <div className="flex justify-between items-center">
                  <span className="text-[11px] text-black leading-[13.13px] font-pretendard">최대혜택가</span>
                  <span className="text-[16px] font-bold text-[#ea1917] leading-[19.09px] font-pretendard">
                    {product.price?.final || formatPrice(product.discount_price || product.price)}
                  </span>
                </div>
              </div>
            </>
          ) : (
            <>
              {/* 기본 가격 정보 */}
              <div className="space-y-[14px] text-[11px]">
                {product.price?.discount && (
                  <div className="flex justify-between">
                    <span className="text-black leading-[13.13px] font-pretendard">제휴카드 할인 &gt;</span>
                    <span className="text-black leading-[13.13px] font-pretendard">{product.price.discount}</span>
                  </div>
                )}
                <div className="flex justify-between items-center">
                  <span className="text-[11px] text-black leading-[13.13px] font-pretendard">최대혜택가</span>
                  <span className="text-[16px] font-bold text-[#ea1917] leading-[19.09px] font-pretendard">
                    {product.price?.final || formatPrice(product.discount_price || product.price)}
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

// 가격 포맷팅 헬퍼 함수
const formatPrice = (price) => {
  if (typeof price === 'number') {
    return new Intl.NumberFormat('ko-KR').format(price) + '원'
  }
  return price || '가격 정보 없음'
}

export default ProductCard

