import { useState } from 'react'

export default function DiagnosticPage() {
  const [cookieStatus, setCookieStatus] = useState<any>(null)
  const [loginResult, setLoginResult] = useState<any>(null)
  const [meResult, setMeResult] = useState<any>(null)

  const checkCookie = () => {
    const cookies = document.cookie
    const hasAccessToken = cookies.includes('access_token=')
    setCookieStatus({
      hasCookie: hasAccessToken,
      allCookies: cookies || '(空)',
      message: hasAccessToken ? '✅ 找到 access_token Cookie' : '❌ 未找到 access_token Cookie'
    })
  }

  const testLogin = async () => {
    try {
      setLoginResult({ loading: true })

      const response = await fetch('http://localhost:8000/api/v1/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ username: 'demo', password: 'demo123' })
      })

      const data = await response.json()

      if (response.ok) {
        setLoginResult({
          success: true,
          user: data.user,
          message: `✅ 登录成功 - User: ${data.user?.username}`
        })
        checkCookie()
      } else {
        setLoginResult({
          success: false,
          message: `❌ 登录失败: ${data.detail}`
        })
      }
    } catch (error: any) {
      setLoginResult({
        success: false,
        message: `❌ 请求失败: ${error.message}`
      })
    }
  }

  const testMeAPI = async () => {
    try {
      setMeResult({ loading: true })

      const response = await fetch('http://localhost:8000/api/v1/auth/me', {
        credentials: 'include'
      })

      if (response.ok) {
        const data = await response.json()
        setMeResult({
          success: true,
          user: data,
          message: `✅ 认证成功 - User: ${data.username}`
        })
      } else {
        const data = await response.json()
        setMeResult({
          success: false,
          message: `❌ 认证失败 (${response.status}): ${data.detail}`
        })
      }
    } catch (error: any) {
      setMeResult({
        success: false,
        message: `❌ 请求失败: ${error.message}`
      })
    }
  }

  return (
    <div style={{ padding: '20px', maxWidth: '800px', margin: '0 auto' }}>
      <h1>🔍 认证诊断页面</h1>

      <div style={{ background: '#f8f9fa', padding: '15px', margin: '15px 0', borderRadius: '8px' }}>
        <h2>Cookie 状态</h2>
        <button onClick={checkCookie} style={{ padding: '10px 20px', marginRight: '10px' }}>
          检查 Cookie
        </button>
        {cookieStatus && (
          <div style={{ marginTop: '10px', padding: '10px', background: '#d1ecf1', borderRadius: '4px' }}>
            <div>{cookieStatus.message}</div>
            <div style={{ fontSize: '12px', marginTop: '5px', fontFamily: 'monospace' }}>
              {cookieStatus.allCookies}
            </div>
          </div>
        )}
      </div>

      <div style={{ background: '#f8f9fa', padding: '15px', margin: '15px 0', borderRadius: '8px' }}>
        <h2>测试登录</h2>
        <button onClick={testLogin} style={{ padding: '10px 20px', background: '#007bff', color: 'white', border: 'none', borderRadius: '4px', cursor: 'pointer' }}>
          测试登录
        </button>
        {loginResult && (
          <div style={{ marginTop: '10px', padding: '10px', background: loginResult.success ? '#d1ecf1' : '#f8d7da', borderRadius: '4px' }}>
            {loginResult.message}
          {loginResult.user && (
            <div style={{ marginTop: '5px', fontSize: '12px' }}>
              Username: {loginResult.user.username}<br/>
              Email: {loginResult.user.email}
            </div>
          )}
          </div>
        )}
      </div>

      <div style={{ background: '#f8f9fa', padding: '15px', margin: '15px 0', borderRadius: '8px' }}>
        <h2>测试 /me API</h2>
        <button onClick={testMeAPI} style={{ padding: '10px 20px', background: '#28a745', color: 'white', border: 'none', borderRadius: '4px', cursor: 'pointer' }}>
          测试 /me API
        </button>
        {meResult && (
          <div style={{ marginTop: '10px', padding: '10px', background: meResult.success ? '#d1ecf1' : '#f8d7da', borderRadius: '4px' }}>
            {meResult.message}
            {meResult.user && (
            <div style={{ marginTop: '5px', fontSize: '12px' }}>
              Username: {meResult.user.username}<br/>
              Email: {meResult.user.email}
            </div>
            )}
          </div>
        )}
      </div>

      <div style={{ background: '#f8f9fa', padding: '15px', margin: '15px 0', borderRadius: '8px' }}>
        <h2>浏览器信息</h2>
        <div style={{ fontSize: '12px', fontFamily: 'monospace', padding: '10px', background: '#343a40', color: '#f8f9fa', borderRadius: '4px' }}>
          URL: {window.location.href}<br/>
          User Agent: {navigator.userAgent}<br/>
          Cookie Enabled: {navigator.cookieEnabled ? 'Yes' : 'No'}
        </div>
      </div>
    </div>
  )
}
