import { createContext, useContext, useEffect, useState, type ReactNode } from 'react'
import client from '../api/client'
import type { LoginResponse, Role } from '../api/types'

interface AuthState {
  token: string | null
  role: Role | null
  enterpriseId: string | null
  officerId: string | null
}

interface AuthContextValue extends AuthState {
  login: (phone: string, password: string) => Promise<void>
  logout: () => void
  isAuthenticated: boolean
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined)

function loadInitialState(): AuthState {
  return {
    token: localStorage.getItem('cf_token'),
    role: (localStorage.getItem('cf_role') as Role | null) ?? null,
    enterpriseId: localStorage.getItem('cf_enterprise_id'),
    officerId: localStorage.getItem('cf_officer_id'),
  }
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [state, setState] = useState<AuthState>(loadInitialState)

  useEffect(() => {
    if (state.token) localStorage.setItem('cf_token', state.token)
    if (state.role) localStorage.setItem('cf_role', state.role)
    if (state.enterpriseId) localStorage.setItem('cf_enterprise_id', state.enterpriseId)
    if (state.officerId) localStorage.setItem('cf_officer_id', state.officerId)
  }, [state])

  async function login(phone: string, password: string) {
    const { data } = await client.post<LoginResponse>('/auth/login', { phone, password })
    setState({
      token: data.token,
      role: data.role,
      enterpriseId: data.enterprise_id,
      officerId: data.officer_id,
    })
  }

  function logout() {
    localStorage.removeItem('cf_token')
    localStorage.removeItem('cf_role')
    localStorage.removeItem('cf_enterprise_id')
    localStorage.removeItem('cf_officer_id')
    setState({ token: null, role: null, enterpriseId: null, officerId: null })
  }

  return (
    <AuthContext.Provider value={{ ...state, login, logout, isAuthenticated: !!state.token }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used within AuthProvider')
  return ctx
}
