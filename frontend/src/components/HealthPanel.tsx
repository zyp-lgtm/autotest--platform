// 健康状态面板组件 - 用于仪表板（带服务管理）
import { useEffect, useState } from 'react'
import { healthApi } from '../api/health'
import { servicesApi } from '../api/services'
import { useToast } from '../contexts/ToastContext'
import type { HealthStatus, ServiceHealth, ServiceStatus } from '../types/health'

export function HealthPanel() {
  const [health, setHealth] = useState<HealthStatus | null>(null)
  const toast = useToast()
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [operatingService, setOperatingService] = useState<string | null>(null)
  const [manualOperation, setManualOperation] = useState<{serviceId: string; action: 'stop' | 'start'; timestamp: number} | null>(null)
  const [showBackendTip, setShowBackendTip] = useState(false)

  const fetchHealth = async () => {
    try {
      setError(null)
      const status = await healthApi.getHealthStatus()

      // 如果有手动操作标记，检查服务实际状态
      if (manualOperation && manualOperation.action === 'stop') {
        const serviceIndex = ['backend', 'frontend', 'agent'].indexOf(manualOperation.serviceId)
        if (serviceIndex >= 0 && status.services[serviceIndex]?.status === 'healthy') {
          // 服务实际已经启动，清除手动操作标记
          setManualOperation(null)
          setShowBackendTip(false)
        }
      }

      setHealth(status)
    } catch (err) {
      setError(err instanceof Error ? err.message : '获取健康状态失败')
    } finally {
      setLoading(false)
    }
  }

  const handleServiceAction = async (serviceId: string, action: 'start' | 'stop' | 'restart') => {
    setOperatingService(serviceId)
    try {
      let result
      switch (action) {
        case 'start':
          result = await servicesApi.startService(serviceId)
          if (result.success) {
            setManualOperation(null)
            setShowBackendTip(false)
            setTimeout(() => fetchHealth(), 3000)
          } else {
            if (serviceId === 'backend') {
              setShowBackendTip(true)
            }
          }
          break
        case 'stop':
          result = await servicesApi.stopService(serviceId)
          if (result.success && health) {
            setManualOperation({ serviceId, action: 'stop', timestamp: Date.now() })
            setHealth({
              ...health,
              services: health.services.map((s, idx) =>
                ['backend', 'frontend', 'agent'][idx] === serviceId
                  ? { ...s, status: 'down' as const, message: '服务已停止' }
                  : s
              )
            })
            if (serviceId === 'backend') {
              setShowBackendTip(true)
            }
          }
          break
        case 'restart':
          result = await servicesApi.restartService(serviceId)
          if (result.success) {
            setManualOperation(null)
            if (serviceId === 'backend') {
              setTimeout(() => {
                setShowBackendTip(true)
                fetchHealth()
              }, 3000)
            } else {
              setTimeout(() => fetchHealth(), 3000)
            }
          }
          break
      }

      if (!result.success && serviceId !== 'backend') {
        toast.error(result.message)
        fetchHealth()
      }
    } catch (err) {
      if (serviceId === 'backend' && action === 'start') {
        setShowBackendTip(true)
      } else {
        toast.error(err instanceof Error ? err.message : '操作失败')
      }
      fetchHealth()
    } finally {
      setOperatingService(null)
    }
  }

  useEffect(() => {
    fetchHealth()

    const interval = setInterval(() => {
      if (manualOperation && manualOperation.action === 'stop') {
        const timeSinceOperation = Date.now() - manualOperation.timestamp
        if (timeSinceOperation < 60000) {
          console.log('[HealthPanel] 跳过刷新，保持手动停止状态')
          return
        } else {
          console.log('[HealthPanel] 超过60秒，清除手动操作标记')
          setManualOperation(null)
        }
      }
      console.log('[HealthPanel] 执行健康检查')
      fetchHealth()
    }, 5000)

    return () => clearInterval(interval)
  }, []) // 移除依赖，避免定时器重置

  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-lg font-semibold mb-4">系统健康状态</h2>
        <div className="flex items-center justify-center py-8">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
        </div>
      </div>
    )
  }

  if (error || !health) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-lg font-semibold mb-4">系统健康状态</h2>
        <div className="text-red-600 text-center py-4">
          {error || '无法获取健康状态'}
        </div>
      </div>
    )
  }

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-semibold">系统健康状态</h2>
        <button
          onClick={fetchHealth}
          className="text-sm text-blue-600 hover:text-blue-700"
        >
          刷新
        </button>
      </div>

      {/* 后端启动命令提示 */}
      {showBackendTip && (
        <div className="mb-4 bg-yellow-50 border border-yellow-200 rounded-lg p-4">
          <div className="flex items-start gap-3">
            <span className="text-yellow-600 text-2xl">💡</span>
            <div className="flex-1">
              <div className="text-sm font-semibold text-yellow-800 mb-1">后端服务已停止</div>
              <div className="text-xs text-yellow-700 mb-2">在任意终端执行以下命令启动后端：</div>
              <code className="block bg-gray-800 text-green-400 text-xs p-3 rounded font-mono overflow-x-auto">
                bash /Users/apple/aicode/.worktrees/test-platform/backend/start_backend.sh
              </code>
              <button
                onClick={() => {
                  setShowBackendTip(false)
                  // 如果后端已经启动，也清除手动操作标记
                  fetchHealth()
                }}
                className="mt-2 text-xs text-yellow-800 underline hover:text-yellow-900"
              >
                知道了
              </button>
            </div>
          </div>
        </div>
      )}

      {/* 总体状态 */}
      <div className={`mb-4 p-4 rounded-lg border ${
        health.overall === 'healthy' ? 'border-green-200 bg-green-50' :
        health.overall === 'degraded' ? 'border-yellow-200 bg-yellow-50' :
        'border-red-200 bg-red-50'
      }`}>
        <div className="flex items-center justify-between">
          <div>
            <div className="text-sm text-gray-600 mb-1">总体状态</div>
            <div className="text-2xl font-bold">
              {health.overall === 'healthy' && '🟢 系统正常'}
              {health.overall === 'degraded' && '🟡 系统警告'}
              {health.overall === 'down' && '🔴 系统异常'}
            </div>
          </div>
          <div className="text-right">
            <div className="text-sm text-gray-600 mb-1">核心服务</div>
            <div className="text-lg font-semibold">
              <span className="text-green-600">{health.summary.healthy}</span>
              {' / '}
              <span className="text-gray-600">{health.summary.total}</span>
            </div>
          </div>
        </div>
      </div>

      {/* 服务列表 */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
        {health.services.map((service, index) => {
          const serviceId = ['backend', 'frontend', 'agent'][index] || null
          const manageable = index < 3
          const isOperating = operatingService === serviceId

          // 如果该服务处于手动停止状态，覆盖显示状态
          const displayService = { ...service }
          if (manualOperation && manualOperation.serviceId === serviceId && manualOperation.action === 'stop') {
            const timeSinceOperation = Date.now() - manualOperation.timestamp
            if (timeSinceOperation < 60000) {
              displayService.status = 'down' as const
              displayService.message = '服务已停止'
            }
          }

          return (
            <ServiceCard
              key={index}
              service={{ ...displayService, id: serviceId || undefined, manageable }}
              onAction={handleServiceAction}
              operating={isOperating}
            />
          )
        })}
      </div>

      {/* 最后更新时间 */}
      <div className="mt-4 text-xs text-gray-500 text-center">
        最后更新: {new Date(health.timestamp).toLocaleString()}
      </div>
    </div>
  )
}

