import { useState } from 'react'
import { ChevronDown, ChevronRight, Bug, Download, FileText, Terminal, Globe } from 'lucide-react'
import type { DebugInfo } from '../../types/debug'
import ScreenshotViewer from './ScreenshotViewer'
import ConsoleLogs from './ConsoleLogs'
import NetworkRequests from './NetworkRequests'
import ExecutionSteps from './ExecutionSteps'

interface DebugPanelProps {
  debugInfo: DebugInfo
  defaultOpen?: boolean
}

type TabType = 'screenshot' | 'console' | 'network' | 'steps' | 'html'

export default function DebugPanel({ debugInfo, defaultOpen = false }: DebugPanelProps) {
  const [isOpen, setIsOpen] = useState(defaultOpen)
  const [activeTab, setActiveTab] = useState<TabType>('screenshot')

  const tabs = [
    { id: 'screenshot' as TabType, label: '截图', icon: Bug },
    { id: 'console' as TabType, label: '控制台', icon: Terminal },
    { id: 'network' as TabType, label: '网络', icon: Globe },
    { id: 'steps' as TabType, label: '步骤', icon: FileText },
    { id: 'html' as TabType, label: 'HTML', icon: FileText },
  ]

  const renderTab = () => {
    switch (activeTab) {
      case 'screenshot':
        return <ScreenshotViewer screenshotPath={debugInfo.screenshot} />
      case 'console':
        return <ConsoleLogs logs={debugInfo.console_logs} />
      case 'network':
        return <NetworkRequests requests={debugInfo.network_requests} />
      case 'steps':
        return <ExecutionSteps steps={debugInfo.execution_steps} />
      case 'html':
        return <HTMLSnapshotViewer htmlPath={debugInfo.html_snapshot} />
      default:
        return <div className="text-gray-500">选择一个标签页查看调试信息</div>
    }
  }

  return (
    <div className="border border-red-200 rounded-lg bg-red-50">
      {/* 标题栏 */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="w-full px-4 py-3 flex items-center justify-between hover:bg-red-100 transition-colors"
      >
        <div className="flex items-center gap-2">
          <Bug className="w-5 h-5 text-red-600" />
          <span className="font-semibold text-red-900">调试信息</span>
          {debugInfo.step_name && (
            <span className="text-sm text-red-600">- {debugInfo.step_name}</span>
          )}
        </div>
        {isOpen ? (
          <ChevronDown className="w-5 h-5 text-red-600" />
        ) : (
          <ChevronRight className="w-5 h-5 text-red-600" />
        )}
      </button>

      {/* 内容 */}
      {isOpen && (
        <div className="border-t border-red-200">
          {/* 标签页 */}
          <div className="flex border-b border-red-200 bg-red-100">
            {tabs.map((tab) => {
              const Icon = tab.icon
              const isActive = activeTab === tab.id

              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`px-4 py-2 flex items-center gap-2 text-sm font-medium transition-colors ${
                    isActive
                      ? 'bg-red-200 text-red-900 border-b-2 border-red-600'
                      : 'text-red-700 hover:bg-red-200'
                  }`}
                >
                  <Icon className="w-4 h-4" />
                  {tab.label}
                  {tab.id === 'console' && debugInfo.console_logs?.length > 0 && (
                    <span className="ml-1 px-1.5 py-0.5 bg-orange-500 text-white text-xs rounded-full">
                      {debugInfo.console_logs.length}
                    </span>
                  )}
                  {tab.id === 'network' && debugInfo.network_requests?.length > 0 && (
                    <span className="ml-1 px-1.5 py-0.5 bg-blue-500 text-white text-xs rounded-full">
                      {debugInfo.network_requests.length}
                    </span>
                  )}
                </button>
              )
            })}
          </div>

          {/* 标签页内容 */}
          <div className="p-4 bg-white">
            {renderTab()}
          </div>

          {/* 报告下载按钮 */}
          {debugInfo.report_path && (
            <div className="px-4 py-2 bg-red-50 border-t border-red-200">
              <button
                onClick={() => {
                  window.open(`/api/v1/files/debug?path=${debugInfo.report_path}`, '_blank')
                }}
                className="text-sm text-red-600 hover:text-red-800 underline flex items-center gap-1"
              >
                <Download className="w-4 h-4" />
                下载完整调试报告（JSON）
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

// HTML 快照查看器
function HTMLSnapshotViewer({ htmlPath }: { htmlPath?: string }) {
  if (!htmlPath) {
    return <div className="text-gray-500 text-center py-8">HTML 快照不可用</div>
  }

  return (
    <div className="space-y-3">
      <p className="text-sm text-gray-600">HTML 页面快照（失败时的页面结构）</p>
      <div className="flex gap-2">
        <button
          onClick={() => window.open(`/api/v1/files/debug?path=${htmlPath}`, '_blank')}
          className="px-3 py-1.5 text-sm bg-gray-100 hover:bg-gray-200 border border-gray-300 rounded"
        >
          在新窗口打开
        </button>
        <button
          onClick={() => {
            fetch(`/api/v1/files/debug?path=${htmlPath}`)
              .then(r => r.text())
              .then(html => {
                const blob = new Blob([html], { type: 'text/html' })
                const url = URL.createObjectURL(blob)
                window.open(url, '_blank')
              })
          }}
          className="px-3 py-1.5 text-sm bg-blue-500 text-white hover:bg-blue-600 rounded"
        >
          下载 HTML 文件
        </button>
      </div>
      <pre className="text-xs text-gray-500">
        路径: {htmlPath}
      </pre>
    </div>
  )
}
