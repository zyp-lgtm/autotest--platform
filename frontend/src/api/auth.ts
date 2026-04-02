import apiClient from './client'
import type { LoginRequest, RegisterRequest, AuthResponse, User } from '../types'

export const authApi = {
  login: async (data: LoginRequest): Promise<AuthResponse> => {
    const formData = new FormData()
    formData.append('username', data.username)
    formData.append('password', data.password)

    const response = await apiClient.post<AuthResponse>('/v1/auth/login', formData)
    return response.data
  },

  register: async (data: RegisterRequest): Promise<User> => {
    const response = await apiClient.post<User>('/v1/auth/register', data)
    return response.data
  },

  getCurrentUser: async (): Promise<User> => {
    const response = await apiClient.get<User>('/v1/auth/me')
    return response.data
  },
}
