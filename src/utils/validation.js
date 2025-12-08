/**
 * 가격 포맷팅 유틸리티 함수
 */
export const formatPrice = (price) => {
  if (!price && price !== 0) return '가격 정보 없음'
  if (typeof price === 'string') {
    // 이미 포맷팅된 문자열인 경우 그대로 반환
    if (price.includes('원') || price.includes('월')) return price
    // 숫자 문자열인 경우 파싱
    const num = parseFloat(price.replace(/,/g, ''))
    if (!isNaN(num)) {
      return new Intl.NumberFormat('ko-KR').format(num) + '원'
    }
    return price
  }
  if (typeof price === 'number') {
    return new Intl.NumberFormat('ko-KR').format(price) + '원'
  }
  return '가격 정보 없음'
}

/**
 * 가격 파싱 함수 (문자열에서 숫자 추출)
 */
export const parsePrice = (priceStr) => {
  if (!priceStr) return 0
  const match = priceStr.toString().match(/[\d,]+/)
  if (match) {
    return parseInt(match[0].replace(/,/g, ''))
  }
  return 0
}
