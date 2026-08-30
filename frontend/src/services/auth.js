import api, { applyAuthSession, clearSessionTokens, getStoredRefreshToken, refreshAccessToken } from './api'

export async function signup({ email, password }) {
  const { data } = await api.post(
    '/api/v1/auth/signup',
    { email, password },
    { skipAuth: true, skipRefresh: true },
  )
  applyAuthSession(data)
  return data
}

export async function login({ email, password }) {
  const { data } = await api.post(
    '/api/v1/auth/login',
    { email, password },
    { skipAuth: true, skipRefresh: true },
  )
  applyAuthSession(data)
  return data
}

export async function fetchCurrentUser() {
  const { data } = await api.get('/api/v1/auth/me')
  return data
}

export async function restoreSession() {
  if (!getStoredRefreshToken()) {
    return null
  }

  try {
    await refreshAccessToken()
    return await fetchCurrentUser()
  } catch {
    clearSessionTokens({ notify: false })
    return null
  }
}

export function logoutSession() {
  clearSessionTokens({ notify: false })
}
