import { useState, useEffect, useCallback } from 'react'
import { recordingApi, CapturedAction, DataPattern } from '../api/recording'

interface RecordingWizardProps {
  taskId: string
  onComplete: (scenario: any) => void
  onCancel: () => void
}

export default function RecordingWizard({ taskId, onComplete, onCancel }: RecordingWizardProps) {
  const [currentStep, setCurrentStep] = useState(1)
  const [scenarioName, setScenarioName] = useState('')
  const [isRecording, setIsRecording] = useState(false)
  const [sessionId, setSessionId] = useState<string | null>(null)
  const [capturedActions, setCapturedActions] = useState<CapturedAction[]>([])
  const [dataPatterns, setDataPatterns] = useState<DataPattern[]>([])
  const [generatedScenario, setGeneratedScenario] = useState<any>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // 🔥 新增：录制配置选项
  const [recordingConfig, setRecordingConfig] = useState({
    enableSmartWait: true,
    autoExtractVariables: true,
    mergeContinuousInputs: true
  })

  const steps = [
    { number: 1, title: '录制准备', description: '设置场景信息' },
    { number: 2, title: '录制中', description: '在浏览器中执行操作' },
    { number: 3, title: '智能提取', description: '提取测试数据' },
    { number: 4, title: '预览调整', description: '查看和编辑结果' }
  ]

  // 轮询捕获的操作
  const pollActions = useCallback(async (sessionId: string) => {
    try {
      const actions = await recordingApi.getCapturedActions(sessionId)
      setCapturedActions(actions)
    } catch (err) {
      console.error('获取操作失败:', err)
    }
  }, [])

  // 启动轮询
  useEffect(() => {
    let intervalId: ReturnType<typeof setInterval> | null = null

    if (isRecording && sessionId) {
      intervalId = setInterval(() => {
        pollActions(sessionId)
      }, 2000) // 每2秒轮询一次
    }

    return () => {
      if (intervalId) {
        clearInterval(intervalId)
      }
    }
  }, [isRecording, sessionId, pollActions])

  const handleStartRecording = async () => {
    if (!scenarioName.trim()) {
      alert('请输入场景名称')
      return
    }

    setLoading(true)
    setError(null)

    try {
      const response = await recordingApi.startRecording({
        project_id: taskId,
        scenario_name: scenarioName,
        config: recordingConfig
      })

      setSessionId(response.session_id)
      setIsRecording(true)
      setCurrentStep(2)
      console.log('录制已启动:', response.session_id)
    } catch (err: any) {
      setError(`启动录制失败: ${err.message || err}`)
      console.error('启动录制失败:', err)
    } finally {
      setLoading(false)
    }
  }

  const handleStopRecording = async () => {
    if (!sessionId) {
      setError('录制会话不存在')
      return
    }

    setLoading(true)
    setError(null)

    try {
      // 停止录制
      const stopResponse = await recordingApi.stopRecording({ session_id: sessionId })
      setCapturedActions(stopResponse.actions)
      setIsRecording(false)

      // 提取数据模式
      if (stopResponse.actions.length > 0) {
        const extractionResult = await recordingApi.extractTestData({
          actions: stopResponse.actions
        })
        setDataPatterns(extractionResult.patterns)
      }

      setCurrentStep(3)
      console.log(`录制已完成，捕获 ${stopResponse.actions_count} 个操作`)
    } catch (err: any) {
      setError(`停止录制失败: ${err.message || err}`)
      console.error('停止录制失败:', err)
      setIsRecording(false)
    } finally {
      setLoading(false)
    }
  }

  const handlePreview = async () => {
    setLoading(true)
    setError(null)

    try {
      // 生成场景
      const response = await recordingApi.generateScenario({
        project_id: taskId,
        scenario_name: scenarioName,
        actions: capturedActions,
        data_patterns: dataPatterns,
        config: recordingConfig
      })

      setGeneratedScenario(response.scenario)
      setCurrentStep(4)
      console.log('场景已生成:', response.scenario)
    } catch (err: any) {
      setError(`生成场景失败: ${err.message || err}`)
      console.error('生成场景失败:', err)
    } finally {
      setLoading(false)
    }
  }

  const handleConfirmSave = () => {
    if (generatedScenario) {
      onComplete(generatedScenario)
    } else {
      setError('场景未生成，请重新生成')
    }
  }

  const handleRetry = () => {
    setCurrentStep(1)
    setScenarioName('')
    setCapturedActions([])
    setDataPatterns([])
    setGeneratedScenario(null)
    setSessionId(null)
    setError(null)
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg max-w-4xl w-full max-h-screen overflow-y-auto">
        {/* 头部 */}
        <div className="sticky top-0 bg-white border-b px-6 py-4">
          <div className="flex justify-between items-center">
            <div>
              <h2 className="text-2xl font-bold">🎬 录制创建场景</h2>
              <p className="text-sm text-gray-500">按步骤完成录制，系统将自动生成测试场景</p>
            </div>
            <button
              onClick={onCancel}
              className="text-gray-400 hover:text-gray-600 text-2xl"
            >
              ×
            </button>
          </div>

          {/* 步骤指示器 */}
          <div className="flex items-center justify-between mt-4 px-4">
            {steps.map((step, index) => (
              <div key={step.number} className="flex items-center flex-1">
                <div className={`flex flex-col items-center ${
                  index < currentStep - 1 ? 'text-blue-600' : index === currentStep - 1 ? 'text-blue-600' : 'text-gray-400'
                }`}>
                  <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold ${
                    index < currentStep - 1 ? 'bg-blue-600 text-white' :
                    index === currentStep - 1 ? 'bg-blue-100 border-2 border-blue-600' :
                    'bg-gray-200'
                  }`}>
                    {index < currentStep - 1 ? '✓' : step.number}
                  </div>
                  <div className="text-xs mt-1 text-center">
                    <div className="font-medium">{step.title}</div>
                    <div className="text-gray-500">{step.description}</div>
                  </div>
                </div>
                {index < steps.length - 1 && (
                  <div className={`flex-1 h-1 mx-2 ${index < currentStep - 1 ? 'bg-blue-600' : 'bg-gray-200'}`} />
                )}
              </div>
            ))}
          </div>
        </div>

        {/* 错误提示 */}
        {error && (
          <div className="mx-6 mt-4 bg-red-50 border border-red-200 rounded-lg p-3 flex items-start gap-2">
            <span className="text-red-600">⚠️</span>
            <div className="flex-1">
              <div className="text-sm font-medium text-red-800">发生错误</div>
              <div className="text-xs text-red-700 mt-1">{error}</div>
            </div>
            <button
              onClick={() => setError(null)}
              className="text-red-400 hover:text-red-600"
            >
              ×
            </button>
          </div>
        )}

        {/* 步骤内容 */}
        <div className="p-6">
          {currentStep === 1 && (
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  场景名称 <span className="text-red-500">*</span>
                </label>
                <input
                  type="text"
                  value={scenarioName}
                  onChange={(e) => setScenarioName(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                  placeholder="例如: 用户登录流程"
                />
              </div>

              <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
                <h3 className="font-medium text-gray-900 mb-3">⚙️ 录制配置</h3>
                <div className="space-y-3">
                  <label className="flex items-center gap-2">
                    <input
                      type="checkbox"
                      checked={recordingConfig.enableSmartWait}
                      onChange={(e) => setRecordingConfig(prev => ({ ...prev, enableSmartWait: e.target.checked }))}
                      className="rounded"
                    />
                    <div className="flex-1">
                      <div className="text-sm font-medium text-gray-700">启用智能等待</div>
                      <div className="text-xs text-gray-500">在每个操作前自动等待元素就绪（推荐）</div>
                    </div>
                  </label>

                  <label className="flex items-center gap-2">
                    <input
                      type="checkbox"
                      checked={recordingConfig.autoExtractVariables}
                      onChange={(e) => setRecordingConfig(prev => ({ ...prev, autoExtractVariables: e.target.checked }))}
                      className="rounded"
                    />
                    <div className="flex-1">
                      <div className="text-sm font-medium text-gray-700">自动提取变量</div>
                      <div className="text-xs text-gray-500">智能识别可参数化的输入字段</div>
                    </div>
                  </label>

                  <label className="flex items-center gap-2">
                    <input
                      type="checkbox"
                      checked={recordingConfig.mergeContinuousInputs}
                      onChange={(e) => setRecordingConfig(prev => ({ ...prev, mergeContinuousInputs: e.target.checked }))}
                      className="rounded"
                    />
                    <div className="flex-1">
                      <div className="text-sm font-medium text-gray-700">合并连续输入</div>
                      <div className="text-xs text-gray-500">只记录最终输入值，不记录过程</div>
                    </div>
                  </label>
                </div>
              </div>

              <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                <h3 className="font-medium text-blue-900 mb-2">📋 录制前准备</h3>
                <ul className="text-sm text-blue-800 space-y-2">
                  <li>1. 确保您已经安装了浏览器扩展程序（首次使用）</li>
                  <li>2. 准备好要测试的网页地址</li>
                  <li>3. 规划好要执行的操作流程</li>
                  <li>4. 点击"开始录制"后，系统将打开专门的录制浏览器</li>
                </ul>
              </div>

              <div className="flex justify-end">
                <button
                  onClick={handleStartRecording}
                  disabled={loading}
                  className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-400"
                >
                  {loading ? '启动中...' : '开始录制 →'}
                </button>
              </div>
            </div>
          )}

          {currentStep === 2 && (
            <div className="space-y-4">
              {isRecording && (
                <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-center">
                  <div className="text-2xl mb-2">🔴 录制中...</div>
                  <div className="text-sm text-red-700 mb-4">
                    请在新打开的浏览器中执行您的测试操作
                  </div>
                  <div className="text-xs text-red-600">
                    已捕获 {capturedActions.length} 个操作
                  </div>
                </div>
              )}

              <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
                <h3 className="font-medium mb-2">录制提示</h3>
                <ul className="text-sm text-gray-700 space-y-1">
                  <li>• 执行您想要测试的完整流程</li>
                  <li>• 系统会自动捕获点击、输入、导航等操作</li>
                  <li>• 完成后点击下方"停止录制"按钮</li>
                  <li>• 录制越精确，生成的测试越可靠</li>
                </ul>
              </div>

              <div className="flex justify-end">
                <button
                  onClick={handleStopRecording}
                  disabled={loading}
                  className="px-6 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 disabled:bg-gray-400"
                >
                  {loading ? '停止中...' : '停止录制 →'}
                </button>
              </div>
            </div>
          )}

          {currentStep === 3 && (
            <div className="space-y-4">
              <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                <h3 className="font-medium text-green-900 mb-2">🧠 智能数据提取与变量管理</h3>
                <p className="text-sm text-green-700 mb-4">
                  系统已从您的操作中识别出以下可变数据。您可以修改变量名、输入新值或添加额外的测试数据。
                </p>

                {dataPatterns.length === 0 ? (
                  <div className="text-sm text-green-700 bg-white p-4 rounded border">
                    未检测到可变数据模式。您可以直接点击"预览结果"继续。
                  </div>
                ) : (
                  <div className="space-y-3">
                    {dataPatterns.map((pattern) => (
                      <div key={pattern.id} className="bg-white rounded border p-3">
                        {/* 头部：选择开关和基本信息 */}
                        <div className="flex items-center justify-between mb-2">
                          <div className="flex items-center gap-3">
                            <input
                              type="checkbox"
                              checked={pattern.selected}
                              onChange={(e) => {
                                setDataPatterns(prev =>
                                  prev.map(p =>
                                    p.id === pattern.id ? { ...p, selected: e.target.checked } : p
                                  )
                                )
                              }}
                              className="rounded w-4 h-4"
                            />
                            <input
                              type="text"
                              value={pattern.field_name}
                              onChange={(e) => {
                                setDataPatterns(prev =>
                                  prev.map(p =>
                                    p.id === pattern.id ? { ...p, field_name: e.target.value } : p
                                  )
                                )
                              }}
                              className="text-sm font-medium border-b border-transparent hover:border-gray-300 focus:border-blue-500 focus:outline-none px-1"
                              placeholder="变量名"
                            />
                            <span className="text-xs px-2 py-1 bg-blue-100 text-blue-800 rounded">
                              {pattern.pattern_type}
                            </span>
                          </div>
                          <div className="flex items-center gap-2">
                            {/* 置信度可视化 */}
                            {pattern.confidence && (
                              <div className="flex items-center gap-1">
                                <div className="w-16 h-2 bg-gray-200 rounded-full overflow-hidden">
                                  <div
                                    className={`h-full ${
                                      pattern.confidence >= 0.8 ? 'bg-green-500' :
                                      pattern.confidence >= 0.6 ? 'bg-yellow-500' :
                                      'bg-red-500'
                                    }`}
                                    style={{ width: `${pattern.confidence * 100}%` }}
                                  />
                                </div>
                                <span className="text-xs text-gray-600">
                                  {(pattern.confidence * 100).toFixed(0)}%
                                </span>
                              </div>
                            )}
                          </div>
                        </div>

                        {/* 当前值列表 */}
                        <div className="mb-2">
                          <div className="text-xs text-gray-600 mb-1">当前值:</div>
                          <div className="flex flex-wrap gap-1">
                            {pattern.values.map((value, idx) => (
                              <span
                                key={idx}
                                className="text-xs px-2 py-1 bg-gray-100 rounded"
                              >
                                "{String(value).slice(0, 20)}{String(value).length > 20 ? '...' : ''}"
                              </span>
                            ))}
                          </div>
                        </div>

                        {/* 添加新值 */}
                        <div className="flex items-center gap-2">
                          <input
                            type="text"
                            className="flex-1 text-sm border border-gray-300 rounded px-2 py-1 focus:ring-2 focus:ring-blue-500 focus:outline-none"
                            placeholder="输入新的测试值..."
                            onKeyPress={(e) => {
                              if (e.key === 'Enter' && e.currentTarget.value.trim()) {
                                setDataPatterns(prev =>
                                  prev.map(p =>
                                    p.id === pattern.id
                                      ? { ...p, values: [...p.values, e.currentTarget.value.trim()] }
                                      : p
                                  )
                                )
                                e.currentTarget.value = ''
                              }
                            }}
                          />
                          <button
                            onClick={() => {
                              const input = document.activeElement as HTMLInputElement
                              if (input && input.value.trim()) {
                                setDataPatterns(prev =>
                                  prev.map(p =>
                                    p.id === pattern.id
                                      ? { ...p, values: [...p.values, input.value.trim()] }
                                      : p
                                  )
                                )
                                input.value = ''
                              }
                            }}
                            className="px-3 py-1 text-xs bg-blue-600 text-white rounded hover:bg-blue-700"
                          >
                            添加
                          </button>
                        </div>
                      </div>
                    ))}
                  </div>
                )}

                {/* 添加新变量按钮 */}
                {dataPatterns.length > 0 && (
                  <button
                    onClick={() => {
                      const newPattern = {
                        id: `custom_${Date.now()}`,
                        field_name: 'new_variable',
                        pattern_type: 'custom',
                        values: [''],
                        confidence: 1.0,
                        selected: true
                      }
                      setDataPatterns(prev => [...prev, newPattern])
                    }}
                    className="mt-3 px-4 py-2 text-sm border-2 border-dashed border-green-300 text-green-700 rounded-lg hover:bg-green-50 w-full"
                  >
                    + 添加自定义变量
                  </button>
                )}
              </div>

              <div className="flex justify-end">
                <button
                  onClick={handlePreview}
                  disabled={loading}
                  className="px-6 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:bg-gray-400"
                >
                  {loading ? '处理中...' : '预览结果 →'}
                </button>
              </div>
            </div>
          )}

          {currentStep === 4 && (
            <div className="space-y-4">
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                <h3 className="font-medium text-blue-900 mb-2">📊 录制结果预览</h3>
                {generatedScenario ? (
                  <>
                    <div className="text-sm text-blue-700 mb-4">
                      系统已为您生成 {generatedScenario.cases?.[0]?.steps?.length || 0} 个步骤
                      {generatedScenario.cases?.length > 1 && `，${generatedScenario.cases.length} 个用例`}
                      ，您可以查看和调整
                    </div>

                    {/* 生成的用例和步骤 - 增强版 */}
                    <div className="space-y-3">
                      {generatedScenario.cases?.map((testCase: any, caseIndex: number) => (
                        <div key={testCase.id || caseIndex} className="bg-white p-3 rounded border">
                          <div className="font-medium text-sm mb-2 flex items-center gap-2">
                            <span>用例 {caseIndex + 1}: {testCase.name}</span>
                            <span className="text-xs px-2 py-1 bg-green-100 text-green-800 rounded">
                              {testCase.steps?.length || 0} 步骤
                            </span>
                          </div>
                          {testCase.description && (
                            <div className="text-xs text-gray-600 mb-3">{testCase.description}</div>
                          )}
                          <div className="space-y-2">
                            {testCase.steps?.map((step: any, stepIndex: number) => (
                              <div key={step.id || stepIndex} className="border border-gray-200 rounded overflow-hidden">
                                {/* 步骤头部 */}
                                <div className="flex items-center gap-2 p-2 bg-gray-50">
                                  <span className="text-xs font-mono text-gray-500 w-6">
                                    {stepIndex + 1}.
                                  </span>
                                  <span className="text-sm font-medium flex-1">{step.step_name}</span>
                                  <span className="text-xs px-2 py-1 bg-blue-100 text-blue-800 rounded">
                                    {step.keyword_id?.replace('kw_', '') || '未知'}
                                  </span>
                                  {step.enabled === false && (
                                    <span className="text-xs px-2 py-1 bg-gray-200 text-gray-600 rounded">
                                      禁用
                                    </span>
                                  )}
                                </div>

                                {/* 步骤参数（可展开） */}
                                {step.parameters && Object.keys(step.parameters).length > 0 && (
                                  <div className="p-2 bg-white border-t border-gray-200">
                                    <div className="text-xs text-gray-500 mb-1">参数:</div>
                                    <div className="grid grid-cols-2 gap-2 text-xs">
                                      {Object.entries(step.parameters).map(([key, value]) => (
                                        <div key={key} className="flex items-center gap-2">
                                          <span className="font-medium text-gray-700">{key}:</span>
                                          <span className="text-gray-600 font-mono bg-gray-100 px-1 rounded truncate">
                                            {typeof value === 'object' ? JSON.stringify(value) : String(value)}
                                          </span>
                                        </div>
                                      ))}
                                    </div>
                                  </div>
                                )}
                              </div>
                            ))}
                          </div>
                        </div>
                      ))}
                    </div>

                    {/* 变量汇总 */}
                    {dataPatterns.filter(p => p.selected).length > 0 && (
                      <div className="mt-4 p-3 bg-purple-50 border border-purple-200 rounded">
                        <div className="text-sm font-medium text-purple-900 mb-2">
                          📝 提取的变量 ({dataPatterns.filter(p => p.selected).length} 个)
                        </div>
                        <div className="flex flex-wrap gap-2">
                          {dataPatterns.filter(p => p.selected).map(pattern => (
                            <div key={pattern.id} className="text-xs bg-white px-2 py-1 rounded border">
                              <span className="font-medium">\${pattern.field_name}</span>
                              <span className="text-gray-500 ml-1">
                                ({pattern.values.length} 个值)
                              </span>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {generatedScenario.metadata && (
                      <div className="mt-3 text-xs text-gray-600 bg-white p-2 rounded border">
                        <div className="flex flex-wrap gap-x-4 gap-y-1">
                          <span>创建方式: <strong>{generatedScenario.metadata.created_by}</strong></span>
                          <span>操作数: <strong>{generatedScenario.metadata.actions_count}</strong></span>
                          <span>数据模式: <strong>{generatedScenario.metadata.data_patterns_count}</strong></span>
                          {recordingConfig.enableSmartWait && (
                            <span>智能等待: <strong className="text-green-600">✓ 已启用</strong></span>
                          )}
                        </div>
                      </div>
                    )}
                  </>
                ) : (
                  <div className="text-sm text-blue-700 bg-white p-4 rounded border">
                    场景生成中，请稍候...
                  </div>
                )}
              </div>

              <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
                <h3 className="font-medium text-yellow-900 mb-2">💡 下一步操作</h3>
                <ul className="text-sm text-yellow-800 space-y-1">
                  <li>• 保存后，可以在场景编辑器中继续编辑步骤</li>
                  <li>• 可以添加断言验证步骤</li>
                  <li>• 可以创建测试数据集进行数据驱动测试</li>
                  <li>• 建议先运行测试验证流程是否正确</li>
                </ul>
              </div>

              <div className="flex justify-end gap-2">
                <button
                  onClick={handleRetry}
                  className="px-6 py-2 border border-gray-300 rounded-lg hover:bg-gray-50"
                >
                  重新录制
                </button>
                <button
                  onClick={handleConfirmSave}
                  disabled={!generatedScenario}
                  className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-400"
                >
                  确认保存
                </button>
              </div>
            </div>
          )}
                <button
                  onClick={handleConfirmSave}
                  disabled={!generatedScenario}
                  className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-400"
                >
                  确认保存
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}