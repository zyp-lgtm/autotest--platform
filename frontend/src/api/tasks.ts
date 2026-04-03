import apiClient from './client'
import type { UITask } from '../types'

export const tasksApi = {
  getTasks: async (projectId: string): Promise<UITask[]> => {
    const response = await apiClient.get<UITask[]>(`/api/v1/ui/tasks/?project_id=${projectId}`)
    return response.data
  },

  getTask: async (taskId: string): Promise<UITask> => {
    const response = await apiClient.get<UITask>(`/api/v1/ui/tasks/${taskId}`)
    return response.data
  },

  createTask: async (projectId: string, data: Partial<UITask>): Promise<UITask> => {
    const response = await apiClient.post<UITask>(`/api/v1/ui/tasks/?project_id=${projectId}`, data)
    return response.data
  },

  updateTask: async (taskId: string, data: Partial<UITask>): Promise<UITask> => {
    const response = await apiClient.put<UITask>(`/api/v1/ui/tasks/${taskId}`, data)
    return response.data
  },

  deleteTask: async (taskId: string): Promise<void> => {
    await apiClient.delete(`/api/v1/ui/tasks/${taskId}`)
  },

  executeTask: async (taskId: string): Promise<{ execution_id: string; status: string }> => {
    const response = await apiClient.post<{ execution_id: string; status: string }>(`/api/v1/ui/tasks/${taskId}/execute`, {})
    return response.data
  },
}
