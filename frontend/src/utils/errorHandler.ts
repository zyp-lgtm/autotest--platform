/**
 * 错误处理工具
 * 用于统一处理 API 错误
 */

export interface ApiError {
  status?: number
  data?: {
    detail?: string
    retry_after?: number
    code?: string
    message?: string
  }
  retryAfter?: number
}

/**
 * 检查是否为速率限制错误
 */
export function isRateLimitError(error: any): error is ApiError {
  return error?.response?.status === 429 || error?.retryAfter !== undefined
}

/**
 * 获取错误消息
 */
export function getErrorMessage(error: any): string {
  if (isRateLimitError(error)) {
    const retryAfter = error.response?.data?.retry_after || error.retryAfter
    return `请求过于频繁，请 ${retryAfter} 秒后再试`
  }

  if (error?.response?.data?.detail) {
    return error.response.data.detail
  }

  if (error?.response?.data?.message) {
    return error.response.data.message
  }

  if (error?.message) {
    return error.message
  }

  return '操作失败，请重试'
}

/**
 * 获取速率限制的等待时间
 */
export function getRetryAfter(error: any): number | null {
  if (isRateLimitError(error)) {
    return error.response?.data?.retry_after || error.retryAfter || null
  }
  return null
}
