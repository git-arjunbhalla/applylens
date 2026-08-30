import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react'
import { subscribeToSessionCleared } from '../services/api'
import { login as loginRequest, logoutSession, restoreSession, signup as signupRequest } from '../services/auth'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [isInitializing, setIsInitializing] = useState(true)

  useEffect(() => {
    const unsubscribe = subscribeToSessionCleared(() => {
      setUser(null)
    })

    let cancelled = false
    restoreSession()
      .then((restoredUser) => {
        if (!cancelled) {
          setUser(restoredUser)
        }
      })
      .finally(() => {
        if (!cancelled) {
          setIsInitializing(false)
        }
      })

    return () => {
      cancelled = true
      unsubscribe()
    }
  }, [])

  const signup = useCallback(async ({ email, password }) => {
    const data = await signupRequest({ email, password })
    setUser(data.user)
    return data.user
  }, [])

  const login = useCallback(async ({ email, password }) => {
    const data = await loginRequest({ email, password })
    setUser(data.user)
    return data.user
  }, [])

  const logout = useCallback(() => {
    logoutSession()
    setUser(null)
  }, [])

  const value = useMemo(
    () => ({
      user,
      isInitializing,
      isAuthenticated: Boolean(user),
      signup,
      login,
      logout,
    }),
    [user, isInitializing, signup, login, logout],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (context === null) {
    throw new Error('useAuth must be used within AuthProvider')
  }
  return context
}