interface ServiceCardProps {
  service: ServiceHealth & { id?: string | null; manageable?: boolean }
  onAction: (serviceId: string, action: 'start' | 'stop' | 'restart') => Promise<void>
  operating?: boolean
}

function ServiceCard({ service, onAction, operating }: ServiceCardProps) {
  const getStatusColor = (status: ServiceStatus): string => {
    switch (status) {
      case 'healthy':
        return 'border-green-200 bg-green-50'
      case 'degraded':
        return 'border-yellow-200 bg-yellow-50'
      case 'down':
        return 'border-red-200 bg-red-50'
      default:
        return 'border-gray-200 bg-gray-50'
    }
  }

  const getStatusDot = (status: ServiceStatus): string => {
    switch (status) {
      case 'healthy':
        return 'bg-green-500'
      case 'degraded':
        return 'bg-yellow-500'
      case 'down':
        return 'bg-red-500'
      default:
        return 'bg-gray-500'
    }
  }

  return (
    <div className={`p-3 rounded-lg border ${getStatusColor(service.status)}`}>
      <div className="flex items-start justify-between gap-2">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <div className={`w-2 h-2 rounded-full ${getStatusDot(service.status)}`}></div>
            <h3 className="font-medium text-sm truncate">{service.name}</h3>
            {service.response_time && (
              <span className="text-xs text-gray-500">
                {(service.response_time * 1000).toFixed(0)}ms
              </span>
            )}
          </div>
          <p className="text-xs text-gray-600 truncate">{service.message}</p>

          {service.details && (
            <div className="mt-2 text-xs space-y-1">
              {Object.entries(service.details).map(([key, value]) => (
                <div key={key} className="flex items-center gap-2">
                  <span className="font-medium text-gray-500">{key}:</span>
                  <span className="font-mono text-gray-700">
                    {typeof value === 'number'
                      ? key.includes('percent') || key.includes('mb')
                        ? value.toFixed(2)
                        : value
                      : String(value)}
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* 服务管理按钮 */}
        {service.manageable && service.id && (
          <div className="flex flex-col gap-1">
            {service.status === 'down' ? (
              <button
                onClick={() => onAction(service.id!, 'start')}
                disabled={operating}
                className="px-3 py-1 text-xs bg-green-600 text-white rounded hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                {operating ? '启动中...' : '启动'}
              </button>
            ) : (
              <>
                <button
                  onClick={() => onAction(service.id!, 'restart')}
                  disabled={operating}
                  className="px-3 py-1 text-xs bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                  {operating ? '重启中...' : '重启'}
                </button>
                <button
                  onClick={() => onAction(service.id!, 'stop')}
                  disabled={operating}
                  className="px-3 py-1 text-xs bg-red-600 text-white rounded hover:bg-red-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                  停止
                </button>
              </>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
