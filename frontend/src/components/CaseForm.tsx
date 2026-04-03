import { useState } from 'react'
import { scenariosApi, Case, CaseCreate, CaseUpdate } from '../api/scenarios'

interface CaseFormProps {
  scenarioId: string
  case?: Case
  onSuccess?: (testCase: Case) => void
  onCancel?: () => void
}

export default function CaseForm({ scenarioId, case: testCase, onSuccess, onCancel }: CaseFormProps) {
  const [name, setName] = useState(testCase?.name || '')
  const [description, setDescription] = useState(testCase?.description || '')
  const [priority, setPriority] = useState(testCase?.priority || 'P2')
  const [tags, setTags] = useState(testCase?.tags?.join(', ') || '')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()

    if (!name.trim()) {
      setError('请输入用例名称')
      return
    }

    try {
      setLoading(true)
      setError(null)

      const data: CaseCreate | CaseUpdate = {
        name: name.trim(),
        description: description.trim() || undefined,
        priority,
        tags: tags ? tags.split(',').map(t => t.trim()).filter(t => t) : [],
        case_type: 'ui',
        data_bindings: {},
        browser_config: {}
      }

      let result: Case
      if (testCase) {
        result = await scenariosApi.updateCase(testCase.id, data)
      } else {
        result = await scenariosApi.createCase(scenarioId, data as CaseCreate)
      }

      onSuccess?.(result)
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || '操作失败')
    } finally {
      setLoading(false)
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          用例名称 <span className="text-red-500">*</span>
        </label>
        <input
          type="text"
          value={name}
          onChange={(e) => setName(e.target.value)}
          placeholder="例如：百度搜索测试"
          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
        />
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          描述
        </label>
        <textarea
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          placeholder="用例描述..."
          rows={3}
          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
        />
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          优先级
        </label>
        <select
          value={priority}
          onChange={(e) => setPriority(e.target.value)}
          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
        >
          <option value="P0">P0 - 关键</option>
          <option value="P1">P1 - 高</option>
          <option value="P2">P2 - 中</option>
          <option value="P3">P3 - 低</option>
        </select>
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          标签
        </label>
        <input
          type="text"
          value={tags}
          onChange={(e) => setTags(e.target.value)}
          placeholder="搜索, 主页, 冒烟测试 (逗号分隔)"
          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
        />
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-2 rounded text-sm">
          {error}
        </div>
      )}

      <div className="flex gap-2 pt-2">
        <button
          type="submit"
          disabled={loading}
          className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed"
        >
          {loading ? '保存中...' : testCase ? '更新' : '创建'}
        </button>
        <button
          type="button"
          onClick={onCancel}
          className="px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50"
        >
          取消
        </button>
      </div>
    </form>
  )
}
