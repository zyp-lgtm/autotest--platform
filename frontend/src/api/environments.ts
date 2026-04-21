import apiClient from './client'

// 环境配置相关类型定义
export interface Environment {
  id: string
  project_id: string
  name: string
  base_url?: string
  variables: Record<string, any>
  is_default: boolean
  created_at: string
  updated_at?: string
}

export interface EnvironmentCreate {
  project_id: string
  name: string
  base_url?: string
  variables?: Record<string, any>
  is_default?: boolean
}

export interface EnvironmentUpdate {
  name?: string
  base_url?: string
  variables?: Record<string, any>
  is_default?: boolean
}

export const environmentsApi = {
  // 获取环境列表
  getEnvironments: async (projectId?: string): Promise<Environment[]> => {
    const params = projectId ? `?project_id=${projectId}` : ''
    const response = await apiClient.get<Environment[]>(`/v1/environments/${params}`)
    return response.data
  },

  // 获取环境详情
  getEnvironment: async (environmentId: string): Promise<Environment> => {
    const response = await apiClient.get<Environment>(`/v1/environments/${environmentId}`)
    return response.data
  },

  // 获取默认环境
  getDefaultEnvironment: async (projectId: string): Promise<Environment | { message: string }> => {
    const response = await apiClient.get<Environment | { message: string }>(`/v1/environments/project/${projectId}/default`)
    return response.data
  },

  // 创建环境
  createEnvironment: async (data: EnvironmentCreate): Promise<Environment> => {
    const response = await apiClient.post<Environment>('/v1/environments/', data)
    return response.data
  },

  // 更新环境
  updateEnvironment: async (environmentId: string, data: EnvironmentUpdate): Promise<Environment> => {
    const response = await apiClient.put<Environment>(`/v1/environments/${environmentId}`, data)
    return response.data
  },

  // 删除环境
  deleteEnvironment: async (environmentId: string): Promise<void> => {
    await apiClient.delete(`/v1/environments/${environmentId}`)
  },

  // 设置默认环境
  setDefaultEnvironment: async (environmentId: string): Promise<Environment> => {
    const response = await apiClient.post<Environment>(`/v1/environments/${environmentId}/set-default`)
    return response.data
  },
}
