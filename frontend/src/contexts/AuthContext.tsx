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

  // 监听登出事件（由响应拦截器触发）
  useEffect(() => {
    const handleLogout = () => {
      console.log('[AuthContext] 收到登出事件，清除状态')
      setUser(null)
      setToken(null)
      setLoading(false)
    }

    window.addEventListener('auth:logout', handleLogout)
    return () => {
      window.removeEventListener('auth:logout', handleLogout)
    }
  }, [])

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
      console.error('[AuthContext] 获取用户信息失败:', error)
      // 不要立即清除 token，因为可能是网络错误或临时故障
      // 只有在确认 token 无效时才清除（由响应拦截器处理）
      // 如果获取用户信息失败，至少设置 loading 为 false
    } finally {
      setLoading(false)
    }
  }

  const login = async (username: string, password: string) => {
    console.log('[AuthContext] 开始登录流程')
    try {
      const response = await authApi.login({ username, password })
      const { access_token } = response
      console.log('[AuthContext] 登录 API 返回成功')

      // 从 JWT 解码获取用户信息（不需要额外的 API 调用）
      const parts = access_token.split('.')
      if (parts.length === 3) {
        const payload = JSON.parse(atob(parts[1]))
        console.log('[AuthContext] JWT payload:', payload)

        const userData = {
          username: payload.sub,
          id: payload.sub
        }

        // 先设置用户信息和 token
        setUser(userData)
        setToken(access_token)

        // 然后保存到 localStorage（重要：要在设置 state 之后）
        localStorage.setItem('access_token', access_token)

        console.log('[AuthContext] 登录成功，用户信息已设置:', userData)
        console.log('[AuthContext] Token 已保存到 localStorage')
      } else {
        throw new Error('Invalid token format')
      }
    } catch (error) {
      console.error('[AuthContext] 登录失败:', error)
      throw error
    } finally {
      setLoading(false)
    }
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
