import { useState } from 'react'
import { AlertCircle, AlertTriangle, Info, Terminal, Filter, ChevronDown, ChevronRight } from 'lucide-react'
import type { ConsoleMessage } from '../../types/debug'

interface ConsoleLogsProps {
  logs: ConsoleMessage[]
}

export default function ConsoleLogs({ logs }: ConsoleLogsProps) {
  const [filter, setFilter] = useState<'all' | 'error' | 'warning' | 'info' | 'log'>('all')
  const [expandedLog, setExpandedLog] = useState<Set<number>>(new Set())

  if (!logs || logs.length === 0) {
    return <div className="text-gray-500 text-center py-8">没有控制台日志</div>
  }

  const filteredLogs = logs.filter(log => {
    if (filter === 'all') return true
    return log.type === filter
  })

  const getIcon = (type: string) => {
    switch (type) {
      case 'error':
        return <AlertCircle className="w-4 h-4 text-red-600" />
      case 'warning':
        return <AlertTriangle className="w-4 h-4 text-orange-500" />
      case 'info':
        return <Info className="w-4 h-4 text-blue-500" />
      default:
        return <Terminal className="w-4 h-4 text-gray-600" />
    }
  }

  const getBgColor = (type: string) => {
    switch (type) {
      case 'error':
        return 'bg-red-50 border-red-200'
      case 'warning':
        return 'bg-orange-50 border-orange-200'
      case 'info':
        return 'bg-blue-50 border-blue-200'
      default:
        return 'bg-gray-50 border-gray-200'
    }
  }

  const toggleExpand = (index: number) => {
    const newExpanded = new Set(expandedLog)
    if (newExpanded.has(index)) {
      newExpanded.delete(index)
    } else {
      newExpanded.add(index)
    }
    setExpandedLog(newExpanded)
  }

  return (
    <div className="space-y-3">
      {/* 过滤器 */}
      <div className="flex items-center gap-2">
        <Filter className="w-4 h-4 text-gray-500" />
        <select
          value={filter}
          onChange={(e) => setFilter(e.target.value as any)}
          className="px-3 py-1.5 text-sm border border-gray-300 rounded"
        >
          <option value="all">全部 ({filteredLogs.length})</option>
          <option value="error">错误 ({logs.filter(l => l.type === 'error').length})</option>
          <option value="warning">警告 ({logs.filter(l => l.type === 'warning').length})</option>
          <option value="info">信息 ({logs.filter(l => l.type === 'info').length})</option>
          <option value="log">日志 ({logs.filter(l => l.type === 'log').length})</option>
        </select>
      </div>

      {/* 日志列表 */}
      <div className="space-y-2 max-h-[500px] overflow-y-auto">
        {filteredLogs.map((log, index) => (
          <div
            key={index}
            className={`border rounded-lg overflow-hidden ${getBgColor(log.type)}`}
          >
            {/* 日志头部（可点击展开） */}
            <button
              onClick={() => toggleExpand(index)}
              className="w-full px-3 py-2 flex items-start gap-2 hover:bg-opacity-50 transition-colors text-left"
            >
              <div className="flex-shrink-0 mt-0.5">
                {expandedLog.has(index) ? (
                  <ChevronDown className="w-3 h-3 text-gray-500" />
                ) : (
                  <ChevronRight className="w-3 h-3 text-gray-500" />
                )}
              </div>
              <div className="flex-grow">
                <div className="flex items-center gap-2">
                  {getIcon(log.type)}
                  <span className="font-mono text-sm break-all">{log.text}</span>
                </div>
                {log.location && expandedLog.has(index) && (
                  <div className="text-xs text-gray-500 mt-1">
                    位置: {log.location}
                  </div>
                )}
              </div>
            </button>

            {/* 详细信息 */}
            {expandedLog.has(index) && (
              <div className="px-3 pb-2 text-xs space-y-1 border-t border-gray-300 border-opacity-50 pt-2">
                <div><span className="font-medium">类型:</span> {log.type}</div>
                <div><span className="font-medium">时间:</span> {log.timestamp}</div>
                {log.location && <div><span className="font-medium">位置:</span> {log.location}</div>}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  )
}
