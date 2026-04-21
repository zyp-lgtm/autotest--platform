import apiClient from './client'

// 批量操作相关类型定义
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

export const batchApi = {
  // 批量启用场景
  batchEnableScenarios: async (scenarioIds: string[]): Promise<BatchOperationResult> => {
    const response = await apiClient.post<BatchOperationResult>('/v1/batch/scenarios/enable', scenarioIds)
    return response.data
  },

  // 批量禁用场景
  batchDisableScenarios: async (scenarioIds: string[]): Promise<BatchOperationResult> => {
    const response = await apiClient.post<BatchOperationResult>('/v1/batch/scenarios/disable', scenarioIds)
    return response.data
  },

  // 批量删除场景
  batchDeleteScenarios: async (scenarioIds: string[]): Promise<BatchOperationResult> => {
    const response = await apiClient.post<BatchOperationResult>('/v1/batch/scenarios/delete', scenarioIds)
    return response.data
  },

  // 批量导出场景
  batchExportScenarios: async (scenarioIds: string[]): Promise<BatchOperationResult & { data: any[] }> => {
    const response = await apiClient.post<BatchOperationResult & { data: any[] }>('/v1/batch/scenarios/export', scenarioIds)
    return response.data
  },

  // 批量删除任务
  batchDeleteTasks: async (taskIds: string[]): Promise<BatchOperationResult> => {
    const response = await apiClient.post<BatchOperationResult>('/v1/batch/tasks/delete', taskIds)
    return response.data
  },

  // 预览批量操作
  previewBatchOperation: async (
    operationType: string,
    itemIds: string[],
    itemType: string
  ): Promise<BatchPreviewResult> => {
    const params = new URLSearchParams({
      operation_type: operationType,
      item_type: itemType
    })

    const response = await apiClient.get<BatchPreviewResult>(`/v1/batch/operations/preview?${params.toString()}&item_ids=${itemIds.join(',')}`)
    return response.data
  },
}
