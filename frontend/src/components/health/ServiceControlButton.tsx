/**
 * 服务控制按钮组件
 *
 * 用于启动、重启、停止服务的按钮
 */

interface ServiceControlButtonProps {
  status: 'healthy' | 'degraded' | 'down'
  isOperating: boolean
  onStart: () => void
  onRestart: () => void
  onStop: () => void
}

export function ServiceControlButton({
  status,
  isOperating,
  onStart,
  onRestart,
  onStop
}: ServiceControlButtonProps) {
  // 服务停止时，只显示启动按钮
  if (status === 'down') {
    return (
      <button
        onClick={onStart}
        disabled={isOperating}
        className="px-2 py-1 text-xs bg-green-600 text-white rounded hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed"
        title="启动服务"
      >
        {isOperating ? '启动中...' : '启动'}
      </button>
    )
  }

  // 服务运行时，显示重启和停止按钮
  return (
    <>
      <button
        onClick={onRestart}
        disabled={isOperating}
        className="px-2 py-1 text-xs bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
        title="重启服务"
      >
        {isOperating ? '重启中...' : '重启'}
      </button>
      <button
        onClick={onStop}
        disabled={isOperating}
        className="px-2 py-1 text-xs bg-red-600 text-white rounded hover:bg-red-700 disabled:opacity-50 disabled:cursor-not-allowed"
        title="停止服务"
      >
        停止
      </button>
    </>
  )
}
