/**
 * API 유틸리티 함수
 */

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
    await fetch('/api/products/', {
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
  const csrfToken = getCSRFToken() || await initCSRFToken()
  
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

  const response = await fetch(url, mergedOptions)
  
  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ error: 'Unknown error' }))
    throw new Error(errorData.error || `HTTP error! status: ${response.status}`)
  }

  return response.json()
}

