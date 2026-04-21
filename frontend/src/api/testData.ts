import apiClient from './client'

// 测试数据相关类型定义
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

export interface TestDataCreate {
  project_id: string
  name: string
  description?: string
  data_type?: string
  data: any[]
  tags?: string[]
}

export interface DataBinding {
  id: string
  case_id: string
  data_id: string
  enabled: boolean
  created_at: string
  test_data?: TestData
}

export interface DataBindingCreate {
  case_id: string
  data_id: string
  enabled?: boolean
}

export const testDataApi = {
  // 获取测试数据列表
  getTestDataList: async (projectId?: string): Promise<TestData[]> => {
    const params = projectId ? `?project_id=${projectId}` : ''
    const response = await apiClient.get<TestData[]>(`/v1/test-data/${params}`)
    return response.data
  },

  // 获取测试数据详情
  getTestData: async (dataId: string): Promise<TestData> => {
    const response = await apiClient.get<TestData>(`/v1/test-data/${dataId}`)
    return response.data
  },

  // 创建测试数据
  createTestData: async (data: TestDataCreate): Promise<TestData> => {
    const response = await apiClient.post<TestData>('/v1/test-data/', data)
    return response.data
  },

  // 更新测试数据
  updateTestData: async (dataId: string, data: Partial<TestDataCreate>): Promise<TestData> => {
    const response = await apiClient.put<TestData>(`/v1/test-data/${dataId}`, data)
    return response.data
  },

  // 删除测试数据
  deleteTestData: async (dataId: string): Promise<void> => {
    await apiClient.delete(`/v1/test-data/${dataId}`)
  },

  // 绑定数据到用例
  bindDataToCase: async (binding: DataBindingCreate): Promise<DataBinding> => {
    const response = await apiClient.post<DataBinding>('/v1/test-data/bindings', binding)
    return response.data
  },

  // 获取用例的数据绑定
  getCaseBindings: async (caseId: string): Promise<DataBinding[]> => {
    const response = await apiClient.get<DataBinding[]>(`/v1/test-data/bindings/case/${caseId}`)
    return response.data
  },

  // 解除数据绑定
  unbindData: async (bindingId: string): Promise<void> => {
    await apiClient.delete(`/v1/test-data/bindings/${bindingId}`)
  },
}
