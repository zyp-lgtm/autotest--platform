import { useState } from 'react'
import { CheckCircle2, Clock, ChevronDown, ChevronRight, FileText } from 'lucide-react'
import type { ExecutionStep } from '../../types/debug'

interface ExecutionStepsProps {
  steps: ExecutionStep[]
}

export default function ExecutionSteps({ steps }: ExecutionStepsProps) {
  const [expandedStep, setExpandedStep] = useState<Set<number>>(new Set())

  if (!steps || steps.length === 0) {
    return <div className="text-gray-500 text-center py-8">没有执行步骤记录</div>
  }

  const toggleExpand = (index: number) => {
    const newExpanded = new Set(expandedStep)
    if (newExpanded.has(index)) {
      newExpanded.delete(index)
    } else {
      newExpanded.add(index)
    }
    setExpandedStep(newExpanded)
  }

  const getActionIcon = (action: string) => {
    switch (action) {
      case 'complete':
        return <CheckCircle2 className="w-4 h-4 text-green-600" />
      case 'start':
        return <Clock className="w-4 h-4 text-blue-500" />
      default:
        return <FileText className="w-4 h-4 text-gray-400" />
    }
  }

  const getActionBgColor = (action: string) => {
    switch (action) {
      case 'complete':
        return 'bg-green-50 border-green-200'
      case 'start':
        return 'bg-blue-50 border-blue-200'
      default:
        return 'bg-gray-50 border-gray-200'
    }
  }

  const formatDuration = (ms?: number) => {
    if (!ms) return '-'
    if (ms < 1000) return `${ms}ms`
    return `${(ms / 1000).toFixed(2)}s`
  }

  const formatTimestamp = (timestamp: string) => {
    try {
      const date = new Date(timestamp)
      return date.toLocaleTimeString('zh-CN', { hour12: false })
    } catch {
      return timestamp
    }
  }

  return (
    <div className="space-y-3">
      {/* 统计信息 */}
      <div className="flex items-center justify-between text-sm">
        <div className="flex items-center gap-4">
          <span className="text-gray-600">总计: {steps.length} 个步骤</span>
          <span className="text-green-600">
            完成: {steps.filter(s => s.action === 'complete').length}
          </span>
        </div>
      </div>

      {/* 步骤列表 */}
      <div className="space-y-2">
        {steps.map((step, index) => (
          <div
            key={index}
            className={`border rounded-lg overflow-hidden ${getActionBgColor(step.action)}`}
          >
            {/* 步骤头部（可点击展开） */}
            <button
              onClick={() => toggleExpand(index)}
              className="w-full px-3 py-2 flex items-start gap-2 hover:bg-opacity-50 transition-colors text-left"
            >
              <div className="flex-shrink-0 mt-0.5">
                {expandedStep.has(index) ? (
                  <ChevronDown className="w-3 h-3 text-gray-500" />
                ) : (
                  <ChevronRight className="w-3 h-3 text-gray-500" />
                )}
              </div>
              <div className="flex-grow">
                <div className="flex items-center gap-2">
                  {getActionIcon(step.action)}
                  <span className="font-medium text-sm">{step.step_name}</span>
                  {step.keyword && (
                    <span className="px-1.5 py-0.5 bg-gray-200 text-gray-700 text-xs rounded font-mono">
                      {step.keyword}
                    </span>
                  )}
                </div>
                <div className="flex items-center gap-3 mt-1 text-xs text-gray-600">
                  <span>时间: {formatTimestamp(step.timestamp)}</span>
                  {step.duration_ms && (
                    <span>耗时: {formatDuration(step.duration_ms)}</span>
                  )}
                  {step.result?.status && (
                    <span className={`font-medium ${
                      step.result.status === 'success' ? 'text-green-600' : 'text-red-600'
                    }`}>
                      {step.result.status}
                    </span>
                  )}
                </div>
              </div>
            </button>

            {/* 详细信息 */}
            {expandedStep.has(index) && (
              <div className="px-3 pb-2 text-xs space-y-2 border-t border-gray-300 border-opacity-50 pt-2">
                <div><span className="font-medium">动作:</span> {step.action}</div>
                <div><span className="font-medium">步骤:</span> {step.step_name}</div>
                {step.keyword && <div><span className="font-medium">关键字:</span> {step.keyword}</div>}
                {step.duration_ms && <div><span className="font-medium">耗时:</span> {formatDuration(step.duration_ms)}</div>}
                <div><span className="font-medium">时间戳:</span> {step.timestamp}</div>

                {/* 参数 */}
                {step.parameters && Object.keys(step.parameters).length > 0 && (
                  <div>
                    <span className="font-medium">参数:</span>
                    <pre className="mt-1 text-xs bg-gray-50 p-2 rounded overflow-x-auto">
                      {JSON.stringify(step.parameters, null, 2)}
                    </pre>
                  </div>
                )}

                {/* 结果 */}
                {step.result && Object.keys(step.result).length > 0 && (
                  <div>
                    <span className="font-medium">结果:</span>
                    <pre className="mt-1 text-xs bg-gray-50 p-2 rounded overflow-x-auto">
                      {JSON.stringify(step.result, null, 2)}
                    </pre>
                  </div>
                )}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  )
}
