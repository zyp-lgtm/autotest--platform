import apiClient from './client'

export interface DashboardStats {
  total_tasks: number
  total_scenarios: number
  total_cases: number
  total_steps: number
  recent_executions: number
}

export const statsApi = {
  getDashboardStats: async (projectId: string): Promise<DashboardStats> => {
    const response = await apiClient.get<DashboardStats>(
      `/v1/stats/dashboard?project_id=${projectId}`
    )
    return response.data
  },
}
