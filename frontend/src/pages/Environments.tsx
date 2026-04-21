import React, { useState, useEffect } from 'react'
import { environmentsApi } from '../api/environments'
import { projectsApi } from '../api/projects'
import type { Environment } from '../types/models'
import type { Project } from '../types/models'

const EnvironmentsPage: React.FC = () => {
  const [environments, setEnvironments] = useState<Environment[]>([])
  const [projects, setProjects] = useState<Project[]>([])
  const [loading, setLoading] = useState(true)
  const [message, setMessage] = useState<{type: 'success' | 'error', text: string} | null>(null)
  const [selectedProjectId, setSelectedProjectId] = useState<string>('')
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [newEnvName, setNewEnvName] = useState('')
  const [newEnvBaseUrl, setNewEnvBaseUrl] = useState('')
  const [newEnvVariables, setNewEnvVariables] = useState('')

  // 加载项目列表
  useEffect(() => {
    loadProjects()
  }, [])

  // 加载环境列表
  useEffect(() => {
    if (selectedProjectId) {
      loadEnvironments()
    } else {
      setLoading(false)
    }
  }, [selectedProjectId])

  const loadProjects = async () => {
    try {
      const data = await projectsApi.getProjects()
      setProjects(data)
      // 自动选择第一个项目
      if (data.length > 0 && !selectedProjectId) {
        setSelectedProjectId(data[0].id)
      }
    } catch (error) {
      console.error('加载项目失败:', error)
      showMessage('error', '加载项目列表失败')
      setLoading(false)
    }
  }

  const loadEnvironments = async () => {
    if (!selectedProjectId) {
      setLoading(false)
      return
    }

    try {
      setLoading(true)
      const data = await environmentsApi.getEnvironments(selectedProjectId)
      setEnvironments(data)
    } catch (error) {
      console.error('加载环境配置失败:', error)
      showMessage('error', '加载环境配置失败')
    } finally {
      setLoading(false)
    }
  }

  const showMessage = (type: 'success' | 'error', text: string) => {
    setMessage({ type, text })
    setTimeout(() => setMessage(null), 3000)
  }

  const handleCreateEnvironment = async () => {
    if (!newEnvName.trim()) {
      showMessage('error', '请输入环境名称')
      return
    }

    if (!selectedProjectId) {
      showMessage('error', '请先选择项目')
      return
    }

    try {
      let variables = {}
      try {
        variables = JSON.parse(newEnvVariables)
      } catch {
        variables = {}
      }

      await environmentsApi.createEnvironment({
        project_id: selectedProjectId,
        name: newEnvName,
        base_url: newEnvBaseUrl || undefined,
        variables,
        is_default: false
      })

      showMessage('success', '环境创建成功')
      await loadEnvironments()
      resetForm()
      setShowCreateModal(false)
    } catch (error: any) {
      console.error('创建环境失败:', error)
      const errorMsg = error?.response?.data?.detail || error?.message || '创建环境失败'
      showMessage('error', errorMsg)
    }
  }

  const handleSetDefault = async (envId: string) => {
    try {
      await environmentsApi.setDefaultEnvironment(envId)
      showMessage('success', '默认环境设置成功')
      await loadEnvironments()
    } catch (error: any) {
      console.error('设置默认环境失败:', error)
      const errorMsg = error?.response?.data?.detail || error?.message || '设置默认环境失败'
      showMessage('error', errorMsg)
    }
  }

  const handleDeleteEnvironment = async (envId: string) => {
    const env = environments.find(e => e.id === envId)
    if (env?.is_default) {
      showMessage('error', '不能删除默认环境')
      return
    }

    if (!confirm('确定要删除这个环境配置吗？')) {
      return
    }

    try {
      await environmentsApi.deleteEnvironment(envId)
      showMessage('success', '环境删除成功')
      await loadEnvironments()
    } catch (error: any) {
      console.error('删除环境失败:', error)
      const errorMsg = error?.response?.data?.detail || error?.message || '删除环境失败'
      showMessage('error', errorMsg)
    }
  }

  const resetForm = () => {
    setNewEnvName('')
    setNewEnvBaseUrl('')
    setNewEnvVariables('{}')
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
        <h1 className="text-2xl font-bold">环境配置管理</h1>
        <button
          onClick={() => setShowCreateModal(true)}
          disabled={!selectedProjectId}
          className={`px-4 py-2 rounded ${
            selectedProjectId
              ? 'bg-blue-500 text-white hover:bg-blue-600'
              : 'bg-gray-300 text-gray-500 cursor-not-allowed'
          }`}
        >
          创建环境
        </button>
      </div>

      {/* 项目选择器 */}
      <div className="mb-6">
        <label className="block text-sm font-medium text-gray-700 mb-2">
          选择项目 <span className="text-red-500">*</span>
        </label>
        <select
          value={selectedProjectId}
          onChange={(e) => setSelectedProjectId(e.target.value)}
          className="w-full md:w-64 px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          <option value="">请选择项目</option>
          {projects.map((project) => (
            <option key={project.id} value={project.id}>
              {project.name}
            </option>
          ))}
        </select>
        {projects.length === 0 && (
          <p className="text-sm text-gray-500 mt-1">暂无可用项目</p>
        )}
      </div>

      {loading ? (
        <div className="flex items-center justify-center h-64">
          <div className="text-gray-500">加载中...</div>
        </div>
      ) : (
        <>
          {!selectedProjectId ? (
            <div className="text-center py-12">
              <p className="text-gray-500">请先选择项目以查看环境配置</p>
            </div>
          ) : environments.length === 0 ? (
            <div className="text-center py-12">
              <p className="text-gray-500">暂无环境配置，请创建环境</p>
            </div>
          ) : (
            <div className="space-y-4">
              {environments.map((env) => (
                <div key={env.id} className="border rounded-lg p-4 hover:shadow-md transition-shadow">
                  <div className="flex justify-between items-start">
                    <div className="flex-1">
                      <div className="flex items-center gap-2">
                        <h3 className="text-lg font-semibold">{env.name}</h3>
                        {env.is_default && (
                          <span className="px-2 py-1 bg-green-100 text-green-800 text-xs rounded">
                            默认
                          </span>
                        )}
                      </div>

                      {env.base_url && (
                        <p className="text-sm text-gray-600 mt-1">
                          <strong>Base URL:</strong> {env.base_url}
                        </p>
                      )}

                      {Object.keys(env.variables).length > 0 && (
                        <div className="mt-2">
                          <p className="text-sm font-medium text-gray-700 mb-1">环境变量:</p>
                          <div className="bg-gray-50 rounded p-2 text-xs">
                            {Object.entries(env.variables).map(([key, value]) => (
                              <div key={key} className="flex">
                                <span className="font-medium text-gray-700">{key}:</span>
                                <span className="ml-2 text-gray-600">{String(value)}</span>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}

                      <div className="mt-2 text-xs text-gray-500">
                        创建时间: {new Date(env.created_at).toLocaleString()}
                      </div>
                    </div>

                    <div className="flex space-x-2">
                      {!env.is_default && (
                        <button
                          onClick={() => handleSetDefault(env.id)}
                          className="px-3 py-1 bg-blue-100 text-blue-700 rounded hover:bg-blue-200 text-sm"
                        >
                          设为默认
                        </button>
                      )}
                      <button
                        onClick={() => handleDeleteEnvironment(env.id)}
                        className="px-3 py-1 bg-red-100 text-red-700 rounded hover:bg-red-200 text-sm"
                      >
                        删除
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </>
      )}

      {/* 创建环境模态框 */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-md">
            <h2 className="text-xl font-bold mb-4">创建环境配置</h2>

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  环境名称 <span className="text-red-500">*</span>
                </label>
                <input
                  type="text"
                  value={newEnvName}
                  onChange={(e) => setNewEnvName(e.target.value)}
                  className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="例如: 开发环境"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Base URL
                </label>
                <input
                  type="text"
                  value={newEnvBaseUrl}
                  onChange={(e) => setNewEnvBaseUrl(e.target.value)}
                  className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="https://api.example.com"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  环境变量 (JSON)
                </label>
                <textarea
                  value={newEnvVariables}
                  onChange={(e) => setNewEnvVariables(e.target.value)}
                  className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 font-mono text-sm"
                  placeholder='{"API_KEY": "xxx"}'
                  rows={3}
                />
                <p className="text-xs text-gray-500 mt-1">
                  输入JSON格式的环境变量，例如：{'{"API_KEY": "test123"}'}
                </p>
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
                  onClick={handleCreateEnvironment}
                  className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
                >
                  创建
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
export default EnvironmentsPage
