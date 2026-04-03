import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { scenariosApi, Scenario, Case, Step } from '../api/scenarios'
import { keywordsApi, Keyword } from '../api/keywords'

export default function Scenarios() {
  const { taskId } = useParams<{ taskId: string }>()
  const navigate = useNavigate()
  const [scenarios, setScenarios] = useState<Scenario[]>([])
  const [cases, setCases] = useState<Record<string, Case[]>>({})
  const [steps, setSteps] = useState<Record<string, Step[]>>({})
  const [keywords, setKeywords] = useState<Record<string, Keyword>>({})
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [expandedScenarios, setExpandedScenarios] = useState<Record<string, boolean>>({})
  const [expandedCases, setExpandedCases] = useState<Record<string, boolean>>({})

  useEffect(() => {
    loadData()
  }, [taskId])

  const loadData = async () => {
    if (!taskId) return

    try {
      setLoading(true)
      setError(null)

      // 加载场景
      const scenariosData = await scenariosApi.getScenarios(taskId)
      setScenarios(scenariosData)

      // 加载所有用例
      const casesData: Record<string, Case[]> = {}
      for (const scenario of scenariosData) {
        if (scenario.case_ids.length > 0) {
          casesData[scenario.id] = await scenariosApi.getCases(scenario.id)
        }
      }
      setCases(casesData)

      // 加载所有步骤
      const stepsData: Record<string, Step[]> = {}
      for (const [, caseList] of Object.entries(casesData)) {
        for (const caseItem of caseList) {
          if (caseItem.step_ids.length > 0) {
            stepsData[caseItem.id] = await scenariosApi.getSteps(caseItem.id)
          }
        }
      }
      setSteps(stepsData)

      // 加载关键字映射
      const keywordsData = await keywordsApi.getKeywords()
      const kwMap: Record<string, Keyword> = {}
      for (const kw of keywordsData) {
        kwMap[kw.id] = kw
      }
      setKeywords(kwMap)
    } catch (err: any) {
      setError(err.response?.data?.detail || '加载失败')
    } finally {
      setLoading(false)
    }
  }

  const toggleScenario = (scenarioId: string) => {
    setExpandedScenarios(prev => ({ ...prev, [scenarioId]: !prev[scenarioId] }))
  }

  const toggleCase = (caseId: string) => {
    setExpandedCases(prev => ({ ...prev, [caseId]: !prev[caseId] }))
  }

  const handleDeleteScenario = async (scenarioId: string, scenarioName: string) => {
    if (!confirm(`确定要删除场景 "${scenarioName}" 吗？`)) {
      return
    }

    try {
      await scenariosApi.deleteScenario(scenarioId)
      setScenarios(scenarios.filter(s => s.id !== scenarioId))
    } catch (err: any) {
      alert('删除失败: ' + (err.response?.data?.detail || err.message))
    }
  }

  const handleDeleteCase = async (caseId: string, caseName: string, scenarioId: string) => {
    if (!confirm(`确定要删除用例 "${caseName}" 吗？`)) {
      return
    }

    try {
      await scenariosApi.deleteCase(caseId)
      setCases(prev => ({
        ...prev,
        [scenarioId]: prev[scenarioId].filter(c => c.id !== caseId)
      }))
    } catch (err: any) {
      alert('删除失败: ' + (err.response?.data?.detail || err.message))
    }
  }

  const handleDeleteStep = async (stepId: string, stepName: string, caseId: string) => {
    if (!confirm(`确定要删除步骤 "${stepName}" 吗？`)) {
      return
    }

    try {
      await scenariosApi.deleteStep(stepId)
      // 更新步骤列表
      for (const [cId, stepList] of Object.entries(steps)) {
        if (cId === caseId) {
          setSteps(prev => ({
            ...prev,
            [caseId]: stepList.filter(s => s.id !== stepId)
          }))
          break
        }
      }
    } catch (err: any) {
      alert('删除失败: ' + (err.response?.data?.detail || err.message))
    }
  }

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'P0': return 'text-red-600 bg-red-50'
      case 'P1': return 'text-orange-600 bg-orange-50'
      case 'P2': return 'text-yellow-600 bg-yellow-50'
      case 'P3': return 'text-green-600 bg-green-50'
      default: return 'text-gray-600 bg-gray-50'
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-gray-500">加载中...</div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
        {error}
        <button onClick={loadData} className="ml-4 underline">重试</button>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* 标题栏 */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">场景管理</h1>
          <p className="text-sm text-gray-500 mt-1">共 {scenarios.length} 个场景</p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={() => navigate(-1)}
            className="px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50"
          >
            返回
          </button>
          {/* <button
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
          >
            创建场景
          </button> */}
        </div>
      </div>

      {/* 场景列表 */}
      {scenarios.length === 0 ? (
        <div className="text-center py-12 bg-white rounded-lg border border-dashed border-gray-300">
          <p className="text-gray-500">暂无场景</p>
        </div>
      ) : (
        <div className="space-y-4">
          {scenarios.map((scenario) => (
            <div key={scenario.id} className="bg-white border border-gray-200 rounded-lg overflow-hidden">
              {/* 场景头部 */}
              <div
                className="flex items-center justify-between p-4 bg-gray-50 cursor-pointer hover:bg-gray-100"
                onClick={() => toggleScenario(scenario.id)}
              >
                <div className="flex items-center gap-3">
                  <span className="text-gray-400">
                    {expandedScenarios[scenario.id] ? '▼' : '▶'}
                  </span>
                  <div>
                    <div className="font-medium">
                      场景 #{scenario.execution_order + 1}: {scenario.name}
                    </div>
                    <div className="text-sm text-gray-500">
                      用例数: {scenario.case_ids?.length || 0}
                      {scenario.description && ` · ${scenario.description}`}
                    </div>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <button
                    onClick={(e) => {
                      e.stopPropagation()
                      handleDeleteScenario(scenario.id, scenario.name)
                    }}
                    className="px-3 py-1 text-sm bg-red-600 text-white rounded hover:bg-red-700"
                  >
                    删除
                  </button>
                </div>
              </div>

              {/* 用例列表 */}
              {expandedScenarios[scenario.id] && (
                <div className="p-4 border-t border-gray-200 space-y-3">
                  {!cases[scenario.id] || cases[scenario.id].length === 0 ? (
                    <div className="text-center text-gray-500 py-4">暂无用例</div>
                  ) : (
                    cases[scenario.id].map((caseItem) => (
                      <div key={caseItem.id} className="border border-gray-200 rounded-lg overflow-hidden">
                        {/* 用例头部 */}
                        <div
                          className="flex items-center justify-between p-3 bg-gray-50 cursor-pointer hover:bg-gray-100"
                          onClick={() => toggleCase(caseItem.id)}
                        >
                          <div className="flex items-center gap-3">
                            <span className="text-gray-400 text-sm">
                              {expandedCases[caseItem.id] ? '▼' : '▶'}
                            </span>
                            <div>
                              <div className="font-medium text-sm">{caseItem.name}</div>
                              <div className="text-xs text-gray-500">
                                步骤数: {caseItem.step_ids?.length || 0}
                                {caseItem.description && ` · ${caseItem.description}`}
                              </div>
                            </div>
                          </div>
                          <div className="flex items-center gap-2">
                            <span className={`px-2 py-0.5 text-xs rounded ${getPriorityColor(caseItem.priority)}`}>
                              {caseItem.priority}
                            </span>
                            <button
                              onClick={(e) => {
                                e.stopPropagation()
                                handleDeleteCase(caseItem.id, caseItem.name, scenario.id)
                              }}
                              className="px-2 py-1 text-xs bg-red-600 text-white rounded hover:bg-red-700"
                            >
                              删除
                            </button>
                          </div>
                        </div>

                        {/* 步骤列表 */}
                        {expandedCases[caseItem.id] && (
                          <div className="p-3 bg-white space-y-2">
                            {!steps[caseItem.id] || steps[caseItem.id].length === 0 ? (
                              <div className="text-center text-gray-500 py-2 text-sm">暂无步骤</div>
                            ) : (
                              steps[caseItem.id].map((step) => {
                                const keyword = keywords[step.keyword_id]
                                return (
                                  <div
                                    key={step.id}
                                    className={`flex items-center justify-between p-2 rounded text-sm ${
                                      step.enabled ? 'bg-white border' : 'bg-gray-100 border border-gray-200 opacity-60'
                                    }`}
                                  >
                                    <div className="flex items-center gap-2">
                                      <span className="text-gray-400">{step.step_order + 1}.</span>
                                      <span className="font-medium">{step.step_name}</span>
                                      <span className="text-xs text-gray-500">({keyword?.name || step.keyword_id})</span>
                                      {!step.enabled && (
                                        <span className="text-xs text-gray-400">[禁用]</span>
                                      )}
                                    </div>
                                    <button
                                      onClick={() => handleDeleteStep(step.id, step.step_name, caseItem.id)}
                                      className="px-2 py-1 text-xs bg-red-600 text-white rounded hover:bg-red-700"
                                    >
                                      删除
                                    </button>
                                  </div>
                                )
                              })
                            )}
                          </div>
                        )}
                      </div>
                    ))
                  )}
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
