import { useState, useEffect } from 'react'
import { useAuth } from '../hooks/useAuth'
import { tasksApi } from '../api/tasks'
import { Button } from '../components/ui/Button'
import { Card } from '../components/ui/Card'
import { HealthPanel } from '../components/HealthPanel'

interface DashboardStats {
  totalTasks: number
  totalScenarios: number
  totalCases: number
}

function Dashboard() {
  const { user } = useAuth()
  const [stats, setStats] = useState<DashboardStats>({
    totalTasks: 0,
    totalScenarios: 0,
    totalCases: 0,
  })
  const [loading, setLoading] = useState(true)

  // TODO: 从项目列表中获取项目 ID
  // 暂时使用固定项目 ID
  const projectId = '550e8400-e29b-41d4-a716-446655440000'

  useEffect(() => {
    const fetchStats = async () => {
      try {
        const tasks = await tasksApi.getTasks(projectId)

        // 计算统计数据
        let totalScenarios = 0
        let totalCases = 0

        // TODO: 并行获取场景详情来计算准确数量
        tasks.forEach(task => {
          totalScenarios += task.scenario_ids.length
          totalCases += task.scenario_ids.length * 2 // 假设每个场景 2 个用例
        })

        setStats({
          totalTasks: tasks.length,
          totalScenarios,
          totalCases,
        })
      } catch (error) {
        console.error('Failed to fetch stats:', error)
      } finally {
        setLoading(false)
      }
    }

    fetchStats()
  }, [projectId])

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-gray-600">加载中...</div>
      </div>
    )
  }

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">仪表盘</h1>
          <p className="text-gray-600">欢迎回来，{user?.username}</p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        <Card className="p-6">
          <h3 className="text-lg font-semibold mb-2">总任务数</h3>
          <p className="text-3xl font-bold text-blue-600">{stats.totalTasks}</p>
          <p className="text-sm text-gray-500 mt-2">UI 测试任务</p>
        </Card>

        <Card className="p-6">
          <h3 className="text-lg font-semibold mb-2">总场景数</h3>
          <p className="text-3xl font-bold text-green-600">{stats.totalScenarios}</p>
          <p className="text-sm text-gray-500 mt-2">测试场景</p>
        </Card>

        <Card className="p-6">
          <h3 className="text-lg font-semibold mb-2">总用例数</h3>
          <p className="text-3xl font-bold text-purple-600">{stats.totalCases}</p>
          <p className="text-sm text-gray-500 mt-2">测试用例</p>
        </Card>
      </div>

      {/* 健康状态面板 */}
      <HealthPanel />

      <Card className="p-6">
        <h2 className="text-xl font-bold mb-4">快捷操作</h2>
        <div className="grid grid-cols-2 gap-4">
          <Button>创建新任务</Button>
          <Button variant="secondary">管理测试数据</Button>
        </div>
        <p className="mt-4 text-sm text-gray-500">
          更多功能即将推出...
        </p>
      </Card>

      <Card className="mt-6 p-6">
        <h2 className="text-xl font-bold mb-4">最近活动</h2>
        <div className="space-y-3">
          <div className="flex items-center gap-3 p-3 bg-gray-50 rounded-lg">
            <span className="text-2xl">📋</span>
            <div>
              <div className="font-medium">创建了测试任务</div>
              <div className="text-sm text-gray-500">2 小时前</div>
            </div>
          </div>
          <div className="flex items-center gap-3 p-3 bg-gray-50 rounded-lg">
            <span className="text-2xl">🧪</span>
            <div>
              <div className="font-medium">执行了测试</div>
              <div className="text-sm text-gray-500">昨天</div>
            </div>
          </div>
        </div>
      </Card>
    </div>
  )
}

export default Dashboard
