import apiClient from './client'

// 录制相关类型
export interface CapturedAction {
  id: string
  timestamp: number
  action_type: string
  selector: string
  selector_strategy?: string
  value?: string
  element_tag?: string
  element_text?: string
  element_attributes?: Record<string, string>
  page_url?: string
  page_title?: string
}

export interface DataPattern {
  id: string
  field_name: string
  pattern_type: string
  values: any[]
  confidence: number
  selected: boolean
  suggested_variations?: any[]
}

export interface GeneratedStep {
  id: string
  step_name: string
  keyword_id: string
  parameters: Record<string, any>
  enabled: boolean
  continue_on_failure: boolean
  step_order: number
}

export interface GeneratedCase {
  id: string
  name: string
  description: string
  steps: GeneratedStep[]
}

export interface GeneratedScenario {
  name: string
  description: string
  scenario_type: string
  cases: GeneratedCase[]
  metadata?: {
    created_by: string
    actions_count: number
    data_patterns_count: number
  }
}

export interface RecordingStartRequest {
  project_id: string
  scenario_name: string
}

export interface RecordingStartResponse {
  session_id: string
  status: string
  message: string
  instructions: {
    browser_launched: string
    start_operations: string
    monitoring: string
    stop_recording: string
  }
}

export interface RecordingStopRequest {
  session_id: string
}

export interface RecordingStopResponse {
  session_id: string
  actions_count: number
  actions: CapturedAction[]
  scenario_name: string
  project_id: string
  status: string
}

export interface DataExtractionRequest {
  actions: CapturedAction[]
}

export interface DataExtractionResponse {
  patterns: DataPattern[]
  patterns_count: number
}

export interface ScenarioGenerationRequest {
  project_id: string
  scenario_name: string
  actions: CapturedAction[]
  data_patterns: DataPattern[]
}

export interface ScenarioGenerationResponse {
  scenario: GeneratedScenario
  test_data?: any
}

export interface RecordingSession {
  id: string
  project_id: string
  scenario_name: string
  status: string
  actions_count: number
  started_at?: string
}

export interface SessionsListResponse {
  sessions: RecordingSession[]
  sessions_count: number
}

export const recordingApi = {
  // 启动录制会话
  startRecording: async (request: RecordingStartRequest): Promise<RecordingStartResponse> => {
    const response = await apiClient.post<RecordingStartResponse>('/v1/recording/start', request)
    return response.data
  },

  // 停止录制会话
  stopRecording: async (request: RecordingStopRequest): Promise<RecordingStopResponse> => {
    const response = await apiClient.post<RecordingStopResponse>('/v1/recording/stop', request)
    return response.data
  },

  // 获取捕获的操作（用于轮询）
  getCapturedActions: async (sessionId: string): Promise<CapturedAction[]> => {
    const response = await apiClient.get<{ actions: CapturedAction[] }>(`/v1/recording/actions/${sessionId}`)
    return response.data.actions
  },

  // 智能提取测试数据
  extractTestData: async (request: DataExtractionRequest): Promise<DataExtractionResponse> => {
    const response = await apiClient.post<DataExtractionResponse>('/v1/recording/extract-data', request)
    return response.data
  },

  // 生成测试场景
  generateScenario: async (request: ScenarioGenerationRequest): Promise<ScenarioGenerationResponse> => {
    const response = await apiClient.post<ScenarioGenerationResponse>('/v1/recording/generate-scenario', request)
    return response.data
  },

  // 列出所有活动的录制会话
  listSessions: async (): Promise<SessionsListResponse> => {
    const response = await apiClient.get<SessionsListResponse>('/v1/recording/sessions')
    return response.data
  },

  // 关闭录制会话
  closeSession: async (sessionId: string): Promise<{ message: string; session_id: string }> => {
    const response = await apiClient.post<{ message: string; session_id: string }>(`/v1/recording/sessions/${sessionId}/close`)
    return response.data
  },

  // 录制服务健康检查
  healthCheck: async (): Promise<{ status: string; active_sessions: number; available: boolean }> => {
    const response = await apiClient.get<{ status: string; active_sessions: number; available: boolean }>('/v1/recording/health')
    return response.data
  }
}
