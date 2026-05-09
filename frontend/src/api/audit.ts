import apiClient from './client'

export interface AuditLog {
  id: string
  user_id: string
  username: string
  action: string
  resource_type: string
  resource_id: string
  details: string
  ip_address: string
  success: boolean
  timestamp: string
}

export interface AuditLogsResponse {
  total: number
  logs: AuditLog[]
}

export const auditApi = {
  getUserLogs: async (userId: string, limit: number = 20): Promise<AuditLogsResponse> => {
    const response = await apiClient.get<AuditLogsResponse>(`/v1/audit/logs/user/${userId}?limit=${limit}`)
    return response.data
  }
}
