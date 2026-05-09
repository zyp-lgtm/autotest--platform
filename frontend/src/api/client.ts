import axios from 'axios'

const apiClient = axios.create({
  baseURL: '/api',
  timeout: 180000, // 3分钟超时，UI测试执行需要较长时间
  withCredentials: true, // 支持 HttpOnly Cookie
})

// 请求拦截器：添加 token
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token')
    // 检查是否有 Cookie（通过 document.cookie 无法读取 HttpOnly Cookie，所以使用推断）
    const hasCookie = document.cookie.includes('access_token') || !token // 如果没有 localStorage token，说明依赖 Cookie

    console.log('[apiClient] 请求拦截器:', {
      method: config.method,
      url: config.url,
      authType: token ? 'localStorage' : (hasCookie ? 'Cookie' : 'none'),
      withCredentials: config.withCredentials
    })

    // 只在有有效的Bearer token时才添加Authorization头
    // 如果使用Cookie认证（token为'cookie-based'或不存在），不添加Authorization头
    if (token && token !== 'cookie-based') {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => Promise.reject(error)
)

// 响应拦截器：处理错误
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response) {
      console.log('[apiClient] 响应错误:', {
        status: error.response.status,
        url: error.config?.url,
        method: error.config?.method,
        statusText: error.response.statusText,
        data: error.response.data
      })

      // 处理速率限制错误 (429)
      if (error.response.status === 429) {
        const retryAfter = error.response.data?.retry_after
        console.log('[apiClient] 速率限制触发，需等待', retryAfter, '秒')

        // 将 retry_after 信息附加到错误对象上
        error.retryAfter = retryAfter
      }

      // 处理 401 未授权错误
      if (error.response.status === 401) {
        console.log('[apiClient] 检测到 401 错误，检查请求URL')

        // 如果不是在验证当前会话的请求，才清除并重定向
        const isMeRequest = error.config?.url?.includes('/me')

        if (!isMeRequest) {
          console.log('[apiClient] 401错误 - 清除认证信息')
          console.log('[apiClient] 当前路径:', window.location.pathname)

          // 清除 token
          localStorage.removeItem('access_token')

          // 触发自定义事件，通知 AuthContext 更新状态
          window.dispatchEvent(new CustomEvent('auth:logout'))

          // 延迟重定向，让日志有时间输出
          setTimeout(() => {
            if (!window.location.pathname.match(/^(\/login|\/register)/)) {
              console.log('[apiClient] 重定向到登录页面')
              window.location.href = '/login'
            }
          }, 100)
        } else {
          console.log('[apiClient] 401错误 - /me请求，不重定向（由AuthContext处理）')
        }
      }
    }
    return Promise.reject(error)
  }
)

export default apiClient
