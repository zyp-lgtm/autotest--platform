// 用户类型
export interface User {
  id: string
  username: string
  email: string
  full_name?: string
  is_active: boolean
  role: string
  created_at: string
}

// 认证相关类型
export interface LoginRequest {
  username: string
  password: string
}

export interface RegisterRequest {
  username: string
  email: string
  password: string
  full_name?: string
}

export interface AuthResponse {
  access_token: string
  token_type: string
}

// 项目类型
export interface Project {
  id: string
  name: string
  description?: string
  created_at: string
}

// 测试数据类型
export interface TestData {
  id: string
  project_id: string
  data_name: string
  data_value: string
  data_type: 'string' | 'number' | 'boolean' | 'json'
  description?: string
  tags: string[]
  is_sensitive: boolean
  created_at: string
}

// UI 任务类型
export interface UITask {
  id: string
  project_id: string
  name: string
  description?: string
  tags: string[]
  scenario_ids: string[]
  created_at: string
}

// 场景类型
export interface UIScenario {
  id: string
  name: string
  description?: string
  scenario_type: string
  case_ids: string[]
}

// 统计数据类型
export interface DashboardStats {
  totalTasks: number
  totalScenarios: number
  totalCases: number
}

// API 响应类型
export interface ApiResponse<T> {
  data?: T
  detail?: string
  message?: string
}

// 执行记录类型
export interface StepExecution {
  id: string
  step_id: string
  step_name: string
  step_order: number
  keyword_name: string
  category: string
  status: string
  result?: string
  duration?: number
  error_message?: string
  screenshot_path?: string
  logs: Array<{ timestamp: string; level: string; message: string }>
  output?: any
}

export interface CaseExecution {
  id: string
  case_id: string
  status: string
  result?: string
  duration?: number
  total_steps: number
  passed_steps: number
  failed_steps: number
  error_message?: string
  step_executions: StepExecution[]
}

export interface ScenarioExecution {
  id: string
  scenario_id: string
  status: string
  result?: string
  duration?: number
  execution_order: number
  total_cases: number
  total_steps: number
  passed_steps: number
  failed_steps: number
  case_executions: CaseExecution[]
}

export interface TestExecution {
  id: string
  task_id: string
  project_id: string
  user_id?: string
  status: string
  result?: string
  started_at?: string
  completed_at?: string
  duration?: number

  // 统计
  total_scenarios: number
  total_cases: number
  total_steps: number
  passed_steps: number
  failed_steps: number
  skipped_steps: number

  error_message?: string
  scenario_executions: ScenarioExecution[]
  created_at: string
}
