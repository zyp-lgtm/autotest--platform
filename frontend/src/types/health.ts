// 健康检查类型定义

export type ServiceStatus = 'healthy' | 'degraded' | 'down'

export interface ServiceHealth {
  id?: string  // 服务ID，用于服务管理操作
  name: string
  status: ServiceStatus
  message: string
  response_time?: number
  details?: Record<string, any>
  manageable?: boolean  // 是否可管理（可启动/停止/重启）
}

export interface HealthSummary {
  total: number
  healthy: number
  degraded: number
  down: number
}

export interface HealthStatus {
  timestamp: string
  overall: ServiceStatus
  summary: HealthSummary
  services: ServiceHealth[]
}

