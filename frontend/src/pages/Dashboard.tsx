import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'
import { useProject } from '../contexts/ProjectContext'
import { statsApi, type DashboardStats } from '../api/stats'
import { useToast } from '../contexts/ToastContext'
import { auditApi } from '../api/audit'
import { Button } from '../components/ui/Button'
import { Card } from '../components/ui/Card'
import { HealthPanel } from '../components/HealthPanel'

interface AuditLog {
  id: string
  action: string
  resource_type: string
  details: Record<string, any> | null
  success: boolean
  timestamp: string
}

function Dashboard() {
  const { user } = useAuth()
  const { currentProject } = useProject()
  const navigate = useNavigate()
  const toast = useToast()
  const [stats, setStats] = useState<DashboardStats>({
    total_tasks: 0,
    total_scenarios: 0,
    total_cases: 0,
    total_steps: 0,
    recent_executions: 0,
  })
  const [auditLogs, setAuditLogs] = useState<AuditLog[]>([])
  const [loading, setLoading] = useState(true)
  const [logsLoading, setLogsLoading] = useState(false)

  useEffect(() => {
    if (currentProject) {
      loadStats()
    } else {
      // 没有项目时，不显示加载状态
      setLoading(false)
    }
  }, [currentProject])

  useEffect(() => {
    if (user) {
      loadAuditLogs()
    }
  }, [user])

  const loadStats = async () => {
    if (!currentProject) return

    try {
      setLoading(true)
      const data = await statsApi.getDashboardStats(currentProject.id)
      setStats(data)
    } catch (error: any) {
      console.error('Failed to fetch stats:', error)
      toast.error('加载统计数据失败，请确认后端已重启')
    } finally {
      setLoading(false)
    }
  }

  const loadAuditLogs = async () => {
    if (!user) return

    try {
      setLogsLoading(true)
      const response = await auditApi.getUserLogs(user.id, 10)
      setAuditLogs(response.logs || [])
    } catch (error) {
      console.error('Failed to fetch audit logs:', error)
      setAuditLogs([])
    } finally {
      setLogsLoading(false)
    }
  }

  const getActionIcon = (action: string) => {
    const iconMap: Record<string, string> = {
      'create': '📝',
      'update': '✏️',
      'delete': '🗑️',
      'execute': '▶️',
      'login': '🔐',
      'logout': '👋',
      'read': '👁️',
    }
    return iconMap[action] || '📋'
  }

  const getActionText = (action: string) => {
    const textMap: Record<string, string> = {
      'create': '创建了',
      'update': '更新了',
      'delete': '删除了',
      'execute': '执行了',
      'login': '登录了',
      'logout': '登出了',
      'read': '查看了',
    }
    return textMap[action] || action
  }

  const getResourceText = (resourceType: string) => {
    const typeMap: Record<string, string> = {
      'task': '任务',
      'scenario': '场景',
      'case': '用例',
      'step': '步骤',
      'test_data': '测试数据',
      'project': '项目',
      'execution': '执行记录',
    }
    return typeMap[resourceType] || resourceType
  }

  const formatTime = (timestamp: string) => {
    const date = new Date(timestamp)
    const now = new Date()
    const diffMs = now.getTime() - date.getTime()
    const diffMins = Math.floor(diffMs / 60000)
    const diffHours = Math.floor(diffMs / 3600000)
    const diffDays = Math.floor(diffMs / 86400000)

    if (diffMins < 1) return '刚刚'
    if (diffMins < 60) return `${diffMins} 分钟前`
    if (diffHours < 24) return `${diffHours} 小时前`
    return `${diffDays} 天前`
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-gray-600">加载中...</div>
      </div>
    )
  }

  if (!currentProject) {
    return (
      <div className="flex flex-col items-center justify-center h-64">
        <div className="text-gray-600 mb-4">请先创建或选择一个项目</div>
        <Button onClick={() => navigate('/projects')}>
          前往项目管理
        </Button>
      </div>
    )
  }

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">仪表盘</h1>
          <p className="text-gray-600">
            欢迎回来，{user?.username} · {currentProject?.name || '未选择项目'}
          </p>
        </div>
      </div>

      {/* 统计卡片 */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
        <Card className="p-6">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-sm font-medium text-gray-600 mb-1">总任务数</h3>
              <p className="text-2xl font-bold text-blue-600">{stats.total_tasks}</p>
            </div>
            <span className="text-2xl">📋</span>
          </div>
        </Card>

        <Card className="p-6">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-sm font-medium text-gray-600 mb-1">总场景数</h3>
              <p className="text-2xl font-bold text-green-600">{stats.total_scenarios}</p>
            </div>
            <span className="text-2xl">📑</span>
          </div>
        </Card>

        <Card className="p-6">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-sm font-medium text-gray-600 mb-1">总用例数</h3>
              <p className="text-2xl font-bold text-purple-600">{stats.total_cases}</p>
            </div>
            <span className="text-2xl">📄</span>
          </div>
        </Card>

        <Card className="p-6">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-sm font-medium text-gray-600 mb-1">总步骤数</h3>
              <p className="text-2xl font-bold text-orange-600">{stats.total_steps}</p>
            </div>
            <span className="text-2xl">⚙️</span>
          </div>
        </Card>
      </div>

      {/* 健康状态面板 */}
      <HealthPanel />

      {/* 快捷操作 */}
      <Card className="p-6 mb-6">
        <h2 className="text-lg font-bold mb-4">快捷操作</h2>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          <Button
            onClick={() => navigate('/tasks/new')}
            className="w-full"
          >
            <span className="text-xl mr-2">➕</span>
            创建任务
          </Button>
          <Button
            onClick={() => navigate('/test-data')}
            variant="secondary"
            className="w-full"
          >
            <span className="text-xl mr-2">📊</span>
            测试数据
          </Button>
          <Button
            onClick={() => navigate('/projects')}
            variant="secondary"
            className="w-full"
          >
            <span className="text-xl mr-2">🗂️</span>
            项目管理
          </Button>
          <Button
            onClick={() => navigate('/scheduled-jobs')}
            variant="secondary"
            className="w-full"
          >
            <span className="text-xl mr-2">⏰</span>
            定时任务
          </Button>
        </div>
      </Card>

      {/* 最近活动 */}
      <Card className="p-6">
        <h2 className="text-lg font-bold mb-4">最近活动</h2>
        {!currentProject ? (
          <div className="text-center py-8 text-gray-500">
            请先选择一个项目以查看活动记录
          </div>
        ) : logsLoading ? (
          <div className="text-center py-8 text-gray-500">
            加载中...
          </div>
        ) : auditLogs.length === 0 ? (
          <div className="text-center py-8 text-gray-500">
            暂无活动记录
          </div>
        ) : (
          <div className="space-y-2">
            {auditLogs.map((log) => (
              <div key={log.id} className="flex items-center gap-3 p-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition">
                <span className="text-xl flex-shrink-0">
                  {getActionIcon(log.action)}
                </span>
                <div className="flex-1 min-w-0">
                  <div className="text-sm font-medium text-gray-900">
                    {getActionText(log.action)} {getResourceText(log.resource_type)}
                  </div>
                  {log.details && (
                    <div className="text-xs text-gray-500 truncate">
                      {typeof log.details === 'string'
                        ? log.details
                        : log.details.path || log.details.method
                          ? `${log.details.method || ''} ${log.details.path || ''}`
                          : JSON.stringify(log.details)
                      }
                    </div>
                  )}
                </div>
                <div className="text-xs text-gray-500 flex-shrink-0">
                  {formatTime(log.timestamp)}
                </div>
              </div>
            ))}
          </div>
        )}
      </Card>
    </div>
  )
}

export default Dashboard
