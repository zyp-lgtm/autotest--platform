// 健康状态监控组件（带服务管理功能）
import { useEffect, useState } from 'react'
import { healthApi } from '../api/health'
import { servicesApi } from '../api/services'
import type { HealthStatus, ServiceHealth, ServiceStatus } from '../types/health'

export function HealthStatusIndicator() {
  const [health, setHealth] = useState<HealthStatus | null>(null)
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
          console.log('检测到服务已启动，清除手动操作标记')
          setManualOperation(null)
          setShowBackendTip(false)
        }
      }

      // 只在没有手动停止操作时更新健康状态
      // 如果有手动停止操作，保持显示的"已停止"状态
      if (!manualOperation || manualOperation.action !== 'stop') {
        setHealth(status)
      } else {
        console.log('有手动停止操作，跳过健康状态更新以保持停止状态')
      }
    } catch (err) {
      // 如果是后端停止导致的错误，不要覆盖手动停止状态
      if (manualOperation && manualOperation.action === 'stop' && manualOperation.serviceId === 'backend') {
        console.log('后端停止期间健康检查失败，保持停止状态')
        // 不更新状态，保持显示的停止状态
        return
      }
      setError(err instanceof Error ? err.message : '获取健康状态失败')
    } finally {
      setLoading(false)
    }
  }

  const handleServiceAction = async (serviceId: string, action: 'start' | 'stop' | 'restart') => {
    console.log('[ServiceAction] 开始操作:', serviceId, action)
    setOperatingService(serviceId)

    try {
      let result
      switch (action) {
        case 'start':
          console.log('[ServiceAction] 调用启动API')
          result = await servicesApi.startService(serviceId)
          console.log('[ServiceAction] 启动响应:', result)
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
          console.log('[ServiceAction] 调用停止API')
          result = await servicesApi.stopService(serviceId)
          console.log('[ServiceAction] 停止响应:', result)
          if (result.success) {
            console.log('[ServiceAction] 停止成功，准备更新状态')

            // 立即显示提示
            if (serviceId === 'backend') {
              console.log('[ServiceAction] 显示后端提示')
              setShowBackendTip(true)
            }

            // 设置手动操作标记
            setManualOperation({ serviceId, action: 'stop', timestamp: Date.now() })
            console.log('[ServiceAction] 已设置手动操作标记')

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
              console.log('[ServiceAction] 新的健康状态:', newHealth.services[0])
              setHealth(newHealth)
            } else {
              console.warn('[ServiceAction] health 为 null')
            }
          } else {
            console.warn('[ServiceAction] 停止失败:', result.message)
            alert(result.message)
          }
          break

        case 'restart':
          console.log('[ServiceAction] 调用重启API')
          result = await servicesApi.restartService(serviceId)
          console.log('[ServiceAction] 重启响应:', result)
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
        alert(result.message)
        fetchHealth()
      }
    } catch (err) {
      console.error('[ServiceAction] 操作异常:', err)
      if (serviceId === 'backend' && action === 'start') {
        setShowBackendTip(true)
      } else {
        alert(err instanceof Error ? err.message : '操作失败')
      }
      if (action !== 'stop') {
        fetchHealth()
      }
    } finally {
      console.log('[ServiceAction] 操作完成，清除操作状态')
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
          console.log('[AutoRefresh] 跳过刷新，保持手动停止状态')
          return
        } else {
          // 超过60秒，清除手动操作标记
          console.log('[AutoRefresh] 超过60秒，清除手动操作标记')
          setManualOperation(null)
        }
      }

      console.log('[AutoRefresh] 执行健康检查')
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
        <div className="mt-2 bg-yellow-50 border border-yellow-200 rounded-lg p-3 shadow-lg max-w-sm">
          <div className="flex items-start gap-2">
            <span className="text-yellow-600 text-lg">💡</span>
            <div className="flex-1">
              <div className="text-sm font-semibold text-yellow-800 mb-1">后端服务已停止</div>
              <div className="text-xs text-yellow-700 mb-2">在任意终端执行以下命令启动后端：</div>
              <code className="block bg-gray-800 text-green-400 text-xs p-2 rounded overflow-x-auto">
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

interface ServiceCardProps {
  service: ServiceHealth & { id?: string | null; manageable?: boolean }
  onAction: (serviceId: string, action: 'start' | 'stop' | 'restart') => Promise<void>
  operating?: boolean
}

function ServiceCard({ service, onAction, operating }: ServiceCardProps) {
  const getStatusColor = (status: ServiceStatus): string => {
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

  const isOperating = operating && service.manageable !== false

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
            {service.status === 'down' ? (
              <button
                onClick={() => onAction(service.id!, 'start')}
                disabled={isOperating}
                className="px-2 py-1 text-xs bg-green-600 text-white rounded hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed"
                title="启动服务"
              >
                {isOperating ? '启动中...' : '启动'}
              </button>
            ) : (
              <>
                <button
                  onClick={() => onAction(service.id!, 'restart')}
                  disabled={isOperating}
                  className="px-2 py-1 text-xs bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
                  title="重启服务"
                >
                  {isOperating ? '重启中...' : '重启'}
                </button>
                <button
                  onClick={() => onAction(service.id!, 'stop')}
                  disabled={isOperating}
                  className="px-2 py-1 text-xs bg-red-600 text-white rounded hover:bg-red-700 disabled:opacity-50 disabled:cursor-not-allowed"
                  title="停止服务"
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
