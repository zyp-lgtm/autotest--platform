import apiClient from './client'
import type { UITask } from '../types'

export const tasksApi = {
  getTasks: async (projectId: string): Promise<UITask[]> => {
    const response = await apiClient.get<UITask[]>(`/v1/ui/tasks/?project_id=${projectId}`)
    return response.data
  },

  getTask: async (taskId: string): Promise<UITask> => {
    const response = await apiClient.get<UITask>(`/v1/ui/tasks/${taskId}`)
    return response.data
  },

  createTask: async (projectId: string, data: Partial<UITask>): Promise<UITask> => {
    const response = await apiClient.post<UITask>(`/v1/ui/tasks/?project_id=${projectId}`, data)
    return response.data
  },

  updateTask: async (taskId: string, data: Partial<UITask>): Promise<UITask> => {
    const response = await apiClient.put<UITask>(`/v1/ui/tasks/${taskId}`, data)
    return response.data
  },

  deleteTask: async (taskId: string): Promise<void> => {
    await apiClient.delete(`/v1/ui/tasks/${taskId}`)
  },

  executeTask: async (taskId: string): Promise<any> => {
    const response = await apiClient.post(`/v1/ui/tasks/${taskId}/execute`, {})
    return response.data
  },

  getTaskExecutions: async (taskId: string, limit: number = 10): Promise<any[]> => {
    const response = await apiClient.get(`/v1/ui/tasks/${taskId}/executions?limit=${limit}`)
    return response.data
  },

  getExecution: async (executionId: string): Promise<any> => {
    const response = await apiClient.get(`/v1/ui/tasks/executions/${executionId}`)
    return response.data
  },
}
