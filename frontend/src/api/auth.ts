import apiClient from './client'
import type { LoginRequest, RegisterRequest, AuthResponse, User } from '../types'

export const authApi = {
  login: async (data: LoginRequest): Promise<AuthResponse> => {
    // 使用 URLSearchParams 发送 form-encoded 数据
    const params = new URLSearchParams()
    params.append('username', data.username)
    params.append('password', data.password)

    const response = await apiClient.post<AuthResponse>('/api/v1/auth/login', params)
    return response.data
  },

  register: async (data: RegisterRequest): Promise<User> => {
    const response = await apiClient.post<User>('/api/v1/auth/register', data)
    return response.data
  },

  getCurrentUser: async (): Promise<User> => {
    const response = await apiClient.get<User>('/api/v1/auth/me')
    return response.data
  },
}
