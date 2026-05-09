import React, { useState, useEffect } from 'react'
import { testDataApi } from '../api/testData'
import { projectsApi } from '../api/projects'
import type { TestData } from '../types/models'
import type { Project } from '../types/models'

// 项目统计信息
interface ProjectWithStats extends Project {
  testDataCount?: number
}

const TestDataPage: React.FC = () => {
  const [testDataList, setTestDataList] = useState<TestData[]>([])
  const [projects, setProjects] = useState<ProjectWithStats[]>([])
  const [projectStats, setProjectStats] = useState<Record<string, number>>({})
  const [loading, setLoading] = useState(true)
  const [message, setMessage] = useState<{type: 'success' | 'error', text: string} | null>(null)
  const [selectedProjectId, setSelectedProjectId] = useState<string>('')
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [showViewModal, setShowViewModal] = useState(false)
  const [showEditModal, setShowEditModal] = useState(false)
  const [viewingData, setViewingData] = useState<TestData | null>(null)
  const [editingData, setEditingData] = useState<TestData | null>(null)
  const [newDataName, setNewDataName] = useState('')
  const [newDataDescription, setNewDataDescription] = useState('')
  const [newDataJson, setNewDataJson] = useState('[\n  {"username": "test1", "password": "pass1"}\n]')
  const [editDataJson, setEditDataJson] = useState('')

  // 加载项目列表
  useEffect(() => {
    loadProjects()
  }, [])

  // 加载测试数据列表
  useEffect(() => {
    if (selectedProjectId) {
      loadTestData()
    } else {
      setLoading(false)
    }
  }, [selectedProjectId])

  const loadProjects = async () => {
    try {
      const data = await projectsApi.getProjects()

      // 获取每个项目的测试数据统计
      const stats: Record<string, number> = {}
      for (const project of data) {
        try {
          const testData = await testDataApi.getTestDataList(project.id)
          stats[project.id] = testData.length
        } catch {
          stats[project.id] = 0
        }
      }

      setProjectStats(stats)
      setProjects(data as ProjectWithStats[])

      // 自动选择第一个有数据的项目，否则选择第一个项目
      if (data.length > 0 && !selectedProjectId) {
        const firstProjectWithData = data.find(p => stats[p.id] > 0)
        setSelectedProjectId(firstProjectWithData?.id || data[0].id)
      }
    } catch (error) {
      console.error('加载项目失败:', error)
      showMessage('error', '加载项目列表失败')
      setLoading(false)
    }
  }

  const loadTestData = async () => {
    if (!selectedProjectId) {
      setLoading(false)
      return
    }

    try {
      setLoading(true)
      const data = await testDataApi.getTestDataList(selectedProjectId)
      setTestDataList(data)
    } catch (error) {
      console.error('加载测试数据失败:', error)
      showMessage('error', '加载测试数据失败')
    } finally {
      setLoading(false)
    }
  }

  const showMessage = (type: 'success' | 'error', text: string) => {
    setMessage({ type, text })
    setTimeout(() => setMessage(null), 3000)
  }

  const handleCreateTestData = async () => {
    if (!newDataName.trim()) {
      showMessage('error', '请输入数据名称')
      return
    }

    if (!newDataJson.trim()) {
      showMessage('error', '请输入JSON数据')
      return
    }

    if (!selectedProjectId) {
      showMessage('error', '请先选择项目')
      return
    }

    try {
      const parsedData = JSON.parse(newDataJson)
      await testDataApi.createTestData({
        project_id: selectedProjectId,
        name: newDataName,
        description: newDataDescription,
        data_type: 'json',
        data: parsedData,
        tags: []
      })

      showMessage('success', '测试数据创建成功')
      await loadTestData()
      await loadProjects() // 更新项目统计
      resetForm()
      setShowCreateModal(false)
    } catch (error: any) {
      console.error('创建测试数据失败:', error)
      if (error instanceof SyntaxError) {
        showMessage('error', 'JSON格式错误，请检查输入')
      } else {
        const errorMsg = error?.response?.data?.detail || error?.message || '创建测试数据失败'
        showMessage('error', errorMsg)
      }
    }
  }

  const handleDeleteTestData = async (dataId: string) => {
    if (!confirm('确定要删除这个测试数据吗？')) {
      return
    }

    try {
      await testDataApi.deleteTestData(dataId)
      showMessage('success', '测试数据删除成功')
      await loadTestData()
      await loadProjects() // 更新项目统计
    } catch (error: any) {
      console.error('删除测试数据失败:', error)
      const errorMsg = error?.response?.data?.detail || error?.message || '删除测试数据失败'
      showMessage('error', errorMsg)
    }
  }

  const handleViewData = (data: TestData) => {
    setViewingData(data)
    setShowViewModal(true)
  }

  const handleEditData = (data: TestData) => {
    setEditingData(data)
    setEditDataJson(JSON.stringify(data.data, null, 2))
    setShowEditModal(true)
  }

  const handleUpdateData = async () => {
    if (!editingData) return

    try {
      const parsedData = JSON.parse(editDataJson)
      await testDataApi.updateTestData(editingData.id, {
        name: editingData.name,
        description: editingData.description,
        data_type: editingData.data_type,
        data: parsedData,
        tags: editingData.tags
      })

      showMessage('success', '测试数据更新成功')
      await loadTestData()
      await loadProjects() // 更新项目统计
      setShowEditModal(false)
      setEditingData(null)
    } catch (error: any) {
      console.error('更新测试数据失败:', error)
      if (error instanceof SyntaxError) {
        showMessage('error', 'JSON格式错误，请检查输入')
      } else {
        const errorMsg = error?.response?.data?.detail || error?.message || '更新测试数据失败'
        showMessage('error', errorMsg)
      }
    }
  }

  const resetForm = () => {
    setNewDataName('')
    setNewDataDescription('')
    setNewDataJson('[\n  {"username": "test1", "password": "pass1"}\n]')
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
        <h1 className="text-2xl font-bold">测试数据管理</h1>
        <button
          onClick={() => setShowCreateModal(true)}
          disabled={!selectedProjectId}
          className={`px-4 py-2 rounded ${
            selectedProjectId
              ? 'bg-blue-500 text-white hover:bg-blue-600'
              : 'bg-gray-300 text-gray-500 cursor-not-allowed'
          }`}
        >
          创建测试数据
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
          className="w-full md:w-80 px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          <option value="">请选择项目</option>
          {projects.map((project) => {
            const dataCount = projectStats[project.id] || 0
            return (
              <option key={project.id} value={project.id}>
                {project.name} ({dataCount} 条数据)
              </option>
            )
          })}
        </select>
        {projects.length > 0 && (
          <div className="mt-2 text-sm text-gray-600">
            💡 提示：括号中的数字表示该项目已有的测试数据数量
          </div>
        )}
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
              <p className="text-gray-500">请先选择项目以查看测试数据</p>
            </div>
          ) : testDataList.length === 0 ? (
            <div className="text-center py-12">
              <p className="text-gray-500 mb-4">该项目暂无测试数据</p>
              <button
                onClick={() => setShowCreateModal(true)}
                className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
              >
                创建测试数据
              </button>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {testDataList.map((data) => (
                <div key={data.id} className="border rounded-lg p-4 hover:shadow-md transition-shadow">
                  <h3 className="text-lg font-semibold mb-2">{data.name}</h3>
                  <p className="text-gray-600 text-sm mb-2">
                    {data.description || '暂无描述'}
                  </p>
                  <div className="text-xs text-gray-500 mb-2">
                    类型: {data.data_type} | 数据条数: {data.data?.length || 0}
                  </div>
                  {data.tags && data.tags.length > 0 && (
                    <div className="flex gap-1 mb-2">
                      {data.tags.map((tag, index) => (
                        <span key={index} className="px-2 py-1 bg-blue-100 text-blue-700 text-xs rounded">
                          {tag}
                        </span>
                      ))}
                    </div>
                  )}
                  <div className="flex justify-between items-center mt-3">
                    <span className="text-xs text-gray-500">
                      创建时间: {new Date(data.created_at).toLocaleDateString()}
                    </span>
                    <div className="flex gap-2">
                      <button
                        onClick={() => handleViewData(data)}
                        className="text-blue-500 hover:text-blue-700 text-sm"
                      >
                        查看
                      </button>
                      <button
                        onClick={() => handleEditData(data)}
                        className="text-green-500 hover:text-green-700 text-sm"
                      >
                        编辑
                      </button>
                      <button
                        onClick={() => handleDeleteTestData(data.id)}
                        className="text-red-500 hover:text-red-700 text-sm"
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

      {/* 创建测试数据模态框 */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-md max-h-screen overflow-y-auto">
            <h2 className="text-xl font-bold mb-4">创建测试数据</h2>

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  数据名称 <span className="text-red-500">*</span>
                </label>
                <input
                  type="text"
                  value={newDataName}
                  onChange={(e) => setNewDataName(e.target.value)}
                  className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="例如: 用户登录数据"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  数据描述
                </label>
                <textarea
                  value={newDataDescription}
                  onChange={(e) => setNewDataDescription(e.target.value)}
                  className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="输入数据描述"
                  rows={2}
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  JSON 数据 <span className="text-red-500">*</span>
                </label>
                <textarea
                  value={newDataJson}
                  onChange={(e) => setNewDataJson(e.target.value)}
                  className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 font-mono text-sm"
                  placeholder='[{"username": "test1", "password": "pass1"}]'
                  rows={8}
                />
                <p className="text-xs text-gray-500 mt-1">
                  请输入有效的 JSON 数组格式，例如：{'[{"username": "test1", "password": "pass1"}]'}
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
                  onClick={handleCreateTestData}
                  className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
                >
                  创建
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* 查看测试数据模态框 */}
      {showViewModal && viewingData && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-3xl max-h-screen overflow-y-auto">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-xl font-bold">测试数据详情</h2>
              <button
                onClick={() => setShowViewModal(false)}
                className="text-gray-400 hover:text-gray-600"
              >
                ✕
              </button>
            </div>

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700">数据名称</label>
                <p className="mt-1 text-gray-900">{viewingData.name}</p>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700">数据描述</label>
                <p className="mt-1 text-gray-900">{viewingData.description || '暂无描述'}</p>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700">数据类型</label>
                <p className="mt-1 text-gray-900">{viewingData.data_type}</p>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700">数据条数</label>
                <p className="mt-1 text-gray-900">{viewingData.data?.length || 0} 条</p>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">JSON 数据</label>
                <pre className="bg-gray-50 p-4 rounded-lg overflow-x-auto text-sm">
                  {JSON.stringify(viewingData.data, null, 2)}
                </pre>
              </div>

              {viewingData.tags && viewingData.tags.length > 0 && (
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">标签</label>
                  <div className="flex flex-wrap gap-2">
                    {viewingData.tags.map((tag, index) => (
                      <span key={index} className="px-2 py-1 bg-blue-100 text-blue-700 text-xs rounded">
                        {tag}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              <div className="text-xs text-gray-500">
                创建时间: {new Date(viewingData.created_at).toLocaleString('zh-CN')}
              </div>

              <div className="flex justify-end space-x-2 pt-4 border-t">
                <button
                  onClick={() => {
                    setShowViewModal(false)
                    handleEditData(viewingData)
                  }}
                  className="px-4 py-2 bg-green-500 text-white rounded hover:bg-green-600"
                >
                  编辑
                </button>
                <button
                  onClick={() => setShowViewModal(false)}
                  className="px-4 py-2 border rounded hover:bg-gray-50"
                >
                  关闭
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* 编辑测试数据模态框 */}
      {showEditModal && editingData && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-3xl max-h-screen overflow-y-auto">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-xl font-bold">编辑测试数据</h2>
              <button
                onClick={() => {
                  setShowEditModal(false)
                  setEditingData(null)
                }}
                className="text-gray-400 hover:text-gray-600"
              >
                ✕
              </button>
            </div>

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  数据名称 <span className="text-red-500">*</span>
                </label>
                <input
                  type="text"
                  value={editingData.name}
                  onChange={(e) => setEditingData({ ...editingData, name: e.target.value })}
                  className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  数据描述
                </label>
                <textarea
                  value={editingData.description || ''}
                  onChange={(e) => setEditingData({ ...editingData, description: e.target.value })}
                  className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="输入数据描述"
                  rows={2}
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  JSON 数据 <span className="text-red-500">*</span>
                </label>
                <textarea
                  value={editDataJson}
                  onChange={(e) => setEditDataJson(e.target.value)}
                  className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 font-mono text-sm"
                  placeholder='[{"username": "test1", "password": "pass1"}]'
                  rows={12}
                />
                <p className="text-xs text-gray-500 mt-1">
                  请输入有效的 JSON 数组格式
                </p>
              </div>

              <div className="flex justify-end space-x-2 pt-4 border-t">
                <button
                  onClick={() => {
                    setShowEditModal(false)
                    setEditingData(null)
                  }}
                  className="px-4 py-2 border rounded hover:bg-gray-50"
                >
                  取消
                </button>
                <button
                  onClick={handleUpdateData}
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
export default TestDataPage
