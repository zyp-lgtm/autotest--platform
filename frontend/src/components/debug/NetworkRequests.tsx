import { useState } from 'react'
import { Globe, AlertCircle, CheckCircle2 } from 'lucide-react'
import type { NetworkRequest } from '../../types/debug'

interface NetworkRequestsProps {
  requests: NetworkRequest[]
}

export default function NetworkRequests({ requests }: NetworkRequestsProps) {
  const [filter, setFilter] = useState<'all' | 'failed' | 'success'>('all')

  if (!requests || requests.length === 0) {
    return <div className="text-gray-500 text-center py-8">没有网络请求记录</div>
  }

  const filteredRequests = requests.filter(req => {
    if (filter === 'all') return true
    if (filter === 'failed') return (req.status || 200) >= 400
    if (filter === 'success') return (req.status || 200) < 400
    return true
  })

  const getStatusIcon = (status?: number) => {
    if (!status) return <CheckCircle className="w-4 h-4 text-gray-400" />
    if (status >= 400) return <AlertCircle className="w-4 h-4 text-red-600" />
    return <CheckCircle className="w-4 h-4 text-green-600" />
  }

  const getStatusColor = (status?: number) => {
    if (!status) return 'text-gray-400'
    if (status >= 400) return 'text-red-600'
    if (status >= 300) return 'text-orange-500'
    return 'text-green-600'
  }

  const formatHeaders = (headers?: Record<string, string>) => {
    if (!headers) return ''
    return Object.entries(headers)
      .filter(([key]) => !['authorization', 'cookie'].includes(key.toLowerCase()))
      .map(([key, value]) => `${key}: ${value}`)
      .join(', ')
  }

  return (
    <div className="space-y-3">
      {/* 过滤器 */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Globe className="w-4 h-4 text-gray-500" />
          <span className="text-sm text-gray-600">网络请求</span>
        </div>
        <select
          value={filter}
          onChange={(e) => setFilter(e.target.value as any)}
          className="px-3 py-1.5 text-sm border border-gray-300 rounded"
        >
          <option value="all">全部 ({filteredRequests.length})</option>
          <option value="success">成功 ({requests.filter(r => !r.status || r.status < 400).length})</option>
          <option value="failed">失败 ({requests.filter(r => r.status && r.status >= 400).length})</option>
        </select>
      </div>

      {/* 请求列表 */}
      <div className="border border-gray-300 rounded-lg overflow-hidden">
        <div className="overflow-x-auto">
          <table className="min-w-full text-sm">
            <thead className="bg-gray-50 border-b border-gray-200">
              <tr>
                <th className="px-3 py-2 text-left font-medium text-gray-700">状态</th>
                <th className="px-3 py-2 text-left font-medium text-gray-700">方法</th>
                <th className="px-3 py-2 text-left font-medium text-gray-700">URL</th>
                <th className="px-3 py-2 text-left font-medium text-gray-700">状态码</th>
                <th className="px-3 py-2 text-left font-medium text-gray-700">类型</th>
                <th className="px-3 py-2 text-left font-medium text-gray-700">大小</th>
              </tr>
            </thead>
            <tbody>
              {filteredRequests.map((req, index) => (
                <tr key={index} className="border-b border-gray-200 hover:bg-gray-50">
                  <td className="px-3 py-2">{getStatusIcon(req.status)}</td>
                  <td className="px-3 py-2 font-mono text-xs">{req.method}</td>
                  <td className="px-3 py-2 max-w-xs truncate" title={req.url}>
                    {req.url}
                  </td>
                  <td className={`px-3 py-2 font-mono text-xs ${getStatusColor(req.status)}`}>
                    {req.status || '-'}
                  </td>
                  <td className="px-3 py-2 text-xs">{req.resource_type}</td>
                  <td className="px-3 py-2 text-xs">
                    {req.response_size ? `${(req.response_size / 1024).toFixed(1)} KB` : '-'}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* 详细信息 */}
      {filteredRequests.length > 0 && (
        <details className="text-xs">
          <summary className="cursor-pointer font-medium text-gray-700 hover:text-gray-900">
            查看请求/响应头（前10个）
          </summary>
          <div className="mt-3 space-y-2 pl-4">
            {filteredRequests.slice(0, 10).map((req, index) => (
              <details key={index} className="group">
                <summary className="cursor-pointer font-mono text-sm hover:underline">
                  {req.method} {req.url}
                </summary>
                <div className="mt-2 pl-4 space-y-1 text-gray-600">
                  <div><span className="font-medium">状态:</span> {req.status || 'N/A'}</div>
                  <div>
                    <span className="font-medium">请求头:</span>
                    <pre className="mt-1 text-xs bg-gray-50 p-2 rounded overflow-x-auto">
                      {formatHeaders(req.headers) || '无'}
                    </pre>
                  </div>
                  {req.response_headers && (
                    <div>
                      <span className="font-medium">响应头:</span>
                      <pre className="mt-1 text-xs bg-gray-50 p-2 rounded overflow-x-auto">
                        {formatHeaders(req.response_headers) || '无'}
                      </pre>
                    </div>
                  )}
                </div>
              </details>
            ))}
          </div>
        </details>
      )}
    </div>
  )
}
