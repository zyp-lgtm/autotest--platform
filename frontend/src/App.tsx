import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { AuthProvider, useAuth } from './contexts/AuthContext'
import { ProjectProvider } from './contexts/ProjectContext'
import { Layout } from './components/layout/Layout'
import { lazy, Suspense } from 'react'

// 懒加载页面组件
const Dashboard = lazy(() => import('./pages/Dashboard'))
const LoginPage = lazy(() => import('./pages/Login'))
const RegisterPage = lazy(() => import('./pages/Register'))
const Tasks = lazy(() => import('./pages/Tasks'))
const TaskForm = lazy(() => import('./components/TaskForm'))
const ExecutionReportPage = lazy(() => import('./pages/ExecutionReport'))
const Scenarios = lazy(() => import('./pages/Scenarios'))

// 懒加载组件的加载指示器
function LazyLoader() {
  return <div className="min-h-screen flex items-center justify-center">加载中...</div>
}

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { user, loading } = useAuth()

  if (loading) {
    return <div className="min-h-screen flex items-center justify-center">加载中...</div>
  }

  if (!user) {
    return <Navigate to="/login" replace />
  }

  return <>{children}</>
}

function App() {
  return (
    <AuthProvider>
      <ProjectProvider>
        <BrowserRouter>
          <Suspense fallback={<LazyLoader />}>
            <Routes>
              <Route path="/login" element={<LoginPage />} />
              <Route path="/register" element={<RegisterPage />} />
              <Route
                path="/*"
                element={
                  <ProtectedRoute>
                    <Layout>
                      <Routes>
                        <Route path="/" element={<Dashboard />} />
                        <Route path="/tasks" element={<Tasks />} />
                        <Route path="/tasks/new" element={<TaskForm mode="create" />} />
                        <Route path="/tasks/:taskId/edit" element={<TaskForm mode="edit" />} />
                        <Route path="/tasks/:taskId/scenarios" element={<Scenarios />} />
                        <Route path="/executions/:executionId" element={<ExecutionReportPage />} />
                        {/* 未来添加更多路由 */}
                      </Routes>
                    </Layout>
                  </ProtectedRoute>
                }
              />
            </Routes>
          </Suspense>
        </BrowserRouter>
      </ProjectProvider>
    </AuthProvider>
  )
}

export default App
