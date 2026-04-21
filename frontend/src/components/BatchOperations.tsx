import React, { useState } from 'react'
import { batchApi } from '../api/batch'
import type { BatchPreviewResult, BatchOperationResult } from '../types/models'

interface BatchOperationsProps {
  itemType: 'scenarios' | 'tasks'
  selectedIds: string[]
  onOperationComplete?: () => void
}

export const BatchOperations: React.FC<BatchOperationsProps> = ({
  itemType,
  selectedIds,
  onOperationComplete
}) => {
  const [previewData, setPreviewData] = useState<BatchPreviewResult | null>(null)
  const [operation, setOperation] = useState<string>('')
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<BatchOperationResult | null>(null)

  const handlePreview = async (operationType: string) => {
    if (selectedIds.length === 0) {
      alert('请先选择要操作的项目')
      return
    }

    try {
      setLoading(true)
      setOperation(operationType)
      const data = await batchApi.previewBatchOperation(operationType, selectedIds, itemType)
      setPreviewData(data)
    } catch (error) {
      console.error('预览批量操作失败:', error)
      alert('预览失败，请检查连接')
    } finally {
      setLoading(false)
    }
  }

  const handleExecute = async () => {
    if (!previewData) {
      return
    }

    if (previewData.warnings.length > 0) {
      // 如果有警告，确认是否继续
      if (!confirm(`操作包含 ${previewData.warnings.length} 个警告，是否继续？`)) {
        return
      }
    }

    try {
      setLoading(true)

      let response: BatchOperationResult

      switch (operation) {
        case 'enable':
          response = await batchApi.batchEnableScenarios(selectedIds)
          break
        case 'disable':
          response = await batchApi.batchDisableScenarios(selectedIds)
          break
        case 'delete':
          response = await batchApi.batchDeleteScenarios(selectedIds)
          break
        case 'export':
          response = await batchApi.batchExportScenarios(selectedIds)
          break
        default:
          throw new Error('未知的操作类型')
      }

      setResult(response)

      if (response.success) {
        alert(response.message)
        onOperationComplete?.()
      } else {
        alert('操作失败: ' + response.message)
      }

      // 清理状态
      setPreviewData(null)
      setResult(null)
    } catch (error) {
      console.error('执行批量操作失败:', error)
      alert('执行失败，请检查连接')
    } finally {
      setLoading(false)
    }
  }

  if (selectedIds.length === 0) {
    return null
  }

  return (
    <div className="border rounded-lg p-4 bg-gray-50">
      <h3 className="text-lg font-semibold mb-4">批量操作 ({selectedIds.length} 项已选)</h3>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-2 mb-4">
        <button
          onClick={() => handlePreview('enable')}
          disabled={loading}
          className="px-3 py-2 bg-green-500 text-white rounded hover:bg-green-600 disabled:opacity-50 text-sm"
        >
          批量启用
        </button>
        <button
          onClick={() => handlePreview('disable')}
          disabled={loading}
          className="px-3 py-2 bg-yellow-500 text-white rounded hover:bg-yellow-600 disabled:opacity-50 text-sm"
        >
          批量禁用
        </button>
        <button
          onClick={() => handlePreview('delete')}
          disabled={loading}
          className="px-3 py-2 bg-red-500 text-white rounded hover:bg-red-600 disabled:opacity-50 text-sm"
        >
          批量删除
        </button>
        <button
          onClick={() => handlePreview('export')}
          disabled={loading}
          className="px-3 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 disabled:opacity-50 text-sm"
        >
          批量导出
        </button>
      </div>

      {/* 预览结果 */}
      {previewData && (
        <div className="bg-white rounded-lg p-4">
          <h4 className="font-semibold mb-2">操作预览</h4>

          {previewData.warnings.length > 0 && (
            <div className="mb-4">
              <p className="text-sm font-medium text-yellow-700 mb-2">警告:</p>
              <ul className="list-disc list-inside text-sm text-yellow-600">
                {previewData.warnings.map((warning, index) => (
                  <li key={index}>{warning}</li>
                ))}
              </ul>
            </div>
          )}

          <div className="mb-4">
            <p className="text-sm font-medium text-gray-700 mb-2">
              影响项目 ({previewData.total_items} 个):
            </p>
            <div className="max-h-40 overflow-y-auto border rounded p-2">
              {previewData.items.map((item) => (
                <div key={item.id} className="text-sm py-1 border-b last:border-0">
                  {item.name} {item.warning && <span className="text-yellow-600 ml-2">{item.warning}</span>}
                </div>
              ))}
            </div>
          </div>

          <div className="flex justify-end space-x-2">
            <button
              onClick={() => setPreviewData(null)}
              className="px-4 py-2 border rounded hover:bg-gray-50"
            >
              取消
            </button>
            <button
              onClick={handleExecute}
              disabled={loading}
              className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 disabled:opacity-50"
            >
              {loading ? '执行中...' : '确认执行'}
            </button>
          </div>
        </div>
      )}

      {/* 执行结果 */}
      {result && (
        <div className={`rounded-lg p-4 ${result.success ? 'bg-green-50' : 'bg-red-50'}`}>
          <p className={`font-medium ${result.success ? 'text-green-800' : 'text-red-800'}`}>
            {result.message}
          </p>
          <div className="text-sm text-gray-600 mt-2">
            请求: {result.total_requested} |
            成功: {result.success ? (result.enabled_count || result.deleted_count || result.exported_count) : 0} |
            失败: {result.not_found_count || 0}
          </div>
        </div>
      )}
    </div>
  )
}
