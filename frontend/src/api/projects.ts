import apiClient from './client'

// 项目相关类型定义
export interface Project {
  id: string
  name: string
  description: string
  owner_id: string
  created_at: string
  updated_at?: string
}

export interface ProjectCreate {
  name: string
  description?: string
}

export interface ProjectUpdate {
  name?: string
  description?: string
}

export const projectsApi = {
  // 获取项目列表
  getProjects: async (): Promise<Project[]> => {
    const response = await apiClient.get<Project[]>('/v1/projects/')
    return response.data
  },

  // 获取项目详情
  getProject: async (projectId: string): Promise<Project> => {
    const response = await apiClient.get<Project>(`/v1/projects/${projectId}`)
    return response.data
  },

  // 创建项目
  createProject: async (data: ProjectCreate): Promise<Project> => {
    const response = await apiClient.post<Project>('/v1/projects/', data)
    return response.data
  },

  // 更新项目
  updateProject: async (projectId: string, data: ProjectUpdate): Promise<Project> => {
    const response = await apiClient.put<Project>(`/v1/projects/${projectId}`, data)
    return response.data
  },

  // 删除项目
  deleteProject: async (projectId: string): Promise<void> => {
    await apiClient.delete(`/v1/projects/${projectId}`)
  },
}
