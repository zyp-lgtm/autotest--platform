// 模型类型定义 - 补充现有类型

// 项目模型
export interface Project {
  id: string
  name: string
  description: string
  owner_id: string
  created_at: string
  updated_at?: string
}

// 测试数据模型
export interface TestData {
  id: string
  project_id: string
  name: string
  description?: string
  data_type: string
  data: any[]
  tags: string[]
  created_by?: string
  created_at: string
  updated_at?: string
}

// 环境配置模型
export interface Environment {
  id: string
  project_id: string
  name: string
  base_url?: string
  variables: Record<string, any>
  is_default: boolean
  created_at: string
  updated_at?: string
}

// 定时任务模型
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

// 批量操作结果
export interface BatchOperationResult {
  message: string
  total_requested: number
  enabled_count?: number
  disabled_count?: number
  deleted_count?: number
  not_found_count?: number
  skipped_count?: number
  exported_count?: number
  success: boolean
}

// 批量操作预览
export interface BatchPreviewResult {
  total_items: number
  operation: string
  item_type: string
  items: Array<{
    id: string
    name: string
    enabled?: boolean
    warning?: string
  }>
  warnings: string[]
  errors?: string[]
}

// 数据绑定模型
export interface DataBinding {
  id: string
  case_id: string
  test_data_id: string
  binding_type: string
  created_at: string
}

// 调度器统计
export interface SchedulerStats {
  scheduler: {
    running: boolean
    total_jobs: number
    running_jobs: number
  }
}
