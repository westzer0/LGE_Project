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
  const [portfolioData, setPortfolioData] = useState(null) // 포트폴리오 전체 데이터 (스타일 분석 포함)

  // PRD: 가전별 대표 이미지 그룹화 (카테고리별)
  const categoryProducts = useMemo(() => {
    const grouped = {}
    products.forEach((product, index) => {
      const category = product.category || '기타'
      if (!grouped[category]) {
        grouped[category] = {
          category,
          products: [],
          representativeImage: null,
        }
      }
      grouped[category].products.push({ ...product, index })
      // 첫 번째 제품을 대표 이미지로 사용
      if (!grouped[category].representativeImage && product.image_url) {
        grouped[category].representativeImage = product.image_url
      }
    })
    return Object.values(grouped)
  }, [products])

  // PRD: 가전 이미지 클릭 시 해당 위치로 스크롤
  const scrollToProduct = useCallback((productId) => {
    const element = document.getElementById(`product-${productId}`)
    if (element) {
      element.scrollIntoView({ behavior: 'smooth', block: 'center' })
      // 하이라이트 효과
      element.classList.add('highlight')
      setTimeout(() => {
        element.classList.remove('highlight')
      }, 2000)
    }
  }, [])

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

    // URL 경로 또는 쿼리 파라미터에서 portfolio_id 가져오기
    const urlParams = new URLSearchParams(window.location.search)
    let portfolioId = urlParams.get('portfolio_id') || urlParams.get('id')
    
    // URL 경로에서 portfolio_id 추출 (예: /portfolio/PF-001/)
    if (!portfolioId) {
      const pathMatch = window.location.pathname.match(/\/portfolio\/([^\/]+)\/?$/)
      if (pathMatch && pathMatch[1]) {
        portfolioId = pathMatch[1]
        console.log('[PortfolioResult] URL 경로에서 portfolio_id 추출:', portfolioId)
      }
    }

    console.log('[PortfolioResult] 최종 portfolio_id:', portfolioId)
    console.log('[PortfolioResult] 현재 URL:', window.location.href)
    console.log('[PortfolioResult] 현재 경로:', window.location.pathname)

    if (portfolioId) {
      console.log('[PortfolioResult] 포트폴리오 데이터 로드 시작:', portfolioId)
      fetchPortfolioData(portfolioId)
    } else {
      console.warn('[PortfolioResult] portfolio_id를 찾을 수 없어 기본 샘플 데이터를 로드합니다.')
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
      console.log('[PortfolioResult] portfolio_id:', portfolioId)
      console.log('[PortfolioResult] style_type:', data?.portfolio?.style_type)

      if (data.success && data.portfolio) {
        // 포트폴리오 전체 데이터 저장 (스타일 분석 포함)
        setPortfolioData(data.portfolio)

        // 포트폴리오 데이터에서 제품 정보 추출
        const portfolioProducts = data.portfolio.products || []

        console.log('[PortfolioResult] 제품 수:', portfolioProducts.length)
        console.log('[PortfolioResult] 제품 목록:', portfolioProducts)

        if (portfolioProducts.length === 0) {
          console.warn('[PortfolioResult] 포트폴리오에 제품이 없습니다.')
          console.error('[PortfolioResult] portfolio_id:', portfolioId, '에 제품이 없습니다.')
          // 제품이 없어도 스타일 정보는 표시
          if (data.portfolio.style_type && data.portfolio.style_title) {
            console.log('[PortfolioResult] 스타일 정보는 있지만 제품이 없습니다. 스타일 정보만 표시합니다.')
            // 스타일 정보는 유지하고 제품만 빈 배열로 설정
            setProducts([])
          } else {
            loadSampleData()
          }
          return
        }

        // 제품 데이터를 포맷팅
        const formattedProducts = portfolioProducts.map((product, index) => {
          console.log(`[PortfolioResult] 제품 ${index} 포맷팅:`, product)
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

          const formattedProduct = {
            id: product.id || product.product_id || `product-${index}`,
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
          console.log(`[PortfolioResult] 포맷팅된 제품 ${index}:`, formattedProduct)
          return formattedProduct
        })

        console.log('[PortfolioResult] 포맷팅된 제품 목록:', formattedProducts)
        console.log('[PortfolioResult] 스타일 타입:', data.portfolio.style_type)
        console.log('[PortfolioResult] 스타일 제목:', data.portfolio.style_title)
        console.log('[PortfolioResult] 포트폴리오 ID:', data.portfolio.portfolio_id)
        
        // 스타일 타입과 제품이 올바르게 로드되었는지 확인
        if (data.portfolio.style_type && formattedProducts.length > 0) {
          console.log(`[PortfolioResult] ✅ 포트폴리오 로드 성공: ${data.portfolio.portfolio_id} (${data.portfolio.style_type})`)
        } else {
          console.error('[PortfolioResult] ❌ 포트폴리오 데이터가 불완전합니다:', {
            style_type: data.portfolio.style_type,
            products_count: formattedProducts.length
          })
        }
        
        setProducts(formattedProducts)
      } else {
        console.error('[PortfolioResult] 포트폴리오 조회 실패:', data.error)
        console.error('[PortfolioResult] 응답 데이터:', data)
        console.error('[PortfolioResult] portfolio_id:', portfolioId)
        // API 응답이 실패했지만 portfolio_id가 있으면 재시도하지 않고 에러 표시
        alert(`포트폴리오를 불러올 수 없습니다: ${data.error || '알 수 없는 오류'}\n포트폴리오 ID: ${portfolioId}`)
        loadSampleData()
      }
    } catch (error) {
      console.error('[PortfolioResult] 포트폴리오 데이터 로드 실패:', error)
      console.error('[PortfolioResult] 에러 상세:', error.stack)
      console.error('[PortfolioResult] portfolio_id:', portfolioId)
      console.error('[PortfolioResult] 요청 URL:', `/api/portfolio/${portfolioId}/`)
      // 에러 발생 시 샘플 데이터 사용
      alert(`포트폴리오를 불러올 수 없습니다: ${error.message}\n포트폴리오 ID: ${portfolioId}`)
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

  const handleConsultation = useCallback(async () => {
    // 베스트샵 상담예약 로직
    console.log('[PortfolioResult] 베스트샵 상담예약 클릭')

    // URL 파라미터에서 portfolio_id 가져오기
    const urlParams = new URLSearchParams(window.location.search)
    const portfolioId = urlParams.get('portfolio_id') || urlParams.get('id')

    if (portfolioId) {
      try {
        // 베스트샵 상담예약 API 호출
        const data = await apiRequest('/api/bestshop/consultation/', {
          method: 'POST',
          body: JSON.stringify({
            portfolio_id: portfolioId,
            consultation_purpose: '이사',
          }),
        })

        if (data.success) {
          // 상담예약 페이지로 이동 또는 모달 표시
          if (data.reservation_id) {
            window.location.href = `/reservation-status?reservation_id=${data.reservation_id}`
          } else {
            alert('상담예약이 접수되었습니다.')
          }
        } else {
          alert(`상담예약 실패: ${data.error || '알 수 없는 오류'}`)
        }
      } catch (error) {
        console.error('[PortfolioResult] 상담예약 실패:', error)
        alert(`상담예약 중 오류가 발생했습니다: ${error.message}`)
      }
    } else {
      // portfolio_id가 없으면 상담예약 페이지로 이동
      window.location.href = '/reservation-status'
    }
  }, [])

  const handleKakaoShare = useCallback(async () => {
    // 카카오 공유 로직
    console.log('[PortfolioResult] 카카오 공유 클릭')

    // URL 파라미터에서 portfolio_id 가져오기
    const urlParams = new URLSearchParams(window.location.search)
    const portfolioId = urlParams.get('portfolio_id') || urlParams.get('id')

    if (!portfolioId) {
      alert('포트폴리오 ID가 없습니다.')
      return
    }

    try {
      // 카카오 공유 메타데이터 가져오기
      const data = await apiRequest(`/api/portfolio/${portfolioId}/share/`, {
        method: 'POST',
      })

      if (data.success && data.kakao_share_data) {
        // 카카오 JavaScript SDK 사용 (TODO: SDK 로드 확인 필요)
        if (window.Kakao && window.Kakao.isInitialized()) {
          window.Kakao.Share.sendDefault({
            objectType: 'feed',
            content: {
              title: data.kakao_share_data.title,
              description: data.kakao_share_data.description,
              imageUrl: data.kakao_share_data.image_url,
              link: {
                mobileWebUrl: data.kakao_share_data.link,
                webUrl: data.kakao_share_data.link,
              },
            },
          })
        } else {
          // SDK가 없으면 링크 복사
          navigator.clipboard.writeText(data.kakao_share_data.link)
          alert('링크가 클립보드에 복사되었습니다.')
        }
      } else {
        alert('공유 정보를 가져올 수 없습니다.')
      }
    } catch (error) {
      console.error('[PortfolioResult] 카카오 공유 실패:', error)
      alert(`공유 중 오류가 발생했습니다: ${error.message}`)
    }
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
      <style>{`
        .highlight {
          animation: highlightPulse 2s ease-in-out;
        }
        @keyframes highlightPulse {
          0%, 100% { 
            transform: scale(1);
            box-shadow: 0 0 0 0 rgba(59, 130, 246, 0);
          }
          50% { 
            transform: scale(1.02);
            box-shadow: 0 0 20px 5px rgba(59, 130, 246, 0.5);
          }
        }
      `}</style>
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
          {/* PRD: 스타일 분석 결과 타이틀 */}
          <div className="absolute left-[1070px] top-[33px] text-center">
            {portfolioData?.style_title ? (
              <>
                <div className="text-[15px] text-black mb-1 leading-[17.9px] font-pretendard">
                  {portfolioData.style_subtitle || '고객님에게 꼭 맞는'}
                </div>
                <div className="text-[20px] font-bold text-black leading-[23.87px] font-pretendard">
                  {portfolioData.style_title}
                </div>
              </>
            ) : (
              <>
                <div className="text-[15px] text-black mb-1 leading-[17.9px] font-pretendard">
                  고객님에게 꼭 맞는
                </div>
                <div className="text-[20px] font-bold text-black leading-[23.87px] font-pretendard">
                  모던한 실속형 가전 패키지가 도착했어요.
                </div>
              </>
            )}
          </div>

          {/* PRD: 가전별 대표 이미지 (카테고리별) - 상단에 배치 */}
          {categoryProducts.length > 0 && (
            <div className="absolute left-[0px] top-[106px] w-full px-4">
              <div className="mb-4">
                <div className="text-sm text-gray-600 mb-2 font-pretendard">가전별 대표 이미지</div>
                <div className="flex gap-4 flex-wrap">
                  {categoryProducts.map((categoryGroup) => (
                    <div
                      key={categoryGroup.category}
                      className="flex flex-col items-center cursor-pointer group transition-transform hover:scale-105"
                      onClick={() => {
                        // 첫 번째 제품으로 스크롤
                        if (categoryGroup.products.length > 0) {
                          const firstProduct = categoryGroup.products[0]
                          scrollToProduct(firstProduct.id)
                        }
                      }}
                      title={`${categoryGroup.category} 클릭 시 해당 제품으로 이동`}
                    >
                      <div className="w-20 h-20 rounded-lg overflow-hidden border-2 border-gray-200 group-hover:border-blue-500 transition-all shadow-md group-hover:shadow-lg">
                        {categoryGroup.representativeImage ? (
                          <img
                            src={categoryGroup.representativeImage}
                            alt={categoryGroup.category}
                            className="w-full h-full object-cover"
                            onError={(e) => {
                              // 이미지 로드 실패 시 기본 이미지
                              e.target.src = 'https://via.placeholder.com/80?text=' + encodeURIComponent(categoryGroup.category.substring(0, 2))
                            }}
                          />
                        ) : (
                          <div className="w-full h-full bg-gradient-to-br from-gray-100 to-gray-200 flex items-center justify-center text-gray-500 text-xs font-bold">
                            {categoryGroup.category.substring(0, 2)}
                          </div>
                        )}
                      </div>
                      <div className="mt-1.5 text-xs text-gray-700 text-center font-medium font-pretendard">
                        {categoryGroup.category}
                      </div>
                      <div className="text-[10px] text-gray-400 text-center font-pretendard">
                        {categoryGroup.products.length}개 제품
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* Purchase Type Toggle */}
          <div className="absolute left-[879px] top-[0px] flex gap-0">
            <button
              onClick={() => setPurchaseType('가전구독')}
              className={`px-[12.8px] py-2 rounded-full text-[14px] font-normal h-8 transition-colors font-pretendard ${purchaseType === '가전구독'
                ? 'bg-[#212121] text-white'
                : 'bg-white text-black border border-[#eeeeee]'
                }`}
            >
              가전구독
            </button>
            <button
              onClick={() => setPurchaseType('일반구매')}
              className={`px-[12.8px] py-2 rounded-full text-[14px] font-normal h-8 transition-colors font-pretendard ${purchaseType === '일반구매'
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
                  className={`px-[12.8px] py-2 rounded-full text-[14px] font-normal h-8 transition-colors font-pretendard ${contractPeriod === period
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

          {/* Product Cards - PRD: 가전별 대표 이미지 아래에 표시, 클릭 시 스크롤 가능하도록 id 추가 */}
          <div
            className="absolute left-[0px] top-[200px] flex gap-[13px] flex-wrap"
            style={{ width: '1032px', maxHeight: '500px', overflowY: 'auto' }}
          >
            {products.map((product) => (
              <div
                key={product.id}
                id={`product-${product.id}`}
                className="transition-all duration-300"
              >
                <ProductCard
                  product={product}
                  isRecommended={product.isRecommended}
                  purchaseType={purchaseType}
                  contractPeriod={contractPeriod}
                />
              </div>
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
                <button
                  onClick={handleKakaoShare}
                  className="w-12 h-12 bg-white border border-[#d9d9d9] rounded-full flex items-center justify-center hover:bg-gray-50 transition-colors"
                  title="카카오톡 공유"
                >
                  <svg className="w-5 h-5 text-gray-600" fill="currentColor" viewBox="0 0 24 24">
                    <path d="M12 3c5.799 0 10.5 3.664 10.5 8.185 0 4.52-4.701 8.184-10.5 8.184a13.5 13.5 0 0 1-1.727-.11l-4.408 2.883c-.501.265-.678.236-.472-.413l.892-3.678c-2.88-1.46-4.785-3.99-4.785-6.866C1.5 6.665 6.201 3 12 3z" />
                  </svg>
                </button>
                <button
                  onClick={() => {
                    const url = window.location.href
                    navigator.clipboard.writeText(url)
                    alert('링크가 클립보드에 복사되었습니다.')
                  }}
                  className="w-12 h-12 bg-white border border-[#d9d9d9] rounded-full flex items-center justify-center hover:bg-gray-50 transition-colors"
                  title="링크 복사"
                >
                  <svg className="w-5 h-5 text-gray-600" fill="currentColor" viewBox="0 0 24 24">
                    <path d="M18 16.08c-.76 0-1.44.3-1.96.77L8.91 12.7c.05-.23.09-.46.09-.7s-.04-.47-.09-.7l7.05-4.11c.54.5 1.25.81 2.04.81 1.66 0 3-1.34 3-3s-1.34-3-3-3-3 1.34-3 3c0 .24.04.47.09.7L8.04 9.81C7.5 9.31 6.79 9 6 9c-1.66 0-3 1.34-3 3s1.34 3 3 3c.79 0 1.5-.31 2.04-.81l7.12 4.16c-.05.21-.08.43-.08.65 0 1.61 1.31 2.92 2.92 2.92 1.61 0 2.92-1.31 2.92-2.92s-1.31-2.92-2.92-2.92z" />
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
