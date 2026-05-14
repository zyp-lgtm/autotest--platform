// 健康状态监控组件（带服务管理功能）
import { useEffect, useState } from 'react'
import { healthApi } from '../api/health'
import { servicesApi } from '../api/services'
import { useToast } from '../contexts/ToastContext'
import type { HealthStatus, ServiceStatus } from '../types/health'
import { ServiceCard } from './health/ServiceCard'
import { BackendTipBanner } from './health/BackendTipBanner'

export function HealthStatusIndicator() {
  const [health, setHealth] = useState<HealthStatus | null>(null)
  const toast = useToast()
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [isOpen, setIsOpen] = useState(false)
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

      // 只在没有手动停止操作时更新健康状态
      // 如果有手动停止操作，保持显示的"已停止"状态
      if (!manualOperation || manualOperation.action !== 'stop') {
        setHealth(status)
      }
    } catch (err) {
      // 如果是后端停止导致的错误，不要覆盖手动停止状态
      if (manualOperation && manualOperation.action === 'stop' && manualOperation.serviceId === 'backend') {
        // 不更新状态，保持显示的停止状态
        return
      }
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
            // 启动失败，显示提示
            if (serviceId === 'backend') {
              setShowBackendTip(true)
            }
          }
          break

        case 'stop':
          result = await servicesApi.stopService(serviceId)
          if (result.success) {
            // 立即显示提示
            if (serviceId === 'backend') {
              setShowBackendTip(true)
            }

            // 设置手动操作标记
            setManualOperation({ serviceId, action: 'stop', timestamp: Date.now() })

            // 更新健康状态
            if (health) {
              const newHealth = {
                ...health,
                services: health.services.map((s, idx) =>
                  ['backend', 'frontend', 'agent'][idx] === serviceId
                    ? { ...s, status: 'down' as const, message: '服务已停止' }
                    : s
                )
              }
              setHealth(newHealth)
            }
          } else {
            toast.error(result.message)
          }
          break

        case 'restart':
          result = await servicesApi.restartService(serviceId)
          if (result.success) {
            setManualOperation(null)
            if (serviceId === 'backend') {
              // 重启后端后延迟显示提示
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
      console.error('[ServiceAction] 操作异常:', err)
      if (serviceId === 'backend' && action === 'start') {
        setShowBackendTip(true)
      } else {
        toast.error(err instanceof Error ? err.message : '操作失败')
      }
      if (action !== 'stop') {
        fetchHealth()
      }
    } finally {
      setOperatingService(null)
    }
  }

  useEffect(() => {
    fetchHealth()

    const interval = setInterval(() => {
      // 如果有手动停止操作，且时间不超过60秒，跳过自动刷新该服务状态
      if (manualOperation && manualOperation.action === 'stop') {
        const timeSinceOperation = Date.now() - manualOperation.timestamp
        if (timeSinceOperation < 60000) {
          // 跳过自动刷新，保持手动停止的状态
          return
        } else {
          // 超过60秒，清除手动操作标记
          setManualOperation(null)
        }
      }

      fetchHealth()
    }, 5000)

    return () => clearInterval(interval)
  }, []) // 移除 manualOperation 依赖，避免每次都重新创建定时器

  const getStatusColor = (status: ServiceStatus): string => {
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

  if (loading) {
    return (
      <div className="fixed top-4 right-4 z-50">
        <div className="bg-white rounded-lg shadow-lg p-3 flex items-center gap-2">
          <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-500"></div>
          <span className="text-sm text-gray-600">加载中...</span>
        </div>
      </div>
    )
  }

  if (error || !health) {
    return (
      <div className="fixed top-4 right-4 z-50">
        <div className="bg-white rounded-lg shadow-lg p-3 flex items-center gap-2 cursor-pointer hover:bg-gray-50">
          <div className="w-3 h-3 rounded-full bg-gray-400"></div>
          <span className="text-sm text-gray-600">状态未知</span>
        </div>
      </div>
    )
  }

  return (
    <div className="fixed top-4 right-4 z-50">
      <div
        onClick={() => setIsOpen(!isOpen)}
        className="bg-white rounded-lg shadow-lg p-3 flex items-center gap-2 cursor-pointer hover:bg-gray-50 transition-colors"
      >
        <div className={`w-3 h-3 rounded-full ${getStatusColor(health.overall)}`}></div>
        <span className="text-sm font-medium">
          {health.overall === 'healthy' && '系统正常'}
          {health.overall === 'degraded' && '系统警告'}
          {health.overall === 'down' && '系统异常'}
        </span>
        <span className="text-xs text-gray-500">
          ({health.summary.healthy}/{health.summary.total})
        </span>
      </div>

      {/* 后端启动命令提示 */}
      {showBackendTip && (
        <BackendTipBanner
          onDismiss={() => setShowBackendTip(false)}
          onRefresh={fetchHealth}
        />
      )}

      {isOpen && (
        <div className="mt-2 bg-white rounded-lg shadow-lg p-4 w-96 max-h-[70vh] overflow-y-auto">
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-sm font-semibold">系统健康状态</h3>
            <button
              onClick={() => setIsOpen(false)}
              className="text-gray-400 hover:text-gray-600"
            >
              ✕
            </button>
          </div>

          <div className="mb-4 p-3 bg-gray-50 rounded-lg">
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-600">总体状态</span>
              <div className="flex items-center gap-2">
                <span>
                  {health.overall === 'healthy' && '🟢 正常'}
                  {health.overall === 'degraded' && '🟡 警告'}
                  {health.overall === 'down' && '🔴 异常'}
                </span>
              </div>
            </div>
            <div className="mt-2 text-xs text-gray-500">
              最后更新: {new Date(health.timestamp).toLocaleTimeString()}
            </div>
          </div>

          <div className="space-y-2">
            {health.services.map((service, index) => {
              // 为核心服务添加ID
              const serviceId = ['backend', 'frontend', 'agent'][index] || null
              const manageable = index < 3  // 前3个服务可管理

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
                  operating={operatingService === serviceId}
                />
              )
            })}
          </div>

          <div className="mt-4 pt-3 border-t flex gap-2">
            <button
              onClick={fetchHealth}
              className="flex-1 px-3 py-2 text-sm bg-blue-500 text-white rounded hover:bg-blue-600 transition-colors"
            >
              刷新
            </button>
            <button
              onClick={() => setIsOpen(false)}
              className="flex-1 px-3 py-2 text-sm bg-gray-200 text-gray-700 rounded hover:bg-gray-300 transition-colors"
            >
              关闭
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
