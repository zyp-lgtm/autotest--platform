import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useProject } from '../contexts/ProjectContext'
import { tasksApi } from '../api/tasks'
import type { UITask } from '../types'
import type { TestExecution } from '../types'

export default function Tasks() {
  const navigate = useNavigate()
  const { currentProject } = useProject()
  const [tasks, setTasks] = useState<UITask[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [searchTerm, setSearchTerm] = useState('')
  const [executions, setExecutions] = useState<Record<string, TestExecution[]>>({})
  const [showHistory, setShowHistory] = useState<Record<string, boolean>>({})

  useEffect(() => {
    loadTasks()
  }, [currentProject])

  const loadTasks = async () => {
    if (!currentProject) {
      setLoading(false)
      return
    }

    try {
      setLoading(true)
      setError(null)
      const data = await tasksApi.getTasks(currentProject.id)
      setTasks(data)
    } catch (err: any) {
      setError(err.response?.data?.detail || '加载任务失败')
    } finally {
      setLoading(false)
    }
  }

  const handleDelete = async (taskId: string, taskName: string) => {
    if (!confirm(`确定要删除任务 "${taskName}" 吗？`)) {
      return
    }

    try {
      await tasksApi.deleteTask(taskId)
      setTasks(tasks.filter(t => t.id !== taskId))
    } catch (err: any) {
      alert('删除失败: ' + (err.response?.data?.detail || err.message))
    }
  }

  const handleExecute = async (taskId: string) => {
    try {
      const result = await tasksApi.executeTask(taskId)
      // 执行成功后导航到报告页面
      navigate(`/executions/${result.id}`)
    } catch (err: any) {
      alert('执行失败: ' + (err.response?.data?.detail || err.message))
    }
  }

  const loadExecutions = async (taskId: string) => {
    try {
      const data = await tasksApi.getTaskExecutions(taskId, 5)
      setExecutions(prev => ({ ...prev, [taskId]: data }))
    } catch (err: any) {
      console.error('加载执行历史失败:', err)
    }
  }

  const toggleHistory = async (taskId: string) => {
    const isShowing = showHistory[taskId]
    setShowHistory(prev => ({ ...prev, [taskId]: !isShowing }))

    // 如果首次展开，加载执行历史
    if (!isShowing && !executions[taskId]) {
      await loadExecutions(taskId)
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed': return 'text-green-600'
      case 'running': return 'text-blue-600'
      case 'failed': return 'text-red-600'
      default: return 'text-gray-600'
    }
  }

  const getResultBadge = (result?: string) => {
    if (!result) return null
    switch (result) {
      case 'pass': return 'bg-green-100 text-green-700'
      case 'fail': return 'bg-red-100 text-red-700'
      case 'partial': return 'bg-orange-100 text-orange-700'
      case 'error': return 'bg-red-100 text-red-700'
      default: return 'bg-gray-100 text-gray-700'
    }
  }

  const filteredTasks = tasks.filter(task =>
    task.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    (task.description && task.description.toLowerCase().includes(searchTerm.toLowerCase())) ||
    task.tags.some(tag => tag.toLowerCase().includes(searchTerm.toLowerCase()))
  )

  if (!currentProject) {
    return (
      <div className="flex items-center justify-center h-64">
        <p className="text-gray-500">请先选择一个项目</p>
      </div>
    )
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-gray-500">加载中...</div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
        {error}
        <button onClick={loadTasks} className="ml-4 underline">重试</button>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* 标题和操作栏 */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">任务管理</h1>
          <p className="text-sm text-gray-500 mt-1">
            项目: {currentProject.name} · 共 {tasks.length} 个任务
          </p>
        </div>
        <button
          onClick={() => navigate('/tasks/new')}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition"
        >
          创建任务
        </button>
      </div>

      {/* 搜索栏 */}
      <div className="flex items-center space-x-4">
        <input
          type="text"
          placeholder="搜索任务名称、描述或标签..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
        />
      </div>

      {/* 任务列表 */}
      {filteredTasks.length === 0 ? (
        <div className="text-center py-12 bg-white rounded-lg border border-dashed border-gray-300">
          <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
          </svg>
          <h3 className="mt-2 text-sm font-medium text-gray-900">暂无任务</h3>
          <p className="mt-1 text-sm text-gray-500">
            {searchTerm ? '没有找到匹配的任务' : '开始创建您的第一个测试任务'}
          </p>
          {!searchTerm && (
            <div className="mt-6">
              <button
                onClick={() => navigate('/tasks/new')}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition"
              >
                创建任务
              </button>
            </div>
          )}
        </div>
      ) : (
        <div className="grid gap-4">
          {filteredTasks.map((task) => (
            <div key={task.id} className="bg-white border border-gray-200 rounded-lg p-4 hover:shadow-md transition">
              <div className="flex justify-between items-start">
                <div className="flex-1">
                  <h3 className="text-lg font-medium text-gray-900">{task.name}</h3>
                  {task.description && (
                    <p className="text-sm text-gray-600 mt-1">{task.description}</p>
                  )}

                  {/* 标签 */}
                  {task.tags && task.tags.length > 0 && (
                    <div className="flex flex-wrap gap-2 mt-2">
                      {task.tags.map((tag, index) => (
                        <span
                          key={index}
                          className="px-2 py-1 text-xs bg-blue-50 text-blue-700 rounded"
                        >
                          {tag}
                        </span>
                      ))}
                    </div>
                  )}

                  {/* 场景数量 */}
                  <div className="flex items-center gap-4 mt-3 text-sm text-gray-500">
                    <span>场景数: {task.scenario_ids?.length || 0}</span>
                    <span>创建时间: {new Date(task.created_at).toLocaleString('zh-CN')}</span>
                  </div>
                </div>

                {/* 操作按钮 */}
                <div className="flex items-center space-x-2 ml-4">
                  <button
                    onClick={() => handleExecute(task.id)}
                    className="px-3 py-1.5 text-sm bg-green-600 text-white rounded hover:bg-green-700 transition"
                  >
                    执行
                  </button>
                  <button
                    onClick={() => toggleHistory(task.id)}
                    className="px-3 py-1.5 text-sm bg-purple-600 text-white rounded hover:bg-purple-700 transition"
                  >
                    {showHistory[task.id] ? '收起历史' : '查看历史'}
                  </button>
                  <button
                    onClick={() => navigate(`/tasks/${task.id}/scenarios`)}
                    className="px-3 py-1.5 text-sm bg-indigo-600 text-white rounded hover:bg-indigo-700 transition"
                  >
                    管理场景
                  </button>
                  <button
                    onClick={() => navigate(`/tasks/${task.id}/edit`)}
                    className="px-3 py-1.5 text-sm bg-blue-600 text-white rounded hover:bg-blue-700 transition"
                  >
                    编辑
                  </button>
                  <button
                    onClick={() => handleDelete(task.id, task.name)}
                    className="px-3 py-1.5 text-sm bg-red-600 text-white rounded hover:bg-red-700 transition"
                  >
                    删除
                  </button>
                </div>
              </div>

              {/* 执行历史 */}
              {showHistory[task.id] && (
                <div className="mt-4 pt-4 border-t border-gray-200">
                  <h4 className="text-sm font-medium text-gray-700 mb-2">执行历史</h4>
                  {!executions[task.id] ? (
                    <div className="text-sm text-gray-500">加载中...</div>
                  ) : executions[task.id].length === 0 ? (
                    <div className="text-sm text-gray-500">暂无执行记录</div>
                  ) : (
                    <div className="space-y-2">
                      {executions[task.id].map((execution) => (
                        <div
                          key={execution.id}
                          className="flex items-center justify-between bg-gray-50 rounded px-3 py-2 hover:bg-gray-100 transition cursor-pointer"
                          onClick={() => navigate(`/executions/${execution.id}`)}
                        >
                          <div className="flex items-center gap-3 text-sm">
                            <span className={getStatusColor(execution.status)}>
                              {execution.status === 'completed' ? (execution.result || '完成') : execution.status}
                            </span>
                            <span className="text-gray-500">
                              {execution.started_at ? new Date(execution.started_at).toLocaleString('zh-CN') : '-'}
                            </span>
                            <span className="text-gray-500">
                              耗时: {execution.duration ? `${Math.floor(execution.duration / 60)}分${Math.floor(execution.duration % 60)}秒` : '-'}
                            </span>
                          </div>
                          <div className="flex items-center gap-2">
                            {execution.result && (
                              <span className={`px-2 py-0.5 text-xs rounded ${getResultBadge(execution.result)}`}>
                                {execution.result.toUpperCase()}
                              </span>
                            )}
                            <span className="text-xs text-gray-500">
                              通过: {execution.passed_steps} / 失败: {execution.failed_steps}
                            </span>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
