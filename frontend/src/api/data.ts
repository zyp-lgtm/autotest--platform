import apiClient from './client'
import type { TestData } from '../types'

export const dataApi = {
  getTestData: async (projectId: string): Promise<TestData[]> => {
    const response = await apiClient.get<TestData[]>(`/v1/projects/${projectId}/data/`)
    return response.data
  },

  createTestData: async (projectId: string, data: Partial<TestData>): Promise<TestData> => {
    const response = await apiClient.post<TestData>(`/v1/projects/${projectId}/data/`, data)
    return response.data
  },

  deleteTestData: async (projectId: string, dataId: string): Promise<void> => {
    await apiClient.delete(`/v1/projects/${projectId}/data/${dataId}`)
  },
}
