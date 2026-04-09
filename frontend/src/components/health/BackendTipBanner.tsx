/**
 * 后端服务提示横幅组件
 *
 * 当后端服务停止时，显示启动命令提示
 */

interface BackendTipBannerProps {
  onDismiss: () => void
  onRefresh: () => void
}

export function BackendTipBanner({ onDismiss, onRefresh }: BackendTipBannerProps) {
  return (
    <div className="mt-2 bg-yellow-50 border border-yellow-200 rounded-lg p-3 shadow-lg max-w-sm">
      <div className="flex items-start gap-2">
        <span className="text-yellow-600 text-lg">💡</span>
        <div className="flex-1">
          <div className="text-sm font-semibold text-yellow-800 mb-1">后端服务已停止</div>
          <div className="text-xs text-yellow-700 mb-2">在任意终端执行以下命令启动后端：</div>
          <code className="block bg-gray-800 text-green-400 text-xs p-2 rounded overflow-x-auto">
            bash /Users/apple/aicode/.worktrees/test-platform/backend/start_backend.sh
          </code>
          <div className="mt-2 flex gap-2">
            <button
              onClick={() => {
                onDismiss()
                onRefresh()
              }}
              className="text-xs text-yellow-800 underline hover:text-yellow-900"
            >
              我已启动，刷新状态
            </button>
            <button
              onClick={onDismiss}
              className="text-xs text-yellow-800 underline hover:text-yellow-900"
            >
              知道了
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
