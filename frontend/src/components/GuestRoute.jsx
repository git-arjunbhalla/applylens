import { Navigate, Outlet } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'
import AuthLoading from './AuthLoading'

function GuestRoute() {
  const { isAuthenticated, isInitializing } = useAuth()

  if (isInitializing) {
    return <AuthLoading />
  }

  if (isAuthenticated) {
    return <Navigate to="/" replace />
  }

  return <Outlet />
}

export default GuestRoute
