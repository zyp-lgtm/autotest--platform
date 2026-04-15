import { useState } from 'react'
import { ChevronDown, ChevronRight, Clock, AlertCircle, CheckCircle, XCircle } from 'lucide-react'

interface StepDetailProps {
  step: {
    step_name: string
    keyword_name: string
    parameters?: Record<string, any>
    status: string
    result?: string
    duration?: number
    error_message?: string
    logs?: Array<{ timestamp: string; level: string; message: string }>
    screenshot_path?: string
    output?: {
      error_category?: string
      error_severity?: string
      error_suggestion?: {
        title: string
        description: string
        solutions: string[]
      }
    }
  }
}

export default function StepDetail({ step }: StepDetailProps) {
  const [isExpanded, setIsExpanded] = useState(false)

  const getStatusIcon = () => {
    if (step.result === 'pass') {
      return <CheckCircle className="w-4 h-4 text-green-600" />
    } else if (step.result === 'fail') {
      return <XCircle className="w-4 h-4 text-red-600" />
    }
    return <AlertCircle className="w-4 h-4 text-gray-400" />
  }

  const getSeverityColor = (severity?: string) => {
    switch (severity) {
      case 'critical': return 'text-red-700 bg-red-50'
      case 'high': return 'text-red-600 bg-red-50'
      case 'medium': return 'text-yellow-600 bg-yellow-50'
      case 'low': return 'text-blue-600 bg-blue-50'
      default: return 'text-gray-600 bg-gray-50'
    }
  }

  return (
    <div className="border border-gray-200 rounded-lg overflow-hidden">
      {/* 步骤头部 */}
      <div
        className="flex items-center justify-between p-3 cursor-pointer hover:bg-gray-50 transition-colors"
        onClick={() => setIsExpanded(!isExpanded)}
      >
        <div className="flex items-center gap-3">
          {getStatusIcon()}
          <span className="font-medium text-sm">{step.step_name}</span>
          <span className="text-xs px-2 py-1 rounded bg-gray-100 text-gray-600">
            {step.keyword_name}
          </span>
          {step.result === 'pass' && (
            <span className="text-xs px-2 py-1 rounded bg-green-100 text-green-700">
              ✓ 成功
            </span>
          )}
          {step.result === 'fail' && (
            <span className="text-xs px-2 py-1 rounded bg-red-100 text-red-700">
              ✗ 失败
            </span>
          )}
        </div>

        <div className="flex items-center gap-3 text-sm text-gray-500">
          {step.duration && (
            <span className="flex items-center gap-1">
              <Clock className="w-3 h-3" />
              {(step.duration).toFixed(2)}s
            </span>
          )}
          {isExpanded ? (
            <ChevronDown className="w-4 h-4" />
          ) : (
            <ChevronRight className="w-4 h-4" />
          )}
        </div>
      </div>

      {/* 详细信息 */}
      {isExpanded && (
        <div className="p-4 bg-gray-50 space-y-4">
          {/* 参数信息 */}
          {step.parameters && Object.keys(step.parameters).length > 0 && (
            <div>
              <h4 className="text-sm font-medium text-gray-700 mb-2">参数信息</h4>
              <div className="bg-white rounded border p-3">
                <table className="w-full text-sm">
                  <tbody>
                    {Object.entries(step.parameters).map(([key, value]) => (
                      <tr key={key} className="border-b last:border-0">
                        <td className="py-2 px-3 font-medium text-gray-600 w-1/3">{key}</td>
                        <td className="py-2 px-3 text-gray-900 font-mono text-xs">
                          {typeof value === 'object' ? JSON.stringify(value, null, 2) : String(value)}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* 错误信息和建议 */}
          {step.result === 'fail' && (
            <div>
              <h4 className="text-sm font-medium text-gray-700 mb-2">错误详情</h4>

              {/* 错误消息 */}
              <div className="mb-3 p-3 bg-red-50 border border-red-200 rounded">
                <p className="text-sm text-red-800 font-mono whitespace-pre-wrap">{step.error_message}</p>
              </div>

              {/* 失败截图 */}
              {step.screenshot_path && (
                <div className="mb-3">
                  <h5 className="text-xs font-medium text-gray-600 mb-2">失败截图</h5>
                  <div className="border border-gray-300 rounded overflow-hidden">
                    <img
                      src={step.screenshot_path}
                      alt="失败截图"
                      className="w-full"
                      onError={(e) => {
                        e.currentTarget.src = 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjAwIiBoZWlnaHQ9IjE1MCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cmVjdCB3aWR0aD0iMjAwIiBoZWlnaHQ9IjE1MCIgZmlsbD0iI2VjZWNlYyIvPjx0ZXh0IHg9IjUwJSIgeT0iNTAlIiBkb21pbmFudC1iYXNlbGluZT0ibWlkZGxlIiBmb250LXNpemU9IjE0IiBmaWxsPSIjOTk5Ij7lipvvvI7lnKjnva7lm648L3RleHQ+PC9zdmc+'
                      }}
                    />
                  </div>
                </div>
              )}

              {/* 错误分类和建议 */}
              {step.output?.error_suggestion && (
                <div className="p-3 bg-blue-50 border border-blue-200 rounded">
                  <div className="flex items-center gap-2 mb-2">
                    <span className="text-sm font-semibold text-blue-900">
                      💡 {step.output.error_suggestion.title}
                    </span>
                    {step.output.error_severity && (
                      <span className={`text-xs px-2 py-1 rounded ${getSeverityColor(step.output.error_severity)}`}>
                        {step.output.error_severity}
                      </span>
                    )}
                  </div>
                  <p className="text-sm text-blue-800 mb-2">{step.output.error_suggestion.description}</p>
                  <div className="text-sm text-blue-700">
                    <p className="font-medium mb-1">解决方案：</p>
                    <ul className="list-disc list-inside space-y-1">
                      {step.output.error_suggestion.solutions.map((solution, idx) => (
                        <li key={idx}>{solution}</li>
                      ))}
                    </ul>
                  </div>
                </div>
              )}
            </div>
          )}

          {/* 执行日志 */}
          {step.logs && step.logs.length > 0 && (
            <div>
              <h4 className="text-sm font-medium text-gray-700 mb-2">执行日志</h4>
              <div className="bg-gray-900 rounded p-3 max-h-40 overflow-y-auto">
                {step.logs.map((log, idx) => (
                  <div key={idx} className="font-mono text-xs mb-1 last:mb-0">
                    <span className="text-gray-400">{log.timestamp.split('T')[1].split('.')[0]}</span>
                    <span className={`ml-2 ${
                      log.level === 'error' ? 'text-red-400' :
                      log.level === 'warn' ? 'text-yellow-400' :
                      log.level === 'info' ? 'text-blue-400' :
                      'text-gray-400'
                    }`}>
                      [{log.level.toUpperCase()}]
                    </span>
                    <span className="text-gray-300 ml-2">{log.message}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
