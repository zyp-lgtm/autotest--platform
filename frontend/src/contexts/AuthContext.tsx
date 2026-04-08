import { createContext, useContext, useState, useEffect, ReactNode } from 'react'
import { authApi } from '../api/auth'
import type { User } from '../types'

interface AuthContextType {
  user: User | null
  token: string | null
  login: (username: string, password: string) => Promise<void>
  register: (username: string, email: string, password: string) => Promise<void>
  logout: () => void
  loading: boolean
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [token, setToken] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)

  // 初始化：从 localStorage 读取 token
  useEffect(() => {
    console.log('[AuthContext] 初始化开始')
    try {
      const storedToken = localStorage.getItem('access_token')
      console.log('[AuthContext] 存储的 token:', storedToken ? '存在' : '不存在')
      if (storedToken) {
        setToken(storedToken)
        fetchCurrentUser(storedToken)
      } else {
        console.log('[AuthContext] 无 token，设置 loading=false')
        setLoading(false)
      }
    } catch (error) {
      console.error('[AuthContext] 初始化失败:', error)
      setLoading(false)
    }
  }, [])

  const fetchCurrentUser = async (_accessToken: string) => {
    try {
      const userData = await authApi.getCurrentUser()
      setUser(userData)
    } catch (error) {
      console.error('Failed to fetch user:', error)
      localStorage.removeItem('access_token')
      setToken(null)
    } finally {
      setLoading(false)
    }
  }

  const login = async (username: string, password: string) => {
    const response = await authApi.login({ username, password })
    const { access_token } = response

    localStorage.setItem('access_token', access_token)
    setToken(access_token)

    await fetchCurrentUser(access_token)
  }

  const register = async (username: string, email: string, password: string) => {
    await authApi.register({ username, email, password, full_name: '' })
    // 注册成功后自动登录
    await login(username, password)
  }

  const logout = () => {
    localStorage.removeItem('access_token')
    setUser(null)
    setToken(null)
  }

  return (
    <AuthContext.Provider value={{ user, token, login, register, logout, loading }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider')
  }
  return context
}
