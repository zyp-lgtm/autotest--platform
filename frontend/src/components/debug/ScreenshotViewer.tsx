import { useState } from 'react'
import { ZoomIn, ZoomOut, Download, Maximize2 } from 'lucide-react'

interface ScreenshotViewerProps {
  screenshotPath?: string
}

export default function ScreenshotViewer({ screenshotPath }: ScreenshotViewerProps) {
  const [zoom, setZoom] = useState(1)
  const [isLoading, setIsLoading] = useState(false)

  if (!screenshotPath) {
    return <div className="text-gray-500 text-center py-8">没有可用的截图</div>
  }

  const handleDownload = () => {
    window.open(`/api/v1/files/debug?path=${screenshotPath}`, '_blank')
  }

  const handleZoomIn = () => setZoom(prev => Math.min(prev + 0.25, 3))
  const handleZoomOut = () => setZoom(prev => Math.max(prev - 0.25, 0.5))

  return (
    <div className="space-y-4">
      {/* 工具栏 */}
      <div className="flex items-center justify-between">
        <div className="flex gap-2">
          <button
            onClick={handleZoomOut}
            disabled={zoom <= 0.5}
            className="p-2 bg-gray-100 hover:bg-gray-200 border border-gray-300 rounded disabled:opacity-50"
            title="缩小"
          >
            <ZoomOut className="w-4 h-4" />
          </button>
          <span className="px-3 py-1 bg-gray-100 border border-gray-300 rounded min-w-[60px] text-center">
            {Math.round(zoom * 100)}%
          </span>
          <button
            onClick={handleZoomIn}
            disabled={zoom >= 3}
            className="p-2 bg-gray-100 hover:bg-gray-200 border border-gray-300 rounded disabled:opacity-50"
            title="放大"
          >
            <ZoomIn className="w-4 h-4" />
          </button>
        </div>
        <div className="flex gap-2">
          <button
            onClick={() => setZoom(1)}
            className="px-3 py-1 text-sm bg-gray-100 hover:bg-gray-200 border border-gray-300 rounded"
          >
            重置
          </button>
          <button
            onClick={handleDownload}
            className="px-3 py-1 text-sm bg-blue-500 text-white hover:bg-blue-600 rounded flex items-center gap-1"
          >
            <Download className="w-4 h-4" />
            下载
          </button>
        </div>
      </div>

      {/* 图片预览 */}
      <div className="border border-gray-300 rounded overflow-hidden bg-gray-50">
        <div
          className="overflow-auto"
          style={{ maxHeight: '600px' }}
        >
          <img
            src={`/api/v1/files/debug?path=${screenshotPath}`}
            alt="失败截图"
            className="w-full"
            style={{ transform: `scale(${zoom})`, transformOrigin: 'top left' }}
            onLoad={() => setIsLoading(false)}
            onError={() => setIsLoading(false)}
          />
        </div>
        {isLoading && (
          <div className="absolute inset-0 flex items-center justify-center bg-gray-100">
            <div className="text-gray-500">加载中...</div>
          </div>
        )}
      </div>

      {/* 文件路径 */}
      <div className="text-xs text-gray-500">
        {screenshotPath}
      </div>
    </div>
  )
}
