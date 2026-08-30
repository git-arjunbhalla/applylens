import { Navigate, Route, Routes } from 'react-router-dom'
import AppLayout from './components/AppLayout'
import GuestRoute from './components/GuestRoute'
import ProtectedRoute from './components/ProtectedRoute'
import { AuthProvider } from './context/AuthContext'
import ApplicationCreatePage from './pages/ApplicationCreatePage'
import ApplicationDetailPage from './pages/ApplicationDetailPage'
import ApplicationEditPage from './pages/ApplicationEditPage'
import ApplicationsPage from './pages/ApplicationsPage'
import DashboardPage from './pages/DashboardPage'
import LoginPage from './pages/LoginPage'
import SignupPage from './pages/SignupPage'

function App() {
  return (
    <AuthProvider>
      <Routes>
        <Route element={<GuestRoute />}>
          <Route path="/login" element={<LoginPage />} />
          <Route path="/signup" element={<SignupPage />} />
        </Route>
        <Route element={<ProtectedRoute />}>
          <Route element={<AppLayout />}>
            <Route path="/" element={<DashboardPage />} />
            <Route path="/applications" element={<ApplicationsPage />} />
            <Route path="/applications/new" element={<ApplicationCreatePage />} />
            <Route path="/applications/:applicationId/edit" element={<ApplicationEditPage />} />
            <Route path="/applications/:applicationId" element={<ApplicationDetailPage />} />
          </Route>
        </Route>
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </AuthProvider>
  )
}

export default App
