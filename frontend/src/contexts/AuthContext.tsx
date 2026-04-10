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
      console.error('[AuthContext] 获取用户信息失败:', error)
      // 不要立即清除 token，因为可能是网络错误或临时故障
      // 只有在确认 token 无效时才清除（由响应拦截器处理）
      // 如果获取用户信息失败，至少设置 loading 为 false
    } finally {
      setLoading(false)
    }
  }

  const login = async (username: string, password: string) => {
    const response = await authApi.login({ username, password })
    const { access_token } = response

    // 先设置 token 到 state 和 localStorage
    setToken(access_token)
    localStorage.setItem('access_token', access_token)

    // 使用新获取的 token 调用 API
    // 注意：不能立即调用 fetchCurrentUser，因为响应拦截器可能还没更新
    // 给一点时间让 token 传播到 apiClient
    try {
      // 手动添加 Authorization 头来确保请求使用最新的 token
      const response = await fetch('/api/v1/auth/me', {
        headers: {
          'Authorization': `Bearer ${access_token}`
        }
      })

      if (response.ok) {
        const userData = await response.json()
        setUser(userData)
      } else {
        // 如果获取用户信息失败，仍然保持登录状态（使用 JWT 中的信息）
        console.warn('[AuthContext] 获取用户信息失败，但保持登录状态')
        // 从 JWT 解码获取用户名
        const parts = access_token.split('.')
        if (parts.length === 3) {
          const payload = JSON.parse(atob(parts[1]))
          setUser({ username: payload.sub, id: payload.sub })
        }
      }
    } catch (error) {
      console.error('[AuthContext] 获取用户信息失败:', error)
      // 即使获取用户信息失败，也保持登录状态
      // 因为 login API 已经成功返回了 token
      const parts = access_token.split('.')
      if (parts.length === 3) {
        try {
          const payload = JSON.parse(atob(parts[1]))
          setUser({ username: payload.sub, id: payload.sub })
        } catch {
          // 如果解码失败，至少设置用户名为已知值
          setUser({ username, id: username })
        }
      }
    }

    setLoading(false)
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
