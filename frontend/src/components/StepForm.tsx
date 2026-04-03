import { useState, useEffect } from 'react'
import { scenariosApi, Step, StepCreate, StepUpdate } from '../api/scenarios'
import { keywordsApi, Keyword } from '../api/keywords'
import KeywordSelector from './KeywordSelector'

interface StepFormProps {
  caseId: string
  step?: Step
  onSuccess?: (step: Step) => void
  onCancel?: () => void
}

export default function StepForm({ caseId, step, onSuccess, onCancel }: StepFormProps) {
  const [stepName, setStepName] = useState(step?.step_name || '')
  const [keywordId, setKeywordId] = useState(step?.keyword_id || '')
  const [parameters, setParameters] = useState<string>(
    step?.parameters ? JSON.stringify(step.parameters, null, 2) : '{}'
  )
  const [enabled, setEnabled] = useState(step?.enabled ?? true)
  const [continueOnFailure, setContinueOnFailure] = useState(step?.continue_on_failure || false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [selectedKeyword, setSelectedKeyword] = useState<Keyword | null>(null)

  // 当选择关键字时，加载关键字详情
  useEffect(() => {
    if (keywordId) {
      loadKeywordDetails(keywordId)
    }
  }, [keywordId])

  const loadKeywordDetails = async (kwId: string) => {
    try {
      const kw = await keywordsApi.getKeyword(kwId)
      setSelectedKeyword(kw)
      // 如果参数为空且关键字有参数schema，设置一个默认模板
      if (parameters === '{}' && kw.parameter_schema && Object.keys(kw.parameter_schema).length > 0) {
        const defaultParams: Record<string, any> = {}
        for (const [key, schema] of Object.entries(kw.parameter_schema)) {
          const def = schema as any
          if (def.default !== undefined) {
            defaultParams[key] = def.default
          } else if (def.type === 'string') {
            defaultParams[key] = ''
          } else if (def.type === 'object') {
            defaultParams[key] = {}
          } else if (def.type === 'integer' || def.type === 'number') {
            defaultParams[key] = def.default || 0
          } else if (def.type === 'boolean') {
            defaultParams[key] = def.default || false
          }
        }
        setParameters(JSON.stringify(defaultParams, null, 2))
      }
    } catch (err) {
      console.error('加载关键字详情失败:', err)
    }
  }

  const fillExample = () => {
    if (selectedKeyword?.examples && selectedKeyword.examples.length > 0) {
      setParameters(JSON.stringify(selectedKeyword.examples[0], null, 2))
    }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()

    if (!stepName.trim()) {
      setError('请输入步骤名称')
      return
    }

    if (!keywordId) {
      setError('请选择关键字')
      return
    }

    // 验证JSON格式
    let parsedParams: Record<string, any>
    try {
      parsedParams = JSON.parse(parameters)
    } catch {
      setError('参数格式错误，请输入有效的JSON')
      return
    }

    try {
      setLoading(true)
      setError(null)

      const data: StepCreate | StepUpdate = {
        step_name: stepName,
        keyword_id: keywordId,
        parameters: parsedParams,
        enabled,
        continue_on_failure: continueOnFailure,
        step_order: step?.step_order || 0
      }

      let result: Step
      if (step) {
        result = await scenariosApi.updateStep(step.id, data)
      } else {
        result = await scenariosApi.createStep(caseId, data as StepCreate)
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
          步骤名称 <span className="text-red-500">*</span>
        </label>
        <input
          type="text"
          value={stepName}
          onChange={(e) => setStepName(e.target.value)}
          placeholder="例如：打开百度首页"
          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
        />
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          选择关键字 <span className="text-red-500">*</span>
        </label>
        <KeywordSelector
          value={keywordId}
          onChange={setKeywordId}
        />
      </div>

      <div>
        <div className="flex justify-between items-center mb-1">
          <label className="block text-sm font-medium text-gray-700">
            参数配置 (JSON格式)
          </label>
          {selectedKeyword?.examples && selectedKeyword.examples.length > 0 && (
            <button
              type="button"
              onClick={fillExample}
              className="text-xs text-blue-600 hover:text-blue-800"
            >
              填充示例
            </button>
          )}
        </div>

        {/* 参数说明 */}
        {selectedKeyword?.parameter_schema && Object.keys(selectedKeyword.parameter_schema).length > 0 && (
          <div className="mb-2 p-2 bg-blue-50 rounded text-xs">
            <div className="font-medium text-blue-900 mb-1">可用参数:</div>
            <div className="space-y-1">
              {Object.entries(selectedKeyword.parameter_schema).map(([key, schema]: any) => (
                <div key={key} className="flex items-center gap-2">
                  <code className="bg-blue-100 px-1 rounded">{key}</code>
                  <span className="text-gray-600">
                    ({schema.type || 'any'})
                    {schema.required && <span className="text-red-500"> *必填</span>}
                  </span>
                  {schema.description && (
                    <span className="text-gray-500">- {schema.description}</span>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        <textarea
          value={parameters}
          onChange={(e) => setParameters(e.target.value)}
          placeholder='{"url": "https://www.baidu.com"}'
          rows={6}
          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 font-mono text-sm"
        />
        <p className="text-xs text-gray-500 mt-1">
          输入JSON格式的参数，例如: {"{"}selector": "#input", "text": "hello"{"}"}
        </p>
      </div>

      <div className="flex items-center gap-4">
        <label className="flex items-center gap-2">
          <input
            type="checkbox"
            checked={enabled}
            onChange={(e) => setEnabled(e.target.checked)}
            className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
          />
          <span className="text-sm text-gray-700">启用此步骤</span>
        </label>

        <label className="flex items-center gap-2">
          <input
            type="checkbox"
            checked={continueOnFailure}
            onChange={(e) => setContinueOnFailure(e.target.checked)}
            className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
          />
          <span className="text-sm text-gray-700">失败后继续</span>
        </label>
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
          {loading ? '保存中...' : step ? '更新' : '创建'}
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
