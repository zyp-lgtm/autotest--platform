import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'
import { Button } from '../components/ui/Button'
import { Input } from '../components/ui/Input'
import { Card } from '../components/ui/Card'
import { Layout } from '../components/layout/Layout'

function RegisterPage() {
  const [username, setUsername] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const { register } = useAuth()
  const navigate = useNavigate()

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')

    if (password !== confirmPassword) {
      setError('两次输入的密码不一致')
      return
    }

    if (password.length < 6) {
      setError('密码长度至少 6 位')
      return
    }

    setLoading(true)

    try {
      await register(username, email, password)
      navigate('/')
    } catch (err: any) {
      setError(err.response?.data?.detail || '注册失败')
    } finally {
      setLoading(false)
    }
  }

  return (
    <Layout>
      <div className="max-w-md mx-auto">
        <Card className="p-8">
          <h2 className="text-2xl font-bold mb-6 text-center">注册</h2>

          <form onSubmit={handleSubmit} className="space-y-4">
            <Input
              name="username"
              label="用户名"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              required
            />

            <Input
              name="email"
              label="邮箱"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
            />

            <Input
              name="password"
              label="密码"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />

            <Input
              name="confirmPassword"
              label="确认密码"
              type="password"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              required
            />

            {error && (
              <div className="bg-red-50 text-red-600 p-3 rounded-lg text-sm">
                {error}
              </div>
            )}

            <Button
              type="submit"
              className="w-full"
              disabled={loading}
            >
              {loading ? '注册中...' : '注册'}
            </Button>
          </form>

          <div className="mt-4 text-center text-sm">
            已有账号？{' '}
            <Link to="/login" className="text-blue-600 hover:underline">
              登录
            </Link>
          </div>
        </Card>
      </div>
    </Layout>
  )
}

export default RegisterPage
