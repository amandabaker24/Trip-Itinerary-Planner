import { Link, Outlet, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import Button from './ui/Button'

export default function AppLayout() {
  const { logout, user } = useAuth()
  const navigate = useNavigate()

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  return (
    <div className="layout">
      <header className="topbar">
        <div className="brand" onClick={() => navigate('/trips')}>
          <span className="brand-mark">TripIt</span>
          <span className="brand-sub">itinerary planner</span>
        </div>
        <nav className="topnav">
          <Link to="/trips">Trips</Link>
        </nav>
        <div className="auth-chip">
          <div className="user">{user?.username ?? 'User'}</div>
          <Button variant="ghost" onClick={handleLogout}>Logout</Button>
        </div>
      </header>
      <main className="content">
        <Outlet />
      </main>
    </div>
  )
}
