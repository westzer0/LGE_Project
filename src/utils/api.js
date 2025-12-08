/**
 * API 유틸리티 함수
 */

/**
 * API Base URL 가져오기 (환경 변수 또는 기본값)
 */
const getApiBaseUrl = () => {
  // 프로덕션 환경에서 환경 변수로 설정 가능
  if (import.meta.env.VITE_API_BASE_URL) {
    return import.meta.env.VITE_API_BASE_URL
  }
  // 개발 환경에서는 상대 경로 사용
  return ''
}

/**
 * CSRF 토큰 가져오기
 */
export const getCSRFToken = () => {
  const name = 'csrftoken'
  let cookieValue = null
  if (document.cookie && document.cookie !== '') {
    const cookies = document.cookie.split(';')
    for (let i = 0; i < cookies.length; i++) {
      const cookie = cookies[i].trim()
      if (cookie.substring(0, name.length + 1) === (name + '=')) {
        cookieValue = decodeURIComponent(cookie.substring(name.length + 1))
        break
      }
    }
  }
  return cookieValue || ''
}

/**
 * CSRF 토큰 초기화 (Django에서 토큰 받아오기)
 */
export const initCSRFToken = async () => {
  try {
    const url = `${getApiBaseUrl()}/api/products/`
    await fetch(url, {
      method: 'GET',
      credentials: 'include',
    })
    return getCSRFToken()
  } catch (e) {
    console.warn('CSRF 토큰 초기화 실패:', e)
    return ''
  }
}

/**
 * API 요청 헬퍼 함수
 */
export const apiRequest = async (url, options = {}) => {
  try {
    const csrfToken = getCSRFToken() || await initCSRFToken()
    
    // 절대 URL이 아니면 base URL 추가
    const fullUrl = url.startsWith('http') ? url : `${getApiBaseUrl()}${url}`
    
    const defaultOptions = {
      credentials: 'include',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': csrfToken,
      },
    }

    const mergedOptions = {
      ...defaultOptions,
      ...options,
      headers: {
        ...defaultOptions.headers,
        ...options.headers,
      },
    }

    console.log(`[API] 요청: ${fullUrl}`, mergedOptions)

    const response = await fetch(fullUrl, mergedOptions)
    
    console.log(`[API] 응답 상태: ${response.status} ${response.statusText}`)

    // 응답 본문 읽기 시도
    let responseData
    const contentType = response.headers.get('content-type')
    
    if (contentType && contentType.includes('application/json')) {
      try {
        responseData = await response.json()
      } catch (e) {
        console.error('[API] JSON 파싱 실패:', e)
        const text = await response.text()
        console.error('[API] 응답 본문:', text)
        throw new Error(`서버 응답 파싱 실패: ${text.substring(0, 100)}`)
      }
    } else {
      const text = await response.text()
      responseData = { error: text || `HTTP ${response.status}` }
    }
    
    if (!response.ok) {
      const errorMsg = responseData.error || responseData.detail || `HTTP error! status: ${response.status}`
      console.error('[API] 오류 응답:', responseData)
      throw new Error(errorMsg)
    }

    console.log('[API] 성공 응답:', responseData)
    return responseData
  } catch (error) {
    console.error('[API] 요청 실패:', error)
    
    // 네트워크 오류 처리
    if (error.name === 'TypeError' && error.message.includes('fetch')) {
      throw new Error('서버에 연결할 수 없습니다. 서버가 실행 중인지 확인해주세요.')
    }
    
    throw error
  }
}

