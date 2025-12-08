/**
 * 환경 변수 유틸리티
 */

/**
 * API Base URL 가져오기
 */
export const getApiBaseUrl = () => {
  // Vite 환경 변수 사용
  if (import.meta.env.VITE_API_BASE_URL) {
    return import.meta.env.VITE_API_BASE_URL
  }
  // 개발 환경에서는 상대 경로 사용
  return ''
}

/**
 * 환경 모드 확인
 */
export const isDevelopment = () => {
  return import.meta.env.MODE === 'development'
}

export const isProduction = () => {
  return import.meta.env.MODE === 'production'
}

