import { createContext, useContext, useState, useEffect, ReactNode } from 'react'
import { authApi } from '../api/auth'
import type { User, AuthResponse } from '../types'

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

  // 初始化：验证 Cookie 中的 token 是否有效
  useEffect(() => {
    console.log('[AuthContext] 初始化开始 - 使用 HttpOnly Cookie')
    validateCurrentSession()
  }, [])

  // 验证当前会话（Cookie 中的 token）
  const validateCurrentSession = async () => {
    console.log('[AuthContext] 验证当前会话...')
    try {
      // 直接调用 API，Cookie 会自动发送
      const userData = await authApi.getCurrentUser()
      console.log('[AuthContext] 当前会话有效，用户:', userData)
      setUser(userData)
      setToken('cookie-based')  // 标记使用 Cookie
      setLoading(false)
    } catch (error: any) {
      console.log('[AuthContext] 当前会话无效或未登录:', error?.response?.status)
      // 401 表示未认证，这是正常的
      if (error?.response?.status !== 401) {
        console.error('[AuthContext] 验证会话时发生错误:', error)
      }
      setUser(null)
      setToken(null)
      setLoading(false)
    }
  }

  const fetchCurrentUser = async (accessToken: string) => {
    try {
      const userData = await authApi.getCurrentUser()
      setUser(userData)
    } catch (error) {
      console.error('[AuthContext] 获取用户信息失败:', error)
      throw error
    }
  }

  const login = async (username: string, password: string) => {
    console.log('[AuthContext] 开始登录流程')
    try {
      const response: AuthResponse = await authApi.login({ username, password })

      // 后端现在返回 user 对象
      if (response.user) {
        console.log('[AuthContext] 登录成功，用户信息:', response.user)
        setUser(response.user)
        setToken('cookie-based')  // 标记使用 Cookie
      } else {
        // 如果后端没有返回 user（向后兼容），从 JWT 解码
        if (response.access_token) {
          const parts = response.access_token.split('.')
          if (parts.length === 3) {
            const payload = JSON.parse(atob(parts[1]))
            const userData = {
              username: payload.sub,
              id: payload.sub,
              email: '',
              full_name: '',
              is_active: true,
              role: ''
            }
            setUser(userData)
            setToken('cookie-based')
          }
        } else {
          throw new Error('Invalid login response')
        }
      }

      console.log('[AuthContext] 登录成功，已设置 HttpOnly Cookie')
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

  const logout = async () => {
    try {
      // 调用后端登出接口（如果有的话）
      // await authApi.logout()
      console.log('[AuthContext] 登出成功')
    } catch (error) {
      console.error('[AuthContext] 登出时发生错误:', error)
    } finally {
      // 清除本地状态
      setUser(null)
      setToken(null)
    }
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
