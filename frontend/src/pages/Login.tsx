import { useState } from 'react'
import { useNavigate, useLocation, Link } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'
import { Button } from '../components/ui/Button'
import { Input } from '../components/ui/Input'
import { Card } from '../components/ui/Card'
import { Layout } from '../components/layout/Layout'
import { RateLimitCountdown } from '../components/ui/RateLimitCountdown'
import { isRateLimitError, getRetryAfter } from '../utils/errorHandler'
import { Eye, EyeOff } from 'lucide-react'

function LoginPage() {
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const [rateLimitError, setRateLimitError] = useState<any>(null)
  const [showPassword, setShowPassword] = useState(false)

  const { login } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setRateLimitError(null)
    setLoading(true)

    try {
      await login(username, password)

      // 登录成功，重定向到原来想访问的页面或首页
      const from = (location.state as any)?.from?.pathname || '/'
      navigate(from, { replace: true })
    } catch (err: any) {
      // 检查是否为速率限制错误
      if (isRateLimitError(err)) {
        setRateLimitError(err)
      } else {
        const errorMessage = err.response?.data?.detail || err.message || '登录失败，请检查用户名和密码'
        setError(errorMessage)
      }
    } finally {
      setLoading(false)
    }
  }

  // 倒计时结束后重置状态
  const handleRetry = () => {
    setRateLimitError(null)
    setLoading(false)
  }

  return (
    <Layout>
      <div className="max-w-md mx-auto">
        <Card className="p-8">
          <h2 className="text-2xl font-bold mb-2 text-center">登录账号</h2>
          <p className="text-gray-600 text-center text-sm mb-6">
            欢迎回来！请输入您的账号信息
          </p>

          {/* 提示信息 */}
          <div className="bg-gray-50 border border-gray-200 rounded-lg p-4 mb-6 text-sm">
            <div className="flex items-start gap-2">
              <span className="text-lg">💡</span>
              <div className="flex-1 text-gray-700">
                <p className="font-medium mb-1">测试账号</p>
                <ul className="space-y-1 text-xs">
                  <li>• 用户名：<code className="bg-white px-1 py-0.5 rounded">demo</code></li>
                  <li>• 密码：<code className="bg-white px-1 py-0.5 rounded">demo123</code></li>
                </ul>
              </div>
            </div>
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            <Input
              name="username"
              label="用户名"
              placeholder="请输入用户名"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              required
              autoFocus
            />

            <div className="relative">
              <Input
                name="password"
                label="密码"
                type={showPassword ? 'text' : 'password'}
                placeholder="请输入密码"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="absolute right-3 top-[2.1rem] text-gray-500 hover:text-gray-700 focus:outline-none"
                tabIndex={-1}
                aria-label={showPassword ? '隐藏密码' : '显示密码'}
              >
                {showPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
              </button>
            </div>

            {rateLimitError ? (
              <RateLimitCountdown
                retryAfter={getRetryAfter(rateLimitError) || 15}
                onRetry={handleRetry}
              />
            ) : error && (
              <div className="bg-red-50 border border-red-200 text-red-700 p-4 rounded-lg text-sm">
                <p className="font-medium">⚠️ 登录失败</p>
                <p className="mt-1">{error}</p>
                {error.includes('用户名或密码') && (
                  <p className="mt-2 text-xs">
                    💡 提示：忘记密码？请联系管理员重置
                  </p>
                )}
              </div>
            )}

            <Button
              type="submit"
              className="w-full"
              disabled={loading || !!rateLimitError}
            >
              {loading ? '登录中...' : '登录'}
            </Button>
          </form>

          <div className="mt-4 text-center text-sm text-gray-600">
            还没有账号？{' '}
            <Link to="/register" className="text-blue-600 hover:underline font-medium">
              立即注册
            </Link>
          </div>
        </Card>
      </div>
    </Layout>
  )
}

export default LoginPage
