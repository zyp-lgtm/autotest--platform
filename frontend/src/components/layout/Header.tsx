import { Link, useLocation } from 'react-router-dom'
import { useAuth } from '../../hooks/useAuth'

export function Header() {
  const { user, logout } = useAuth()
  const location = useLocation()

  const navItems = [
    { path: '/', label: '仪表盘' },
    { path: '/tasks', label: '任务管理' },
  ]

  return (
    <header className="bg-white shadow">
      <div className="max-w-7xl mx-auto px-4 py-4">
        {/* Top row: Logo and navigation */}
        <div className="flex justify-between items-center">
          <h1 className="text-xl font-bold text-gray-900">测试自动化平台</h1>

          {/* Navigation */}
          {user && (
            <nav className="flex items-center gap-6">
              {navItems.map((item) => (
                <Link
                  key={item.path}
                  to={item.path}
                  className={`text-sm font-medium transition ${
                    location.pathname === item.path
                      ? 'text-blue-600'
                      : 'text-gray-600 hover:text-gray-900'
                  }`}
                >
                  {item.label}
                </Link>
              ))}
            </nav>
          )}
        </div>

        {/* Bottom row: User info */}
        {user && (
          <div className="flex justify-end items-center mt-3 pt-3 border-t border-gray-100">
            <span className="text-sm text-gray-600 mr-4">欢迎, {user.username}</span>
            <button
              onClick={logout}
              className="px-4 py-1.5 text-sm border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition"
            >
              退出
            </button>
          </div>
        )}
      </div>
    </header>
  )
}
