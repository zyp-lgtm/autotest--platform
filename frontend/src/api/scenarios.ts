import apiClient from './client'

// 场景相关类型
export interface Scenario {
  id: string
  task_id: string
  project_id: string
  name: string
  description?: string
  scenario_type: string
  execution_order: number
  case_ids: string[]
  tags: string[]
  created_at: string
  updated_at?: string
}

export interface Case {
  id: string
  scenario_id: string
  project_id: string
  name: string
  description?: string
  case_type: string
  step_ids: string[]
  priority: string
  tags: string[]
  data_bindings: Record<string, any>
  browser_config: Record<string, any>
  created_at: string
  updated_at?: string
}

export interface Step {
  id: string
  case_id: string
  scenario_id: string
  task_id: string
  step_order: number
  keyword_id: string
  step_name: string
  step_type: string
  parameters: Record<string, any>
  enabled: boolean
  continue_on_failure: boolean
  screenshot_config: Record<string, any>
  created_at: string
  updated_at?: string
}

export interface ScenarioCreate {
  name: string
  description?: string
  scenario_type?: string
  tags?: string[]
}

export interface ScenarioUpdate {
  name?: string
  description?: string
  scenario_type?: string
  tags?: string[]
}

export interface CaseCreate {
  name: string
  description?: string
  case_type?: string
  priority?: string
  tags?: string[]
  data_bindings?: Record<string, any>
  browser_config?: Record<string, any>
}

export interface CaseUpdate {
  name?: string
  description?: string
  case_type?: string
  priority?: string
  tags?: string[]
  data_bindings?: Record<string, any>
  browser_config?: Record<string, any>
}

export interface StepCreate {
  step_order: number
  keyword_id: string
  step_name: string
  parameters?: Record<string, any>
  enabled?: boolean
  continue_on_failure?: boolean
  screenshot_config?: Record<string, any>
}

export interface StepUpdate {
  step_order?: number
  keyword_id?: string
  step_name?: string
  parameters?: Record<string, any>
  enabled?: boolean
  continue_on_failure?: boolean
  screenshot_config?: Record<string, any>
}

export const scenariosApi = {
  // ==================== 场景管理 ====================
  getScenarios: async (taskId: string): Promise<Scenario[]> => {
    const response = await apiClient.get<Scenario[]>(`/v1/ui/scenarios?task_id=${taskId}`)
    return response.data
  },

  getScenario: async (scenarioId: string): Promise<Scenario> => {
    const response = await apiClient.get<Scenario>(`/v1/ui/scenarios/${scenarioId}`)
    return response.data
  },

  createScenario: async (taskId: string, data: ScenarioCreate): Promise<Scenario> => {
    const response = await apiClient.post<Scenario>(`/v1/ui/scenarios/?task_id=${taskId}`, data)
    return response.data
  },

  updateScenario: async (scenarioId: string, data: ScenarioUpdate): Promise<Scenario> => {
    const response = await apiClient.put<Scenario>(`/v1/ui/scenarios/${scenarioId}`, data)
    return response.data
  },

  deleteScenario: async (scenarioId: string): Promise<void> => {
    await apiClient.delete(`/v1/ui/scenarios/${scenarioId}`)
  },

  // ==================== 用例管理 ====================
  getCases: async (scenarioId: string): Promise<Case[]> => {
    const response = await apiClient.get<Case[]>(`/v1/ui/scenarios/${scenarioId}/cases`)
    return response.data
  },

  createCase: async (scenarioId: string, data: CaseCreate): Promise<Case> => {
    const response = await apiClient.post<Case>(`/v1/ui/scenarios/${scenarioId}/cases`, data)
    return response.data
  },

  updateCase: async (caseId: string, data: CaseUpdate): Promise<Case> => {
    const response = await apiClient.put<Case>(`/v1/ui/scenarios/cases/${caseId}`, data)
    return response.data
  },

  deleteCase: async (caseId: string): Promise<void> => {
    await apiClient.delete(`/v1/ui/scenarios/cases/${caseId}`)
  },

  // ==================== 步骤管理 ====================
  getSteps: async (caseId: string): Promise<Step[]> => {
    const response = await apiClient.get<Step[]>(`/v1/ui/scenarios/cases/${caseId}/steps`)
    return response.data
  },

  createStep: async (caseId: string, data: StepCreate): Promise<Step> => {
    const response = await apiClient.post<Step>(`/v1/ui/scenarios/cases/${caseId}/steps`, data)
    return response.data
  },

  updateStep: async (stepId: string, data: StepUpdate): Promise<Step> => {
    const response = await apiClient.put<Step>(`/v1/ui/scenarios/steps/${stepId}`, data)
    return response.data
  },

  deleteStep: async (stepId: string): Promise<void> => {
    await apiClient.delete(`/v1/ui/scenarios/steps/${stepId}`)
  },
}
