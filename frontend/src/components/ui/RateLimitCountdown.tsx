/**
 * 速率限制倒计时组件
 * 当触发速率限制时显示剩余等待时间
 */

import { useState, useEffect } from 'react'
import { AlertCircle } from 'lucide-react'

interface RateLimitCountdownProps {
  retryAfter: number
  onRetry?: () => void
}

export function RateLimitCountdown({ retryAfter, onRetry }: RateLimitCountdownProps) {
  const [secondsLeft, setSecondsLeft] = useState(retryAfter)

  useEffect(() => {
    if (secondsLeft <= 0) {
      // 倒计时结束
      if (onRetry) {
        onRetry()
      }
      return
    }

    // 每秒更新倒计时
    const timer = setInterval(() => {
      setSecondsLeft((prev) => {
        if (prev <= 1) {
          clearInterval(timer)
          return 0
        }
        return prev - 1
      })
    }, 1000)

    return () => clearInterval(timer)
  }, [secondsLeft, onRetry])

  if (secondsLeft <= 0) {
    return (
      <div className="bg-green-50 text-green-700 p-4 rounded-lg flex items-center gap-3">
        <AlertCircle className="w-5 h-5" />
        <div>
          <p className="font-medium">可以重试了</p>
          <p className="text-sm">现在可以重新提交注册请求</p>
        </div>
      </div>
    )
  }

  return (
    <div className="bg-yellow-50 border border-yellow-200 text-yellow-800 p-4 rounded-lg">
      <div className="flex items-start gap-3">
        <AlertCircle className="w-5 h-5 mt-0.5 flex-shrink-0" />
        <div className="flex-1">
          <p className="font-medium">请求过于频繁</p>
          <p className="text-sm mt-1">
            为保护系统安全，请等待
            <span className="inline-flex items-center justify-center mx-1 px-2 py-0.5 bg-yellow-100 rounded-md font-mono font-bold text-yellow-900">
              {secondsLeft}
            </span>
            秒后再试
          </p>
          <div className="mt-3 bg-yellow-100 rounded-full h-2 overflow-hidden">
            <div
              className="bg-yellow-500 h-full transition-all duration-1000 ease-linear"
              style={{
                width: `${((retryAfter - secondsLeft) / retryAfter) * 100}%`
              }}
            />
          </div>
        </div>
      </div>
    </div>
  )
}
