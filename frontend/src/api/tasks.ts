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
}
