/**
 * 调试信息类型定义
 */

export interface DebugInfo {
  step_name: string
  error: string
  selector?: string
  timestamp: string
  session_id?: string
  screenshot?: string
  html_snapshot?: string
  console_logs: ConsoleMessage[]
  network_requests: NetworkRequest[]
  execution_steps: ExecutionStep[]
  report_path?: string
}

export interface ConsoleMessage {
  type: 'log' | 'warning' | 'error' | 'info' | 'debug'
  text: string
  timestamp: string
  location?: string
}

export interface NetworkRequest {
  method: string
  url: string
  resource_type: string
  timestamp: string
  headers?: Record<string, string>
  status?: number
  status_text?: string
  response_headers?: Record<string, string>
  timing?: any
  response_size?: number
}

export interface ExecutionStep {
  action: 'start' | 'complete'
  step_name: string
  keyword?: string
  parameters?: Record<string, any>
  result?: Record<string, any>
  duration_ms?: number
  timestamp: string
}

export interface StepExecution {
  id: string
  step_name: string
  keyword_name: string
  status: string
  result: 'pass' | 'fail'
  error_message?: string
  screenshot_path?: string
  debug_info?: DebugInfo
  logs?: LogEntry[]
}

export interface LogEntry {
  timestamp: string
  level: 'info' | 'debug' | 'error'
  message: string
}
