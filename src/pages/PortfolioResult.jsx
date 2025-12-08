import React, { useState, useEffect, useMemo, useCallback } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'
import ProductCard from '../components/ProductCard'
import { apiRequest } from '../utils/api'
import { formatPrice, parsePrice } from '../utils/validation'

const PortfolioResult = () => {
  const location = useLocation()
  const navigate = useNavigate()
  const [purchaseType, setPurchaseType] = useState('가전구독')
  const [contractPeriod, setContractPeriod] = useState('6년')
  const [products, setProducts] = useState([])
  const [loading, setLoading] = useState(true)

  // 가격 계산 최적화 (useMemo 사용)
  const benefitInfo = useMemo(() => {
    if (products.length === 0) {
      return {
        totalPrice: 0,
        totalDiscount: 0,
        totalBenefit: 0,
        items: []
      }
    }

    let totalPrice = 0
    let totalDiscount = 0
    const categoryMap = new Map()

    products.forEach((product) => {
      let price = 0
      let discount = 0
      
      if (purchaseType === '가전구독') {
        // 가전구독: 월 가격 기준
        price = parsePrice(product.price?.final || product.price?.original || '0')
        discount = parsePrice(product.price?.discount || '0')
      } else {
        // 일반구매: 일시불 가격 기준
        price = parsePrice(product.price?.final || '0')
        discount = parsePrice(product.price?.discount || '0')
      }
      
      totalPrice += price
      totalDiscount += Math.abs(discount)
      
      // 카테고리별로 그룹화
      const category = product.category || '기타'
      if (categoryMap.has(category)) {
        categoryMap.set(category, categoryMap.get(category) + price)
      } else {
        categoryMap.set(category, price)
      }
    })

    // 카테고리별 항목 생성
    const items = Array.from(categoryMap.entries()).map(([category, price]) => ({
      category: category,
      price: formatPrice(price)
    }))

    const totalBenefit = totalPrice - totalDiscount

    return {
      totalPrice,
      totalDiscount,
      totalBenefit,
      items
    }
  }, [purchaseType, products])



  // 초기 데이터 로드
  useEffect(() => {
    // location.state에서 추천 결과 가져오기 (온보딩에서 전달된 경우)
    if (location.state?.recommendations) {
      console.log('[PortfolioResult] location.state에서 추천 결과 로드:', location.state)
      const recommendations = location.state.recommendations
      
      if (!recommendations || recommendations.length === 0) {
        console.warn('[PortfolioResult] 추천 결과가 비어있습니다.')
        loadSampleData()
        setLoading(false)
        return
      }
      
      const formattedProducts = recommendations.map((rec) => {
        // API 응답 형식에 맞게 변환
        // rec 구조: { product_id, name, model, category, price, discount_price, image_url, reason, score, ... }
        const priceValue = rec.price || rec.discount_price || 0
        const discountValue = rec.discount_price || 0
        
        // 월 가격 계산 (가전구독 기준)
        const monthlyPrice = Math.floor(priceValue / 72) // 6년 기준
        const monthlyDiscount = Math.floor(discountValue / 72)
        
        return {
          id: rec.product_id || rec.id,
          name: rec.name || rec.product_name || '제품명 없음',
          model: rec.model || rec.model_number || '',
          rating: rec.rating || '',
          reason: rec.reason || rec.recommend_reason || '고객님의 선호도에 맞는 제품입니다.',
          category: rec.category || rec.main_category || '기타',
          specs: rec.specs || {},
          price: {
            original: monthlyPrice > 0 ? `월 ${formatPrice(monthlyPrice)}` : undefined,
            discount: monthlyDiscount > 0 ? `월 -${formatPrice(monthlyDiscount)}` : undefined,
            final: (monthlyPrice - monthlyDiscount) > 0 ? `월 ${formatPrice(monthlyPrice - monthlyDiscount)}` : (monthlyPrice > 0 ? `월 ${formatPrice(monthlyPrice)}` : undefined),
          },
          image_url: rec.image_url || '',
          isRecommended: rec.is_recommended || false,
          score: rec.score || rec.taste_score || 0,
        }
      })
      
      console.log('[PortfolioResult] 포맷팅된 제품:', formattedProducts)
      setProducts(formattedProducts)
      setLoading(false)
      return
    }

    // URL 파라미터에서 portfolio_id 가져오기
    const urlParams = new URLSearchParams(window.location.search)
    const portfolioId = urlParams.get('portfolio_id') || urlParams.get('id')
    
    if (portfolioId) {
      fetchPortfolioData(portfolioId)
    } else {
      // 기본 샘플 데이터
      loadSampleData()
      setLoading(false)
    }
  }, [location.state])

  const fetchPortfolioData = async (portfolioId) => {
    try {
      setLoading(true)
      console.log(`[PortfolioResult] 포트폴리오 조회: ${portfolioId}`)
      
      const data = await apiRequest(`/api/portfolio/${portfolioId}/`, {
        method: 'GET',
      })
      
      console.log('[PortfolioResult] 포트폴리오 응답:', data)
      
      if (data.success && data.portfolio) {
        // 포트폴리오 데이터에서 제품 정보 추출
        const portfolioProducts = data.portfolio.products || []
        
        if (portfolioProducts.length === 0) {
          console.warn('[PortfolioResult] 포트폴리오에 제품이 없습니다.')
          loadSampleData()
          return
        }
        
        // 제품 데이터를 포맷팅
        const formattedProducts = portfolioProducts.map((product) => {
          // 가격 정보 포맷팅
          let priceInfo = {}
          const price = product.price || product.discount_price || 0
          const discountPrice = product.discount_price || 0
          
          if (purchaseType === '가전구독') {
            // 가전구독 가격 정보 (월 가격으로 변환)
            const monthlyPrice = Math.floor(price / 72) // 6년 기준
            const monthlyDiscount = Math.floor(discountPrice / 72)
            priceInfo = {
              original: monthlyPrice > 0 ? `월 ${formatPrice(monthlyPrice)}` : undefined,
              discount: monthlyDiscount > 0 ? `월 -${formatPrice(monthlyDiscount)}` : undefined,
              final: (monthlyPrice - monthlyDiscount) > 0 ? `월 ${formatPrice(monthlyPrice - monthlyDiscount)}` : undefined,
            }
          } else {
            // 일반구매 가격 정보
            priceInfo = {
              discount: discountPrice > 0 ? `-${formatPrice(discountPrice)}` : undefined,
              final: formatPrice(price - discountPrice),
            }
          }
          
          return {
            id: product.id || product.product_id,
            name: product.name || product.product_name || '제품명 없음',
            model: product.model || product.model_number || '',
            rating: product.rating || '',
            reason: product.reason || product.recommend_reason || '고객님의 선호도에 맞는 제품입니다.',
            category: product.category || '기타',
            specs: product.specs || {},
            contractPeriod: product.contract_period || '6년',
            careServiceCycle: product.care_service_cycle || '',
            careServiceType: product.care_service_type || '',
            price: priceInfo,
            image_url: product.image_url || '',
            isRecommended: product.is_recommended || false,
          }
        })
        
        console.log('[PortfolioResult] 포맷팅된 제품:', formattedProducts)
        setProducts(formattedProducts)
      } else {
        console.error('[PortfolioResult] 포트폴리오 조회 실패:', data.error)
        loadSampleData()
      }
    } catch (error) {
      console.error('[PortfolioResult] 포트폴리오 데이터 로드 실패:', error)
      alert(`포트폴리오를 불러올 수 없습니다: ${error.message}`)
      // 에러 발생 시 샘플 데이터 사용
      loadSampleData()
    } finally {
      setLoading(false)
    }
  }

  const loadSampleData = () => {
    setProducts([
      {
        id: 1,
        name: 'LG 올레드 TV (스탠드형)',
        model: 'OLED65B4NNA',
        rating: '5.0(340)',
        reason: '우리 아이에게 영화관 같은 기분을 선물할 수 있어요',
        category: 'TV',
        contractPeriod: '6년',
        careServiceCycle: '12개월마다',
        careServiceType: '프리미엄',
        price: {
          original: '월 65,400원',
          discount: '월 -26,000원',
          final: '월 39,400원',
        },
      },
      {
        id: 2,
        name: 'LG 디오스 오브제컬렉션 매직스페이스 냉장고',
        model: 'S834MBC13',
        rating: '4.8(256)',
        reason: '넉넉한 수납 공간으로 깔끔한 주방을 완성할 수 있어요',
        category: '냉장고',
        specs: {
          color: '베이지/베이지',
          door: '네이처(메탈)',
          capacity: '367L/503L',
          power: '49.0kW',
        },
        price: {
          discount: '-126,000원',
          final: '2,600,000원',
        },
        isRecommended: true,
      },
      {
        id: 3,
        name: 'LG 휘센 스탠드형 에어컨',
        model: 'FQ17VDWWK',
        rating: '4.9(189)',
        reason: '시원한 바람으로 여름을 시원하게 보낼 수 있어요',
        category: '에어컨',
        contractPeriod: '6년',
        careServiceCycle: '12개월마다',
        careServiceType: '프리미엄',
        price: {
          original: '월 89,400원',
          discount: '월 -20,000원',
          final: '월 69,400원',
        },
      },
    ])
  }

  const handleRefresh = useCallback(() => {
    // 다시 추천받기 로직
    navigate('/onboarding')
  }, [navigate])

  const handlePurchase = useCallback(() => {
    // 구매하기 로직
    console.log('[PortfolioResult] 구매하기 클릭')
    // TODO: 구매 페이지로 이동 또는 모달 표시
  }, [])

  const handleConsultation = useCallback(() => {
    // 베스트샵 상담예약 로직
    console.log('[PortfolioResult] 베스트샵 상담예약 클릭')
    // TODO: 상담예약 API 호출 또는 모달 표시
  }, [])

  if (loading) {
    return (
      <div className="min-h-screen bg-white flex items-center justify-center">
        <div className="text-lg">로딩 중...</div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-white relative overflow-hidden">
      {/* Background Image Section */}
      <div className="relative w-full max-w-[1920px] mx-auto h-[1080px]">
        {/* Background Image */}
        <div className="absolute inset-0">
          <div className="w-full h-full bg-gradient-to-b from-gray-200 to-gray-400" />
        </div>
        
        {/* Top Beige Bar */}
        <div className="absolute top-0 left-[519px] w-[521px] h-[36px] bg-[#ece0db]" />
        
        {/* Bottom Gray Bar */}
        <div className="absolute top-[1036px] left-[862px] w-[539px] h-[43px] bg-[#f1f1f1]" />
        
        {/* Light Gray Background */}
        <div className="absolute top-[293px] left-0 w-full h-[1067px] bg-[#f9f9f9]" />
        
        {/* White Content Area */}
        <div className="absolute top-[293px] left-[101px] w-[1771px] h-[740px] bg-white">
          {/* Title Section */}
          <div className="absolute left-[1070px] top-[33px] text-center">
            <div className="text-[15px] text-black mb-1 leading-[17.9px] font-pretendard">
              고객님에게 꼭 맞는
            </div>
            <div className="text-[20px] font-bold text-black leading-[23.87px] font-pretendard">
              모던한 실속형 가전 패키지가 도착했어요.
            </div>
          </div>
          
          {/* Purchase Type Toggle */}
          <div className="absolute left-[879px] top-[0px] flex gap-0">
            <button
              onClick={() => setPurchaseType('가전구독')}
              className={`px-[12.8px] py-2 rounded-full text-[14px] font-normal h-8 transition-colors font-pretendard ${
                purchaseType === '가전구독'
                  ? 'bg-[#212121] text-white'
                  : 'bg-white text-black border border-[#eeeeee]'
              }`}
            >
              가전구독
            </button>
            <button
              onClick={() => setPurchaseType('일반구매')}
              className={`px-[12.8px] py-2 rounded-full text-[14px] font-normal h-8 transition-colors font-pretendard ${
                purchaseType === '일반구매'
                  ? 'bg-[#212121] text-white'
                  : 'bg-white text-black border border-[#eeeeee]'
              }`}
            >
              일반구매
            </button>
          </div>
          
          {/* Contract Period Selection */}
          {purchaseType === '가전구독' && (
            <div className="absolute left-[790px] top-[52px] flex gap-0">
              {['3년', '4년', '5년', '6년'].map((period) => (
                <button
                  key={period}
                  onClick={() => setContractPeriod(period)}
                  className={`px-[12.8px] py-2 rounded-full text-[14px] font-normal h-8 transition-colors font-pretendard ${
                    contractPeriod === period
                      ? 'bg-[#212121] text-white border border-[#eeeeee]'
                      : 'bg-white text-black border border-[#eeeeee]'
                  }`}
                >
                  {period}
                </button>
              ))}
            </div>
          )}
          
          {/* Refresh Button */}
          <div className="absolute left-[0px] top-[0px] flex items-center gap-2">
            <svg className="w-6 h-6 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
            </svg>
            <button 
              onClick={handleRefresh}
              className="text-[14px] text-black leading-[16.71px] font-pretendard hover:underline"
            >
              다시 추천받기
            </button>
          </div>
          
          {/* Product Cards - 3개만 표시 */}
          <div className="absolute left-[0px] top-[106px] flex gap-[13px]" style={{ width: '1032px' }}>
            {products.slice(0, 3).map((product) => (
              <ProductCard 
                key={product.id} 
                product={product} 
                isRecommended={product.isRecommended}
                purchaseType={purchaseType}
                contractPeriod={contractPeriod}
              />
            ))}
          </div>
          
          {/* Benefit Info Box */}
          <div className="absolute right-[0px] top-[106px] w-[304px]">
            <div className="bg-[#eaeaea] rounded-[10px] p-6">
              <div className="text-[18px] font-bold text-black mb-6 leading-[21.48px] font-pretendard">
                혜택 정보
              </div>
              
              <div className="space-y-[11px] mb-6">
                <div className="flex justify-between items-center">
                  <span className="text-[14px] text-black leading-[16.71px] font-pretendard">총 구매금액</span>
                  <span className="text-[15px] text-[#8f8f8f] leading-[17.9px] font-pretendard">
                    {formatPrice(benefitInfo.totalPrice)}
                  </span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-[14px] text-black leading-[16.71px] font-pretendard">할인혜택</span>
                  <span className="text-[15px] text-black leading-[17.9px] font-pretendard">
                    -{formatPrice(benefitInfo.totalDiscount)}
                  </span>
                </div>
              </div>
              
              <div className="border-t border-[#9f9f9f] pt-4 mb-6">
                <div className="flex justify-between items-center mb-2">
                  <span className="text-[15px] font-bold text-black leading-[17.9px] font-pretendard">총 혜택가</span>
                  <span className="text-[20px] font-bold text-black leading-[23.87px] font-pretendard">
                    {purchaseType === '가전구독' 
                      ? `월 ${formatPrice(benefitInfo.totalBenefit)}`
                      : formatPrice(benefitInfo.totalBenefit)
                    }
                  </span>
                </div>
              </div>
              
              <div className="mb-6">
                <div className="text-[14px] text-[#666666] mb-3 leading-[16.71px] font-pretendard">상세 항목</div>
                <div className="space-y-[11px]">
                  {benefitInfo.items.length > 0 ? (
                    benefitInfo.items.map((item, index) => (
                      <div key={index} className="flex justify-between items-center">
                        <span className="text-[14px] text-black leading-[16.71px] font-pretendard">{item.category}</span>
                        <span className="text-[14px] text-black leading-[16.71px] font-pretendard">{item.price}</span>
                      </div>
                    ))
                  ) : (
                    <div className="text-[14px] text-[#666666] leading-[16.71px] font-pretendard">
                      상세 정보가 없습니다.
                    </div>
                  )}
                </div>
              </div>
              
              {/* Action Buttons */}
              <div className="space-y-3">
                <button 
                  onClick={handlePurchase}
                  className="w-full h-12 bg-[#ea1917] text-white rounded-[10px] text-[13px] font-normal border border-[#d9d9d9] leading-[15.51px] font-pretendard hover:bg-[#d0100e] transition-colors"
                >
                  구매하기
                </button>
                <button 
                  onClick={handleConsultation}
                  className="w-full h-12 bg-[#212121] text-white rounded-[10px] text-[13px] font-normal border border-[#d9d9d9] leading-[15.51px] font-pretendard hover:bg-[#333333] transition-colors"
                >
                  베스트샵 상담예약
                </button>
              </div>
              
              {/* Social Share Buttons */}
              <div className="flex gap-3 mt-6 justify-center">
                <button className="w-12 h-12 bg-white border border-[#d9d9d9] rounded-full flex items-center justify-center hover:bg-gray-50 transition-colors">
                  <svg className="w-5 h-5 text-gray-600" fill="currentColor" viewBox="0 0 24 24">
                    <path d="M18 16.08c-.76 0-1.44.3-1.96.77L8.91 12.7c.05-.23.09-.46.09-.7s-.04-.47-.09-.7l7.05-4.11c.54.5 1.25.81 2.04.81 1.66 0 3-1.34 3-3s-1.34-3-3-3-3 1.34-3 3c0 .24.04.47.09.7L8.04 9.81C7.5 9.31 6.79 9 6 9c-1.66 0-3 1.34-3 3s1.34 3 3 3c.79 0 1.5-.31 2.04-.81l7.12 4.16c-.05.21-.08.43-.08.65 0 1.61 1.31 2.92 2.92 2.92 1.61 0 2.92-1.31 2.92-2.92s-1.31-2.92-2.92-2.92z"/>
                  </svg>
                </button>
                <button className="w-12 h-12 bg-white border border-[#d9d9d9] rounded-full flex items-center justify-center hover:bg-gray-50 transition-colors">
                  <svg className="w-5 h-5 text-gray-600" fill="currentColor" viewBox="0 0 24 24">
                    <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"/>
                  </svg>
                </button>
                <button className="w-12 h-12 bg-white border border-[#d9d9d9] rounded-full flex items-center justify-center hover:bg-gray-50 transition-colors">
                  <svg className="w-5 h-5 text-gray-600" fill="currentColor" viewBox="0 0 24 24">
                    <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 15h-2v-6h2v6zm0-8h-2V7h2v2z"/>
                  </svg>
                </button>
              </div>
            </div>
          </div>
          
          {/* Recommendation Process Button */}
          <div className="absolute left-[469px] bottom-[0px]">
            <button className="w-[233px] h-[233px] bg-white border border-[#dddddd] rounded-full flex flex-col items-center justify-center hover:bg-gray-50 transition-colors">
              <div className="text-[24.4px] text-black leading-[28.55px] text-center font-lg-smart">
                🧐<br />
                추천 과정<br />
                보러가기
              </div>
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}

export default PortfolioResult
