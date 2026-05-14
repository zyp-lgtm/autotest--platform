import apiClient from './client'

export interface Keyword {
  id: string
  name: string
  category: string
  description: string
  parameter_schema: Record<string, any>
  enabled: boolean
  examples: any[]
}

export const keywordsApi = {
  getKeywords: async (category?: string): Promise<Keyword[]> => {
    const url = category
      ? `/v1/ui/keywords?category=${category}&enabled_only=true`
      : `/v1/ui/keywords?enabled_only=true`
    const response = await apiClient.get<Keyword[]>(url)
    return response.data
  },

  getCategories: async (): Promise<string[]> => {
    const response = await apiClient.get<string[]>(`/v1/ui/keywords/categories`)
    return response.data
  },

  getKeyword: async (keywordId: string): Promise<Keyword> => {
    const response = await apiClient.get<Keyword>(`/v1/ui/keywords/${keywordId}`)
    return response.data
  },

  createKeyword: async (data: Record<string, any>): Promise<Keyword> => {
    const response = await apiClient.post<Keyword>(`/v1/ui/keywords`, data)
    return response.data
  },

  updateKeyword: async (keywordId: string, data: Record<string, any>): Promise<Keyword> => {
    const response = await apiClient.put<Keyword>(`/v1/ui/keywords/${keywordId}`, data)
    return response.data
  },

  deleteKeyword: async (keywordId: string): Promise<void> => {
    await apiClient.delete(`/v1/ui/keywords/${keywordId}`)
  },
}
