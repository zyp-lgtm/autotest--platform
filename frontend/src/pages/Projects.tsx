import React, { useState, useEffect } from 'react'
import { projectsApi } from '../api/projects'
import { environmentsApi } from '../api/environments'
import { testDataApi } from '../api/testData'
import { tasksApi } from '../api/tasks'
import type { Project } from '../types/models'

const ProjectsPage: React.FC = () => {
  const [projects, setProjects] = useState<Project[]>([])
  const [loading, setLoading] = useState(true)
  const [message, setMessage] = useState<{type: 'success' | 'error', text: string} | null>(null)
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [showEditModal, setShowEditModal] = useState(false)
  const [editingProject, setEditingProject] = useState<Project | null>(null)
  const [newProjectName, setNewProjectName] = useState('')
  const [newProjectDescription, setNewProjectDescription] = useState('')
  const [projectStats, setProjectStats] = useState<Record<string, {
    environments: number
    testData: number
    tasks: number
  }>>({})

  // 加载项目列表
  useEffect(() => {
    loadProjects()
  }, [])

  const loadProjects = async () => {
    try {
      setLoading(true)
      const data = await projectsApi.getProjects()
      setProjects(data)

      // 加载每个项目的统计信息
      const stats: Record<string, any> = {}
      for (const project of data) {
        try {
          const [envs, testData, tasks] = await Promise.all([
            environmentsApi.getEnvironments(project.id).catch(() => []),
            testDataApi.getTestDataList(project.id).catch(() => []),
            tasksApi.getTasks(project.id).catch(() => [])
          ])
          stats[project.id] = {
            environments: Array.isArray(envs) ? envs.length : 0,
            testData: Array.isArray(testData) ? testData.length : 0,
            tasks: Array.isArray(tasks) ? tasks.length : 0
          }
        } catch (error) {
          stats[project.id] = { environments: 0, testData: 0, tasks: 0 }
        }
      }
      setProjectStats(stats)
    } catch (error) {
      console.error('加载项目列表失败:', error)
      showMessage('error', '加载项目列表失败')
    } finally {
      setLoading(false)
    }
  }

  const showMessage = (type: 'success' | 'error', text: string) => {
    setMessage({ type, text })
    setTimeout(() => setMessage(null), 3000)
  }

  const handleCreateProject = async () => {
    if (!newProjectName.trim()) {
      showMessage('error', '请输入项目名称')
      return
    }

    try {
      await projectsApi.createProject({
        name: newProjectName,
        description: newProjectDescription
      })

      showMessage('success', '项目创建成功')
      await loadProjects()
      resetForm()
      setShowCreateModal(false)
    } catch (error: any) {
      console.error('创建项目失败:', error)
      const errorMsg = error?.response?.data?.detail || error?.message || '创建项目失败'
      showMessage('error', errorMsg)
    }
  }

  const handleEditProject = async () => {
    if (!editingProject || !newProjectName.trim()) {
      showMessage('error', '请输入项目名称')
      return
    }

    try {
      await projectsApi.updateProject(editingProject.id, {
        name: newProjectName,
        description: newProjectDescription
      })

      showMessage('success', '项目更新成功')
      await loadProjects()
      resetForm()
      setShowEditModal(false)
      setEditingProject(null)
    } catch (error: any) {
      console.error('更新项目失败:', error)
      const errorMsg = error?.response?.data?.detail || error?.message || '更新项目失败'
      showMessage('error', errorMsg)
    }
  }

  const handleDeleteProject = async (projectId: string) => {
    const project = projects.find(p => p.id === projectId)
    const stats = projectStats[projectId]

    // 检查是否有关联数据
    if (stats && (stats.environments > 0 || stats.testData > 0 || stats.tasks > 0)) {
      showMessage('error', `无法删除项目：该项目还有 ${stats.environments} 个环境、${stats.testData} 个测试数据、${stats.tasks} 个任务`)
      return
    }

    if (!confirm(`确定要删除项目"${project?.name}"吗？此操作不可恢复。`)) {
      return
    }

    try {
      await projectsApi.deleteProject(projectId)
      showMessage('success', '项目删除成功')
      await loadProjects()
    } catch (error: any) {
      console.error('删除项目失败:', error)
      const errorMsg = error?.response?.data?.detail || error?.message || '删除项目失败'
      showMessage('error', errorMsg)
    }
  }

  const openEditModal = (project: Project) => {
    setEditingProject(project)
    setNewProjectName(project.name)
    setNewProjectDescription(project.description || '')
    setShowEditModal(true)
  }

  const resetForm = () => {
    setNewProjectName('')
    setNewProjectDescription('')
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-gray-500">加载中...</div>
      </div>
    )
  }

  return (
    <div className="container mx-auto px-4 py-8">
      {/* 消息提示 */}
      {message && (
        <div className={`mb-4 p-4 rounded-lg ${
          message.type === 'success'
            ? 'bg-green-100 text-green-700 border border-green-300'
            : 'bg-red-100 text-red-700 border border-red-300'
        }`}>
          {message.text}
        </div>
      )}

      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold">项目管理</h1>
        <button
          onClick={() => setShowCreateModal(true)}
          className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
        >
          创建项目
        </button>
      </div>

      {projects.length === 0 ? (
        <div className="text-center py-12">
          <p className="text-gray-500 mb-4">暂无项目，请创建一个项目开始使用</p>
          <button
            onClick={() => setShowCreateModal(true)}
            className="px-6 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
          >
            创建第一个项目
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {projects.map((project) => {
            const stats = projectStats[project.id] || { environments: 0, testData: 0, tasks: 0 }
            return (
              <div key={project.id} className="border rounded-lg p-4 hover:shadow-md transition-shadow">
                <div className="flex justify-between items-start mb-2">
                  <h3 className="text-lg font-semibold">{project.name}</h3>
                  <button
                    onClick={() => openEditModal(project)}
                    className="text-blue-500 hover:text-blue-700 text-sm"
                  >
                    编辑
                  </button>
                </div>

                <p className="text-gray-600 text-sm mb-3">
                  {project.description || '暂无描述'}
                </p>

                {/* 项目统计 */}
                <div className="grid grid-cols-3 gap-2 text-xs mb-3">
                  <div className="bg-gray-50 rounded p-2 text-center">
                    <div className="font-medium text-gray-700">{stats.environments}</div>
                    <div className="text-gray-500">环境</div>
                  </div>
                  <div className="bg-gray-50 rounded p-2 text-center">
                    <div className="font-medium text-gray-700">{stats.testData}</div>
                    <div className="text-gray-500">数据</div>
                  </div>
                  <div className="bg-gray-50 rounded p-2 text-center">
                    <div className="font-medium text-gray-700">{stats.tasks}</div>
                    <div className="text-gray-500">任务</div>
                  </div>
                </div>

                <div className="flex justify-between items-center">
                  <span className="text-xs text-gray-500">
                    创建时间: {new Date(project.created_at).toLocaleDateString()}
                  </span>
                  <button
                    onClick={() => handleDeleteProject(project.id)}
                    className="text-red-500 hover:text-red-700 text-sm"
                  >
                    删除
                  </button>
                </div>
              </div>
            )
          })}
        </div>
      )}

      {/* 创建项目模态框 */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-md">
            <h2 className="text-xl font-bold mb-4">创建项目</h2>

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  项目名称 <span className="text-red-500">*</span>
                </label>
                <input
                  type="text"
                  value={newProjectName}
                  onChange={(e) => setNewProjectName(e.target.value)}
                  className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="例如: Web测试项目"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  项目描述
                </label>
                <textarea
                  value={newProjectDescription}
                  onChange={(e) => setNewProjectDescription(e.target.value)}
                  className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="简要描述项目用途和目标"
                  rows={3}
                />
              </div>

              <div className="flex justify-end space-x-2">
                <button
                  onClick={() => {
                    setShowCreateModal(false)
                    resetForm()
                  }}
                  className="px-4 py-2 border rounded hover:bg-gray-50"
                >
                  取消
                </button>
                <button
                  onClick={handleCreateProject}
                  className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
                >
                  创建
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* 编辑项目模态框 */}
      {showEditModal && editingProject && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-md">
            <h2 className="text-xl font-bold mb-4">编辑项目</h2>

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  项目名称 <span className="text-red-500">*</span>
                </label>
                <input
                  type="text"
                  value={newProjectName}
                  onChange={(e) => setNewProjectName(e.target.value)}
                  className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="项目名称"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  项目描述
                </label>
                <textarea
                  value={newProjectDescription}
                  onChange={(e) => setNewProjectDescription(e.target.value)}
                  className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="项目描述"
                  rows={3}
                />
              </div>

              <div className="flex justify-end space-x-2">
                <button
                  onClick={() => {
                    setShowEditModal(false)
                    resetForm()
                    setEditingProject(null)
                  }}
                  className="px-4 py-2 border rounded hover:bg-gray-50"
                >
                  取消
                </button>
                <button
                  onClick={handleEditProject}
                  className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
                >
                  保存
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default ProjectsPage
