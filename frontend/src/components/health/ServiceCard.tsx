/**
 * 服务卡片组件
 *
 * 显示单个服务的状态和控制按钮
 */
import type { ServiceHealth, ServiceStatus } from '../../types/health'
import { ServiceControlButton } from './ServiceControlButton'

interface ServiceCardProps {
  service: ServiceHealth & { id?: string | null; manageable?: boolean }
  onAction: (serviceId: string, action: 'start' | 'stop' | 'restart') => Promise<void>
  operating?: boolean
}

function getStatusColor(status: ServiceStatus): string {
  switch (status) {
    case 'healthy':
      return 'bg-green-100 text-green-800 border-green-200'
    case 'degraded':
      return 'bg-yellow-100 text-yellow-800 border-yellow-200'
    case 'down':
      return 'bg-red-100 text-red-800 border-red-200'
    default:
      return 'bg-gray-100 text-gray-800 border-gray-200'
  }
}

export function ServiceCard({ service, onAction, operating }: ServiceCardProps) {
  const isOperating = (operating || false) && (service.manageable || false) !== false

  return (
    <div className={`p-3 rounded-lg border ${getStatusColor(service.status)}`}>
      <div className="flex items-start justify-between gap-2">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <span className="text-sm font-medium">{service.name}</span>
            {service.response_time && (
              <span className="text-xs text-gray-500">
                {(service.response_time * 1000).toFixed(0)}ms
              </span>
            )}
          </div>
          <div className="text-xs opacity-75">{service.message}</div>
        </div>

        {/* 服务管理按钮 */}
        {service.manageable && service.id && (
          <div className="flex items-center gap-1">
            <ServiceControlButton
              status={service.status}
              isOperating={isOperating}
              onStart={() => onAction(service.id!, 'start')}
              onRestart={() => onAction(service.id!, 'restart')}
              onStop={() => onAction(service.id!, 'stop')}
            />
          </div>
        )}
      </div>
    </div>
  )
}
