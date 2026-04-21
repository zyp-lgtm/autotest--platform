import React, { useState, useEffect } from 'react'
import { scheduledJobsApi } from '../api/scheduledJobs'
import { projectsApi } from '../api/projects'
import { tasksApi } from '../api/tasks'
import type { ScheduledJob, SchedulerStats } from '../types/models'
import type { Project } from '../types/models'

const ScheduledJobsPage: React.FC = () => {
  const [jobs, setJobs] = useState<ScheduledJob[]>([])
  const [projects, setProjects] = useState<Project[]>([])
  const [tasks, setTasks] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [message, setMessage] = useState<{type: 'success' | 'error', text: string} | null>(null)
  const [schedulerStats, setSchedulerStats] = useState<SchedulerStats | null>(null)
  const [selectedProjectId, setSelectedProjectId] = useState<string>('')
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [newJobName, setNewJobName] = useState('')
  const [newJobCron, setNewJobCron] = useState('0 9 * * *')
  const [selectedTaskId, setSelectedTaskId] = useState('')

  // 加载项目列表
  useEffect(() => {
    loadProjects()
    loadSchedulerStats()
  }, [])

  // 加载定时任务
  useEffect(() => {
    if (selectedProjectId) {
      loadJobs()
      loadTasks()
    } else {
      setLoading(false)
    }
  }, [selectedProjectId])

  const loadProjects = async () => {
    try {
      const data = await projectsApi.getProjects()
      setProjects(data)
      // 自动选择第一个项目
      if (data.length > 0 && !selectedProjectId) {
        setSelectedProjectId(data[0].id)
      }
    } catch (error) {
      console.error('加载项目失败:', error)
      showMessage('error', '加载项目列表失败')
      setLoading(false)
    }
  }

  const loadJobs = async () => {
    if (!selectedProjectId) {
      setLoading(false)
      return
    }

    try {
      setLoading(true)
      const data = await scheduledJobsApi.getScheduledJobs(selectedProjectId)
      setJobs(data)
    } catch (error) {
      console.error('加载定时任务失败:', error)
      showMessage('error', '加载定时任务失败')
    } finally {
      setLoading(false)
    }
  }

  const loadTasks = async () => {
    if (!selectedProjectId) return

    try {
      const data = await tasksApi.getTasks(selectedProjectId)
      setTasks(data)
    } catch (error) {
      console.error('加载任务列表失败:', error)
    }
  }

  const loadSchedulerStats = async () => {
    try {
      const stats = await scheduledJobsApi.getSchedulerStats()
      setSchedulerStats(stats)
    } catch (error) {
      console.error('加载调度器统计失败:', error)
    }
  }

  const showMessage = (type: 'success' | 'error', text: string) => {
    setMessage({ type, text })
    setTimeout(() => setMessage(null), 3000)
  }

  const handleCreateJob = async () => {
    if (!newJobName.trim()) {
      showMessage('error', '请输入任务名称')
      return
    }

    if (!newJobCron.trim()) {
      showMessage('error', '请输入 Cron 表达式')
      return
    }

    if (!selectedTaskId) {
      showMessage('error', '请选择要执行的任务')
      return
    }

    if (!selectedProjectId) {
      showMessage('error', '请先选择项目')
      return
    }

    try {
      await scheduledJobsApi.createScheduledJob({
        project_id: selectedProjectId,
        name: newJobName,
        task_id: selectedTaskId,
        cron_expression: newJobCron,
        enabled: true,
        max_retries: 3
      })

      showMessage('success', '定时任务创建成功')
      await loadJobs()
      await loadSchedulerStats()
      resetForm()
      setShowCreateModal(false)
    } catch (error: any) {
      console.error('创建定时任务失败:', error)
      const errorMsg = error?.response?.data?.detail || error?.message || '创建定时任务失败'
      showMessage('error', errorMsg)
    }
  }

  const handleToggleJob = async (job: ScheduledJob) => {
    try {
      if (job.enabled) {
        await scheduledJobsApi.pauseScheduledJob(job.id)
        showMessage('success', '定时任务已暂停')
      } else {
        await scheduledJobsApi.resumeScheduledJob(job.id)
        showMessage('success', '定时任务已恢复')
      }

      await loadJobs()
      await loadSchedulerStats()
    } catch (error: any) {
      console.error('切换任务状态失败:', error)
      const errorMsg = error?.response?.data?.detail || error?.message || '操作失败'
      showMessage('error', errorMsg)
    }
  }

  const handleTriggerJob = async (jobId: string) => {
    if (!confirm('确定要手动触发这个任务吗？')) {
      return
    }

    try {
      await scheduledJobsApi.triggerScheduledJob(jobId)
      showMessage('success', '任务已触发执行')
    } catch (error: any) {
      console.error('触发任务失败:', error)
      const errorMsg = error?.response?.data?.detail || error?.message || '触发任务失败'
      showMessage('error', errorMsg)
    }
  }

  const handleDeleteJob = async (jobId: string) => {
    if (!confirm('确定要删除这个定时任务吗？')) {
      return
    }

    try {
      await scheduledJobsApi.deleteScheduledJob(jobId)
      showMessage('success', '定时任务删除成功')
      await loadJobs()
      await loadSchedulerStats()
    } catch (error: any) {
      console.error('删除定时任务失败:', error)
      const errorMsg = error?.response?.data?.detail || error?.message || '删除定时任务失败'
      showMessage('error', errorMsg)
    }
  }

  const resetForm = () => {
    setNewJobName('')
    setNewJobCron('0 9 * * *')
    setSelectedTaskId('')
  }

  const formatCronExpression = (cron: string) => {
    // 简单的 cron 格式化显示
    const parts = cron.split(' ')
    if (parts.length === 5) {
      const [minute, hour, , , weekday] = parts
      const weekdayMap: Record<string, string> = {
        '0': '周日',
        '1': '周一',
        '2': '周二',
        '3': '周三',
        '4': '周四',
        '5': '周五',
        '6': '周六',
        '*': '每天'
      }
      return `${hour}:${minute} ${weekday === '*' ? '每天' : weekdayMap[weekday] || weekday}`
    }
    return cron
  }

  return (
    <div className="container mx-auto px-4 py-8">
      {/* 消息提示 */}
      {message && (
        <div className={`mb-4 p-4 rounded-lg ${
          message.type === 'success'
            ? 'bg-green-100 text-green-700 border border-green-300'
            : 'bg-red-100 text-red-700 border border-red-300'
        }`}>
          {message.text}
        </div>
      )}

      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold">定时任务管理</h1>
        <button
          onClick={() => setShowCreateModal(true)}
          disabled={!selectedProjectId || tasks.length === 0}
          className={`px-4 py-2 rounded ${
            selectedProjectId && tasks.length > 0
              ? 'bg-blue-500 text-white hover:bg-blue-600'
              : 'bg-gray-300 text-gray-500 cursor-not-allowed'
          }`}
        >
          创建定时任务
        </button>
      </div>

      {/* 调度器状态 */}
      {schedulerStats && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6">
          <h3 className="text-lg font-semibold text-blue-900 mb-2">调度器状态</h3>
          <div className="grid grid-cols-3 gap-4 text-sm">
            <div>
              <span className="text-blue-700">状态: </span>
              <span className={schedulerStats.scheduler.running ? 'text-green-700' : 'text-red-700'}>
                {schedulerStats.scheduler.running ? '运行中' : '已停止'}
              </span>
            </div>
            <div>
              <span className="text-blue-700">总任务数: </span>
              <span className="text-blue-900">{schedulerStats.scheduler.total_jobs}</span>
            </div>
            <div>
              <span className="text-blue-700">活跃任务: </span>
              <span className="text-blue-900">{schedulerStats.scheduler.running_jobs}</span>
            </div>
          </div>
        </div>
      )}

      {/* 项目选择器 */}
      <div className="mb-6">
        <label className="block text-sm font-medium text-gray-700 mb-2">
          选择项目 <span className="text-red-500">*</span>
        </label>
        <select
          value={selectedProjectId}
          onChange={(e) => setSelectedProjectId(e.target.value)}
          className="w-full md:w-64 px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          <option value="">请选择项目</option>
          {projects.map((project) => (
            <option key={project.id} value={project.id}>
              {project.name}
            </option>
          ))}
        </select>
        {projects.length === 0 && (
          <p className="text-sm text-gray-500 mt-1">暂无可用项目</p>
        )}
      </div>

      {loading ? (
        <div className="flex items-center justify-center h-64">
          <div className="text-gray-500">加载中...</div>
        </div>
      ) : (
        <>
          {!selectedProjectId ? (
            <div className="text-center py-12">
              <p className="text-gray-500">请先选择项目以查看定时任务</p>
            </div>
          ) : jobs.length === 0 ? (
            <div className="text-center py-12">
              <p className="text-gray-500">暂无定时任务，请创建定时任务</p>
            </div>
          ) : (
            <div className="space-y-4">
              {jobs.map((job) => (
                <div key={job.id} className="border rounded-lg p-4 hover:shadow-md transition-shadow">
                  <div className="flex justify-between items-start">
                    <div className="flex-1">
                      <div className="flex items-center gap-2">
                        <h3 className="text-lg font-semibold">{job.name}</h3>
                        <span className={`px-2 py-1 text-xs rounded ${
                          job.enabled
                            ? 'bg-green-100 text-green-800'
                            : 'bg-gray-100 text-gray-800'
                        }`}>
                          {job.enabled ? '启用' : '禁用'}
                        </span>
                      </div>

                      {job.cron_expression && (
                        <p className="text-sm text-gray-600 mt-1">
                          <strong>执行时间:</strong> {formatCronExpression(job.cron_expression)}
                        </p>
                      )}

                      {job.scheduler_status?.next_run_time && (
                        <p className="text-sm text-blue-600 mt-1">
                          下次运行: {new Date(job.scheduler_status.next_run_time).toLocaleString()}
                        </p>
                      )}

                      {job.last_run_at && (
                        <p className="text-xs text-gray-500 mt-1">
                          上次运行: {new Date(job.last_run_at).toLocaleString()}
                        </p>
                      )}

                      <div className="mt-2 text-xs text-gray-500">
                        重试次数: {job.retry_count}/{job.max_retries}
                      </div>
                    </div>

                    <div className="flex space-x-2">
                      <button
                        onClick={() => handleTriggerJob(job.id)}
                        className="px-3 py-1 bg-blue-100 text-blue-700 rounded hover:bg-blue-200 text-sm"
                      >
                        立即执行
                      </button>
                      <button
                        onClick={() => handleToggleJob(job)}
                        className="px-3 py-1 bg-yellow-100 text-yellow-700 rounded hover:bg-yellow-200 text-sm"
                      >
                        {job.enabled ? '暂停' : '恢复'}
                      </button>
                      <button
                        onClick={() => handleDeleteJob(job.id)}
                        className="px-3 py-1 bg-red-100 text-red-700 rounded hover:bg-red-200 text-sm"
                      >
                        删除
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </>
      )}

      {/* 创建定时任务模态框 */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-md">
            <h2 className="text-xl font-bold mb-4">创建定时任务</h2>

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  任务名称 <span className="text-red-500">*</span>
                </label>
                <input
                  type="text"
                  value={newJobName}
                  onChange={(e) => setNewJobName(e.target.value)}
                  className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="例如: 每日回归测试"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Cron 表达式 <span className="text-red-500">*</span>
                </label>
                <input
                  type="text"
                  value={newJobCron}
                  onChange={(e) => setNewJobCron(e.target.value)}
                  className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 font-mono text-sm"
                  placeholder="0 9 * * * (每天9点)"
                />
                <p className="text-xs text-gray-500 mt-1">
                  格式: 分 时 日 月 周 (例如: 0 9 * * * 表示每天9点)
                </p>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  选择任务 <span className="text-red-500">*</span>
                </label>
                <select
                  value={selectedTaskId}
                  onChange={(e) => setSelectedTaskId(e.target.value)}
                  className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="">请选择任务</option>
                  {tasks.map((task) => (
                    <option key={task.id} value={task.id}>
                      {task.name}
                    </option>
                  ))}
                </select>
                {tasks.length === 0 && (
                  <p className="text-xs text-gray-500 mt-1">当前项目没有可用任务</p>
                )}
              </div>

              <div className="flex justify-end space-x-2">
                <button
                  onClick={() => {
                    setShowCreateModal(false)
                    resetForm()
                  }}
                  className="px-4 py-2 border rounded hover:bg-gray-50"
                >
                  取消
                </button>
                <button
                  onClick={handleCreateJob}
                  className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
                >
                  创建
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
export default ScheduledJobsPage
