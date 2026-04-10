import axios from 'axios'

const apiClient = axios.create({
  baseURL: '/api',
  timeout: 180000, // 3分钟超时，UI测试执行需要较长时间
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

// 响应拦截器：处理 401 错误
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response) {
      console.log('[apiClient] 响应错误:', {
        status: error.response.status,
        url: error.config?.url,
        method: error.config?.method,
        statusText: error.response.statusText
      })
    }

    if (error.response?.status === 401) {
      console.log('[apiClient] 检测到 401 错误，清除认证信息')
      console.log('[apiClient] 当前路径:', window.location.pathname)

      // 清除 token
      localStorage.removeItem('access_token')

      // 触发自定义事件，通知 AuthContext 更新状态
      window.dispatchEvent(new CustomEvent('auth:logout'))

      // 只在非登录/注册页面时才重定向
      if (!window.location.pathname.match(/^(\/login|\/register)/)) {
        console.log('[apiClient] 重定向到登录页面')
        window.location.href = '/login'
      }
    }
    return Promise.reject(error)
  }
)

export default apiClient
