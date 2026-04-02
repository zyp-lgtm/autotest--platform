import React from 'react'
import { useAuth } from '../../hooks/useAuth'

export function Header() {
  const { user, logout } = useAuth()

  return (
    <header className="bg-white shadow">
      <div className="max-w-7xl mx-auto px-4 py-4 flex justify-between items-center">
        <h1 className="text-xl font-bold text-gray-900">测试自动化平台</h1>

        <div className="flex items-center gap-4">
          {user ? (
            <>
              <span className="text-sm text-gray-600">欢迎, {user.username}</span>
              <button
                onClick={logout}
                className="px-4 py-2 text-sm text-gray-700 hover:text-gray-900"
              >
                退出
              </button>
            </>
          ) : (
            <a
              href="/login"
              className="px-4 py-2 bg-blue-600 text-white rounded-lg text-sm hover:bg-blue-700"
            >
              登录
            </a>
          )}
        </div>
      </div>
    </header>
  )
}
