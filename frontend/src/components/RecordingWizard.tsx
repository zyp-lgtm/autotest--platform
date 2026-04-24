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
        scenario_name: scenarioName
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
        data_patterns: dataPatterns
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
                <h3 className="font-medium text-green-900 mb-2">🧠 智能数据提取</h3>
                <p className="text-sm text-green-700 mb-4">
                  系统已从您的操作中识别出以下可变数据，选择要作为测试数据的字段
                </p>

                {dataPatterns.length === 0 ? (
                  <div className="text-sm text-green-700 bg-white p-4 rounded border">
                    未检测到可变数据模式。您可以直接点击"预览结果"继续。
                  </div>
                ) : (
                  <div className="space-y-2">
                    {dataPatterns.map((pattern) => (
                      <div key={pattern.id} className="flex items-center justify-between p-2 bg-white rounded border">
                        <div className="flex items-center gap-2">
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
                            className="rounded"
                          />
                          <span className="text-sm font-medium">{pattern.field_name}</span>
                          <span className="text-xs text-gray-500">{pattern.pattern_type}</span>
                        </div>
                        <div className="text-xs bg-gray-100 px-2 py-1 rounded">
                          检测到 {pattern.values.length} 个值
                          {pattern.confidence && ` · 置信度 ${(pattern.confidence * 100).toFixed(0)}%`}
                        </div>
                      </div>
                    ))}
                  </div>
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

                    {/* 生成的用例和步骤 */}
                    <div className="space-y-3">
                      {generatedScenario.cases?.map((testCase: any, caseIndex: number) => (
                        <div key={testCase.id || caseIndex} className="bg-white p-3 rounded border">
                          <div className="font-medium text-sm mb-2">用例 {caseIndex + 1}: {testCase.name}</div>
                          {testCase.description && (
                            <div className="text-xs text-gray-600 mb-2">{testCase.description}</div>
                          )}
                          <div className="space-y-1">
                            {testCase.steps?.map((step: any, stepIndex: number) => (
                              <div key={step.id || stepIndex} className="flex items-center gap-2 p-2 bg-gray-50 rounded">
                                <span className="text-xs text-gray-500">{stepIndex + 1}.</span>
                                <span className="text-sm">{step.step_name}</span>
                                {step.keyword_id && (
                                  <span className="text-xs bg-blue-100 text-blue-800 px-1 rounded">
                                    关键字
                                  </span>
                                )}
                              </div>
                            ))}
                          </div>
                        </div>
                      ))}
                    </div>

                    {generatedScenario.metadata && (
                      <div className="mt-3 text-xs text-gray-600 bg-white p-2 rounded">
                        创建方式: {generatedScenario.metadata.created_by} ·
                        操作数: {generatedScenario.metadata.actions_count} ·
                        数据模式: {generatedScenario.metadata.data_patterns_count}
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
                <h3 className="font-medium text-yellow-900 mb-2">💡 提示</h3>
                <p className="text-sm text-yellow-800">
                  保存后，您可以像编辑手动创建的场景一样继续编辑这些步骤，添加断言、修改参数等
                </p>
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
        </div>
      </div>
    </div>
  )
}