import React, { createContext, useContext, useState, useEffect } from 'react'
import { api } from '../api/client'

export interface User {
  id: string
  email: string
  name: string
  role: string
  is_active: boolean
}

interface AuthContextType {
  user: User | null
  token: string | null
  loading: boolean
  login: (email: string, pass: string) => Promise<void>
  logout: () => void
  hasRole: (...roles: string[]) => boolean
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null)
  const [token, setToken] = useState<string | null>(localStorage.getItem('insighttext_token'))
  const [loading, setLoading] = useState<boolean>(true)

  useEffect(() => {
    async function loadUser() {
      const storedToken = localStorage.getItem('insighttext_token')
      if (storedToken) {
        try {
          const userData = await api.auth.me()
          setUser(userData)
        } catch {
          localStorage.removeItem('insighttext_token')
          setToken(null)
          setUser(null)
        }
      }
      setLoading(false)
    }
    loadUser()
  }, [])

  const login = async (email: string, pass: string) => {
    const res = await api.auth.login({ email, password: pass })
    localStorage.setItem('insighttext_token', res.access_token)
    setToken(res.access_token)
    setUser(res.user)
  }

  const logout = () => {
    localStorage.removeItem('insighttext_token')
    setToken(null)
    setUser(null)
  }

  const hasRole = (...roles: string[]) => {
    if (!user) return false
    if (user.role === 'admin') return true
    return roles.includes(user.role)
  }

  return (
    <AuthContext.Provider value={{ user, token, loading, login, logout, hasRole }}>
      {children}
    </AuthContext.Provider>
  )
}

export const useAuth = () => {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}
