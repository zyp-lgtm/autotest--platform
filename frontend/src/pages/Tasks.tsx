import { useState, useEffect, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import { useProject } from '../contexts/ProjectContext'
import { useToast } from '../contexts/ToastContext'
import { tasksApi } from '../api/tasks'
import { keywordsApi, Keyword } from '../api/keywords'
import { scenariosApi } from '../api/scenarios'
import type { UITask } from '../types'
import type { TestExecution } from '../types'

export default function Tasks() {
  const navigate = useNavigate()
  const toast = useToast()
  const { currentProject, projects, setCurrentProject } = useProject()
  const [tasks, setTasks] = useState<UITask[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [searchTerm, setSearchTerm] = useState('')
  const [executions, setExecutions] = useState<Record<string, TestExecution[]>>({})
  const [showHistory, setShowHistory] = useState<Record<string, boolean>>({})
  const [keywords, setKeywords] = useState<Record<string, Keyword>>({})
  const [taskKeywords, setTaskKeywords] = useState<Record<string, string[]>>({})
  const [allProjectTasks, setAllProjectTasks] = useState<Record<string, UITask[]>>({})
  const [showAllTasks, setShowAllTasks] = useState(false)
  const [runningExecutions, setRunningExecutions] = useState<Record<string, string>>(() => {
    // 从 sessionStorage 恢复运行中的执行 ID（跨页面导航保持）
    try {
      const saved = sessionStorage.getItem('runningExecutions')
      return saved ? JSON.parse(saved) : {}
    } catch {
      return {}
    }
  })

  useEffect(() => {
    loadTasks()
    loadKeywords()
    loadAllProjectTasks()
  }, [currentProject])

  // 定期检查运行中的执行状态（每5秒），用 ref 避免依赖循环
  const runningRef = useRef(runningExecutions)
  runningRef.current = runningExecutions

  useEffect(() => {
    const interval = setInterval(async () => {
      const current = runningRef.current
      const taskIds = Object.keys(current)
      if (taskIds.length === 0) return
      let changed = false
      const updated = { ...current }
      for (const taskId of taskIds) {
        try {
          const execs = await tasksApi.getTaskExecutions(taskId, 1)
          setExecutions(prev => ({ ...prev, [taskId]: execs }))
          const stillRunning = execs.find((e: any) => e.status === 'running')
          if (!stillRunning) {
            delete updated[taskId]
            changed = true
          }
        } catch (_err) {}
      }
      if (changed) {
        setRunningExecutions(updated)
        persistRunning(updated)
      }
    }, 5000)
    return () => clearInterval(interval)
  }, [])

  const loadAllProjectTasks = async () => {
    // 加载所有项目的任务，用于统计显示
    const allTasks: Record<string, UITask[]> = {}
    for (const project of projects) {
      try {
        const projectTasks = await tasksApi.getTasks(project.id)
        allTasks[project.id] = projectTasks
      } catch {
        allTasks[project.id] = []
      }
    }
    setAllProjectTasks(allTasks)
  }

  const loadKeywords = async () => {
    try {
      const keywordsData = await keywordsApi.getKeywords()
      const kwMap: Record<string, Keyword> = {}
      for (const kw of keywordsData) {
        kwMap[kw.id] = kw
      }
      setKeywords(kwMap)
    } catch (err) {
      console.error('加载关键字失败:', err)
    }
  }

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

      // 加载每个任务的关键字统计
      const taskKwMap: Record<string, string[]> = {}
      for (const task of data) {
        try {
          const uniqueKeywords = new Set<string>()

          // 遍历任务的所有场景
          for (const scenarioId of task.scenario_ids) {
            try {
              const cases = await scenariosApi.getCases(scenarioId)

              // 遍历每个场景的用例
              for (const caseItem of cases) {
                try {
                  const steps = await scenariosApi.getSteps(caseItem.id)

                  // 收集步骤中使用的关键字
                  for (const step of steps) {
                    if (step.keyword_id) {
                      uniqueKeywords.add(step.keyword_id)
                    }
                  }
                } catch (err) {
                  console.error(`加载用例 ${caseItem.id} 的步骤失败:`, err)
                }
              }
            } catch (err) {
              console.error(`加载场景 ${scenarioId} 的用例失败:`, err)
            }
          }

          taskKwMap[task.id] = Array.from(uniqueKeywords)
        } catch (err) {
          console.error(`加载任务 ${task.id} 的关键字统计失败:`, err)
          taskKwMap[task.id] = []
        }
      }
      setTaskKeywords(taskKwMap)

      // 加载执行历史，检测正在运行的任务
      const newRunning: Record<string, string> = {}
      for (const task of data) {
        try {
          const execs = await tasksApi.getTaskExecutions(task.id, 3)
          setExecutions(prev => ({ ...prev, [task.id]: execs }))
          const running = execs.find((e: any) => e.status === 'running')
          if (running) {
            newRunning[task.id] = running.id
          }
        } catch (_err) {
          // 静默忽略
        }
      }
      // 用实际运行中的执行覆盖（清除已完成的）
      setRunningExecutions(newRunning)
      persistRunning(newRunning)
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
      // 从当前项目任务列表中移除
      setTasks(prev => prev.filter(t => t.id !== taskId))
      // 从所有项目任务缓存中移除，避免"显示所有项目"时仍出现
      setAllProjectTasks(prev => {
        const updated = { ...prev }
        for (const projectId of Object.keys(updated)) {
          updated[projectId] = updated[projectId].filter(t => t.id !== taskId)
        }
        return updated
      })
      // 清除已删除任务的执行历史
      setExecutions(prev => {
        const updated = { ...prev }
        delete updated[taskId]
        return updated
      })
      setShowHistory(prev => {
        const updated = { ...prev }
        delete updated[taskId]
        return updated
      })
    } catch (err: any) {
      toast.error('删除失败: ' + (err.response?.data?.detail || err.message))
    }
  }

  const persistRunning = (map: Record<string, string>) => {
    sessionStorage.setItem('runningExecutions', JSON.stringify(map))
  }

  const handleExecute = async (taskId: string) => {
    try {
      const result = await tasksApi.executeTask(taskId)
      const updated = { ...runningExecutions, [taskId]: result.id }
      setRunningExecutions(updated)
      persistRunning(updated)
      // 立即加载执行历史，让用户看到 running 状态
      await loadExecutions(taskId)
      setShowHistory(prev => ({ ...prev, [taskId]: true }))
    } catch (err: any) {
      toast.error('执行失败: ' + (err.response?.data?.detail || err.message))
    }
  }

  const handleCancelExecution = async (taskId: string, executionId: string) => {
    if (!confirm('确定要停止执行吗？')) return
    try {
      await tasksApi.cancelExecution(executionId)
      const updated = { ...runningExecutions }
      delete updated[taskId]
      setRunningExecutions(updated)
      persistRunning(updated)
      await loadExecutions(taskId)
    } catch (err: any) {
      toast.error('停止失败: ' + (err.response?.data?.detail || err.message))
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
      case 'cancelled': return 'text-orange-600'
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

  const filteredTasks = (showAllTasks
    ? Object.values(allProjectTasks).flat()
    : tasks
  ).filter(task =>
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
          <div className="flex items-center gap-4 mt-1">
            {/* 项目选择器 */}
            <div className="flex items-center gap-2">
              <span className="text-sm text-gray-500">项目:</span>
              <select
                value={currentProject?.id || ''}
                onChange={(e) => {
                  const project = projects.find(p => p.id === e.target.value)
                  if (project) setCurrentProject(project)
                }}
                className="px-3 py-1 border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                {projects.map((project) => {
                  const taskCount = allProjectTasks[project.id]?.length || 0
                  return (
                    <option key={project.id} value={project.id}>
                      {project.name} ({taskCount} 个任务)
                    </option>
                  )
                })}
              </select>
            </div>
            <span className="text-sm text-gray-500">
              当前显示: {showAllTasks ? '所有项目' : currentProject?.name} · {filteredTasks.length} 个任务
            </span>
          </div>
        </div>
        <div className="flex gap-2">
          <button
            onClick={() => setShowAllTasks(!showAllTasks)}
            className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 transition"
          >
            {showAllTasks ? '显示当前项目' : '显示所有项目'}
          </button>
          <button
            onClick={() => navigate('/tasks/new')}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition"
          >
            创建任务
          </button>
        </div>
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
          {filteredTasks.map((task) => {
            // 找到任务所属的项目
            const taskProject = showAllTasks
              ? projects.find(p => p.id === task.project_id)
              : currentProject

            return (
              <div key={task.id} className="bg-white border border-gray-200 rounded-lg p-4 hover:shadow-md transition">
                <div className="flex justify-between items-start">
                  <div className="flex-1">
                    {/* 任务名称 */}
                    <h3 className="text-lg font-medium text-gray-900">{task.name}</h3>

                    {/* 项目名称（仅在显示所有项目时） */}
                    {showAllTasks && taskProject && (
                      <div className="mt-1">
                        <span className="inline-flex items-center px-2 py-1 text-xs bg-gray-100 text-gray-700 rounded">
                          📁 {taskProject.name}
                        </span>
                      </div>
                    )}

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

                  {/* 场景数量和关键字统计 */}
                  <div className="flex items-center gap-4 mt-3 text-sm text-gray-500">
                    <span>场景数: {task.scenario_ids?.length || 0}</span>
                    {taskKeywords[task.id] && taskKeywords[task.id].length > 0 && (
                      <span>关键字数: {taskKeywords[task.id].length}</span>
                    )}
                    <span>创建时间: {new Date(task.created_at).toLocaleString('zh-CN')}</span>
                  </div>

                  {/* 关键字标签 */}
                  {taskKeywords[task.id] && taskKeywords[task.id].length > 0 && (
                    <div className="flex flex-wrap gap-2 mt-2">
                      {taskKeywords[task.id].slice(0, 5).map((keywordId) => {
                        const keyword = keywords[keywordId]
                        return keyword ? (
                          <span
                            key={keywordId}
                            className="px-2 py-1 text-xs bg-purple-50 text-purple-700 rounded border border-purple-200"
                            title={keyword.description}
                          >
                            {keyword.name}
                          </span>
                        ) : null
                      })}
                      {taskKeywords[task.id].length > 5 && (
                        <span className="px-2 py-1 text-xs bg-gray-100 text-gray-600 rounded">
                          +{taskKeywords[task.id].length - 5} 更多
                        </span>
                      )}
                    </div>
                  )}
                </div>

                {/* 操作按钮 */}
                <div className="flex items-center space-x-2 ml-4">
                  {runningExecutions[task.id] ? (
                    <button
                      onClick={() => handleCancelExecution(task.id, runningExecutions[task.id])}
                      className="px-3 py-1.5 text-sm bg-red-600 text-white rounded hover:bg-red-700 transition animate-pulse"
                    >
                      停止
                    </button>
                  ) : (
                    <button
                      onClick={() => handleExecute(task.id)}
                      className="px-3 py-1.5 text-sm bg-green-600 text-white rounded hover:bg-green-700 transition"
                    >
                      执行
                    </button>
                  )}
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
                              {execution.status === 'cancelled' ? '已取消' : execution.status === 'completed' ? (execution.result || '完成') : execution.status}
                            </span>
                            <span className="text-gray-500">
                              {execution.started_at ? new Date(execution.started_at).toLocaleString('zh-CN') : '-'}
                            </span>
                            <span className="text-gray-500">
                              耗时: {execution.duration ? `${Math.floor(execution.duration / 60)}分${Math.floor(execution.duration % 60)}秒` : '-'}
                            </span>
                          </div>
                          <div className="flex items-center gap-2" onClick={e => e.stopPropagation()}>
                            {execution.status === 'running' && (
                              <button
                                onClick={() => handleCancelExecution(task.id, execution.id)}
                                className="px-2 py-0.5 text-xs bg-red-600 text-white rounded hover:bg-red-700 transition"
                              >
                                停止
                              </button>
                            )}
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
            )
          })}
        </div>
      )}
    </div>
  )
}
