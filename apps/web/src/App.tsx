import { Navigate, Route, Routes } from 'react-router-dom'
import { useAuth } from './auth/AuthContext'
import Landing from './pages/Landing'
import Login from './pages/Login'
import OwnerHome from './pages/owner/OwnerHome'
import EnterpriseProfile from './pages/officer/EnterpriseProfile'
import PortfolioList from './pages/officer/PortfolioList'

function RequireAuth({ children }: { children: React.ReactNode }) {
  const { isAuthenticated } = useAuth()
  if (!isAuthenticated) return <Navigate to="/login" replace />
  return <>{children}</>
}

function HomeRedirect() {
  const { role } = useAuth()
  if (role === 'officer') return <Navigate to="/officer" replace />
  if (role === 'owner') return <Navigate to="/owner" replace />
  return <Navigate to="/login" replace />
}

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Landing />} />
      <Route path="/login" element={<Login />} />
      <Route path="/app" element={<RequireAuth><HomeRedirect /></RequireAuth>} />
      <Route path="/owner" element={<RequireAuth><OwnerHome /></RequireAuth>} />
      <Route path="/officer" element={<RequireAuth><PortfolioList /></RequireAuth>} />
      <Route path="/officer/enterprise/:enterpriseId" element={<RequireAuth><EnterpriseProfile /></RequireAuth>} />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}
