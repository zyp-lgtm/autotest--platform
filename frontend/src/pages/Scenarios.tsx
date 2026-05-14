import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { scenariosApi, Scenario, Case, Step } from '../api/scenarios'
import { keywordsApi, Keyword } from '../api/keywords'
import { tasksApi, UITask } from '../api/tasks'
import ScenarioForm from '../components/ScenarioForm'
import CaseForm from '../components/CaseForm'
import StepForm from '../components/StepForm'
import RecordingWizard from '../components/RecordingWizard'

type ModalType = 'scenario' | 'case' | 'step' | 'recording' | null

export default function Scenarios() {
  const { taskId } = useParams<{ taskId: string }>()
  const navigate = useNavigate()
  const [scenarios, setScenarios] = useState<Scenario[]>([])
  const [cases, setCases] = useState<Record<string, Case[]>>({})
  const [steps, setSteps] = useState<Record<string, Step[]>>({})
  const [keywords, setKeywords] = useState<Record<string, Keyword>>({})
  const [task, setTask] = useState<UITask | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [expandedScenarios, setExpandedScenarios] = useState<Record<string, boolean>>({})
  const [expandedCases, setExpandedCases] = useState<Record<string, boolean>>({})

  // 步骤多选状态
  const [selectedSteps, setSelectedSteps] = useState<Set<string>>(new Set())
  const [batchDialogOpen, setBatchDialogOpen] = useState(false)
  const [batchCaseId, setBatchCaseId] = useState<string | null>(null)

  // Modal state
  const [modalType, setModalType] = useState<ModalType>(null)
  const [modalScenarioId, setModalScenarioId] = useState<string | null>(null)
  const [modalCaseId, setModalCaseId] = useState<string | null>(null)
  const [editingScenario, setEditingScenario] = useState<Scenario | undefined>(undefined)
  const [editingCase, setEditingCase] = useState<Case | undefined>(undefined)
  const [editingStep, setEditingStep] = useState<Step | undefined>(undefined)

  useEffect(() => {
    loadData()
  }, [taskId])

  const loadData = async () => {
    if (!taskId) return

    try {
      setLoading(true)
      setError(null)

      // 加载任务信息以获取 project_id
      const taskData = await tasksApi.getTask(taskId)
      setTask(taskData)

      const scenariosData = await scenariosApi.getScenarios(taskId)
      setScenarios(scenariosData)

      const casesData: Record<string, Case[]> = {}
      for (const scenario of scenariosData) {
        // 🔥 修复：无论 case_ids 是否为空，都尝试加载用例
        // 后端会通过 scenario_id 查询，不依赖 case_ids 字段
        try {
          casesData[scenario.id] = await scenariosApi.getCases(scenario.id)
        } catch (e) {
          console.error(`加载场景 ${scenario.id} 的用例失败:`, e)
          casesData[scenario.id] = []
        }
      }
      setCases(casesData)

      const stepsData: Record<string, Step[]> = {}
      for (const [, caseList] of Object.entries(casesData)) {
        for (const caseItem of caseList) {
          if (caseItem.step_ids.length > 0) {
            stepsData[caseItem.id] = await scenariosApi.getSteps(caseItem.id)
          }
        }
      }
      setSteps(stepsData)

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

  // 打开创建模态框 - 新增创建方式选择
  const [showCreationModeSelector, setShowCreationModeSelector] = useState(false)

  const openCreateScenario = () => {
    setShowCreationModeSelector(true)
  }

  const selectCreationMode = (mode: 'manual' | 'recording') => {
    setShowCreationModeSelector(false)
    if (mode === 'manual') {
      setEditingScenario(undefined)
      setModalType('scenario')
    } else {
      // TODO: 实现录制创建模式
      setModalType('recording')
    }
  }

  const openEditScenario = (scenario: Scenario) => {
    setEditingScenario(scenario)
    setModalType('scenario')
  }

  const openCreateCase = (scenarioId: string) => {
    setModalScenarioId(scenarioId)
    setEditingCase(undefined)
    setModalType('case')
  }

  const openEditCase = (testCase: Case, scenarioId: string) => {
    setModalScenarioId(scenarioId)
    setEditingCase(testCase)
    setModalType('case')
  }

  const openCreateStep = (caseId: string) => {
    setModalCaseId(caseId)
    setEditingStep(undefined)
    setModalType('step')
  }

  const openEditStep = (step: Step, caseId: string) => {
    setModalCaseId(caseId)
    setEditingStep(step)
    setModalType('step')
  }

  // 关闭模态框
  const closeModal = () => {
    setModalType(null)
    setModalScenarioId(null)
    setModalCaseId(null)
    setEditingScenario(undefined)
    setEditingCase(undefined)
    setEditingStep(undefined)
  }

  // 处理创建/更新成功
  const handleScenarioSuccess = async (scenario: any) => {
    // 检查是否是从录制向导返回的完整场景数据
    if (scenario.cases && Array.isArray(scenario.cases)) {
      // 这是录制场景，需要调用保存API
      if (!task) {
        alert('任务信息未加载，请刷新页面重试')
        return
      }

      try {
        const response = await fetch('/api/v1/recording/save-scenario', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          credentials: 'include', // 发送Cookie
          body: JSON.stringify({
            task_id: taskId,
            project_id: task.project_id,
            scenario_name: scenario.name,
            scenario_description: scenario.description || '',
            scenario_type: scenario.scenario_type || 'recorded',
            cases: scenario.cases,
            test_data: scenario.test_data  // 添加测试数据
          })
        })

        if (!response.ok) {
          const error = await response.json()
          throw new Error(error.detail || '保存失败')
        }

        const savedScenario = await response.json()

        console.log('[保存成功] 场景已保存:', savedScenario)

        // 🔥 保存成功后重新加载数据，确保用例正确显示
        await loadData()

        // 🔥 显示成功提示
        alert(`场景 "${savedScenario.name}" 保存成功！`)

        closeModal()
      } catch (error: any) {
        console.error('保存录制场景失败:', error)
        alert(`保存失败: ${error.message}`)
      }
    } else {
      // 普通场景（表单创建）
      if (editingScenario) {
        setScenarios(prev => prev.map(s => s.id === scenario.id ? scenario : s))
      } else {
        setScenarios(prev => [...prev, scenario])
      }
      closeModal()
    }
  }

  const handleCaseSuccess = (testCase: Case) => {
    if (editingCase) {
      // 更新
      if (modalScenarioId) {
        setCases(prev => ({
          ...prev,
          [modalScenarioId]: prev[modalScenarioId].map(c => c.id === testCase.id ? testCase : c)
        }))
      }
    } else {
      // 创建
      if (modalScenarioId) {
        setCases(prev => ({
          ...prev,
          [modalScenarioId]: [...(prev[modalScenarioId] || []), testCase]
        }))
      }
    }
    closeModal()
  }

  const handleStepSuccess = (step: Step) => {
    if (editingStep) {
      // 更新
      if (modalCaseId) {
        setSteps(prev => ({
          ...prev,
          [modalCaseId]: prev[modalCaseId].map(s => s.id === step.id ? step : s)
        }))
      }
    } else {
      // 创建
      if (modalCaseId) {
        setSteps(prev => ({
          ...prev,
          [modalCaseId]: [...(prev[modalCaseId] || []), step]
        }))
      }
    }
    closeModal()
  }

  const handleDeleteScenario = async (scenarioId: string, scenarioName: string) => {
    if (!confirm(`确定要删除场景 "${scenarioName}" 吗？`)) return

    try {
      console.log('[删除场景] 开始删除:', scenarioId)
      await scenariosApi.deleteScenario(scenarioId)
      console.log('[删除场景] 删除成功，刷新列表')
      // 删除成功后重新加载数据，而不是本地过滤
      await loadData()
      console.log('[删除场景] 数据已刷新')
    } catch (err: any) {
      console.error('[删除场景] 失败:', err)
      alert('删除失败: ' + (err.response?.data?.detail || err.message))
    }
  }

  const handleDeleteCase = async (caseId: string, caseName: string, scenarioId: string) => {
    if (!confirm(`确定要删除用例 "${caseName}" 吗？`)) return

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
    if (!confirm(`确定要删除步骤 "${stepName}" 吗？`)) return

    try {
      await scenariosApi.deleteStep(stepId)
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

  const toggleStepSelection = (stepId: string) => {
    setSelectedSteps(prev => {
      const next = new Set(prev)
      if (next.has(stepId)) {
        next.delete(stepId)
      } else {
        next.add(stepId)
      }
      return next
    })
  }

  const clearStepSelection = () => setSelectedSteps(new Set())

  const handleBatchInsertAssertions = async () => {
    if (!batchCaseId || selectedSteps.size === 0) return
    try {
      const result = await scenariosApi.batchInsertSteps(batchCaseId, {
        after_step_ids: Array.from(selectedSteps),
        keyword_name: 'ASSERT_NO_ERROR',
        parameters: { error_text: '系统错误', timeout: 15000, poll_interval: 500 },
        continue_on_failure: true
      })
      alert(`已插入 ${result.inserted_count} 个断言步骤`)
      clearStepSelection()
      setBatchDialogOpen(false)
      setBatchCaseId(null)
      await loadData()
    } catch (err: any) {
      alert('批量插入失败: ' + (err.response?.data?.detail || err.message))
    }
  }

  const handleAutoInsertErrorAssertions = async (caseId: string) => {
    const caseSteps = steps[caseId] || []
    // 筛选出 CLICK 和 NAVIGATE 类型的步骤
    const clickNavStepIds = caseSteps
      .filter(s => {
        const kw = keywords[s.keyword_id]
        return kw && (kw.name === 'CLICK' || kw.name === 'NAVIGATE')
      })
      .map(s => s.id)

    if (clickNavStepIds.length === 0) {
      alert('该用例中没有 CLICK 或 NAVIGATE 步骤')
      return
    }

    if (!confirm(`将在 ${clickNavStepIds.length} 个点击/导航步骤后插入 ASSERT_NO_ERROR 断言，确认？`)) return

    try {
      const result = await scenariosApi.batchInsertSteps(caseId, {
        after_step_ids: clickNavStepIds,
        keyword_name: 'ASSERT_NO_ERROR',
        parameters: { error_text: '系统错误', timeout: 15000, poll_interval: 500 },
        continue_on_failure: true
      })
      alert(`已插入 ${result.inserted_count} 个断言步骤`)
      await loadData()
    } catch (err: any) {
      alert('自动插入失败: ' + (err.response?.data?.detail || err.message))
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
            onClick={openCreateScenario}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
          >
            创建场景
          </button>
          <button
            onClick={() => navigate(-1)}
            className="px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50"
          >
            返回
          </button>
        </div>
      </div>

      {/* 场景列表 */}
      {scenarios.length === 0 ? (
        <div className="text-center py-12 bg-white rounded-lg border border-dashed border-gray-300">
          <p className="text-gray-500 mb-4">暂无场景</p>
          <button
            onClick={openCreateScenario}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
          >
            创建第一个场景
          </button>
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
                    onClick={(e) => { e.stopPropagation(); openEditScenario(scenario) }}
                    className="px-3 py-1 text-sm bg-blue-600 text-white rounded hover:bg-blue-700"
                  >
                    编辑
                  </button>
                  <button
                    onClick={(e) => { e.stopPropagation(); openCreateCase(scenario.id) }}
                    className="px-3 py-1 text-sm bg-green-600 text-white rounded hover:bg-green-700"
                  >
                    添加用例
                  </button>
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
                    <div className="text-center text-gray-500 py-4">
                      暂无用例
                      <button
                        onClick={() => openCreateCase(scenario.id)}
                        className="ml-2 text-blue-600 hover:underline"
                      >
                        添加用例
                      </button>
                    </div>
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
                              onClick={(e) => { e.stopPropagation(); openEditCase(caseItem, scenario.id) }}
                              className="px-2 py-1 text-xs bg-blue-600 text-white rounded hover:bg-blue-700"
                            >
                              编辑
                            </button>
                            <button
                              onClick={(e) => { e.stopPropagation(); openCreateStep(caseItem.id) }}
                              className="px-2 py-1 text-xs bg-green-600 text-white rounded hover:bg-green-700"
                            >
                              添加步骤
                            </button>
                            <button
                              onClick={(e) => {
                                e.stopPropagation()
                                handleAutoInsertErrorAssertions(caseItem.id)
                              }}
                              className="px-2 py-1 text-xs bg-purple-600 text-white rounded hover:bg-purple-700"
                              title="在所有CLICK/NAVIGATE步骤后插入ASSERT_NO_ERROR"
                            >
                              ⚡一键插入错误断言
                            </button>
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
                              <div className="text-center text-gray-500 py-2 text-sm">
                                暂无步骤
                                <button
                                  onClick={() => openCreateStep(caseItem.id)}
                                  className="ml-2 text-blue-600 hover:underline"
                                >
                                  添加步骤
                                </button>
                              </div>
                            ) : (
                              steps[caseItem.id].map((step) => {
                                const keyword = keywords[step.keyword_id]
                                return (
                                  <div
                                    key={step.id}
                                    className={`flex items-center justify-between p-2 rounded text-sm ${
                                      step.enabled ? 'bg-white border' : 'bg-gray-100 border border-gray-200 opacity-60'
                                    } ${selectedSteps.has(step.id) ? 'ring-2 ring-blue-400 bg-blue-50' : ''}`}
                                  >
                                    <div className="flex items-center gap-2">
                                      <input
                                        type="checkbox"
                                        checked={selectedSteps.has(step.id)}
                                        onChange={() => {
                                          setBatchCaseId(caseItem.id)
                                          toggleStepSelection(step.id)
                                        }}
                                        onClick={(e) => e.stopPropagation()}
                                        className="w-4 h-4 text-blue-600 rounded border-gray-300 focus:ring-blue-500"
                                      />
                                      <span className="text-gray-400">{step.step_order + 1}.</span>
                                      <span className="font-medium">{step.step_name}</span>
                                      <span className="text-xs text-gray-500">({keyword?.name || step.keyword_id})</span>
                                      {!step.enabled && <span className="text-xs text-gray-400">[禁用]</span>}
                                    </div>
                                    <div className="flex items-center gap-1">
                                      <button
                                        onClick={() => openEditStep(step, caseItem.id)}
                                        className="px-2 py-1 text-xs bg-blue-600 text-white rounded hover:bg-blue-700"
                                      >
                                        编辑
                                      </button>
                                      <button
                                        onClick={() => handleDeleteStep(step.id, step.step_name, caseItem.id)}
                                        className="px-2 py-1 text-xs bg-red-600 text-white rounded hover:bg-red-700"
                                      >
                                        删除
                                      </button>
                                    </div>
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

      {/* 批量操作工具栏 */}
      {selectedSteps.size > 0 && (
        <div className="fixed bottom-6 left-1/2 transform -translate-x-1/2 bg-white border border-gray-300 shadow-xl rounded-lg px-4 py-3 flex items-center gap-3 z-40">
          <span className="text-sm font-medium text-gray-700">
            已选 <span className="text-blue-600">{selectedSteps.size}</span> 个步骤
          </span>
          <button
            onClick={() => handleBatchInsertAssertions()}
            className="px-3 py-1 text-sm bg-purple-600 text-white rounded hover:bg-purple-700"
          >
            插入断言
          </button>
          <button
            onClick={clearStepSelection}
            className="px-3 py-1 text-sm border border-gray-300 text-gray-600 rounded hover:bg-gray-50"
          >
            取消选择
          </button>
        </div>
      )}

      {/* 创建方式选择对话框 */}
      {showCreationModeSelector && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg max-w-3xl w-full p-6">
            <h2 className="text-2xl font-bold mb-2">选择场景创建方式</h2>
            <p className="text-gray-600 mb-6">选择适合您的创建方式，录制创建后可继续手工调整</p>

            <div className="grid grid-cols-2 gap-6">
              {/* 手动创建 */}
              <div
                onClick={() => selectCreationMode('manual')}
                className="border-2 border-gray-200 rounded-lg p-6 cursor-pointer hover:border-blue-500 hover:shadow-lg transition"
              >
                <div className="text-5xl mb-3">✏️</div>
                <h3 className="text-xl font-semibold mb-2">手动创建</h3>
                <p className="text-sm text-gray-600 mb-4">
                  逐步创建用例和步骤，精确控制每个细节
                </p>
                <ul className="text-sm space-y-1 text-gray-700">
                  <li>✓ 完全控制每个步骤</li>
                  <li>✓ 适合复杂测试逻辑</li>
                  <li>✓ 支持所有高级功能</li>
                  <li>✓ 可复用测试数据</li>
                </ul>
              </div>

              {/* 录制创建 */}
              <div
                onClick={() => selectCreationMode('recording')}
                className="border-2 border-gray-200 rounded-lg p-6 cursor-pointer hover:border-green-500 hover:shadow-lg transition"
              >
                <div className="text-5xl mb-3">🎬</div>
                <h3 className="text-xl font-semibold mb-2">录制创建</h3>
                <p className="text-sm text-gray-600 mb-4">
                  在浏览器中操作流程，自动生成测试步骤
                </p>
                <ul className="text-sm space-y-1 text-gray-700">
                  <li>✓ 快速生成基础步骤</li>
                  <li>✓ 自动识别元素选择器</li>
                  <li>✓ 智能提取测试数据</li>
                  <li>✓ 可后续手工调整</li>
                </ul>
              </div>
            </div>

            <div className="mt-6 flex justify-center">
              <button
                onClick={() => setShowCreationModeSelector(false)}
                className="px-6 py-2 border border-gray-300 rounded-lg hover:bg-gray-50"
              >
                取消
              </button>
            </div>
          </div>
        </div>
      )}

      {/* 模态框 */}
      {modalType && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg max-w-lg w-full max-h-[90vh] overflow-y-auto">
            <div className="p-6">
              <h2 className="text-xl font-semibold mb-4">
                {modalType === 'scenario' && (editingScenario ? '编辑场景' : '创建场景')}
                {modalType === 'case' && (editingCase ? '编辑用例' : '创建用例')}
                {modalType === 'step' && (editingStep ? '编辑步骤' : '创建步骤')}
              </h2>

              {modalType === 'recording' && taskId && (
                <RecordingWizard
                  taskId={taskId}
                  onComplete={handleScenarioSuccess}
                  onCancel={closeModal}
                />
              )}

              {modalType === 'scenario' && taskId && (
                <ScenarioForm
                  taskId={taskId}
                  scenario={editingScenario}
                  onSuccess={handleScenarioSuccess}
                  onCancel={closeModal}
                />
              )}

              {modalType === 'case' && modalScenarioId && (
                <CaseForm
                  scenarioId={modalScenarioId}
                  case={editingCase}
                  onSuccess={handleCaseSuccess}
                  onCancel={closeModal}
                />
              )}

              {modalType === 'step' && modalCaseId && (
                <StepForm
                  caseId={modalCaseId}
                  step={editingStep}
                  onSuccess={handleStepSuccess}
                  onCancel={closeModal}
                />
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
