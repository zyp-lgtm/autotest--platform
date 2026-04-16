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
    console.log('[apiClient] 请求拦截器:', {
      method: config.method,
      url: config.url,
      hasToken: !!token,
      tokenPrefix: token ? token.substring(0, 20) + '...' : 'none'
    })
    if (token) {
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
        console.log('[apiClient] 检测到 401 错误，清除认证信息')
        console.log('[apiClient] 当前路径:', window.location.pathname)
        console.log('[apiClient] 清除前 localStorage 有 token:', !!localStorage.getItem('access_token'))

        // 清除 token
        localStorage.removeItem('access_token')

        console.log('[apiClient] Token 已清除，localStorage 现在有 token:', !!localStorage.getItem('access_token'))

        // 触发自定义事件，通知 AuthContext 更新状态
        window.dispatchEvent(new CustomEvent('auth:logout'))

        // 延迟重定向，让日志有时间输出
        setTimeout(() => {
          if (!window.location.pathname.match(/^(\/login|\/register)/)) {
            console.log('[apiClient] 重定向到登录页面')
            window.location.href = '/login'
          }
        }, 100)
      }
    }
    return Promise.reject(error)
  }
)

export default apiClient
