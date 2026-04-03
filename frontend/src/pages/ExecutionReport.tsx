import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { tasksApi } from '../api/tasks'
import type { TestExecution } from '../types'

export default function ExecutionReport() {
  const { executionId } = useParams<{ executionId: string }>()
  const navigate = useNavigate()
  const [execution, setExecution] = useState<TestExecution | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    loadExecution()
  }, [executionId])

  const loadExecution = async () => {
    if (!executionId) return

    try {
      setLoading(true)
      setError(null)
      const data = await tasksApi.getExecution(executionId)
      setExecution(data)
    } catch (err: any) {
      setError(err.response?.data?.detail || '加载失败')
    } finally {
      setLoading(false)
    }
  }

  const formatDuration = (seconds?: number) => {
    if (!seconds) return '-'
    const mins = Math.floor(seconds / 60)
    const secs = Math.floor(seconds % 60)
    return mins > 0 ? `${mins}分${secs}秒` : `${secs}秒`
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed': return 'green'
      case 'running': return 'blue'
      case 'failed': return 'red'
      case 'pending': return 'gray'
      default: return 'gray'
    }
  }

  const getResultColor = (result?: string) => {
    switch (result) {
      case 'pass': return 'green'
      case 'fail': return 'red'
      case 'partial': return 'orange'
      case 'error': return 'red'
      default: return 'gray'
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
      <button onClick={() => navigate(-1)} className="ml-4 underline">返回</button>
    </div>
  )
  }

  if (!execution) {
    return (
      <div className="text-center py-8">
        <p className="text-gray-500">执行记录不存在</p>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* 标题栏 */}
      <div className="flex justify-between items-start">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">测试报告</h1>
          <p className="text-sm text-gray-500 mt-1">
            执行ID: {execution.id.slice(0, 8)}...
          </p>
        </div>
        <button
          onClick={() => navigate(-1)}
          className="px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50"
        >
          返回
        </button>
      </div>

      {/* 执行概览 */}
      <div className="bg-white border border-gray-200 rounded-lg p-6">
        <h2 className="text-lg font-semibold mb-4">执行概览</h2>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div>
            <p className="text-sm text-gray-500">状态</p>
            <p className="text-lg font-semibold" style={{ color: getStatusColor(execution.status) }}>
              {execution.status === 'completed' ? execution.result : execution.status}
            </p>
          </div>
          <div>
            <p className="text-sm text-gray-500">开始时间</p>
            <p className="text-sm font-medium">
              {execution.started_at ? new Date(execution.started_at).toLocaleString('zh-CN') : '-'}
            </p>
          </div>
          <div>
            <p className="text-sm text-gray-500">执行时长</p>
            <p className="text-sm font-medium">{formatDuration(execution.duration)}</p>
          </div>
          <div>
            <p className="text-sm text-gray-500">结果</p>
            <p className="text-lg font-semibold" style={{ color: getResultColor(execution.result) }}>
              {execution.result?.toUpperCase() || '-'}
            </p>
          </div>
        </div>

        {/* 统计信息 */}
        <div className="mt-4 pt-4 border-t">
          <div className="grid grid-cols-2 md:grid-cols-3 gap-4 text-sm">
            <div>
              <span className="text-gray-500">场景数: </span>
              <span className="font-medium ml-2">{execution.total_scenarios}</span>
            </div>
            <div>
              <span className="text-gray-500">用例数: </span>
              <span className="font-medium ml-2">{execution.total_cases}</span>
            </div>
            <div>
              <span className="text-gray-500">步骤数: </span>
              <span className="font-medium ml-2">{execution.total_steps}</span>
            </div>
            <div>
              <span className="text-green-600">通过: </span>
              <span className="font-medium ml-2">{execution.passed_steps}</span>
            </div>
            <div>
              <span className="text-red-600">失败: </span>
              <span className="font-medium ml-2">{execution.failed_steps}</span>
            </div>
            <div>
              <span className="text-gray-500">跳过: </span>
              <span className="font-medium ml-2">{execution.skipped_steps}</span>
            </div>
          </div>
        </div>

        {execution.error_message && (
          <div className="mt-4 p-3 bg-red-50 text-red-700 rounded">
            <p className="font-medium">错误信息:</p>
            <p className="text-sm">{execution.error_message}</p>
          </div>
        )}
      </div>

      {/* 场景执行详情 */}
      <div className="space-y-4">
        <h2 className="text-lg font-semibold">场景执行详情</h2>
        {execution.scenario_executions.map((scenarioExec) => (
          <div key={scenarioExec.id} className="bg-white border border-gray-200 rounded-lg p-4">
            <div className="flex justify-between items-start mb-2">
              <h3 className="font-medium">场景 #{scenarioExec.execution_order}</h3>
              <span className={`px-2 py-1 text-xs rounded ${
                scenarioExec.result === 'pass' ? 'bg-green-100 text-green-700' :
                scenarioExec.result === 'fail' ? 'bg-red-100 text-red-700' :
                'bg-gray-100 text-gray-700'
              }`}>
                {scenarioExec.result?.toUpperCase() || scenarioExec.status}
              </span>
            </div>

            <div className="text-sm text-gray-500 mb-3">
              用例数: {scenarioExec.total_cases} •
              通过步骤: {scenarioExec.passed_steps} •
              失败步骤: {scenarioExec.failed_steps} •
              时长: {formatDuration(scenarioExec.duration)}
            </div>

            {/* 用例执行列表 */}
            {scenarioExec.case_executions.map((caseExec) => (
              <details key={caseExec.id} className="ml-4 mt-2 border-l-2 border-gray-200 pl-4">
                <summary className="cursor-pointer py-1 font-medium text-sm hover:text-blue-600">
                  用例: {caseExec.id.slice(0, 8)}...
                  <span className={`ml-2 px-2 py-0.5 text-xs rounded ${
                    caseExec.result === 'pass' ? 'bg-green-100 text-green-700' :
                    caseExec.result === 'fail' ? 'bg-red-100 text-red-700' :
                    'bg-gray-100 text-gray-700'
                  }`}>
                    {caseExec.result?.toUpperCase() || caseExec.status}
                  </span>
                </summary>

                <div className="mt-2 space-y-2">
                  {caseExec.step_executions.map((stepExec) => (
                    <div key={stepExec.id} className="bg-gray-50 rounded p-2 text-sm">
                      <div className="flex justify-between items-start">
                        <span className="font-mono text-xs">
                          {stepExec.step_order}. {stepExec.keyword_name}
                        </span>
                        <span className={`px-2 py-0.5 text-xs rounded ${
                          stepExec.result === 'pass' ? 'bg-green-100 text-green-700' :
                          stepExec.result === 'fail' ? 'bg-red-100 text-red-700' :
                          'bg-gray-100 text-gray-700'
                        }`}>
                          {stepExec.result?.toUpperCase() || stepExec.status}
                        </span>
                      </div>

                      {stepExec.error_message && (
                        <div className="mt-1 text-red-600 text-xs">
                          错误: {stepExec.error_message}
                        </div>
                      )}

                      {stepExec.screenshot_path && (
                        <div className="mt-1">
                          <span className="text-xs text-gray-500">
                            <a href={`http://localhost:8000/screenshots/${stepExec.screenshot_path.split('/')[-1]}`}
                               target="_blank"
                               className="text-blue-600 hover:underline">
                              查看截图
                            </a>
                          </span>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </details>
            ))}
          </div>
        ))}
      </div>
    </div>
  )
}
