import type { ReactElement } from 'react'
import './App.css'
import { Navigate, Route, Routes } from 'react-router-dom'
import LoginPage from './pages/LoginPage'
import RegisterPage from './pages/RegisterPage'
import TripsListPage from './pages/TripsListPage'
import TripDetailPage from './pages/TripDetailPage'
import { useAuth } from './context/AuthContext'
import AppLayout from './components/AppLayout'

const ProtectedRoute = ({ children }: { children: ReactElement }) => {
  const { token } = useAuth()
  if (!token) {
    return <Navigate to="/login" replace />
  }
  return children
}

const DefaultRedirect = () => {
  const { token } = useAuth()
  return <Navigate to={token ? '/trips' : '/login'} replace />
}

function App() {
  return (
    <Routes>
      <Route path="/" element={<DefaultRedirect />} />
      <Route path="/login" element={<LoginPage />} />
      <Route path="/register" element={<RegisterPage />} />

      <Route
        element={
          <ProtectedRoute>
            <AppLayout />
          </ProtectedRoute>
        }
      >
        <Route path="/trips" element={<TripsListPage />} />
        <Route path="/trips/:id" element={<TripDetailPage />} />
      </Route>

      <Route path="*" element={<DefaultRedirect />} />
    </Routes>
  )
}

export default App
