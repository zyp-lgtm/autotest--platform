// 健康检查 API
import apiClient from './client'
import type { HealthStatus } from '../types/health'

export const healthApi = {
  /**
   * 获取系统健康状态
   */
  async getHealthStatus(): Promise<HealthStatus> {
    const response = await apiClient.get<HealthStatus>('/v1/health')
    return response.data
  },

  /**
   * 强制刷新健康状态
   */
  async refreshHealthStatus(): Promise<HealthStatus> {
    const response = await apiClient.post<HealthStatus>('/v1/health/refresh', {})
    return response.data
  }
}
