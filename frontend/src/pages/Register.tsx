import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'
import { Button } from '../components/ui/Button'
import { Input } from '../components/ui/Input'
import { Card } from '../components/ui/Card'
import { Layout } from '../components/layout/Layout'
import { RateLimitCountdown } from '../components/ui/RateLimitCountdown'
import { isRateLimitError, getRetryAfter } from '../utils/errorHandler'
import { Eye, EyeOff } from 'lucide-react'

function RegisterPage() {
  const [username, setUsername] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [fullName, setFullName] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const [rateLimitError, setRateLimitError] = useState<any>(null)

  // 密码显示/隐藏状态
  const [showPassword, setShowPassword] = useState(false)
  const [showConfirmPassword, setShowConfirmPassword] = useState(false)

  // 密码强度指示
  const [passwordStrength, setPasswordStrength] = useState<'weak' | 'medium' | 'strong' | null>(null)
  const { register } = useAuth()
  const navigate = useNavigate()

  // 检查密码强度
  const checkPasswordStrength = (pwd: string) => {
    if (pwd.length === 0) {
      setPasswordStrength(null)
      return
    }

    let score = 0
    if (pwd.length >= 8) score++
    if (pwd.length >= 12) score++
    if (/[a-z]/.test(pwd)) score++
    if (/[A-Z]/.test(pwd)) score++
    if (/[0-9]/.test(pwd)) score++
    if (/[^a-zA-Z0-9]/.test(pwd)) score++

    if (score <= 2) setPasswordStrength('weak')
    else if (score <= 4) setPasswordStrength('medium')
    else setPasswordStrength('strong')
  }

  const handlePasswordChange = (value: string) => {
    setPassword(value)
    checkPasswordStrength(value)
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setRateLimitError(null)

    // 基本验证
    if (!username.trim()) {
      setError('请输入用户名')
      return
    }

    if (!email.trim()) {
      setError('请输入邮箱地址')
      return
    }

    if (password !== confirmPassword) {
      setError('两次输入的密码不一致')
      return
    }

    setLoading(true)

    try {
      await register(username, email, password, fullName)
      navigate('/')
    } catch (err: any) {
      // 检查是否为速率限制错误
      if (isRateLimitError(err)) {
        setRateLimitError(err)
      } else {
        setError(err.response?.data?.detail || '注册失败')
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

  // 密码强度颜色
  const getStrengthColor = () => {
    switch (passwordStrength) {
      case 'weak': return 'bg-red-500'
      case 'medium': return 'bg-yellow-500'
      case 'strong': return 'bg-green-500'
      default: return 'bg-gray-200'
    }
  }

  // 密码强度文字
  const getStrengthText = () => {
    switch (passwordStrength) {
      case 'weak': return '弱'
      case 'medium': return '中'
      case 'strong': return '强'
      default: return ''
    }
  }

  return (
    <Layout>
      <div className="max-w-md mx-auto">
        <Card className="p-8">
          <h2 className="text-2xl font-bold mb-2 text-center">注册账号</h2>
          <p className="text-gray-600 text-center text-sm mb-6">
            创建一个新账号以开始使用测试自动化平台
          </p>

          {/* 注册要求提示 */}
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6 text-sm">
            <h3 className="font-semibold text-blue-900 mb-2">📋 注册要求</h3>
            <ul className="space-y-1 text-blue-800">
              <li>• 用户名：至少 3 个字符</li>
              <li>• 邮箱：有效的邮箱地址</li>
              <li>• 密码：
                <ul className="ml-4 mt-1 space-y-1 text-blue-700">
                  <li>- 至少 8 个字符</li>
                  <li>- 至少 1 个大写字母（A-Z）</li>
                  <li>- 至少 1 个小写字母（a-z）</li>
                  <li>- 至少 1 个数字（0-9）</li>
                  <li>- 至少 1 个特殊字符（如：!@#$%）</li>
                </ul>
              </li>
            </ul>
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            <Input
              name="username"
              label="用户名"
              placeholder="请输入用户名（至少3个字符）"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              required
            />

            <Input
              name="email"
              label="邮箱地址"
              type="email"
              placeholder="请输入邮箱地址"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
            />

            <div>
              <div className="relative">
                <Input
                  name="password"
                  label="密码"
                  type={showPassword ? 'text' : 'password'}
                  placeholder="请输入密码"
                  value={password}
                  onChange={(e) => handlePasswordChange(e.target.value)}
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

              {/* 密码强度指示器 */}
              {password && passwordStrength && (
                <div className="mt-2">
                  <div className="flex items-center justify-between text-xs mb-1">
                    <span className="text-gray-600">密码强度：</span>
                    <span className={`font-medium ${
                      passwordStrength === 'weak' ? 'text-red-600' :
                      passwordStrength === 'medium' ? 'text-yellow-600' :
                      'text-green-600'
                    }`}>
                      {getStrengthText()}
                    </span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div
                      className={`h-full rounded-full transition-all duration-300 ${getStrengthColor()}`}
                      style={{ width: passwordStrength === 'weak' ? '33%' : passwordStrength === 'medium' ? '66%' : '100%' }}
                    />
                  </div>
                </div>
              )}
            </div>

            <div className="relative">
              <Input
                name="confirmPassword"
                label="确认密码"
                type={showConfirmPassword ? 'text' : 'password'}
                placeholder="请再次输入密码"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                required
              />
              <button
                type="button"
                onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                className="absolute right-3 top-[2.1rem] text-gray-500 hover:text-gray-700 focus:outline-none"
                tabIndex={-1}
                aria-label={showConfirmPassword ? '隐藏密码' : '显示密码'}
              >
                {showConfirmPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
              </button>
            </div>

            <Input
              name="fullName"
              label="姓名（可选）"
              type="text"
              placeholder="请输入您的姓名"
              value={fullName}
              onChange={(e) => setFullName(e.target.value)}
            />

            {rateLimitError ? (
              <RateLimitCountdown
                retryAfter={getRetryAfter(rateLimitError) || 15}
                onRetry={handleRetry}
              />
            ) : error && (
              <div className="bg-red-50 border border-red-200 text-red-700 p-4 rounded-lg text-sm">
                <p className="font-medium">⚠️ 注册失败</p>
                <p className="mt-1">{error}</p>
                {error.includes('已存在') && (
                  <p className="mt-2 text-xs">
                    💡 提示：如果账号已存在，请直接
                    <Link to="/login" className="text-blue-700 hover:underline ml-1">登录</Link>
                  </p>
                )}
              </div>
            )}

            <Button
              type="submit"
              className="w-full"
              disabled={loading || !!rateLimitError}
            >
              {loading ? '注册中...' : '注册账号'}
            </Button>
          </form>

          <div className="mt-4 text-center text-sm text-gray-600">
            已有账号？{' '}
            <Link to="/login" className="text-blue-600 hover:underline font-medium">
              立即登录
            </Link>
          </div>
        </Card>
      </div>
    </Layout>
  )
}

export default RegisterPage
