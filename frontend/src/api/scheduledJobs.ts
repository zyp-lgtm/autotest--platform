import apiClient from './client'

// 定时任务相关类型定义
export interface ScheduledJob {
  id: string
  project_id: string
  name: string
  task_id: string
  cron_expression?: string
  enabled: boolean
  next_run_at?: string
  last_run_at?: string
  retry_count: number
  max_retries: number
  created_at: string
  updated_at?: string
  scheduler_status?: {
    id: string
    name: string
    next_run_time?: string
    running: boolean
  }
}

export interface ScheduledJobCreate {
  project_id: string
  name: string
  task_id: string
  cron_expression?: string
  enabled?: boolean
  max_retries?: number
}

export interface ScheduledJobUpdate {
  name?: string
  cron_expression?: string
  enabled?: boolean
  max_retries?: number
}

export interface SchedulerStats {
  scheduler: {
    running: boolean
    total_jobs: number
    running_jobs: number
  }
  jobs: Array<{
    id: string
    name: string
    next_run_time?: string
  }>
}

export const scheduledJobsApi = {
  // 获取定时任务列表
  getScheduledJobs: async (projectId?: string): Promise<ScheduledJob[]> => {
    const params = projectId ? `?project_id=${projectId}` : ''
    const response = await apiClient.get<ScheduledJob[]>(`/v1/scheduled-jobs/${params}`)
    return response.data
  },

  // 获取定时任务详情
  getScheduledJob: async (jobId: string): Promise<ScheduledJob> => {
    const response = await apiClient.get<ScheduledJob>(`/v1/scheduled-jobs/${jobId}`)
    return response.data
  },

  // 创建定时任务
  createScheduledJob: async (data: ScheduledJobCreate): Promise<ScheduledJob> => {
    const response = await apiClient.post<ScheduledJob>('/v1/scheduled-jobs/', data)
    return response.data
  },

  // 更新定时任务
  updateScheduledJob: async (jobId: string, data: ScheduledJobUpdate): Promise<ScheduledJob> => {
    const response = await apiClient.put<ScheduledJob>(`/v1/scheduled-jobs/${jobId}`, data)
    return response.data
  },

  // 删除定时任务
  deleteScheduledJob: async (jobId: string): Promise<void> => {
    await apiClient.delete(`/v1/scheduled-jobs/${jobId}`)
  },

  // 暂停定时任务
  pauseScheduledJob: async (jobId: string): Promise<{ message: string }> => {
    const response = await apiClient.post<{ message: string }>(`/v1/scheduled-jobs/${jobId}/pause`)
    return response.data
  },

  // 恢复定时任务
  resumeScheduledJob: async (jobId: string): Promise<{ message: string }> => {
    const response = await apiClient.post<{ message: string }>(`/v1/scheduled-jobs/${jobId}/resume`)
    return response.data
  },

  // 手动触发定时任务
  triggerScheduledJob: async (jobId: string): Promise<{ message: string }> => {
    const response = await apiClient.post<{ message: string }>(`/v1/scheduled-jobs/trigger/${jobId}`)
    return response.data
  },

  // 获取调度器统计信息
  getSchedulerStats: async (): Promise<SchedulerStats> => {
    const response = await apiClient.get<SchedulerStats>('/v1/scheduled-jobs/stats/scheduler')
    return response.data
  },
}
