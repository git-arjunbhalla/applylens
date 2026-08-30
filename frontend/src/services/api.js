import axios from 'axios'

const REFRESH_STORAGE_KEY = 'applylens.refresh_token'

let accessToken = null
let refreshPromise = null
const sessionClearedListeners = new Set()

export function getAccessToken() {
  return accessToken
}

export function getStoredRefreshToken() {
  try {
    return window.localStorage.getItem(REFRESH_STORAGE_KEY)
  } catch {
    return null
  }
}

function persistRefreshToken(token) {
  try {
    if (token) {
      window.localStorage.setItem(REFRESH_STORAGE_KEY, token)
    } else {
      window.localStorage.removeItem(REFRESH_STORAGE_KEY)
    }
  } catch {
    // Storage can be unavailable in private mode; session still works in memory.
  }
}

export function applyAuthSession(tokens) {
  accessToken = tokens.access_token
  persistRefreshToken(tokens.refresh_token)
}

export function subscribeToSessionCleared(listener) {
  sessionClearedListeners.add(listener)
  return () => {
    sessionClearedListeners.delete(listener)
  }
}

function notifySessionCleared() {
  sessionClearedListeners.forEach((listener) => listener())
}

export function clearSessionTokens({ notify = true } = {}) {
  accessToken = null
  persistRefreshToken(null)
  refreshPromise = null
  if (notify) {
    notifySessionCleared()
  }
}

export function resetAuthClientState() {
  accessToken = null
  refreshPromise = null
  persistRefreshToken(null)
}

function isAuthCredentialRequest(url = '') {
  return (
    url.includes('/api/v1/auth/login') ||
    url.includes('/api/v1/auth/signup') ||
    url.includes('/api/v1/auth/refresh')
  )
}

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

api.interceptors.request.use((config) => {
  if (accessToken && !config.skipAuth) {
    config.headers.Authorization = `Bearer ${accessToken}`
  }
  return config
})

export async function refreshAccessToken() {
  if (refreshPromise) {
    return refreshPromise
  }

  const refreshToken = getStoredRefreshToken()
  if (!refreshToken) {
    clearSessionTokens({ notify: true })
    const error = new Error('No refresh token')
    error.code = 'NO_REFRESH_TOKEN'
    throw error
  }

  refreshPromise = api
    .post(
      '/api/v1/auth/refresh',
      { refresh_token: refreshToken },
      { skipAuth: true, skipRefresh: true },
    )
    .then((response) => {
      applyAuthSession(response.data)
      return response.data
    })
    .catch((error) => {
      clearSessionTokens({ notify: true })
      throw error
    })
    .finally(() => {
      refreshPromise = null
    })

  return refreshPromise
}

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const original = error.config
    if (!original || original.skipRefresh || original._retry) {
      return Promise.reject(error)
    }

    if (error.response?.status !== 401) {
      return Promise.reject(error)
    }

    if (isAuthCredentialRequest(original.url || '')) {
      return Promise.reject(error)
    }

    original._retry = true

    try {
      await refreshAccessToken()
      return api(original)
    } catch (refreshError) {
      return Promise.reject(refreshError)
    }
  },
)

export default api
