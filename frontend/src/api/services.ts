// 服务管理 API
import apiClient from './client'

export interface ServiceActionResponse {
  success: boolean
  message: string
  pid?: number
}

export const servicesApi = {
  /**
   * 启动服务
   */
  async startService(serviceId: string): Promise<ServiceActionResponse> {
    const response = await apiClient.post<ServiceActionResponse>(`/v1/services/${serviceId}/start`)
    return response.data
  },

  /**
   * 停止服务
   */
  async stopService(serviceId: string): Promise<ServiceActionResponse> {
    const response = await apiClient.post<ServiceActionResponse>(`/v1/services/${serviceId}/stop`)
    return response.data
  },

  /**
   * 重启服务
   */
  async restartService(serviceId: string): Promise<ServiceActionResponse> {
    const response = await apiClient.post<ServiceActionResponse>(`/v1/services/${serviceId}/restart`)
    return response.data
  }
}
