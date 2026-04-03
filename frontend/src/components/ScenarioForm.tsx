import { useState } from 'react'
import { scenariosApi, Scenario, ScenarioCreate, ScenarioUpdate } from '../api/scenarios'

interface ScenarioFormProps {
  taskId: string
  scenario?: Scenario
  onSuccess?: (scenario: Scenario) => void
  onCancel?: () => void
}

export default function ScenarioForm({ taskId, scenario, onSuccess, onCancel }: ScenarioFormProps) {
  const [name, setName] = useState(scenario?.name || '')
  const [description, setDescription] = useState(scenario?.description || '')
  const [scenarioType, setScenarioType] = useState(scenario?.scenario_type || 'ui')
  const [tags, setTags] = useState(scenario?.tags?.join(', ') || '')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()

    if (!name.trim()) {
      setError('请输入场景名称')
      return
    }

    try {
      setLoading(true)
      setError(null)

      const data: ScenarioCreate | ScenarioUpdate = {
        name: name.trim(),
        description: description.trim() || undefined,
        scenario_type: scenarioType,
        tags: tags ? tags.split(',').map(t => t.trim()).filter(t => t) : []
      }

      let result: Scenario
      if (scenario) {
        result = await scenariosApi.updateScenario(scenario.id, data)
      } else {
        result = await scenariosApi.createScenario(taskId, data as ScenarioCreate)
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
          场景名称 <span className="text-red-500">*</span>
        </label>
        <input
          type="text"
          value={name}
          onChange={(e) => setName(e.target.value)}
          placeholder="例如：用户登录场景"
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
          placeholder="场景描述..."
          rows={3}
          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
        />
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          场景类型
        </label>
        <select
          value={scenarioType}
          onChange={(e) => setScenarioType(e.target.value)}
          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
        >
          <option value="ui">UI测试</option>
          <option value="api">API测试</option>
          <option value="data">数据测试</option>
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
          placeholder="登录, 认证, 关键路径 (逗号分隔)"
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
          {loading ? '保存中...' : scenario ? '更新' : '创建'}
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
